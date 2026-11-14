"""Actual PostgreSQL immutable stock receipt and cross-row financial tests."""

import json
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError


@pytest_asyncio.fixture
async def receipt(engine, migrated, new_user):
    uid = await new_user()
    async with engine.connect() as conn:
        tx = await conn.begin()
        cid = (await conn.execute(text("SELECT min(coin_id) FROM stock_instruments"))).scalar_one()
        yield conn, cid, uid
        await tx.rollback()


async def complete_receipt(conn, cid, uid, *, movement_changes=None, authority=None, **changes):
    tid = await insert_trade(conn, cid, uid, **changes)
    await conn.execute(
        text("""INSERT INTO stock_fill_facts
      (trade_id,coin_id,user_id,provider_asset_id,symbol,company_name,listing_exchange,
      source,feed,bid,ask,exact_mid,held_after,event_at,collected_at,observed_at,
      session_date,opens_at,closes_at,authority)
      SELECT id,coin_id,user_id,'fixture-asset','AAPL','Test company','NASDAQ',
      'alpaca','iex',10,10,10,2,price_as_of,price_as_of,price_as_of,
      (price_as_of AT TIME ZONE 'UTC')::date,price_as_of-interval '1 hour',
      price_as_of+interval '1 hour',CAST(:authority AS jsonb) FROM trades WHERE id=:t"""),
        {"t": tid, "authority": json.dumps(authority or {})},
    )
    movement_values = {"c": cid, "u": uid, "t": tid, "k": str(uuid4()), "bb": "0", "ab": "20"}
    movement_values.update(movement_changes or {})
    await conn.execute(
        text("""INSERT INTO stock_ownership_movements
      (coin_id,user_id,sequence,economic_at,recorded_at,quantity,before_quantity,
       after_quantity,before_basis,after_basis,unit_epoch,cause_kind,trade_id,causal_key)
      VALUES (:c,:u,900000000,clock_timestamp(),clock_timestamp(),2,0,2,:bb,:ab,0,'fill',:t,:k)"""),
        movement_values,
    )
    return tid


async def insert_trade(conn, cid, uid, **changes):
    values = dict(c=cid, u=uid, q="2", fee="0", delta="-20", price="10", key=str(uuid4()), at=None)
    values.update(changes)
    return (
        await conn.execute(
            text("""INSERT INTO public.trades
      (coin_id,user_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
       exec_price,fee,cash_delta,cash_after,idempotency_key)
      VALUES (:c,:u,'buy','quantity',:q,:q,10,
      COALESCE(CAST(:at AS timestamptz),clock_timestamp()),:price,:fee,:delta,9980,:key)
      RETURNING id"""),
            values,
        )
    ).scalar_one()


async def test_stock_trade_requires_complete_receipt(engine, migrated, new_user):
    uid = await new_user()
    async with engine.connect() as conn:
        tx = await conn.begin()
        cid = (await conn.execute(text("SELECT min(coin_id) FROM stock_instruments"))).scalar_one()
        await insert_trade(conn, cid, uid)
        with pytest.raises(DBAPIError, match="stock fill integrity"):
            await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        await tx.rollback()


async def test_complete_receipt_passes_deferred_constraint(receipt):
    conn, cid, uid = receipt
    tid = await complete_receipt(conn, cid, uid)
    await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    assert (
        await conn.execute(
            text("SELECT held_after FROM stock_fill_facts WHERE trade_id=:t"), {"t": tid}
        )
    ).scalar_one() == 2


@pytest.mark.parametrize(
    "changes", [dict(q="1.5"), dict(fee="1"), dict(delta="-19"), dict(price="11")]
)
async def test_invalid_financial_cross_rows_cannot_commit(receipt, changes):
    conn, cid, uid = receipt
    await complete_receipt(conn, cid, uid, **changes)
    with pytest.raises(DBAPIError, match="stock fill integrity"):
        await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))


@pytest.mark.parametrize("table", ["stock_fill_facts", "stock_ownership_movements", "trades"])
@pytest.mark.parametrize("verb", ["UPDATE", "DELETE"])
async def test_ordinary_owner_dml_cannot_rewrite_financial_history(receipt, table, verb):
    conn, cid, uid = receipt
    tid = await complete_receipt(conn, cid, uid)
    await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    column = "id" if table == "trades" else "trade_id"
    mutable = "cash_after" if table == "trades" else column
    sql = (
        f"DELETE FROM public.{table} WHERE {column}=:t"  # noqa: S608 - fixed test matrix
        if verb == "DELETE"
        else f"UPDATE public.{table} SET {mutable}={mutable} WHERE {column}=:t"  # noqa: S608
    )
    with pytest.raises(DBAPIError, match="immutable"):
        await conn.execute(text(sql), {"t": tid})


@pytest.mark.parametrize(
    "field,value", [("after_basis", "19"), ("after_quantity", "3"), ("quantity", "-2")]
)
async def test_movement_mismatch_is_rejected(receipt, field, value):
    conn, cid, uid = receipt
    # Change test input INSERT before the append-only trigger can apply.
    tid = await insert_trade(conn, cid, uid)
    with pytest.raises(DBAPIError):
        await conn.execute(
            text("""INSERT INTO stock_ownership_movements
        (coin_id,user_id,sequence,economic_at,recorded_at,quantity,before_quantity,
        after_quantity,before_basis,after_basis,unit_epoch,cause_kind,trade_id,causal_key)
        VALUES (:c,:u,900000000,now(),now(),:q,0,:after,0,:basis,
        0,'fill',:t,'test')"""),
            {
                "c": cid,
                "u": uid,
                "t": tid,
                "q": value if field == "quantity" else "2",
                "after": value if field == "after_quantity" else "2",
                "basis": value if field == "after_basis" else "20",
            },
        )
        await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))


@pytest.mark.parametrize("lease", ["0 seconds", "61 seconds"])
async def test_status_lease_is_bounded(receipt, lease):
    conn, cid, _ = receipt
    with pytest.raises(DBAPIError):
        await conn.execute(
            text("""INSERT INTO stock_status_evidence
        (coin_id,provider_asset_id,source_ref,observed_at,valid_until)
        VALUES (:c,'fixture','fixture',now(),now()+CAST(:lease AS interval))"""),
            {"c": cid, "lease": lease},
        )


async def test_derived_basis_cross_row_must_match_cash(receipt):
    conn, cid, uid = receipt
    await complete_receipt(conn, cid, uid, movement_changes={"ab": "19"})
    with pytest.raises(DBAPIError, match="basis mismatch"):
        await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))


async def test_crypto_cannot_receive_stock_facts(receipt):
    conn, _, uid = receipt
    cid = (await conn.execute(text("SELECT id FROM coins WHERE symbol='BTC'"))).scalar_one()
    with pytest.raises(DBAPIError):
        await complete_receipt(conn, cid, uid)
        await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))


async def test_empty_downgrade_and_populated_upgrade_preserve_financial_rows(engine, migrated):
    from tests.test_migrations import EXPECTED_HEAD, _versions
    from tests.test_stock_migrations import _financial_snapshot, migrate

    before = await _financial_snapshot(engine)
    await migrate("0012", down=True)
    assert await _versions(engine) == ["0012"]
    assert await _financial_snapshot(engine) == before
    await migrate("head")
    assert await _versions(engine) == [EXPECTED_HEAD]
    assert await _financial_snapshot(engine) == before


async def test_populated_status_prevents_downgrade(engine, migrated):
    from tests.test_stock_migrations import migrate

    async with engine.begin() as conn:
        cid = (await conn.execute(text("SELECT min(coin_id) FROM stock_instruments"))).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO stock_status_evidence(coin_id,provider_asset_id,source_ref) "
                "VALUES (:c,'fixture','fixture')"
            ),
            {"c": cid},
        )
    try:
        with pytest.raises(DBAPIError, match="populated stock execution"):
            await migrate("0012", down=True)
    finally:
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM stock_status_evidence WHERE coin_id=:c"), {"c": cid}
            )
