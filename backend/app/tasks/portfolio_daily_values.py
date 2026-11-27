"""A bounded, database-only daily valuation cycle in the price scheduler."""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import SchedulerSettings
from app.db.schema_contract import require_schema
from app.models.portfolio_daily_value import PortfolioDailyValue
from app.models.user import Account
from app.services.portfolio_daily_values import (
    capture_portfolio_daily_value,
    capture_window_day,
    utc_now,
)
from app.tasks.scheduler import CycleResult

logger = logging.getLogger(__name__)
CHECK_INTERVAL_SECONDS = 60
SCHEMA_TIMEOUT_SECONDS = 3
TICK_TIMEOUT_SECONDS = 20
ROOT_TIMEOUT_SECONDS = 2
BATCH_SIZE = 8


@dataclass
class DailyValueCursor:
    day: date | None = None
    after_id: int = 0


async def daily_capture_schema_available(engine: AsyncEngine) -> bool:
    try:
        async with asyncio.timeout(SCHEMA_TIMEOUT_SECONDS), engine.connect() as conn:
            await require_schema(conn, consumer="portfolio_daily")
    except Exception as exc:
        logger.warning("daily portfolio schema unavailable: %s", type(exc).__name__)
        return False
    return True


async def run_portfolio_daily_capture(
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
    settings: SchedulerSettings,
    cursor: DailyValueCursor,
    clock: Callable[[], datetime] = utc_now,
) -> CycleResult:
    accepted = rejected = 0
    try:
        async with asyncio.timeout(TICK_TIMEOUT_SECONDS):
            day = capture_window_day(clock())
            if cursor.day != day:
                cursor.day, cursor.after_id = day, 0
            if day is None:
                return CycleResult("ok")
            async with sessionmaker() as db:
                roots = (
                    await db.execute(
                        select(Account.id, Account.user_id)
                        .where(
                            Account.id > cursor.after_id,
                            Account.closed_at.is_(None),
                            ~select(PortfolioDailyValue.portfolio_id)
                            .where(
                                PortfolioDailyValue.portfolio_id == Account.id,
                                PortfolioDailyValue.utc_day == day,
                            )
                            .exists(),
                        )
                        .order_by(Account.id)
                        .limit(BATCH_SIZE)
                    )
                ).all()
            if not roots:
                cursor.after_id = 0
            for root, owner in roots:
                if capture_window_day(clock()) != day:
                    break
                cursor.after_id = root
                try:
                    async with asyncio.timeout(ROOT_TIMEOUT_SECONDS), sessionmaker.begin() as db:
                        appended = await capture_portfolio_daily_value(
                            db,
                            owner_id=owner,
                            portfolio_id=root,
                            expected_day=day,
                            settings=settings,
                            clock=clock,
                        )
                    accepted += int(appended)
                except Exception as exc:
                    rejected += 1
                    logger.warning("daily portfolio capture rolled back: %s", type(exc).__name__)
    except Exception as exc:
        logger.warning("daily portfolio capture cycle failed: %s", type(exc).__name__)
        return CycleResult("source_error", accepted=accepted, rejected=rejected)
    return CycleResult("ok", accepted=accepted, rejected=rejected)
