import re

from sqlalchemy import select

from app.models.user import User
from tests.helpers import (
    cash_of,
    holding_of,
    put_holding,
    set_cash,
    sign_in,
    trade_count,
    unique_email,
)


async def test_portfolio_requires_session(auth_client):
    assert (await auth_client.get("/api/v1/portfolio")).status_code == 401


async def test_portfolio_is_private_plain_and_read_only(auth_client, outbox, engine, clean_prices):
    email = unique_email()
    await sign_in(auth_client, outbox, email)
    async with engine.connect() as conn:
        uid = (await conn.execute(select(User.id).where(User.email == email))).scalar_one()
    await set_cash(engine, uid, "9999")
    await put_holding(engine, uid, "BTC", "1", "2")
    before = (
        await cash_of(engine, uid),
        await holding_of(engine, uid, "BTC"),
        await trade_count(engine, uid),
    )
    response = await auth_client.get("/api/v1/portfolio")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert set(body) == {
        "cash",
        "starting_cash",
        "total_value",
        "total_pl",
        "total_pl_percent",
        "cash_allocation_percent",
        "valuation_complete",
        "valued_at",
        "prices_as_of",
        "fresh_seconds",
        "stale_seconds",
        "holdings",
    }
    assert body["cash"] == "9999.00"
    assert body["starting_cash"] == "10000.00"
    assert body["total_value"] is None
    h = body["holdings"][0]
    assert h["status"] == "unpriced"
    assert set(h) == {
        "symbol",
        "name",
        "is_active",
        "quantity",
        "cost_basis",
        "average_cost",
        "mid",
        "current_value",
        "unrealized_pl",
        "unrealized_pl_percent",
        "allocation_percent",
        "as_of",
        "age_seconds",
        "status",
    }
    for key in ("quantity", "cost_basis", "average_cost"):
        assert isinstance(h[key], str) and re.fullmatch(r"\d+(\.\d+)?", h[key])
    assert before == (
        await cash_of(engine, uid),
        await holding_of(engine, uid, "BTC"),
        await trade_count(engine, uid),
    )
    # A different real synthetic session must never inherit A's financial rows.
    auth_client.cookies.clear()
    await sign_in(auth_client, outbox, unique_email())
    other = (await auth_client.get("/api/v1/portfolio")).json()
    assert other["holdings"] == []
    assert other["cash"] == other["total_value"] == "10000.00"
