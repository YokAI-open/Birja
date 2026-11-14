"""Authenticated mixed-event History over actual retained PostgreSQL records."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select, text

from app.models.user import User
from app.services.event_history import EventHistoryCursor, encode_cursor
from app.services.history import HistoryCursor
from app.services.history import encode_cursor as legacy_cursor
from tests.dividend_fixtures import (
    books,
    dividend_case,
    hold,
    ownership,
    process,
    revise,
    status_case,
    stock_trade_case,
)
from tests.helpers import sign_in, unique_email
from tests.test_history_service import STAMP, put_fill

__all__ = ["dividend_case", "ownership", "status_case", "stock_trade_case"]


async def sign_in_owner(factory, ids, client, outbox):
    async with factory() as db:
        email = await db.scalar(select(User.email).where(User.id == ids["user_id"]))
    await sign_in(client, outbox, email)


async def test_mixed_history_authenticated_empty_read(auth_client, outbox):
    await sign_in(auth_client, outbox, unique_email())
    response = await auth_client.get("/api/v1/history")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {"items": [], "next_cursor": None}


async def test_mixed_history_requires_real_session(auth_client):
    response = await auth_client.get("/api/v1/history")
    assert response.status_code == 401
    assert response.json()["detail"] == {
        "code": "not_authenticated",
        "message": "Sign in to continue.",
    }
    auth_client.cookies.set("bj_access", "forged")
    assert (await auth_client.get("/api/v1/history")).status_code == 401


@pytest.mark.parametrize("limit", ["0", "101", "-1", "1.0", "1e1", "true", "01", " 1", "9" * 1000])
async def test_mixed_history_limit_fixed_error(auth_client, outbox, limit):
    await sign_in(auth_client, outbox, unique_email())
    response = await auth_client.get("/api/v1/history", params={"limit": limit})
    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["detail"] == {
        "code": "invalid_limit",
        "message": "History limit must be between 1 and 100.",
    }


@pytest.mark.parametrize("limit", ["1", "100"])
async def test_mixed_history_valid_limits(auth_client, outbox, limit):
    await sign_in(auth_client, outbox, unique_email())
    response = await auth_client.get("/api/v1/history", params={"limit": limit})
    assert response.status_code == 200
    assert response.json() == {"items": [], "next_cursor": None}


@pytest.mark.parametrize(
    "cursor",
    [
        "",
        "not-a-cursor",
        "<private-provider-data>",
        "a" * 512,
        "a" * 513,
        legacy_cursor(HistoryCursor(created_at=STAMP, id=1)),
    ],
)
async def test_mixed_history_cursor_fixed_error(auth_client, outbox, cursor):
    await sign_in(auth_client, outbox, unique_email())
    response = await auth_client.get("/api/v1/history", params={"cursor": cursor})
    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["detail"] == {
        "code": "invalid_cursor",
        "message": "Invalid history cursor.",
    }


async def test_mixed_history_default_page_size_exact_crypto_and_read_only(
    auth_client, outbox, engine
):
    email = unique_email()
    await sign_in(auth_client, outbox, email)
    async with engine.connect() as conn:
        uid = await conn.scalar(select(User.id).where(User.email == email))
    for _ in range(26):
        await put_fill(engine, uid)
    first = await auth_client.get("/api/v1/history")
    assert first.status_code == 200
    body = first.json()
    assert len(body["items"]) == 25 and body["next_cursor"] is not None
    item = body["items"][0]
    assert set(item) == {
        "kind",
        "id",
        "recorded_at",
        "asset_type",
        "symbol",
        "name",
        "cash_delta",
        "side",
        "quantity",
        "exec_price",
        "fee",
        "filled_at",
        "source",
        "feed",
        "quote_at",
    }
    assert item["kind"] == "trade" and item["asset_type"] == "crypto"
    assert item["id"].startswith("trade:")
    assert (
        item["recorded_at"]
        == item["filled_at"]
        == STAMP.isoformat(timespec="microseconds").replace("+00:00", "Z")
    )
    assert item["quantity"] == "0.00000001"
    assert item["exec_price"] == "123.45678901"
    assert item["fee"] == "0.25000000" and item["cash_delta"] == "-100.00000000"
    assert item["source"] is item["feed"] is item["quote_at"] is None
    last = (await auth_client.get("/api/v1/history", params={"cursor": body["next_cursor"]})).json()
    assert len(last["items"]) == 1 and last["next_cursor"] is None
    assert len({row["id"] for row in body["items"] + last["items"]}) == 26


@pytest.mark.parametrize("classification", ["uncertain", "cancelled"])
async def test_mixed_history_actual_paid_held_owner_lineage_and_no_mutation(
    dividend_case, auth_client, outbox, new_user, classification
):
    factory, ids = dividend_case
    await sign_in_owner(factory, ids, auth_client, outbox)
    paid = await process(factory, ids)
    saved = (await auth_client.get("/api/v1/history")).json()["items"][0]
    assert saved["id"] == saved["payment_reference"] == f"dividend:{paid.payment_id}"
    assert Decimal(saved["credited_amount"]) == Decimal(saved["cash_delta"]) == 1
    assert Decimal(saved["eligible_quantity"]) == 2 and Decimal(saved["rate"]) == Decimal(".5")
    assert saved["credited_at"] == saved["recorded_at"]
    assert datetime.fromisoformat(saved["cutoff"]).utcoffset() == UTC.utcoffset(None)
    assert saved["ex_date"] < saved["record_date"] <= saved["payable_date"]
    revised = await revise(factory, ids, classification=classification, eligible=False)
    decision = await hold(factory, paid.payment_id, revised["revision_fingerprint"])
    assert await hold(factory, paid.payment_id, revised["revision_fingerprint"]) == decision
    before = await books(factory, ids["user_id"])
    response = await auth_client.get("/api/v1/history", params={"limit": 1})
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    body = response.json()
    held = body["items"][0]
    assert held["kind"] == "dividend_correction" and held["outcome"] == "held_uncertain"
    assert held["reason"] == "terms_unverified"
    assert held["id"] == held["decision_reference"] == f"dividend_correction:{decision.decision_id}"
    assert held["original"] == saved and held["payment_reference"] == saved["id"]
    assert held["terms"] is held["desired_total"] is held["proposed_delta"] is None
    assert Decimal(held["cash_delta"]) == Decimal(held["applied_delta"]) == 0
    assert Decimal(held["cumulative_applied_before"]) == 1
    assert (
        await auth_client.get("/api/v1/history", params={"cursor": body["next_cursor"]})
    ).json()["items"] == [saved]
    assert await books(factory, ids["user_id"]) == before
    # Query-supplied owner/reference fields cannot replace the cookie identity.
    foreign = await new_user()
    own = await auth_client.get(
        "/api/v1/history", params={"user_id": foreign, "payment_id": paid.payment_id}
    )
    assert len(own.json()["items"]) == 2
    await sign_in(auth_client, outbox, unique_email())
    forged = encode_cursor(EventHistoryCursor(datetime.now(UTC), 4, 9223372036854775807))
    for params in (
        {"user_id": ids["user_id"], "decision_id": decision.decision_id},
        {"cursor": forged, "payment_id": paid.payment_id},
    ):
        foreign_read = await auth_client.get("/api/v1/history", params=params)
        assert foreign_read.status_code == 200
        assert foreign_read.json() == {"items": [], "next_cursor": None}
    assert await books(factory, ids["user_id"]) == before


async def test_mixed_history_openapi_has_no_owner_parameter(running_app):
    operation = running_app.openapi()["paths"]["/api/v1/history"]["get"]
    assert {row["name"] for row in operation["parameters"]} == {"limit", "cursor"}
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/EventHistoryPage"
    }


async def test_mixed_history_and_portfolio_share_actual_cash_without_recredit(
    dividend_case, auth_client, outbox
):
    factory, ids = dividend_case
    await sign_in_owner(factory, ids, auth_client, outbox)
    before = (await auth_client.get("/api/v1/portfolio")).json()
    original = await process(factory, ids)
    changed = await revise(factory, ids, rate="0.75")
    applied = await process(factory, changed)
    assert await process(factory, changed) == applied
    response = await auth_client.get("/api/v1/history")
    assert response.status_code == 200
    records = response.json()["items"]
    assert [item["kind"] for item in records] == ["dividend_correction", "dividend"]
    assert records[0]["outcome"] == "applied" and Decimal(records[0]["cash_delta"]) == Decimal(".5")
    assert records[0]["original"] == records[1]
    portfolio = (await auth_client.get("/api/v1/portfolio")).json()
    assert Decimal(portfolio["cash"]) == Decimal(before["cash"]) + Decimal("1.5")
    assert portfolio["starting_cash"] == before["starting_cash"] == "10000.00"
    unchanged = await books(factory, ids["user_id"])
    async with factory.begin() as db:
        previous = (
            await db.execute(
                text("SELECT symbol,name FROM coins WHERE id=:c"), {"c": ids["coin_id"]}
            )
        ).one()
        await db.execute(
            text("UPDATE coins SET symbol='RENAMED',name='Mutable label' WHERE id=:c"),
            {"c": ids["coin_id"]},
        )
    try:
        assert (await auth_client.get("/api/v1/history")).json() == response.json()
        assert await process(factory, ids) == original
        assert await books(factory, ids["user_id"]) == unchanged
    finally:
        async with factory.begin() as db:
            await db.execute(
                text("UPDATE coins SET symbol=:s,name=:n WHERE id=:c"),
                {"s": previous.symbol, "n": previous.name, "c": ids["coin_id"]},
            )


async def test_mixed_history_preanchor_uncertainty_never_fabricates_dividend(
    dividend_case, auth_client, outbox
):
    from app.services.dividends import DividendRefused

    factory, ids = dividend_case
    await sign_in_owner(factory, ids, auth_client, outbox)
    await revise(factory, ids, classification="uncertain", eligible=False)
    before = await books(factory, ids["user_id"])
    for _ in range(3):
        with pytest.raises(DividendRefused):
            await process(factory, ids)
        response = await auth_client.get("/api/v1/history")
        assert response.status_code == 200
        assert response.json() == {"items": [], "next_cursor": None}
    assert await books(factory, ids["user_id"]) == before
