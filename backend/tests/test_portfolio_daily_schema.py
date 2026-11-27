"""Daily value migrations and authority on a disposable PostgreSQL database."""

import asyncio
import os
import secrets
import sys
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from tests.portfolio_fixtures import economic_snapshot, seed_portfolio_world
from tests.test_migrations import BACKEND_DIR, test_migration_url

OBSERVATION = text("""
    INSERT INTO public.portfolio_daily_values
        (portfolio_id,user_id,utc_day,captured_at,starting_cash,total_value,valuation_complete)
    VALUES (:portfolio,:owner,:day,:capture,:starting_cash,:total,:complete)
""")
LOCK_ROOT = text("SELECT public.lock_portfolio_daily_value_root(:owner,:portfolio)")
MIGRATION_REVISION = text("SELECT version_num FROM public.alembic_version")


@pytest_asyncio.fixture
async def scratch_database() -> AsyncIterator[tuple[AsyncEngine, AsyncEngine]]:
    # The existing migration URL helper admits only the local disposable test
    # administrator. Create and remove a test-owned database on that server.
    admin_url = make_url(os.environ["DATABASE_URL"])
    migrator_url = make_url(test_migration_url())
    name = f"daily_values_{uuid4().hex}_test"
    admin = create_async_engine(admin_url, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    scratch = create_async_engine(
        admin_url.set(database=name), poolclass=NullPool, hide_parameters=True
    )
    migrator = create_async_engine(migrator_url.set(database=name), poolclass=NullPool)
    try:
        async with admin.connect() as conn:
            assert await conn.scalar(
                text("""
                SELECT current_database()='birja_test' AND session_user='birja_test' AND rolsuper
                FROM pg_roles WHERE rolname=session_user
            """)
            )
            await conn.exec_driver_sql(f'CREATE DATABASE "{name}" TEMPLATE template0')
        try:
            async with scratch.begin() as conn:
                await conn.exec_driver_sql("GRANT USAGE, CREATE ON SCHEMA public TO birja_migrator")
                await conn.exec_driver_sql(
                    "GRANT USAGE ON SCHEMA public TO birja_app, birja_scheduler"
                )
                await conn.exec_driver_sql(
                    "REVOKE CREATE ON SCHEMA public FROM PUBLIC, birja_app, birja_scheduler"
                )
            yield scratch, migrator
        finally:
            await migrator.dispose()
            await scratch.dispose()
            async with admin.connect() as conn:
                await conn.exec_driver_sql(f'DROP DATABASE "{name}"')
    finally:
        await admin.dispose()


async def run_migration(engine: AsyncEngine, revision: str, *, down: bool = False) -> None:
    child = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "alembic",
        "downgrade" if down else "upgrade",
        revision,
        cwd=BACKEND_DIR,
        env={**os.environ, "DATABASE_URL": engine.url.render_as_string(hide_password=False)},
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(child.communicate(), timeout=120)
    except TimeoutError:
        child.kill()
        await child.wait()
        raise
    if child.returncode:
        output = (stdout + stderr).decode().replace(engine.url.password or "", "[redacted]")
        raise RuntimeError(output)


def observation(owner: int, portfolio: int, **overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "owner": owner,
        "portfolio": portfolio,
        "day": date(2026, 11, 26),
        "capture": datetime(2026, 11, 26, 22, 30, tzinfo=UTC),
        "starting_cash": Decimal("10000"),
        "total": Decimal("0"),
        "complete": True,
    }
    values.update(overrides)
    return values


async def test_isolated_schema_populated_predecessor_and_empty_downgrade(scratch_database):
    admin, migrator = scratch_database
    await run_migration(migrator, "0027")
    async with migrator.begin() as conn:
        await seed_portfolio_world(conn)
        original = await economic_snapshot(conn)
    await run_migration(migrator, "0028")
    async with admin.connect() as conn:
        assert await conn.scalar(MIGRATION_REVISION) == "0028"
        assert await economic_snapshot(conn) == original
        assert await conn.scalar(text("SELECT count(*) FROM public.portfolio_daily_values")) == 0
        for role in ("birja_app", "birja_scheduler", "birja_action_operator"):
            assert await conn.scalar(
                text("""
                    SELECT NOT has_any_column_privilege(:role, 'public.portfolio_daily_values',
                        'SELECT, INSERT, UPDATE, REFERENCES')
                      AND NOT has_table_privilege(:role, 'public.portfolio_daily_values',
                        'DELETE, TRUNCATE')
                      AND NOT has_function_privilege(:role,
                        'public.lock_portfolio_daily_value_root(bigint,bigint)', 'EXECUTE')
                """),
                {"role": role},
            )
    await run_migration(migrator, "0027", down=True)
    async with admin.connect() as conn:
        assert await conn.scalar(MIGRATION_REVISION) == "0027"
        assert (
            await conn.scalar(text("SELECT to_regclass('public.portfolio_daily_values')")) is None
        )
        assert await economic_snapshot(conn) == original


async def test_isolated_schema_exact_observations_and_populated_downgrade(scratch_database):
    _, migrator = scratch_database
    await run_migration(migrator, "0028")
    async with migrator.begin() as conn:
        world = await seed_portfolio_world(conn)
        zero = observation(world.owner, world.first)
        missing = observation(world.owner, world.sibling, total=None, complete=False)
        assert await conn.scalar(LOCK_ROOT, zero)
        assert not await conn.scalar(LOCK_ROOT, observation(world.owner, world.closed))
        assert not await conn.scalar(LOCK_ROOT, observation(world.foreign_owner, world.first))
        observed = await conn.execute(OBSERVATION, zero)
        assert observed.rowcount == 1
        await conn.execute(OBSERVATION, missing)
        for overrides, sqlstate in (
            ({}, "23505"),
            ({"owner": world.foreign_owner}, "23514"),
            ({"portfolio": world.closed}, "23514"),
            ({"day": date(2026, 11, 27)}, "23514"),
            ({"capture": datetime(2026, 11, 26, 21, 59, tzinfo=UTC)}, "23514"),
            ({"complete": False}, "23514"),
            ({"total": Decimal("NaN")}, "23514"),
            ({"starting_cash": Decimal("NaN")}, "23514"),
        ):
            with pytest.raises(DBAPIError) as failure:
                async with conn.begin_nested():
                    await conn.execute(OBSERVATION, {**zero, **overrides})
            assert failure.value.orig.sqlstate == sqlstate
    with pytest.raises(RuntimeError, match="Daily value downgrade refused"):
        await run_migration(migrator, "0027", down=True)
    async with migrator.connect() as conn:
        assert await conn.scalar(MIGRATION_REVISION) == "0028"
        assert (
            await conn.execute(
                text("""
                    SELECT total_value, valuation_complete FROM public.portfolio_daily_values
                    ORDER BY portfolio_id
                """)
            )
        ).all() == [(Decimal("0.00"), True), (None, False)]


async def authorize_dev(engine: AsyncEngine, revision: str) -> None:
    from app.db.dev_bootstrap import _authorize_portfolios

    async with engine.begin() as conn:
        assert await conn.scalar(MIGRATION_REVISION) == revision
        raw = await conn.get_raw_connection()
        await _authorize_portfolios(raw.driver_connection, revision)


@pytest.mark.parametrize("source", [None, "0027"], ids=["fresh", "populated"])
async def test_current_admission_after_verified_migration(scratch_database, source):
    from app.db.portfolio_migrate import require_migrator, require_source
    from app.db.schema_contract import SchemaAdmissionError, require_schema

    admin, migrator = scratch_database
    require_source()
    if source is not None:
        await run_migration(migrator, source)
        async with migrator.begin() as conn:
            await seed_portfolio_world(conn)
        await authorize_dev(admin, source)
        async with admin.connect() as conn:
            await conn.execute(text("SET LOCAL ROLE birja_app"))
            assert await require_schema(conn) == source
            with pytest.raises(SchemaAdmissionError, match="incompatible_schema"):
                await require_schema(conn, consumer="portfolio_daily")
    async with migrator.connect() as conn:
        assert await require_migrator(conn, fresh=source is None) == source

    await run_migration(migrator, "0028")
    async with migrator.connect() as conn:
        assert await require_migrator(conn) == "0028"
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM public.portfolio_daily_values")) == 0
        with pytest.raises(SchemaAdmissionError, match="incompatible_authority"):
            await require_schema(conn, consumer="portfolio_daily")
    await authorize_dev(admin, "0028")
    async with admin.connect() as conn:
        await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
        assert await require_schema(conn, consumer="portfolio_daily") == "0028"


async def test_current_admission_exact_runtime_roles_and_reapplication(scratch_database):
    from app.db.schema_contract import SchemaAdmissionError, require_schema

    admin, migrator = scratch_database
    await run_migration(migrator, "0028")
    async with migrator.begin() as conn:
        world = await seed_portfolio_world(conn)
        economics_before = await economic_snapshot(conn)
    await authorize_dev(admin, "0028")

    roles = {}
    try:
        async with admin.begin() as conn:
            for role in ("birja_app", "birja_scheduler"):
                password = secrets.token_hex(32)
                statement = await conn.scalar(
                    text(
                        "SELECT format('ALTER ROLE %I LOGIN PASSWORD %L',"
                        " CAST(:role AS text), CAST(:password AS text))"
                    ),
                    {"role": role, "password": password},
                )
                raw = await conn.get_raw_connection()
                await raw.driver_connection.execute(statement)
                roles[role] = create_async_engine(
                    admin.url.set(username=role, password=password), poolclass=NullPool
                )
        value = observation(world.owner, world.first, total=Decimal("2468.17"))
        async with roles["birja_scheduler"].begin() as conn:
            assert await conn.scalar(text("SELECT session_user")) == "birja_scheduler"
            assert await require_schema(conn, consumer="portfolio_daily") == "0028"
            assert await conn.scalar(LOCK_ROOT, value)
            assert not await conn.scalar(LOCK_ROOT, observation(world.owner, world.closed))
            append = text(
                OBSERVATION.text
                + " ON CONFLICT (portfolio_id,utc_day) DO NOTHING RETURNING portfolio_id"
            )
            assert await conn.scalar(append, value) == world.first
            assert await conn.scalar(append, {**value, "total": Decimal("1")}) is None
            for statement in (
                "SELECT total_value FROM public.portfolio_daily_values",
                "UPDATE public.accounts SET cash=cash WHERE false",
                "UPDATE public.portfolio_daily_values SET total_value=0 WHERE false",
                "DELETE FROM public.portfolio_daily_values WHERE false",
                "TRUNCATE public.portfolio_daily_values",
            ):
                with pytest.raises(DBAPIError) as denied:
                    async with conn.begin_nested():
                        await conn.exec_driver_sql(statement)
                assert denied.value.orig.sqlstate == "42501"
            with pytest.raises(DBAPIError) as closed:
                async with conn.begin_nested():
                    await conn.execute(OBSERVATION, observation(world.owner, world.closed))
            assert closed.value.orig.sqlstate == "23514"
        async with roles["birja_app"].begin() as conn:
            assert await conn.scalar(text("SELECT session_user")) == "birja_app"
            assert await require_schema(conn, consumer="portfolio_daily") == "0028"
            assert await conn.scalar(
                text("SELECT total_value FROM public.portfolio_daily_values")
            ) == Decimal("2468.17")
            with pytest.raises(DBAPIError) as denied:
                async with conn.begin_nested():
                    await conn.execute(OBSERVATION, observation(world.owner, world.sibling))
            assert denied.value.orig.sqlstate == "42501"
    finally:
        for engine in roles.values():
            await engine.dispose()

    await authorize_dev(admin, "0028")
    async with admin.begin() as conn:
        assert await economic_snapshot(conn) == economics_before
        assert await conn.scalar(
            text("SELECT total_value FROM public.portfolio_daily_values")
        ) == Decimal("2468.17")
        with pytest.raises(SchemaAdmissionError, match="incompatible_authority"):
            async with conn.begin_nested():
                await conn.exec_driver_sql(
                    "REVOKE SELECT ON public.portfolio_daily_values FROM birja_app"
                )
                await require_schema(conn, consumer="portfolio_daily")
        assert await require_schema(conn, consumer="portfolio_daily") == "0028"
