"""Real public closure linearizes private reads at their final root fence."""

import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import history
from tests.test_portfolio_closure_api import authority, closure_api, create, delete, intent
from tests.test_portfolio_closure_events import blocked

__all__ = ["authority", "closure_api"]


async def finish(*tasks):
    for task in tasks:
        if not task.done():
            task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


@pytest.mark.parametrize("listing", [False, True])
async def test_metadata_late_read_cannot_publish_closed_identity(closure_api, monkeypatch, listing):
    api = closure_api
    made = await create(api)
    root = made.json()["id"]
    reached, release = asyncio.Event(), asyncio.Event()
    original = AsyncSession.execute
    armed = True

    async def pause(db, statement, *args, **kwargs):
        nonlocal armed
        result = await original(db, statement, *args, **kwargs)
        if armed and str(statement).startswith("SELECT accounts.id, accounts.name"):
            armed = False
            reached.set()
            await release.wait()
        return result

    monkeypatch.setattr(AsyncSession, "execute", pause)
    path = "/api/v2/portfolios" if listing else f"/api/v2/portfolios/{root}/metadata"
    reader = asyncio.create_task(api.client.get(path))
    try:
        await asyncio.wait_for(reached.wait(), 5)
        closed = await delete(api, root, intent())
        assert closed.status_code == 200, closed.text
        release.set()
        response = await asyncio.wait_for(reader, 5)
        assert response.status_code == 404, response.text
        assert response.json() == {"detail": {"code": "portfolio_unavailable"}}
        assert response.headers["cache-control"] == "no-store"
    finally:
        release.set()
        await finish(reader)


@pytest.mark.parametrize("path", ["history", "event-history"])
async def test_history_final_fence_holds_closer_until_response(closure_api, monkeypatch, path):
    api = closure_api
    root = (await create(api)).json()["id"]
    reached, release = asyncio.Event(), asyncio.Event()
    original = history.validate_portfolio_read
    calls, pid = 0, None

    async def pause(db, portfolio, **kwargs):
        nonlocal calls, pid
        await original(db, portfolio, **kwargs)
        calls += 1
        if calls == 2:
            pid = await db.scalar(text("SELECT pg_backend_pid()"))
            reached.set()
            await release.wait()

    monkeypatch.setattr(history, "validate_portfolio_read", pause)
    # Mixed History imports the validator directly; patch its bound reference too.
    from app.services import event_history

    monkeypatch.setattr(event_history, "validate_portfolio_read", pause)
    reader = asyncio.create_task(api.client.get(f"/api/v2/portfolios/{root}/{path}"))
    closer = None
    try:
        await asyncio.wait_for(reached.wait(), 5)
        closer = asyncio.create_task(delete(api, root, intent()))
        assert await blocked(api, pid, "close_portfolio")
        assert not closer.done()
        release.set()
        response, closed = await asyncio.wait_for(asyncio.gather(reader, closer), 8)
        assert response.status_code == 200, response.text
        assert response.json() == {"items": [], "next_cursor": None}
        assert closed.status_code == 200, closed.text
        assert (await api.client.get(f"/api/v2/portfolios/{root}/{path}")).status_code == 404
    finally:
        release.set()
        await finish(reader, *([closer] if closer is not None else []))


@pytest.mark.parametrize("path", ["history", "event-history"])
async def test_history_close_before_final_read_refuses_hydrated_data(
    closure_api, monkeypatch, path
):
    api = closure_api
    root = (await create(api)).json()["id"]
    reached, release = asyncio.Event(), asyncio.Event()
    original = history.validate_portfolio_read
    calls = 0

    async def pause(db, portfolio, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            reached.set()
            await release.wait()
        return await original(db, portfolio, **kwargs)

    monkeypatch.setattr(history, "validate_portfolio_read", pause)
    from app.services import event_history

    monkeypatch.setattr(event_history, "validate_portfolio_read", pause)
    reader = asyncio.create_task(api.client.get(f"/api/v2/portfolios/{root}/{path}"))
    try:
        await asyncio.wait_for(reached.wait(), 5)
        assert (await delete(api, root, intent())).status_code == 200
        release.set()
        response = await asyncio.wait_for(reader, 5)
        assert response.status_code == 404
        assert response.json() == {"detail": {"code": "portfolio_unavailable"}}
        assert response.headers["cache-control"] == "no-store"
    finally:
        release.set()
        await finish(reader)


@pytest.mark.parametrize("listing", [False, True])
async def test_metadata_final_fence_holds_closer_until_response(closure_api, monkeypatch, listing):
    from app.services import portfolios

    api = closure_api
    root = (await create(api)).json()["id"]
    reached, release = asyncio.Event(), asyncio.Event()
    original = portfolios.fence_owned_active_portfolios
    pid = None

    async def pause(db, owner, identifiers):
        nonlocal pid
        await original(db, owner, identifiers)
        if identifiers:
            pid = await db.scalar(text("SELECT pg_backend_pid()"))
            reached.set()
            await release.wait()

    monkeypatch.setattr(portfolios, "fence_owned_active_portfolios", pause)
    path = "/api/v2/portfolios" if listing else f"/api/v2/portfolios/{root}/metadata"
    reader = asyncio.create_task(api.client.get(path))
    closer = None
    try:
        await asyncio.wait_for(reached.wait(), 5)
        closer = asyncio.create_task(delete(api, root, intent()))
        assert await blocked(api, pid, "close_portfolio")
        assert not closer.done()
        release.set()
        response, closed = await asyncio.wait_for(asyncio.gather(reader, closer), 8)
        assert response.status_code == closed.status_code == 200
        assert (response.json()[0] if listing else response.json())["name"] == "Strategy"
        assert (await api.client.get("/api/v2/portfolios")).json() == []
    finally:
        release.set()
        await finish(reader, *([closer] if closer is not None else []))
