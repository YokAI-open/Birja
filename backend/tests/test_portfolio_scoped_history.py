"""Real financial reads and strict cursors cannot retarget an owned portfolio."""

import base64
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from app.services import event_history as mixed
from app.services import history as trades
from app.services.portfolios import OwnedActivePortfolio
from tests.portfolio_fixtures import portfolio_migration_db
from tests.stock_trade_fixtures import ownership, status_case, stock_trade_case
from tests.test_portfolio_dividends import dividend_books, pay, revise
from tests.test_portfolio_splits import record_split, split_case
from tests.test_portfolio_stock_authority import stock_authority_case
from tests.test_portfolio_stock_ownership import journal_case
from tests.test_portfolio_stock_trading import execute, stock_books

__all__ = [
    "portfolio_migration_db",
    "dividend_books",
    "stock_books",
    "ownership",
    "status_case",
    "stock_trade_case",
    "split_case",
    "journal_case",
    "stock_authority_case",
]


def wire(obj):
    return (
        base64.urlsafe_b64encode(json.dumps(obj, separators=(",", ":")).encode())
        .decode()
        .rstrip("=")
    )


@pytest.mark.parametrize("module", [trades, mixed])
def test_canonical_cursor_binds_expected_root(module):
    now = datetime(2026, 11, 16, tzinfo=UTC)
    cursor = (
        trades.HistoryCursor(now, 99, 71)
        if module is trades
        else mixed.EventHistoryCursor(now, 4, 99, 71)
    )
    value = module.encode_cursor(cursor)
    assert module.decode_cursor(value, expected_portfolio_id=71) == cursor
    with pytest.raises(module.InvalidCursor):
        module.decode_cursor(value, expected_portfolio_id=72)
    raw = json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)))
    assert raw["v"] == (2 if module is trades else 3) and raw["portfolio_id"] == "71"


@pytest.mark.parametrize("module", [trades, mixed])
@pytest.mark.parametrize(
    "mutation", ["old", "missing", "bool", "zero", "overflow", "extra", "numeric"]
)
def test_old_malformed_or_tampered_cursor_refused(module, mutation):
    obj = (
        {"v": 2, "created_at": "2026-11-16T00:00:00.000000Z", "id": "99"}
        if module is trades
        else {
            "v": 3,
            "recorded_at": "2026-11-16T00:00:00.000000Z",
            "kind_rank": 4,
            "source_id": "99",
        }
    )
    obj["portfolio_id"] = "71"
    if mutation == "old":
        obj["v"] -= 1
    elif mutation == "missing":
        del obj["portfolio_id"]
    elif mutation == "bool":
        obj["portfolio_id"] = True
    elif mutation == "zero":
        obj["portfolio_id"] = "0"
    elif mutation == "overflow":
        obj["portfolio_id"] = "9223372036854775808"
    elif mutation == "extra":
        obj["owner"] = "17"
    else:
        obj["portfolio_id"] = 71
    with pytest.raises(module.InvalidCursor):
        module.decode_cursor(wire(obj), expected_portfolio_id=71)


async def read(factory, target, *, module=mixed, **kw):
    async with factory() as db:
        function = module.list_history if module is trades else module.list_event_history
        return await function(
            db, portfolio=OwnedActivePortfolio(target["portfolio_id"], target["user_id"]), **kw
        )


async def crypto_fill(factory, target, stamp):
    async with factory.begin() as db:
        return await db.scalar(
            text("""INSERT INTO trades(portfolio_id,user_id,coin_id,
          side,input_kind,input_value,quantity,mid_price,price_as_of,exec_price,fee,
          cash_delta,cash_after,idempotency_key,created_at)
          SELECT :p,:u,id,'buy','quantity',1,1,10,:t,10,0,-10,90,:k,:t
          FROM coins WHERE symbol='BTC' RETURNING id"""),
            {"p": target["portfolio_id"], "u": target["user_id"], "t": stamp, "k": uuid4()},
        )


@pytest.mark.parametrize("module", [trades, mixed])
async def test_tied_trade_pagination_cross_root_cursor_and_append(dividend_books, module):
    _, factory, targets = dividend_books
    stamp = datetime.now(UTC) - timedelta(minutes=1)
    own = [await crypto_fill(factory, targets[0], stamp) for _ in range(4)]
    sibling = await crypto_fill(factory, targets[1], stamp)
    foreign = await crypto_fill(factory, targets[2], stamp)
    page = await read(factory, targets[0], module=module, limit=2)

    def ident(tid):
        return str(tid) if module is trades else f"trade:{tid}"

    assert [i.id for i in page.items] == list(map(ident, reversed(own[2:])))
    assert page.next_cursor
    with pytest.raises(module.InvalidCursor):
        await read(factory, targets[1], module=module, cursor=page.next_cursor)
    newer = await crypto_fill(factory, targets[0], stamp + timedelta(seconds=1))
    tail = await read(factory, targets[0], module=module, cursor=page.next_cursor, limit=2)
    assert [i.id for i in tail.items] == list(map(ident, reversed(own[:2])))
    assert tail.next_cursor is None
    assert (await read(factory, targets[0], module=module, limit=1)).items[0].id == ident(newer)
    assert (await read(factory, targets[1], module=module)).items[0].id == ident(sibling)
    assert (await read(factory, targets[2], module=module)).items[0].id == ident(foreign)


@pytest.mark.parametrize("module", [trades, mixed])
@pytest.mark.parametrize("target", ["closed", "foreign", "missing"])
async def test_private_unavailable_target_no_financial_rows(dividend_books, module, target):
    _, factory, targets = dividend_books
    bad = dict(targets[0])
    if target == "closed":
        async with factory.begin() as db:
            await db.execute(
                text("UPDATE accounts SET closed_at=clock_timestamp() WHERE id=:p"),
                {"p": bad["portfolio_id"]},
            )
    elif target == "foreign":
        bad["portfolio_id"] = targets[2]["portfolio_id"]
    else:
        bad["portfolio_id"] = 9223372036854775807
    with pytest.raises(HTTPException) as exc:
        await read(factory, bad, module=module)
    assert exc.value.status_code == 404 and exc.value.detail == {"code": "portfolio_unavailable"}


async def test_correction_hydrates_only_its_owned_original_off_page(dividend_books):
    engine, factory, targets = dividend_books
    original = await pay(engine, targets[0])
    sibling = await pay(engine, targets[1])
    changed = await revise(factory, targets[0], rate=".75")
    corrected = await pay(engine, changed)
    page = await read(factory, targets[0], limit=1)
    item = page.items[0]
    assert item.kind == "dividend_correction" and item.cash_delta == "0.50000000"
    assert item.original.id == f"dividend:{original.payment_id}"
    assert item.original.id != f"dividend:{sibling.payment_id}"
    assert item.original.credited_amount == "1.00000000"
    assert page.next_cursor
    tail = await read(factory, targets[0], cursor=page.next_cursor)
    assert [i.id for i in tail.items] == [item.original.id]
    assert corrected.payment_id == original.payment_id


async def test_held_correction_remains_zero_cash_with_private_original(dividend_books):
    engine, factory, targets = dividend_books
    original = await pay(engine, targets[0])
    changed = await revise(factory, targets[0], rate=".1")
    async with factory.begin() as db:
        await db.execute(
            text("UPDATE accounts SET cash=.79 WHERE id=:p"), {"p": targets[0]["portfolio_id"]}
        )
    await pay(engine, changed)
    item = (await read(factory, targets[0], limit=1)).items[0]
    assert item.outcome == "held_unaffordable" and Decimal(item.cash_delta) == 0
    assert item.original.id == f"dividend:{original.payment_id}"
    assert (await read(factory, targets[1])).items == []


async def test_stock_hydration_uses_root_paired_immutable_facts(stock_books, settings):
    factory, cid, (root, sibling, *_), _ = stock_books
    receipt, _ = await execute(factory, root, settings)
    async with factory() as db:
        page = await mixed.list_event_history(db, portfolio=root)
        assert (await mixed.list_event_history(db, portfolio=sibling)).items == []
    item = page.items[0]
    assert item.id == f"trade:{receipt.trade_id}" and item.asset_type == "stock"
    assert item.feed == "iex" and Decimal(item.fee) == 0 and item.symbol == "AAPL"
    async with factory.begin() as db:
        await db.execute(text("UPDATE coins SET name='Renamed catalog' WHERE id=:c"), {"c": cid})
    async with factory() as db:
        assert (await mixed.list_event_history(db, portfolio=root)).items == page.items


async def test_global_split_hydrates_distinct_owned_movements(split_case):
    db, _, case, action, evidence = split_case
    applications = await record_split(db, case, action, evidence)
    first = OwnedActivePortfolio(case["first"], case["owner"])
    sibling = OwnedActivePortfolio(case["sibling"], case["owner"])
    left = await mixed.list_event_history(db, portfolio=first)
    right = await mixed.list_event_history(db, portfolio=sibling)
    assert len(left.items) == len(right.items) == len(applications) == 1
    a, b = left.items[0], right.items[0]
    assert a.kind == b.kind == "split" and a.id != b.id
    assert (a.quantity_before, a.quantity_after) == ("2.00000000", "4.00000000")
    assert a.cost_basis_before == a.cost_basis_after == b.cost_basis_after
    assert a.cash_delta == b.cash_delta == "0"


async def test_missing_stock_original_refuses_incomplete_projection(stock_authority_case):
    conn, case = stock_authority_case
    from sqlalchemy.ext.asyncio import AsyncSession

    await conn.execute(
        text("""INSERT INTO trades(portfolio_id,user_id,coin_id,side,
      input_kind,input_value,quantity,mid_price,price_as_of,exec_price,fee,cash_delta,
      cash_after,idempotency_key,created_at)
      VALUES (:p,:u,:c,'buy','quantity',1,1,10,:t,10,0,-10,90,:k,:t)"""),
        {"p": case["first"], "u": case["owner"], "c": case["coin"], "t": case["now"], "k": uuid4()},
    )
    async with AsyncSession(bind=conn, join_transaction_mode="create_savepoint") as db:
        with pytest.raises(ValueError, match="Missing immutable stock fill facts"):
            await mixed.list_event_history(
                db, portfolio=OwnedActivePortfolio(case["first"], case["owner"])
            )


async def test_mixed_kind_tie_uses_complete_tuple_without_duplicate_or_omission(dividend_books):
    engine, factory, targets = dividend_books
    payment = await pay(engine, targets[0])
    async with factory() as db:
        stamp = await db.scalar(
            text("SELECT recorded_at FROM stock_dividend_payments WHERE id=:i"),
            {"i": payment.payment_id},
        )
    tid = await crypto_fill(factory, targets[0], stamp)
    await crypto_fill(factory, targets[1], stamp)
    first = await read(factory, targets[0], limit=1)
    assert [i.id for i in first.items] == [f"trade:{tid}"]
    tail = await read(factory, targets[0], limit=1, cursor=first.next_cursor)
    assert [i.id for i in tail.items] == [f"dividend:{payment.payment_id}"]
    assert tail.next_cursor is None


@pytest.mark.parametrize("module", [trades, mixed])
@pytest.mark.parametrize("limit", [0, 101, True, "1", None])
async def test_limit_rejected_before_any_query(module, limit):
    function = module.list_history if module is trades else module.list_event_history
    with pytest.raises(ValueError, match="limit"):
        await function(None, portfolio=OwnedActivePortfolio(1, 1), limit=limit)


@pytest.mark.parametrize("module", [trades, mixed])
async def test_cursor_root_checked_before_any_query(module):
    stamp = datetime.now(UTC)
    value = module.encode_cursor(
        trades.HistoryCursor(stamp, 1, 1)
        if module is trades
        else mixed.EventHistoryCursor(stamp, 4, 1, 1)
    )
    function = module.list_history if module is trades else module.list_event_history
    with pytest.raises(module.InvalidCursor):
        await function(None, portfolio=OwnedActivePortfolio(2, 1), cursor=value)


async def test_actual_restricted_app_can_read_only_requested_financial_history(dividend_books):
    from sqlalchemy.ext.asyncio import AsyncSession

    engine, _, targets = dividend_books
    original = await pay(engine, targets[0])
    await pay(engine, targets[1])
    async with engine.connect() as conn:
        await conn.execute(text("SET ROLE birja_app"))
        await conn.commit()
        try:
            async with AsyncSession(bind=conn) as db:
                page = await mixed.list_event_history(
                    db,
                    portfolio=OwnedActivePortfolio(
                        targets[0]["portfolio_id"], targets[0]["user_id"]
                    ),
                )
                assert [i.id for i in page.items] == [f"dividend:{original.payment_id}"]
        finally:
            await conn.rollback()
            await conn.execute(text("RESET ROLE"))
            await conn.commit()
