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
