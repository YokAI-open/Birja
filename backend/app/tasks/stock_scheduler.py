"""Independent stock collection boundary, disabled until authoritative admission."""

from collections.abc import Callable
from datetime import UTC, datetime

import httpx
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import SchedulerSettings
from app.tasks.scheduler import CycleResult

LOCK_KEY = "sim:lock:stock-refresh"


async def run_stock_cycle(
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    http: httpx.AsyncClient,
    settings: SchedulerSettings,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> CycleResult:
    return CycleResult("ok")
