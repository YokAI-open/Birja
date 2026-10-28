import uuid
from datetime import datetime
from decimal import Decimal

import httpx
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models.price import Coin, Price
from app.models.trade import Holding, Trade
from app.models.user import Account


class OutboxSender:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    async def send_code(self, to: str, code: str) -> None:
        self.messages.append((to, code))


async def csrf_headers(client: httpx.AsyncClient) -> dict[str, str]:
    await client.get("/api/v1/auth/csrf")
    return {"X-CSRF-Token": client.cookies["bj_csrf"]}


def unique_email(prefix: str = "user") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


async def request_and_get_code(client: httpx.AsyncClient, outbox: OutboxSender, email: str) -> str:
    headers = await csrf_headers(client)
    resp = await client.post("/api/v1/auth/request-code", json={"email": email}, headers=headers)
    assert resp.status_code == 202
    return [code for to, code in outbox.messages if to == email][-1]


async def sign_in(client: httpx.AsyncClient, outbox: OutboxSender, email: str) -> httpx.Response:
    code = await request_and_get_code(client, outbox, email)
    headers = {"X-CSRF-Token": client.cookies["bj_csrf"]}
    resp = await client.post(
        "/api/v1/auth/verify-code", json={"email": email, "code": code}, headers=headers
    )
    assert resp.status_code == 200
    return resp


async def coin_id(engine: AsyncEngine, symbol: str) -> int:
    async with engine.connect() as conn:
        return (await conn.execute(select(Coin.id).where(Coin.symbol == symbol))).scalar_one()


async def put_price(engine: AsyncEngine, symbol: str, mid: str, as_of: datetime) -> None:
    cid = await coin_id(engine, symbol)
    stmt = pg_insert(Price).values(coin_id=cid, mid=Decimal(mid), as_of=as_of, source="fake")
    stmt = stmt.on_conflict_do_update(
        index_elements=[Price.coin_id],
        set_={"mid": stmt.excluded.mid, "as_of": stmt.excluded.as_of},
    )
    async with engine.begin() as conn:
        await conn.execute(stmt)


async def set_cash(engine: AsyncEngine, user_id: int, cash: str) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            update(Account).where(Account.user_id == user_id).values(cash=Decimal(cash))
        )


async def put_holding(
    engine: AsyncEngine, user_id: int, symbol: str, quantity: str, cost_basis: str
) -> None:
    cid = await coin_id(engine, symbol)
    async with engine.begin() as conn:
        await conn.execute(
            delete(Holding).where(Holding.user_id == user_id, Holding.coin_id == cid)
        )
        await conn.execute(
            pg_insert(Holding).values(
                user_id=user_id,
                coin_id=cid,
                quantity=Decimal(quantity),
                cost_basis=Decimal(cost_basis),
            )
        )


async def cash_of(engine: AsyncEngine, user_id: int) -> Decimal:
    async with engine.connect() as conn:
        return (
            await conn.execute(select(Account.cash).where(Account.user_id == user_id))
        ).scalar_one()


async def holding_of(
    engine: AsyncEngine, user_id: int, symbol: str
) -> tuple[Decimal, Decimal] | None:
    cid = await coin_id(engine, symbol)
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                select(Holding.quantity, Holding.cost_basis).where(
                    Holding.user_id == user_id, Holding.coin_id == cid
                )
            )
        ).first()
    return None if row is None else (row[0], row[1])


async def trade_count(engine: AsyncEngine, user_id: int) -> int:
    async with engine.connect() as conn:
        return (
            await conn.execute(
                select(func.count()).select_from(Trade).where(Trade.user_id == user_id)
            )
        ).scalar_one()
