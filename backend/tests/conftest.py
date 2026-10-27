import os
from collections.abc import AsyncIterator, Iterator
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
    from tests.helpers import OutboxSender


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
async def running_app(app: FastAPI) -> AsyncIterator[FastAPI]:
    async with app.router.lifespan_context(app):
        yield app


@pytest_asyncio.fixture(scope="session")
async def client(running_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=running_app), base_url="http://test"
    ) as c:
        yield c


@pytest_asyncio.fixture
async def auth_client(running_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    # https so the Secure CSRF cookie is kept; fresh cookie jar per test.
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=running_app), base_url="https://test"
    ) as c:
        yield c


@pytest.fixture
def outbox(running_app: FastAPI) -> Iterator[OutboxSender]:
    from tests.helpers import OutboxSender

    original = running_app.state.email_sender
    sender = OutboxSender()
    running_app.state.email_sender = sender
    yield sender
    running_app.state.email_sender = original


@pytest_asyncio.fixture(autouse=True)
async def clean_auth_redis(redis_client: Redis) -> None:
    for pattern in ("sim:otp:*", "sim:rl:*"):
        async for key in redis_client.scan_iter(match=pattern):
            await redis_client.delete(key)
