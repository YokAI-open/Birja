"""Consume display history demand under a separate wall clock and attempt budget."""

import asyncio
import logging
import secrets
import time
from collections import deque
from collections.abc import Callable, Sequence
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from math import ceil

import httpx
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import SchedulerSettings
from app.schemas.market_history import (
    HistoryCoverage,
    HistoryState,
    IexHistoryScope,
    KrakenHistoryScope,
    MarketHistoryResponse,
)
from app.services.kraken import TICKER_ATTEMPTS
from app.services.market_history import HistoryDataError, normalize_history
from app.services.market_history_authority import (
    HistoryAuthority,
    HistoryInstrumentNotFound,
    HistoryListingChanged,
    resolve_history,
)
from app.services.market_history_demand import (
    HistoryJob,
    claim_history,
    complete_history,
    current_history_job,
    history_response,
    release_history,
)
from app.services.market_history_providers import (
    HistoryProviderError,
    fetch_iex_history,
    fetch_kraken_history,
)
from app.services.stock_admission import ProductAdmission
from app.tasks.scheduler import CycleResult
from app.tasks.stock_scheduler import _admissions, account_request_ceiling, reserve_account_attempt

HISTORY_CHECK_INTERVAL_SECONDS = 2
_WALL_SECONDS = 5
_CACHE_SECONDS = {"1D": 120, "1W": 600, "1M": 600}
_CACHE_STATES: dict[HistoryCoverage, HistoryState] = {
    "complete": "ready",
    "partial": "partial",
    "empty": "empty",
}
_WINDOW = """
local t = redis.call('TIME')
local now = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)
for i, key in ipairs(KEYS) do
    redis.call('ZREMRANGEBYSCORE', key, '-inf', now-60000)
    if redis.call('ZCARD', key) >= tonumber(ARGV[i]) then return 0 end
end
if #KEYS == 2 and redis.call('ZCOUNT', KEYS[1], now-1000, '+inf') > 0 then return 0 end
for _, key in ipairs(KEYS) do
    redis.call('ZADD', key, now, ARGV[#KEYS + 1])
    redis.call('PEXPIRE', key, 60000)
end
return 1
"""
logger = logging.getLogger(__name__)


class _HistoryDeferred(Exception):
    """History capacity or authority is currently unavailable."""


class KrakenHistoryBudget:
    """The dedicated scheduler observes its actual Ticker attempts without blocking them."""

    def __init__(self, interval: int, monotonic: Callable[[], float] = time.monotonic) -> None:
        self.interval = interval
        self.monotonic = monotonic
        self.started_at: float | None = None
        self.next_due: float | None = None
        self.running = False
        self.pairs: frozenset[str] = frozenset()
        self.attempts: deque[tuple[float, frozenset[str]]] = deque()

    def start_ticker(self) -> None:
        self.running = True
        now = self.monotonic()
        base = min(now, self.next_due) if self.next_due is not None else now
        self.next_due = base + self.interval

    def finish_ticker(self) -> None:
        now = self.monotonic()
        if self.next_due is not None and self.next_due <= now:
            self.next_due = now + self.interval
        self.running = False

    def set_pairs(self, pairs: Sequence[str]) -> None:
        self.pairs = frozenset(pairs)

    def record_ticker_attempt(self, pairs: Sequence[str]) -> None:
        now = self.monotonic()
        if self.started_at is None:
            self.started_at = now
        self._prune(now)
        self.attempts.append((now, frozenset(pairs)))

    def _prune(self, now: float) -> None:
        while self.attempts and self.attempts[0][0] <= now - 60:
            self.attempts.popleft()

    def headroom(self, scope: KrakenHistoryScope, pair: str) -> tuple[int, int] | None:
        now = self.monotonic()
        if (
            self.started_at is None
            or now - self.started_at < 60
            or self.next_due is None
            or self.running
            or now + _WALL_SECONDS >= self.next_due
            or (self.attempts and now - self.attempts[-1][0] < 1)
            or pair not in self.pairs
        ):
            return None
        self._prune(now)
        # Reserve the full retry plus pair-fallback cost of future Ticker cycles
        # overlapping this minute. Count every real attempt still in the window.
        upcoming = ceil((60 - (self.next_due - now)) / self.interval)
        upcoming = max(0, upcoming)
        global_reserve = len(self.attempts) + upcoming * (TICKER_ATTEMPTS + len(self.pairs))
        pair_reserve = sum(pair in pairs for _, pairs in self.attempts) + upcoming * (
            TICKER_ATTEMPTS + 1
        )
        return (
            min(
                6,
                scope.admitted_requests_per_minute,
                scope.observed_requests_per_minute,
                scope.aggregate_ip_requests_per_minute - global_reserve,
            ),
            scope.aggregate_pair_requests_per_minute - pair_reserve,
        )


async def _reserve_alpaca(
    redis: Redis,
    settings: SchedulerSettings,
    scope: IexHistoryScope,
    evidence: dict[str, ProductAdmission],
    now: datetime,
) -> bool:
    ceiling = min(
        account_request_ceiling(settings, evidence, now),
        scope.admitted_requests_per_minute,
        scope.observed_requests_per_minute,
    )
    available = ceiling - (ceiling + 1) // 2
    if available < 1:
        return False
    account = sha256(scope.account.encode()).hexdigest()
    reserved = await redis.eval(
        _WINDOW,
        1,
        f"sim:history-quota:v1:alpaca:{account}",
        min(4, available),
        secrets.token_hex(16),
    )
    return bool(
        reserved and await reserve_account_attempt(redis, settings, evidence, at=now, cap=available)
    )


async def _reserve_kraken(
    redis: Redis, scope: KrakenHistoryScope, pair: str, tracker: KrakenHistoryBudget | None
) -> bool:
    room = tracker.headroom(scope, pair) if tracker is not None else None
    if room is None or min(room) < 1:
        return False
    server = sha256(scope.server.encode()).hexdigest()
    prefix = f"sim:history-quota:v1:kraken:{server}"
    return bool(
        await redis.eval(_WINDOW, 2, prefix, f"{prefix}:{pair}", *room, secrets.token_hex(16))
    )


def _cache_expiry_ms(authority: HistoryAuthority, started: datetime, *, available: bool) -> int:
    ceiling = _CACHE_SECONDS[authority.window.range] if available else 10
    retained_until = started + timedelta(seconds=min(ceiling, authority.scope.retention_seconds))
    return int(min(authority.valid_until, retained_until).timestamp() * 1000)


async def _load_authority(
    db: AsyncSession, settings: SchedulerSettings, job: HistoryJob, at: datetime
) -> HistoryAuthority | None:
    try:
        authority = await resolve_history(db, settings, job.query, at)
    except HistoryInstrumentNotFound, HistoryListingChanged:
        return None
    if authority is None or authority.fingerprint != job.fingerprint:
        return None
    return authority


async def _consume(
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    quota_redis: Redis,
    http: httpx.AsyncClient,
    stock_http: httpx.AsyncClient | None,
    settings: SchedulerSettings,
    job: HistoryJob,
    tracker: KrakenHistoryBudget | None,
    now: Callable[[], datetime],
) -> int:
    started = now()
    server = settings.stock_data_server
    async with sessionmaker() as db:
        authority = await _load_authority(db, settings, job, started)
    if authority is None:
        await complete_history(redis, server, job)
        return 0
    scope = authority.scope

    async def before_attempt() -> None:
        checked_at = now()
        async with sessionmaker() as db:
            current = await _load_authority(db, settings, job, checked_at)
            evidence = await _admissions(db) if isinstance(scope, IexHistoryScope) else {}
        if current is None or not await current_history_job(redis, server, job):
            raise _HistoryDeferred
        if isinstance(scope, IexHistoryScope):
            permitted = await _reserve_alpaca(quota_redis, settings, scope, evidence, checked_at)
        else:
            permitted = await _reserve_kraken(
                quota_redis, scope, authority.provider_symbol, tracker
            )
        if (
            not permitted
            or not await current_history_job(redis, server, job)
            or now() >= current.valid_until
        ):
            raise _HistoryDeferred
        if isinstance(scope, KrakenHistoryScope):
            # The reservation and lease check both await Redis. Recheck ticker
            # priority after those awaits, immediately before the OHLC request.
            room = tracker.headroom(scope, authority.provider_symbol) if tracker else None
            if room is None or min(room) < 1:
                raise _HistoryDeferred

    try:
        if isinstance(scope, IexHistoryScope) and stock_http is not None:
            batch = await fetch_iex_history(
                stock_http,
                authority.provider_symbol,
                authority.window,
                before_attempt=before_attempt,
                max_bytes=scope.max_response_bytes,
            )
        elif isinstance(scope, KrakenHistoryScope) and settings.price_source == "kraken":
            batch = await fetch_kraken_history(
                http,
                authority.provider_symbol,
                authority.window,
                before_attempt=before_attempt,
                max_bytes=scope.max_response_bytes,
            )
        else:
            raise _HistoryDeferred
        series = normalize_history(authority.window, batch)
        result = MarketHistoryResponse(
            instrument=job.query.instrument,
            range=job.query.range,
            state=_CACHE_STATES[series.coverage],
            series=series,
        )
    except HistoryProviderError, HistoryDataError, _HistoryDeferred:
        result = history_response(job.query, "unavailable")

    async with sessionmaker() as db:
        current = await _load_authority(db, settings, job, now())
    if current is None:
        await complete_history(redis, server, job)
        return 0
    expires_at = _cache_expiry_ms(current, started, available=result.series is not None)
    stored = await complete_history(redis, server, job, result, expires_at_ms=expires_at)
    return int(stored and result.series is not None)


async def run_history_cycle(
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis | None,
    quota_redis: Redis,
    http: httpx.AsyncClient,
    stock_http: httpx.AsyncClient | None,
    settings: SchedulerSettings,
    tracker: KrakenHistoryBudget | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> CycleResult:
    if redis is None or settings.market_history_scope_json is None:
        return CycleResult("ok")
    job = None
    failed = False
    server = settings.stock_data_server
    try:
        async with asyncio.timeout(_WALL_SECONDS):
            job = await claim_history(redis, server)
            if job is None:
                return CycleResult("ok")
            accepted = await _consume(
                sessionmaker, redis, quota_redis, http, stock_http, settings, job, tracker, now
            )
            return CycleResult("ok", accepted=accepted, rejected=1 - accepted)
    except Exception as exc:
        failed = True
        logger.warning("market history cycle failed: %s", type(exc).__name__)
        return CycleResult("source_error")
    finally:
        if job is not None:
            with suppress(RedisError, TimeoutError):
                async with asyncio.timeout(1):
                    if failed:
                        await complete_history(redis, server, job)
                    await release_history(redis, server, job)
