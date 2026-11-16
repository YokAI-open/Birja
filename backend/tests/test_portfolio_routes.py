"""Actual financial read adapters; final production composition is verified below."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import select, text, update

from app.api.v2.history import router as history_router
from app.api.v2.portfolios import router as portfolios_router
from app.api.v2.trades import router as trades_router
from app.core.config import Settings
from app.main import create_app
from app.models.user import Account, User
from tests.helpers import sign_in
from tests.test_portfolio_crypto import crypto_books, fill

__all__ = ["crypto_books"]


@pytest.fixture(scope="session")
def app(settings: Settings) -> FastAPI:
    composition = create_app(settings)
    from app.api.v2.router import api_router

    composition.include_router(api_router, prefix="/api/v2")
    for router in (history_router, portfolios_router, trades_router):
        composition.include_router(router, prefix="/api/v2")
    return composition


@pytest_asyncio.fixture
async def read_auth(crypto_books, auth_client, outbox):
    factory, roots, cid = crypto_books
    async with factory() as db:
        email = await db.scalar(select(User.email).where(User.id == roots[0].user_id))
    await sign_in(auth_client, outbox, email)
    return auth_client, factory, roots, cid


def path(root, suffix=""):
    return f"/api/v2/portfolios/{root.portfolio_id}{suffix}"


def private(response):
    assert response.headers["cache-control"] == "no-store"
    assert {v.strip().lower() for v in response.headers["vary"].split(",")} >= {
        "cookie",
        "authorization",
    }


async def test_metadata_lists_only_owned_active_identity_in_stable_order(read_auth):
    client, factory, roots, _ = read_auth
    response = await client.get("/api/v2/portfolios")
    assert response.status_code == 200
    private(response)
    assert response.json() == [
        {"id": str(roots[0].portfolio_id), "name": "My portfolio"},
        {"id": str(roots[1].portfolio_id), "name": "Sibling"},
    ]
    async with factory() as db:
        before = (
            await db.execute(select(Account.__table__).where(Account.user_id == roots[0].user_id))
        ).all()
    for _ in range(2):
        assert (await client.get("/api/v2/portfolios")).json() == response.json()
    async with factory() as db:
        assert (
            await db.execute(select(Account.__table__).where(Account.user_id == roots[0].user_id))
        ).all() == before


async def test_metadata_zero_active_does_not_recreate_or_fund(read_auth):
    client, factory, roots, _ = read_auth
    async with factory.begin() as db:
        await db.execute(
            update(Account)
            .where(Account.user_id == roots[0].user_id, Account.closed_at.is_(None))
            .values(closed_at=datetime.now(UTC))
        )
    for _ in range(2):
        response = await client.get("/api/v2/portfolios")
        assert response.status_code == 200 and response.json() == []
        private(response)
    async with factory() as db:
        rows = (
            (
                await db.execute(
                    select(Account.cash)
                    .where(Account.user_id == roots[0].user_id)
                    .order_by(Account.id)
                )
            )
            .scalars()
            .all()
        )
    assert rows == [Decimal("1000"), Decimal("2000"), Decimal("55")]


async def test_valuation_preserves_root_baseline_and_exact_wire_values(read_auth):
    client, _, roots, _ = read_auth
    first = await client.get(path(roots[0]))
    sibling = await client.get(path(roots[1]))
    assert first.status_code == sibling.status_code == 200
    for response, root in ((first, roots[0]), (sibling, roots[1])):
        private(response)
        assert response.json()["portfolio_id"] == str(root.portfolio_id)
        assert isinstance(response.json()["cash"], str)
    assert Decimal(first.json()["total_value"]) == 1010
    assert Decimal(sibling.json()["starting_cash"]) == 7654
    assert Decimal(sibling.json()["total_value"]) == 2020
    assert sibling.json()["name"] == "Sibling"


@pytest.mark.parametrize("suffix", ["", "/history", "/event-history"])
@pytest.mark.parametrize("target", ["foreign", "closed", "unknown"])
async def test_valuation_history_unavailable_targets_are_private(read_auth, suffix, target):
    client, _, roots, _ = read_auth
    pid = (
        roots[3].portfolio_id
        if target == "foreign"
        else roots[2].portfolio_id
        if target == "closed"
        else 9223372036854775807
    )
    response = await client.get(f"/api/v2/portfolios/{pid}{suffix}")
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "portfolio_unavailable"}}
    private(response)


@pytest.mark.parametrize("suffix", ["/history", "/event-history"])
@pytest.mark.parametrize("query", ["limit=0", "limit=101", "limit=1.0", "cursor=bad"])
async def test_history_bad_limits_and_cursors_are_private(read_auth, suffix, query):
    client, _, roots, _ = read_auth
    response = await client.get(path(roots[0], suffix) + "?" + query)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == (
        "invalid_cursor" if query.startswith("cursor") else "invalid_limit"
    )
    private(response)


async def test_history_cursor_cannot_retarget_sibling_and_original_fills(read_auth, settings):
    client, factory, roots, _ = read_auth
    for _ in range(3):
        await fill(factory, roots[0], settings, value="0.1", key=uuid4())
    await fill(factory, roots[1], settings, value="0.1", key=uuid4())
    for suffix in ("/history", "/event-history"):
        first = await client.get(path(roots[0], suffix) + "?limit=1")
        assert first.status_code == 200
        private(first)
        cursor = first.json()["next_cursor"]
        assert cursor
        crossed = await client.get(path(roots[1], suffix), params={"cursor": cursor})
        assert crossed.status_code == 422 and crossed.json()["detail"]["code"] == "invalid_cursor"
        second = await client.get(path(roots[0], suffix), params={"cursor": cursor})
        assert second.status_code == 200
        assert second.json()["items"][0]["id"] != first.json()["items"][0]["id"]
    async with factory() as db:
        assert (
            await db.execute(
                text("SELECT count(*) FROM trades WHERE portfolio_id=:p"),
                {"p": roots[0].portfolio_id},
            )
        ).scalar_one() == 3


async def test_valuation_root_lost_after_resolution_never_publishes(read_auth, monkeypatch):
    client, factory, roots, _ = read_auth
    from app.api.v2 import portfolios

    original = portfolios.get_portfolio

    async def close_before_read(db, **kwargs):
        async with factory.begin() as conn:
            await conn.execute(
                update(Account)
                .where(Account.id == roots[0].portfolio_id)
                .values(closed_at=datetime.now(UTC))
            )
        return await original(db, **kwargs)

    monkeypatch.setattr(portfolios, "get_portfolio", close_before_read)
    response = await client.get(path(roots[0]))
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "portfolio_unavailable"}}
    private(response)


async def test_metadata_and_reads_require_authentication(read_auth):
    client, _, roots, _ = read_auth
    client.cookies.clear()
    for url in (
        "/api/v2/portfolios",
        path(roots[0]),
        path(roots[0], "/history"),
        path(roots[0], "/event-history"),
    ):
        response = await client.get(url)
        assert response.status_code == 401
        private(response)
