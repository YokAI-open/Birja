"""One price refresh cycle: lock, load coins, fetch, evaluate, upsert, release.

The long-running loop lives elsewhere; this function never raises for expected
failures so the loop survives. Logs carry only symbols, reasons and counts.
"""

import asyncio
import contextlib
import logging
import secrets
import signal
import tempfile
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

import httpx
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.services import kraken
from app.services.fake_prices import make_fake_source
from app.services.kraken import KrakenError, TickerSource
from app.services.price_rules import Candidate, evaluate_price, mid_from_ticker
from app.services.prices import AcceptedPrice, CoinState, load_active_coins, upsert_prices

# Explicit name: under ``python -m`` __name__ is "__main__", which is outside the
# "app" tree that configure_logging() attaches its handler to, so INFO logs were lost.
logger = logging.getLogger("app.tasks.scheduler")

LOCK_KEY = "sim:lock:price-refresh"
# CYCLE_TIMEOUT_S bounds the whole cycle under the lock (DB read, source call, evaluate,
# upsert), so the lock cannot expire while this instance still works. The margin up to
# LOCK_TTL_MS covers the release call. SOURCE_TIMEOUT_S bounds the source call inside it,
# because httpx timeouts apply per phase, so retries plus backoff could otherwise outlive it.
LOCK_TTL_MS = 45_000
CYCLE_TIMEOUT_S = 40
SOURCE_TIMEOUT_S = 35

_RELEASE_LUA = (
    "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) "
    "else return 0 end"
)

CycleStatus = Literal["ok", "locked", "lock_error", "source_error"]


@dataclass(frozen=True)
class CycleResult:
    status: CycleStatus
    accepted: int = 0
    rejected: int = 0


def build_source(settings: Settings, http: httpx.AsyncClient) -> TickerSource:
    if settings.price_source == "fake":
        if settings.env == "prod":
            raise RuntimeError("price_source 'fake' is not allowed in prod")
        return make_fake_source(lambda: datetime.now(UTC))

    async def source(pairs: Sequence[str]) -> dict[str, Any]:
        return await kraken.fetch_tickers_isolated(http, pairs)

    return source


async def _release(redis: Redis, token: str) -> None:
    try:
        await redis.eval(_RELEASE_LUA, 1, LOCK_KEY, token)
    except RedisError:
        logger.warning("price lock release failed")


def _evaluate_coin(
    coin: CoinState,
    entry: object,
    settings: Settings,
    candidates: dict[int, Candidate],
    observed_at: datetime,
) -> AcceptedPrice | None:
    """Accepted price for one coin, or None (logged) if this poll is rejected."""
    mid = mid_from_ticker(entry)
    if mid is None:
        logger.warning("price rejected: symbol=%s reason=invalid", coin.symbol)
        return None
    decision, candidate = evaluate_price(
        coin.last_mid,
        mid,
        candidates.get(coin.coin_id),
        max_move=settings.price_max_move,
        confirm_tol=settings.price_confirm_tolerance,
        confirm_n=settings.price_confirm_polls,
    )
    if candidate is None:
        candidates.pop(coin.coin_id, None)
    else:
        candidates[coin.coin_id] = candidate
    if decision in ("accept", "accept_confirmed"):
        return AcceptedPrice(coin.coin_id, mid, observed_at)
    assert coin.last_mid is not None  # noqa: S101 - a spike needs a last good price
    move = abs(mid - coin.last_mid) / coin.last_mid
    logger.warning(
        "price rejected: symbol=%s reason=%s move=%s",
        coin.symbol,
        decision,
        move.quantize(Decimal("0.001")),
    )
    return None


async def _refresh(
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
    source: TickerSource,
    settings: Settings,
    candidates: dict[int, Candidate],
    now: Callable[[], datetime],
) -> CycleResult:
    # Short read: the session (and its transaction) is closed before the source call,
    # so no connection sits idle in a transaction while Kraken is slow.
    async with sessionmaker() as session:
        coins = await load_active_coins(session)
    if not coins:
        return CycleResult("ok")
    try:
        async with asyncio.timeout(SOURCE_TIMEOUT_S):
            result = await source([c.kraken_pair for c in coins])
    except (KrakenError, httpx.HTTPError, TimeoutError) as exc:
        logger.error("price source failed: %s", str(exc) or type(exc).__name__)
        return CycleResult("source_error")
    # Ticker carries no timestamp: the arrival time is the as_of.
    observed_at = now()
    accepted: list[AcceptedPrice] = []
    rejected = 0
    for coin in coins:
        entry = result.get(coin.kraken_pair)
        if entry is None:
            rejected += 1
            logger.warning("price rejected: symbol=%s reason=missing", coin.symbol)
            continue
        try:
            price = _evaluate_coin(coin, entry, settings, candidates, observed_at)
        except ArithmeticError, ValueError:
            # One coin's bad numbers (e.g. Decimal overflow) must not abort the cycle.
            price = None
            logger.warning("price rejected: symbol=%s reason=invalid", coin.symbol)
        if price is None:
            rejected += 1
        else:
            accepted.append(price)
    async with sessionmaker() as session:
        await upsert_prices(session, accepted, settings.price_source)
        await session.commit()
    return CycleResult("ok", accepted=len(accepted), rejected=rejected)


async def run_cycle(
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    source: TickerSource,
    settings: Settings,
    candidates: dict[int, Candidate],
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> CycleResult:
    token = secrets.token_hex(16)
    try:
        got_lock = await redis.set(LOCK_KEY, token, nx=True, px=LOCK_TTL_MS)
    except RedisError:
        logger.warning("price cycle: lock unavailable, skipping")
        return CycleResult("lock_error")
    if not got_lock:
        logger.info("price cycle: lock held elsewhere, skipping")
        return CycleResult("locked")
    try:
        async with asyncio.timeout(CYCLE_TIMEOUT_S):
            outcome = await _refresh(
                sessionmaker=sessionmaker,
                source=source,
                settings=settings,
                candidates=candidates,
                now=now,
            )
    except TimeoutError:
        logger.error("price cycle timed out after %ss", CYCLE_TIMEOUT_S)
        outcome = CycleResult("source_error")
    except Exception:
        logger.exception("price cycle failed unexpectedly")
        outcome = CycleResult("source_error")
    finally:
        await _release(redis, token)
    logger.info(
        "price cycle: status=%s accepted=%d rejected=%d",
        outcome.status,
        outcome.accepted,
        outcome.rejected,
    )
    return outcome


HEARTBEAT_PATH = Path(tempfile.gettempdir()) / "birja-scheduler-heartbeat"


def touch_heartbeat(path: Path) -> None:
    path.touch()


async def _cycle_unless_stopped(
    cycle: Callable[[], Awaitable[CycleResult]], stop: asyncio.Event
) -> bool:
    """Run one cycle; True if it finished, False if ``stop`` cancelled it first."""
    task = asyncio.ensure_future(cycle())
    stopper = asyncio.ensure_future(stop.wait())
    try:
        await asyncio.wait({task, stopper}, return_when=asyncio.FIRST_COMPLETED)
    finally:
        stopper.cancel()
        if not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
    if task.cancelled():
        logger.info("price cycle cancelled for shutdown")
        return False
    task.result()
    return True


async def run(
    *,
    cycle: Callable[[], Awaitable[CycleResult]],
    interval: float,
    stop: asyncio.Event,
    heartbeat: Path = HEARTBEAT_PATH,
    monotonic: Callable[[], float] = time.monotonic,
) -> None:
    """Run ``cycle`` now and then on a fixed schedule until ``stop`` is set.

    The heartbeat is touched after every cycle, even failed ones, so an upstream outage
    shows up as stale prices rather than as a restarting container. Setting ``stop``
    cancels an in-flight cycle, so its ``finally`` releases the lock well within the
    container's stop grace period instead of being cut off by SIGKILL.
    """
    next_tick = monotonic()
    while not stop.is_set():
        if not await _cycle_unless_stopped(cycle, stop):
            return
        touch_heartbeat(heartbeat)
        next_tick += interval
        if next_tick - monotonic() < 0:
            next_tick = monotonic() + interval
        delay = max(0.0, next_tick - monotonic())
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=delay)


async def amain(stop: asyncio.Event | None = None) -> None:
    configure_logging()
    settings = get_settings()
    own_stop = stop is None
    stop = stop or asyncio.Event()
    if own_stop:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, stop.set)
    engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={
            "timeout": 5,
            "server_settings": {
                "statement_timeout": "30000",
                "idle_in_transaction_session_timeout": "30000",
            },
        },
    )
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    http = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
    try:
        source = build_source(settings, http)
        candidates: dict[int, Candidate] = {}
        logger.info(
            "price scheduler started source=%s interval=%s",
            settings.price_source,
            settings.price_poll_interval_seconds,
        )

        async def cycle() -> CycleResult:
            return await run_cycle(
                sessionmaker=sessionmaker,
                redis=redis,
                source=source,
                settings=settings,
                candidates=candidates,
            )

        await run(
            cycle=cycle,
            interval=settings.price_poll_interval_seconds,
            stop=stop,
        )
    finally:
        await http.aclose()
        await redis.aclose()
        await engine.dispose()


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":  # pragma: no cover
    main()
