# ruff: noqa: F811
"""Deterministic real-PostgreSQL proofs, including a split-reader negative control."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal as D

import pytest
from sqlalchemy import select, text, update
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.trade import Holding
from app.models.user import Account
from app.services.portfolio import get_portfolio
from app.services.portfolios import OwnedActivePortfolio
from tests.dividend_fixtures import dividend_case, hold, process, revise  # noqa: F401
from tests.helpers import put_holding, put_price, set_cash
from tests.stock_action_fixtures import synthetic_portfolio_id
from tests.stock_trade_fixtures import ownership, status_case, stock_trade_case  # noqa: F401

OLD = (D("9000"), D("1"), D("1000"), D("10000"))
NEW = (D("8000"), D("2"), D("2000"), D("10000"))


def financial_tuple(snapshot):
    h = snapshot.holdings[0]
    return snapshot.cash, h.quantity, h.cost_basis, snapshot.total_value


def assert_whole_snapshot(values):
    assert values in (OLD, NEW), "Financial inputs came from different commits"


async def seed(engine, new_user):
    uid = await new_user()
    await set_cash(engine, uid, "9000")
    await put_holding(engine, uid, "BTC", "1", "1000")
    await put_price(engine, "BTC", "1000", datetime.now(UTC))
    async with async_sessionmaker(engine)() as db:
        return OwnedActivePortfolio(await synthetic_portfolio_id(db, uid), uid)


async def write_position(session, portfolio):
    await session.execute(
        update(Account)
        .where(Account.id == portfolio.portfolio_id, Account.user_id == portfolio.user_id)
        .values(cash=D("8000"))
    )
    await session.execute(
        update(Holding)
        .where(Holding.portfolio_id == portfolio.portfolio_id, Holding.user_id == portfolio.user_id)
        .values(quantity=D("2"), cost_basis=D("2000"))
    )


async def test_locked_writer_waits_for_root_proof_but_preserves_whole_old_snapshot(
    engine, new_user, settings, clean_prices
):
    portfolio = await seed(engine, new_user)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    ready, release = asyncio.Event(), asyncio.Event()
    writer_pid = None
    read_task = None

    async def writer():
        nonlocal writer_pid
        async with sessions() as session, session.begin():
            writer_pid = (await session.execute(text("SELECT pg_backend_pid()"))).scalar_one()
            await write_position(session, portfolio)
            ready.set()
            await release.wait()

    task = asyncio.create_task(writer())
    try:
        await asyncio.wait_for(ready.wait(), timeout=5)
        async with sessions() as reader:
            reader_pid = (await reader.execute(text("SELECT pg_backend_pid()"))).scalar_one()
            read_task = asyncio.create_task(
                get_portfolio(reader, portfolio=portfolio, settings=settings)
            )
            # The financial snapshot is nonlocking, but the final identity proof
            # deliberately holds FOR SHARE until request transaction end. Prove
            # the actual PostgreSQL wait, not merely a pending asyncio task.
            async with sessions() as observer, asyncio.timeout(5):
                while True:
                    blocked = (
                        await observer.execute(
                            text(
                                "SELECT :writer=ANY(pg_blocking_pids(:reader)) "
                                "AND EXISTS(SELECT FROM pg_stat_activity WHERE pid=:reader "
                                "AND state='active' AND wait_event_type='Lock')"
                            ),
                            {"writer": writer_pid, "reader": reader_pid},
                        )
                    ).scalar_one()
                    await observer.commit()
                    if blocked:
                        break
                    await asyncio.sleep(0.01)
            assert not task.done() and not read_task.done()
            release.set()
            before = await asyncio.wait_for(read_task, timeout=5)
        assert financial_tuple(before) == OLD
    finally:
        release.set()
        if read_task is not None and not read_task.done():
            read_task.cancel()
            await asyncio.gather(read_task, return_exceptions=True)
        await asyncio.wait_for(task, timeout=5)
    async with sessions() as reader:
        after = await get_portfolio(reader, portfolio=portfolio, settings=settings)
    assert financial_tuple(after) == NEW


@pytest.mark.parametrize("split_reader", [False, True], ids=["production", "negative-control"])
async def test_commit_between_input_reads_exposes_split_reader(
    engine, new_user, settings, clean_prices, monkeypatch, split_reader
):
    portfolio = await seed(engine, new_user)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    first_read, committed = asyncio.Event(), asyncio.Event()

    async def writer():
        await first_read.wait()
        async with sessions() as session, session.begin():
            await write_position(session, portfolio)
        committed.set()

    task = asyncio.create_task(writer())
    try:
        async with sessions() as reader:
            execute = reader.execute
            statements = []

            async def execute_at_boundary(statement, *args, **kwargs):
                result = await execute(statement, *args, **kwargs)
                statements.append(str(statement.compile(dialect=postgresql.dialect())))
                if len(statements) == 1:
                    first_read.set()
                    await asyncio.wait_for(committed.wait(), timeout=2)
                return result

            monkeypatch.setattr(reader, "execute", execute_at_boundary)
            if split_reader:
                cash = (
                    await reader.execute(
                        select(Account.cash).where(
                            Account.id == portfolio.portfolio_id,
                            Account.user_id == portfolio.user_id,
                        )
                    )
                ).scalar_one()
                quantity, basis = (
                    await reader.execute(
                        select(Holding.quantity, Holding.cost_basis).where(
                            Holding.portfolio_id == portfolio.portfolio_id,
                            Holding.user_id == portfolio.user_id,
                        )
                    )
                ).one()
                values = cash, quantity, basis, cash + quantity * D("1000")
                assert values == (D("9000"), D("2"), D("2000"), D("11000"))
                with pytest.raises(AssertionError, match="different commits"):
                    assert_whole_snapshot(values)
            else:
                snapshot = await get_portfolio(reader, portfolio=portfolio, settings=settings)
                assert_whole_snapshot(financial_tuple(snapshot))
                assert financial_tuple(snapshot) == OLD
                assert len(statements) == 2
                sql = statements[0].upper()
                assert all("FOR UPDATE" not in statement.upper() for statement in statements)
                assert "FOR SHARE OF ACCOUNTS" in statements[1].upper()
                assert "ACCOUNTS.CASH" not in statements[1].upper()
                for table in ("ACCOUNTS", "HOLDINGS", "COINS", "PRICES"):
                    assert table in sql
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


async def test_actual_mixed_snapshot_never_combines_cash_and_positions_from_different_commits(
    stock_trade_case, settings, engine, clean_prices, monkeypatch
):
    from uuid import uuid4

    from app.services import stock_trading, trading
    from tests.test_stock_trading_service import trade_order

    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        portfolio = OwnedActivePortfolio(await synthetic_portfolio_id(db, uid), uid)
    await put_price(engine, "BTC", "100", now)
    async with factory() as db:
        await stock_trading.execute(db, portfolio=portfolio, order=trade_order(), settings=settings)
        await trading.execute(
            db,
            portfolio=portfolio,
            order=trading.Order("BTC", "buy", "usd", D(100)),
            expected_mid=D(100),
            idempotency_key=uuid4(),
            settings=settings,
        )
    async with factory() as reader:
        original = reader.execute
        statements = []

        async def read_then_fill(statement, *args, **kwargs):
            result = await original(statement, *args, **kwargs)
            statements.append(str(statement.compile(dialect=postgresql.dialect())))
            if len(statements) == 1:
                async with factory() as writer:
                    await stock_trading.execute(
                        writer,
                        portfolio=portfolio,
                        order=trade_order(quantity="1"),
                        settings=settings,
                    )
                await put_price(engine, "BTC", "200", now)
            return result

        monkeypatch.setattr(reader, "execute", read_then_fill)
        before = await get_portfolio(reader, portfolio=portfolio, settings=settings)
        assert before.cash == 9696 and before.total_value == D("9997.50")
        assert [h.symbol for h in before.holdings] == ["AAPL", "BTC"]
        assert [h.quantity for h in before.holdings] == [D(2), D("0.99501246")]
        assert [h.mid for h in before.holdings] == [D(101), D(100)]
        assert before.class_values.stocks == 202 and before.class_values.crypto == D("99.50")
        assert len(statements) == 2
        financial = [sql for sql in statements if "accounts.cash" in sql]
        assert len(financial) == 1 and "holdings.quantity" in financial[0]
        assert "FOR SHARE OF accounts" in statements[1]
        assert "accounts.cash" not in statements[1]
    async with factory() as reader:
        after = await get_portfolio(reader, portfolio=portfolio, settings=settings)
        assert after.cash == 9594 and after.total_value == D("10096.00")
        assert after.holdings[0].quantity == 3 and after.holdings[1].mid == 200


async def test_actual_dividend_cash_and_correction_enter_portfolio_once(dividend_case, settings):
    from app.services.event_history import list_event_history

    factory, ids = dividend_case

    async def snapshot():
        async with factory() as db:
            return await get_portfolio(
                db,
                portfolio=OwnedActivePortfolio(ids["portfolio_id"], ids["user_id"]),
                settings=settings,
            )

    before = await snapshot()
    assert before.cash == D(100) and before.starting_cash == D(10000)
    original = await process(factory, ids)
    assert await process(factory, ids) == original
    credited = await snapshot()
    assert credited.cash == D(101) and credited.starting_cash == before.starting_cash
    assert credited.class_values.cash == credited.cash
    assert credited.known_value == before.known_value + D(1)
    corrected = await revise(factory, ids, rate="0.75")
    correction = await process(factory, corrected)
    assert correction.outcome == "applied" and await process(factory, corrected) == correction
    applied = await snapshot()
    assert applied.cash == D("101.50") and applied.starting_cash == before.starting_cash
    assert applied.known_value == applied.cash + sum(
        (h.current_value for h in applied.holdings if h.current_value is not None), D(0)
    )
    uncertain = await revise(factory, corrected, classification="uncertain", eligible=False)
    held = await hold(factory, original.payment_id, uncertain["revision_fingerprint"])
    assert await hold(factory, original.payment_id, uncertain["revision_fingerprint"]) == held
    after = await snapshot()
    assert after.cash == applied.cash and after.starting_cash == before.starting_cash
    assert after.class_values.cash == D("101.50")
    async with factory() as db:
        history = await list_event_history(
            db, portfolio=OwnedActivePortfolio(ids["portfolio_id"], ids["user_id"])
        )
    assert [item.kind for item in history.items] == [
        "dividend_correction",
        "dividend_correction",
        "dividend",
    ]
    assert sum((D(item.cash_delta) for item in history.items), D(0)) == D("1.50")
    assert after.cash == before.cash + D("1.50")
