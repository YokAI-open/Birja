"""Stock identities must never enter legacy crypto pricing or execution."""

from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.config import Settings
from app.models.price import Coin, Price
from app.models.trade import Holding, Trade
from app.services.portfolio import get_portfolio
from app.services.prices import AcceptedPrice, list_prices, load_active_coins, upsert_prices

NewUser = Callable[[], Awaitable[int]]

D = Decimal
NOW = datetime(2026, 11, 10, 14, tzinfo=UTC)


@pytest_asyncio.fixture
async def stock_id(engine: AsyncEngine, migrated: None) -> AsyncIterator[int]:
    async with engine.connect() as conn:
        cid = (await conn.execute(select(Coin.id).where(Coin.symbol == "AAPL"))).scalar_one()
    yield cid
    async with engine.begin() as conn:
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
