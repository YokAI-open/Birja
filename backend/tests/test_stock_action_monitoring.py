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
from tests.test_stock_admission import action_admitted, admitted
from tests.test_stock_sessions import evidence


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
