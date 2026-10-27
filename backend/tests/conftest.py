import os
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

import httpx
import pytest
import pytest_asyncio
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from tests.guard import ensure_test_stack

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://yokai_test:test@127.0.0.1:55432/yokai_test"
)
TEST_REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://:test@127.0.0.1:56379/0")

# Guard runs before any app import or fixture can touch a database.
ensure_test_stack(TEST_DATABASE_URL, TEST_REDIS_URL)

os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["REDIS_URL"] = TEST_REDIS_URL
os.environ["OTP_HMAC_SECRET"] = "test-only-otp-hmac-secret-0123456789-abcdefghij"

if TYPE_CHECKING:
    from fastapi import FastAPI

    from app.core.config import Settings


@pytest.fixture(scope="session")
def settings() -> Settings:
    from app.core.config import Settings

    return Settings()


@pytest_asyncio.fixture(scope="session")
async def engine(settings: Settings) -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine(settings.database_url)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture(scope="session")
async def redis_client(settings: Settings) -> AsyncIterator[Redis]:
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    yield client
    await client.aclose()


@pytest.fixture(scope="session")
def app(settings: Settings) -> FastAPI:
    from app.main import create_app

    return create_app(settings)


@pytest_asyncio.fixture(scope="session")
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c,
    ):
        yield c
