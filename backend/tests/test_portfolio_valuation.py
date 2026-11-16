"""Real owned statements preserve exact baselines without pooling siblings."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from app.schemas.portfolio import PortfolioOut
from app.services.portfolio import get_portfolio
from app.services.portfolios import OwnedActivePortfolio
from tests.stock_trade_fixtures import ownership, status_case, stock_trade_case
from tests.test_portfolio_crypto import crypto_books
from tests.test_portfolio_stock_trading import execute, order, stock_books

__all__ = ["crypto_books", "stock_books", "ownership", "status_case", "stock_trade_case"]


async def statement(factory, root, settings, **kw):
    async with factory() as db:
        return await get_portfolio(db, portfolio=root, settings=settings, **kw)


async def test_actual_unequal_baselines_and_same_symbol_siblings(crypto_books, settings):
    factory, (first, sibling, *_), _ = crypto_books
    p = await statement(factory, first, settings)
    q = await statement(factory, sibling, settings)
    assert (p.cash, p.starting_cash, p.total_value, p.total_pl) == (
        Decimal("1000"),
        Decimal("10000"),
        Decimal("1010"),
        Decimal("-8990"),
    )
    assert (q.cash, q.starting_cash, q.total_value, q.total_pl) == (
        Decimal("2000"),
        Decimal("7654"),
        Decimal("2020"),
        Decimal("-5634"),
    )
    assert p.holdings[0].quantity == Decimal("0.1")
    assert q.holdings[0].quantity == Decimal("0.2")
    assert q.total_pl_percent == Decimal("-73.61")
    wire = PortfolioOut.from_value(q).model_dump(mode="json")
    assert wire["portfolio_id"] == str(sibling.portfolio_id) and wire["name"] == "Sibling"
    assert wire["cash"] == "2000.00" and isinstance(wire["total_value"], str)


@pytest.mark.parametrize("target", ["foreign", "closed", "unknown"])
async def test_unavailable_root_never_discloses_statement(crypto_books, settings, target):
    factory, roots, _ = crypto_books
    root = {
        "foreign": roots[3],
        "closed": roots[2],
        "unknown": OwnedActivePortfolio(9223372036854775807, roots[0].user_id),
    }[target]
    with pytest.raises(HTTPException) as exc:
        await statement(factory, root, settings)
    assert exc.value.status_code == 404
    assert exc.value.detail == {"code": "portfolio_unavailable"}


async def test_cash_only_root_and_zero_active_do_not_regrant(crypto_books, settings):
    factory, roots, _ = crypto_books
    async with factory.begin() as db:
        await db.execute(
            text("UPDATE holdings SET quantity=0,cost_basis=0 WHERE portfolio_id=:p"),
            {"p": roots[1].portfolio_id},
        )
    q = await statement(factory, roots[1], settings)
    assert q.cash == q.known_value == q.total_value == Decimal("2000")
    assert q.starting_cash == Decimal("7654") and q.holdings == ()
    assert q.prices_as_of is None and q.cash_allocation_percent == 100


async def test_unpriced_holding_is_incomplete_without_sibling_pooling(crypto_books, settings):
    factory, roots, cid = crypto_books
    async with factory.begin() as db:
        await db.execute(text("DELETE FROM prices WHERE coin_id=:c"), {"c": cid})
    q = await statement(factory, roots[1], settings)
    assert q.known_value == Decimal("2000") and not q.valuation_complete
    assert q.unvalued_holding_count == 1 and q.total_value is None
    assert q.total_pl is q.total_pl_percent is q.cash_allocation_percent is None
    assert q.holdings[0].current_value is q.holdings[0].allocation_percent is None


@pytest.mark.parametrize("age,status", [(119, "fresh"), (120, "aging"), (301, "stale")])
async def test_crypto_mark_age_rules_are_unchanged(crypto_books, settings, age, status):
    factory, roots, cid = crypto_books
    now = datetime.now(UTC)
    async with factory.begin() as db:
        await db.execute(
            text("UPDATE prices SET as_of=:t WHERE coin_id=:c"),
            {"c": cid, "t": now - timedelta(seconds=age)},
        )
    p = await statement(factory, roots[0], settings, now=now)
    assert p.holdings[0].age_seconds == age and p.holdings[0].status == status
    assert p.total_value == Decimal("1010")


async def test_stock_midpoint_and_sibling_cash_are_independent(stock_books, settings):
    factory, _, (root, sibling, *_), _ = stock_books
    await execute(factory, root, settings)
    await execute(factory, sibling, settings, order(quantity="3"))
    p, q = await statement(factory, root, settings), await statement(factory, sibling, settings)
    assert (p.cash, p.total_value, p.holdings[0].mid) == (796, 998, 101)
    assert (q.cash, q.total_value, q.starting_cash) == (1694, 1997, 7654)
    assert p.holdings[0].cost_basis == 204 and q.holdings[0].cost_basis == 306
    assert p.holdings[0].stock_mark.mark_mode == "fresh"


async def test_uncertain_stock_mark_keeps_known_cash_and_unavailable_returns(stock_books, settings):
    factory, cid, (root, sibling, *_), _ = stock_books
    await execute(factory, root, settings)
    async with factory.begin() as db:
        await db.execute(
            text("UPDATE stock_action_state SET health='unknown' WHERE coin_id=:c"), {"c": cid}
        )
    p, q = await statement(factory, root, settings), await statement(factory, sibling, settings)
    assert p.known_value == 796 and p.unvalued_holding_count == 1
    assert p.total_value is p.total_pl is p.total_pl_percent is None
    assert p.holdings[0].current_value is None
    assert q.total_value == 2000 and q.valuation_complete


@pytest.mark.parametrize("mode", ["halted", "closed"])
async def test_dated_stock_marks_keep_source_time_and_exact_owned_value(
    stock_books, settings, monkeypatch, mode
):
    from app.services import stock_sessions

    factory, _, (root, *_), now = stock_books
    receipt, _ = await execute(factory, root, settings)
    if mode == "closed":
        close = receipt.executed_at + timedelta(microseconds=1)
        original = stock_sessions.calendars.get_calendar

        def closed_calendar(*args, **kwargs):
            calendar = original(*args, **kwargs)
            prior = calendar.session_close
            calendar.session_close = lambda day: (
                type(prior(day))(close) if str(day) == str(now.date()) else prior(day)
            )
            return calendar

        stock_sessions._calendar_bounds.cache_clear()
        monkeypatch.setattr(stock_sessions.calendars, "get_calendar", closed_calendar)
        async with factory.begin() as db:
            await db.execute(
                text("UPDATE stock_sessions SET closes_at=:c WHERE session_date=:d"),
                {"c": close, "d": now.date()},
            )
    async with factory.begin() as db:
        if mode == "halted":
            await db.execute(text("UPDATE stock_status_evidence SET state='halted'"))
        await db.execute(text("UPDATE stock_quotes SET event_at=collected_at-interval '5 minutes'"))
    try:
        p = await statement(factory, root, settings)
        assert p.total_value == 998 and p.holdings[0].stock_mark.mark_mode == mode
        assert p.holdings[0].age_seconds >= 300
        assert p.holdings[0].stock_mark.feed == "iex"
    finally:
        stock_sessions._calendar_bounds.cache_clear()
