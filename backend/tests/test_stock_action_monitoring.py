"""Real PostgreSQL continuity; private provider traffic is always mocked."""

from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta

import httpx
import pytest_asyncio
import respx
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import SchedulerSettings
from app.models.corporate_action import StockActionState
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
            db.add(StockDataAdmission(**asdict(replace(
                auth, reviewed_at=baseline - timedelta(hours=1),
                valid_from=baseline - timedelta(hours=2),
                valid_until=now + timedelta(hours=2),
            ))))
    settings = SchedulerSettings(env="test", database_url=str(engine.url),
        redis_url="redis://:test@127.0.0.1:56379/0",
        alpaca_api_key="synthetic", alpaca_secret_key="synthetic")
    settings = settings.model_copy(update={"stock_actions_enabled": True,
        "stock_actions_coverage_start": baseline,
        "stock_actions_segment_days": 100})
    try:
        yield factory, settings, baseline
    finally:
        async with factory.begin() as db:
            await db.execute(delete(StockActionState))
            for cid, pid, checked in saved:
                await db.execute(update(StockInstrument).where(StockInstrument.coin_id == cid)
                    .values(provider_asset_id=pid, provider_verified_at=checked))
        async for key in redis_client.scan_iter(match="sim:stock:actions:*"):
            await redis_client.delete(key)


async def states(factory):
    async with factory() as db:
        return (await db.execute(select(StockActionState).order_by(StockActionState.coin_id))).scalars().all()


async def cycle(monitor, redis, http):
    factory, settings, _ = monitor
    return await stock_actions.run_stock_action_cycle(sessionmaker=factory,
        redis=redis, http=http, settings=settings)


async def test_complete_snapshot_and_replay_publish_twenty_durable_current_states(monitor, redis_client):
    with respx.mock(assert_all_called=False) as router:
        router.get("https://data.alpaca.markets/v1/corporate-actions").respond(200,
            json={"corporate_actions": {}, "next_page_token": None})
        router.get(url__startswith="https://stream.data.alpaca.markets/").respond(200,
            content=b"", headers={"content-type": "text/event-stream"})
        async with httpx.AsyncClient() as http:
            result = await cycle(monitor, redis_client, http)
    rows = await states(monitor[0])
    assert len(rows) == 20
    assert all(row.health == "current" for row in rows)
    assert all(row.covered_until > monitor[2] for row in rows)
    assert result.status == "ok"
