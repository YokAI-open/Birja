"""Actual scoped stock routers, real sessions/DB; production composition is Plan15."""

from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import select, update

from app.api.v2.router import api_router as identity_router
from app.api.v2.stock_trades import router as stock_router
from app.core.config import Settings
from app.main import create_app
from app.models.stock import StockDataAdmission, StockQuote
from app.models.trade import Trade
from app.models.user import User
from app.services import stock_trading
from tests.helpers import sign_in
from tests.test_portfolio_stock_trading import (
    ownership,
    snapshot,
    status_case,
    stock_books,
    stock_trade_case,
)

__all__ = ["ownership", "status_case", "stock_books", "stock_trade_case"]


@pytest.fixture(scope="session")
def app(settings: Settings) -> FastAPI:
    composition = create_app(settings)
    # Actual router objects and final prefixes; production registration belongs15.
    composition.include_router(identity_router, prefix="/api/v2")
    composition.include_router(stock_router, prefix="/api/v2")
    return composition


@pytest_asyncio.fixture
async def stock_auth(stock_books, auth_client, outbox):
    factory, cid, roots, now = stock_books
    async with factory() as db:
        email = await db.scalar(select(User.email).where(User.id == roots[0].user_id))
    await sign_in(auth_client, outbox, email)
    return auth_client, factory, cid, roots, now


def path(root, endpoint="stock-trades"):
    return f"/api/v2/portfolios/{root.portfolio_id}/{endpoint}"


def headers(client):
    return {"X-CSRF-Token": client.cookies["bj_csrf"]}


def body(**changes):
    return {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": "2",
        "expected_exec_price": "102",
        "idempotency_key": str(uuid4()),
        **changes,
    }


def private(response):
    assert response.headers["cache-control"] == "no-store"
    assert {x.strip().lower() for x in response.headers["vary"].split(",")} >= {
        "cookie",
        "authorization",
    }


async def test_scoped_quote_receipt_context_and_original_replay(stock_auth):
    client, factory, cid, (root, sibling, *_), now = stock_auth
    sibling_before = await snapshot(factory, sibling)
    quote = await client.post(
        path(root, "stock-trades/quote"),
        json={"symbol": "AAPL", "side": "buy", "quantity": "2"},
        headers=headers(client),
    )
    assert quote.status_code == 200
    private(quote)
    assert quote.json()["portfolio_id"] == str(root.portfolio_id)
    assert (
        Decimal(quote.json()["cash_before"]) == 1000 and Decimal(quote.json()["exec_price"]) == 102
    )
    order = body()
    first = await client.post(path(root), json=order, headers=headers(client))
    assert first.status_code == 201
    private(first)
    original = first.json()
    assert original["portfolio_id"] == str(root.portfolio_id) and Decimal(original["fee"]) == 0
    for key in (
        "quantity",
        "exec_price",
        "cash_after",
        "cash_delta",
        "exact_mid",
        "bid",
        "ask",
        "notional",
    ):
        assert isinstance(original[key], str)
    async with factory.begin() as db:
        saved = (
            await db.execute(select(Trade.__table__).where(Trade.id == int(original["trade_id"])))
        ).one()
        await db.execute(update(StockDataAdmission).values(state="denied"))
    again = await client.post(
        path(root), json={**order, "expected_exec_price": "999"}, headers=headers(client)
    )
    assert again.status_code == 200 and again.json() == original
    private(again)
    async with factory() as db:
        assert (
            await db.execute(select(Trade.__table__).where(Trade.id == int(original["trade_id"])))
        ).one() == saved
    assert await snapshot(factory, sibling) == sibling_before


async def test_context_never_uses_sibling_cash_or_holdings(stock_auth):
    client, _, _, (root, sibling, *_), _ = stock_auth
    for target, expected in ((root, 1000), (sibling, 2000)):
        response = await client.get(path(target, "stock-trades/AAPL/context"))
        assert response.status_code == 200
        private(response)
        assert response.json()["portfolio_id"] == str(target.portfolio_id)
        assert Decimal(response.json()["cash"]) == expected
        assert Decimal(response.json()["held_quantity"]) == 0


@pytest.mark.parametrize("target", ["foreign", "closed", "unknown"])
@pytest.mark.parametrize(
    "endpoint", ["stock-trades", "stock-trades/quote", "stock-trades/AAPL/context"]
)
async def test_unavailable_target_private_and_identical(stock_auth, target, endpoint):
    client, _, _, roots, _ = stock_auth
    pid = (
        roots[3].portfolio_id
        if target == "foreign"
        else roots[2].portfolio_id
        if target == "closed"
        else 9223372036854775807
    )
    url = f"/api/v2/portfolios/{pid}/{endpoint}"
    response = (
        await client.get(url)
        if endpoint.endswith("context")
        else await client.post(
            url,
            json=body()
            if endpoint == "stock-trades"
            else {"symbol": "AAPL", "side": "buy", "quantity": "2"},
            headers=headers(client),
        )
    )
    assert response.status_code == 404 and response.json() == {
        "detail": {"code": "portfolio_unavailable"}
    }
    private(response)


@pytest.mark.parametrize("pid", ["abc", "0", "-1", "9223372036854775808"])
async def test_malformed_path_has_no_private_financial_fallback(stock_auth, pid):
    client, *_ = stock_auth
    response = await client.get(f"/api/v2/portfolios/{pid}/stock-trades/AAPL/context")
    assert response.status_code == 422
    private(response)


async def test_root_and_payload_key_conflicts_cannot_disclose_receipt(stock_auth):
    client, _, _, (root, sibling, closed, *_), _ = stock_auth
    order = body()
    assert (await client.post(path(root), json=order, headers=headers(client))).status_code == 201
    for target, changes in ((sibling, {}), (root, {"quantity": "3"})):
        response = await client.post(
            path(target), json={**order, **changes}, headers=headers(client)
        )
        assert (
            response.status_code == 409
            and response.json()["detail"]["code"] == "idempotency_conflict"
        )
        private(response)
    unavailable = await client.post(path(closed), json=order, headers=headers(client))
    assert unavailable.status_code == 404
    assert unavailable.json() == {"detail": {"code": "portfolio_unavailable"}}
    private(unavailable)


async def test_body_target_override_is_rejected(stock_auth):
    client, factory, _, (root, sibling, *_), _ = stock_auth
    before = await snapshot(factory, root)
    response = await client.post(
        path(root), json=body(portfolio_id=str(sibling.portfolio_id)), headers=headers(client)
    )
    assert response.status_code == 422
    private(response)
    assert await snapshot(factory, root) == before


async def test_csrf_and_session_required(stock_auth):
    client, _, _, (root, *_), _ = stock_auth
    denied = await client.post(path(root), json=body())
    assert denied.status_code == 403
    private(denied)
    client.cookies.clear()
    denied = await client.get(path(root, "stock-trades/AAPL/context"))
    assert denied.status_code == 401
    private(denied)


async def test_repricing_then_stale_quote_never_fills_automatically(stock_auth):
    client, factory, cid, (root, *_), now = stock_auth
    before = await snapshot(factory, root)
    response = await client.post(
        path(root), json=body(expected_exec_price="101"), headers=headers(client)
    )
    assert response.status_code == 409 and response.json()["detail"]["code"] == "price_changed"
    assert response.json()["detail"]["quote"]["portfolio_id"] == str(root.portfolio_id)
    private(response)
    assert await snapshot(factory, root) == before
    async with factory.begin() as db:
        await db.execute(
            update(StockQuote)
            .where(StockQuote.coin_id == cid)
            .values(event_at=now - timedelta(minutes=3), collected_at=now - timedelta(minutes=3))
        )
    response = await client.post(path(root), json=body(), headers=headers(client))
    assert response.status_code == 409 and response.json()["detail"]["code"] == "quote_stale"
    assert await snapshot(factory, root) == before


async def test_response_loss_after_commit_keeps_original_target_retry(stock_auth, monkeypatch):
    client, factory, _, (root, sibling, *_), _ = stock_auth
    original = stock_trading.execute

    async def lost(*args, **kwargs):
        await original(*args, **kwargs)
        raise RuntimeError("synthetic response loss")

    order = body()
    with monkeypatch.context() as patch:
        patch.setattr(stock_trading, "execute", lost)
        response = await client.post(path(root), json=order, headers=headers(client))
    assert (
        response.status_code == 500 and response.json()["detail"]["code"] == "service_unavailable"
    )
    private(response)
    response = await client.post(path(root), json=order, headers=headers(client))
    assert response.status_code == 200 and response.json()["portfolio_id"] == str(root.portfolio_id)
    assert len((await snapshot(factory, root))[2]) == 1
    response = await client.post(path(sibling), json=order, headers=headers(client))
    assert response.status_code == 409
