# ruff: noqa: F811
"""Bounded parallel requests use actual PostgreSQL locks and independent sessions."""

import asyncio
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select, update

from app.models.corporate_action import StockOwnershipMovement
from app.models.price import Coin
from app.models.stock_execution import StockFillFacts
from app.models.trade import Holding, Trade
from app.models.user import Account
from app.services import stock_trading, trading
from app.services.trade_math import TradeRefused
from tests.helpers import put_price
from tests.stock_trade_fixtures import ownership, status_case, stock_pair_case, stock_trade_case  # noqa: F401
from tests.test_stock_trading_service import trade_order


async def stock_request(factory, uid, settings, order):
    async with factory() as db:
        try:
            return await stock_trading.execute(db, user_id=uid, order=order, settings=settings)
        except TradeRefused as exc:
            return exc.code


async def books(factory, uid):
    async with factory() as db:
        cash = await db.scalar(select(Account.cash).where(Account.user_id == uid))
        counts = [
            (await db.scalar(select(func.count()).select_from(model).where(model.user_id == uid)))
            for model in (Trade, StockFillFacts, StockOwnershipMovement)
        ]
        positions = list(
            (
                await db.execute(
                    select(Holding.coin_id, Holding.quantity, Holding.cost_basis)
                    .where(Holding.user_id == uid)
                    .order_by(Holding.coin_id)
                )
            ).all()
        )
        return cash, counts, positions


@pytest.mark.parametrize("same_key", [False, True])
async def test_parallel_first_holdings_never_double_spend_or_double_fill(
    stock_trade_case, settings, same_key
):
    factory, cid, uid, now = stock_trade_case
    async with factory.begin() as db:
        await db.execute(update(Account).where(Account.user_id == uid).values(cash=Decimal(510)))
    key = uuid4()
    async with asyncio.timeout(15):
        results = await asyncio.gather(
            *(
                stock_request(
                    factory,
                    uid,
                    settings,
                    trade_order(quantity="1", idempotency_key=key if same_key else uuid4()),
                )
                for _ in range(10)
            )
        )
    successful = [r for r in results if isinstance(r, tuple)]
    cash, counts, positions = await books(factory, uid)
    if same_key:
        assert len(successful) == 10 and sum(r[1] for r in successful) == 1
        assert all(r[0] == successful[0][0] for r in successful)
        assert (
            cash == 408 and counts == [1, 1, 1] and positions == [(cid, Decimal(1), Decimal(102))]
        )
    else:
        assert len(successful) == 5 and results.count("insufficient_cash") == 5
        assert cash == 0 and counts == [5, 5, 5] and positions == [(cid, Decimal(5), Decimal(510))]


async def test_concurrent_sells_never_oversell(stock_trade_case, settings):
    factory, cid, uid, now = stock_trade_case
    assert (await stock_request(factory, uid, settings, trade_order(quantity="3")))[1]
    async with asyncio.timeout(15):
        results = await asyncio.gather(
            *(
                stock_request(
                    factory,
                    uid,
                    settings,
                    trade_order(side="sell", quantity="1", expected_exec_price="100"),
                )
                for _ in range(8)
            )
        )
    assert sum(isinstance(r, tuple) for r in results) == 3
    assert results.count("insufficient_holding") == 5
    cash, counts, positions = await books(factory, uid)
    assert cash == 9994 and counts == [4, 4, 4] and positions == [(cid, Decimal(0), Decimal(0))]


async def test_different_stocks_compete_for_same_cash(stock_pair_case, settings):
    factory, ids, uid, now = stock_pair_case
    async with factory.begin() as db:
        await db.execute(update(Account).where(Account.user_id == uid).values(cash=Decimal(102)))
        symbols = list(
            (await db.scalars(select(Coin.symbol).where(Coin.id.in_(ids)).order_by(Coin.id))).all()
        )
    async with asyncio.timeout(15):
        results = await asyncio.gather(
            *(
                stock_request(factory, uid, settings, trade_order(symbol=symbol, quantity="1"))
                for symbol in symbols
            )
        )
    assert sum(isinstance(r, tuple) for r in results) == 1
    assert results.count("insufficient_cash") == 1
    cash, counts, positions = await books(factory, uid)
    assert cash == 0 and counts == [1, 1, 1] and len(positions) == 1


@pytest.mark.parametrize("same_key", [False, True])
async def test_stock_crypto_competing_spends_and_keys(
    stock_trade_case, settings, engine, clean_prices, same_key
):
    factory, cid, uid, now = stock_trade_case
    await put_price(engine, "BTC", "100", now)
    async with factory.begin() as db:
        await db.execute(update(Account).where(Account.user_id == uid).values(cash=Decimal(102)))
    key = uuid4()

    async def crypto():
        async with factory() as db:
            try:
                return await trading.execute(
                    db,
                    user_id=uid,
                    order=trading.Order("BTC", "buy", "usd", Decimal(102)),
                    expected_mid=Decimal(100),
                    idempotency_key=key if same_key else uuid4(),
                    settings=settings,
                )
            except TradeRefused as exc:
                return exc.code

    async with asyncio.timeout(15):
        results = await asyncio.gather(
            stock_request(factory, uid, settings, trade_order(quantity="1", idempotency_key=key)),
            crypto(),
        )
    assert sum(isinstance(r, tuple) for r in results) == 1
    assert results.count("idempotency_conflict" if same_key else "insufficient_cash") == 1
    cash, counts, positions = await books(factory, uid)
    assert cash == 0 and counts[0] == 1
    assert counts[1:] in ([0, 0], [1, 1])


async def test_multi_user_multi_stock_lock_graph_completes(stock_pair_case, settings, new_user):
    factory, ids, uid, now = stock_pair_case
    other = await new_user()
    async with factory() as db:
        symbols = list(
            (await db.scalars(select(Coin.symbol).where(Coin.id.in_(ids)).order_by(Coin.id))).all()
        )
    # All holders exist, so each journal append locks both users in stable order.
    for user in (uid, other):
        for symbol in symbols:
            assert (
                await stock_request(
                    factory, user, settings, trade_order(symbol=symbol, quantity="1")
                )
            )[1]
    async with asyncio.timeout(15):
        results = await asyncio.gather(
            *(
                stock_request(factory, user, settings, trade_order(symbol=symbol, quantity="1"))
                for user, symbol in (
                    (uid, symbols[0]),
                    (other, symbols[1]),
                    (uid, symbols[1]),
                    (other, symbols[0]),
                )
            )
        )
    assert all(isinstance(r, tuple) and r[1] for r in results)
    for user in (uid, other):
        cash, counts, positions = await books(factory, user)
        assert cash == 9592 and counts == [4, 4, 4]
        assert all(p[1:] == (Decimal(2), Decimal(204)) for p in positions)


@pytest.mark.parametrize("next_asset", ["stock", "crypto"])
async def test_stock_sale_cash_is_immediately_reusable(
    stock_trade_case, settings, engine, clean_prices, next_asset
):
    factory, cid, uid, now = stock_trade_case
    await put_price(engine, "BTC", "100", now)
    async with factory.begin() as db:
        await db.execute(update(Account).where(Account.user_id == uid).values(cash=Decimal(204)))
    await stock_request(factory, uid, settings, trade_order())
    sale = await stock_request(
        factory, uid, settings, trade_order(side="sell", expected_exec_price="100")
    )
    assert sale[0].cash_after == 200
    if next_asset == "stock":
        result = await stock_request(factory, uid, settings, trade_order(quantity="1"))
        assert result[1] and result[0].cash_after == 98
    else:
        async with factory() as db:
            fill, created = await trading.execute(
                db,
                user_id=uid,
                order=trading.Order("BTC", "buy", "usd", Decimal(200)),
                expected_mid=Decimal(100),
                idempotency_key=uuid4(),
                settings=settings,
            )
            assert created and fill.cash_after == 0
