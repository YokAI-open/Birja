"""Real same-transaction closure proof; no public API/admission substitution."""

from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_portfolio_closure_authority import authority, stock_authority  # noqa: F401


async def proof_grants(admin):
    # Plan04 owns runtime admission; this is explicit disposable service proof.
    async with admin.begin() as conn:
        await conn.execute(text("GRANT SELECT ON portfolio_lifecycle_closures,portfolio_closure_intents TO birja_app"))


async def test_multi_stock_complete_service_commits_original_and_closed_replay(stock_authority):
    from app.services.portfolio_closure import ClosureIntent, close_portfolio

    app, _, admin, books = stock_authority
    await proof_grants(admin)
    user, portfolio = books["roots"][0]
    original = ClosureIntent(user, portfolio, uuid4(), "Strategy")
    async with AsyncSession(app) as db:
        assert (await close_portfolio(db, original)).outcome == "closed"
        assert not db.in_transaction()
        assert (await close_portfolio(db, original)).replayed is True
    async with admin.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM portfolio_stock_closures WHERE portfolio_id=:p"), {"p": portfolio})).scalar_one() == 2


async def test_corrupt_one_of_multiple_histories_rolls_back_all_new_evidence(stock_authority):
    from app.services.portfolio_closure import ClosureIntent, close_portfolio
    from app.services.stock_ownership import OwnershipHeld

    app, migrator, admin, books = stock_authority
    await proof_grants(admin)
    user, portfolio = books["roots"][0]
    async with migrator.begin() as conn:
        await conn.execute(text("ALTER TABLE trades DISABLE TRIGGER USER"))
        await conn.execute(text("UPDATE trades SET cash_delta=cash_delta-1 WHERE id=(SELECT min(id) FROM trades)"))
        await conn.execute(text("ALTER TABLE trades ENABLE TRIGGER USER"))
    async with AsyncSession(app) as db:
        with pytest.raises(OwnershipHeld, match="fill_mismatch"):
            await close_portfolio(db, ClosureIntent(user, portfolio, uuid4(), "Strategy"))
        assert not db.in_transaction()
    async with admin.connect() as conn:
        assert (await conn.execute(text("SELECT closed_at FROM accounts WHERE id=:p"), {"p": portfolio})).scalar_one() is None
        assert (await conn.execute(text("SELECT count(*) FROM portfolio_lifecycle_closures WHERE portfolio_id=:p"), {"p": portfolio})).scalar_one() == 0
        assert (await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))).scalar_one() == 0


async def test_guard_still_rejects_second_financial_instrument(stock_authority):
    from app.services.stock_ownership import OwnershipHeld, assert_ownership_consistent

    app, _, _, books = stock_authority
    async with AsyncSession(app) as db:
        await assert_ownership_consistent(db, books["stocks"][0])
        with pytest.raises(OwnershipHeld, match="one_instrument_per_transaction"):
            await assert_ownership_consistent(db, books["stocks"][1])
        await db.rollback()


async def test_guard_closure_proof_cannot_be_called_without_current_service_context(authority):
    from app.services.stock_ownership import OwnershipHeld, assert_closure_ownership_consistent

    app, _, _ = authority
    async with AsyncSession(app) as db:
        with pytest.raises(OwnershipHeld, match="invalid_closure"):
            await assert_closure_ownership_consistent(db)
        await db.rollback()
