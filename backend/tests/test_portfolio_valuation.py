"""Real owned statements preserve exact baselines without pooling siblings."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.trade import Holding
from app.models.user import Account
from app.schemas.portfolio import PortfolioOut
from app.services.portfolio import get_portfolio, load_portfolio_snapshots
from app.services.portfolios import OwnedActivePortfolio
from tests.helpers import coin_id, put_price
from tests.portfolio_fixtures import close_empty_test_root
from tests.stock_trade_fixtures import ownership, status_case, stock_trade_case
from tests.test_portfolio_creation import authority, management_api
from tests.test_portfolio_stock_trading import execute, order

__all__ = ["crypto_books", "stock_books", "ownership", "status_case", "stock_trade_case"]


@pytest_asyncio.fixture
async def migrated(management_api):
    """Explicit current0023 setup; retained global fixture remains untouched."""
    yield


__all__ += ["management_api", "authority"]


async def _roots(factory, uid, other, now):
    async with factory.begin() as db:
        first = (await db.scalars(select(Account).where(Account.user_id == uid))).one()
        first.cash = Decimal("1000")
        sibling = Account(
            user_id=uid,
            name="Sibling",
            name_key="sibling",
            cash=Decimal("2000"),
            starting_cash=Decimal("7654"),
        )
        closed = Account(
            user_id=uid,
            name="Closed",
            name_key="closed",
            cash=Decimal("55"),
            starting_cash=Decimal("99"),
        )
        db.add_all([sibling, closed])
        await db.flush()
        await close_empty_test_root(db, closed.id)
        foreign = (await db.scalars(select(Account).where(Account.user_id == other))).one()
        return [OwnedActivePortfolio(a.id, uid) for a in (first, sibling, closed, foreign)]


@pytest_asyncio.fixture
async def crypto_books(engine, new_user, clean_prices):
    uid, other = await new_user(), await new_user()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    cid = await coin_id(engine, "BTC")
    roots = await _roots(factory, uid, other, datetime.now(UTC))
    async with factory.begin() as db:
        for root, qty, basis in ((roots[0], "0.1", "123"), (roots[1], "0.2", "456")):
            db.add(
                Holding(
                    portfolio_id=root.portfolio_id,
                    user_id=uid,
                    coin_id=cid,
                    quantity=Decimal(qty),
                    cost_basis=Decimal(basis),
                )
            )
    await put_price(engine, "BTC", "100", datetime.now(UTC))
    return factory, roots, cid


@pytest_asyncio.fixture
async def stock_books(stock_trade_case, new_user):
    factory, cid, uid, now = stock_trade_case
    roots = await _roots(factory, uid, await new_user(), now)
    return factory, cid, roots, now


async def statement(factory, root, settings, **kw):
    async with factory() as db:
        return await get_portfolio(db, portfolio=root, settings=settings, **kw)


@pytest.mark.parametrize("count", [2, 10])
async def test_shared_stock_proof_is_original_to_each_root(stock_books, settings, count):
    """A sibling holding cannot borrow another root's original retention proof."""
    from dataclasses import asdict

    from sqlalchemy import event

    factory, cid, (root, sibling, *_), _ = stock_books
    await execute(factory, root, settings)
    async with factory.begin() as db:
        await db.execute(
            text(
                "INSERT INTO holdings(portfolio_id,user_id,coin_id,quantity,cost_basis) "
                "VALUES (:p,:u,:c,3,306)"
            ),
            {"p": sibling.portfolio_id, "u": sibling.user_id, "c": cid},
        )
        for i in range(count - 2):
            extra_id = (
                await db.execute(
                    text(
                        "INSERT INTO accounts(user_id,name,name_key,cash,starting_cash) "
                        "VALUES (:u,:n,:n,1000,10000) RETURNING id"
                    ),
                    {"u": root.user_id, "n": f"extra-{i}"},
                )
            ).scalar_one()
            crypto = (
                await db.execute(text("SELECT id FROM coins WHERE symbol='BTC'"))
            ).scalar_one()
            await db.execute(
                text(
                    "INSERT INTO prices(coin_id,mid,as_of,source) "
                    "VALUES (:c,100,clock_timestamp(),'fake') ON CONFLICT(coin_id) "
                    "DO UPDATE SET mid=100,as_of=excluded.as_of"
                ),
                {"c": crypto},
            )
            await db.execute(
                text(
                    "INSERT INTO holdings(portfolio_id,user_id,coin_id,quantity,cost_basis) "
                    "VALUES (:p,:u,:c,1,100),(:p,:u,:crypto,0.1,5)"
                ),
                {"p": extra_id, "u": root.user_id, "c": cid, "crypto": crypto},
            )
    now = datetime.now(UTC)
    queries = []
    engine = factory.kw["bind"].sync_engine

    def capture(conn, cursor, statement, params, context, many):
        queries.append(statement)

    event.listen(engine, "before_cursor_execute", capture)
    try:
        async with factory() as db:
            p, q, *extra = await load_portfolio_snapshots(
                db,
                owner_id=root.user_id,
                portfolio_ids=None,
                settings=settings,
                now=now,
            )
    finally:
        event.remove(engine, "before_cursor_execute", capture)
    assert len(queries) == 2
    assert len(extra) == count - 2
    assert all(p.known_value == 1010 and p.total_value is None for p in extra)
    assert p.total_value == 998 and p.valuation_complete
    assert q.known_value == 2000 and q.total_value is None
    assert q.holdings[0].stock_mark.valuation_reason == "permission_unavailable"
    assert q.holdings[0].quantity == 3 and q.holdings[0].stock_mark.units_safe
    assert p.valued_at == q.valued_at == now
    assert asdict(p) == asdict(await statement(factory, root, settings, now=now))
    assert asdict(q) == asdict(await statement(factory, sibling, settings, now=now))


@pytest.mark.parametrize("change", ["units", "safety", "expiry", "price"])
async def test_shared_stock_recheck_never_renews_original_mark(
    stock_books, settings, monkeypatch, change
):
    from sqlalchemy.ext.asyncio import AsyncSession

    factory, cid, (root, sibling, *_), _ = stock_books
    await execute(factory, root, settings)
    await execute(factory, sibling, settings, order(quantity="3"))
    original = AsyncSession.execute
    reads = 0

    async def intercepted(db, stmt, *args, **kwargs):
        nonlocal reads
        result = await original(db, stmt, *args, **kwargs)
        reads += 1
        if reads == 1:
            sql = {
                "units": "UPDATE stock_action_state SET unit_epoch=unit_epoch+1 WHERE coin_id=:c",
                "safety": ("UPDATE stock_action_state SET epoch=epoch+1 WHERE coin_id=:c"),
                "expiry": (
                    "UPDATE stock_data_admissions SET valid_until=clock_timestamp() "
                    "WHERE product='quotes'"
                ),
                "price": "UPDATE stock_quotes SET bid=200,ask=202,mid=201 WHERE coin_id=:c",
            }[change]
            async with factory.begin() as writer:
                await original(writer, text(sql), {"c": cid})
        return result

    monkeypatch.setattr(AsyncSession, "execute", intercepted)
    async with factory() as db:
        p, q = await load_portfolio_snapshots(
            db, owner_id=root.user_id, portfolio_ids=None, settings=settings
        )
    if change == "price":
        assert p.total_value == 998 and q.total_value == 1997
        assert p.holdings[0].mid == q.holdings[0].mid == 101
    else:
        assert p.total_value is q.total_value is None
        assert p.known_value == 796 and q.known_value == 1694
        if change in {"units", "safety"}:
            assert not p.holdings[0].stock_mark.units_safe
            assert not q.holdings[0].stock_mark.units_safe
            assert p.holdings[0].average_cost is q.holdings[0].average_cost is None


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


async def test_shared_time_is_sampled_after_final_await(stock_books, settings, monkeypatch):
    from app.services import portfolio

    factory, _, (root, sibling, *_), _ = stock_books
    await execute(factory, root, settings)
    await execute(factory, sibling, settings)
    captured = datetime.now(UTC)

    class AdvancingClock(datetime):
        calls = 0

        @classmethod
        def now(cls, tz=None):
            cls.calls += 1
            return captured + timedelta(hours=2) if cls.calls >= 3 else captured

    monkeypatch.setattr(portfolio, "datetime", AdvancingClock)
    async with factory() as db:
        p, q = await load_portfolio_snapshots(db, owner_id=root.user_id, settings=settings)
    assert p.valued_at == q.valued_at == captured + timedelta(hours=2)
    assert p.total_value is q.total_value is None
    assert p.known_value == 796 and q.known_value == 1796


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
