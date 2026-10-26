import sys
from decimal import Decimal

from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


class _Money(BaseModel):
    v: Decimal


def test_python_314() -> None:
    assert sys.version_info[:2] == (3, 14)


def test_app_imports_and_has_health_route() -> None:
    from app.main import create_app

    paths = {getattr(r, "path", None) for r in create_app().routes}
    assert "/api/v1/health" in paths


async def test_asyncpg_returns_decimal(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        value = (await conn.execute(text("SELECT 0.00015::numeric(20,8)"))).scalar_one()
    assert isinstance(value, Decimal)
    assert value == Decimal("0.00015000")
    assert str(value) == "0.00015000"


def test_pydantic_decimal_roundtrip_as_string() -> None:
    m = _Money(v=Decimal("0.00015000"))
    dumped = m.model_dump_json()
    assert dumped == '{"v":"0.00015000"}'
    assert _Money.model_validate_json(dumped).v == Decimal("0.00015000")


async def test_redis_ping(redis_client: Redis) -> None:
    assert await redis_client.ping() is True
