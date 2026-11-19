"""Real public closure linearizes private reads at their final root fence."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import history
from tests.test_portfolio_closure_api import authority, closure_api, create, delete, intent
from tests.test_portfolio_closure_events import blocked
from tests.test_portfolio_strategy_events import management_api, strategy_books, strategy_events
from tests.test_portfolio_strategy_lifecycle import ledger, trade

__all__ = ["authority", "closure_api", "management_api", "strategy_books", "strategy_events"]


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


@pytest.mark.parametrize(
    "stock,operation",
    [
        (stock, operation)
        for stock in (False, True)
        for operation in ("quote", "context", "fill", "retry", "reprice")
    ],
)
async def test_late_financial_read_or_original_receipt_cannot_publish_closed_root(
    strategy_books, monkeypatch, stock, operation
):
    from app.services import stock_trading, trading
    from app.services.trade_math import TradeRefused

    api, roots, _, _ = strategy_books
    root, key = roots[0], uuid4()
    if operation in {"context", "retry"}:
        response = await trade(api, root, stock=stock, key=key)
        assert response.status_code == 201, response.text
    module = stock_trading if stock else trading
    method = "quote" if operation == "quote" else "context" if stock else "holding_quantity"
    if operation in {"fill", "retry", "reprice"}:
        method = "execute"
    original = getattr(module, method)
    reached, release = asyncio.Event(), asyncio.Event()

    async def pause(*args, **kwargs):
        try:
            result = await original(*args, **kwargs)
        except TradeRefused:
            reached.set()
            await release.wait()
            raise
        reached.set()
        await release.wait()
        return result

    monkeypatch.setattr(module, method, pause)
    base = f"/api/v2/portfolios/{root}"
    if operation == "context":
        path = base + ("/stock-trades/AAPL/context" if stock else "/holdings/BTC")
        request = api.client.get(path)
    else:
        body = {"symbol": "AAPL" if stock else "BTC", "side": "buy", "quantity": "1"}
        path = base + ("/stock-trades" if stock else "/trades")
        if operation == "quote":
            path += "/quote"
        else:
            body["idempotency_key"] = str(key)
            body["expected_exec_price" if stock else "expected_mid"] = (
                ("101" if stock else "99")
                if operation == "reprice"
                else ("102" if stock else "100")
            )
        request = api.client.post(path, json=body, headers={"X-CSRF-Token": "test-csrf"})
    reader = asyncio.create_task(request)
    try:
        await asyncio.wait_for(reached.wait(), 5)
        closed = await delete(api, root, intent("Patient"))
        assert closed.status_code == 200, closed.text
        before = await ledger(api, root)
        release.set()
        response = await asyncio.wait_for(reader, 5)
        assert response.status_code == 404, response.text
        assert response.json() == {"detail": {"code": "portfolio_unavailable"}}
        assert response.headers["cache-control"] == "no-store"
        assert await ledger(api, root) == before
        # A fill can commit before the read fence loses to closure. Never claim
        # the committed fill was rolled back just because its receipt is private.
        if operation in {"fill", "retry"}:
            async with api.migrator.connect() as db:
                count = await db.scalar(
                    text("SELECT count(*) FROM trades WHERE portfolio_id=:p"), {"p": int(root)}
                )
                assert count == 1
    finally:
        release.set()
        await finish(reader)
