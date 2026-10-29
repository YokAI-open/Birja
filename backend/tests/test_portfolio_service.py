from datetime import UTC, datetime, timedelta
from decimal import Decimal as D

import pytest
from app.services.portfolio import get_portfolio
from sqlalchemy import event, update

from app.models.price import Coin
from tests.helpers import put_holding, put_price, set_cash


async def test_single_scalar_snapshot_includes_inactive_and_omits_zero(
    db, engine, new_user, settings, clean_prices
):
    uid = await new_user()
    await set_cash(engine, uid, "9900")
    await put_holding(engine, uid, "BTC", "0.00099501", "100")
    await put_holding(engine, uid, "ETH", "0", "0")
    now = datetime.now(UTC)
    await put_price(engine, "BTC", "100000", now - timedelta(seconds=120))
    async with engine.begin() as conn:
        await conn.execute(update(Coin).where(Coin.symbol == "BTC").values(is_active=False))
    statements = []

    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", capture)
    try:
        p = await get_portfolio(db, user_id=uid, settings=settings, now=now)
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", capture)
        async with engine.begin() as conn:
            await conn.execute(update(Coin).where(Coin.symbol == "BTC").values(is_active=True))
    assert len(statements) == 1
    assert "FOR UPDATE" not in statements[0].upper()
    assert p.total_value == D("9999.50")
    assert p.prices_as_of == now - timedelta(seconds=120)
    assert len(p.holdings) == 1
    assert p.holdings[0].is_active is False
    assert (p.holdings[0].age_seconds, p.holdings[0].status) == (120, "aging")


async def test_cash_only_missing_account_and_unpriced(db, engine, new_user, settings, clean_prices):
    uid = await new_user()
    await set_cash(engine, uid, "9999")
    p = await get_portfolio(db, user_id=uid, settings=settings)
    assert p.total_value == D("9999") and p.total_pl == D("-1")
    assert p.prices_as_of is None
    assert p.valued_at.tzinfo is not None
    await db.rollback()
    await put_holding(engine, uid, "BTC", "1", "2")
    p = await get_portfolio(db, user_id=uid, settings=settings)
    assert p.holdings[0].status == "unpriced"
    assert p.holdings[0].as_of is p.holdings[0].age_seconds is None
    assert p.total_value is None
    with pytest.raises(RuntimeError, match="account"):
        await get_portfolio(db, user_id=-1, settings=settings)
