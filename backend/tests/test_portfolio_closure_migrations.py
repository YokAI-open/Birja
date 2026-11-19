"""Real migration-only closure schema; no partial-schema app startup."""

import asyncio
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from tests.portfolio_fixtures import reset_disposable_schema
from tests.test_migrations import ensure_dividend_test_owner, run_test_migration, test_migration_url


async def migrate(revision, *, down=False):
    assert revision in {"0020", "0021", "0022"}
    await asyncio.to_thread(run_test_migration, revision, down=down)


@pytest_asyncio.fixture
async def staged(engine):
    # This stack/database is exclusively owned by this serial migration campaign.
    # Never use migrated/head or restore a partial schema as an application.
    await reset_disposable_schema(engine)
    await migrate("0020")
    migration = create_async_engine(test_migration_url())
    try:
        yield migration
    finally:
        await migration.dispose()
        await reset_disposable_schema(engine)
        await migrate("0020")


async def root(conn, *, closed=False):
    owner = (
        await conn.execute(
            text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
            {"e": f"closure-migration-{uuid4()}@example.test"},
        )
    ).scalar_one()
    portfolio = (
        await conn.execute(
            text("""INSERT INTO accounts
        (user_id,name,name_key,cash,starting_cash,closed_at)
        VALUES (:u,'Strategy','strategy',8765.43,12500,
        CASE WHEN :closed THEN clock_timestamp() ELSE NULL END) RETURNING id"""),
            {"u": owner, "closed": closed},
        )
    ).scalar_one()
    return owner, portfolio


async def rejected(conn, query, params, *, state="23514"):
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await conn.execute(text(query), params)
            await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    assert error.value.orig.sqlstate == state


async def snapshot(conn):
    return {
        table: (
            await conn.execute(text(f"SELECT to_jsonb(t)::text FROM {table} t ORDER BY id"))  # noqa: S608
        ).all()
        for table in (
            "accounts",
            "holdings",
            "trades",
            "stock_ownership_movements",
            "stock_split_applications",
            "stock_dividend_entitlements",
            "stock_dividend_payments",
            "stock_dividend_decisions",
        )
    }


async def test_expansion_preserves_finance_and_identity(staged):
    async with staged.begin() as conn:
        await root(conn)
        before = await snapshot(conn)
    await migrate("0021")
    async with staged.connect() as conn:
        assert await snapshot(conn) == before
        for table in ("portfolio_lifecycle_closures", "portfolio_closure_intents"):
            assert (await conn.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one() == 0  # noqa: S608
            assert (
                await conn.execute(
                    text("""SELECT attidentity::text FROM pg_attribute
                WHERE attrelid=CAST(:t AS regclass) AND attname='id'"""),
                    {"t": table},
                )
            ).scalar_one() == "a"
        assert (
            await conn.execute(
                text(
                    "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                    "WHERE n.nspname='public' AND c.relkind='r'"
                )
            )
        ).scalar_one() == 31


async def test_expansion_rejects_foreign_and_malformed_intents(staged):
    await migrate("0021")
    async with staged.begin() as conn:
        owner, portfolio = await root(conn)
        foreign, _ = await root(conn)
        query = """INSERT INTO portfolio_closure_intents
            (user_id,portfolio_id,intent_key,confirmation_name,policy_version,outcome)
            VALUES (:u,:p,:k,:n,:policy,:outcome)"""
        valid = {
            "u": owner,
            "p": portfolio,
            "k": uuid4(),
            "n": "Strategy",
            "policy": "freeze_at_closure_v1",
            "outcome": "confirmation_changed",
        }
        await rejected(conn, query, {**valid, "u": foreign}, state="23503")
        for changes in ({"policy": "other"}, {"outcome": "pending"}, {"n": "  Strategy "}):
            await rejected(conn, query, {**valid, **changes})
        await conn.execute(text(query), valid)
        await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        for mutation in (
            "UPDATE portfolio_closure_intents SET confirmation_name='Other'",
            "DELETE FROM portfolio_closure_intents",
        ):
            await rejected(conn, mutation, {})


async def test_expansion_immutable_lifecycle_and_deferred_lineage(staged):
    await migrate("0021")
    async with staged.begin() as conn:
        owner, portfolio = await root(conn, closed=True)
        query = """INSERT INTO portfolio_lifecycle_closures
            (user_id,portfolio_id,closed_at,policy_version,provenance)
            SELECT :u,:p,closed_at,'freeze_at_closure_v1','retained_boundary'
            FROM accounts WHERE id=:p"""
        await conn.execute(text(query), {"u": owner, "p": portfolio})
        await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        for mutation in (
            "UPDATE portfolio_lifecycle_closures SET policy_version='other'",
            "DELETE FROM portfolio_lifecycle_closures",
        ):
            await rejected(conn, mutation, {})
        active_owner, active_portfolio = await root(conn)
        await rejected(
            conn,
            """INSERT INTO portfolio_lifecycle_closures
            (user_id,portfolio_id,closed_at,policy_version,provenance)
            VALUES (:u,:p,clock_timestamp(),'freeze_at_closure_v1','retained_boundary')""",
            {"u": active_owner, "p": active_portfolio},
        )


async def test_expansion_runtime_roles_cannot_forge_evidence(staged, engine):
    await migrate("0021")
    async with engine.begin() as conn:
        owner, portfolio = await root(conn)
        for role in ("birja_app", "birja_scheduler"):
            await conn.execute(text(f"SET LOCAL ROLE {role}"))  # noqa: S608
            await rejected(
                conn,
                """INSERT INTO portfolio_closure_intents
                (user_id,portfolio_id,intent_key,confirmation_name,policy_version,outcome)
                VALUES (:u,:p,:k,'Strategy','freeze_at_closure_v1','confirmation_changed')""",
                {"u": owner, "p": portfolio, "k": uuid4()},
                state="42501",
            )
            await conn.execute(text("RESET ROLE"))


async def test_expansion_bootstrap_repeated_and_unknown_objects_refused(staged, engine):
    await migrate("0021")
    await ensure_dividend_test_owner()
    # A new process must validate an already-present successor schema, not just
    # share a successful initial session fixture.
    import os
    import subprocess
    import sys

    child = await asyncio.to_thread(
        subprocess.run,
        [
            sys.executable,
            "-c",
            "import asyncio; from tests.test_migrations import ensure_dividend_test_owner; "
            "asyncio.run(ensure_dividend_test_owner())",
        ],  # noqa: S603
        env=os.environ.copy(),
        capture_output=True,
        timeout=30,
    )
    assert child.returncode == 0, child.stderr.decode()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE TABLE public.unexpected_closure_object(id bigint)"))
    try:
        with pytest.raises(RuntimeError, match="inventory"):
            await ensure_dividend_test_owner()
    finally:
        async with engine.begin() as conn:
            await conn.execute(text("DROP TABLE public.unexpected_closure_object"))


async def test_expansion_downgrade_refuses_before_data_loss(staged):
    await migrate("0021")
    with pytest.raises(RuntimeError, match="downgrade refused"):
        await migrate("0020", down=True)
    async with staged.connect() as conn:
        assert (
            await conn.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one() == "0021"


async def test_backfill_preserves_retained_multistock_sold_out_and_empty_books(staged):
    from tests.portfolio_closure_fixtures import retained_snapshot, seed_retained_books

    async with staged.begin() as conn:
        books = await seed_retained_books(conn, root)
        before = await retained_snapshot(conn)
    await migrate("0022")
    async with staged.connect() as conn:
        assert await retained_snapshot(conn) == before
        rows = (await conn.execute(text("""SELECT portfolio_id,provenance,confirmation_name,intent_id
            FROM portfolio_lifecycle_closures ORDER BY portfolio_id"""))).all()
        assert rows == [(p,"retained_boundary",None,None) for p in books["closed"]]
        assert (await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))).scalar_one() == 0
        boundaries = (await conn.execute(text("""SELECT closing_sequence FROM portfolio_stock_closures
            ORDER BY coin_id"""))).scalars().all()
        assert boundaries == [4,1]
    await ensure_dividend_test_owner()


@pytest.mark.parametrize("damage", ["missing_boundary", "global_tail", "units", "financial_chain"])
async def test_corrupt_backfill_refuses_before_writing_any_lifecycle(staged, damage):
    from tests.portfolio_closure_fixtures import retained_snapshot, seed_retained_books

    async with staged.begin() as conn:
        books = await seed_retained_books(conn, root)
        # Exact privileged corruption fixture; never an application repair path.
        table = "stock_ownership_movements" if damage == "financial_chain" else "portfolio_stock_closures"
        await conn.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER USER"))  # noqa: S608
        if damage == "missing_boundary":
            await conn.execute(text("DELETE FROM portfolio_stock_closures WHERE coin_id=:c"), {"c":books["stocks"][0]})
        elif damage == "global_tail":
            await conn.execute(text("UPDATE portfolio_stock_closures SET closing_sequence=3 WHERE coin_id=:c"), {"c":books["stocks"][0]})
        elif damage == "units":
            await conn.execute(text("UPDATE portfolio_stock_closures SET unit_epoch=1 WHERE coin_id=:c"), {"c":books["stocks"][0]})
        else:
            await conn.execute(text("UPDATE stock_ownership_movements SET recorded_at=economic_at-interval '1 hour' WHERE sequence=1"))
        await conn.execute(text(f"ALTER TABLE {table} ENABLE TRIGGER USER"))  # noqa: S608
        before = await retained_snapshot(conn)
    await migrate("0021")
    with pytest.raises((RuntimeError,DBAPIError), match="retained closure"):
        await migrate("0022")
    async with staged.connect() as conn:
        assert await retained_snapshot(conn) == before
        assert (await conn.execute(text("SELECT count(*) FROM portfolio_lifecycle_closures"))).scalar_one() == 0
        assert (await conn.execute(text("SELECT version_num FROM alembic_version"))).scalar_one() == "0021"


async def test_backfill_resumes_durable_batches_and_validates_boundary_fk(staged, monkeypatch):
    from importlib.util import module_from_spec, spec_from_file_location
    from pathlib import Path

    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    async with staged.begin() as conn:
        closed = [await root(conn, closed=True) for _ in range(3)]
    await migrate("0021")
    path = Path(__file__).parents[1] / "alembic/versions/0022_portfolio_closure_provenance.py"
    spec = spec_from_file_location("closure_backfill", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    original = module._backfill_batch
    calls = 0

    def interrupted():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("synthetic interrupted closure batch")
        return original()

    monkeypatch.setattr(module,"BATCH_SIZE",1)
    monkeypatch.setattr(module,"_backfill_batch",interrupted)
    async with staged.connect() as conn:
        def apply(sync):
            with Operations.context(MigrationContext.configure(sync)):
                module.upgrade()
        with pytest.raises(RuntimeError,match="synthetic interrupted"):
            await conn.run_sync(apply)
    async with staged.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM portfolio_lifecycle_closures"))).scalar_one() == 1
    await migrate("0022")
    await ensure_dividend_test_owner()
    async with staged.connect() as conn:
        assert (await conn.execute(text("SELECT portfolio_id FROM portfolio_lifecycle_closures ORDER BY portfolio_id"))).scalars().all() == [p for _,p in closed]
        assert (await conn.execute(text("SELECT convalidated FROM pg_constraint WHERE conname='fk_portfolio_stock_closure_lifecycle'"))).scalar_one() is True
    with pytest.raises(RuntimeError,match="downgrade refused"):
        await migrate("0021",down=True)
