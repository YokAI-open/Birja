"""Real PostgreSQL journal, cutoff and shared-gate behavioral tests."""

from decimal import Decimal

from sqlalchemy import select

from app.models.trade import Holding
from app.services.stock_ownership import StockMovementInput, append_stock_movement
from tests.stock_action_fixtures import ownership, synthetic_fill  # noqa: F401


async def test_movement_updates_holding_once_and_replays(ownership):
    factory, coin_id, user_id = ownership
    async with factory.begin() as db:
        trade = await synthetic_fill(db, coin_id, user_id)
        movement = StockMovementInput(user_id, coin_id, Decimal(2), Decimal(20), "fill:"+str(trade.id), trade.id)
        first = await append_stock_movement(db, movement)
        replay = await append_stock_movement(db, movement)
        assert first.id == replay.id
        holding = (await db.execute(select(Holding).where(Holding.user_id==user_id,Holding.coin_id==coin_id))).scalar_one()
        assert (holding.quantity, holding.cost_basis) == (Decimal(2),Decimal(20))
