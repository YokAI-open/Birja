"""Actual PostgreSQL immutable stock receipt and cross-row financial tests."""

from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError


async def insert_trade(conn, cid, uid, **changes):
    values = dict(c=cid, u=uid, q="2", fee="0", delta="-20", price="10", key=str(uuid4()))
    values.update(changes)
    return (await conn.execute(text("""INSERT INTO public.trades
      (coin_id,user_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
       exec_price,fee,cash_delta,cash_after,idempotency_key)
      VALUES (:c,:u,'buy','quantity',:q,:q,10,clock_timestamp(),:price,:fee,:delta,9980,:key)
      RETURNING id"""), values)).scalar_one()


async def test_stock_trade_requires_complete_receipt(engine, migrated, new_user):
    uid = await new_user()
    async with engine.connect() as conn:
        tx = await conn.begin()
        cid = (await conn.execute(text("SELECT min(coin_id) FROM stock_instruments"))).scalar_one()
        await insert_trade(conn, cid, uid)
        with pytest.raises(DBAPIError, match="stock fill integrity"):
            await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        await tx.rollback()
