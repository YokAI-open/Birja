"""Real0017 crypto transactions with independent owned roots and sessions."""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.price import Price
from app.models.trade import Holding, Trade
from app.models.user import Account
from app.services import trading
from app.services.portfolios import OwnedActivePortfolio
from app.services.trade_math import TradeRefused
from tests.helpers import coin_id, put_price


@pytest_asyncio.fixture
async def crypto_books(engine, new_user, clean_prices):
    uid, other = await new_user(), await new_user()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    cid = await coin_id(engine, "BTC")
    async with factory() as db:
        first = (await db.execute(select(Account).where(Account.user_id == uid))).scalar_one()
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
            closed_at=datetime.now(UTC),
        )
        db.add_all([sibling, closed])
        await db.flush()
        foreign = (await db.execute(select(Account).where(Account.user_id == other))).scalar_one()
        for root, qty, basis in ((first, "0.1", "123"), (sibling, "0.2", "456")):
            db.add(
                Holding(
                    portfolio_id=root.id,
                    user_id=uid,
                    coin_id=cid,
                    quantity=Decimal(qty),
                    cost_basis=Decimal(basis),
                )
            )
        roots = [OwnedActivePortfolio(a.id, uid) for a in (first, sibling, closed, foreign)]
        await db.commit()
    await put_price(engine, "BTC", "100", datetime.now(UTC))
    return factory, roots, cid


async def fill(
    factory,
    root,
    settings,
    *,
    key=None,
    value="1",
    kind="quantity",
    symbol="BTC",
    side="buy",
    expected="100",
):
    async with factory() as db:
        return await trading.execute(
            db,
            portfolio=root,
            order=trading.Order(symbol, side, kind, Decimal(value)),
            expected_mid=Decimal(expected),
            idempotency_key=key or uuid4(),
            settings=settings,
        )


async def snapshot(factory, root):
    async with factory() as db:
        account = (
            await db.execute(
                select(Account.cash, Account.starting_cash).where(Account.id == root.portfolio_id)
            )
        ).one()
        rows = (
            await db.execute(
                select(Holding.quantity, Holding.cost_basis).where(
                    Holding.portfolio_id == root.portfolio_id
                )
            )
        ).all()
        return account, rows


async def test_quote_and_fill_preserve_exact_crypto_economics(crypto_books, settings):
    factory, (first, sibling, *_), _ = crypto_books
    before = await snapshot(factory, sibling)
    async with factory() as db:
        quote = await trading.quote(
            db,
            portfolio=first,
            order=trading.Order("BTC", "buy", "quantity", Decimal("1")),
            settings=settings,
        )
        assert quote.portfolio_id == first.portfolio_id
        assert quote.plan.exec_price == Decimal("100.25")
        assert quote.plan.fee == Decimal("0.25")
        assert quote.plan.cash_delta == Decimal("-100.50")
        assert quote.plan.held_before == Decimal("0.1")
    receipt, created = await fill(factory, first, settings)
    assert created and receipt.portfolio_id == first.portfolio_id
    assert receipt.cash_after == Decimal("899.50") and receipt.quantity == Decimal("1")
    assert (await snapshot(factory, first))[1] == [(Decimal("1.1"), Decimal("223.50"))]
    assert await snapshot(factory, sibling) == before


async def test_holding_reads_exact_sibling(crypto_books):
    factory, roots, _ = crypto_books
    async with factory() as db:
        assert await trading.holding_quantity(db, portfolio=roots[0], symbol="btc") == (
            "BTC",
            Decimal("0.1"),
        )
        assert await trading.holding_quantity(db, portfolio=roots[1], symbol="BTC") == (
            "BTC",
            Decimal("0.2"),
        )


async def test_original_active_receipt_replays_before_current_price_gates(
    crypto_books, settings, engine
):
    factory, (root, *_), cid = crypto_books
    key = uuid4()
    original, created = await fill(factory, root, settings, key=key)
    async with engine.begin() as conn:
        await conn.execute(
            update(Price)
            .where(Price.coin_id == cid)
            .values(as_of=datetime.now(UTC) - timedelta(days=3), mid=Decimal("700"))
        )
    before = await snapshot(factory, root)
    replay, created = await fill(factory, root, settings, key=key, expected="999")
    assert not created and replay == original
    assert await snapshot(factory, root) == before


@pytest.mark.parametrize("change", ["root", "payload", "symbol", "side", "kind"])
async def test_global_key_compares_original_root_and_payload(crypto_books, settings, change):
    factory, (root, sibling, *_), _ = crypto_books
    key = uuid4()
    await fill(factory, root, settings, key=key)
    options = {"key": key}
    target = root
    if change == "root":
        target = sibling
    elif change == "payload":
        options["value"] = "2"
    elif change == "symbol":
        options["symbol"] = "ETH"
    elif change == "side":
        options["side"] = "sell"
    else:
        options["kind"] = "usd"
    before = await snapshot(factory, sibling)
    with pytest.raises(TradeRefused, match="different order") as exc:
        await fill(factory, target, settings, **options)
    assert exc.value.code == "idempotency_conflict"
    assert await snapshot(factory, sibling) == before


@pytest.mark.parametrize("operation", ["quote", "holding", "execute"])
@pytest.mark.parametrize("target", ["closed", "foreign", "missing"])
async def test_unavailable_target_rechecked_in_every_service(
    crypto_books, settings, operation, target
):
    factory, roots, _ = crypto_books
    root = (
        roots[2]
        if target == "closed"
        else roots[3]
        if target == "foreign"
        else OwnedActivePortfolio(9223372036854775807, roots[0].user_id)
    )
    with pytest.raises(HTTPException) as exc:
        async with factory() as db:
            if operation == "quote":
                await trading.quote(
                    db,
                    portfolio=root,
                    order=trading.Order("BTC", "buy", "quantity", Decimal(1)),
                    settings=settings,
                )
            elif operation == "holding":
                await trading.holding_quantity(db, portfolio=root, symbol="BTC")
            else:
                await fill(factory, root, settings)
    assert exc.value.status_code == 404 and exc.value.detail == {"code": "portfolio_unavailable"}


async def test_stale_resolved_root_cannot_replay_after_closure(crypto_books, settings, engine):
    factory, (root, *_), _ = crypto_books
    key = uuid4()
    await fill(factory, root, settings, key=key)
    async with engine.begin() as conn:
        await conn.execute(
            update(Account)
            .where(Account.id == root.portfolio_id)
            .values(closed_at=datetime.now(UTC))
        )
    with pytest.raises(HTTPException) as exc:
        await fill(factory, root, settings, key=key)
    assert exc.value.status_code == 404


async def test_same_root_concurrent_spend_is_serialized(crypto_books, settings):
    factory, (root, *_), _ = crypto_books
    results = await asyncio.gather(
        *(fill(factory, root, settings, value="800", kind="usd") for _ in range(2)),
        return_exceptions=True,
    )
    assert sum(isinstance(r, tuple) for r in results) == 1
    errors = [r for r in results if isinstance(r, TradeRefused)]
    assert len(errors) == 1 and errors[0].code == "insufficient_cash"
    assert (await snapshot(factory, root))[0].cash == Decimal("200")


async def test_siblings_can_spend_independently(crypto_books, settings):
    factory, (first, sibling, *_), _ = crypto_books
    results = await asyncio.gather(
        *(fill(factory, r, settings, value="800", kind="usd") for r in (first, sibling))
    )
    assert all(created for _, created in results)
    assert (await snapshot(factory, first))[0].cash == Decimal("200")
    assert (await snapshot(factory, sibling))[0].cash == Decimal("1200")


async def test_duplicate_response_loss_and_concurrent_retry_one_effect(crypto_books, settings):
    factory, (root, *_), _ = crypto_books
    key = uuid4()
    results = await asyncio.gather(*(fill(factory, root, settings, key=key) for _ in range(2)))
    assert sum(created for _, created in results) == 1
    assert results[0][0] == results[1][0]
    assert (await snapshot(factory, root))[0].cash == Decimal("899.50")
    async with factory() as db:
        assert (
            await db.execute(
                select(func.count())
                .select_from(Trade)
                .where(Trade.user_id == root.user_id, Trade.idempotency_key == key)
            )
        ).scalar_one() == 1


async def test_same_user_key_race_across_roots_never_returns_foreign_receipt(
    crypto_books, settings
):
    factory, (first, sibling, *_), _ = crypto_books
    key = uuid4()
    results = await asyncio.gather(
        *(fill(factory, r, settings, key=key) for r in (first, sibling)), return_exceptions=True
    )
    successes = [r for r in results if isinstance(r, tuple)]
    errors = [r for r in results if isinstance(r, TradeRefused)]
    assert len(successes) == len(errors) == 1
    assert errors[0].code == "idempotency_conflict"
    cash = [(await snapshot(factory, r))[0].cash for r in (first, sibling)]
    assert sum(cash) == Decimal("2899.50")


async def test_price_change_is_read_only_and_quote_stays_in_original_root(crypto_books, settings):
    factory, (root, *_), _ = crypto_books
    before = await snapshot(factory, root)
    with pytest.raises(trading.PriceChanged) as exc:
        await fill(factory, root, settings, expected="99")
    assert exc.value.quote.portfolio_id == root.portfolio_id
    assert await snapshot(factory, root) == before


async def test_restricted_application_role_can_create_only_target_holding(
    crypto_books, settings, engine
):
    factory, (root, sibling, *_), _ = crypto_books
    await put_price(engine, "ETH", "100", datetime.now(UTC))
    before = await snapshot(factory, sibling)
    async with factory() as db:
        await db.execute(text("SET LOCAL ROLE birja_app"))
        receipt, created = await trading.execute(
            db,
            portfolio=root,
            order=trading.Order("ETH", "buy", "quantity", Decimal("1")),
            expected_mid=Decimal("100"),
            idempotency_key=uuid4(),
            settings=settings,
        )
    assert created and receipt.cash_after == Decimal("899.50")
    async with factory() as db:
        await db.execute(text("SET LOCAL ROLE birja_app"))
        assert await trading.holding_quantity(db, portfolio=root, symbol="ETH") == (
            "ETH",
            Decimal("1"),
        )
        assert await trading.holding_quantity(db, portfolio=sibling, symbol="ETH") == (
            "ETH",
            Decimal("0"),
        )
    assert await snapshot(factory, sibling) == before
