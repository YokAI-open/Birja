import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest

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


async def test_health_redis_down(settings: Settings, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING, logger="app.services.health")
    broken = settings.model_copy(update={"redis_url": "redis://127.0.0.1:1/0"})
    async with _client_for(broken) as c:
        resp = await c.get("/api/v1/health")
    assert resp.status_code == 503
    assert resp.json() == {"status": "degraded", "db": "ok", "redis": "error"}
    assert resp.headers["cache-control"] == "no-store"
    assert any("dependency=redis" in r.getMessage() for r in caplog.records)


async def test_health_db_down(settings: Settings, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING, logger="app.services.health")
    broken = settings.model_copy(
        update={"database_url": "postgresql+asyncpg://birja_test:test@127.0.0.1:1/birja_test"}
    )
    async with _client_for(broken) as c:
        resp = await c.get("/api/v1/health")
    assert resp.status_code == 503
    assert resp.json() == {"status": "degraded", "db": "error", "redis": "ok"}
    assert any("dependency=db" in r.getMessage() for r in caplog.records)


async def test_health_degraded_body_has_no_internals(settings: Settings) -> None:
    broken = settings.model_copy(update={"redis_url": "redis://127.0.0.1:1/0"})
    async with _client_for(broken) as c:
        resp = await c.get("/api/v1/health")
    assert set(resp.json()) == {"status", "db", "redis"}
    assert "127.0.0.1" not in resp.text


def test_create_app_twice_keeps_one_log_handler(settings: Settings) -> None:
    create_app(settings)
    create_app(settings)
    assert len(logging.getLogger("app").handlers) == 1
