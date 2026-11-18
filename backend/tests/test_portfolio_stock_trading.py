"""Actual0017 stock services with independent roots, receipts and transactions."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import func, select, text, update

from app.models.price import Coin
from app.models.stock import StockDataAdmission
from app.models.stock_execution import StockFillFacts
from app.models.trade import Holding, Trade
from app.models.user import Account
from app.schemas.stock_trades import QuoteIn, TradeIn
from app.services import stock_trading, trading
from app.services.portfolios import OwnedActivePortfolio
from app.services.trade_math import TradeRefused
from tests.helpers import put_price
from tests.stock_trade_fixtures import ownership, status_case, stock_trade_case

__all__ = ["ownership", "status_case", "stock_trade_case"]


@pytest_asyncio.fixture
async def stock_books(stock_trade_case, new_user):
    factory, cid, uid, now = stock_trade_case
    foreign_uid = await new_user()
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
            closed_at=now,
        )
        db.add_all([sibling, closed])
        await db.flush()
        foreign = (await db.scalars(select(Account).where(Account.user_id == foreign_uid))).one()
        roots = [OwnedActivePortfolio(a.id, uid) for a in (first, sibling, closed, foreign)]
    return factory, cid, roots, now


def order(**changes):
    return TradeIn.model_validate(
        {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": "2",
            "expected_exec_price": "102",
            "idempotency_key": str(uuid4()),
            **changes,
        }
    )


async def execute(factory, root, settings, body=None):
    async with factory() as db:
        return await stock_trading.execute(
            db, portfolio=root, order=body or order(), settings=settings
        )


async def snapshot(factory, root):
    async with factory() as db:
        money = (
            await db.execute(
                select(Account.cash, Account.starting_cash).where(Account.id == root.portfolio_id)
            )
        ).one()
        holdings = (
            await db.execute(
                select(Holding.coin_id, Holding.quantity, Holding.cost_basis)
                .where(Holding.portfolio_id == root.portfolio_id)
                .order_by(Holding.coin_id)
            )
        ).all()
        fills = (
            await db.execute(
                select(Trade.__table__)
                .where(Trade.portfolio_id == root.portfolio_id)
                .order_by(Trade.id)
            )
        ).all()
        return money, holdings, fills


async def test_preview_context_and_exact_buy_sell_are_root_scoped(stock_books, settings):
    factory, cid, (root, sibling, *_), _ = stock_books
    before = await snapshot(factory, sibling)
    async with factory() as db:
        preview = await stock_trading.quote(
            db,
            portfolio=root,
            order=QuoteIn(symbol="AAPL", side="buy", quantity="2"),
            settings=settings,
        )
        assert preview.cash_before == 1000 and preview.exec_price == 102 and preview.fee == 0
        context = await stock_trading.context(db, portfolio=root, symbol="AAPL", settings=settings)
        assert context.cash == 1000 and context.held_quantity == 0
    receipt, created = await execute(factory, root, settings)
    assert created and receipt.cash_after == 796 and receipt.held_after == 2 and receipt.fee == 0
    sold, _ = await execute(
        factory, root, settings, order(side="sell", quantity="1", expected_exec_price="100")
    )
    assert sold.cash_after == 896 and sold.held_after == 1
    assert (await snapshot(factory, root))[1] == [(cid, Decimal(1), Decimal(102))]
    assert await snapshot(factory, sibling) == before


async def test_same_owner_sibling_same_symbol_keeps_independent_basis(stock_books, settings):
    factory, cid, (root, sibling, *_), _ = stock_books
    await execute(factory, root, settings)
    await execute(factory, sibling, settings, order(quantity="3"))
    assert (await snapshot(factory, root))[:2] == (
        (Decimal(796), Decimal(10000)),
        [(cid, Decimal(2), Decimal(204))],
    )
    assert (await snapshot(factory, sibling))[:2] == (
        (Decimal(1694), Decimal(7654)),
        [(cid, Decimal(3), Decimal(306))],
    )


@pytest.mark.parametrize("target", ["foreign", "closed", "unknown"])
@pytest.mark.parametrize("operation", ["quote", "context", "execute"])
async def test_unavailable_root_refused_before_market_or_receipt(
    stock_books, settings, target, operation
):
    factory, _, roots, _ = stock_books
    root = (
        roots[3]
        if target == "foreign"
        else roots[2]
        if target == "closed"
        else OwnedActivePortfolio(9223372036854775807, roots[0].user_id)
    )
    async with factory() as db:
        with pytest.raises(HTTPException) as exc:
            if operation == "execute":
                await stock_trading.execute(db, portfolio=root, order=order(), settings=settings)
            elif operation == "quote":
                await stock_trading.quote(
                    db,
                    portfolio=root,
                    order=QuoteIn(symbol="AAPL", side="buy", quantity="2"),
                    settings=settings,
                )
            else:
                await stock_trading.context(db, portfolio=root, symbol="AAPL", settings=settings)
        assert exc.value.status_code == 404 and exc.value.detail == {
            "code": "portfolio_unavailable"
        }


@pytest.mark.parametrize("change", [{"quantity": "3"}, {"side": "sell"}, {"symbol": "MSFT"}])
async def test_original_payload_conflicts_without_financial_effect(stock_books, settings, change):
    factory, _, (root, *_), _ = stock_books
    body = order()
    await execute(factory, root, settings, body)
    before = await snapshot(factory, root)
    with pytest.raises(TradeRefused, match="already used"):
        await execute(factory, root, settings, order(**{**body.model_dump(mode="json"), **change}))
    assert await snapshot(factory, root) == before


async def test_global_key_cannot_replay_sibling_and_original_survives_market_denial(
    stock_books, settings
):
    factory, cid, (root, sibling, *_), _ = stock_books
    body = order()
    original, _ = await execute(factory, root, settings, body)
    with pytest.raises(TradeRefused) as exc:
        await execute(factory, sibling, settings, body)
    assert exc.value.code == "idempotency_conflict"
    before = await snapshot(factory, root)
    async with factory.begin() as db:
        await db.execute(update(StockDataAdmission).values(state="denied"))
        await db.execute(update(Coin).where(Coin.id == cid).values(is_active=False))
    try:
        replay, created = await execute(
            factory, root, settings, body.model_copy(update={"expected_exec_price": Decimal(999)})
        )
        assert not created and replay == original
        assert await snapshot(factory, root) == before
    finally:
        async with factory.begin() as db:
            await db.execute(update(Coin).where(Coin.id == cid).values(is_active=True))


async def test_closed_original_has_no_receipt(stock_books, settings):
    factory, _, (root, *_), _ = stock_books
    body = order()
    await execute(factory, root, settings, body)
    async with factory() as db:
        # The local transition rolls back after refusal; committed closed roots
        # are independently covered by unavailable-root cases above.
        await db.execute(
            update(Account)
            .where(Account.id == root.portfolio_id)
            .values(closed_at=datetime.now(UTC))
        )
        with pytest.raises(HTTPException) as exc:
            await stock_trading.execute(db, portfolio=root, order=body, settings=settings)
        assert exc.value.status_code == 404


@pytest.mark.parametrize("same_key", [False, True])
async def test_stock_crypto_race_shares_only_selected_cash(
    stock_books, settings, engine, clean_prices, same_key
):
    factory, _, (root, sibling, *_), now = stock_books
    await put_price(engine, "BTC", "100", now)
    async with factory.begin() as db:
        await db.execute(
            update(Account).where(Account.id == root.portfolio_id).values(cash=Decimal(102))
        )
    sibling_before = await snapshot(factory, sibling)
    key = uuid4()

    async def stock():
        try:
            return await execute(
                factory, root, settings, order(quantity="1", idempotency_key=str(key))
            )
        except TradeRefused as exc:
            return exc.code

    async def crypto():
        async with factory() as db:
            try:
                return await trading.execute(
                    db,
                    portfolio=root,
                    order=trading.Order("BTC", "buy", "usd", Decimal(102)),
                    expected_mid=Decimal(100),
                    idempotency_key=key if same_key else uuid4(),
                    settings=settings,
                )
            except TradeRefused as exc:
                return exc.code

    async with asyncio.timeout(15):
        results = await asyncio.gather(stock(), crypto())
    assert sum(isinstance(r, tuple) for r in results) == 1
    assert results.count("idempotency_conflict" if same_key else "insufficient_cash") == 1
    assert (await snapshot(factory, root))[0][0] == 0
    assert await snapshot(factory, sibling) == sibling_before


@pytest.mark.parametrize("first_asset", ["stock", "crypto"])
async def test_cross_asset_original_keys_conflict_in_both_directions(
    stock_books, settings, engine, clean_prices, first_asset
):
    factory, _, (root, *_), now = stock_books
    await put_price(engine, "BTC", "100", now)
    key = uuid4()

    async def crypto():
        async with factory() as db:
            return await trading.execute(
                db,
                portfolio=root,
                order=trading.Order("BTC", "buy", "quantity", Decimal(1)),
                expected_mid=Decimal(100),
                idempotency_key=key,
                settings=settings,
            )

    async def stock():
        return await execute(factory, root, settings, order(idempotency_key=str(key)))

    first, second = (stock, crypto) if first_asset == "stock" else (crypto, stock)
    assert (await first())[1]
    before = await snapshot(factory, root)
    with pytest.raises(TradeRefused) as exc:
        await second()
    assert exc.value.code == "idempotency_conflict"
    assert await snapshot(factory, root) == before


async def test_inner_stock_readers_never_substitute_a_root_or_crypto_receipt(
    stock_books, settings, engine, clean_prices
):
    factory, coin, (root, *_), now = stock_books
    await put_price(engine, "BTC", "100", now)
    key = uuid4()
    async with factory() as db:
        await trading.execute(
            db,
            portfolio=root,
            order=trading.Order("BTC", "buy", "quantity", Decimal(2)),
            expected_mid=Decimal(100),
            idempotency_key=key,
            settings=settings,
        )
    before = await snapshot(factory, root)
    async with factory() as db:
        with pytest.raises(HTTPException) as missing:
            await stock_trading._financial(
                db, OwnedActivePortfolio(9223372036854775807, root.user_id), coin
            )
        assert missing.value.status_code == 404
        assert missing.value.detail == {"code": "portfolio_unavailable"}
        with pytest.raises(TradeRefused) as conflict:
            await stock_trading._replay(db, root, order(idempotency_key=str(key)))
        assert conflict.value.code == "idempotency_conflict"
    assert await snapshot(factory, root) == before


@pytest.mark.parametrize("same_key", [False, True])
async def test_parallel_stock_requests_one_effect_or_no_overspend(stock_books, settings, same_key):
    factory, _, (root, *_), _ = stock_books
    async with factory.begin() as db:
        await db.execute(
            update(Account).where(Account.id == root.portfolio_id).values(cash=Decimal(204))
        )
    key = str(uuid4())

    async def request():
        try:
            return await execute(
                factory,
                root,
                settings,
                order(quantity="1", idempotency_key=key if same_key else str(uuid4())),
            )
        except TradeRefused as exc:
            return exc.code

    async with asyncio.timeout(15):
        results = await asyncio.gather(*(request() for _ in range(5)))
    successful = [r for r in results if isinstance(r, tuple)]
    assert len(successful) == (5 if same_key else 2)
    assert sum(r[1] for r in successful) == (1 if same_key else 2)
    assert len((await snapshot(factory, root))[2]) == (1 if same_key else 2)


async def test_reprice_requires_confirmation_and_rolls_back(stock_books, settings):
    factory, _, (root, *_), _ = stock_books
    before = await snapshot(factory, root)
    with pytest.raises(stock_trading.PriceChanged) as exc:
        await execute(factory, root, settings, order(expected_exec_price="101"))
    assert exc.value.quote.exec_price == 102 and exc.value.detail.cash_delta_change == -2
    assert await snapshot(factory, root) == before


async def test_closure_while_waiting_for_root_refuses_new_fill(stock_books, settings, monkeypatch):
    factory, _, (root, *_), _ = stock_books
    waiting = asyncio.Event()
    original = stock_trading._account

    async def observe(db, portfolio, *, lock=False):
        if lock:
            waiting.set()
        return await original(db, portfolio, lock=lock)

    monkeypatch.setattr(stock_trading, "_account", observe)
    async with factory() as closer:
        await closer.execute(
            select(Account).where(Account.id == root.portfolio_id).with_for_update()
        )
        pending = asyncio.create_task(execute(factory, root, settings))
        async with asyncio.timeout(10):
            await waiting.wait()
            await closer.execute(
                update(Account)
                .where(Account.id == root.portfolio_id)
                .values(closed_at=datetime.now(UTC))
            )
            await closer.commit()
            with pytest.raises(HTTPException) as exc:
                await pending
        assert exc.value.status_code == 404
    assert (await snapshot(factory, root))[2] == []


async def test_actual_restricted_app_can_create_paired_stock_receipt(stock_books, settings):
    factory, _, (root, *_), _ = stock_books
    async with factory() as db:
        await db.execute(text("SET LOCAL ROLE birja_app"))
        receipt, created = await stock_trading.execute(
            db, portfolio=root, order=order(), settings=settings
        )
        assert created and receipt.cash_after == 796
    async with factory() as db:
        assert (
            await db.scalar(
                select(func.count())
                .select_from(StockFillFacts)
                .where(StockFillFacts.portfolio_id == root.portfolio_id)
            )
            == 1
        )
