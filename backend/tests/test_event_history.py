"""Real SQL owner-scoped mixed publication and immutable linked originals."""

import asyncio
import json
import shutil
import subprocess
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import event as sql_event
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.event_history import EventHistoryCursor, encode_cursor, list_event_history
from tests.test_dividend_authority import authority_case, successor
from tests.test_dividend_corrections import hold
from tests.test_dividend_payments import process
from tests.test_dividend_schema import dividend_case
from tests.test_stock_action_migrations import event, ledger

__all__ = ["authority_case", "dividend_case", "ledger"]


async def test_mixed_original_is_published_from_actual_cash_effect(authority_case):
    conn, ids = authority_case
    result = await process(conn, ids)
    async with AsyncSession(bind=conn) as db:
        page = await list_event_history(db, user_id=ids["user_id"])
    assert len(page.items) == 1, "Real dividend cash must publish its immutable History original"
    assert page.items[0].id == f"dividend:{result.payment_id}"


async def page_for(conn, uid, **kw):
    async with AsyncSession(bind=conn) as db:
        return await list_event_history(db, user_id=uid, **kw)


async def fill(conn, uid, stamp, *, cid=None, stock=False, high=False):
    await conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
    if cid is None:
        cid = (await conn.execute(text("SELECT id FROM coins WHERE symbol='BTC'"))).scalar_one()
    # Projection fixtures are retained immutable facts, not mocked trade execution.
    sql = """INSERT INTO trades (user_id,coin_id,side,input_kind,input_value,quantity,
        mid_price,price_as_of,exec_price,fee,cash_delta,cash_after,idempotency_key,created_at)
        VALUES (:u,:c,'buy','quantity',2,2,10,:t,10,0,-20,80,:k,:t) RETURNING id"""
    if stock:
        sql = sql.replace("quantity',2,2,10,", "quantity',2,2,9.5,")
    if high:
        sql = sql.replace("(user_id,", "(id,user_id,").replace(
            "VALUES (:u,", "OVERRIDING SYSTEM VALUE VALUES (:high_id,:u,"
        )
    tid = (
        await conn.execute(
            text(sql),
            {"u": uid, "c": cid, "t": stamp, "k": uuid4(), "high_id": 9007199254740993 + uid},
        )
    ).scalar_one()
    if stock:
        await conn.execute(
            text("""INSERT INTO stock_fill_facts
          (trade_id,coin_id,user_id,provider_asset_id,symbol,company_name,listing_exchange,
          source,feed,bid,ask,exact_mid,held_after,event_at,collected_at,observed_at,
          session_date,opens_at,closes_at,authority) VALUES
          (:id,:c,:u,'saved-asset','AAPL','Saved Apple','NASDAQ','alpaca','iex',9,10,9.5,4,
          :t,:t,:t,CAST(:t AS timestamptz)::date,
          :t-interval '1 hour',:t+interval '1 hour','{}')"""),
            {"id": tid, "c": cid, "u": uid, "t": stamp},
        )
        await conn.execute(
            text("""INSERT INTO stock_ownership_movements
          (coin_id,user_id,sequence,economic_at,recorded_at,quantity,before_quantity,
          after_quantity,before_basis,after_basis,unit_epoch,cause_kind,trade_id,causal_key)
          VALUES (:c,:u,2,:t,:t,2,2,4,20,40,0,'fill',:id,:k)"""),
            {"c": cid, "u": uid, "t": stamp, "id": tid, "k": str(uuid4())},
        )
    return tid


async def split_row(conn, ids, stamp):
    eid, _, rid = await event(conn, ids["coin_id"])
    await conn.execute(
        text(
            "UPDATE stock_action_revisions SET normalized_terms=CAST(:terms AS jsonb) WHERE id=:r"
        ),
        {"r": rid, "terms": json.dumps({"symbol": "AAPL"})},
    )
    aid = (
        await conn.execute(
            text("""INSERT INTO stock_split_applications
      (coin_id,economic_event_id,revision_id,new_rate,old_rate,cutoff,prior_unit_epoch,
      new_unit_epoch,sequence_boundary,before_digest,after_digest,processed_at)
      VALUES (:c,:e,:r,'1.5','1',:t,0,1,3,repeat('a',64),repeat('b',64),:t) RETURNING id"""),
            {"c": ids["coin_id"], "e": eid, "r": rid, "t": stamp},
        )
    ).scalar_one()
    return (
        await conn.execute(
            text("""INSERT INTO stock_ownership_movements
      (coin_id,user_id,sequence,economic_at,recorded_at,quantity,before_quantity,
      after_quantity,before_basis,after_basis,unit_epoch,cause_kind,application_id,causal_key)
      VALUES (:c,:u,3,:t,:t,2,4,6,40,40,1,'split',:a,:k) RETURNING id"""),
            {"c": ids["coin_id"], "u": ids["user_id"], "t": stamp, "a": aid, "k": str(uuid4())},
        )
    ).scalar_one()


@pytest.mark.parametrize("limit", [1, 2, 3, 25, 100])
async def test_mixed_tied_time_whole_tuple_owner_paging_and_rename(authority_case, limit, tmp_path):
    conn, ids = authority_case
    result = await process(conn, ids)
    original = (await page_for(conn, ids["user_id"])).items[0]
    stamp = (
        await conn.execute(
            text("SELECT recorded_at FROM stock_dividend_payments WHERE id=:p"),
            {"p": result.payment_id},
        )
    ).scalar_one()
    crypto = await fill(conn, ids["user_id"], stamp, high=True)
    stock = await fill(conn, ids["user_id"], stamp, cid=ids["coin_id"], stock=True)
    split = await split_row(conn, ids, stamp)
    await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    expected = [
        f"trade:{max(stock, crypto)}",
        f"trade:{min(stock, crypto)}",
        original.id,
        f"split:{split}",
    ]
    owner = ids["user_id"]
    other = (
        await conn.execute(
            text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
            {"e": f"other-history-{uuid4()}@example.test"},
        )
    ).scalar_one()
    foreign = await fill(conn, other, stamp)
    all_items, cursor = [], None
    while True:
        page = await page_for(conn, owner, limit=limit, cursor=cursor)
        all_items.extend(page.items)
        cursor = page.next_cursor
        if cursor is None:
            break
    assert [item.id for item in all_items] == expected
    assert len({item.id for item in all_items}) == 4
    assert all(item.id != f"trade:{foreign}" for item in all_items)
    split_item = next(item for item in all_items if item.kind == "split")
    assert (split_item.ratio_new, split_item.ratio_old) == ("3", "2")
    assert (split_item.quantity_before, split_item.quantity_after) == ("4.00000000", "6.00000000")
    assert split_item.cost_basis_before == split_item.cost_basis_after == "40.00000000"
    assert split_item.name == "AAPL"
    before = (await page_for(conn, owner)).model_dump(mode="json")
    await conn.execute(
        text("UPDATE coins SET symbol='RENAMED',name='Mutable Company' WHERE id=:c"),
        {"c": ids["coin_id"]},
    )
    assert (await page_for(conn, owner)).model_dump(mode="json") == before
    forged = encode_cursor(EventHistoryCursor(stamp, 4, foreign))
    assert all(i.id in expected for i in (await page_for(conn, owner, cursor=forged)).items)
    assert (await page_for(conn, other)).items[0].id == f"trade:{foreign}"
    assert (
        await page_for(conn, other, cursor=encode_cursor(EventHistoryCursor(stamp, 1, 1)))
    ).items == []
    inserted = await fill(conn, owner, stamp + timedelta(microseconds=1))
    assert (await page_for(conn, owner, limit=1)).items[0].id == f"trade:{inserted}"
    if limit == 25:
        # Execute the actual installed TS parser against a real database page.
        await asyncio.to_thread(assert_current_ts_parser, before, tmp_path)


def assert_current_ts_parser(page, directory):
    path = directory / "wire.json"
    path.write_text(json.dumps(page))
    parser = Path(__file__).resolve().parents[2] / "frontend/src/api/eventHistory.ts"
    source = parser.read_text().replace(
        'import { apiFetch } from "./client";',
        'const apiFetch = async (..._args: any[]): Promise<any> => { throw new Error("unused"); };',
    )
    module = directory / "wire-parser.ts"
    module.write_text(source)
    node = shutil.which("node")
    assert node is not None, "Existing approved Node24 is required for wire compatibility"
    script = (
        "import fs from 'node:fs'; "
        "const {isEventHistoryPage} = await import(process.argv[1]); "
        "if (!isEventHistoryPage(JSON.parse(fs.readFileSync(process.argv[2],'utf8')))) "
        "process.exit(1);"
    )
    checked = subprocess.run(  # noqa: S603 - resolved Node, fixed script and pytest-owned paths
        [node, "--input-type=module", "-e", script, module.as_uri(), str(path)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert checked.returncode == 0, checked.stderr


@pytest.mark.parametrize("classification", ["uncertain", "cancelled"])
async def test_lineage_offpage_actual_hold_dedup_and_owner(authority_case, classification):
    conn, ids = authority_case
    original = await process(conn, ids)
    saved = (await page_for(conn, ids["user_id"])).items[0]
    revised = await successor(conn, ids, classification=classification, eligible=False)
    held = await hold(conn, original.payment_id, revised["revision_fingerprint"])
    assert await hold(conn, original.payment_id, revised["revision_fingerprint"]) == held
    page = await page_for(conn, ids["user_id"], limit=1)
    correction = page.items[0]
    assert correction.kind == "dividend_correction"
    assert correction.original == saved and correction.payment_reference == saved.id
    assert correction.outcome == "held_uncertain" and correction.terms is None
    assert correction.desired_total is None and correction.proposed_delta is None
    assert Decimal(correction.cash_delta) == Decimal(correction.applied_delta) == 0
    assert page.next_cursor is not None
    assert (await page_for(conn, ids["user_id"], cursor=page.next_cursor)).items == [saved]
    assert (await page_for(conn, 9223372036854775807)).items == []


@pytest.mark.parametrize(
    "rate,outcome",
    [("0.75", "applied"), ("0.5", "verified_no_change"), ("0.1", "held_unaffordable")],
)
async def test_lineage_verified_actual_correction_outcomes(authority_case, rate, outcome):
    conn, ids = authority_case
    original = await process(conn, ids)
    saved = (await page_for(conn, ids["user_id"])).items[0]
    revised = await successor(conn, ids, rate=rate)
    if outcome == "held_unaffordable":
        await conn.execute(text("UPDATE accounts SET cash=0 WHERE user_id=:user_id"), ids)
    result = await process(conn, revised)
    assert result.outcome == outcome
    assert await process(conn, revised) == result
    page = await page_for(conn, ids["user_id"], limit=1)
    item = page.items[0]
    assert item.outcome == outcome and item.original == saved
    assert item.payment_reference == f"dividend:{original.payment_id}"
    assert item.terms is not None and Decimal(item.terms.rate) == Decimal(rate)
    assert Decimal(item.applied_delta) == (Decimal(".5") if outcome == "applied" else Decimal(0))


@pytest.mark.parametrize("limit", [0, 101, True, "1", 1.0])
async def test_owner_and_page_bounds_before_any_query(db, engine, limit):
    statements = []

    def capture(*args):
        statements.append(args[2])

    sql_event.listen(engine.sync_engine, "before_cursor_execute", capture)
    try:
        with pytest.raises(ValueError):
            await list_event_history(db, user_id=1, limit=limit)
        assert statements == []
    finally:
        sql_event.remove(engine.sync_engine, "before_cursor_execute", capture)


@pytest.mark.parametrize("owner", [0, -1, True, "1", 9223372036854775808])
async def test_invalid_owner_rejected(db, owner):
    with pytest.raises(ValueError):
        await list_event_history(db, user_id=owner)


async def test_owner_missing_stock_receipt_refuses_incomplete_uncommitted_facts(authority_case):
    conn, ids = authority_case
    stamp = (await conn.execute(text("SELECT clock_timestamp()"))).scalar_one()
    await fill(conn, ids["user_id"], stamp, cid=ids["coin_id"])
    with pytest.raises(ValueError, match="Missing immutable stock fill facts"):
        await page_for(conn, ids["user_id"])
    # Uncommitted incomplete fixture is rolled back, never granted persistence.


async def test_mixed_all_kinds_tied_and_colliding_ids_are_distinct(dividend_case):
    """Read-only retained-record fixture; no successful cash execution is simulated."""
    from tests.test_dividend_schema import decision, payment

    conn, ids = dividend_case
    # All four sources share a tick; trade and payment also collide on ID.
    # Explicit trade identity is test-owner-only and does not change its sequence.
    stamp = (await conn.execute(text("SELECT now()"))).scalar_one()
    pid = await payment(conn, ids)
    shared = pid
    await conn.execute(
        text("""INSERT INTO trades
      (id,user_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
       exec_price,fee,cash_delta,cash_after,idempotency_key,created_at)
      OVERRIDING SYSTEM VALUE SELECT :id,:u,id,'buy','quantity',1,1,10,:t,10,0,-10,90,
      gen_random_uuid(),:t FROM coins WHERE symbol='BTC'"""),
        {"id": shared, "u": ids["user_id"], "t": stamp},
    )
    sid = await split_row(conn, ids, stamp)
    # A verified no-change checkpoint has no monetary effect. It is a retained
    # projection fixture, distinct from the real apply/hold tests above.
    did = await decision(
        conn,
        ids,
        pid,
        recorded_at=stamp,
        cutoff=stamp,
        rate=Decimal(".5"),
        desired_total=Decimal(1),
        cumulative_applied_before=Decimal(1),
        proposed_delta=Decimal(0),
        applied_delta=Decimal(0),
        outcome="verified_no_change",
        reason="target_unchanged",
    )
    page = await page_for(conn, ids["user_id"])
    assert [i.id for i in page.items] == [
        f"trade:{shared}",
        f"dividend:{pid}",
        f"split:{sid}",
        f"dividend_correction:{did}",
    ]
    for rank, identifier, remaining in [(4, shared, 3), (3, pid, 2), (2, sid, 1), (1, did, 0)]:
        result = await page_for(
            conn, ids["user_id"], cursor=encode_cursor(EventHistoryCursor(stamp, rank, identifier))
        )
        assert len(result.items) == remaining
