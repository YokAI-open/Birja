"""Actual isolated PostgreSQL corporate-action financial invariants."""

from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest_asyncio
from sqlalchemy import delete, func, select, update

from app.models.corporate_action import (
    StockActionEvent, StockActionObservation, StockActionRevision,
    StockDividendEntitlement,
)
from app.models.price import Coin
from app.models.stock import StockDataAdmission, StockInstrument
from app.services.alpaca_actions import ActionBatch, ActionObservation
from app.services.corporate_actions import persist_action_batch
from tests.stock_action_fixtures import ownership as _ownership
from tests.test_corporate_action_rules import dividend
from tests.test_stock_admission import action_admitted

ownership = _ownership


@pytest_asyncio.fixture
async def actions(ownership):
    factory, cid, uid = ownership
    now = datetime.now(UTC)
    auth = replace(action_admitted(), generation=1, reviewed_at=now-timedelta(hours=1),
                   valid_from=now-timedelta(hours=2), valid_until=now+timedelta(hours=2))
    async with factory.begin() as db:
        instrument = await db.get(StockInstrument, cid)
        saved = instrument.provider_asset_id, instrument.provider_verified_at
        instrument.provider_asset_id = f"synthetic-{cid}"
        instrument.provider_verified_at = now-timedelta(days=1)
        symbol = (await db.execute(select(Coin.symbol).where(Coin.id == cid))).scalar_one()
        db.add(StockDataAdmission(**asdict(auth)))
    action = replace(dividend(), coin_id=cid, symbol=symbol, observed_at=now,
                     ex_date=now.date()+timedelta(days=2),
                     record_date=now.date()+timedelta(days=2),
                     payable_date=now.date()+timedelta(days=10))
    try:
        yield factory, cid, uid, action, auth
    finally:
        async with factory.begin() as db:
            events=select(StockActionEvent.id).where(StockActionEvent.coin_id==cid)
            await db.execute(delete(StockActionObservation).where(StockActionObservation.event_id.in_(events)))
            await db.execute(delete(StockDividendEntitlement).where(StockDividendEntitlement.event_id.in_(events)))
            await db.execute(delete(StockDataAdmission).where(StockDataAdmission.product.in_(["actions", "calendar"])))
            await db.execute(update(StockInstrument).where(StockInstrument.coin_id==cid).values(provider_asset_id=saved[0],provider_verified_at=saved[1]))


def batch(action, **changes):
    return ActionBatch(records=(action,), observations=(ActionObservation(action, **changes),), complete=True)


async def test_revision_repeated_terms_append_observations_only(actions):
    factory, _, _, action, auth = actions
    async with factory.begin() as db:
        result = await persist_action_batch(db, batch(action), auth)
        assert len(result) == 1
        await persist_action_batch(db, batch(replace(action, observed_at=action.observed_at+timedelta(microseconds=1))), auth)
        assert (await db.execute(select(func.count()).select_from(StockActionRevision))).scalar_one() == 1
        assert (await db.execute(select(func.count()).select_from(StockActionObservation))).scalar_one() == 2
