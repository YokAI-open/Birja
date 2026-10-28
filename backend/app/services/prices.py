from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.price import Coin, Price

PriceStatus = Literal["fresh", "aging", "stale"]


def age_seconds(as_of: datetime, now: datetime) -> int:
    """Whole seconds between as_of and now; negative skew clamps to 0."""
    return max(0, int((now - as_of).total_seconds()))


def freshness(age: int, fresh_seconds: int, stale_seconds: int) -> PriceStatus:
    """D-03: under fresh_seconds is fresh, up to stale_seconds is aging, beyond is stale."""
    if age < fresh_seconds:
        return "fresh"
    if age <= stale_seconds:
        return "aging"
    return "stale"


@dataclass(frozen=True)
class PriceRow:
    symbol: str
    name: str
    price: Decimal
    as_of: datetime
    age_seconds: int
    status: PriceStatus


async def list_prices(
    db: AsyncSession, settings: Settings, now: datetime | None = None
) -> list[PriceRow]:
    now = now or datetime.now(UTC)
    result = await db.execute(
        select(Coin.symbol, Coin.name, Price.mid, Price.as_of)
        .join(Price, Price.coin_id == Coin.id)
        .where(Coin.is_active)
        .order_by(Coin.sort_order, Coin.id)
    )
    rows: list[PriceRow] = []
    for symbol, name, mid, as_of in result:
        age = age_seconds(as_of, now)
        rows.append(
            PriceRow(
                symbol=symbol,
                name=name,
                price=mid,
                as_of=as_of,
                age_seconds=age,
                status=freshness(age, settings.price_fresh_seconds, settings.price_stale_seconds),
            )
        )
    return rows


@dataclass(frozen=True)
class CoinState:
    coin_id: int
    symbol: str
    kraken_pair: str
    last_mid: Decimal | None


async def load_active_coins(db: AsyncSession) -> list[CoinState]:
    """Active coins in display order with their last good mid (None if never priced)."""
    result = await db.execute(
        select(Coin.id, Coin.symbol, Coin.kraken_pair, Price.mid)
        .outerjoin(Price, Price.coin_id == Coin.id)
        .where(Coin.is_active)
        .order_by(Coin.sort_order, Coin.id)
    )
    return [CoinState(cid, symbol, pair, mid) for cid, symbol, pair, mid in result]


@dataclass(frozen=True)
class AcceptedPrice:
    coin_id: int
    mid: Decimal
    as_of: datetime


async def upsert_prices(db: AsyncSession, rows: Sequence[AcceptedPrice], source: str) -> int:
    """Insert or update prices in one statement; as_of never moves backwards.

    The caller commits. Returns the number of rows inserted or updated.
    """
    if not rows:
        return 0
    stmt = insert(Price).values(
        [{"coin_id": r.coin_id, "mid": r.mid, "as_of": r.as_of, "source": source} for r in rows]
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[Price.coin_id],
        set_={
            "mid": stmt.excluded.mid,
            "as_of": stmt.excluded.as_of,
            "source": stmt.excluded.source,
        },
        where=Price.as_of < stmt.excluded.as_of,
    )
    result = await db.execute(stmt)
    return int(result.rowcount)  # type: ignore[attr-defined]
