import base64
import json
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import event, select, text, update

from app.models.price import Coin
from app.models.trade import Trade
from app.services.history import HistoryCursor, InvalidCursor, decode_cursor, encode_cursor, list_history
from tests.helpers import coin_id

STAMP = datetime(2026, 10, 30, 8, 1, 2, 123456, tzinfo=UTC)


def token(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


VALID = {"v": 1, "created_at": "2026-10-30T08:01:02.123456Z", "id": "9223372036854775807"}
INVALID = [
    "x" * 513, "", "!", "e30=", "a", token(b"\xff"), token(b"{"),
    token([]), token(None), token({}), token({**VALID, "extra": 1}),
    token(b'{"v":1,"v":1,"created_at":"2026-10-30T08:01:02.123456Z","id":"1"}'),
    *[token({**VALID, "v": v}) for v in (True, 2, "1", 1.0, None)],
    *[token({**VALID, "created_at": v}) for v in (
        None, 1, "2026-10-30T08:01:02.123456", "bad", "2026-02-30T08:01:02.123456Z",
        "2026-10-30T08:01:02Z", "2026-10-30T08:01:02.123Z", "2026-10-30T08:01:02.1234567Z",
        "2026-10-30T09:01:02.123456+01:00",
    )],
    *[token({**VALID, "id": v}) for v in (True, 1, "0", "-1", "01", "+1", "1e2", "1.0", "9223372036854775808")],
    token({"v": 1, "id": "1"}),
]


def test_cursor_round_trip_preserves_microseconds_and_bigint():
    boundary = HistoryCursor(created_at=STAMP, id=9223372036854775807)
    encoded = encode_cursor(boundary)
    assert "=" not in encoded
    assert decode_cursor(encoded) == boundary
    assert json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))) == VALID


@pytest.mark.parametrize("cursor", INVALID)
def test_invalid_cursor(cursor):
    with pytest.raises(InvalidCursor):
        decode_cursor(cursor)


async def put_fill(engine, uid, *, stamp=STAMP, side="buy", total="-100.00", high=False):
    cid = await coin_id(engine, "BTC")
    values = dict(user_id=uid, coin_id=cid, side=side, input_kind="quantity", input_value=Decimal("1"),
                  quantity=Decimal("0.00000001"), mid_price=Decimal("123"), price_as_of=stamp,
                  exec_price=Decimal("123.45678901"), fee=Decimal("0.25"), cash_delta=Decimal(total),
                  cash_after=Decimal("9900"), idempotency_key=uuid.uuid4(), created_at=stamp)
    async with engine.begin() as conn:
        if high:
            # Fixed SQL and bound fixture values, only on the guarded isolated test DB.
            result = await conn.execute(text("""INSERT INTO trades
                (id,user_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
                 exec_price,fee,cash_delta,cash_after,idempotency_key,created_at)
                OVERRIDING SYSTEM VALUE VALUES
                (9007199254740993,:user_id,:coin_id,:side,:input_kind,:input_value,:quantity,
                 :mid_price,:price_as_of,:exec_price,:fee,:cash_delta,:cash_after,:idempotency_key,:created_at)
                RETURNING id"""), values)
        else:
            result = await conn.execute(Trade.__table__.insert().values(**values).returning(Trade.id))
        return result.scalar_one()


@pytest.mark.parametrize("limit", [1, 25, 100])
async def test_keyset_exact_lookahead_and_refresh(db, engine, new_user, limit):
    uid, other = await new_user(), await new_user()
    assert (await list_history(db, user_id=uid, limit=limit)).items == []
    ids = [await put_fill(engine, uid) for _ in range(limit + 1)]
    foreign = await put_fill(engine, other)
    first = await list_history(db, user_id=uid, limit=limit)
    assert [int(i.id) for i in first.items] == sorted(ids, reverse=True)[:limit]
    assert decode_cursor(first.next_cursor).id == int(first.items[-1].id)
    second = await list_history(db, user_id=uid, limit=limit, cursor=first.next_cursor)
    assert [int(i.id) for i in second.items] == [min(ids)]
    assert second.next_cursor is None
    assert foreign not in [int(i.id) for i in first.items + second.items]
    scoped = await list_history(db, user_id=uid, limit=limit,
                                cursor=encode_cursor(HistoryCursor(created_at=STAMP, id=foreign)))
    assert all(int(i.id) in ids for i in scoped.items)
    newer = await put_fill(engine, uid, stamp=STAMP + timedelta(microseconds=1))
    assert int((await list_history(db, user_id=uid, limit=limit)).items[0].id) == newer


async def test_stored_totals_inactive_and_bigint(db, engine, new_user):
    uid = await new_user()
    high = await put_fill(engine, uid, high=True)
    await put_fill(engine, uid, side="sell", total="99.50", stamp=STAMP - timedelta(seconds=1))
    await put_fill(engine, uid, side="sell", total="0.00", stamp=STAMP - timedelta(seconds=2))
    async with engine.begin() as conn:
        await conn.execute(update(Coin).where(Coin.symbol == "BTC").values(is_active=False))
    try:
        statements = []
        def capture(conn, cursor, statement, parameters, context, executemany):
            statements.append((statement, parameters))
        event.listen(engine.sync_engine, "before_cursor_execute", capture)
        try:
            page = await list_history(db, user_id=uid)
        finally:
            event.remove(engine.sync_engine, "before_cursor_execute", capture)
        assert len(statements) == 1
        assert statements[0][0].lstrip().upper().startswith("SELECT")
        assert 26 in statements[0][1]
        assert page.items[0].id == str(high)
        assert page.items[0].created_at == STAMP
        assert [i.total for i in page.items] == [Decimal("-100"), Decimal("99.50"), Decimal("0")]
        assert page.items[0].exec_price == Decimal("123.45678901")
        assert page.items[0].fee == Decimal("0.25")
        assert page.next_cursor is None
    finally:
        async with engine.begin() as conn:
            await conn.execute(update(Coin).where(Coin.symbol == "BTC").values(is_active=True))
