"""Real PostgreSQL continuity; private provider traffic is always mocked."""

from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import pytest_asyncio
import respx
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import SchedulerSettings
from app.models.corporate_action import (
    StockActionEvent,
    StockActionObservation,
    StockActionRevision,
    StockActionSource,
    StockActionState,
    StockDividendEntitlement,
)
from app.models.stock import StockDataAdmission, StockInstrument
from app.tasks import stock_actions
from app.tasks import stock_scheduler
from tests.test_stock_admission import action_admitted, admitted
from tests.test_stock_sessions import evidence


@pytest_asyncio.fixture(autouse=True)
async def clean_account_attempts(redis_client):
    async for key in redis_client.scan_iter(match=stock_scheduler.ACCOUNT_WINDOW_PREFIX + "*"):
        await redis_client.delete(key)
    yield
    async for key in redis_client.scan_iter(match=stock_scheduler.ACCOUNT_WINDOW_PREFIX + "*"):
        await redis_client.delete(key)


@pytest_asyncio.fixture
async def monitor(engine, clean_stock_discovery, redis_client):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)
    baseline = now - timedelta(days=2)
    async with factory.begin() as db:
        rows = (await db.execute(select(StockInstrument))).scalars().all()
        saved = [(r.coin_id, r.provider_asset_id, r.provider_verified_at) for r in rows]
        for row in rows:
            row.provider_asset_id = f"synthetic-{row.coin_id}"
            row.provider_verified_at = baseline - timedelta(days=1)
        for auth in (action_admitted(), evidence(now), admitted("reference")):
            db.add(
                StockDataAdmission(
                    **asdict(
                        replace(
                            auth,
                            reviewed_at=now - timedelta(hours=1),
                            valid_from=now - timedelta(hours=2),
                            valid_until=now + timedelta(hours=2),
                            quota={**auth.quota, "requests_per_minute": 200},
                        )
                    )
                )
            )
    settings = SchedulerSettings(
        env="test",
        database_url=str(engine.url),
        redis_url="redis://:test@127.0.0.1:56379/0",
        alpaca_api_key="synthetic",
        alpaca_secret_key="synthetic",
    )
    settings = settings.model_copy(
        update={
            "stock_actions_enabled": True,
            "stock_actions_coverage_start": baseline,
            "stock_actions_segment_days": 100,
        }
    )
    try:
        yield factory, settings, baseline
    finally:
        async with factory.begin() as db:
            for model in (StockActionObservation, StockDividendEntitlement):
                await db.execute(delete(model))
            await db.execute(update(StockActionEvent).values(current_revision_id=None))
            await db.execute(delete(StockActionRevision))
            await db.execute(delete(StockActionSource))
            await db.execute(delete(StockActionEvent))
            await db.execute(delete(StockActionState))
            for cid, pid, checked in saved:
                await db.execute(
                    update(StockInstrument)
                    .where(StockInstrument.coin_id == cid)
                    .values(provider_asset_id=pid, provider_verified_at=checked)
                )
        async for key in redis_client.scan_iter(match="sim:stock:actions:*"):
            await redis_client.delete(key)


async def states(factory):
    async with factory() as db:
        return (
            (await db.execute(select(StockActionState).order_by(StockActionState.coin_id)))
            .scalars()
            .all()
        )


async def cycle(monitor, redis, http):
    factory, settings, _ = monitor
    return await stock_actions.run_stock_action_cycle(
        sessionmaker=factory, redis=redis, http=http, settings=settings
    )


async def test_complete_snapshot_and_replay_publish_twenty_durable_current_states(
    monitor, redis_client
):
    with respx.mock(assert_all_called=False) as router:
        router.get("https://data.alpaca.markets/v1/corporate-actions").respond(
            200, json={"corporate_actions": {}, "next_page_token": None}
        )
        router.get(url__startswith="https://stream.data.alpaca.markets/").respond(
            200, content=b"", headers={"content-type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            result = await cycle(monitor, redis_client, http)
    rows = await states(monitor[0])
    assert len(rows) == 20
    assert all(row.health == "current" for row in rows), [
        (r.health, r.staged_continuation) for r in rows[:1]
    ]
    assert all(row.covered_until > monitor[2] for row in rows)
    assert result.status == "ok"


def routes(router, *, rest_status=200, replay_status=200, body=None):
    rest = router.get("https://data.alpaca.markets/v1/corporate-actions").respond(
        rest_status, json=body or {"corporate_actions": {}, "next_page_token": None}
    )
    replay = router.get(url__startswith="https://stream.data.alpaca.markets/").respond(
        replay_status, content=b"", headers={"content-type": "text/event-stream"}
    )
    return rest, replay


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500])
async def test_failed_replay_never_publishes_current(monitor, redis_client, status):
    with respx.mock(assert_all_called=False) as router:
        routes(router, replay_status=status)
        async with httpx.AsyncClient(trust_env=False) as http:
            result = await cycle(monitor, redis_client, http)
    rows = await states(monitor[0])
    assert result.status == "source_error"
    assert len(rows) == 20 and all(r.health == "reconciling" for r in rows)
    assert all(r.covered_until is None and r.valid_until is None for r in rows)


async def test_durable_segments_resume_until_future_horizon_complete(monitor, redis_client):
    factory, settings, _ = monitor
    settings.stock_actions_segment_days = 31
    with respx.mock(assert_all_called=False) as router:
        rest, _ = routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            starts = []
            for _index in range(2):
                await redis_client.delete(stock_actions.WINDOW_KEY)
                assert (await cycle(monitor, redis_client, http)).status == "source_error"
                rows = await states(factory)
                assert all(r.health == "reconciling" and r.valid_until is None for r in rows)
                starts.append(rest.calls.last.request.url.params["start"])
            await redis_client.delete(stock_actions.WINDOW_KEY)
            assert (await cycle(monitor, redis_client, http)).status == "ok"
            assert len(set(starts)) == 2
    assert all(r.health == "current" for r in await states(factory))


async def test_incomplete_pagination_keeps_start_and_records_continuation(monitor, redis_client):
    with respx.mock(assert_all_called=False) as router:
        routes(router, body={"corporate_actions": {}, "next_page_token": "same-page"})
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
    rows = await states(monitor[0])
    assert all(r.staged_continuation["next_date"] == monitor[2].date().isoformat() for r in rows)
    assert all(r.health == "reconciling" for r in rows)


@pytest.mark.parametrize("product", ["actions", "calendar", "reference"])
async def test_revoked_rights_create_no_http_or_monitor_authority(monitor, redis_client, product):
    async with monitor[0].begin() as db:
        await db.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == product)
            .values(collection_allowed=False)
        )
    with respx.mock() as router:
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
        assert not router.calls
    assert not await states(monitor[0])


async def test_disabled_needs_no_datastore_or_provider(monitor, redis_client):
    monitor[1].stock_actions_enabled = False
    async with httpx.AsyncClient(trust_env=False) as http:
        assert (await cycle(monitor, redis_client, http)).status == "ok"
    assert not await states(monitor[0])


@pytest.mark.parametrize("key", [stock_actions.LOCK_KEY, stock_actions.WINDOW_KEY])
async def test_duplicate_cycle_and_cadence_are_independently_owned(monitor, redis_client, key):
    await redis_client.set(key, "other", px=60000)
    async with httpx.AsyncClient(trust_env=False) as http:
        assert (await cycle(monitor, redis_client, http)).status == "locked"
    assert await redis_client.get(key) == "other"


async def test_shared_account_budget_counts_real_attempts_and_rejects_excess(monitor, redis_client):
    from app.tasks.stock_scheduler import _admissions, reserve_account_attempt

    settings = monitor[1]
    settings.stock_account_requests_per_minute = 2
    async with monitor[0]() as db:
        auth = await _admissions(db)
    assert await reserve_account_attempt(redis_client, settings, auth)
    with respx.mock(assert_all_called=False) as router:
        rest, replay = routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
            assert http.event_hooks["request"] == []
    assert rest.call_count == 1 and replay.call_count == 0
    assert all(row.health == "reconciling" for row in await states(monitor[0]))
    assert not await reserve_account_attempt(redis_client, settings, auth)


async def test_account_budget_is_atomic_across_concurrent_products(monitor, redis_client):
    import asyncio
    from app.tasks.stock_scheduler import _admissions, reserve_account_attempt

    settings = monitor[1]
    settings.stock_account_requests_per_minute = 3
    async with monitor[0]() as db:
        auth = await _admissions(db)
    results = await asyncio.gather(
        *(reserve_account_attempt(redis_client, settings, auth) for _ in range(12))
    )
    assert sum(results) == 3
    settings.stock_data_account = "other-account"
    assert await reserve_account_attempt(redis_client, settings, auth)


@pytest.mark.parametrize("phase", ["acquire", "release"])
async def test_redis_failure_is_bounded_and_sanitized(monitor, redis_client, monkeypatch, phase):
    from redis.exceptions import RedisError

    async def failed(*args, **kwargs):
        raise RedisError("private-credential-never-log")

    monkeypatch.setattr(redis_client, "set" if phase == "acquire" else "eval", failed)
    with respx.mock(assert_all_called=False) as router:
        routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            result = await cycle(monitor, redis_client, http)
    assert result.status == ("lock_error" if phase == "acquire" else "source_error")


async def test_hung_source_cancels_and_releases_only_own_lease(monitor, redis_client):
    import asyncio

    entered = asyncio.Event()

    async def hang(request):
        entered.set()
        await asyncio.Event().wait()

    with respx.mock() as router:
        router.get("https://data.alpaca.markets/v1/corporate-actions").mock(side_effect=hang)
        async with httpx.AsyncClient(trust_env=False) as http:
            task = asyncio.create_task(cycle(monitor, redis_client, http))
            await asyncio.wait_for(entered.wait(), 3)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert http.event_hooks["request"] == []
    assert not await redis_client.exists(stock_actions.LOCK_KEY)
    assert all(r.health == "reconciling" for r in await states(monitor[0]))


async def test_health_deadline_never_outlives_reviewed_calendar(monitor, redis_client):
    reviewed_until = datetime.now(UTC) + timedelta(seconds=10)
    async with monitor[0].begin() as db:
        row = (await db.execute(select(StockDataAdmission).where(
            StockDataAdmission.product == "calendar"))).scalar_one()
        row.calendar = {**row.calendar, "review_valid_until": reviewed_until.isoformat()}
    with respx.mock() as router:
        routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "ok"
    assert all(r.valid_until == reviewed_until for r in await states(monitor[0]))


def mixed_body():
    from uuid import UUID
    today = datetime.now(UTC).date()
    base = {"symbol": "AAPL", "cusip": "037833100", "process_date": today.isoformat(),
        "ex_date": (today + timedelta(days=2)).isoformat()}
    return {"corporate_actions": {
        "cash_dividends": [{**base, "id": str(UUID(int=1)), "rate": 1,
            "currency": "USD", "foreign": False, "special": False,
            "record_date": base["ex_date"], "payable_date": (today + timedelta(days=5)).isoformat()}],
        "forward_splits": [{**base, "id": str(UUID(int=2)), "old_rate": 1, "new_rate": 2}],
        "reverse_splits": [{**base, "id": str(UUID(int=3)), "old_rate": 2, "new_rate": 1}],
    }, "next_page_token": None}


async def test_mixed_events_only_cash_dividends_receive_entitlement_derivation(monitor, redis_client):
    from app.services.corporate_actions import persistent_action_holds
    with respx.mock() as router:
        routes(router, body=mixed_body())
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "ok"
    async with monitor[0]() as db:
        event = (await db.execute(select(StockActionEvent).limit(1))).scalar_one()
        assert await persistent_action_holds(db, event.coin_id)
    assert len(await states(monitor[0])) == 20
