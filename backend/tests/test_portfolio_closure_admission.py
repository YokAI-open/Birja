"""Exact successor authority on owned disposable PostgreSQL, never production."""

import asyncio
import re
import subprocess
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from tests.portfolio_fixtures import reset_disposable_schema
from tests.test_migrations import run_test_migration, test_migration_url
from tests.test_portfolio_management_grants import production_bootstrap, sql


async def authorize(engine):
    from app.db.portfolio_bootstrap import GRANTS_0023_SQL, PREFLIGHT_0023_SQL

    async with engine.begin() as conn:
        await conn.execute(text(PREFLIGHT_0023_SQL))
        await sql(conn, GRANTS_0023_SQL)


@pytest.mark.parametrize(
    "drift",
    [
        "CREATE VIEW public.unexpected AS SELECT id FROM accounts",
        "ALTER FUNCTION close_portfolio(bigint,bigint,uuid,text,text) SET search_path=public",
        "GRANT EXECUTE ON FUNCTION check_stock_terminal_clock() TO PUBLIC",
        "DROP TRIGGER stock_terminal_clock ON stock_ownership_movements",
    ],
)
async def test_production_sql_and_python_refuse_same_corrupt_successor(successor, drift):
    from app.db.portfolio_bootstrap import ACL_SQL, PREFLIGHT_0023_SQL

    await authorize(successor)
    async with successor.begin() as conn:
        await conn.execute(text(drift))
        before_acl = (await conn.execute(text(ACL_SQL))).scalar_one()
        before_finance = (
            await conn.execute(text("SELECT id,cash,starting_cash FROM accounts ORDER BY id"))
        ).all()
        with pytest.raises(DBAPIError):
            async with conn.begin_nested():
                await conn.execute(text(PREFLIGHT_0023_SQL))
    code, _ = await production_bootstrap()
    assert code != 0
    async with successor.connect() as conn:
        assert (await conn.execute(text(ACL_SQL))).scalar_one() == before_acl
        assert (
            await conn.execute(text("SELECT id,cash,starting_cash FROM accounts ORDER BY id"))
        ).all() == before_finance


@pytest.mark.parametrize(
    "drift",
    [
        "CREATE TABLE public.unexpected(id bigint)",
        "CREATE VIEW public.unexpected AS SELECT id FROM accounts",
        "CREATE FUNCTION public.close_portfolio(text) RETURNS bigint "
        "LANGUAGE sql AS $$SELECT 1::bigint$$",
        "ALTER FUNCTION close_portfolio(bigint,bigint,uuid,text,text) SET search_path=public",
        "ALTER FUNCTION check_stock_terminal_clock() SECURITY INVOKER",
        "ALTER TABLE portfolio_closure_intents DISABLE TRIGGER portfolio_lifecycle_integrity",
        "ALTER TABLE portfolio_lifecycle_closures OWNER TO birja_test",
        "GRANT EXECUTE ON FUNCTION check_stock_terminal_clock() TO PUBLIC",
        "GRANT INSERT ON portfolio_closure_intents TO birja_app",
        "GRANT USAGE ON SEQUENCE portfolio_closure_intents_id_seq TO birja_scheduler",
        "ALTER ROLE birja_action_operator LOGIN",
        "GRANT CREATE ON SCHEMA public TO birja_app",
        "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator GRANT SELECT ON TABLES TO birja_app",
    ],
)
async def test_successor_drift_refuses_before_grants(successor, drift):
    from app.db.portfolio_bootstrap import ACL_SQL, PREFLIGHT_0023_SQL

    await authorize(successor)
    async with successor.connect() as conn:
        tx = await conn.begin()
        try:
            await conn.execute(text(drift))
            before = (await conn.execute(text(ACL_SQL))).scalar_one()
            with pytest.raises(DBAPIError):
                async with conn.begin_nested():
                    await conn.execute(text(PREFLIGHT_0023_SQL))
            assert (await conn.execute(text(ACL_SQL))).scalar_one() == before
        finally:
            await tx.rollback()


@pytest.mark.parametrize("role", ["birja_app", "birja_scheduler"])
async def test_successor_direct_lifecycle_and_identity_mutation_denied(successor, role):
    await authorize(successor)
    for statement in (
        "INSERT INTO portfolio_closure_intents(user_id) VALUES (1)",
        "UPDATE portfolio_lifecycle_closures SET policy_version='forged'",
        "DELETE FROM portfolio_stock_closures",
        "SELECT nextval('portfolio_lifecycle_closures_id_seq')",
        "SELECT nextval('portfolio_closure_intents_id_seq')",
    ):
        async with successor.begin() as conn:
            await conn.execute(text(f"SET LOCAL ROLE {role}"))  # noqa: S608 - finite role matrix
            with pytest.raises(DBAPIError) as error:
                async with conn.begin_nested():
                    await conn.execute(text(statement))
            assert error.value.orig.sqlstate == "42501"
    async with successor.begin() as conn:
        await conn.execute(text(f"SET LOCAL ROLE {role}"))  # noqa: S608
        assert (
            await conn.execute(
                text(
                    "SELECT has_function_privilege(current_user, "
                    "'close_portfolio(bigint,bigint,uuid,text,text)','EXECUTE')"
                )
            )
        ).scalar_one() is (role == "birja_app")
        for signature in (
            "check_stock_terminal_clock()",
            "check_portfolio_lifecycle_integrity()",
            "check_portfolio_terminal_root()",
        ):
            assert not (
                await conn.execute(
                    text("SELECT has_function_privilege(current_user,:s,'EXECUTE')"),
                    {"s": signature},
                )
            ).scalar_one()


def test_qualified_bootstrap_literals_0017_and_0020_unchanged():
    from app.db import portfolio_bootstrap as current

    source = subprocess.run(
        ["/usr/bin/git", "show", "9527e35:backend/app/db/portfolio_bootstrap.py"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    namespace = {}
    exec(compile(source, "qualified0020/bootstrap.py", "exec"), namespace)  # noqa: S102
    for name in (
        "PREFLIGHT_0017_SQL",
        "GRANTS_0017_SQL",
        "PREFLIGHT_SQL",
        "GRANTS_SQL",
        "CATALOGUE_SQL",
        "ACL_SQL",
        "CATALOGUE_0020_SHA256",
        "ACL_0020_SHA256",
    ):
        assert getattr(current, name) == namespace[name], name
    previous_sql = subprocess.run(
        ["/usr/bin/git", "show", "9527e35:deploy/db/bootstrap-roles.sql"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    new_sql = (Path(__file__).parents[2] / "deploy/db/bootstrap-roles.sql").read_text()
    for tag in (
        "portfolio_identity",
        "portfolio_grants",
        "management_identity",
        "management_grants",
    ):
        pattern = rf"DO \${tag}\$.*?END \${tag}\$;"
        assert (
            re.search(pattern, previous_sql, re.S).group()
            == re.search(pattern, new_sql, re.S).group()
        )


@pytest_asyncio.fixture(params=["fresh", "upgraded"])
async def successor(engine, request):
    await reset_disposable_schema(engine)
    migrator = create_async_engine(test_migration_url())
    if request.param == "upgraded":
        await asyncio.to_thread(run_test_migration, "0020")
        async with migrator.begin() as conn:
            await conn.execute(text("INSERT INTO users(email) VALUES ('upgrade@example.test')"))
            await conn.execute(
                text(
                    "SELECT initialize_portfolio(id) FROM users WHERE email='upgrade@example.test'"
                )
            )
            await conn.execute(text("UPDATE accounts SET cash=123.45"))
    await asyncio.to_thread(run_test_migration, "0023")
    try:
        yield engine
    finally:
        await migrator.dispose()
        await reset_disposable_schema(engine)
        await asyncio.to_thread(run_test_migration, "0020")


async def test_fresh_upgraded_exact_successor_admission_and_sql_parity(successor):
    from app.db.portfolio_bootstrap import (
        ACL_0023_SHA256,
        ACL_SQL,
        CATALOGUE_0023_SHA256,
        CATALOGUE_0023_SQL,
        GRANTS_0023_SQL,
        PREFLIGHT_0023_SQL,
    )
    from app.db.schema_contract import require_schema

    async with successor.begin() as conn:
        before = (await conn.execute(text("SELECT id,cash,starting_cash FROM accounts"))).all()
        await conn.execute(text(PREFLIGHT_0023_SQL))
        await sql(conn, GRANTS_0023_SQL)
        assert await require_schema(conn) == "0023"
        assert (await conn.execute(text(CATALOGUE_0023_SQL))).scalar_one() == CATALOGUE_0023_SHA256
        assert (await conn.execute(text(ACL_SQL))).scalar_one() == ACL_0023_SHA256
    code, diagnostic = await production_bootstrap()
    assert code == 0, diagnostic
    async with successor.connect() as conn:
        assert await require_schema(conn) == "0023"
        assert (
            await conn.execute(text("SELECT id,cash,starting_cash FROM accounts"))
        ).all() == before
