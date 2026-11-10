"""A read-only, user-scoped financial statement snapshot."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.price import Coin, Price
from app.models.trade import Holding
from app.models.user import Account
from app.services.portfolio_math import (
    PortfolioValue,
    PositionInput,
    PositionValue,
    calculate_portfolio,
)
from app.services.prices import age_seconds, freshness

PortfolioPriceStatus = Literal["fresh", "aging", "stale", "unpriced"]


@dataclass(frozen=True)
class HoldingValue(PositionValue):
    age_seconds: int | None
    status: PortfolioPriceStatus


@dataclass(frozen=True)
class PortfolioSnapshot(PortfolioValue):
    holdings: tuple[HoldingValue, ...]
    valued_at: datetime
    prices_as_of: datetime | None
    fresh_seconds: int
    stale_seconds: int


async def get_portfolio(
    db: AsyncSession, *, user_id: int, settings: Settings, now: datetime | None = None
) -> PortfolioSnapshot:
    # Scalar columns prevent identity-map reuse or lazy reads. The positive-quantity
    # predicate stays in ON so a cash-only account still produces one row.
    result = await db.execute(
        select(
            Account.cash,
            Account.starting_cash,
            Coin.symbol,
            Coin.name,
            Coin.is_active,
            Holding.quantity,
            Holding.cost_basis,
            Price.mid,
            Price.as_of,
        )
        .select_from(Account)
        .outerjoin(Holding, and_(Holding.user_id == Account.user_id, Holding.quantity > 0))
        .outerjoin(Coin, Coin.id == Holding.coin_id)
        .outerjoin(Price, Price.coin_id == Coin.id)
        .where(Account.user_id == user_id)
        .order_by(Coin.sort_order, Coin.id)
    )
    valued_at = now or datetime.now(UTC)  # Sample after the awaited statement.
    rows = result.all()
    if not rows:
        raise RuntimeError("Authenticated user has no account")
    positions = [PositionInput(*row[2:]) for row in rows if row.symbol is not None]
    value = calculate_portfolio(rows[0].cash, rows[0].starting_cash, positions)
    holdings = []
    for p in value.holdings:
        age = age_seconds(p.as_of, valued_at) if p.as_of is not None else None
        status: PortfolioPriceStatus = (
            freshness(age, settings.price_fresh_seconds, settings.price_stale_seconds)
            if age is not None
            else "unpriced"
        )
        holdings.append(HoldingValue(**asdict(p), age_seconds=age, status=status))
    return PortfolioSnapshot(
        **{key: val for key, val in asdict(value).items() if key != "holdings"},
        holdings=tuple(holdings),
        valued_at=valued_at,
        prices_as_of=min((p.as_of for p in positions if p.as_of is not None), default=None),
        fresh_seconds=settings.price_fresh_seconds,
        stale_seconds=settings.price_stale_seconds,
    )
