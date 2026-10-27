import asyncio
import logging
from typing import Literal

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.health import HealthOut

logger = logging.getLogger(__name__)

CHECK_TIMEOUT_SECONDS = 3

CheckResult = Literal["ok", "error"]


async def _check_db(db: AsyncSession) -> CheckResult:
    try:
        async with asyncio.timeout(CHECK_TIMEOUT_SECONDS):
            await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("health check failed: dependency=%s error_type=%s", "db", type(exc).__name__)
        return "error"
    return "ok"


async def _check_redis(redis: Redis) -> CheckResult:
    try:
        async with asyncio.timeout(CHECK_TIMEOUT_SECONDS):
            await redis.ping()
    except Exception as exc:
        logger.warning(
            "health check failed: dependency=%s error_type=%s", "redis", type(exc).__name__
        )
        return "error"
    return "ok"


async def check_health(db: AsyncSession, redis: Redis) -> HealthOut:
    db_state, redis_state = await asyncio.gather(_check_db(db), _check_redis(redis))
    overall: Literal["ok", "degraded"] = (
        "ok" if db_state == "ok" and redis_state == "ok" else "degraded"
    )
    return HealthOut(status=overall, db=db_state, redis=redis_state)
