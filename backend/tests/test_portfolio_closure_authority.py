"""Real authenticated0023 SQL authority; runtime admission belongs to Plan04."""

import asyncio
import hashlib
import secrets
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from tests.portfolio_fixtures import reset_disposable_schema
from tests.test_migrations import ensure_dividend_test_owner, run_test_migration, test_migration_url
from tests.test_portfolio_closure_migrations import root

CLOSE = "SELECT * FROM public.close_portfolio(:u,:p,:k,:n,:policy)"
POLICY = "freeze_at_closure_v1"
BACKEND = Path(__file__).parents[1]


@pytest_asyncio.fixture
async def authority(engine):
    await reset_disposable_schema(engine)
    await asyncio.to_thread(run_test_migration, "0022")
    if (BACKEND / "alembic/versions/0023_portfolio_closure_authority.py").exists():
        await asyncio.to_thread(run_test_migration, "0023")
    password = secrets.token_hex(32)
    async with engine.begin() as conn:
        await conn.execute(text(f"ALTER ROLE birja_app LOGIN PASSWORD '{password}'"))  # noqa: S608
    app = create_async_engine(make_url(engine.url).set(username="birja_app", password=password))
    migrator = create_async_engine(test_migration_url())
    try:
        yield app, migrator, engine
    finally:
        await app.dispose()
        await migrator.dispose()
        await reset_disposable_schema(engine)
        await asyncio.to_thread(run_test_migration, "0020")


@pytest_asyncio.fixture
async def stock_authority(authority):
    from tests.portfolio_closure_fixtures import seed_retained_books

    app, migrator, admin = authority
    await reset_disposable_schema(admin)
    await asyncio.to_thread(run_test_migration, "0020")
    async with migrator.begin() as conn:
        books = await seed_retained_books(conn, root)
        # Declared privileged HISTORICAL fixture: make the retained fixture's
        # sold-out/multi-stock book active before the new lifecycle schema.
        for table in ("accounts", "portfolio_stock_closures"):
            await conn.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER USER"))  # noqa: S608
        portfolio = books["roots"][0][1]
        await conn.execute(
            text("DELETE FROM portfolio_stock_closures WHERE portfolio_id=:p"), {"p": portfolio}
        )
        await conn.execute(text("UPDATE accounts SET closed_at=NULL WHERE id=:p"), {"p": portfolio})
        for table in ("accounts", "portfolio_stock_closures"):
            await conn.execute(text(f"ALTER TABLE {table} ENABLE TRIGGER USER"))  # noqa: S608
    await asyncio.to_thread(run_test_migration, "0023")
    return app, migrator, admin, books


def intent(owner, portfolio, name="Strategy", key=None):
    return {"u": owner, "p": portfolio, "k": key or uuid4(), "n": name, "policy": POLICY}


async def call(app, payload):
    async with app.begin() as conn:
        return (await conn.execute(text(CLOSE), payload)).one()


async def reject(app, payload, state, message=None):
    with pytest.raises(DBAPIError) as error:
        await call(app, payload)
    assert error.value.orig.sqlstate == state, str(error.value.orig)
    if message:
        assert message in str(error.value.orig)


async def test_named_closure_is_atomic_immutable_and_preserves_finances(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
        before = (
            await conn.execute(
                text("SELECT cash,starting_cash FROM accounts WHERE id=:p"), {"p": portfolio}
            )
        ).one()
    result = await call(app, intent(owner, portfolio))
    assert tuple(result) == (portfolio, "closed", False)
    async with migrator.connect() as conn:
        after = (
            await conn.execute(
                text("SELECT cash,starting_cash FROM accounts WHERE id=:p"), {"p": portfolio}
            )
        ).one()
        assert before == after
        assert (
            await conn.execute(
                text("""SELECT a.closed_at=c.closed_at,
            c.provenance,c.confirmation_name,c.closed_at=i.recorded_at,i.outcome
            FROM accounts a JOIN portfolio_lifecycle_closures c ON c.portfolio_id=a.id
            JOIN portfolio_closure_intents i ON i.id=c.intent_id WHERE a.id=:p"""),
                {"p": portfolio},
            )
        ).one() == (True, "owner_confirmation", "Strategy", True, "closed")
        for table in ("trades", "stock_dividend_payments", "stock_ownership_movements"):
            assert (await conn.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one() == 0  # noqa: S608


async def test_replay_original_never_retargets_reused_name(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
    payload = intent(owner, portfolio)
    await call(app, payload)
    async with app.begin() as conn:
        replacement = (
            await conn.execute(
                text("SELECT portfolio_id FROM create_portfolio(:u,:k,'Strategy','')"),
                {"u": owner, "k": uuid4()},
            )
        ).scalar_one()
    assert tuple(await call(app, payload)) == (portfolio, "closed", True)
    await reject(app, {**payload, "p": replacement}, "23505", "closure_intent_conflict")
    async with migrator.connect() as conn:
        assert (
            await conn.execute(
                text("SELECT closed_at,cash FROM accounts WHERE id=:p"), {"p": replacement}
            )
        ).one() == (None, 10000)
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))
        ).scalar_one() == 1


async def test_replay_key_body_and_foreign_input_refusals(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
        foreign, _ = await root(conn)
    payload = intent(owner, portfolio)
    for changes in ({"u": foreign}, {"p": 999999999}):
        await reject(app, {**payload, **changes}, "P0002", "portfolio_unavailable")
    for changes in ({"policy": "other"}, {"n": " Strategy "}, {"k": None}):
        await reject(app, {**payload, **changes}, "22023")
    await call(app, payload)
    await reject(app, {**payload, "n": "Other"}, "23505", "closure_intent_conflict")


async def test_rollback_leaves_no_boundary_or_outcome(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
    async with app.connect() as conn:
        await conn.execute(text(CLOSE), intent(owner, portfolio))
        await conn.rollback()
    async with migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT closed_at FROM accounts WHERE id=:p"), {"p": portfolio})
        ).scalar_one() is None
        for table in ("portfolio_closure_intents", "portfolio_lifecycle_closures"):
            assert (await conn.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one() == 0  # noqa: S608


async def test_named_only_exact_app_signature_has_authority(authority):
    app, migrator, admin = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
    async with admin.begin() as conn:
        for role in ("birja_app", "birja_scheduler"):
            assert (
                await conn.execute(
                    text(
                        "SELECT has_function_privilege(:r,"
                        "'public.close_portfolio(bigint,bigint,uuid,text,text)','EXECUTE')"
                    ),
                    {"r": role},
                )
            ).scalar_one() is (role == "birja_app")
            await conn.execute(text(f"SET LOCAL ROLE {role}"))  # noqa: S608
            with pytest.raises(DBAPIError) as error:
                async with conn.begin_nested():
                    await conn.execute(
                        text("UPDATE accounts SET closed_at=clock_timestamp() WHERE id=:p"),
                        {"p": portfolio},
                    )
            assert error.value.orig.sqlstate == "42501"
            await conn.execute(text("RESET ROLE"))
    assert tuple(await call(app, intent(owner, portfolio))) == (portfolio, "closed", False)


async def test_replay_concurrent_original_has_one_outcome(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
    payload = intent(owner, portfolio)
    results = await asyncio.gather(call(app, payload), call(app, payload))
    assert sorted(r.replayed for r in results) == [False, True]
    async with migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))
        ).scalar_one() == 1


async def test_named_sold_out_multistock_uses_global_tail_and_preserves_finance(stock_authority):
    from tests.portfolio_closure_fixtures import retained_snapshot

    app, migrator, _, books = stock_authority
    owner, portfolio = books["roots"][0]
    async with migrator.connect() as conn:
        before = await retained_snapshot(conn)
    assert tuple(await call(app, intent(owner, portfolio))) == (portfolio, "closed", False)
    async with migrator.connect() as conn:
        after = await retained_snapshot(conn)
        # Only account lifecycle state and per-stock terminal evidence change.
        for key in before.keys() - {
            "accounts",
            "portfolio_stock_closures",
            "portfolio_stock_closures_id_seq",
        }:
            assert before[key] == after[key], key
        assert (
            await conn.execute(
                text("""SELECT coin_id,closing_sequence,unit_epoch
            FROM portfolio_stock_closures WHERE portfolio_id=:p ORDER BY coin_id"""),
                {"p": portfolio},
            )
        ).all() == [(books["stocks"][0], 4, 0), (books["stocks"][1], 1, 0)]
        assert (
            await conn.execute(
                text("SELECT cash,starting_cash FROM accounts WHERE id=:p"), {"p": portfolio}
            )
        ).one() == (Decimal("8785.43"), Decimal("12500"))
    assert tuple(await call(app, intent(owner, portfolio))) == (portfolio, "closed", True)


async def test_replay_corrupted_boundary_refuses_without_mutation(stock_authority):
    app, migrator, _, books = stock_authority
    owner, portfolio = books["roots"][0]
    payload = intent(owner, portfolio)
    await call(app, payload)
    async with migrator.begin() as conn:
        await conn.execute(text("ALTER TABLE portfolio_stock_closures DISABLE TRIGGER USER"))
        await conn.execute(
            text("""UPDATE portfolio_stock_closures SET closing_sequence=3
            WHERE portfolio_id=:p AND coin_id=:c"""),
            {"p": portfolio, "c": books["stocks"][0]},
        )
        await conn.execute(text("ALTER TABLE portfolio_stock_closures ENABLE TRIGGER USER"))
    await reject(app, payload, "23514", "invalid closure stock boundary")
    async with migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))
        ).scalar_one() == 1


async def test_named_orphan_holding_refuses_atomically(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
        coin = (
            await conn.execute(
                text("SELECT coin_id FROM stock_instruments ORDER BY coin_id LIMIT 1")
            )
        ).scalar_one()
        await conn.execute(
            text("""INSERT INTO stock_action_state
            (coin_id,admission_generation,journal_start_at,complete_from)
            VALUES (:c,1,clock_timestamp()-interval '1 day',
                    clock_timestamp()-interval '1 hour')"""),
            {"c": coin},
        )
        await conn.execute(
            text("""INSERT INTO holdings
            (user_id,portfolio_id,coin_id,quantity,cost_basis) VALUES (:u,:p,:c,1,10)"""),
            {"u": owner, "p": portfolio, "c": coin},
        )
    await reject(app, intent(owner, portfolio), "23514", "invalid closure holding history")
    async with migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT closed_at FROM accounts WHERE id=:p"), {"p": portfolio})
        ).scalar_one() is None
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))
        ).scalar_one() == 0


async def test_named_first_buy_while_root_waits_requires_transaction_retry(authority):
    """Observe an actual lock wait; no sleep is used as proof of concurrency."""
    app, migrator, admin = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
        coin = (
            await conn.execute(
                text("SELECT coin_id FROM stock_instruments ORDER BY coin_id LIMIT 1")
            )
        ).scalar_one()
        await conn.execute(
            text("""INSERT INTO stock_action_state
            (coin_id,admission_generation,journal_start_at,complete_from)
            VALUES (:c,1,clock_timestamp()-interval '1 day',
                    clock_timestamp()-interval '1 hour')"""),
            {"c": coin},
        )
    async with migrator.connect() as writer, app.connect() as closer:
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
        pid = (await closer.execute(text("SELECT pg_backend_pid()"))).scalar_one()
        task = asyncio.create_task(closer.execute(text(CLOSE), intent(owner, portfolio)))
        try:
            async with asyncio.timeout(1.5):
                while True:
                    async with admin.connect() as observer:
                        waiting = (
                            await observer.execute(
                                text("""SELECT wait_event_type='Lock'
                            AND cardinality(pg_blocking_pids(pid))>0
                            FROM pg_stat_activity WHERE pid=:p"""),
                                {"p": pid},
                            )
                        ).scalar_one()
                    if waiting:
                        break
                    await asyncio.sleep(0)
            # Declared synthetic first ownership: a real journal/root-lock race,
            # not market admission acceptance (that remains Plan09).
            await writer.execute(
                text("""INSERT INTO holdings
                (user_id,portfolio_id,coin_id,quantity,cost_basis) VALUES (:u,:p,:c,1,10)"""),
                {"u": owner, "p": portfolio, "c": coin},
            )
            await writer.execute(
                text("""INSERT INTO stock_ownership_movements
                (user_id,portfolio_id,coin_id,sequence,economic_at,recorded_at,quantity,
                before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,causal_key)
                SELECT :u,:p,:c,1,stamp,stamp,1,0,1,0,10,0,'opening','opening:first-buy'
                FROM (SELECT clock_timestamp() AS stamp) clock"""),
                {"u": owner, "p": portfolio, "c": coin},
            )
            await writer.commit()
            with pytest.raises(DBAPIError) as error:
                await task
            assert error.value.orig.sqlstate == "40001"
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            await closer.rollback()
            await writer.rollback()
    assert tuple(await call(app, intent(owner, portfolio))) == (portfolio, "closed", False)


async def test_migration_checksum_and_authenticated_owner_are_required(authority):
    app, _, _ = authority
    from importlib.util import module_from_spec, spec_from_file_location

    path = BACKEND / "alembic/versions/0023_portfolio_closure_authority.py"
    spec = spec_from_file_location("closure_authority", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    assert (
        hashlib.sha256(
            (BACKEND / "alembic/sql/0023_portfolio_closure.sql").read_bytes()
        ).hexdigest()
        == module.SQL_SHA256
    )
    async with app.connect() as conn:
        settings = (
            await conn.execute(
                text(
                    "SELECT proconfig FROM pg_proc WHERE oid="
                    "'public.close_portfolio(bigint,bigint,uuid,text,text)'::regprocedure"
                )
            )
        ).scalar_one()
        assert {
            "search_path=pg_catalog, public, pg_temp",
            "lock_timeout=2s",
            "statement_timeout=10s",
            "idle_in_transaction_session_timeout=30s",
        } <= set(settings)
    await ensure_dividend_test_owner()


async def test_refusal_is_permanent_after_rename_back_and_delayed_original(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
    payload = intent(owner, portfolio)
    async with app.begin() as conn:
        await conn.execute(
            text("SELECT * FROM update_portfolio_metadata(:u,:p,'New strategy','',true,false)"),
            {"u": owner, "p": portfolio},
        )
    assert tuple(await call(app, payload)) == (portfolio, "confirmation_changed", False)
    async with app.begin() as conn:
        await conn.execute(
            text("SELECT * FROM update_portfolio_metadata(:u,:p,'Strategy','',true,false)"),
            {"u": owner, "p": portfolio},
        )
    # Even after the original name returns, a delayed concurrent copy cannot
    # commit a deletion the browser now knows was definitively refused.
    results = await asyncio.gather(call(app, payload), call(app, payload))
    assert all(tuple(r) == (portfolio, "confirmation_changed", True) for r in results)
    async with migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT closed_at FROM accounts WHERE id=:p"), {"p": portfolio})
        ).scalar_one() is None
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))
        ).scalar_one() == 1
    assert tuple(await call(app, intent(owner, portfolio))) == (portfolio, "closed", False)


async def seed_refusals(conn, owner, portfolio, count):
    # Privileged bounded quota fixture, not an application journal-write path.
    await conn.execute(
        text("""INSERT INTO portfolio_closure_intents
        (user_id,portfolio_id,intent_key,confirmation_name,policy_version,outcome,recorded_at)
        SELECT :u,:p,gen_random_uuid(),'Prior review','freeze_at_closure_v1',
          'confirmation_changed',clock_timestamp() FROM generate_series(1,:count)"""),
        {"u": owner, "p": portfolio, "count": count},
    )


async def same_owner_root(app, owner, name):
    async with app.begin() as conn:
        return (
            await conn.execute(
                text("SELECT portfolio_id FROM create_portfolio(:u,:k,:n,'')"),
                {"u": owner, "k": uuid4(), "n": name},
            )
        ).scalar_one()


async def test_quota_concurrent_edge_is_serialized_and_closed_replay_still_works(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
        await seed_refusals(conn, owner, portfolio, 199)
    sibling = await same_owner_root(app, owner, "Sibling")
    first, second = intent(owner, portfolio), intent(owner, sibling, "Sibling")
    results = await asyncio.gather(call(app, first), call(app, second), return_exceptions=True)
    successes = [
        (payload, result)
        for payload, result in zip((first, second), results, strict=True)
        if not isinstance(result, BaseException)
    ]
    failures = [r for r in results if isinstance(r, DBAPIError)]
    assert len(successes) == len(failures) == 1
    assert failures[0].orig.sqlstate == "P0001"
    assert "closure_quota" in str(failures[0].orig)
    original, closed = successes[0]
    assert closed.outcome == "closed"
    assert tuple(await call(app, original)) == (closed.portfolio_id, "closed", True)
    # A fresh key for an already-closed owned target adds no journal row and
    # acknowledges its immutable boundary even when the new-intent cap is full.
    assert tuple(await call(app, {**original, "k": uuid4()})) == (
        closed.portfolio_id,
        "closed",
        True,
    )
    async with migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))
        ).scalar_one() == 200
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_lifecycle_closures"))
        ).scalar_one() == 1
        assert (
            await conn.execute(text("SELECT count(*) FROM accounts WHERE closed_at IS NULL"))
        ).scalar_one() == 1


async def test_quota_counts_only_current_utc_day_and_refusal_replays_precede_cap(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
        await conn.execute(
            text("""INSERT INTO portfolio_closure_intents
            (user_id,portfolio_id,intent_key,confirmation_name,policy_version,outcome,recorded_at)
            SELECT :u,:p,gen_random_uuid(),'Prior review','freeze_at_closure_v1',
              'confirmation_changed',
              (date_trunc('day',clock_timestamp() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC')
                 -interval '1 second' FROM generate_series(1,200)"""),
            {"u": owner, "p": portfolio},
        )
    payload = intent(owner, portfolio, "Stale review")
    assert tuple(await call(app, payload)) == (portfolio, "confirmation_changed", False)
    async with migrator.begin() as conn:
        await seed_refusals(conn, owner, portfolio, 199)
    assert tuple(await call(app, payload)) == (portfolio, "confirmation_changed", True)
    await reject(app, intent(owner, portfolio), "P0001", "closure_quota")
    async with migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))
        ).scalar_one() == 400
        assert (
            await conn.execute(text("SELECT closed_at FROM accounts WHERE id=:p"), {"p": portfolio})
        ).scalar_one() is None


async def test_replay_concurrent_conflicting_body_cannot_change_original(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
    payload = intent(owner, portfolio)
    results = await asyncio.gather(
        call(app, payload), call(app, {**payload, "n": "Other"}), return_exceptions=True
    )
    assert sum(isinstance(result, DBAPIError) for result in results) == 1
    failure = next(r for r in results if isinstance(r, DBAPIError))
    assert failure.orig.sqlstate == "23505"
    winner = next(r for r in results if not isinstance(r, BaseException))
    assert winner.outcome in {"closed", "confirmation_changed"}
    async with migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))
        ).scalar_one() == 1


async def test_rollback_of_refusal_does_not_manufacture_terminal_resolution(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
    payload = intent(owner, portfolio, "Wrong review")
    async with app.connect() as conn:
        assert (await conn.execute(text(CLOSE), payload)).one().outcome == "confirmation_changed"
        await conn.rollback()
    async with migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))
        ).scalar_one() == 0
    assert tuple(await call(app, payload)) == (portfolio, "confirmation_changed", False)


@pytest.mark.parametrize("failure", ["checksum", "principal"])
async def test_authority_migration_refuses_tamper_or_unauthenticated_principal(authority, failure):
    from importlib.util import module_from_spec, spec_from_file_location

    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    app, migrator, _ = authority
    path = BACKEND / "alembic/versions/0023_portfolio_closure_authority.py"
    spec = spec_from_file_location("closure_authority_negative", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    if failure == "checksum":
        module.SQL_SHA256 = "0" * 64
    target = migrator if failure == "checksum" else app
    async with target.connect() as conn:
        before = (
            await conn.execute(
                text(
                    "SELECT pg_get_functiondef("
                    "'public.close_portfolio(bigint,bigint,uuid,text,text)'::regprocedure)"
                )
            )
        ).scalar_one()

        def apply(sync):
            with Operations.context(MigrationContext.configure(sync)):
                module.upgrade()

        with pytest.raises(RuntimeError, match="checksum mismatch|authenticated birja_migrator"):
            await conn.run_sync(apply)
        assert (
            await conn.execute(
                text(
                    "SELECT pg_get_functiondef("
                    "'public.close_portfolio(bigint,bigint,uuid,text,text)'::regprocedure)"
                )
            )
        ).scalar_one() == before
