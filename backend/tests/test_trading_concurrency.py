"""Success criterion 5: parallel requests never overspend, oversell or double-execute.

Real Postgres, real app engine (pool 5 + 10 overflow): every request gets its own session, so
the row locks in ``trading.execute`` are what keeps the books straight. Each gather stays at
15 requests or fewer so the pool is never exhausted.
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx
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
TRADE_URL = "/api/v1/trades"


async def _setup(
    client: httpx.AsyncClient, outbox: OutboxSender, engine: AsyncEngine
) -> tuple[int, dict[str, str]]:
    email = unique_email("race")
    await sign_in(client, outbox, email)
    async with engine.connect() as conn:
        user_id = (await conn.execute(select(User.id).where(User.email == email))).scalar_one()
    await put_price(engine, "BTC", "100000.00", datetime.now(UTC) - timedelta(seconds=5))
    return user_id, await csrf_headers(client)


def _body(
    side: str, value: str, key: uuid.UUID | None = None, kind: str = "amount_usd"
) -> dict[str, Any]:
    return {
        "symbol": "BTC",
        "side": side,
        kind: value,
        "expected_mid": "100000.00",
        "idempotency_key": str(key or uuid.uuid4()),
    }


async def _post(
    client: httpx.AsyncClient, headers: dict[str, str], body: dict[str, Any]
) -> httpx.Response:
    return await client.post(TRADE_URL, json=body, headers=headers)


async def test_parallel_buys_never_overspend(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    user_id, headers = await _setup(auth_client, outbox, engine)
    await set_cash(engine, user_id, "1000.00")

    results = await asyncio.gather(
        *(_post(auth_client, headers, _body("buy", "100.00")) for _ in range(15))
    )

    ok = [r for r in results if r.status_code == 201]
    refused = [r for r in results if r.status_code == 422]
    assert len(ok) == 10
    assert len(refused) == 5
    assert {r.json()["detail"]["code"] for r in refused} == {"insufficient_cash"}
    assert await cash_of(engine, user_id) == D("0.00")
    assert await trade_count(engine, user_id) == 10
    qty = sum(D(r.json()["quantity"]) for r in ok)
    assert qty == D("10") * D("0.00099501")
    assert await holding_of(engine, user_id, "BTC") == (qty, D("1000.00"))
    assert {D(r.json()["cash_after"]) for r in ok} == {D(x) for x in range(0, 1000, 100)}


async def test_same_key_in_parallel_creates_one_trade(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    user_id, headers = await _setup(auth_client, outbox, engine)
    body = _body("buy", "100.00", uuid.uuid4())

    results = await asyncio.gather(*(_post(auth_client, headers, body) for _ in range(10)))

    codes = sorted(r.status_code for r in results)
    assert codes == [200] * 9 + [201]
    assert all(r.json() == results[0].json() for r in results)
    assert await trade_count(engine, user_id) == 1
    assert await cash_of(engine, user_id) == D("9900.00")


async def test_parallel_sells_never_oversell(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    user_id, headers = await _setup(auth_client, outbox, engine)
    await put_holding(engine, user_id, "BTC", "0.001", "100.00")
    cash_before = await cash_of(engine, user_id)

    results = await asyncio.gather(
        *(_post(auth_client, headers, _body("sell", "0.0004", kind="quantity")) for _ in range(6))
    )

    ok = [r for r in results if r.status_code == 201]
    refused = [r for r in results if r.status_code == 422]
    assert len(ok) == 2
    assert len(refused) == 4
    assert {r.json()["detail"]["code"] for r in refused} == {"insufficient_quantity"}
    holding = await holding_of(engine, user_id, "BTC")
    assert holding is not None
    assert holding[0] == D("0.0002")
    assert await cash_of(engine, user_id) == cash_before + sum(
        D(r.json()["cash_delta"]) for r in ok
    )


async def test_mixed_buys_and_sells_keep_the_books_straight(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    user_id, headers = await _setup(auth_client, outbox, engine)
    await put_holding(engine, user_id, "BTC", "0.005", "500.00")
    await set_cash(engine, user_id, "10000.00")

    bodies = [_body("buy", "100.00") for _ in range(5)] + [
        _body("sell", "0.0005", kind="quantity") for _ in range(5)
    ]
    results = await asyncio.gather(*(_post(auth_client, headers, b) for b in bodies))

    assert all(r.status_code in (201, 422) for r in results)
    buys = [r for r in results[:5] if r.status_code == 201]
    sells = [r for r in results[5:] if r.status_code == 201]
    assert buys
    assert sells
    cash = await cash_of(engine, user_id)
    holding = await holding_of(engine, user_id, "BTC")
    assert holding is not None
    assert cash >= 0
    assert holding[0] >= 0
    assert cash == D("10000.00") + sum(D(r.json()["cash_delta"]) for r in buys + sells)
    assert holding[0] == (
        D("0.005")
        + sum(D(r.json()["quantity"]) for r in buys)
        - sum(D(r.json()["quantity"]) for r in sells)
    )
    assert await trade_count(engine, user_id) == len(buys) + len(sells)
