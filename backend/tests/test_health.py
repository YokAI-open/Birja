from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

from app.core.config import Settings
from app.main import create_app


@asynccontextmanager
async def _client_for(settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(settings)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c,
    ):
        yield c


async def test_health_ok(client: httpx.AsyncClient) -> None:
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "db": "ok", "redis": "ok"}
    assert resp.headers["cache-control"] == "no-store"


async def test_health_redis_down(settings: Settings) -> None:
    broken = settings.model_copy(update={"redis_url": "redis://127.0.0.1:1/0"})
    async with _client_for(broken) as c:
        resp = await c.get("/api/v1/health")
    assert resp.status_code == 503
    assert resp.json() == {"status": "degraded", "db": "ok", "redis": "error"}
    assert resp.headers["cache-control"] == "no-store"


async def test_health_db_down(settings: Settings) -> None:
    broken = settings.model_copy(
        update={"database_url": "postgresql+asyncpg://yokai_test:test@127.0.0.1:1/yokai_test"}
    )
    async with _client_for(broken) as c:
        resp = await c.get("/api/v1/health")
    assert resp.status_code == 503
    assert resp.json() == {"status": "degraded", "db": "error", "redis": "ok"}


async def test_health_degraded_body_has_no_internals(settings: Settings) -> None:
    broken = settings.model_copy(update={"redis_url": "redis://127.0.0.1:1/0"})
    async with _client_for(broken) as c:
        resp = await c.get("/api/v1/health")
    assert set(resp.json()) == {"status", "db", "redis"}
    assert "127.0.0.1" not in resp.text
