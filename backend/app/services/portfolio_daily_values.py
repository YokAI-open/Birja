"""Forward-only private portfolio valuations from the current statement."""

import asyncio
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import MarketValuationSettings
from app.db.schema_contract import SchemaAdmissionError, require_schema
from app.models.portfolio_daily_value import PortfolioDailyValue
from app.models.user import Account
from app.schemas.portfolio_daily_values import (
    PortfolioDailyHistory,
    PortfolioDailyPoint,
    PortfolioDailySeries,
)
from app.services.portfolio import load_daily_portfolio_snapshot
from app.services.portfolios import fence_owned_active_portfolios


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


async def read_portfolio_daily_history(
    db: AsyncSession, *, owner_id: int, clock: Callable[[], datetime] = utc_now
) -> PortfolioDailyHistory:
    end_day = clock().astimezone(UTC).date()
    start_day = end_day - timedelta(days=29)
    daily = PortfolioDailyValue
    roots = (
        select(Account.id, Account.user_id)
        .where(Account.user_id == owner_id, Account.closed_at.is_(None))
        .order_by(Account.id)
        .limit(10)
        .cte("owned_daily_roots")
    )
    points: dict[int, list[PortfolioDailyPoint]] = {}
    try:
        async with asyncio.timeout(5):
            await require_schema(await db.connection(), consumer="portfolio_daily")
            rows = await db.execute(
                select(
                    roots.c.id,
                    daily.utc_day,
                    daily.captured_at,
                    daily.total_value,
                    daily.valuation_complete,
                )
                .select_from(roots)
                .outerjoin(
                    daily,
                    and_(
                        daily.portfolio_id == roots.c.id,
                        daily.user_id == roots.c.user_id,
                        daily.utc_day.between(start_day, end_day),
                    ),
                )
                .order_by(roots.c.id, daily.utc_day)
            )
            for row in rows:
                series = points.setdefault(row.id, [])
                if row.utc_day is not None:
                    series.append(
                        PortfolioDailyPoint(
                            utc_day=row.utc_day,
                            captured_at=row.captured_at.astimezone(UTC),
                            total_value=row.total_value,
                            valuation_complete=row.valuation_complete,
                        )
                    )
            await fence_owned_active_portfolios(db, owner_id, list(points))
    except SchemaAdmissionError, SQLAlchemyError, TimeoutError:
        raise HTTPException(503, detail={"code": "service_unavailable"}) from None
    return PortfolioDailyHistory(
        start_day=start_day,
        end_day=end_day,
        portfolios=[
            PortfolioDailySeries(portfolio_id=key, points=items) for key, items in points.items()
        ],
    )
