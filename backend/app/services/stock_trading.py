"""Stock service boundary; current authority never substitutes for a receipt."""

from app.services.trade_math import TradeRefused


async def quote(db, *, user_id, order, settings):
    raise TradeRefused("quote_unavailable", "Stock execution is not available.")
