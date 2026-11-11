"""Independent stock collection boundary, disabled until authoritative admission."""

import asyncio
import logging
import secrets
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from hashlib import sha256

import httpx
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import SchedulerSettings
from app.models.stock import StockDataAdmission
from app.services.alpaca import AlpacaError, fetch_iex_quotes
from app.services.stock_admission import ProductAdmission, evaluate_admission
from app.services.stock_quote_rules import CURATED_SYMBOLS, verified_mapping
from app.services.stock_quotes import load_stock_catalog, upsert_stock_quotes
from app.services.stock_sessions import RegularSession, build_sessions, persist_sessions, session_at
from app.tasks.scheduler import CycleResult

LOCK_KEY = "sim:lock:stock-refresh"
WINDOW_KEY = "sim:stock:quote-window"
LOCK_TTL_MS = 45_000
CYCLE_TIMEOUT_S = 40
SOURCE_TIMEOUT_S = 35
ACCOUNT_WINDOW_PREFIX = "sim:stock:account-attempts:"
# A rolling 60-second account budget, atomically shared by every real quote and
# action attempt (including failures/retries). Redis TIME supplies one clock.
_ACCOUNT_LUA = """
local t = redis.call('TIME')
local now = tonumber(t[1])*1000 + math.floor(tonumber(t[2])/1000)
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now-60000)
if redis.call('ZCARD', KEYS[1]) >= tonumber(ARGV[1]) then return 0 end
redis.call('ZADD', KEYS[1], now, ARGV[2])
redis.call('PEXPIRE', KEYS[1], 60000)
return 1
"""
_RELEASE_LUA = (
    "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) "
    "else return 0 end"
)
logger = logging.getLogger(__name__)


async def reserve_account_attempt(
    redis: Redis,
    settings: SchedulerSettings,
    evidence: dict[str, ProductAdmission],
    *,
    at: datetime | None = None,
) -> bool:
    # Ignore denied/unrelated rows; an enable flag cannot make them authority.
    now = at or datetime.now(UTC)
    limits = [settings.stock_account_requests_per_minute]
    for product in ("quotes", "actions"):
        row = evidence.get(product)
        decision = evaluate_admission(
            row,
            product,
            "collection",
            now,
            account=settings.stock_data_account,
            server=settings.stock_data_server,
            feed="alpaca-corporate-actions" if product == "actions" else "iex",
        )
        if decision.allowed and row is not None:
            limits.append(int(row.quota["requests_per_minute"]))
    limit = min(limits)
    key = ACCOUNT_WINDOW_PREFIX + sha256(settings.stock_data_account.encode()).hexdigest()
    return bool(await redis.eval(_ACCOUNT_LUA, 1, key, limit, secrets.token_hex(16)) == 1)


async def _admissions(db: AsyncSession) -> dict[str, ProductAdmission]:
    columns = [c for c in StockDataAdmission.__table__.columns if c.name != "id"]
    rows = (
        await db.execute(select(*columns).order_by(StockDataAdmission.product).limit(5))
    ).mappings()
    return {row["product"]: ProductAdmission(**row) for row in rows}


def _allowed(
    evidence: dict[str, ProductAdmission], settings: SchedulerSettings, now: datetime
) -> bool:
    return all(
        evaluate_admission(
            evidence.get(product),
            product,
            purpose,
            now,
            account=settings.stock_data_account,
            server=settings.stock_data_server,
        ).allowed
        for product in ("quotes", "reference", "calendar")
        for purpose in ("collection", "retention", "derived")
    )


def _open_exchanges(
    now: datetime,
    sessions: Sequence[RegularSession],
    authority: ProductAdmission,
    *,
    account: str = "birja",
    server: str = "birja",
) -> set[str]:
    return {
        exchange
        for exchange in ("NYSE", "NASDAQ")
        if session_at(exchange, now, sessions, authority, account=account, server=server).state
        == "open"
    }


async def _refresh(
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    http: httpx.AsyncClient,
    settings: SchedulerSettings,
    now: Callable[[], datetime],
    token: str,
) -> CycleResult:
    scope = {"account": settings.stock_data_account, "server": settings.stock_data_server}
    async with sessionmaker() as db:
        original = await _admissions(db)
        mappings = await load_stock_catalog(db)
    checked = now()
    if not _allowed(original, settings, checked):
        return CycleResult("ok")
    # Calendar package initialization/cold calculations must never block crypto.
    sessions = await asyncio.to_thread(build_sessions, checked, original["calendar"], **scope)
    async with sessionmaker() as db:
        current = await _admissions(db)
        checked = now()
        if current != original or not _allowed(current, settings, checked):
            return CycleResult("ok")
        await persist_sessions(db, sessions, current["calendar"], checked, **scope)
        if await redis.get(LOCK_KEY) != token:
            return CycleResult("locked")
        latest = await _admissions(db)
        if latest != current or not _allowed(latest, settings, now()):
            return CycleResult("ok")
        await db.commit()
    opened = await asyncio.to_thread(
        _open_exchanges, now(), sessions, original["calendar"], **scope
    )
    async with sessionmaker() as db:
        current = await _admissions(db)
        current_mappings = await load_stock_catalog(db)
    checked = now()
    if (
        current != original
        or not _allowed(current, settings, checked)
        or current_mappings != mappings
        or not opened
        or {m.symbol for m in mappings} != CURATED_SYMBOLS
        or not all(verified_mapping(m, checked) for m in mappings)
        or len({m.provider_asset_id for m in mappings}) != 20
    ):
        return CycleResult("ok")
    # Fresh pure check after awaited reads (calendar bounds already warmed above).
    opened &= _open_exchanges(checked, sessions, current["calendar"], **scope)
    selected = [m for m in mappings if m.listing_exchange in opened]
    quota = current["quotes"].quota["requests_per_minute"]
    if not selected or quota < 1 or await redis.get(LOCK_KEY) != token:
        return CycleResult("ok")
    # Separate shared cadence guard survives lease release, including failures.
    if not await redis.set(
        WINDOW_KEY, token, nx=True, px=settings.stock_poll_interval_seconds * 1000
    ):
        return CycleResult("locked")

    async def before_request(request: httpx.Request) -> None:
        # HTTPX async request hooks run before *each* actual attempt, including
        # retries. No DB transaction remains open when the network starts.
        # https://www.python-httpx.org/advanced/event-hooks/
        async with sessionmaker() as db:
            latest = await _admissions(db)
            live_mappings = await load_stock_catalog(db)
        owned = await redis.get(LOCK_KEY) == token
        checked = now()
        if (
            latest != original
            or live_mappings != mappings
            or not owned
            or not _allowed(latest, settings, checked)
            or not opened <= _open_exchanges(checked, sessions, latest["calendar"], **scope)
        ):
            raise AlpacaError("current_admission")
        if not await reserve_account_attempt(redis, settings, latest, at=checked):
            raise AlpacaError("account_budget")

    http.event_hooks["request"].append(before_request)
    try:
        async with asyncio.timeout(SOURCE_TIMEOUT_S):
            batch = await fetch_iex_quotes(
                http,
                selected,
                current["quotes"],
                now,
                attempts=min(settings.stock_max_retries + 1, quota),
                max_bytes=settings.stock_max_response_bytes,
                account=settings.stock_data_account,
                server=settings.stock_data_server,
                budget_seconds=min(
                    10,
                    settings.stock_cycle_budget_seconds,
                    settings.stock_request_timeout_seconds * (settings.stock_max_retries + 1),
                ),
            )
    finally:
        http.event_hooks["request"].remove(before_request)
    accepted = 0
    quotes = list(batch.quotes)
    # HTTP has finished. One instrument gate belongs to each short caller-owned
    # transaction; never hold twenty financial locks or commit inside upsert.
    for quote in sorted(quotes, key=lambda item: item.coin_id):
        async with sessionmaker() as db:
            latest = await _admissions(db)
            checked = now()
            if latest != original or not _allowed(latest, settings, checked):
                return CycleResult("ok", accepted=accepted)
            opened = _open_exchanges(checked, sessions, latest["calendar"], **scope)
            if (
                next(m for m in mappings if m.coin_id == quote.coin_id).listing_exchange
                not in opened
            ):
                continue
            count = await upsert_stock_quotes(
                db,
                [quote],
                original["quotes"].generation,
                now=now,
                account=settings.stock_data_account,
                server=settings.stock_data_server,
            )
            latest = await _admissions(db)
            owned = await redis.get(LOCK_KEY) == token
            if (
                latest != original
                or not _allowed(latest, settings, now())
                or not owned
                or _open_exchanges(now(), sessions, latest["calendar"], **scope) != opened
            ):
                return CycleResult("ok", accepted=accepted)
            await db.commit()
            accepted += count
    return CycleResult("ok", accepted=accepted, rejected=len(selected) - len(quotes))


async def run_stock_cycle(
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    http: httpx.AsyncClient,
    settings: SchedulerSettings,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> CycleResult:
    if not settings.stock_data_enabled:
        return CycleResult("ok")
    token = secrets.token_hex(16)
    try:
        acquired = await redis.set(LOCK_KEY, token, nx=True, px=LOCK_TTL_MS)
    except RedisError:
        logger.warning("stock cycle: lock unavailable")
        return CycleResult("lock_error")
    if not acquired:
        return CycleResult("locked")
    try:
        async with asyncio.timeout(min(CYCLE_TIMEOUT_S, settings.stock_cycle_budget_seconds)):
            return await _refresh(sessionmaker, redis, http, settings, now, token)
    except Exception as exc:
        # No provider bodies, request headers, URLs or private evidence in logs.
        logger.warning("stock cycle failed: %s", type(exc).__name__)
        return CycleResult("source_error")
    finally:
        try:
            await redis.eval(_RELEASE_LUA, 1, LOCK_KEY, token)
        except RedisError:
            logger.warning("stock lock release failed")
