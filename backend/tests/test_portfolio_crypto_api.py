"""Actual crypto routers in isolated composition; production registration is15."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import select, update

from app.api.v2.router import api_router as identity_router
from app.api.v2.trades import router as crypto_router
from app.core.config import Settings
from app.main import create_app
from app.models.price import Price
from app.models.trade import Trade
from app.models.user import Account, User
from app.schemas.trades import PortfolioFillOut
from tests.helpers import sign_in
from tests.test_portfolio_crypto import crypto_books

__all__ = ["crypto_books"]


@pytest.fixture(scope="session")
def app(settings: Settings) -> FastAPI:
    composition = create_app(settings)
    composition.include_router(identity_router, prefix="/api/v2")
    composition.include_router(crypto_router, prefix="/api/v2")
    return composition


@pytest_asyncio.fixture
async def crypto_auth(crypto_books, auth_client, outbox):
    factory, roots, cid = crypto_books
    async with factory() as db:
        email = (
            await db.execute(select(User.email).where(User.id == roots[0].user_id))
        ).scalar_one()
    await sign_in(auth_client, outbox, email)
    return auth_client, factory, roots, cid


def headers(client):
    return {"X-CSRF-Token": client.cookies["bj_csrf"]}


def quote_body():
    return {"symbol": "BTC", "side": "buy", "quantity": "1"}


def trade_body(key=None):
    return {**quote_body(), "expected_mid": "100", "idempotency_key": str(key or uuid4())}


def path(root, endpoint="trades"):
    return f"/api/v2/portfolios/{root.portfolio_id}/{endpoint}"


def private(response):
    assert response.headers["cache-control"] == "no-store"
    assert {v.strip().lower() for v in response.headers["vary"].split(",")} >= {
        "cookie",
        "authorization",
    }


async def test_scoped_quote_fill_holding_and_immutable_original_retry(crypto_auth, engine):
    client, factory, (root, sibling, *_), cid = crypto_auth
    quote = await client.post(
        path(root, "trades/quote"), json=quote_body(), headers=headers(client)
    )
    assert quote.status_code == 200
    private(quote)
    assert quote.json()["portfolio_id"] == str(root.portfolio_id)
    assert Decimal(quote.json()["cash_before"]) == Decimal("1000")
    assert Decimal(quote.json()["fee"]) == Decimal("0.25")
    body = trade_body()
    first = await client.post(path(root), json=body, headers=headers(client))
    assert first.status_code == 201
    private(first)
    payload = first.json()
    assert payload["portfolio_id"] == str(root.portfolio_id)
    for name in (
        "input_value",
        "mid",
        "exec_price",
        "quantity",
        "notional",
        "fee",
        "cash_delta",
        "cash_after",
    ):
        assert isinstance(payload[name], str)
    async with factory() as db:
        saved = (
            await db.execute(select(Trade.__table__).where(Trade.id == payload["trade_id"]))
        ).one()
    async with engine.begin() as conn:
        await conn.execute(
            update(Price)
            .where(Price.coin_id == cid)
            .values(as_of=datetime.now(UTC) - timedelta(days=1))
        )
    replay = await client.post(path(root), json=body, headers=headers(client))
    assert replay.status_code == 200 and replay.json() == payload
    private(replay)
    async with factory() as db:
        assert (
            await db.execute(select(Trade.__table__).where(Trade.id == payload["trade_id"]))
        ).one() == saved
    for target, expected in ((root, "1.1"), (sibling, "0.2")):
        holding = await client.get(path(target, "holdings/BTC"))
        assert holding.status_code == 200
        private(holding)
        assert holding.json()["portfolio_id"] == str(target.portfolio_id)
        assert Decimal(holding.json()["quantity"]) == Decimal(expected)


@pytest.mark.parametrize("endpoint", ["trades/quote", "trades", "holdings/BTC"])
@pytest.mark.parametrize("target", ["foreign", "closed", "unknown"])
async def test_unavailable_http_target_does_not_disclose_receipt(crypto_auth, endpoint, target):
    client, _, roots, _ = crypto_auth
    pid = (
        roots[3].portfolio_id
        if target == "foreign"
        else roots[2].portfolio_id
        if target == "closed"
        else 9223372036854775807
    )
    url = f"/api/v2/portfolios/{pid}/{endpoint}"
    if endpoint.startswith("holdings"):
        response = await client.get(url)
    else:
        response = await client.post(
            url,
            json=trade_body() if endpoint == "trades" else quote_body(),
            headers=headers(client),
        )
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "portfolio_unavailable"}}
    private(response)


@pytest.mark.parametrize("pid", ["no", "0", "-1", "9223372036854775808"])
async def test_malformed_target_is_private_validation_error(crypto_auth, pid):
    client, *_ = crypto_auth
    response = await client.post(
        f"/api/v2/portfolios/{pid}/trades/quote", json=quote_body(), headers=headers(client)
    )
    assert response.status_code == 422
    private(response)


async def test_scoped_csrf_auth_and_body_rejections_stay_private(crypto_auth):
    client, _, (root, *_), _ = crypto_auth
    response = await client.post(path(root), json=trade_body())
    assert response.status_code == 403 and response.json()["detail"]["code"] == "csrf_failed"
    private(response)
    response = await client.post(
        path(root), json={**trade_body(), "portfolio_id": "999"}, headers=headers(client)
    )
    assert response.status_code == 422
    private(response)
    client.cookies.clear()
    response = await client.get(path(root, "holdings/BTC"))
    assert response.status_code == 401
    private(response)


async def test_global_retry_wrong_root_returns_conflict_without_foreign_receipt(crypto_auth):
    client, _, (root, sibling, *_), _ = crypto_auth
    body = trade_body()
    assert (await client.post(path(root), json=body, headers=headers(client))).status_code == 201
    response = await client.post(path(sibling), json=body, headers=headers(client))
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "idempotency_conflict"
    assert "trade_id" not in response.text and str(root.portfolio_id) not in response.text
    private(response)


async def test_closed_original_target_cannot_replay_or_retarget(crypto_auth, engine):
    client, _, (root, sibling, *_), _ = crypto_auth
    body = trade_body()
    assert (await client.post(path(root), json=body, headers=headers(client))).status_code == 201
    async with engine.begin() as conn:
        await conn.execute(
            update(Account)
            .where(Account.id == root.portfolio_id)
            .values(closed_at=datetime.now(UTC))
        )
    refused = await client.post(path(root), json=body, headers=headers(client))
    assert refused.status_code == 404 and refused.json() == {
        "detail": {"code": "portfolio_unavailable"}
    }
    private(refused)
    assert (await client.post(path(sibling), json=body, headers=headers(client))).status_code == 409


async def test_repricing_quote_contains_original_portfolio(crypto_auth):
    client, _, (root, *_), _ = crypto_auth
    response = await client.post(
        path(root), json={**trade_body(), "expected_mid": "99"}, headers=headers(client)
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "price_changed"
    assert response.json()["detail"]["quote"]["portfolio_id"] == str(root.portfolio_id)
    private(response)


async def test_response_failure_after_commit_preserves_safe_original_retry(
    crypto_auth, monkeypatch
):
    client, _, (root, *_), _ = crypto_auth
    body = trade_body()

    def fail(_cls, _fill):
        raise RuntimeError("private internal details")

    with monkeypatch.context() as patch:
        patch.setattr(PortfolioFillOut, "from_fill", classmethod(fail))
        response = await client.post(path(root), json=body, headers=headers(client))
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "service_unavailable"
    assert "private internal details" not in response.text
    private(response)
    replay = await client.post(path(root), json=body, headers=headers(client))
    assert replay.status_code == 200
    assert Decimal(replay.json()["cash_after"]) == Decimal("899.50")


async def test_missing_portfolio_path_never_executes(crypto_auth):
    client, factory, (root, *_), _ = crypto_auth
    response = await client.post("/api/v2/trades", json=trade_body(), headers=headers(client))
    assert response.status_code == 404
    async with factory() as db:
        assert (
            await db.execute(select(Account.cash).where(Account.id == root.portfolio_id))
        ).scalar_one() == Decimal("1000")
