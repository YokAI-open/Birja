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
                "SELECT entitlement_id,desired_total,proposed_delta,applied_delta FROM "
                "stock_dividend_decisions"
            )
        )
    ).one()
    assert tuple(row) == (None, None, None, Decimal(0))
    corrected = await successor(conn, revised, rate=".75")
    # Synthetic reviewed external evidence; the existing SQL reconciliation guard remains real.
    await conn.execute(
        text(
            "INSERT INTO stock_action_resolutions(event_id,coin_id,expected_revision,"
            "admission_generation,epoch,decision,decision_key,evidence,evidence_hash,"
            "before_digest,after_digest,actor_ref,created_at) "
            "SELECT :event_id,:coin_id,:revision_id,4,3,'accept_corrected_supported_revision',"
            "'synthetic-service-reconciliation',"
            "jsonb_build_object('format',1,'held_revision_ids',(SELECT jsonb_agg(r.id ORDER BY "
            "r.id) FROM stock_action_revisions r WHERE r.event_id=:event_id)),"
            "repeat('a',64),repeat('b',64),repeat('c',64),'synthetic-reviewed-operator',"
            "clock_timestamp()"
        ),
        corrected,
    )
    applied = await process(conn, corrected)
    assert applied.outcome == "applied" and await process(conn, corrected) == applied
    assert await cash(conn, ids) == Decimal("101.5")
    assert (
        await conn.execute(
            text(
                "SELECT previous_decision_id,applied_delta FROM stock_dividend_decisions WHERE "
                "id=:id"
            ),
            {"id": applied.decision_id},
        )
    ).one() == (result.decision_id, Decimal(".5"))
    assert (
        await conn.execute(
            text("SELECT original_amount FROM stock_dividend_payments WHERE id=:id"),
            {"id": original.payment_id},
        )
    ).scalar_one() == Decimal(1)


@pytest.mark.parametrize("classification", ["uncertain", "cancelled"])
async def test_correction_before_original_cannot_fabricate_anchor_or_zero(
    authority_case, classification
):
    conn, ids = authority_case
    revised = await successor(conn, ids, classification=classification, eligible=False)
    with pytest.raises(dividends.DividendRefused) as error:
        await hold(conn, 9223372036854775807, revised["revision_fingerprint"])
    assert error.value.code == "authority_unavailable"
    with pytest.raises(dividends.DividendRefused):
        await process(conn, revised)
    assert await cash(conn, ids) == Decimal(100)
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_payments"))
    ).scalar_one() == 0
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_decisions"))
    ).scalar_one() == 0


async def test_correction_hold_requires_current_rights_and_uncertainty(authority_case):
    conn, ids = authority_case
    original = await process(conn, ids)
    with pytest.raises(dividends.DividendRefused):
        await hold(conn, original.payment_id, ids["revision_fingerprint"])
    revised = await successor(conn, ids, classification="uncertain", eligible=False)
    await conn.execute(text("UPDATE stock_data_admissions SET state='denied'"))
    with pytest.raises(dividends.DividendRefused):
        await hold(conn, original.payment_id, revised["revision_fingerprint"])
    assert await cash(conn, ids) == Decimal(101)
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_decisions"))
    ).scalar_one() == 0


@pytest.mark.parametrize(
    "payment,fingerprint", [(True, "a" * 64), (0, "a" * 64), (1, "a" * 65), (1, "X" * 64)]
)
async def test_correction_hold_validates_bounded_work_identity(
    authority_case, payment, fingerprint
):
    conn, ids = authority_case
    with pytest.raises(dividends.DividendRefused) as error:
        await hold(conn, payment, fingerprint)
    assert error.value.code == "invalid_identity"
    assert await cash(conn, ids) == Decimal(100)


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
