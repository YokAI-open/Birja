"""Real isolated datastore cycles; only provider HTTP is replaced."""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import exchange_calendars as calendars
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


@pytest_asyncio.fixture(autouse=True)
async def clean_account_attempts(redis_client):
    async for key in redis_client.scan_iter(match=stock_scheduler.ACCOUNT_WINDOW_PREFIX + "*"):
        await redis_client.delete(key)
    yield
    async for key in redis_client.scan_iter(match=stock_scheduler.ACCOUNT_WINDOW_PREFIX + "*"):
        await redis_client.delete(key)


def next_regular_clock(actual: datetime) -> datetime:
    now = actual.replace(hour=15, minute=0, second=0, microsecond=0)
    calendar = calendars.get_calendar(
        "XNYS", start=now.date().isoformat(), end=(now.date() + timedelta(days=14)).isoformat()
    )
    open_dates = {stamp.date() for stamp in calendar.sessions}
    while now.date() not in open_dates:
        now += timedelta(days=1)
    return now


@pytest.mark.parametrize(
    "day,expected",
    [("2026-11-26", "2026-11-27"), ("2026-12-25", "2026-12-28"), ("2026-11-14", "2026-11-16")],
)
def test_scheduler_fixture_selects_verified_session(day, expected):
    assert (
        next_regular_clock(datetime.fromisoformat(day + "T15:00:00+00:00")).date().isoformat()
        == expected
    )


@pytest_asyncio.fixture
async def state(
    engine: AsyncEngine, clean_stock_discovery: None, redis_client: Redis
) -> AsyncIterator[dict]:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    await redis_client.delete(stock_scheduler.WINDOW_KEY)
    # Fixed open-session clock; expiry guards additionally use actual DB UTC.
    actual = datetime.now(UTC)
    now = next_regular_clock(actual)
    async with factory() as db:
        originals = (await db.execute(select(StockInstrument))).scalars().all()
        saved = [(r.coin_id, r.provider_asset_id, r.provider_verified_at) for r in originals]
        for row in originals:
            row.provider_asset_id = f"synthetic-{row.coin_id}"
            row.provider_verified_at = now - timedelta(days=1)
        for product in ("quotes", "reference"):
            authority = replace(
                admitted(product),
                reviewed_at=now - timedelta(hours=1),
                valid_from=min(now, actual) - timedelta(hours=2),
                valid_until=max(now, actual) + timedelta(hours=8),
            )
            db.add(StockDataAdmission(**asdict(authority)))
        authority = evidence(now)
        authority = replace(
            authority,
            valid_from=min(now, actual) - timedelta(hours=2),
            valid_until=max(now, actual) + timedelta(hours=8),
        )
        # Keep reviewed calendar valid under actual DB wall clock too.
        authority = replace(
            authority,
            calendar={
                **authority.calendar,
                "review_valid_until": max(
                    now + timedelta(hours=8), actual + timedelta(hours=2)
                ).isoformat(),
            },
        )
        db.add(StockDataAdmission(**asdict(authority)))
        await db.commit()
        mappings = await load_stock_catalog(db)
    settings = SchedulerSettings(
        env="test",
        database_url=str(engine.url),
        redis_url="redis://:test@127.0.0.1:56379/0",
        stock_data_enabled=True,
        alpaca_api_key="synthetic-key",
        alpaca_secret_key="synthetic-secret",
        stock_max_retries=0,
    )
    yield {"factory": factory, "now": now, "mappings": mappings, "settings": settings}
    await redis_client.delete(stock_scheduler.WINDOW_KEY)
    async with factory() as db:
        for coin_id, provider_id, verified_at in saved:
            await db.execute(
                update(StockInstrument)
                .where(StockInstrument.coin_id == coin_id)
                .values(provider_asset_id=provider_id, provider_verified_at=verified_at)
            )
        await db.commit()


def body(state: dict, count: int = 20) -> dict:
    return {
        "quotes": {
            m.symbol: {
                "bp": 100,
                "ap": 102,
                "t": state["now"].isoformat(),
                "c": ["R"],
                "bx": "V",
                "ax": "V",
                "bs": 1,
                "as": 1,
                "z": "C" if m.listing_exchange == "NASDAQ" else "A",
            }
            for m in state["mappings"][:count]
        }
    }


async def cycle(state: dict, redis: Redis, http: httpx.AsyncClient):
    return await stock_scheduler.run_stock_cycle(
        sessionmaker=state["factory"],
        redis=redis,
        http=http,
        settings=state["settings"],
        now=lambda: state["now"],
    )


async def test_configured_budget_bounds_pre_fetch_work(state, redis_client, monkeypatch):
    async def hang(*args, **kwargs):
        await asyncio.sleep(1.05)
        return stock_scheduler.CycleResult("ok")

    monkeypatch.setattr(stock_scheduler, "_refresh", hang)
    state["settings"] = state["settings"].model_copy(update={"stock_cycle_budget_seconds": 1})
    async with httpx.AsyncClient() as http:
        result = await cycle(state, redis_client, http)
    assert result.status == "source_error"
    assert not await redis_client.exists(stock_scheduler.LOCK_KEY)


async def test_configured_budget_cancels_post_fetch_write_and_rolls_back(
    state, redis_client, monkeypatch
):
    original = stock_scheduler.upsert_stock_quotes

    async def held(*args, **kwargs):
        count = await original(*args, **kwargs)
        assert count == 20
        await asyncio.sleep(1.1)
        return count

    monkeypatch.setattr(stock_scheduler, "upsert_stock_quotes", held)
    state["settings"] = state["settings"].model_copy(update={"stock_cycle_budget_seconds": 1})
    with respx.mock as router:
        router.get(LATEST_QUOTES_URL).respond(200, json=body(state))
        async with httpx.AsyncClient() as http:
            result = await cycle(state, redis_client, http)
    assert result.status == "source_error"
    assert not await rows(state)
    assert not await redis_client.exists(stock_scheduler.LOCK_KEY)


async def test_nondefault_configured_scope_survives_every_nested_check(state, redis_client):
    scope = {"account": "reviewed-account", "server": "reviewed-server"}
    async with state["factory"]() as db:
        await db.execute(update(StockDataAdmission).values(scope={**admitted().scope, **scope}))
        await db.commit()
    state["settings"] = state["settings"].model_copy(
        update={"stock_data_account": scope["account"], "stock_data_server": scope["server"]}
    )
    with respx.mock as router:
        route = router.get(LATEST_QUOTES_URL).respond(200, json=body(state))
        async with httpx.AsyncClient() as http:
            result = await cycle(state, redis_client, http)
    assert result.accepted == 20
    assert route.call_count == 1


async def rows(state: dict, model=StockQuote):
    async with state["factory"]() as db:
        return (await db.execute(select(model))).scalars().all()


@pytest.mark.parametrize("boundary", ["calendar_build", "session_persist", "lease"])
async def test_calendar_async_boundaries_recheck_authority_and_lease(
    state, redis_client, monkeypatch, boundary
):
    import threading

    entered, release = threading.Event(), threading.Event()
    if boundary == "calendar_build":
        original = stock_scheduler.build_sessions

        def held(*args, **kwargs):
            result = original(*args, **kwargs)
            entered.set()
            assert release.wait(5)
            return result

        monkeypatch.setattr(stock_scheduler, "build_sessions", held)
    else:
        original = stock_scheduler.persist_sessions

        async def held(*args, **kwargs):
            result = await original(*args, **kwargs)
            entered.set()
            if boundary == "lease":
                await redis_client.set(stock_scheduler.LOCK_KEY, "replacement", px=1000)
            else:
                # DB-clock/authority is re-read after the awaited derived write.
                await args[0].execute(
                    update(StockDataAdmission)
                    .where(StockDataAdmission.product == "calendar")
                    .values(state="revoked")
                )
            return result

        monkeypatch.setattr(stock_scheduler, "persist_sessions", held)
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: pytest.fail("must not fetch"))
    ) as http:
        task = asyncio.create_task(cycle(state, redis_client, http))
        try:
            if boundary == "calendar_build":
                assert await asyncio.to_thread(entered.wait, 5)
                async with state["factory"]() as db:
                    await db.execute(
                        update(StockDataAdmission)
                        .where(StockDataAdmission.product == "calendar")
                        .values(state="revoked")
                    )
                    await db.commit()
                release.set()
            result = await asyncio.wait_for(task, 5)
        finally:
            release.set()
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
    assert result.status == ("locked" if boundary == "lease" else "ok")
    assert not await rows(state)
    if boundary == "lease":
        assert await redis_client.get(stock_scheduler.LOCK_KEY) == "replacement"
        await redis_client.delete(stock_scheduler.LOCK_KEY)


async def test_redis_release_failure_is_safe_and_sanitized(
    state, redis_client, monkeypatch, caplog
):
    from redis.exceptions import RedisError

    async def fail(*args, **kwargs):
        raise RedisError("secret-provider-token")

    monkeypatch.setattr(redis_client, "eval", fail)
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body(state)))
    ) as http:
        await cycle(state, redis_client, http)
    assert "stock lock release failed" in caplog.text
    assert "secret-provider-token" not in caplog.text


async def test_permitted_batch_persists_source_times_without_idle_http_transaction(
    state: dict,
    redis_client: Redis,
) -> None:
    async def respond(request):
        async with state["factory"]() as db:
            idle = await db.scalar(
                text(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = "
                    "current_database() AND state = 'idle in transaction'"
                )
            )
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


@pytest.mark.parametrize(
    "problem",
    [
        "disabled",
        "quote_denied",
        "retention_denied",
        "derived_denied",
        "reference_denied",
        "calendar_denied",
        "unverified",
        "closed",
    ],
)
async def test_no_call_without_every_collection_prerequisite(
    state: dict, redis_client: Redis, problem: str
):
    if problem == "disabled":
        state["settings"] = state["settings"].model_copy(update={"stock_data_enabled": False})
    elif problem == "closed":
        state["now"] = state["now"].replace(hour=23)
    else:
        async with state["factory"]() as db:
            if problem == "unverified":
                await db.execute(update(StockInstrument).values(provider_verified_at=None))
            else:
                product = (
                    "reference"
                    if problem == "reference_denied"
                    else "calendar"
                    if problem == "calendar_denied"
                    else "quotes"
                )
                values = {"state": "denied"}
                if problem == "retention_denied":
                    values = {"retention_allowed": False}
                if problem == "derived_denied":
                    values = {"derived_allowed": False}
                await db.execute(
                    update(StockDataAdmission)
                    .where(StockDataAdmission.product == product)
                    .values(**values)
                )
            await db.commit()
    with respx.mock as router:
        route = router.get(LATEST_QUOTES_URL).respond(200, json=body(state))
        async with httpx.AsyncClient() as http:
            await cycle(state, redis_client, http)
    assert route.call_count == 0
    assert await rows(state) == []


async def test_quote_collection_ignores_unrelated_denied_product_quota(state, redis_client):
    authority = replace(admitted("status"), state="denied", quota={})
    async with state["factory"].begin() as db:
        db.add(StockDataAdmission(**asdict(authority)))
    with respx.mock() as router:
        route = router.get(LATEST_QUOTES_URL).respond(200, json=body(state))
        async with httpx.AsyncClient(trust_env=False) as http:
            result = await cycle(state, redis_client, http)
    assert result.accepted == 20 and route.call_count == 1


async def test_one_request_quota_allows_one_actual_quote_attempt(state, redis_client):
    async with state["factory"].begin() as db:
        await db.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "quotes")
            .values(quota={**admitted().quota, "requests_per_minute": 1})
        )
    with respx.mock() as router:
        route = router.get(LATEST_QUOTES_URL).respond(200, json=body(state))
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(state, redis_client, http)).accepted == 20
            await redis_client.delete(stock_scheduler.WINDOW_KEY)
            assert (await cycle(state, redis_client, http)).status == "source_error"
    assert route.call_count == 1


@pytest.mark.parametrize("status", [403, 429, 500])
async def test_provider_failures_keep_data_and_release_lease(
    state: dict, redis_client: Redis, status: int
):
    with respx.mock as router:
        route = router.get(LATEST_QUOTES_URL).respond(200, json=body(state))
        async with httpx.AsyncClient() as http:
            first = await cycle(state, redis_client, http)
            assert first.accepted == 20
            before = [(r.coin_id, r.mid, r.event_at, r.collected_at) for r in await rows(state)]
            await redis_client.delete(stock_scheduler.WINDOW_KEY)
            route.respond(status)
            result = await cycle(state, redis_client, http)
    assert route.call_count == 2
    assert result.status == "source_error"
    assert [(r.coin_id, r.mid, r.event_at, r.collected_at) for r in await rows(state)] == before
    assert await redis_client.exists(stock_scheduler.LOCK_KEY) == 0


async def test_partial_batch_preserves_missing_symbols_and_is_rate_bounded(
    state: dict, redis_client: Redis
):
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
            await db.execute(
                update(StockDataAdmission)
                .where(StockDataAdmission.product == product)
                .values(state="revoked", generation=5)
            )
            await db.commit()
        return httpx.Response(200, json=body(state))

    with respx.mock as router:
        router.get(LATEST_QUOTES_URL).mock(side_effect=revoke)
        async with httpx.AsyncClient() as http:
            await cycle(state, redis_client, http)
    assert await rows(state) == []


async def test_expired_or_replaced_lease_cannot_write_or_release_another_owner(
    state: dict, redis_client: Redis
):
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
            with pytest.raises(asyncio.CancelledError):
                await task
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


async def test_existing_stock_lease_does_not_touch_crypto_lock(state: dict, redis_client: Redis):
    await redis_client.set(stock_scheduler.LOCK_KEY, "other", px=30000)
    await redis_client.set("sim:lock:price-refresh", "crypto-owner", px=30000)
    with respx.mock as router:
        route = router.get(LATEST_QUOTES_URL).respond(200, json=body(state))
        async with httpx.AsyncClient() as http:
            result = await cycle(state, redis_client, http)
    assert result.status == "locked"
    assert route.call_count == 0
    assert await redis_client.get("sim:lock:price-refresh") == "crypto-owner"


@pytest.mark.parametrize("change", ["expired_lease", "close", "expired_calendar", "mapping"])
async def test_post_http_time_and_identity_changes_refuse_batch(
    state: dict, redis_client: Redis, change: str
):
    async def change_boundary(request):
        if change == "expired_lease":
            await redis_client.pexpire(stock_scheduler.LOCK_KEY, 1)
            await asyncio.sleep(0.01)
        elif change == "close":
            state["now"] = state["now"].replace(hour=21)
        else:
            async with state["factory"]() as db:
                if change == "mapping":
                    await db.execute(update(StockInstrument).values(provider_verified_at=None))
                else:
                    row = (
                        await db.execute(
                            select(StockDataAdmission).where(
                                StockDataAdmission.product == "calendar"
                            )
                        )
                    ).scalar_one()
                    row.calendar = {**row.calendar, "review_valid_until": state["now"].isoformat()}
                await db.commit()
        return httpx.Response(200, json=body(state))

    with respx.mock as router:
        router.get(LATEST_QUOTES_URL).mock(side_effect=change_boundary)
        async with httpx.AsyncClient() as http:
            await cycle(state, redis_client, http)
    assert await rows(state) == []


async def test_retry_reloads_committed_admission_before_another_call(
    state: dict, redis_client: Redis
):
    state["settings"] = state["settings"].model_copy(update={"stock_max_retries": 1})

    async def revoke(request):
        async with state["factory"]() as db:
            await db.execute(
                update(StockDataAdmission)
                .where(StockDataAdmission.product == "quotes")
                .values(state="revoked", generation=5)
            )
            await db.commit()
        return httpx.Response(429)

    with respx.mock as router:
        route = router.get(LATEST_QUOTES_URL).mock(side_effect=revoke)
        async with httpx.AsyncClient() as http:
            result = await cycle(state, redis_client, http)
            assert not http.event_hooks["request"]
    assert route.call_count == 1
    assert result.status == "source_error"
    assert await rows(state) == []


async def test_cycle_deadline_bounds_hanging_source(
    state: dict, redis_client: Redis, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(stock_scheduler, "CYCLE_TIMEOUT_S", 0.25)

    async def hang(request):
        await asyncio.Event().wait()

    with respx.mock as router:
        router.get(LATEST_QUOTES_URL).mock(side_effect=hang)
        async with httpx.AsyncClient() as http:
            async with asyncio.timeout(2):
                result = await cycle(state, redis_client, http)
    assert result.status == "source_error"
    assert await redis_client.exists(stock_scheduler.LOCK_KEY) == 0


async def test_closed_day_refresh_does_not_renew_calendar_review(state: dict, redis_client: Redis):
    state["now"] = state["now"].replace(hour=21)
    before = next(row for row in await rows(state, StockDataAdmission) if row.product == "calendar")
    with respx.mock as router:
        route = router.get(LATEST_QUOTES_URL).respond(200, json=body(state))
        async with httpx.AsyncClient() as http:
            await cycle(state, redis_client, http)
    assert route.call_count == 0
    assert len(await rows(state, StockSession)) == 272
    after = next(row for row in await rows(state, StockDataAdmission) if row.product == "calendar")
    assert before.reviewed_at == after.reviewed_at
    assert before.calendar == after.calendar
    assert before.generation == after.generation


async def test_hanging_stock_http_keeps_real_crypto_ticks_and_both_leases_release(
    state: dict, redis_client: Redis, clean_prices: None, tmp_path: Path
):
    from app.services.kraken import TICKER_URL
    from app.tasks import scheduler
    from tests.test_scheduler import _body

    stock_entered = asyncio.Event()
    third_crypto = asyncio.Event()
    stop = asyncio.Event()
    crypto_ticks = []

    async def stock_hang(request):
        stock_entered.set()
        await asyncio.Event().wait()

    async def crypto_reply(request):
        assert "APCA-API-KEY-ID" not in request.headers
        crypto_ticks.append(asyncio.get_running_loop().time())
        await stock_entered.wait()
        if len(crypto_ticks) == 3:
            third_crypto.set()
            await asyncio.Event().wait()
        return httpx.Response(200, json=_body())

    with respx.mock as router:
        router.get(LATEST_QUOTES_URL).mock(side_effect=stock_hang)
        router.get(TICKER_URL).mock(side_effect=crypto_reply)
        async with httpx.AsyncClient() as crypto_http, httpx.AsyncClient() as stock_http:
            candidates = {}

            async def crypto_cycle():
                return await scheduler.run_cycle(
                    sessionmaker=state["factory"],
                    redis=redis_client,
                    source=scheduler.build_source(state["settings"], crypto_http),
                    settings=state["settings"],
                    candidates=candidates,
                    now=lambda: state["now"],
                )

            async def stock_cycle():
                return await cycle(state, redis_client, stock_http)

            async with asyncio.TaskGroup() as group:
                group.create_task(
                    scheduler.run(
                        cycle=crypto_cycle,
                        interval=0.04,
                        stop=stop,
                        heartbeat=tmp_path / "heartbeat",
                    )
                )
                group.create_task(
                    scheduler.run(
                        cycle=stock_cycle, interval=60, stop=stop, heartbeat=tmp_path / "heartbeat"
                    )
                )
                try:
                    await asyncio.wait_for(third_crypto.wait(), 5)
                    assert await redis_client.exists(scheduler.LOCK_KEY) == 1
                    assert await redis_client.exists(stock_scheduler.LOCK_KEY) == 1
                    assert (tmp_path / "heartbeat").exists()
                finally:
                    stop.set()
    assert len(crypto_ticks) == 3
    assert crypto_ticks[-1] - crypto_ticks[1] < 1
    assert await redis_client.exists(scheduler.LOCK_KEY) == 0
    assert await redis_client.exists(stock_scheduler.LOCK_KEY) == 0
