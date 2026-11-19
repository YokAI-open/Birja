"""Exact successor authority on owned disposable PostgreSQL, never production."""

import asyncio

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.portfolio_fixtures import reset_disposable_schema
from tests.test_migrations import run_test_migration, test_migration_url
from tests.test_portfolio_management_grants import production_bootstrap, sql


@pytest_asyncio.fixture(params=["fresh", "upgraded"])
async def successor(engine, request):
    await reset_disposable_schema(engine)
    migrator = create_async_engine(test_migration_url())
    if request.param == "upgraded":
        await asyncio.to_thread(run_test_migration, "0020")
        async with migrator.begin() as conn:
            await conn.execute(text("INSERT INTO users(email) VALUES ('upgrade@example.test')"))
            await conn.execute(
                text("SELECT initialize_portfolio(id) FROM users WHERE email='upgrade@example.test'")
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
        assert (await conn.execute(text("SELECT id,cash,starting_cash FROM accounts"))).all() == before

