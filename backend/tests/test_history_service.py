import base64
import json
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import event, select, text, update

from app.models.price import Coin
from app.models.trade import Trade
from app.models.user import Account
from app.services.history import (
    HistoryCursor,
    InvalidCursor,
    decode_cursor,
    encode_cursor,
    list_history,
)
from app.services.portfolios import OwnedActivePortfolio
from tests.helpers import coin_id
from tests.stock_action_fixtures import synthetic_portfolio_id

STAMP = datetime(2026, 10, 30, 8, 1, 2, 123456, tzinfo=UTC)


def token(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


VALID = {
    "v": 2,
    "portfolio_id": "7",
    "created_at": "2026-10-30T08:01:02.123456Z",
    "id": "9223372036854775807",
}
INVALID = [
    "x" * 513,
    "",
    "!",
    "e30=",
    "e31",  # Nonzero discarded base64 bits decode to {}, but are not canonical.
    "a",
    token(b"\xff"),
    token(b"{"),
    token(json.dumps(VALID).encode()),
    token(b'"string"'),
    token([]),
    token(None),
    token({}),
    token({**VALID, "extra": 1}),
    token(b'{"v":2,"v":2,"portfolio_id":"7","created_at":"2026-10-30T08:01:02.123456Z","id":"1"}'),
    *[token({**VALID, "v": v}) for v in (True, 1, "2", 2.0, None)],
    *[
        token({**VALID, "created_at": v})
        for v in (
            None,
            1,
            "2026-10-30T08:01:02.123456",
            "bad",
            "2026-02-30T08:01:02.123456Z",
            "2026-10-30T08:01:02Z",
            "2026-10-30T08:01:02.123Z",
            "2026-10-30T08:01:02.1234567Z",
            "2026-10-30T09:01:02.123456+01:00",
        )
    ],
    *[
        token({**VALID, "id": v})
        for v in (True, 1, "0", "-1", "01", "+1", "1e2", "1.0", "9223372036854775808")
    ],
    *[
        token({**VALID, "portfolio_id": value})
        for value in (True, 7, "", "0", "-1", "07", "+7", "7.0", "7e0", "9223372036854775808")
    ],
    token({key: value for key, value in VALID.items() if key != "portfolio_id"}),
    token({"v": 1, "id": "1"}),
]


def test_cursor_round_trip_preserves_microseconds_and_bigint():
    boundary = HistoryCursor(created_at=STAMP, id=9223372036854775807, portfolio_id=7)
    encoded = encode_cursor(boundary)
    assert "=" not in encoded
    assert decode_cursor(encoded, expected_portfolio_id=7) == boundary
    assert json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))) == VALID


@pytest.mark.parametrize("cursor", INVALID)
def test_invalid_cursor(cursor):
    with pytest.raises(InvalidCursor):
        decode_cursor(cursor, expected_portfolio_id=7)


def test_cursor_encoder_refuses_naive_time():
    with pytest.raises(InvalidCursor):
        encode_cursor(HistoryCursor(created_at=STAMP.replace(tzinfo=None), id=1, portfolio_id=7))


def test_cursor_cannot_continue_another_portfolio():
    with pytest.raises(InvalidCursor):
        decode_cursor(token(VALID), expected_portfolio_id=8)


@pytest.mark.parametrize("limit", [0, 101, True, 1.0, "1"])
async def test_service_refuses_invalid_page_size_before_query(db, engine, limit):
    statements = []

    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", capture)
    try:
        with pytest.raises(ValueError, match="History limit must be between 1 and 100"):
            await list_history(db, portfolio=OwnedActivePortfolio(1, 1), limit=limit)
        assert statements == []
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", capture)


async def put_fill(engine, uid, *, stamp=STAMP, side="buy", total="-100.00", high=False):
    cid = await coin_id(engine, "BTC")
    values = dict(
        user_id=uid,
        coin_id=cid,
        side=side,
        input_kind="quantity",
        input_value=Decimal("1"),
        quantity=Decimal("0.00000001"),
        mid_price=Decimal("123"),
        price_as_of=stamp,
        exec_price=Decimal("123.45678901"),
        fee=Decimal("0.25"),
        cash_delta=Decimal(total),
        cash_after=Decimal("9900"),
        idempotency_key=uuid.uuid4(),
        created_at=stamp,
    )
    async with engine.begin() as conn:
        values["portfolio_id"] = (
            await conn.execute(select(Account.id).where(Account.user_id == uid))
        ).scalar_one()
        if high:
            # Fixed SQL and bound fixture values, only on the guarded isolated test DB.
            result = await conn.execute(
                text("""INSERT INTO trades
                (id,portfolio_id,user_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
                 exec_price,fee,cash_delta,cash_after,idempotency_key,created_at)
                OVERRIDING SYSTEM VALUE VALUES
                (:high_id,:portfolio_id,:user_id,:coin_id,:side,:input_kind,:input_value,:quantity,
                 :mid_price,:price_as_of,:exec_price,:fee,:cash_delta,:cash_after,:idempotency_key,:created_at)
                RETURNING id"""),
                {**values, "high_id": 9007199254740993 + uid},
            )
        else:
            result = await conn.execute(
                Trade.__table__.insert().values(**values).returning(Trade.id)
            )
        return result.scalar_one()


@pytest.mark.parametrize("limit", [1, 25, 100])
async def test_keyset_exact_lookahead_and_refresh(db, engine, new_user, limit):
    uid, other = await new_user(), await new_user()
    portfolio = OwnedActivePortfolio(await synthetic_portfolio_id(db, uid), uid)
    assert (await list_history(db, portfolio=portfolio, limit=limit)).items == []
    ids = [await put_fill(engine, uid) for _ in range(limit + 1)]
    foreign = await put_fill(engine, other)
    first = await list_history(db, portfolio=portfolio, limit=limit)
    assert [int(i.id) for i in first.items] == sorted(ids, reverse=True)[:limit]
    assert decode_cursor(first.next_cursor, expected_portfolio_id=portfolio.portfolio_id).id == int(
        first.items[-1].id
    )
    second = await list_history(db, portfolio=portfolio, limit=limit, cursor=first.next_cursor)
    assert [int(i.id) for i in second.items] == [min(ids)]
    assert second.next_cursor is None
    assert foreign not in [int(i.id) for i in first.items + second.items]
    scoped = await list_history(
        db,
        portfolio=portfolio,
        limit=limit,
        cursor=encode_cursor(
            HistoryCursor(created_at=STAMP, id=foreign, portfolio_id=portfolio.portfolio_id)
        ),
    )
    assert all(int(i.id) in ids for i in scoped.items)
    newer = await put_fill(engine, uid, stamp=STAMP + timedelta(microseconds=1))
    assert int((await list_history(db, portfolio=portfolio, limit=limit)).items[0].id) == newer


async def test_stored_totals_inactive_and_bigint(db, engine, new_user):
    uid = await new_user()
    portfolio = OwnedActivePortfolio(await synthetic_portfolio_id(db, uid), uid)
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
            page = await list_history(db, portfolio=portfolio)
        finally:
            event.remove(engine.sync_engine, "before_cursor_execute", capture)
        # Revalidate lifecycle before and after the one bounded ledger query.
        assert len(statements) == 3
        assert all(sql.lstrip().upper().startswith("SELECT") for sql, _ in statements)
        assert "accounts" in statements[0][0] and "accounts" in statements[2][0]
        assert "trades" in statements[1][0] and 26 in statements[1][1]
        assert page.items[0].id == str(high)
        assert page.items[0].created_at == STAMP
        assert [i.total for i in page.items] == [Decimal("-100"), Decimal("99.50"), Decimal("0")]
        assert page.items[0].exec_price == Decimal("123.45678901")
        assert page.items[0].fee == Decimal("0.25")
        assert page.next_cursor is None
    finally:
        async with engine.begin() as conn:
            await conn.execute(update(Coin).where(Coin.symbol == "BTC").values(is_active=True))


async def test_bigint_fill_fixture_does_not_collide_between_owners(db, engine, new_user):
    first, second = await new_user(), await new_user()
    first_root = OwnedActivePortfolio(await synthetic_portfolio_id(db, first), first)
    second_root = OwnedActivePortfolio(await synthetic_portfolio_id(db, second), second)
    first_id = await put_fill(engine, first, high=True)
    second_id = await put_fill(engine, second, high=True)
    assert first_id != second_id
    assert first_id > 9007199254740991 and second_id > 9007199254740991
    assert [item.id for item in (await list_history(db, portfolio=first_root)).items] == [
        str(first_id)
    ]
    assert [item.id for item in (await list_history(db, portfolio=second_root)).items] == [
        str(second_id)
    ]
