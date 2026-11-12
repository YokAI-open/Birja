"""Real financial effects through the stock service, never a fabricated fill."""

from decimal import Decimal

from app.schemas.stock_trades import QuoteIn
from app.services import stock_trading
from tests.stock_trade_fixtures import ownership, status_case, stock_trade_case  # noqa: F401
from tests.test_stock_status import financial_snapshot


async def test_stock_preview_is_read_only(stock_trade_case, settings):
    factory, cid, uid, now = stock_trade_case
    before = await financial_snapshot(factory)
    async with factory() as db:
        result = await stock_trading.quote(
            db, user_id=uid, order=QuoteIn(symbol="AAPL", side="buy", quantity="2"), settings=settings,
        )
    assert result.coin_id == str(cid)
    assert result.exec_price == Decimal(102)
    assert result.notional == Decimal(204)
    assert result.cash_after == Decimal(9796)
    assert result.held_after == Decimal(2)
    assert result.fee == 0
    assert await financial_snapshot(factory) == before
