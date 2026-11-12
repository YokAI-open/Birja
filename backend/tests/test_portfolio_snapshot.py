# ruff: noqa: F811
"""Deterministic real-PostgreSQL proofs, including a split-reader negative control."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal as D

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.trade import Holding
from app.models.user import Account
from app.services.portfolio import get_portfolio
from tests.helpers import put_holding, put_price, set_cash
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
    return uid


async def write_position(session, uid):
    await session.execute(update(Account).where(Account.user_id == uid).values(cash=D("8000")))
    await session.execute(
        update(Holding).where(Holding.user_id == uid).values(quantity=D("2"), cost_basis=D("2000"))
    )


async def test_locked_uncommitted_writer_does_not_block_whole_old_snapshot(
    engine, new_user, settings, clean_prices
):
    uid = await seed(engine, new_user)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    ready, release = asyncio.Event(), asyncio.Event()

    async def writer():
        async with sessions() as session, session.begin():
            await write_position(session, uid)
            ready.set()
            await release.wait()

    task = asyncio.create_task(writer())
    try:
        await asyncio.wait_for(ready.wait(), timeout=2)
        async with sessions() as reader:
            before = await asyncio.wait_for(
                get_portfolio(reader, user_id=uid, settings=settings), timeout=2
            )
        assert not task.done()
        assert financial_tuple(before) == OLD
    finally:
        release.set()
        await asyncio.wait_for(task, timeout=2)
    async with sessions() as reader:
        after = await get_portfolio(reader, user_id=uid, settings=settings)
    assert financial_tuple(after) == NEW


@pytest.mark.parametrize("split_reader", [False, True], ids=["production", "negative-control"])
async def test_commit_between_input_reads_exposes_split_reader(
    engine, new_user, settings, clean_prices, monkeypatch, split_reader
):
    uid = await seed(engine, new_user)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    first_read, committed = asyncio.Event(), asyncio.Event()

    async def writer():
        await first_read.wait()
        async with sessions() as session, session.begin():
            await write_position(session, uid)
        committed.set()

    task = asyncio.create_task(writer())
    try:
        async with sessions() as reader:
            execute = reader.execute
            statements = []

            async def execute_at_boundary(statement, *args, **kwargs):
                result = await execute(statement, *args, **kwargs)
                statements.append(str(statement))
                if len(statements) == 1:
                    first_read.set()
                    await asyncio.wait_for(committed.wait(), timeout=2)
                return result

            monkeypatch.setattr(reader, "execute", execute_at_boundary)
            if split_reader:
                cash = (
                    await reader.execute(select(Account.cash).where(Account.user_id == uid))
                ).scalar_one()
                quantity, basis = (
                    await reader.execute(
                        select(Holding.quantity, Holding.cost_basis).where(Holding.user_id == uid)
                    )
                ).one()
                values = cash, quantity, basis, cash + quantity * D("1000")
                assert values == (D("9000"), D("2"), D("2000"), D("11000"))
                with pytest.raises(AssertionError, match="different commits"):
                    assert_whole_snapshot(values)
            else:
                snapshot = await get_portfolio(reader, user_id=uid, settings=settings)
                assert_whole_snapshot(financial_tuple(snapshot))
                assert financial_tuple(snapshot) == OLD
                assert len(statements) == 1
                sql = statements[0].upper()
                assert "FOR UPDATE" not in sql
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
    await put_price(engine, "BTC", "100", now)
    async with factory() as db:
        await stock_trading.execute(db, user_id=uid, order=trade_order(), settings=settings)
        await trading.execute(
            db,
            user_id=uid,
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
            statements.append(str(statement))
            if len(statements) == 1:
                async with factory() as writer:
                    await stock_trading.execute(
                        writer, user_id=uid, order=trade_order(quantity="1"), settings=settings
                    )
                await put_price(engine, "BTC", "200", now)
            return result

        monkeypatch.setattr(reader, "execute", read_then_fill)
        before = await get_portfolio(reader, user_id=uid, settings=settings)
        assert before.cash == 9696 and before.total_value == D("9997.50")
        assert [h.symbol for h in before.holdings] == ["AAPL", "BTC"]
        assert [h.quantity for h in before.holdings] == [D(2), D("0.99501246")]
        assert [h.mid for h in before.holdings] == [D(101), D(100)]
        assert before.class_values.stocks == 202 and before.class_values.crypto == D("99.50")
        assert len(statements) == 2 and sum("FROM accounts" in sql for sql in statements) == 1
    async with factory() as reader:
        after = await get_portfolio(reader, user_id=uid, settings=settings)
        assert after.cash == 9594 and after.total_value == D("10096.00")
        assert after.holdings[0].quantity == 3 and after.holdings[1].mid == 200
