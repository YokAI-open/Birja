"""Real isolated datastore cycles; only provider HTTP is replaced."""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import pytest_asyncio
import respx
from redis.asyncio import Redis
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.core.config import SchedulerSettings
from app.models.stock import StockDataAdmission, StockInstrument, StockQuote, StockSession
from app.services.alpaca import LATEST_QUOTES_URL
from app.services.stock_quotes import load_stock_catalog
from app.tasks import stock_scheduler
from tests.test_stock_admission import admitted
from tests.test_stock_sessions import evidence


@pytest_asyncio.fixture
async def state(engine: AsyncEngine, clean_stock_discovery: None) -> AsyncIterator[dict]:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    # Fixed open-session clock; expiry guards additionally use actual DB UTC.
    actual = datetime.now(UTC)
    now = actual.replace(hour=15, minute=0, second=0, microsecond=0)
    assert now.weekday() < 5  # This fixture uses the reviewed 2026-11-10 session.
    async with factory() as db:
        originals = (await db.execute(select(StockInstrument))).scalars().all()
        saved = [(r.coin_id, r.provider_asset_id, r.provider_verified_at) for r in originals]
        for row in originals:
            row.provider_asset_id = f"synthetic-{row.coin_id}"
            row.provider_verified_at = now - timedelta(days=1)
        for product in ("quotes", "reference"):
            authority = replace(
                admitted(product), reviewed_at=now - timedelta(hours=1),
                valid_from=now - timedelta(hours=2), valid_until=max(now, actual) + timedelta(hours=8),
            )
            db.add(StockDataAdmission(**asdict(authority)))
        authority = evidence(now)
        authority = replace(authority, valid_until=max(now, actual) + timedelta(hours=8))
        # Keep reviewed calendar valid under actual DB wall clock too.
        authority = replace(authority, calendar={**authority.calendar,
            "review_valid_until": (max(now, actual) + timedelta(hours=2)).isoformat()})
        db.add(StockDataAdmission(**asdict(authority)))
        await db.commit()
        mappings = await load_stock_catalog(db)
    settings = SchedulerSettings(
        env="test", database_url=str(engine.url), redis_url="redis://:test@127.0.0.1:56379/0",
        stock_data_enabled=True, alpaca_api_key="synthetic-key", alpaca_secret_key="synthetic-secret",
        stock_max_retries=0,
    )
    yield {"factory": factory, "now": now, "mappings": mappings, "settings": settings}
    async with factory() as db:
        for coin_id, provider_id, verified_at in saved:
            await db.execute(update(StockInstrument).where(StockInstrument.coin_id == coin_id)
                .values(provider_asset_id=provider_id, provider_verified_at=verified_at))
        await db.commit()


def body(state: dict, count: int = 20) -> dict:
    return {"quotes": {m.symbol: {"bp": 100, "ap": 102, "t": state["now"].isoformat(),
        "c": ["R"], "bx": "V", "ax": "V", "bs": 1, "as": 1,
        "z": "C" if m.listing_exchange == "NASDAQ" else "A"}
        for m in state["mappings"][:count]}}


async def cycle(state: dict, redis: Redis, http: httpx.AsyncClient):
    return await stock_scheduler.run_stock_cycle(sessionmaker=state["factory"], redis=redis,
        http=http, settings=state["settings"], now=lambda: state["now"])


async def rows(state: dict, model=StockQuote):
    async with state["factory"]() as db:
        return (await db.execute(select(model))).scalars().all()


async def test_permitted_batch_persists_source_times_without_idle_http_transaction(
    state: dict, redis_client: Redis,
) -> None:
    async def respond(request):
        async with state["factory"]() as db:
            idle = await db.scalar(text("SELECT count(*) FROM pg_stat_activity WHERE datname = "
                "current_database() AND state = 'idle in transaction'"))
            assert idle == 0
        assert len(request.url.params["symbols"].split(",")) == 20
        return httpx.Response(200, json=body(state))
    with respx.mock as router:
        route = router.get(LATEST_QUOTES_URL).mock(side_effect=respond)
        async with httpx.AsyncClient() as http:
            result = await cycle(state, redis_client, http)
    assert route.call_count == 1
    assert result.accepted == 20
    stored = await rows(state)
    assert len(stored) == 20
    assert all(r.event_at == r.collected_at == state["now"] for r in stored)
    assert len(await rows(state, StockSession)) == 272
    assert await redis_client.exists(stock_scheduler.LOCK_KEY) == 0


@pytest.mark.parametrize("problem", ["disabled", "quote_denied", "retention_denied",
    "derived_denied", "reference_denied", "calendar_denied", "unverified", "closed", "quota"])
async def test_no_call_without_every_collection_prerequisite(state: dict, redis_client: Redis, problem: str):
    if problem == "disabled":
        state["settings"] = state["settings"].model_copy(update={"stock_data_enabled": False})
    elif problem == "closed":
        state["now"] = state["now"].replace(hour=23)
    else:
        async with state["factory"]() as db:
            if problem == "unverified":
                await db.execute(update(StockInstrument).values(provider_verified_at=None))
            else:
                product = "reference" if problem == "reference_denied" else "calendar" if problem == "calendar_denied" else "quotes"
                values = {"state": "denied"}
                if problem == "retention_denied": values = {"retention_allowed": False}
                if problem == "derived_denied": values = {"derived_allowed": False}
                if problem == "quota": values = {"quota": {**admitted().quota, "requests_per_minute": 1}}
                await db.execute(update(StockDataAdmission).where(StockDataAdmission.product == product).values(**values))
            await db.commit()
    with respx.mock as router:
        route = router.get(LATEST_QUOTES_URL).respond(200, json=body(state))
        async with httpx.AsyncClient() as http:
            await cycle(state, redis_client, http)
    assert route.call_count == 0
    assert await rows(state) == []


@pytest.mark.parametrize("status", [403, 429, 500])
async def test_provider_failures_keep_data_and_release_lease(state: dict, redis_client: Redis, status: int):
    with respx.mock as router:
        route = router.get(LATEST_QUOTES_URL).respond(status)
        async with httpx.AsyncClient() as http:
            result = await cycle(state, redis_client, http)
    assert route.call_count == 1
    assert result.status == "source_error"
    assert await rows(state) == []
    assert await redis_client.exists(stock_scheduler.LOCK_KEY) == 0


async def test_partial_batch_preserves_missing_symbols_and_is_rate_bounded(state: dict, redis_client: Redis):
    with respx.mock as router:
        route = router.get(LATEST_QUOTES_URL).respond(200, json=body(state, 2))
        async with httpx.AsyncClient() as http:
            first = await cycle(state, redis_client, http)
            await cycle(state, redis_client, http)
    assert first.accepted == 2
    assert first.rejected == 18
    assert route.call_count == 1
    assert len(await rows(state)) == 2


@pytest.mark.parametrize("product", ["quotes", "calendar", "reference"])
async def test_midflight_revocation_discards_batch(state: dict, redis_client: Redis, product: str):
    async def revoke(request):
        async with state["factory"]() as db:
            await db.execute(update(StockDataAdmission).where(StockDataAdmission.product == product)
                .values(state="revoked", generation=5))
            await db.commit()
        return httpx.Response(200, json=body(state))
    with respx.mock as router:
        router.get(LATEST_QUOTES_URL).mock(side_effect=revoke)
        async with httpx.AsyncClient() as http:
            await cycle(state, redis_client, http)
    assert await rows(state) == []


async def test_expired_or_replaced_lease_cannot_write_or_release_another_owner(state: dict, redis_client: Redis):
    async def steal(request):
        await redis_client.set(stock_scheduler.LOCK_KEY, "new-owner", px=30000)
        return httpx.Response(200, json=body(state))
    with respx.mock as router:
        router.get(LATEST_QUOTES_URL).mock(side_effect=steal)
        async with httpx.AsyncClient() as http:
            await cycle(state, redis_client, http)
    assert await rows(state) == []
    assert await redis_client.get(stock_scheduler.LOCK_KEY) == "new-owner"


async def test_shutdown_cancellation_releases_lease(state: dict, redis_client: Redis):
    started = asyncio.Event()
    async def hang(request):
        started.set()
        await asyncio.Event().wait()
    with respx.mock as router:
        router.get(LATEST_QUOTES_URL).mock(side_effect=hang)
        async with httpx.AsyncClient() as http:
            task = asyncio.create_task(cycle(state, redis_client, http))
            try:
                await asyncio.wait_for(started.wait(), 5)
            finally:
                task.cancel()
            with pytest.raises(asyncio.CancelledError): await task
    assert await redis_client.exists(stock_scheduler.LOCK_KEY) == 0


async def test_unavailable_redis_never_calls_provider(state: dict):
    dead = Redis.from_url("redis://127.0.0.1:1", socket_connect_timeout=1)
    try:
        with respx.mock as router:
            route = router.get(LATEST_QUOTES_URL).respond(200, json=body(state))
            async with httpx.AsyncClient() as http:
                result = await cycle(state, dead, http)
        assert result.status == "lock_error"
        assert route.call_count == 0
    finally:
        await dead.aclose()
