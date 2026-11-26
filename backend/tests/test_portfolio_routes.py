"""Actual financial read adapters; final production composition is verified below."""

from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select, text, update

from app.models.user import Account, User
from tests.helpers import sign_in
from tests.portfolio_fixtures import delete_owned_test_root, portfolio_migration_db
from tests.test_portfolio_crypto import crypto_books, fill
from tests.test_portfolio_dividends import (
    authority,
    dividend_books,
    management_api,
    pay,
    revise,
    strategy_books,
    strategy_events,
)

__all__ = [
    "authority",
    "management_api",
    "strategy_books",
    "strategy_events",
    "crypto_books",
    "portfolio_migration_db",
    "dividend_books",
]


def test_retired_history_imports_expose_only_the_refusal_adapter():
    from app.api.v1 import event_history, history, legacy_finance

    assert history.router is event_history.router is legacy_finance.router
    assert {route.endpoint for route in history.router.routes} == {
        legacy_finance.portfolio_required
    }


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
    for root in roots[:2]:
        await delete_owned_test_root(client, factory, root.portfolio_id)
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
        await delete_owned_test_root(client, factory, roots[0].portfolio_id)
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


LEGACY = (
    ("POST", "/trades/quote"),
    ("POST", "/trades"),
    ("GET", "/trades"),
    ("GET", "/holdings/BTC"),
    ("POST", "/stock-trades/quote"),
    ("POST", "/stock-trades"),
    ("GET", "/stock-trades/AAPL/context"),
    ("GET", "/portfolio"),
    ("GET", "/history"),
)


@pytest.mark.parametrize("method,endpoint", LEGACY)
@pytest.mark.parametrize("slash", [False, True])
async def test_legacy_finance_refuses_before_services_and_receipt_lookup(
    read_auth, monkeypatch, method, endpoint, slash
):
    client, factory, roots, _ = read_auth
    from app.services import event_history, history, portfolio, stock_trading, trading

    async def forbidden(*args, **kwargs):
        pytest.fail("Legacy refusal invoked a financial service")

    for module, names in (
        (trading, ("quote", "execute", "holding_quantity")),
        (stock_trading, ("quote", "execute", "context")),
        (portfolio, ("get_portfolio",)),
        (history, ("list_history",)),
        (event_history, ("list_event_history",)),
    ):
        for name in names:
            monkeypatch.setattr(module, name, forbidden)
    async with factory() as db:
        before = (await db.execute(select(Account.__table__))).all()
    kwargs = {
        "headers": {"X-CSRF-Token": client.cookies["bj_csrf"]},
        "follow_redirects": True,
    }
    if method == "POST":
        kwargs["json"] = {"portfolio_id": str(roots[1].portfolio_id), "invalid": True}
    response = await client.request(method, "/api/v1" + endpoint + ("/" if slash else ""), **kwargs)
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "portfolio_required"}}
    assert not response.headers.get_list("set-cookie")
    private(response)
    async with factory() as db:
        assert (await db.execute(select(Account.__table__))).all() == before


@pytest.mark.parametrize("method,endpoint", LEGACY)
async def test_legacy_finance_retains_auth_and_csrf(read_auth, method, endpoint):
    client, *_ = read_auth
    if method == "POST":
        response = await client.post("/api/v1" + endpoint)
        assert response.status_code == 403 and response.json()["detail"]["code"] == "csrf_failed"
        private(response)
    client.cookies.clear()
    response = await client.request(method, "/api/v1" + endpoint)
    assert response.status_code in ({401, 403} if method == "POST" else {401})
    private(response)


def test_production_route_inventory_has_no_implicit_financial_consumer(app):
    schema = app.openapi()["paths"]
    v2 = {
        (method.upper(), path)
        for path, operations in schema.items()
        if path.startswith("/api/v2")
        for method in operations
        if method in {"get", "post", "put", "patch", "delete"}
    }
    base = "/api/v2/portfolios/{portfolio_id}"
    assert v2 == {
        ("POST", "/api/v2/auth/verify-code"),
        ("GET", "/api/v2/me"),
        ("POST", "/api/v2/market-history/query"),
        ("GET", "/api/v2/portfolios"),
        ("POST", "/api/v2/portfolios"),
        ("GET", "/api/v2/portfolios/overview"),
        ("GET", "/api/v2/portfolios/value-history"),
        ("GET", base + "/metadata"),
        ("PATCH", base),
        ("DELETE", base),
        ("GET", base),
        ("GET", base + "/history"),
        ("GET", base + "/event-history"),
        ("GET", base + "/holdings/{symbol}"),
        ("POST", base + "/trades/quote"),
        ("POST", base + "/trades"),
        ("POST", base + "/stock-trades/quote"),
        ("POST", base + "/stock-trades"),
        ("GET", base + "/stock-trades/{symbol}/context"),
        ("POST", "/api/v2/stock-catalog/{catalog_id}/quote"),
        ("GET", base + "/stock-catalog/{catalog_id}/trade-context"),
        ("POST", base + "/stock-catalog/{catalog_id}/preview"),
        ("POST", base + "/stock-catalog/{catalog_id}/confirm"),
        ("POST", base + "/stock-catalog/{catalog_id}/receipt"),
    }
    # These actual registered callables can only refuse. None imports a
    # financial user_id service or can be masked by a test-only registration.
    from app.api.v1.legacy_finance import portfolio_required, router

    assert len(router.routes) == 9
    assert all(route.endpoint is portfolio_required for route in router.routes)
    assert (
        next(iter(schema["/api/v1/trades/quote"])),
        next(iter(schema["/api/v1/portfolio"])),
    ) == ("post", "get")
    for endpoint in ("/api/v1/prices", "/api/v1/stocks", "/api/v1/auth/csrf"):
        assert endpoint in schema


async def test_production_routes_require_delete_intent_and_have_no_unscoped_v2_fallback(read_auth):
    client, _, roots, _ = read_auth
    headers = {"X-CSRF-Token": client.cookies["bj_csrf"]}
    for url in ("/api/v2/trades", "/api/v2/history", "/api/v2/portfolio"):
        assert (await client.get(url)).status_code == 404
    for method, url in (
        ("POST", "/api/v2/portfolios"),
        ("PATCH", path(roots[0])),
    ):
        # Management routes now exist, but strict empty payloads cannot create
        # a strategy or edit metadata. DELETE also requires its original intent.
        assert (await client.request(method, url, headers=headers, json={})).status_code == 422
    assert (await client.delete(path(roots[0]), headers=headers)).status_code == 415


async def test_history_correction_original_is_owned_and_private_over_http(
    dividend_books, auth_client, outbox, running_app
):
    engine, factory, targets = dividend_books
    first = await pay(engine, targets[0])
    sibling = await pay(engine, targets[1])
    changed = await revise(factory, targets[0], rate=".75")
    await pay(engine, changed)
    email = f"history-owner-{uuid4().hex}@example.com"
    async with factory.begin() as db:
        await db.execute(update(User).where(User.id == targets[0]["user_id"]).values(email=email))
    # This fixture deliberately owns/recreates the disposable schema. Discard
    # driver prepared statements from prior tests, never disable ledger guards.
    await running_app.state.engine.dispose()
    try:
        await sign_in(auth_client, outbox, email)
        url = f"/api/v2/portfolios/{targets[0]['portfolio_id']}/event-history"
        response = await auth_client.get(url, params={"limit": 1})
        assert response.status_code == 200
        private(response)
        correction = response.json()["items"][0]
        assert correction["kind"] == "dividend_correction"
        assert correction["original"]["id"] == f"dividend:{first.payment_id}"
        assert correction["original"]["id"] != f"dividend:{sibling.payment_id}"
        assert correction["original"]["credited_amount"] == "1.00000000"
        crossed = await auth_client.get(
            f"/api/v2/portfolios/{targets[1]['portfolio_id']}/event-history",
            params={"cursor": response.json()["next_cursor"]},
        )
        assert crossed.status_code == 422
        foreign = await auth_client.get(
            f"/api/v2/portfolios/{targets[2]['portfolio_id']}/event-history"
        )
        assert foreign.status_code == 404 and foreign.json() == {
            "detail": {"code": "portfolio_unavailable"}
        }
    finally:
        await running_app.state.engine.dispose()
