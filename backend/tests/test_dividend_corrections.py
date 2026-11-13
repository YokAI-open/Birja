"""Immutable corrections and no-cash holds via actual SQL financial effects."""

from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import dividends
from tests.test_dividend_authority import authority_case, successor
from tests.test_dividend_payments import cash, process
from tests.test_dividend_schema import dividend_case
from tests.test_stock_action_migrations import ledger

__all__ = ["authority_case", "dividend_case", "ledger"]


async def hold(conn, payment_id, fingerprint):
    await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
    try:
        async with AsyncSession(bind=conn, join_transaction_mode="create_savepoint") as db:
            return await dividends.record_dividend_hold(
                db, payment_id=payment_id, expected_revision_fingerprint=fingerprint
            )
    finally:
        await conn.execute(text("RESET ROLE"))


@pytest.mark.parametrize("classification", ["uncertain", "cancelled"])
async def test_correction_unknown_after_original_deduplicates_without_reversal(
    authority_case, classification
):
    conn, ids = authority_case
    original = await process(conn, ids)
    revised = await successor(conn, ids, classification=classification, eligible=False)
    result = await hold(conn, original.payment_id, revised["revision_fingerprint"])
    assert result.outcome == "held_uncertain" and result.decision_id is not None
    assert await hold(conn, original.payment_id, revised["revision_fingerprint"]) == result
    assert await cash(conn, ids) == Decimal("101")
    row = (
        await conn.execute(
            text(
                "SELECT entitlement_id,desired_total,proposed_delta,applied_delta FROM stock_dividend_decisions"
            )
        )
    ).one()
    assert tuple(row) == (None, None, None, Decimal(0))


async def test_correction_a_b_a_and_nochange_original_immutable(authority_case):
    conn, ids = authority_case
    original = await process(conn, ids)
    saved = (
        await conn.execute(text("SELECT row_to_json(p) FROM stock_dividend_payments p"))
    ).scalar_one()
    b = await successor(conn, ids)
    first = await process(conn, b)
    a = await successor(conn, b, rate="0.5")
    second = await process(conn, a)
    unchanged = await successor(conn, a, rate="0.5")
    third = await process(conn, unchanged)
    assert [first.outcome, second.outcome, third.outcome] == [
        "applied",
        "applied",
        "verified_no_change",
    ]
    assert (
        await conn.execute(text("SELECT applied_delta FROM stock_dividend_decisions ORDER BY id"))
    ).scalars().all() == [Decimal(".5"), Decimal("-.5"), Decimal(0)]
    assert await process(conn, ids) == original
    assert await cash(conn, ids) == Decimal("101")
    assert (
        await conn.execute(text("SELECT row_to_json(p) FROM stock_dividend_payments p"))
    ).scalar_one() == saved
    await conn.execute(text("UPDATE stock_data_admissions SET state='denied'"))
    assert await process(conn, b) == first


async def test_correction_deficit_hold_can_apply_once_after_funding(authority_case):
    conn, ids = authority_case
    await process(conn, ids)
    revised = await successor(conn, ids, rate=".1")
    await conn.execute(text("UPDATE accounts SET cash=.79 WHERE user_id=:user_id"), ids)
    held = await process(conn, revised)
    assert held.outcome == "held_unaffordable"
    assert await process(conn, revised) == held
    assert await cash(conn, ids) == Decimal(".79")
    await conn.execute(text("UPDATE accounts SET cash=.80 WHERE user_id=:user_id"), ids)
    applied = await process(conn, revised)
    assert applied.outcome == "applied" and applied.decision_id != held.decision_id
    assert await process(conn, revised) == applied
    assert await cash(conn, ids) == Decimal(0)
    assert (
        await conn.execute(
            text("SELECT previous_decision_id FROM stock_dividend_decisions WHERE id=:id"),
            {"id": applied.decision_id},
        )
    ).scalar_one() == held.decision_id
