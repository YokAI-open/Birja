"""Real public closure linearizes private reads at their final root fence."""

import asyncio
from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import history
from tests.test_portfolio_closure_api import authority, closure_api, create, delete, intent
from tests.test_portfolio_closure_events import blocked, pay, revise_event, target
from tests.test_portfolio_strategy_events import management_api, strategy_books, strategy_events
from tests.test_portfolio_strategy_lifecycle import ledger, trade

__all__ = ["authority", "closure_api", "management_api", "strategy_books", "strategy_events"]


@pytest.mark.parametrize("overview", [False, True])
@pytest.mark.parametrize("read_first", [False, True])
async def test_valuation_final_membership_with_public_closure(
    strategy_books, monkeypatch, overview, read_first
):
    api, roots, _, _ = strategy_books
    root = roots[0]
    original = AsyncSession.execute
    reached, release = asyncio.Event(), asyncio.Event()
    armed, pid = True, None

    async def pause(db, statement, *args, **kwargs):
        nonlocal armed, pid
        selected = armed and " AS active_ids" in str(statement)
        if selected:
            armed = False
            if not read_first:
                reached.set()
                await release.wait()
        result = await original(db, statement, *args, **kwargs)
        if selected and read_first:
            pid = await db.scalar(text("SELECT pg_backend_pid()"))
            reached.set()
            await release.wait()
        return result

    monkeypatch.setattr(AsyncSession, "execute", pause)
    path = "/api/v2/portfolios/overview" if overview else f"/api/v2/portfolios/{root}"
    reader = asyncio.create_task(api.client.get(path))
    closer = None
    try:
        await asyncio.wait_for(reached.wait(), 5)
        if read_first:
            closer = asyncio.create_task(delete(api, root, intent("Patient")))
            assert await blocked(api, pid, "close_portfolio")
            assert not closer.done()
            release.set()
            response, closed = await asyncio.wait_for(asyncio.gather(reader, closer), 8)
            assert response.status_code == 200, response.text
            assert closed.status_code == 200, closed.text
        else:
            assert (await delete(api, root, intent("Patient"))).status_code == 200
            release.set()
            response = await asyncio.wait_for(reader, 5)
            assert response.status_code == 404, response.text
            assert response.json() == {"detail": {"code": "portfolio_unavailable"}}
        assert response.headers["cache-control"] == "no-store"
    finally:
        release.set()
        await finish(reader, *([closer] if closer is not None else []))


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


async def test_cursor_original_retry_and_closed_foreign_missing_matrix(strategy_events):
    from app.services import event_history

    api, roots, _, _, action, admission, event_id, engine = strategy_events
    root, sibling = roots
    crypto_key, stock_key = uuid4(), uuid4()
    for stock, key in ((False, crypto_key), (True, stock_key)):
        made = await trade(api, root, stock=stock, key=key)
        assert made.status_code == 201, made.text
    work = await target(api, root, event_id)
    await pay(engine, work)
    await revise_event(engine, action, admission, event_id, Decimal(".75"))
    await pay(engine, await target(api, root, event_id))
    histories = {}
    for name in ("history", "event-history"):
        response = await api.client.get(f"/api/v2/portfolios/{root}/{name}?limit=1")
        assert response.status_code == 200, response.text
        histories[name] = response.json()
        assert histories[name]["next_cursor"]
    full = (await api.client.get(f"/api/v2/portfolios/{root}/event-history")).json()
    correction = next(item for item in full["items"] if item["kind"] == "dividend_correction")
    original_reference = correction["payment_reference"]
    assert correction["original"]["id"] == original_reference
    assert (await delete(api, root, intent("Patient"))).status_code == 200
    frozen = await ledger(api, root)
    foreign = (await create(api, "Foreign", client=api.other)).json()["id"]
    for selected in (root, foreign, "9223372036854775807"):
        prefix = f"/api/v2/portfolios/{selected}"
        for suffix in (
            "",
            "/metadata",
            "/history",
            "/event-history",
            "/holdings/BTC",
            "/stock-trades/AAPL/context",
        ):
            response = await api.client.get(prefix + suffix)
            assert response.status_code == 404, (suffix, response.text)
            assert response.json() == {"detail": {"code": "portfolio_unavailable"}}
            assert response.headers["cache-control"] == "no-store"
        for stock, key in ((False, crypto_key), (True, stock_key)):
            body = {"symbol": "AAPL" if stock else "BTC", "side": "buy", "quantity": "1"}
            trade_path = prefix + ("/stock-trades" if stock else "/trades")
            response = await api.client.post(
                trade_path + "/quote", json=body, headers={"X-CSRF-Token": "test-csrf"}
            )
            assert response.status_code == 404, response.text
            body.update(
                {
                    "idempotency_key": str(key),
                    "expected_exec_price" if stock else "expected_mid": "102" if stock else "100",
                }
            )
            response = await api.client.post(
                trade_path, json=body, headers={"X-CSRF-Token": "test-csrf"}
            )
            assert response.status_code == 404, response.text
            assert response.json() == {"detail": {"code": "portfolio_unavailable"}}
        for name, page in histories.items():
            response = await api.client.get(
                prefix + "/" + name, params={"cursor": page["next_cursor"]}
            )
            assert response.status_code == 404, response.text
    # The original owner cannot turn an old cursor or financial key into the
    # sibling's authority, even though the sibling is independently active.
    for name, page in histories.items():
        response = await api.client.get(
            f"/api/v2/portfolios/{sibling}/{name}", params={"cursor": page["next_cursor"]}
        )
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "invalid_cursor"
    boundary = event_history.decode_cursor(
        histories["event-history"]["next_cursor"], expected_portfolio_id=int(root)
    )
    forged = event_history.encode_cursor(replace(boundary, portfolio_id=int(sibling)))
    response = await api.client.get(
        f"/api/v2/portfolios/{sibling}/event-history", params={"cursor": forged}
    )
    assert response.status_code == 200 and response.json() == {"items": [], "next_cursor": None}
    replacement = (await create(api, "Patient")).json()["id"]
    before = await ledger(api, replacement)
    for stock, key in ((False, crypto_key), (True, stock_key)):
        response = await trade(api, replacement, stock=stock, key=key)
        assert response.status_code == 409, response.text
        assert response.json()["detail"]["code"] == "idempotency_conflict"
        assert "quote" not in response.json()["detail"]
    assert await ledger(api, replacement) == before
    assert await ledger(api, root) == frozen
    assert (await api.other.get(f"/api/v2/portfolios/{root}/event-history")).status_code == 404
    assert root not in [item["id"] for item in (await api.client.get("/api/v2/portfolios")).json()]
    assert root not in [
        item["id"] for item in (await api.client.get("/api/v2/portfolios/overview")).json()
    ]


async def test_retired_finance_never_reads_original_or_selects_replacement(closure_api):
    api = closure_api
    root = (await create(api)).json()["id"]
    assert (await delete(api, root, intent())).status_code == 200
    replacement = (await create(api)).json()["id"]
    before = await ledger(api, replacement)
    for suffix in (
        "/trades",
        "/holdings/BTC",
        "/stock-trades/AAPL/context",
        "/portfolio",
        "/history",
    ):
        response = await api.client.get("/api/v1" + suffix)
        assert response.status_code == 409
        assert response.json() == {"detail": {"code": "portfolio_required"}}
        assert response.headers["cache-control"] == "no-store"
    for suffix in ("/trades", "/trades/quote", "/stock-trades", "/stock-trades/quote"):
        response = await api.client.post(
            "/api/v1" + suffix,
            json={"idempotency_key": str(uuid4())},
            headers={"X-CSRF-Token": "test-csrf"},
        )
        assert response.status_code == 409
        assert response.json() == {"detail": {"code": "portfolio_required"}}
    assert await ledger(api, replacement) == before


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


@pytest.mark.parametrize("stock", [False, True])
async def test_financial_final_fence_keeps_public_closer_waiting(
    strategy_books, monkeypatch, stock
):
    from app.api.v2 import stock_trades, trades

    api, roots, _, _ = strategy_books
    root = roots[0]
    module = stock_trades if stock else trades
    original = module.fence_owned_active_portfolios
    reached, release = asyncio.Event(), asyncio.Event()
    pid = None

    async def pause(db, owner, identifiers):
        nonlocal pid
        await original(db, owner, identifiers)
        pid = await db.scalar(text("SELECT pg_backend_pid()"))
        reached.set()
        await release.wait()

    monkeypatch.setattr(module, "fence_owned_active_portfolios", pause)
    reader = asyncio.create_task(trade(api, root, stock=stock, key=uuid4()))
    closer = None
    try:
        await asyncio.wait_for(reached.wait(), 5)
        closer = asyncio.create_task(delete(api, root, intent("Patient")))
        assert await blocked(api, pid, "close_portfolio")
        assert not closer.done()
        release.set()
        response, closed = await asyncio.wait_for(asyncio.gather(reader, closer), 8)
        assert response.status_code == 201, response.text
        assert closed.status_code == 200, closed.text
        assert (await api.client.get(f"/api/v2/portfolios/{root}/history")).status_code == 404
    finally:
        release.set()
        await finish(reader, *([closer] if closer is not None else []))
