"""Actual retained entitlement payments through the application transaction owner."""

from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import dividends
from tests.test_dividend_authority import authority_case
from tests.test_dividend_schema import dividend_case
from tests.test_stock_action_migrations import ledger

__all__ = ["authority_case", "dividend_case", "ledger"]


async def process(conn, ids, **changes):
    work = {
        "event_id": ids["event_id"],
        "entitlement_id": ids["entitlement_id"],
        "expected_revision_fingerprint": ids["revision_fingerprint"],
        "expected_entitlement_fingerprint": ids["entitlement_fingerprint"],
        **changes,
    }
    await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
    try:
        async with AsyncSession(bind=conn, join_transaction_mode="create_savepoint") as db:
            return await dividends.process_dividend(db, **work)
    finally:
        await conn.execute(text("RESET ROLE"))


async def cash(conn, ids):
    return (
        await conn.execute(text("SELECT cash FROM accounts WHERE user_id=:user_id"), ids)
    ).scalar_one()


async def test_due_original_retained_payment_once(authority_case):
    conn, ids = authority_case
    result = await process(conn, ids)
    assert await cash(conn, ids) == Decimal("101"), "A due retained dividend credits cash"
    assert result.outcome == "original" and result.decision_id is None
    assert await process(conn, ids) == result
    assert await cash(conn, ids) == Decimal("101")
    assert (
        await conn.execute(text("SELECT starting_cash FROM accounts WHERE user_id=:user_id"), ids)
    ).scalar_one() == Decimal("10000")
    assert (await conn.execute(text("SELECT count(*) FROM stock_dividend_payments"))).scalar_one() == 1


async def test_original_replay_after_rights_loss_and_symbol_rename(authority_case):
    conn, ids = authority_case
    result = await process(conn, ids)
    original = (await conn.execute(text("SELECT row_to_json(p) FROM stock_dividend_payments p"))).scalar_one()
    await conn.execute(text("UPDATE stock_data_admissions SET state='denied'"))
    await conn.execute(text("UPDATE coins SET symbol='RENAMED',name='Renamed' WHERE id=:coin_id"), ids)
    await conn.execute(text("UPDATE stock_action_state SET health='held',epoch=epoch+1"))
    assert await process(conn, ids) == result
    assert (await conn.execute(text("SELECT row_to_json(p) FROM stock_dividend_payments p"))).scalar_one() == original
    assert await cash(conn, ids) == Decimal("101")
