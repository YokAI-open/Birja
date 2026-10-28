from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models.price import Coin, Price
from tests.helpers import OutboxSender, sign_in, unique_email


async def test_signed_out_gets_401(client: httpx.AsyncClient) -> None:
    resp = await client.get("/api/v1/prices")
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "not_authenticated"


async def test_signed_in_gets_prices(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    clean_prices: None,
) -> None:
    async with engine.begin() as conn:
        ids = {s: i for s, i in await conn.execute(select(Coin.symbol, Coin.id))}
        now = datetime.now(UTC)
        await conn.execute(
            insert(Price).values(
                coin_id=ids["DOGE"],
                mid=Decimal("0.0799807"),
                as_of=now - timedelta(seconds=600),
                source="fake",
            )
        )
        await conn.execute(
            insert(Price).values(
                coin_id=ids["BTC"],
                mid=Decimal("81042.35"),
                as_of=now - timedelta(seconds=10),
                source="fake",
            )
        )

    await sign_in(auth_client, outbox, unique_email("prices"))
    resp = await auth_client.get("/api/v1/prices")

    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "no-store"
    body = resp.json()
    assert body["fresh_seconds"] == 120
    assert body["stale_seconds"] == 300
    assert isinstance(body["server_time"], str)
    items = body["items"]
    assert [i["symbol"] for i in items] == ["BTC", "DOGE"]
    btc, doge = items
    assert btc["name"] == "Bitcoin"
    assert btc["price"] == "81042.35000000"
    assert isinstance(btc["price"], str)
    assert btc["status"] == "fresh"
    assert 9 <= btc["age_seconds"] <= 20
    assert isinstance(btc["as_of"], str)
    assert doge["price"] == "0.07998070"
    assert doge["status"] == "stale"
    assert doge["age_seconds"] >= 600


async def test_signed_in_empty_when_no_prices(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, clean_prices: None
) -> None:
    await sign_in(auth_client, outbox, unique_email("prices"))
    resp = await auth_client.get("/api/v1/prices")
    assert resp.status_code == 200
    assert resp.json()["items"] == []
