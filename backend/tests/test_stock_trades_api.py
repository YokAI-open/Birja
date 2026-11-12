# ruff: noqa: F811
"""Authenticated HTTP uses real stock execution and isolated persisted authority."""

from decimal import Decimal
from uuid import uuid4

import pytest_asyncio
from sqlalchemy import select

from app.models.user import User
from tests.helpers import csrf_headers, sign_in, unique_email
from tests.stock_trade_fixtures import ownership, status_case, stock_trade_case  # noqa: F401
from tests.test_stock_status import financial_snapshot

BASE="/api/v1/stock-trades"


@pytest_asyncio.fixture
async def stock_http(stock_trade_case,auth_client,outbox):
    factory,cid,unused,now=stock_trade_case
    email=unique_email("stock-http")
    await sign_in(auth_client,outbox,email)
    async with factory() as db:
        uid=await db.scalar(select(User.id).where(User.email==email))
    yield auth_client,await csrf_headers(auth_client),factory,cid,uid,now


def body(**changes):
    return {"symbol":"AAPL","side":"buy","quantity":"2","expected_exec_price":"102",
            "idempotency_key":str(uuid4()),**changes}


async def test_preview_context_and_fill_are_reachable_exact_and_private(stock_http):
    client,headers,factory,cid,uid,now=stock_http
    before=await financial_snapshot(factory)
    preview=await client.post(BASE+"/quote",json={"symbol":"AAPL","side":"buy","quantity":"2"},headers=headers)
    assert preview.status_code==200,preview.text
    assert Decimal(preview.json()["exec_price"])==102
    assert preview.headers["cache-control"]=="no-store"
    context=await client.get(BASE+"/AAPL/context")
    assert context.status_code==200 and Decimal(context.json()["buy_max_quantity"])==98
    assert await financial_snapshot(factory)==before
    order=body()
    fill=await client.post(BASE,json=order,headers=headers)
    assert fill.status_code==201,fill.text
    saved=fill.json()
    assert saved["coin_id"]==str(cid) and isinstance(saved["trade_id"],str)
    assert Decimal(saved["cash_after"])==9796 and Decimal(saved["held_after"])==2
    assert saved["fee"]=="0" and saved["feed"]=="iex"
    again=await client.post(BASE,json=order,headers=headers)
    assert again.status_code==200 and again.json()==saved
