"""One price refresh cycle: lock, load coins, fetch, evaluate, upsert, release.

The long-running loop lives elsewhere; this function never raises for expected
failures so the loop survives. Logs carry only symbols, reasons and counts.
"""

import asyncio
import logging
import secrets
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal

import httpx
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.services import kraken
from app.services.fake_prices import make_fake_source
from app.services.kraken import KrakenError, TickerSource
from app.services.price_rules import Candidate, evaluate_price, mid_from_ticker
from app.services.prices import AcceptedPrice, load_active_coins, upsert_prices

logger = logging.getLogger(__name__)

LOCK_KEY = "sim:lock:price-refresh"
# Exceeds the worst-case cycle; SOURCE_TIMEOUT_S bounds the source call strictly below it,
# because httpx timeouts apply per phase, so retries plus backoff could otherwise outlive it.
LOCK_TTL_MS = 45_000
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
        return await kraken.fetch_tickers(http, pairs)

    return source


async def _release(redis: Redis, token: str) -> None:
    try:
        await redis.eval(_RELEASE_LUA, 1, LOCK_KEY, token)
    except RedisError:
        logger.warning("price lock release failed")


async def _refresh(
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
    source: TickerSource,
    settings: Settings,
    candidates: dict[int, Candidate],
    now: Callable[[], datetime],
) -> CycleResult:
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
            mid = mid_from_ticker(entry)
            if mid is None:
                rejected += 1
                logger.warning("price rejected: symbol=%s reason=invalid", coin.symbol)
                continue
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
                accepted.append(AcceptedPrice(coin.coin_id, mid, observed_at))
            else:
                rejected += 1
                assert coin.last_mid is not None  # noqa: S101 - a spike needs a last good price
                move = abs(mid - coin.last_mid) / coin.last_mid
                logger.warning(
                    "price rejected: symbol=%s reason=%s move=%s",
                    coin.symbol,
                    decision,
                    move.quantize(Decimal("0.001")),
                )
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
        outcome = await _refresh(
            sessionmaker=sessionmaker,
            source=source,
            settings=settings,
            candidates=candidates,
            now=now,
        )
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
