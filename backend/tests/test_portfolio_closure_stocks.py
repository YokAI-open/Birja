"""Real same-transaction closure proof; no public API/admission substitution."""

import asyncio
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_portfolio_closure_authority import authority, stock_authority
from tests.test_portfolio_strategy_events import (
    closure_api,
    management_api,
    strategy_books,
    strategy_events,
)

__all__ = [
    "authority",
    "stock_authority",
    "closure_api",
    "management_api",
    "strategy_books",
    "strategy_events",
]


async def test_sold_out_multiple_stocks_successive_public_sibling_splits(strategy_events):
    from app.services import corporate_actions as actions
    from app.services.corporate_action_rules import CutoffEvidence
    from app.services.stock_ownership import assert_ownership_consistent, reconstruct_stock_quantity
    from tests.portfolio_closure_fixtures import (
        frozen_financial_snapshot,
        seed_public_stock_positions,
    )
    from tests.test_corporate_actions import batch, split_action
    from tests.test_portfolio_closure_api import create, delete, intent
    from tests.test_portfolio_strategy_lifecycle import ledger, scheduler, trade

    api, roots, cid, now, action, admission, event_id, engine = strategy_events
    foreign = (await create(api, "Independent", client=api.other)).json()["id"]
    zero = (await create(api, "Sold out")).json()["id"]
    async with api.migrator.connect() as conn:
        second = (
            await conn.execute(
                text("SELECT min(coin_id) FROM stock_instruments WHERE coin_id<>:c"), {"c": cid}
            )
        ).scalar_one()
    await seed_public_stock_positions(
        api,
        cid,
        now - timedelta(days=10),
        [
            (api.other_uid, foreign, 3, 30),
            (api.uid, zero, 1, 10),
        ],
    )
    await seed_public_stock_positions(
        api,
        second,
        now - timedelta(days=10),
        [
            (api.uid, roots[0], 3, 30),
            (api.uid, roots[1], 5, 50),
        ],
    )
    sold = await trade(api, roots[0], stock=True, side="sell", quantity="2")
    assert sold.status_code == 201, sold.text
    zero_sale = await trade(api, zero, stock=True, side="sell", quantity="1")
    assert zero_sale.status_code == 201, zero_sale.text
    async with api.migrator.connect() as conn:
        tails = dict(
            (
                await conn.execute(
                    text(
                        "SELECT coin_id,max(sequence) FROM stock_ownership_movements "
                        "GROUP BY coin_id"
                    )
                )
            ).all()
        )
    for root, name in ((roots[0], "Patient"), (zero, "Sold out")):
        response = await delete(api, root, intent(name))
        assert response.status_code == 200, response.text
    async with api.migrator.connect() as conn:
        frozen = await frozen_financial_snapshot(conn, int(roots[0]))
        frozen_zero = await frozen_financial_snapshot(conn, int(zero))
        closed_at = (
            await conn.execute(
                text("SELECT closed_at FROM accounts WHERE id=:p"), {"p": int(roots[0])}
            )
        ).scalar_one()
        assert (
            await conn.execute(
                text(
                    "SELECT coin_id,closing_sequence,unit_epoch FROM portfolio_stock_closures "
                    "WHERE portfolio_id=:p ORDER BY coin_id"
                ),
                {"p": int(roots[0])},
            )
        ).all() == [(c, tails[c], 0) for c in sorted((cid, second))]
        assert (
            await conn.execute(
                text(
                    "SELECT closing_sequence,unit_epoch FROM portfolio_stock_closures "
                    "WHERE portfolio_id=:p"
                ),
                {"p": int(zero)},
            )
        ).one() == (tails[cid], 0)
    previous = ()
    for expected in ((8, 6),):
        async with api.migrator.connect() as conn:
            split_at = (await conn.execute(text("SELECT clock_timestamp()"))).scalar_one()
        split = split_action(
            replace(
                action,
                provider_event_id=str(uuid4()),
                observed_at=split_at,
                payable_date=split_at.date(),
            ),
            split_at,
            new_rate=Decimal(2),
        )
        async with scheduler(engine) as db:
            await actions.persist_action_batch(db, batch(split), admission)
            applied = await actions.apply_due_actions(db, cid)
            assert len(applied) == len(previous) + 1
            await db.commit()
        async with scheduler(engine) as db:
            assert await actions.apply_due_actions(db, cid) == applied
            state, _ = await assert_ownership_consistent(db, cid)
            assert state.unit_epoch == len(applied)
            cutoff = CutoffEvidence(closed_at, "NASDAQ", closed_at.date(), 1, "declared-synthetic")
            frozen_quantity = await reconstruct_stock_quantity(db, int(roots[0]), cid, cutoff, 0)
            assert frozen_quantity.quantity == 0
            eligible = await actions.derive_dividend_entitlements(db, event_id)
            assert [(e.portfolio_id, e.eligible_quantity) for e in eligible] == [
                (int(roots[1]), Decimal(4)),
                (int(foreign), Decimal(3)),
            ]
            await db.commit()
        async with api.migrator.connect() as conn:
            assert await frozen_financial_snapshot(conn, int(roots[0])) == frozen
            assert await frozen_financial_snapshot(conn, int(zero)) == frozen_zero
            positions = (
                await conn.execute(
                    text(
                        "SELECT portfolio_id,quantity,cost_basis FROM holdings "
                        "WHERE coin_id=:c AND portfolio_id IN (:p,:f) ORDER BY portfolio_id"
                    ),
                    {"c": cid, "p": int(roots[1]), "f": int(foreign)},
                )
            ).all()
            assert positions == [
                (int(roots[1]), Decimal(expected[0]), Decimal(40)),
                (int(foreign), Decimal(expected[1]), Decimal(30)),
            ]
        previous = applied
    assert (await ledger(api, roots[0]))[0] == (Decimal(10200), Decimal(10000))


async def test_closed_market_stale_quote_and_uncertain_stock_do_not_block_deletion(strategy_events):
    from tests.test_portfolio_closure_api import delete, intent

    api, roots, cid, _, _, _, _, _ = strategy_events
    async with api.migrator.begin() as conn:
        await conn.execute(text("DELETE FROM stock_sessions WHERE exchange='NASDAQ'"))
        await conn.execute(
            text("UPDATE stock_quotes SET event_at=event_at-interval '3 days' WHERE coin_id=:c"),
            {"c": cid},
        )
        await conn.execute(
            text(
                "UPDATE stock_action_state SET health='unknown', "
                "checked_at=clock_timestamp()-interval '2 days', "
                "valid_until=clock_timestamp()-interval '1 day' WHERE coin_id=:c"
            ),
            {"c": cid},
        )
    response = await delete(api, roots[0], intent("Patient"))
    assert response.status_code == 200, response.text


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


async def assert_joint_confirmation_corruption_refused(app, migrator, admin, user, portfolio):
    from app.services.portfolio_closure import ClosureIntent, close_portfolio
    from app.services.stock_ownership import OwnershipHeld
    from tests.portfolio_closure_fixtures import retained_snapshot

    await proof_grants(admin)
    async with AsyncSession(app) as db:
        await close_portfolio(db, ClosureIntent(user, portfolio, uuid4(), "Strategy"))
        # A valid owned already-closed acknowledgement may use a fresh key and
        # another incoming reviewed name; retained evidence stays authoritative.
        assert (
            await close_portfolio(
                db, ClosureIntent(user, portfolio, uuid4(), "Different incoming review")
            )
        ).replayed is True
    async with migrator.begin() as conn:
        # Declared privileged retained-corruption fixture, never runtime DML.
        for table in ("portfolio_lifecycle_closures", "portfolio_closure_intents"):
            await conn.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER USER"))  # noqa: S608
            await conn.execute(
                text(
                    f"UPDATE {table} SET confirmation_name='Corrupt retained name' "  # noqa: S608
                    "WHERE portfolio_id=:p"
                ),
                {"p": portfolio},
            )
            await conn.execute(text(f"ALTER TABLE {table} ENABLE TRIGGER USER"))  # noqa: S608
        assert (
            await conn.execute(text("SELECT name FROM accounts WHERE id=:p"), {"p": portfolio})
        ).scalar_one() == "Strategy"

    async def snapshot(conn):
        result = await retained_snapshot(conn)
        for table in ("portfolio_lifecycle_closures", "portfolio_closure_intents"):
            result[table] = tuple(
                (
                    await conn.execute(
                        text(  # noqa: S608
                            f"SELECT to_jsonb(t)::text FROM {table} t ORDER BY id"  # noqa: S608
                        )
                    )
                ).scalars()
            )
            result[table + "_id_seq"] = tuple(
                (
                    await conn.execute(
                        text(  # noqa: S608
                            f"SELECT last_value,is_called FROM {table}_id_seq"  # noqa: S608
                        )
                    )
                ).one()
            )
        return result

    async with admin.connect() as conn:
        before = await snapshot(conn)
    async with AsyncSession(app) as db:
        with pytest.raises(OwnershipHeld, match="invalid_closure"):
            await close_portfolio(
                db, ClosureIntent(user, portfolio, uuid4(), "Different incoming review")
            )
        assert not db.in_transaction()
    async with admin.connect() as conn:
        assert await snapshot(conn) == before


async def test_joint_confirmation_corruption_refuses_empty_fresh_key_ack(authority):
    from tests.test_portfolio_closure_migrations import root

    app, migrator, admin = authority
    async with migrator.begin() as conn:
        user, portfolio = await root(conn)
    await assert_joint_confirmation_corruption_refused(app, migrator, admin, user, portfolio)


async def test_joint_confirmation_corruption_refuses_stock_fresh_key_ack(stock_authority):
    app, migrator, admin, books = stock_authority
    user, portfolio = books["roots"][0]
    await assert_joint_confirmation_corruption_refused(app, migrator, admin, user, portfolio)


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
