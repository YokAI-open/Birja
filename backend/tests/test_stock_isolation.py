"""Stock identities must never enter legacy crypto pricing or execution."""

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.config import Settings
from app.models.price import Coin, Price
from app.models.stock import StockQuote
from app.models.trade import Holding, Trade
from app.models.user import Account, User
from app.services import trading
from app.services.portfolio import get_portfolio
from app.services.prices import AcceptedPrice, list_prices, load_active_coins, upsert_prices
from app.services.trade_math import TradeRefused
from tests.helpers import OutboxSender, csrf_headers, put_price, sign_in, unique_email

NewUser = Callable[[], Awaitable[int]]

D = Decimal
NOW = datetime(2026, 11, 10, 14, tzinfo=UTC)


@pytest_asyncio.fixture
async def stock_id(engine: AsyncEngine, migrated: None) -> AsyncIterator[int]:
    async with engine.connect() as conn:
        cid = (await conn.execute(select(Coin.id).where(Coin.symbol == "AAPL"))).scalar_one()
    yield cid
    async with engine.begin() as conn:
        await conn.execute(delete(StockQuote).where(StockQuote.coin_id == cid))
        await conn.execute(delete(Trade).where(Trade.coin_id == cid))
        await conn.execute(delete(Holding).where(Holding.coin_id == cid))
        await conn.execute(delete(Price).where(Price.coin_id == cid))
        await conn.execute(update(Coin).where(Coin.id == cid).values(symbol="AAPL", is_active=True))


async def inject_price(engine: AsyncEngine, cid: int) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            insert(Price).values(coin_id=cid, mid=D("200"), as_of=NOW, source="fake")
        )


async def test_crypto_catalogue_and_prices_ignore_stock_even_with_collision(
    engine: AsyncEngine, db: AsyncSession, settings: Settings, clean_prices: None, stock_id: int
) -> None:
    async with engine.begin() as conn:
        original = (
            await conn.execute(
                select(Coin.id, Coin.symbol, Coin.kraken_pair)
                .where(Coin.asset_class == "crypto")
                .order_by(Coin.sort_order, Coin.id)
            )
        ).all()
        await conn.execute(update(Coin).where(Coin.id == stock_id).values(symbol="BTC"))
        await conn.execute(
            insert(Price),
            [dict(coin_id=row.id, mid=D("1"), as_of=NOW, source="fake") for row in original],
        )
    await inject_price(engine, stock_id)
    active = await load_active_coins(db)
    assert [(r.coin_id, r.symbol, r.kraken_pair) for r in active] == [tuple(r) for r in original]
    assert len(active) == 15
    listed = await list_prices(db, settings, NOW)
    assert [r.symbol for r in listed] == [r.symbol for r in original]
    assert all(r.price == D("1") for r in listed)


async def test_crypto_upsert_refuses_forged_stock_id(
    engine: AsyncEngine, db: AsyncSession, clean_prices: None, stock_id: int
) -> None:
    assert await upsert_prices(db, [AcceptedPrice(stock_id, D("200"), NOW)], "fake") == 0
    await db.commit()
    assert (await db.execute(select(Price).where(Price.coin_id == stock_id))).first() is None


async def test_held_stock_remains_visible_but_cannot_reuse_crypto_price(
    engine: AsyncEngine,
    db: AsyncSession,
    settings: Settings,
    clean_prices: None,
    stock_id: int,
    new_user: NewUser,
) -> None:
    user_id = await new_user()
    await inject_price(engine, stock_id)
    async with engine.begin() as conn:
        await conn.execute(
            insert(Holding).values(
                user_id=user_id, coin_id=stock_id, quantity=D("2"), cost_basis=D("300")
            )
        )
    snapshot = await get_portfolio(db, user_id=user_id, settings=settings, now=NOW)
    assert not snapshot.valuation_complete
    assert snapshot.total_value is None
    assert snapshot.prices_as_of is None
    assert len(snapshot.holdings) == 1
    held = snapshot.holdings[0]
    assert (held.symbol, held.quantity, held.cost_basis) == ("AAPL", D("2"), D("300"))
    assert (held.mid, held.as_of, held.current_value, held.status) == (None, None, None, "unpriced")
    assert not held.is_active


async def financial_rows(engine: AsyncEngine, user_id: int) -> tuple:
    async with engine.connect() as conn:
        snapshots = []
        for model in (Account, Holding, Trade):
            order = model.user_id if model is Account else model.id
            rows = await conn.execute(select(model).where(model.user_id == user_id).order_by(order))
            snapshots.append(tuple(rows.all()))
        return tuple(snapshots)


@pytest.mark.parametrize("active", [True, False])
@pytest.mark.parametrize("priced", [True, False])
async def test_stock_service_calls_refuse_without_financial_mutation(
    engine: AsyncEngine,
    db: AsyncSession,
    settings: Settings,
    clean_prices: None,
    stock_id: int,
    new_user: NewUser,
    active: bool,
    priced: bool,
) -> None:
    user_id = await new_user()
    async with engine.begin() as conn:
        await conn.execute(update(Coin).where(Coin.id == stock_id).values(is_active=active))
        await conn.execute(
            insert(Holding).values(
                user_id=user_id, coin_id=stock_id, quantity=D("2"), cost_basis=D("300")
            )
        )
    if priced:
        await inject_price(engine, stock_id)
        async with engine.begin() as conn:
            await conn.execute(
                insert(StockQuote).values(
                    coin_id=stock_id,
                    bid=D("199"),
                    ask=D("201"),
                    mid=D("200"),
                    event_at=NOW,
                    collected_at=NOW,
                    source="alpaca",
                    feed="iex",
                    session_date=NOW.date(),
                    admission_generation=1,
                )
            )
    before = await financial_rows(engine, user_id)
    for side in ("buy", "sell"):
        order = trading.Order("AAPL", side, "quantity", D("1"))
        with pytest.raises(TradeRefused, match="Unknown coin") as exc:
            await trading.quote(db, user_id=user_id, order=order, settings=settings, now=NOW)
        assert exc.value.code == "unknown_coin"
        with pytest.raises(TradeRefused) as exc:
            await trading.execute(
                db,
                user_id=user_id,
                order=order,
                settings=settings,
                now=NOW,
                expected_mid=D("200"),
                idempotency_key=uuid.uuid4(),
            )
        assert exc.value.code == "unknown_coin"
    with pytest.raises(TradeRefused) as exc:
        await trading.holding_quantity(db, user_id=user_id, symbol="AAPL")
    assert exc.value.code == "unknown_coin"
    assert await trading._held(db, user_id, stock_id) == D("0")
    assert await financial_rows(engine, user_id) == before


async def test_symbol_collision_selects_crypto_for_quote_execution_and_holding(
    engine: AsyncEngine,
    db: AsyncSession,
    settings: Settings,
    clean_prices: None,
    stock_id: int,
    new_user: NewUser,
) -> None:
    user_id = await new_user()
    await put_price(engine, "BTC", "100000", NOW)
    await inject_price(engine, stock_id)
    async with engine.begin() as conn:
        await conn.execute(update(Coin).where(Coin.id == stock_id).values(symbol="BTC"))
        await conn.execute(
            insert(Holding).values(
                user_id=user_id, coin_id=stock_id, quantity=D("99"), cost_basis=D("300")
            )
        )
    order = trading.Order("btc", "buy", "usd", D("100"))
    preview = await trading.quote(db, user_id=user_id, order=order, settings=settings, now=NOW)
    assert preview.plan.mid == D("100000")
    assert preview.plan.held_before == D("0")
    fill, created = await trading.execute(
        db,
        user_id=user_id,
        order=order,
        settings=settings,
        now=NOW,
        expected_mid=D("100000"),
        idempotency_key=uuid.uuid4(),
    )
    assert created
    assert fill.cash_after == D("9900")
    assert fill.quantity == D("0.00099501")
    assert await trading.holding_quantity(db, user_id=user_id, symbol="BTC") == (
        "BTC",
        fill.quantity,
    )
    async with engine.connect() as conn:
        filled_id = (
            await conn.execute(select(Trade.coin_id).where(Trade.id == fill.trade_id))
        ).scalar_one()
    assert filled_id != stock_id


async def test_stock_http_bypasses_are_refused_without_mutation(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
    stock_id: int,
) -> None:
    email = unique_email("stock")
    await sign_in(auth_client, outbox, email)
    headers = await csrf_headers(auth_client)
    async with engine.connect() as conn:
        user_id = (await conn.execute(select(User.id).where(User.email == email))).scalar_one()
    await inject_price(engine, stock_id)
    before = await financial_rows(engine, user_id)
    for side in ("buy", "sell"):
        body = {"symbol": "AAPL", "side": side, "quantity": "1"}
        quote = await auth_client.post("/api/v1/trades/quote", json=body, headers=headers)
        assert quote.status_code == 404
        assert quote.json()["detail"]["code"] == "unknown_coin"
        trade = await auth_client.post(
            "/api/v1/trades",
            json=body | {"expected_mid": "200", "idempotency_key": str(uuid.uuid4())},
            headers=headers,
        )
        assert trade.status_code == 404
        assert trade.json()["detail"]["code"] == "unknown_coin"
    assert (await auth_client.get("/api/v1/holdings/AAPL")).status_code == 404
    forged = await auth_client.post(
        "/api/v1/trades",
        json={
            "symbol": "BTC",
            "side": "buy",
            "quantity": "1",
            "coin_id": stock_id,
            "expected_mid": "200",
            "idempotency_key": str(uuid.uuid4()),
        },
        headers=headers,
    )
    assert forged.status_code == 422
    assert await financial_rows(engine, user_id) == before


async def test_stock_fill_cannot_be_replayed_through_crypto_execution(
    engine: AsyncEngine,
    db: AsyncSession,
    settings: Settings,
    stock_id: int,
    new_user: NewUser,
) -> None:
    user_id = await new_user()
    key = uuid.uuid4()
    async with engine.begin() as conn:
        await conn.execute(
            insert(Trade).values(
                user_id=user_id,
                coin_id=stock_id,
                side="buy",
                input_kind="quantity",
                input_value=D("1"),
                quantity=D("1"),
                mid_price=D("200"),
                price_as_of=NOW,
                exec_price=D("200"),
                fee=D("0"),
                cash_delta=D("-200"),
                cash_after=D("9800"),
                idempotency_key=key,
            )
        )
    before = await financial_rows(engine, user_id)
    with pytest.raises(TradeRefused) as exc:
        await trading.execute(
            db,
            user_id=user_id,
            order=trading.Order("AAPL", "buy", "quantity", D("1")),
            settings=settings,
            now=NOW,
            expected_mid=D("200"),
            idempotency_key=key,
        )
    assert exc.value.code == "unknown_coin"
    assert await financial_rows(engine, user_id) == before
