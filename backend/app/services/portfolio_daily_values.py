"""Forward-only private portfolio valuations from the current statement."""

from collections.abc import Callable
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import MarketValuationSettings
from app.models.portfolio_daily_value import PortfolioDailyValue
from app.models.user import Account
from app.services.portfolio import load_daily_portfolio_snapshot


def utc_now() -> datetime:
    return datetime.now(UTC)


def capture_window_day(at: datetime) -> date | None:
    at = at.astimezone(UTC)
    return at.date() if at.hour >= 22 else None


async def capture_portfolio_daily_value(
    db: AsyncSession,
    *,
    owner_id: int,
    portfolio_id: int,
    expected_day: date,
    settings: MarketValuationSettings,
    clock: Callable[[], datetime] = utc_now,
) -> bool:
    """Append the first complete or incomplete observation for this UTC day."""
    if capture_window_day(clock()) != expected_day:
        return False
    snapshot = await load_daily_portfolio_snapshot(
        db, owner_id=owner_id, portfolio_id=portfolio_id, settings=settings, clock=clock
    )
    if snapshot is None or capture_window_day(snapshot.valued_at) != expected_day:
        return False
    starting_cash = (
        await db.execute(
            select(Account.starting_cash).where(
                Account.id == portfolio_id, Account.user_id == owner_id
            )
        )
    ).scalar_one()
    if capture_window_day(clock()) != expected_day:
        return False
    return (
        await db.scalar(
            insert(PortfolioDailyValue)
            .values(
                portfolio_id=portfolio_id,
                user_id=owner_id,
                utc_day=expected_day,
                captured_at=snapshot.valued_at.astimezone(UTC),
                starting_cash=starting_cash,
                total_value=snapshot.total_value,
                valuation_complete=snapshot.valuation_complete,
            )
            .on_conflict_do_nothing(index_elements=["portfolio_id", "utc_day"])
            .returning(PortfolioDailyValue.portfolio_id)
        )
        is not None
    )
