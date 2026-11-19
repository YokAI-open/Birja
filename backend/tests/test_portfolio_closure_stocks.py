"""Real same-transaction closure proof; no public API/admission substitution."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_portfolio_closure_authority import authority, stock_authority

__all__ = ["authority", "stock_authority"]


async def proof_grants(admin):
    # Plan04 owns runtime admission; this is explicit disposable service proof.
    async with admin.begin() as conn:
        await conn.execute(
            text(
                "GRANT SELECT ON portfolio_lifecycle_closures,portfolio_closure_intents "
                "TO birja_app"
            )
        )


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
        assert (
            await conn.execute(
                text("SELECT count(*) FROM portfolio_stock_closures WHERE portfolio_id=:p"),
                {"p": portfolio},
            )
        ).scalar_one() == 2


@pytest.mark.parametrize("instrument", ["first", "second"])
async def test_corrupt_one_of_multiple_histories_rolls_back_all_new_evidence(
    stock_authority, instrument
):
    from app.services.portfolio_closure import ClosureIntent, close_portfolio
    from app.services.stock_ownership import OwnershipHeld

    app, migrator, admin, books = stock_authority
    await proof_grants(admin)
    user, portfolio = books["roots"][0]
    async with migrator.begin() as conn:
        if instrument == "first":
            await conn.execute(text("ALTER TABLE trades DISABLE TRIGGER USER"))
            await conn.execute(
                text("UPDATE trades SET quantity=quantity-1 WHERE id=(SELECT min(id) FROM trades)")
            )
            await conn.execute(text("ALTER TABLE trades ENABLE TRIGGER USER"))
        else:
            # Preserve valid tail/holding arithmetic so SQL's derived boundary
            # passes; ONLY the full second-instrument baseline proof catches it.
            await conn.execute(text("ALTER TABLE stock_ownership_movements DISABLE TRIGGER USER"))
            await conn.execute(
                text("""UPDATE stock_ownership_movements m
                SET economic_at=s.journal_start_at-interval '1 second'
                FROM stock_action_state s WHERE s.coin_id=m.coin_id AND m.coin_id=:c"""),
                {"c": books["stocks"][1]},
            )
            await conn.execute(text("ALTER TABLE stock_ownership_movements ENABLE TRIGGER USER"))
    async with AsyncSession(app) as db:
        with pytest.raises(OwnershipHeld, match="fill_mismatch|history_gap"):
            await close_portfolio(db, ClosureIntent(user, portfolio, uuid4(), "Strategy"))
        assert not db.in_transaction()
    async with admin.connect() as conn:
        assert (
            await conn.execute(text("SELECT closed_at FROM accounts WHERE id=:p"), {"p": portfolio})
        ).scalar_one() is None
        assert (
            await conn.execute(
                text("SELECT count(*) FROM portfolio_lifecycle_closures WHERE portfolio_id=:p"),
                {"p": portfolio},
            )
        ).scalar_one() == 0
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))
        ).scalar_one() == 0


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


async def test_corrupt_closed_replay_is_never_acknowledged(stock_authority):
    from app.services.portfolio_closure import ClosureIntent, close_portfolio
    from app.services.stock_ownership import OwnershipHeld

    app, migrator, admin, books = stock_authority
    await proof_grants(admin)
    user, portfolio = books["roots"][0]
    original = ClosureIntent(user, portfolio, uuid4(), "Strategy")
    async with AsyncSession(app) as db:
        await close_portfolio(db, original)
    async with migrator.begin() as conn:
        await conn.execute(text("ALTER TABLE trades DISABLE TRIGGER USER"))
        await conn.execute(
            text("UPDATE trades SET quantity=quantity-1 WHERE id=(SELECT min(id) FROM trades)")
        )
        await conn.execute(text("ALTER TABLE trades ENABLE TRIGGER USER"))
    async with AsyncSession(app) as db:
        with pytest.raises(OwnershipHeld, match="fill_mismatch"):
            await close_portfolio(db, original)
        with pytest.raises(OwnershipHeld, match="fill_mismatch"):
            await close_portfolio(db, ClosureIntent(user, portfolio, uuid4(), "Different name"))


async def test_multi_empty_proof_and_durable_refusal_commit(authority):
    from app.services.portfolio_closure import ClosureIntent, close_portfolio
    from tests.test_portfolio_closure_migrations import root

    app, migrator, admin = authority
    await proof_grants(admin)
    async with migrator.begin() as conn:
        user, portfolio = await root(conn)
    wrong = ClosureIntent(user, portfolio, uuid4(), "Wrong reviewed name")
    async with AsyncSession(app) as db:
        assert (await close_portfolio(db, wrong)).outcome == "confirmation_changed"
        assert not db.in_transaction()
        assert (await close_portfolio(db, wrong)).replayed is True
        assert (
            await close_portfolio(db, ClosureIntent(user, portfolio, uuid4(), "Strategy"))
        ).outcome == "closed"
    async with admin.connect() as conn:
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))
        ).scalar_one() == 2


async def test_guard_context_is_revoked_after_commit_and_cannot_cross_transactions(
    stock_authority, monkeypatch
):
    from app.services import portfolio_closure as service
    from app.services.stock_ownership import OwnershipHeld, assert_closure_ownership_consistent

    app, _, admin, books = stock_authority
    await proof_grants(admin)
    captured = []
    real = service.assert_closure_ownership_consistent

    async def capture(db):
        captured.append(db.info["portfolio_closure_proof"])
        await real(db)

    monkeypatch.setattr(service, "assert_closure_ownership_consistent", capture)
    user, portfolio = books["roots"][0]
    async with AsyncSession(app) as db:
        await service.close_portfolio(
            db, service.ClosureIntent(user, portfolio, uuid4(), "Strategy")
        )
        assert "portfolio_closure_proof" not in db.info
        # This instrumentation copies only private in-memory state, not DB proof.
        db.info["portfolio_closure_proof"] = captured[0]
        await db.execute(text("SELECT 1"))
        with pytest.raises(OwnershipHeld, match="invalid_closure"):
            await assert_closure_ownership_consistent(db)
        db.info.pop("portfolio_closure_proof")
        await db.rollback()


async def test_multi_service_retries_actual_first_buy_after_root_wait(authority):
    from app.services.portfolio_closure import ClosureIntent, close_portfolio
    from tests.test_portfolio_closure_migrations import root

    app, migrator, admin = authority
    await proof_grants(admin)
    async with migrator.begin() as conn:
        user, portfolio = await root(conn)
        coin = (await conn.execute(text("SELECT min(coin_id) FROM stock_instruments"))).scalar_one()
        await conn.execute(
            text("""INSERT INTO stock_action_state
            (coin_id,admission_generation,journal_start_at,complete_from)
            VALUES (:c,1,clock_timestamp()-interval '2 days',
                    clock_timestamp()-interval '1 day')"""),
            {"c": coin},
        )
    calls = []

    def observe(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("SELECT * FROM public.close_portfolio"):
            calls.append(statement)

    event.listen(app.sync_engine, "before_cursor_execute", observe)
    try:
        async with migrator.connect() as writer, AsyncSession(app) as db:
            await writer.execute(
                text(
                    "SELECT pg_advisory_xact_lock(hashtextextended("
                    "'birja.stock.instrument:' || CAST(:c AS text),0))"
                ),
                {"c": str(coin)},
            )
            await writer.execute(
                text("SELECT id FROM accounts WHERE id=:p FOR UPDATE"), {"p": portfolio}
            )
            pid = (await db.execute(text("SELECT pg_backend_pid()"))).scalar_one()
            task = asyncio.create_task(
                close_portfolio(db, ClosureIntent(user, portfolio, uuid4(), "Strategy"))
            )
            try:
                async with asyncio.timeout(1.5):
                    while True:
                        async with admin.connect() as observer:
                            waiting = (
                                await observer.execute(
                                    text(
                                        "SELECT wait_event_type='Lock' AND "
                                        "cardinality(pg_blocking_pids(pid))>0 "
                                        "FROM pg_stat_activity WHERE pid=:p"
                                    ),
                                    {"p": pid},
                                )
                            ).scalar_one()
                        if waiting:
                            break
                        await asyncio.sleep(0)
                # Declared synthetic first ownership; actual API trading is Plan09.
                await writer.execute(
                    text(
                        "INSERT INTO holdings(user_id,portfolio_id,coin_id,quantity,cost_basis) "
                        "VALUES (:u,:p,:c,1,10)"
                    ),
                    {"u": user, "p": portfolio, "c": coin},
                )
                await writer.execute(
                    text("""INSERT INTO stock_ownership_movements
                    (user_id,portfolio_id,coin_id,sequence,economic_at,recorded_at,quantity,
                    before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,causal_key)
                    SELECT :u,:p,:c,1,t,t,1,0,1,0,10,0,'opening','opening:race'
                    FROM (SELECT clock_timestamp() AS t) stamp"""),
                    {"u": user, "p": portfolio, "c": coin},
                )
                await writer.commit()
                assert (await task).outcome == "closed"
                assert len(calls) == 2
            finally:
                if not task.done():
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
                await writer.rollback()
                await db.rollback()
    finally:
        event.remove(app.sync_engine, "before_cursor_execute", observe)
