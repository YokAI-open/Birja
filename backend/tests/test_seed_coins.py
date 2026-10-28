from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.models.price import Coin, Price

EXPECTED_SYMBOLS = [
    "BTC",
    "ETH",
    "SOL",
    "XRP",
    "BNB",
    "ADA",
    "DOGE",
    "TRX",
    "AVAX",
    "LINK",
    "DOT",
    "LTC",
    "BCH",
    "XLM",
    "ATOM",
]

NOW = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)


async def _coins(engine: AsyncEngine) -> list[Coin]:
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        result = await session.scalars(select(Coin).order_by(Coin.sort_order, Coin.id))
        return list(result)


async def test_seed_has_the_fifteen_coins_in_market_cap_order(
    engine: AsyncEngine, migrated: None
) -> None:
    coins = await _coins(engine)
    seeded = [c for c in coins if c.symbol in EXPECTED_SYMBOLS]
    assert [c.symbol for c in seeded] == EXPECTED_SYMBOLS
    assert [c.sort_order for c in seeded] == list(range(1, 16))
    assert all(c.is_active for c in seeded)
    assert len({c.symbol for c in seeded}) == 15
    assert len({c.kraken_pair for c in seeded}) == 15


async def test_seed_uses_kraken_response_keys(engine: AsyncEngine, migrated: None) -> None:
    pairs = {c.symbol: c.kraken_pair for c in await _coins(engine)}
    assert pairs["DOGE"] == "XDGUSD"
    assert pairs["BTC"] == "XXBTZUSD"
    assert pairs["XLM"] == "XXLMZUSD"


async def _btc_id(engine: AsyncEngine) -> int:
    return next(c.id for c in await _coins(engine) if c.symbol == "BTC")


@pytest.mark.parametrize("mid", [Decimal(0), Decimal(-1)])
async def test_non_positive_mid_refused(
    engine: AsyncEngine, clean_prices: None, mid: Decimal
) -> None:
    coin_id = await _btc_id(engine)
    async with async_sessionmaker(engine)() as session:
        with pytest.raises(IntegrityError, match="ck_prices_mid_positive"):
            await session.execute(
                insert(Price).values(coin_id=coin_id, mid=mid, as_of=NOW, source="kraken")
            )
        await session.rollback()


async def test_second_price_row_for_same_coin_refused(
    engine: AsyncEngine, clean_prices: None
) -> None:
    coin_id = await _btc_id(engine)
    async with async_sessionmaker(engine)() as session:
        await session.execute(
            insert(Price).values(coin_id=coin_id, mid=Decimal(1), as_of=NOW, source="kraken")
        )
        with pytest.raises(IntegrityError, match="pk_prices"):
            await session.execute(
                insert(Price).values(coin_id=coin_id, mid=Decimal(2), as_of=NOW, source="kraken")
            )
        await session.rollback()


async def test_unknown_source_refused(engine: AsyncEngine, clean_prices: None) -> None:
    coin_id = await _btc_id(engine)
    async with async_sessionmaker(engine)() as session:
        with pytest.raises(IntegrityError, match="ck_prices_source_known"):
            await session.execute(
                insert(Price).values(coin_id=coin_id, mid=Decimal(1), as_of=NOW, source="other")
            )
        await session.rollback()


async def test_fake_source_accepted(engine: AsyncEngine, clean_prices: None) -> None:
    coin_id = await _btc_id(engine)
    async with async_sessionmaker(engine)() as session:
        await session.execute(
            insert(Price).values(coin_id=coin_id, mid=Decimal(1), as_of=NOW, source="fake")
        )
        await session.rollback()


async def test_lowercase_symbol_refused(engine: AsyncEngine, migrated: None) -> None:
    async with async_sessionmaker(engine)() as session:
        with pytest.raises(IntegrityError, match="ck_coins_symbol_upper"):
            await session.execute(
                insert(Coin).values(symbol="abc", name="Abc", kraken_pair="ABCUSD", sort_order=98)
            )
        await session.rollback()
