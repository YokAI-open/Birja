"""One bounded worker for selected display, selected financial, and held quotes."""

import asyncio
import logging
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import SchedulerSettings
from app.services.alpaca import AlpacaError, fetch_catalog_iex_quotes
from app.services.stock_catalog_financial_quotes import (
    CatalogFinancialQuoteContext,
    HeldCatalogQuoteCandidate,
    HeldQuotePosition,
    held_catalog_quote_page,
    is_catalog_quote_held,
    load_catalog_financial_quote_context,
    publish_catalog_financial_quote,
)
from app.services.stock_catalog_quote_demand import (
    CatalogQuoteOutcome,
    CatalogQuoteRequest,
    complete_catalog_quote,
    current_catalog_quote_request,
    pending_catalog_quotes,
)
from app.services.stock_catalog_quotes import (
    CatalogQuoteBinding,
    CatalogQuoteContext,
    load_catalog_quote_context,
    publish_catalog_quote,
)
from app.tasks.scheduler import CycleResult
from app.tasks.stock_scheduler import _admissions, reserve_account_attempt

CATALOG_LOCK_KEY = "sim:lock:stock-catalog-quote"
_BATCH_SIZE = 8
_WORK_SECONDS = 6
_LOCK_MS = 10_000
_RELEASE_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""
logger = logging.getLogger(__name__)


def _binding_for(
    request: CatalogQuoteRequest, context: CatalogQuoteContext, now: datetime
) -> CatalogQuoteBinding | None:
    binding, decision = context.binding, context.session
    current = decision.current
    if (
        binding is None
        or binding.catalog_id != request.catalog_id
        or binding.listing_version != request.listing_version
        or binding.fingerprint != request.fingerprint
        or now >= binding.valid_until
        or decision.state != "open"
        or decision.valid_until is None
        or now >= decision.valid_until
        or current is None
        or current.opens_at is None
        or current.closes_at is None
        or not current.opens_at <= now < current.closes_at
    ):
        return None
    return binding


@dataclass
class CatalogQuoteCursor:
    after: HeldQuotePosition | None = None
    next_probe_at: datetime | None = None
    held_first: bool = False


@dataclass(frozen=True)
class _QuoteWork:
    authority: CatalogQuoteBinding | CatalogFinancialQuoteContext
    request: CatalogQuoteRequest | None = None
    held: HeldCatalogQuoteCandidate | None = None

    @property
    def identity(self) -> tuple[int, int]:
        if isinstance(self.authority, CatalogFinancialQuoteContext):
            return self.authority.binding.catalog_id, self.authority.binding.listing_id
        return self.authority.catalog_id, self.authority.listing_version

    @property
    def provider_symbol(self) -> str:
        if isinstance(self.authority, CatalogFinancialQuoteContext):
            return self.authority.binding.provider_symbol
        return self.authority.provider_symbol

    @property
    def exchange(self) -> str:
        if isinstance(self.authority, CatalogFinancialQuoteContext):
            return self.authority.binding.listing_exchange
        return self.authority.listing_exchange


async def _selection_authority(
    db: AsyncSession, settings: SchedulerSettings, request: CatalogQuoteRequest, now: datetime
) -> CatalogQuoteBinding | CatalogFinancialQuoteContext | None:
    if request.purpose == "display":
        context = await load_catalog_quote_context(db, settings, request.catalog_id, now=now)
        return _binding_for(request, context, now)
    financial = await load_catalog_financial_quote_context(
        db, settings, request.catalog_id, request.listing_version, now
    )
    return financial if financial and financial.fingerprint == request.fingerprint else None


async def _select_batch(
    sessionmaker: async_sessionmaker[AsyncSession],
    settings: SchedulerSettings,
    requests: tuple[CatalogQuoteRequest, ...],
    held_page: tuple[HeldCatalogQuoteCandidate, ...],
    now: Callable[[], datetime],
    *,
    held_first: bool,
) -> tuple[list[list[_QuoteWork]], list[CatalogQuoteRequest], set[HeldQuotePosition]]:
    selected: list[_QuoteWork] = []
    held: list[_QuoteWork] = []
    refused: list[CatalogQuoteRequest] = []
    considered: set[HeldQuotePosition] = set()
    financial: dict[tuple[int, int], CatalogFinancialQuoteContext] = {}
    async with sessionmaker() as db:
        for request in requests:
            authority = await _selection_authority(db, settings, request, now())
            if authority is None:
                refused.append(request)
            else:
                work = _QuoteWork(authority, request)
                selected.append(work)
                if isinstance(authority, CatalogFinancialQuoteContext):
                    financial[work.identity] = authority
        for candidate in held_page:
            authority = financial.get((candidate.catalog_id, candidate.listing_id))
            if authority is None:
                authority = await load_catalog_financial_quote_context(
                    db, settings, candidate.catalog_id, candidate.listing_id, now()
                )
            if authority is None or authority.binding.coin_id != candidate.coin_id:
                considered.add(candidate.position)
            else:
                held.append(_QuoteWork(authority, held=candidate))

    # Reserve each lane its first available slot. Alternate the first lane so
    # a one-symbol grant still gives both selected and held work a turn.
    first, second = (held, selected) if held_first else (selected, held)
    groups: dict[str, list[_QuoteWork]] = {}
    for work in (*first[:1], *second[:1], *first[1:], *second[1:]):
        groups.setdefault(work.provider_symbol, []).append(work)
    resolved: list[list[_QuoteWork]] = []
    for group in groups.values():
        if len({(w.identity, w.exchange) for w in group}) != 1:
            refused.extend(w.request for w in group if w.request is not None)
            considered.update(w.held.position for w in group if w.held is not None)
        else:
            resolved.append(group)

    limit = min(
        (w.authority.symbols_per_request for group in resolved for w in group),
        default=_BATCH_SIZE,
    )
    batch = resolved[: min(_BATCH_SIZE, limit)]
    considered.update(w.held.position for group in batch for w in group if w.held is not None)
    return batch, refused, considered


def _requests(batch: list[list[_QuoteWork]]) -> tuple[CatalogQuoteRequest, ...]:
    return tuple(w.request for group in batch for w in group if w.request is not None)


async def _work_deadline(
    db: AsyncSession, settings: SchedulerSettings, work: _QuoteWork, checked_at: datetime
) -> datetime | None:
    authority = work.authority
    if isinstance(authority, CatalogQuoteBinding) and work.request is not None:
        context = await load_catalog_quote_context(
            db, settings, work.request.catalog_id, now=checked_at
        )
        if (
            _binding_for(work.request, context, checked_at) != authority
            or context.session.current is None
        ):
            return None
        closes = context.session.current.closes_at
        return min(authority.valid_until, closes) if closes is not None else None
    if work.request is not None:
        current = await _selection_authority(db, settings, work.request, checked_at)
    else:
        candidate = work.held
        if candidate is None or not await is_catalog_quote_held(db, candidate.coin_id):
            return None
        current = await load_catalog_financial_quote_context(
            db, settings, candidate.catalog_id, candidate.listing_id, checked_at
        )
    if not isinstance(authority, CatalogFinancialQuoteContext) or current != authority:
        return None
    closes = authority.session.closes_at
    if closes is None:
        return None
    deadline = min(authority.valid_until, closes)
    return min(deadline, authority.mark.valid_until) if authority.mark else deadline


async def _refresh(
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    http: httpx.AsyncClient,
    settings: SchedulerSettings,
    selected: list[list[_QuoteWork]],
    now: Callable[[], datetime],
    lock_token: str,
) -> int:
    account, server = settings.stock_data_account, settings.stock_data_server
    work = tuple(item for group in selected for item in group)
    quota = min(item.authority.requests_per_minute for item in work)
    attempt_bytes = min(item.authority.max_response_bytes for item in work)

    async def before_attempt() -> None:
        # Every attempt reads fresh committed evidence and closes the transaction.
        checked_at = now()
        deadlines = []
        async with sessionmaker() as db:
            evidence = await _admissions(db)
            for item in work:
                deadline = await _work_deadline(db, settings, item, checked_at)
                if deadline is None:
                    raise AlpacaError("failed_check")
                deadlines.append(deadline)
        if await redis.get(CATALOG_LOCK_KEY) != lock_token:
            raise AlpacaError("failed_check")
        for request in _requests(selected):
            if not await current_catalog_quote_request(
                redis, request, account=account, server=server
            ):
                raise AlpacaError("failed_check")
        if not await reserve_account_attempt(redis, settings, evidence, at=checked_at, cap=quota):
            raise AlpacaError("account_budget")
        if now() >= min(deadlines):
            raise AlpacaError("failed_check")

    try:
        prices = await fetch_catalog_iex_quotes(
            http,
            {group[0].provider_symbol: group[0].exchange for group in selected},
            now,
            before_attempt=before_attempt,
            attempts=min(settings.stock_max_retries + 1, quota),
            max_bytes=min(attempt_bytes, settings.stock_max_response_bytes),
            budget_seconds=min(_WORK_SECONDS, settings.stock_cycle_budget_seconds),
        )
    except AlpacaError as exc:
        reason: CatalogQuoteOutcome
        if exc.status == 429 or str(exc) == "account_budget":
            reason = "throttled"
        elif str(exc) == "failed_check":
            reason = "failed_check"
        else:
            reason = "source_error"
        for request in _requests(selected):
            await complete_catalog_quote(
                redis, request, account=account, server=server, reason=reason
            )
        return 0

    accepted = 0
    for group in selected:
        price = prices.get(group[0].provider_symbol)
        financial_result: bool | None = None
        for item in sorted(group, key=lambda item: item.request is None):
            selection, authority = item.request, item.authority
            reason = "quote_unavailable"
            owned = await redis.get(CATALOG_LOCK_KEY) == lock_token
            if selection is not None:
                owned = owned and await current_catalog_quote_request(
                    redis, selection, account=account, server=server
                )
            if not owned:
                reason = "failed_check"
            elif isinstance(authority, CatalogFinancialQuoteContext):
                if price is not None and financial_result is None:
                    async with sessionmaker.begin() as db:
                        financial_result = await publish_catalog_financial_quote(
                            db, settings, authority, price, now, held_only=selection is None
                        )
                if financial_result:
                    reason = "ready"
            elif selection is not None:
                async with sessionmaker() as db:
                    context = await load_catalog_quote_context(
                        db, settings, selection.catalog_id, now=now()
                    )
                checked_at = now()
                if _binding_for(selection, context, checked_at) != authority:
                    reason = "failed_check"
                elif price is not None and await publish_catalog_quote(
                    redis,
                    selection,
                    authority,
                    context.session,
                    price,
                    account=account,
                    server=server,
                    now=checked_at,
                ):
                    accepted += 1
                    continue
            if selection is not None:
                complete = await complete_catalog_quote(
                    redis, selection, account=account, server=server, reason=reason
                )
                if complete and reason == "ready":
                    accepted += 1
        if financial_result and any(item.held is not None for item in group):
            accepted += 1
    return accepted


async def run_catalog_quote_cycle(
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    http: httpx.AsyncClient,
    settings: SchedulerSettings,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    cursor: CatalogQuoteCursor | None = None,
) -> CycleResult:
    if not settings.stock_data_enabled:
        return CycleResult("ok")
    account, server = settings.stock_data_account, settings.stock_data_server
    token = secrets.token_hex(16)
    try:
        acquired = await redis.set(CATALOG_LOCK_KEY, token, nx=True, px=_LOCK_MS)
    except RedisError:
        return CycleResult("lock_error")
    if not acquired:
        return CycleResult("locked")

    requests: tuple[CatalogQuoteRequest, ...] = ()
    try:
        async with asyncio.timeout(min(_WORK_SECONDS, settings.stock_cycle_budget_seconds)):
            requests = await pending_catalog_quotes(
                redis, account=account, server=server, limit=_BATCH_SIZE
            )
            held_page: tuple[HeldCatalogQuoteCandidate, ...] = ()
            if cursor is not None and (
                cursor.next_probe_at is None or now() >= cursor.next_probe_at
            ):
                async with sessionmaker() as db:
                    held_page = await held_catalog_quote_page(
                        db,
                        now=now(),
                        after=cursor.after,
                        limit=_BATCH_SIZE,
                        refresh_seconds=settings.stock_poll_interval_seconds,
                    )
                if not held_page:
                    cursor.after = None
                    cursor.next_probe_at = now() + timedelta(
                        seconds=settings.stock_poll_interval_seconds
                    )
            if not requests and not held_page:
                return CycleResult("ok")
            selected, refused, considered = await _select_batch(
                sessionmaker,
                settings,
                requests,
                held_page,
                now,
                held_first=bool(cursor and cursor.held_first),
            )
            if cursor is not None:
                if requests and held_page:
                    cursor.held_first = not cursor.held_first
                for candidate in held_page:
                    if candidate.position not in considered:
                        break
                    cursor.after = candidate.position
            requests = (*refused, *_requests(selected))
            for request in refused:
                await complete_catalog_quote(
                    redis, request, account=account, server=server, reason="failed_check"
                )
            accepted = 0
            if selected:
                accepted = await _refresh(sessionmaker, redis, http, settings, selected, now, token)
            return CycleResult(
                "ok", accepted=accepted, rejected=len(requests) + len(considered) - accepted
            )
    except Exception as exc:
        logger.warning("catalog quote cycle failed: %s", type(exc).__name__)
        try:
            async with asyncio.timeout(1):
                for request in requests:
                    await complete_catalog_quote(
                        redis, request, account=account, server=server, reason="source_error"
                    )
        except RedisError, TimeoutError:
            logger.warning("catalog request completion unavailable")
        return CycleResult("source_error")
    finally:
        try:
            await redis.eval(_RELEASE_LUA, 1, CATALOG_LOCK_KEY, token)
        except RedisError:
            logger.warning("catalog quote lock release failed")
