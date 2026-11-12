"""Real PostgreSQL dividend identities, saved terms and append-only lineage."""

from collections.abc import AsyncIterator
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from tests.test_stock_action_migrations import event, ledger

__all__ = ["ledger"]


async def test_anchor_schema_exists(engine: AsyncEngine, migrated: None) -> None:
    async with engine.connect() as conn:
        tables = set(
            (
                await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
                )
            ).scalars()
        )
        assert tables >= {"stock_dividend_payments", "stock_dividend_decisions"}, (
            "Dividend originals and decisions need durable constrained relations"
        )


@pytest_asyncio.fixture
async def dividend_case(ledger) -> AsyncIterator[tuple[AsyncConnection, dict[str, object]]]:
    conn, cid, uid = ledger
    eid, _, rid = await event(conn, cid)
    entitlement = (
        await conn.execute(
            text("""INSERT INTO stock_dividend_entitlements
        (event_id,user_id,revision_id,cutoff,cutoff_rule,version,units_basis,unit_epoch,
         last_movement_sequence,eligible_quantity,state,fingerprint)
        VALUES (:e,:u,:r,now(),'exclusive',1,'shares',0,0,2,'eligible',:f) RETURNING id"""),
            {"e": eid, "u": uid, "r": rid, "f": "b" * 64},
        )
    ).scalar_one()
    yield (
        conn,
        {
            "event_id": eid,
            "coin_id": cid,
            "user_id": uid,
            "revision_id": rid,
            "revision_fingerprint": "a" * 64,
            "entitlement_id": entitlement,
            "entitlement_fingerprint": "b" * 64,
        },
    )


async def payment(conn: AsyncConnection, terms: dict[str, object], **changes: object) -> int:
    values = {**terms, "original_amount": Decimal("1.00"), **changes}
    return (
        await conn.execute(
            text("""INSERT INTO stock_dividend_payments
      (event_id,coin_id,user_id,revision_id,revision_fingerprint,entitlement_id,
       entitlement_fingerprint,symbol,company_name,cutoff,cutoff_rule,units_basis,
       unit_epoch,eligible_quantity,rate,ex_date,record_date,payable_date,
       original_amount,recorded_at,cash_after)
      VALUES (:event_id,:coin_id,:user_id,:revision_id,:revision_fingerprint,:entitlement_id,
       :entitlement_fingerprint,'AAPL','Saved Apple',now(),'exclusive','shares',0,2,0.5,
       DATE '2026-11-01',DATE '2026-11-02',DATE '2026-11-10',:original_amount,now(),10001)
      RETURNING id"""),
            values,
        )
    ).scalar_one()


async def test_zero_target_anchor(dividend_case) -> None:
    conn, terms = dividend_case
    pid = await payment(conn, terms, original_amount=Decimal("0.00"))
    assert (
        await conn.execute(
            text("SELECT original_amount FROM stock_dividend_payments WHERE id=:p"), {"p": pid}
        )
    ).scalar_one() == Decimal(0)
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await payment(conn, terms)
    assert error.value.orig.sqlstate == "23505"


@pytest.mark.parametrize(
    "field",
    [
        "user_id",
        "event_id",
        "revision_id",
        "entitlement_id",
        "revision_fingerprint",
        "entitlement_fingerprint",
    ],
)
async def test_anchor_cross_links_rejected(dividend_case, field: str) -> None:
    conn, terms = dividend_case
    changes = {field: "c" * 64 if field.endswith("fingerprint") else 9223372036854775807}
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await payment(conn, terms, **changes)
    assert error.value.orig.sqlstate == "23503"


@pytest.mark.parametrize("amount", ["-0.01", "NaN", "Infinity", "1000000000000", "0.001"])
async def test_anchor_amount_finite_nonnegative_cents(dividend_case, amount: str) -> None:
    conn, terms = dividend_case
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await payment(conn, terms, original_amount=Decimal(amount))
    assert error.value.orig.sqlstate in {"23514", "22003"}


@pytest.mark.parametrize(
    "operation",
    ["UPDATE stock_dividend_payments SET symbol='CHANGED'", "DELETE FROM stock_dividend_payments"],
)
async def test_anchor_immutable_even_owner(dividend_case, operation: str) -> None:
    conn, terms = dividend_case
    pid = await payment(conn, terms)
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await conn.execute(text(f"{operation} WHERE id=:p"), {"p": pid})
    assert error.value.orig.sqlstate == "23514"
