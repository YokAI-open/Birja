"""Real SQL owner-scoped mixed publication and immutable linked originals."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.event_history import list_event_history
from tests.test_dividend_authority import authority_case
from tests.test_dividend_payments import process
from tests.test_dividend_schema import dividend_case
from tests.test_stock_action_migrations import ledger

__all__ = ["authority_case", "dividend_case", "ledger"]


async def test_mixed_original_is_published_from_actual_cash_effect(authority_case):
    conn, ids = authority_case
    result = await process(conn, ids)
    async with AsyncSession(bind=conn) as db:
        page = await list_event_history(db, user_id=ids["user_id"])
    assert len(page.items) == 1, "Real dividend cash must publish its immutable History original"
    assert page.items[0].id == f"dividend:{result.payment_id}"
