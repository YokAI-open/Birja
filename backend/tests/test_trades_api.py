import re
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models.user import User
from tests.helpers import (
    OutboxSender,
    cash_of,
    csrf_headers,
    holding_of,
    put_holding,
    put_price,
    set_cash,
    sign_in,
    trade_count,
    unique_email,
)

D = Decimal
QUOTE_URL = "/api/v1/trades/quote"
TRADE_URL = "/api/v1/trades"
MONEY_QUOTE = [
    "input_value",
    "mid",
    "exec_price",
    "quantity",
    "notional",
    "fee",
    "cash_delta",
    "cash_before",
    "cash_after",
    "held_before",
    "held_after",
]
MONEY_FILL = [
    "input_value",
    "mid",
    "exec_price",
    "quantity",
    "notional",
    "fee",
    "cash_delta",
    "cash_after",
]
QUOTE_FIELDS = set(MONEY_QUOTE) | {
    "symbol",
    "side",
    "input_kind",
    "as_of",
    "age_seconds",
    "whole_position",
}
FILL_FIELDS = set(MONEY_FILL) | {"trade_id", "created_at", "symbol", "side", "input_kind", "as_of"}
PLAIN = re.compile(r"^-?\d+(\.\d+)?$")


async def _trader(
    client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    *,
    mid: str = "100000.00",
    age: float = 10,
) -> tuple[int, dict[str, str]]:
    email = unique_email("api")
    await sign_in(client, outbox, email)
    async with engine.connect() as conn:
        user_id = (await conn.execute(select(User.id).where(User.email == email))).scalar_one()
    await put_price(engine, "BTC", mid, datetime.now(UTC) - timedelta(seconds=age))
    return user_id, await csrf_headers(client)


def _buy(amount: str = "100.00", **extra: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"symbol": "BTC", "side": "buy", "amount_usd": amount}
    return body | extra


def _trade_body(key: uuid.UUID | None = None, mid: str = "100000.00", **kw: Any) -> dict[str, Any]:
    body = _buy(**kw) | {"expected_mid": mid, "idempotency_key": str(key or uuid.uuid4())}
    return body


def _assert_plain(body: dict[str, Any], fields: list[str]) -> None:
    for name in fields:
        value = body[name]
        assert isinstance(value, str), name
        assert PLAIN.match(value), (name, value)
        assert "e" not in value.lower()  # plain notation: never 0E-8 or any [eE] exponent


@pytest.mark.parametrize(("url", "body"), [(QUOTE_URL, _buy()), (TRADE_URL, _trade_body())])
async def test_signed_out_post_is_401(
    auth_client: httpx.AsyncClient, url: str, body: dict[str, Any]
) -> None:
    headers = await csrf_headers(auth_client)
    resp = await auth_client.post(url, json=body, headers=headers)
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "not_authenticated"


async def test_signed_out_holdings_is_401(auth_client: httpx.AsyncClient) -> None:
    assert (await auth_client.get("/api/v1/holdings/BTC")).status_code == 401


async def test_missing_csrf_is_403_and_writes_nothing(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    user_id, _ = await _trader(auth_client, outbox, engine)
    for url, body in ((QUOTE_URL, _buy()), (TRADE_URL, _trade_body())):
        resp = await auth_client.post(url, json=body, headers={"X-CSRF-Token": "wrong"})
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "csrf_failed"
    assert await trade_count(engine, user_id) == 0
    assert await cash_of(engine, user_id) == D("10000.00")


async def test_quote_buy_is_read_only_and_typed(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    user_id, headers = await _trader(auth_client, outbox, engine)
    resp = await auth_client.post(QUOTE_URL, json=_buy(), headers=headers)

    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "no-store"
    body = resp.json()
    assert set(body) == QUOTE_FIELDS
    _assert_plain(body, MONEY_QUOTE)
    assert isinstance(body["age_seconds"], int)
    assert body["whole_position"] is False
    assert body["symbol"] == "BTC"
    assert body["input_kind"] == "usd"
    assert D(body["exec_price"]) == D("100250")
    assert D(body["fee"]) == D("0.25")
    assert D(body["quantity"]) == D("0.00099501")
    assert D(body["cash_delta"]) == D("-100.00")
    assert D(body["cash_after"]) == D("9900.00")
    assert await trade_count(engine, user_id) == 0
    assert D((await auth_client.get("/api/v1/me")).json()["cash_usd"]) == D("10000.00")


async def test_quote_symbol_is_case_insensitive_and_unknown_is_404(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    _, headers = await _trader(auth_client, outbox, engine)
    ok = await auth_client.post(QUOTE_URL, json=_buy() | {"symbol": "btc"}, headers=headers)
    assert ok.status_code == 200
    assert ok.json()["symbol"] == "BTC"

    nope = await auth_client.post(QUOTE_URL, json=_buy() | {"symbol": "NOPE"}, headers=headers)
    assert nope.status_code == 404
    assert nope.json()["detail"]["code"] == "unknown_coin"


@pytest.mark.parametrize(
    "patch",
    [
        {"quantity": "0.5"},  # both inputs
        {"amount_usd": None},  # neither input
        {"side": "sell"},  # sell by amount
        {"amount_usd": "1.005"},
        {"amount_usd": "0"},
        {"amount_usd": "-1"},
        {"amount_usd": "NaN"},
        {"amount_usd": "Infinity"},
        {"amount_usd": None, "quantity": "0.000000001"},
        {"amount_usd": None, "quantity": "0"},
        {"amount_usd": None, "quantity": "-1"},
        {"amount_usd": None, "quantity": "NaN"},
        {"side": "hold"},
        {"symbol": "BT-C"},
        {"extra": 1},
    ],
)
async def test_quote_validation_is_422(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
    patch: dict[str, Any],
) -> None:
    _, headers = await _trader(auth_client, outbox, engine)
    body = {k: v for k, v in (_buy() | patch).items() if v is not None}
    resp = await auth_client.post(QUOTE_URL, json=body, headers=headers)
    assert resp.status_code == 422
    assert not isinstance(resp.json()["detail"], dict)  # pydantic list, no domain code


@pytest.mark.parametrize(
    "patch",
    [{"idempotency_key": "not-a-uuid"}, {"expected_mid": None}],
)
async def test_trade_validation_is_422(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
    patch: dict[str, Any],
) -> None:
    user_id, headers = await _trader(auth_client, outbox, engine)
    body = {k: v for k, v in (_trade_body() | patch).items() if v is not None}
    resp = await auth_client.post(TRADE_URL, json=body, headers=headers)
    assert resp.status_code == 422
    assert await trade_count(engine, user_id) == 0


async def test_execute_buy_then_replay_is_byte_identical(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    user_id, headers = await _trader(auth_client, outbox, engine)
    key = uuid.uuid4()
    resp1 = await auth_client.post(TRADE_URL, json=_trade_body(key), headers=headers)

    assert resp1.status_code == 201
    assert resp1.headers["cache-control"] == "no-store"
    fill = resp1.json()
    assert set(fill) == FILL_FIELDS
    _assert_plain(fill, MONEY_FILL)
    assert isinstance(fill["trade_id"], int)
    assert D(fill["cash_after"]) == D("9900.00")
    me = (await auth_client.get("/api/v1/me")).json()
    assert D(me["cash_usd"]) == D(fill["cash_after"])

    resp2 = await auth_client.post(TRADE_URL, json=_trade_body(key), headers=headers)
    assert resp2.status_code == 200
    assert resp2.json() == resp1.json()
    assert await trade_count(engine, user_id) == 1

    other = await auth_client.post(
        TRADE_URL, json=_trade_body(key, amount_usd="50.00"), headers=headers
    )
    assert other.status_code == 409
    assert other.json()["detail"]["code"] == "idempotency_conflict"
    assert await trade_count(engine, user_id) == 1


async def test_price_changed_returns_fresh_quote(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    user_id, headers = await _trader(auth_client, outbox, engine)
    resp = await auth_client.post(TRADE_URL, json=_trade_body(mid="99999.00"), headers=headers)

    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert detail["code"] == "price_changed"
    assert set(detail["quote"]) == QUOTE_FIELDS
    _assert_plain(detail["quote"], MONEY_QUOTE)
    assert D(detail["quote"]["mid"]) == D("100000")
    assert await trade_count(engine, user_id) == 0


async def test_stale_price_boundary(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    user_id, headers = await _trader(auth_client, outbox, engine, age=120)
    quote = await auth_client.post(QUOTE_URL, json=_buy(), headers=headers)
    assert quote.status_code == 409
    assert quote.json()["detail"]["code"] == "stale_price"
    trade = await auth_client.post(TRADE_URL, json=_trade_body(), headers=headers)
    assert trade.status_code == 409
    assert trade.json()["detail"]["code"] == "stale_price"
    assert await trade_count(engine, user_id) == 0

    await put_price(engine, "BTC", "100000.00", datetime.now(UTC) - timedelta(seconds=118.5))
    assert (await auth_client.post(QUOTE_URL, json=_buy(), headers=headers)).status_code == 200


async def test_below_minimum_is_422(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    _, headers = await _trader(auth_client, outbox, engine)
    small = await auth_client.post(QUOTE_URL, json=_buy("0.99"), headers=headers)
    assert small.status_code == 422
    assert small.json()["detail"]["code"] == "below_minimum"


async def test_insufficient_cash_is_422(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    user_id, headers = await _trader(auth_client, outbox, engine)
    await set_cash(engine, user_id, "50.00")
    poor = await auth_client.post(QUOTE_URL, json=_buy(), headers=headers)
    assert poor.status_code == 422
    assert poor.json()["detail"]["code"] == "insufficient_cash"
    assert poor.json()["detail"]["message"] == "You have $50.00; this order needs $100.00."


async def test_insufficient_quantity_is_422(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    _, headers = await _trader(auth_client, outbox, engine)
    sell = await auth_client.post(
        QUOTE_URL, json={"symbol": "BTC", "side": "sell", "quantity": "1"}, headers=headers
    )
    assert sell.status_code == 422
    assert sell.json()["detail"]["code"] == "insufficient_quantity"


async def test_order_too_large_is_422(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    _, headers = await _trader(auth_client, outbox, engine)
    huge = await auth_client.post(
        QUOTE_URL,
        json={"symbol": "BTC", "side": "buy", "quantity": "999999999999"},
        headers=headers,
    )
    assert huge.status_code == 422
    assert huge.json()["detail"]["code"] == "order_too_large"


async def test_holdings_lifecycle_in_plain_notation(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    user_id, headers = await _trader(auth_client, outbox, engine)
    before = await auth_client.get("/api/v1/holdings/BTC")
    assert before.status_code == 200
    assert D(before.json()["quantity"]) == 0
    assert before.json()["symbol"] == "BTC"

    await auth_client.post(TRADE_URL, json=_trade_body(), headers=headers)
    after = await auth_client.get("/api/v1/holdings/btc")
    assert after.json()["quantity"] == "0.00099501"

    sell = {
        "symbol": "BTC",
        "side": "sell",
        "quantity": "0.00099501",
        "expected_mid": "100000.00",
        "idempotency_key": str(uuid.uuid4()),
    }
    assert (await auth_client.post(TRADE_URL, json=sell, headers=headers)).status_code == 201
    empty = await auth_client.get("/api/v1/holdings/BTC")
    assert empty.json()["quantity"] == "0.00000000"
    assert await holding_of(engine, user_id, "BTC") == (D("0"), D("0"))


async def test_unknown_holding_is_404(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, engine: AsyncEngine
) -> None:
    await sign_in(auth_client, outbox, unique_email("api"))
    unknown = await auth_client.get("/api/v1/holdings/NOPE")
    assert unknown.status_code == 404
    assert unknown.json()["detail"]["code"] == "unknown_coin"


async def test_sub_cent_whole_position_sell_is_plain_zero(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    user_id, headers = await _trader(auth_client, outbox, engine)
    await put_price(engine, "DOGE", "0.08", datetime.now(UTC) - timedelta(seconds=5))
    await put_holding(engine, user_id, "DOGE", "0.05", "0.01")
    body = {
        "symbol": "DOGE",
        "side": "sell",
        "quantity": "0.05",
        "expected_mid": "0.08",
        "idempotency_key": str(uuid.uuid4()),
    }
    resp = await auth_client.post(TRADE_URL, json=body, headers=headers)

    assert resp.status_code == 201
    fill = resp.json()
    _assert_plain(fill, MONEY_FILL)
    assert fill["fee"] == "0.00000000"
    assert fill["cash_delta"] == "0.00000000"
