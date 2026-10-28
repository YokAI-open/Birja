from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.core.config import Settings
from app.models.price import Coin, Price
from app.services.prices import age_seconds, freshness, list_prices

NOW = datetime(2026, 10, 28, 12, 0, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("age", "expected"),
    [
        (0, "fresh"),
        (119, "fresh"),
        (120, "aging"),
        (300, "aging"),
        (301, "stale"),
        (100000, "stale"),
    ],
)
def test_freshness_boundaries(age: int, expected: str) -> None:
    assert freshness(age, 120, 300) == expected


def test_freshness_uses_given_thresholds() -> None:
    assert freshness(10, 10, 20) == "aging"
    assert freshness(21, 10, 20) == "stale"


def test_age_floors_to_whole_seconds() -> None:
    assert age_seconds(NOW - timedelta(seconds=48, milliseconds=900), NOW) == 48


def test_age_clamps_negative_to_zero() -> None:
    assert age_seconds(NOW + timedelta(seconds=5), NOW) == 0


async def _coin_ids(engine: AsyncEngine) -> dict[str, int]:
    async with engine.connect() as conn:
        rows = await conn.execute(select(Coin.symbol, Coin.id))
        return {s: i for s, i in rows}


async def _set_price(engine: AsyncEngine, coin_id: int, mid: str, as_of: datetime) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            insert(Price).values(coin_id=coin_id, mid=Decimal(mid), as_of=as_of, source="fake")
        )


async def test_list_prices_empty(
    engine: AsyncEngine, settings: Settings, clean_prices: None
) -> None:
    async with async_sessionmaker(engine)() as db:
        assert await list_prices(db, settings, NOW) == []


async def test_list_prices_orders_by_sort_order_and_computes_status(
    engine: AsyncEngine, settings: Settings, clean_prices: None
) -> None:
    ids = await _coin_ids(engine)
    # inserted out of order on purpose
    await _set_price(engine, ids["DOGE"], "0.07998070", NOW - timedelta(seconds=400))
    await _set_price(engine, ids["BTC"], "81042.35", NOW - timedelta(seconds=48))
    await _set_price(engine, ids["ETH"], "2361.5", NOW - timedelta(seconds=150))

    async with async_sessionmaker(engine)() as db:
        rows = await list_prices(db, settings, NOW)

    assert [r.symbol for r in rows] == ["BTC", "ETH", "DOGE"]
    assert [(r.age_seconds, r.status) for r in rows] == [
        (48, "fresh"),
        (150, "aging"),
        (400, "stale"),
    ]
    assert rows[0].name == "Bitcoin"
    assert rows[0].price == Decimal("81042.35")
    assert rows[0].as_of == NOW - timedelta(seconds=48)


async def test_list_prices_defaults_now_to_clock(
    engine: AsyncEngine, settings: Settings, clean_prices: None
) -> None:
    ids = await _coin_ids(engine)
    await _set_price(engine, ids["BTC"], "1", datetime.now(UTC) - timedelta(seconds=10))
    async with async_sessionmaker(engine)() as db:
        rows = await list_prices(db, settings)
    assert 9 <= rows[0].age_seconds <= 15
    assert rows[0].status == "fresh"


@pytest_asyncio.fixture
async def inactive_coin(engine: AsyncEngine, migrated: None) -> AsyncIterator[int]:
    async with engine.begin() as conn:
        coin_id = (
            await conn.execute(
                insert(Coin)
                .values(
                    symbol="ZZZ",
                    name="Test coin",
                    kraken_pair="ZZZUSD",
                    sort_order=99,
                    is_active=False,
                )
                .returning(Coin.id)
            )
        ).scalar_one()
    yield coin_id
    async with engine.begin() as conn:
        await conn.execute(delete(Price).where(Price.coin_id == coin_id))
        await conn.execute(delete(Coin).where(Coin.id == coin_id))


async def test_inactive_coin_excluded(
    engine: AsyncEngine, settings: Settings, clean_prices: None, inactive_coin: int
) -> None:
    ids = await _coin_ids(engine)
    await _set_price(engine, ids["BTC"], "1", NOW)
    await _set_price(engine, inactive_coin, "2", NOW)
    async with async_sessionmaker(engine)() as db:
        rows = await list_prices(db, settings, NOW)
    assert [r.symbol for r in rows] == ["BTC"]
