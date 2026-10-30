import pytest
from sqlalchemy import select

from app.models.user import User
from app.services.history import HistoryCursor, encode_cursor
from tests.helpers import cash_of, sign_in, trade_count, unique_email
from tests.test_history_service import INVALID, STAMP, put_fill


async def test_history_requires_session(auth_client):
    assert (await auth_client.get("/api/v1/trades")).status_code == 401


async def test_history_private_stored_read_only(auth_client, outbox, engine, new_user):
    email = unique_email()
    await sign_in(auth_client, outbox, email)
    async with engine.connect() as conn:
        uid = (await conn.execute(select(User.id).where(User.email == email))).scalar_one()
    await put_fill(engine, uid)
    foreign = await put_fill(engine, await new_user(), side="sell", total="200")
    before = await cash_of(engine, uid), await trade_count(engine, uid)
    response = await auth_client.get("/api/v1/trades")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert set(body) == {"items", "next_cursor"}
    assert body["next_cursor"] is None
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert set(item) == {
        "id",
        "created_at",
        "symbol",
        "name",
        "side",
        "quantity",
        "exec_price",
        "fee",
        "total",
    }
    assert isinstance(item["id"], str)
    assert item["created_at"] == STAMP.isoformat(timespec="microseconds").replace("+00:00", "Z")
    assert item["total"] == "-100.00000000"
    assert item["fee"] == "0.25000000"
    assert item["quantity"] == "0.00000001"
    assert item["exec_price"] == "123.45678901"
    assert before == (await cash_of(engine, uid), await trade_count(engine, uid))
    # Cursor is an editable boundary, never an authorization claim. Both the
    # foreign boundary and a guessed upper boundary remain session-scoped.
    for boundary in (foreign, 9223372036854775807):
        seek = await auth_client.get(
            "/api/v1/trades",
            params={"cursor": encode_cursor(HistoryCursor(created_at=STAMP, id=boundary))},
        )
        assert seek.status_code == 200
        assert seek.json()["items"] == [item]
    older = encode_cursor(HistoryCursor(created_at=STAMP, id=int(item["id"])))
    assert (await auth_client.get("/api/v1/trades", params={"cursor": older})).json() == {
        "items": [],
        "next_cursor": None,
    }
    for cursor in INVALID:
        bad = await auth_client.get("/api/v1/trades", params={"cursor": cursor})
        assert bad.status_code == 422, cursor
        assert bad.json()["detail"] == {
            "code": "invalid_cursor",
            "message": "Invalid history cursor.",
        }


@pytest.mark.parametrize("limit", ["0", "101", "1.5", "true", "1e1"])
async def test_history_bounds(auth_client, outbox, limit):
    await sign_in(auth_client, outbox, unique_email())
    assert (await auth_client.get("/api/v1/trades", params={"limit": limit})).status_code == 422


@pytest.mark.parametrize("limit", [1, 100])
async def test_history_valid_bounds(auth_client, outbox, limit):
    await sign_in(auth_client, outbox, unique_email())
    assert (await auth_client.get("/api/v1/trades", params={"limit": limit})).json() == {
        "items": [],
        "next_cursor": None,
    }
