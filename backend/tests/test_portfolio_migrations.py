"""Actual migration callers and preservation assertions, not metadata substitutes."""

import asyncio
import os

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from tests.portfolio_fixtures import (
    economic_snapshot,
    migrate_to,
    portfolio_migration_db,
    seed_legacy_books,
)
from tests.test_migrations import (
    ensure_dividend_test_owner,
    run_test_migration,
    test_migration_url,
)

__all__ = ["portfolio_migration_db"]


async def test_migrator_connection_authenticates_without_mutating_parent(engine, settings):
    before_env = os.environ["DATABASE_URL"]
    await asyncio.to_thread(run_test_migration, "0014")
    child = create_async_engine(test_migration_url())
    try:
        async with child.connect() as conn:
            role = (
                await conn.execute(
                    text("""SELECT session_user,current_user,
                rolcanlogin,rolinherit,rolsuper,rolcreatedb,rolcreaterole,rolreplication,
                rolbypassrls FROM pg_roles WHERE rolname=session_user""")
                )
            ).one()
            assert tuple(role) == (
                "birja_migrator",
                "birja_migrator",
                True,
                False,
                False,
                False,
                False,
                False,
                False,
            )
            assert (
                await conn.execute(text("SELECT version_num FROM alembic_version"))
            ).scalar_one() == "0014"
        async with engine.connect() as conn:
            assert (await conn.execute(text("SELECT session_user"))).scalar_one() == "birja_test"
        assert settings.database_url == before_env == os.environ["DATABASE_URL"]
    finally:
        await child.dispose()


async def test_migrator_connection_set_role_does_not_authenticate(engine):
    async with engine.connect() as conn, conn.begin():
        await conn.execute(text("SET LOCAL ROLE birja_migrator"))
        assert (await conn.execute(text("SELECT session_user,current_user"))).one() == (
            "birja_test",
            "birja_migrator",
        )


async def test_migrator_connection_legacy_oracle_has_two_users_one_global_split(engine):
    await asyncio.to_thread(run_test_migration, "0014")
    async with engine.connect() as conn:
        tx = await conn.begin()
        try:
            before = await economic_snapshot(conn)
            books = await seed_legacy_books(conn)
            after = await economic_snapshot(conn)
            snap = {
                table: tuple(row for row in rows if row not in before[table])
                for table, rows in after.items()
            }
            assert len(snap["accounts"]) == 2
            assert len(snap["stock_split_applications"]) == 1
            assert len(snap["stock_ownership_movements"]) == 4
            assert books.cash != books.baselines
            assert len(snap["stock_dividend_entitlements"]) == 2
            assert len(snap["stock_dividend_payments"]) == 1
            assert len(snap["stock_dividend_decisions"]) == 1
        finally:
            await tx.rollback()


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+asyncpg://birja_test:test@prod.example:55432/birja_test",
        "postgresql+asyncpg://birja_test:test@127.0.0.1:5432/birja_test",
        "postgresql+asyncpg://postgres:test@127.0.0.1:55432/birja_test",
        "postgresql+asyncpg://birja_test:test@127.0.0.1:55432/other_test",
        "postgresql+asyncpg://birja_test:test@127.0.0.1:55432/birja_test?options=x",
    ],
)
def test_migrator_connection_unsafe_endpoint_or_admin_refused(url):
    with pytest.raises(RuntimeError):
        test_migration_url(url, "redis://:test@127.0.0.1:56379/0")


@pytest.mark.parametrize(
    "attribute,reset",
    [
        ("SUPERUSER", "NOSUPERUSER"),
        ("CREATEDB", "NOCREATEDB"),
        ("CREATEROLE", "NOCREATEROLE"),
        ("REPLICATION", "NOREPLICATION"),
        ("BYPASSRLS", "NOBYPASSRLS"),
        ("INHERIT", "NOINHERIT"),
    ],
)
async def test_migrator_connection_dangerous_role_attributes_refused(engine, attribute, reset):
    # Transactional hostile setup rolls back before ordinary session use.
    async with engine.connect() as conn, conn.begin():
        await conn.execute(text(f"ALTER ROLE birja_migrator {attribute}"))  # noqa: S608 - fixed matrix
        await conn.commit()
    try:
        with pytest.raises(DBAPIError, match="unsafe disposable migration owner"):
            await ensure_dividend_test_owner()
    finally:
        async with engine.begin() as conn:
            await conn.execute(text(f"ALTER ROLE birja_migrator {reset}"))  # noqa: S608 - fixed matrix


async def test_expansion_preserves_global_split_and_adds_only_unassociated_roots(
    portfolio_migration_db,
):
    engine = portfolio_migration_db
    await migrate_to("0014")
    async with engine.begin() as conn:
        books = await seed_legacy_books(conn)
        before = await economic_snapshot(conn)
    await migrate_to("0015")
    async with engine.connect() as conn:
        assert await economic_snapshot(conn) == before
        for table in (
            "holdings",
            "trades",
            "stock_fill_facts",
            "stock_ownership_movements",
            "stock_dividend_entitlements",
            "stock_dividend_payments",
            "stock_dividend_decisions",
        ):
            assert not (
                await conn.execute(text(f"SELECT 1 FROM {table} WHERE portfolio_id IS NOT NULL"))  # noqa: S608 - fixed migration/test allowlist
            ).all()  # noqa: S608
        split_columns = (
            await conn.execute(
                text("""SELECT column_name,data_type,column_default
            FROM information_schema.columns WHERE table_schema='public'
            AND table_name='stock_split_applications'""")
            )
        ).all()
        assert ("owner_digest_version", "smallint", None) in split_columns
        assert "portfolio_id" not in {c[0] for c in split_columns}
        assert (
            await conn.execute(
                text("SELECT owner_digest_version FROM stock_split_applications WHERE id=:i"),
                {"i": books.split_id},
            )
        ).scalar_one() is None
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_stock_closures"))
        ).scalar_one() == 0
        assert (
            await conn.execute(
                text("""SELECT count(*) FROM pg_constraint WHERE
            conrelid='accounts'::regclass AND contype='u' AND
            pg_get_constraintdef(oid)='UNIQUE (user_id)'""")
            )
        ).scalar_one() == 1
        assert not (
            await conn.execute(
                text("""SELECT has_function_privilege('public',
            'public.associate_legacy_portfolio_only()','EXECUTE')""")
            )
        ).scalar_one()


@pytest.mark.parametrize(
    "table",
    [
        "holdings",
        "trades",
        "stock_fill_facts",
        "stock_ownership_movements",
        "stock_dividend_entitlements",
        "stock_dividend_payments",
        "stock_dividend_decisions",
    ],
)
async def test_association_guard_only_authenticated_finite_unchanged_transition(
    portfolio_migration_db, table
):
    engine = portfolio_migration_db
    await migrate_to("0014")
    async with engine.begin() as conn:
        books = await seed_legacy_books(conn)
        before = await economic_snapshot(conn)
    await migrate_to("0015")
    where = "user_id=:u"
    params = {"u": books.owners[0], "p": books.roots[0], "foreign": books.roots[1]}
    # The ordinary admin and a SET ROLE connection both retain their original
    # session_user. Even client session flags do not authorize this transition.
    async with engine.connect() as conn, conn.begin():
        for set_role in (False, True):
            if set_role:
                await conn.execute(text("SET LOCAL ROLE birja_migrator"))
            await conn.execute(text("SELECT set_config('birja.migrating','true',true)"))
            with pytest.raises(DBAPIError, match="immutable portfolio association"):
                async with conn.begin_nested():
                    await conn.execute(
                        text(f"UPDATE {table} SET portfolio_id=:p WHERE {where}"),  # noqa: S608 - fixed test matrix
                        params,  # noqa: S608 - fixed migration/test allowlist
                    )  # noqa: S608
    authenticated = create_async_engine(test_migration_url())
    try:
        async with authenticated.connect() as conn, conn.begin():
            assert (
                await conn.execute(text("SELECT session_user"))
            ).scalar_one() == "birja_migrator"
            for assignment in ("portfolio_id=:foreign", "portfolio_id=:p,user_id=:foreign"):
                with pytest.raises(DBAPIError, match="immutable portfolio association"):
                    async with conn.begin_nested():
                        await conn.execute(
                            text(f"UPDATE {table} SET {assignment} WHERE {where}"),  # noqa: S608 - fixed test matrix
                            params,  # noqa: S608 - fixed migration/test allowlist
                        )  # noqa: S608
            await conn.execute(text(f"UPDATE {table} SET portfolio_id=:p WHERE {where}"), params)  # noqa: S608
            for assignment in ("portfolio_id=:p", "portfolio_id=NULL"):
                with pytest.raises(DBAPIError, match="immutable portfolio association"):
                    async with conn.begin_nested():
                        await conn.execute(
                            text(f"UPDATE {table} SET {assignment} WHERE {where}"),  # noqa: S608 - fixed test matrix
                            params,  # noqa: S608 - fixed migration/test allowlist
                        )  # noqa: S608
            with pytest.raises(DBAPIError, match="immutable portfolio association"):
                async with conn.begin_nested():
                    await conn.execute(text(f"DELETE FROM {table} WHERE {where}"), params)  # noqa: S608
            assert await economic_snapshot(conn) == before
    finally:
        await authenticated.dispose()


async def test_expansion_global_application_update_and_delete_remain_immutable(
    portfolio_migration_db,
):
    engine = portfolio_migration_db
    await migrate_to("0014")
    async with engine.begin() as conn:
        books = await seed_legacy_books(conn)
    await migrate_to("0015")
    authenticated = create_async_engine(test_migration_url())
    try:
        async with authenticated.connect() as conn, conn.begin():
            for statement in (
                "UPDATE stock_split_applications SET owner_digest_version=2 WHERE id=:i",
                "UPDATE stock_split_applications SET before_digest=repeat('c',64) WHERE id=:i",
                "DELETE FROM stock_split_applications WHERE id=:i",
            ):
                with pytest.raises(DBAPIError, match="immutable"):
                    async with conn.begin_nested():
                        await conn.execute(text(statement), {"i": books.split_id})
    finally:
        await authenticated.dispose()


@pytest.mark.parametrize(
    "legacy_revision", ["0007", "0008", "0009", "0010", "0011", "0012", "0013", "0014"]
)
async def test_preserved_legacy_economics_without_new_grant(
    portfolio_migration_db, legacy_revision
):
    engine = portfolio_migration_db
    await migrate_to(legacy_revision)
    # Upgrade the retained source to0014 before seeding stock accounting; the
    # dedicated original-revision tests retain their own pre-stock populations.
    await migrate_to("0014")
    async with engine.begin() as conn:
        books = await seed_legacy_books(conn)
        before = await economic_snapshot(conn)
    await migrate_to("0015")
    await migrate_to("0016")
    async with engine.connect() as conn:
        assert await economic_snapshot(conn) == before
        assert (
            await conn.execute(
                text("SELECT id,user_id,cash,starting_cash,name FROM accounts ORDER BY id")
            )
        ).all() == [
            (books.roots[i], books.owners[i], books.cash[i], books.baselines[i], "My portfolio")
            for i in range(2)
        ]
        for table in (
            "holdings",
            "trades",
            "stock_fill_facts",
            "stock_ownership_movements",
            "stock_dividend_entitlements",
            "stock_dividend_payments",
            "stock_dividend_decisions",
        ):
            assert not (
                await conn.execute(
                    text(  # noqa: S608 - fixed test inventory
                        f"SELECT 1 FROM {table} t LEFT JOIN accounts a ON a.id=t.portfolio_id "  # noqa: S608
                        "AND a.user_id=t.user_id WHERE a.id IS NULL"
                    )
                )
            ).all()
        split = (
            await conn.execute(
                text("SELECT owner_digest_version FROM stock_split_applications WHERE id=:i"),
                {"i": books.split_id},
            )
        ).scalar_one()
        assert split is None


async def test_resume_refuses_forged_owner_and_preserves_committed_association(
    portfolio_migration_db,
):
    engine = portfolio_migration_db
    await migrate_to("0014")
    async with engine.begin() as conn:
        books = await seed_legacy_books(conn)
        before = await economic_snapshot(conn)
    await migrate_to("0015")
    async with engine.connect() as conn, conn.begin():
        with pytest.raises(DBAPIError, match="immutable|association|portfolio"):
            async with conn.begin_nested():
                await conn.execute(
                    text("UPDATE trades SET portfolio_id=:p WHERE user_id=:u"),
                    {"p": books.roots[1], "u": books.owners[0]},
                )
        await conn.execute(text("SET LOCAL ROLE birja_migrator"))
        with pytest.raises(DBAPIError, match="immutable|association|portfolio"):
            async with conn.begin_nested():
                await conn.execute(
                    text("UPDATE trades SET portfolio_id=:p WHERE user_id=:u"),
                    {"p": books.roots[0], "u": books.owners[0]},
                )
    authenticated = create_async_engine(test_migration_url())
    try:
        async with authenticated.begin() as conn:
            with pytest.raises(DBAPIError, match="immutable|association|portfolio"):
                async with conn.begin_nested():
                    await conn.execute(
                        text("UPDATE trades SET portfolio_id=:p WHERE user_id=:u"),
                        {"p": books.roots[1], "u": books.owners[0]},
                    )
            # Commit one valid batch, representing interruption between finite
            # association batches. The remaining legacy rows are still NULL.
            await conn.execute(
                text("UPDATE trades SET portfolio_id=:p WHERE id=:t"),
                {"p": books.roots[0], "t": books.trade_ids[0]},
            )
    finally:
        await authenticated.dispose()
    # Re-entry must finish this partially associated ledger exactly once.
    await migrate_to("0016")
    await migrate_to("0016")
    async with engine.connect() as conn:
        assert await economic_snapshot(conn) == before
