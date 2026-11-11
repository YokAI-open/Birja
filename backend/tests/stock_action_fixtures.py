"""Explicit synthetic ownership seeds. Never imported by application code."""

from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest_asyncio
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.corporate_action import StockActionState, StockOwnershipMovement
from app.models.stock import StockInstrument
from app.models.trade import Holding, Trade


@pytest_asyncio.fixture
async def ownership(engine, migrated, new_user):
    user_id = await new_user()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory.begin() as db:
        coin_id = (await db.execute(select(StockInstrument.coin_id).order_by(StockInstrument.coin_id))).scalars().first()
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        db.add(StockActionState(coin_id=coin_id, admission_generation=1, health="current", checked_at=now-timedelta(seconds=1), valid_until=now+timedelta(hours=1), journal_start_at=now-timedelta(days=5), complete_from=now-timedelta(days=5), coverage_start=now-timedelta(days=5), covered_until=now))
    try:
        yield factory, coin_id, user_id
    finally:
        async with factory.begin() as db:
            await db.execute(delete(StockOwnershipMovement).where(StockOwnershipMovement.coin_id==coin_id))
            await db.execute(delete(Holding).where(Holding.coin_id==coin_id))
            await db.execute(delete(Trade).where(Trade.coin_id==coin_id))
            await db.execute(delete(StockActionState).where(StockActionState.coin_id==coin_id))


async def synthetic_fill(db, coin_id, user_id, *, quantity=Decimal(2), side="buy"):
    """Fill-like caller only; no production cash service or stock execution."""
    now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
    trade = Trade(coin_id=coin_id,user_id=user_id,side=side,input_kind="quantity",input_value=quantity,quantity=quantity,mid_price=Decimal(10),price_as_of=now,exec_price=Decimal(10),fee=Decimal(0),cash_delta=quantity*Decimal(-10 if side=="buy" else 10),cash_after=Decimal(10000),idempotency_key=uuid4())
    db.add(trade)
    await db.flush()
    return trade
