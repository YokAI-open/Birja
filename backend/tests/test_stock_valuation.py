# ruff: noqa: F811
"""Real mixed financial snapshot and independently permitted stock marks."""

from decimal import Decimal

from app.services.portfolio import get_portfolio
from app.services.stock_trading import execute
from tests.stock_trade_fixtures import ownership,status_case,stock_trade_case  # noqa: F401
from tests.test_stock_trading_service import trade_order


async def test_actual_stock_fill_is_valued_at_exact_midpoint(stock_trade_case,settings):
    factory,cid,uid,now=stock_trade_case
    async with factory() as db:
        await execute(db,user_id=uid,order=trade_order(),settings=settings)
        portfolio=await get_portfolio(db,user_id=uid,settings=settings)
    assert portfolio.total_value==Decimal(9998)
    assert portfolio.known_value==Decimal(9998) and portfolio.unvalued_holding_count==0
    assert portfolio.holdings[0].asset_class=="stock" and portfolio.holdings[0].coin_id==str(cid)
    assert portfolio.holdings[0].mid==101 and portfolio.holdings[0].current_value==202
