from datetime import UTC, datetime, timedelta
from decimal import Decimal as D

import pytest
from sqlalchemy import event, update

from app.models.price import Coin
from app.services.portfolio import get_portfolio
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


@pytest.mark.parametrize(
    "age,fresh,stale,expected_age,expected_status",
    [
        (119, 120, 300, 119, "fresh"),
        (120, 120, 300, 120, "aging"),
        (300, 120, 300, 300, "aging"),
        (301, 120, 300, 301, "stale"),
        (-60, 120, 300, 0, "fresh"),
        (5, 5, 8, 5, "aging"),
        (9, 5, 8, 9, "stale"),
    ],
)
async def test_price_age_boundaries_and_configured_rules(
    db, engine, new_user, settings, clean_prices, age, fresh, stale, expected_age, expected_status
):
    uid = await new_user()
    now = datetime(2026, 10, 30, 12, tzinfo=UTC)
    await put_holding(engine, uid, "BTC", "1", "100")
    await put_price(engine, "BTC", "200", now - timedelta(seconds=age))
    rules = settings.model_copy(update={"price_fresh_seconds": fresh, "price_stale_seconds": stale})
    p = await get_portfolio(db, user_id=uid, settings=rules, now=now)
    assert (p.fresh_seconds, p.stale_seconds) == (fresh, stale)
    assert (p.holdings[0].age_seconds, p.holdings[0].status) == (expected_age, expected_status)


async def test_oldest_available_price_and_missing_totals(
    db, engine, new_user, settings, clean_prices
):
    uid = await new_user()
    now = datetime.now(UTC)
    for symbol in ("BTC", "ETH", "SOL"):
        await put_holding(engine, uid, symbol, "1", "10")
    await put_price(engine, "BTC", "100", now - timedelta(seconds=10))
    await put_price(engine, "ETH", "200", now - timedelta(seconds=301))
    p = await get_portfolio(db, user_id=uid, settings=settings, now=now)
    assert p.prices_as_of == now - timedelta(seconds=301)
    assert not p.valuation_complete
    assert p.total_value is p.total_pl is p.total_pl_percent is p.cash_allocation_percent is None
    rows = {h.symbol: h for h in p.holdings}
    assert rows["BTC"].current_value == D("100")
    assert rows["ETH"].current_value == D("200")
    assert rows["ETH"].status == "stale"
    assert rows["SOL"].status == "unpriced"
    assert rows["SOL"].mid is rows["SOL"].as_of is rows["SOL"].age_seconds is None
    assert all(h.allocation_percent is None for h in p.holdings)


async def test_price_clock_is_sampled_after_awaited_database_read(
    db, engine, new_user, settings, clean_prices, monkeypatch
):
    from app.services import portfolio

    uid = await new_user()
    early = datetime(2026, 10, 30, 12, tzinfo=UTC)
    late = early + timedelta(seconds=182)
    await put_holding(engine, uid, "BTC", "1", "100")
    await put_price(engine, "BTC", "200", early - timedelta(seconds=119))
    read_finished = False

    class Clock:
        @staticmethod
        def now(tz):
            assert tz is UTC
            return late if read_finished else early

    execute = db.execute

    async def delayed_read(*args, **kwargs):
        nonlocal read_finished
        result = await execute(*args, **kwargs)
        read_finished = True
        return result

    monkeypatch.setattr(portfolio, "datetime", Clock)
    monkeypatch.setattr(db, "execute", delayed_read)
    p = await get_portfolio(db, user_id=uid, settings=settings)
    assert p.valued_at == late
    assert (p.holdings[0].age_seconds, p.holdings[0].status) == (301, "stale")
