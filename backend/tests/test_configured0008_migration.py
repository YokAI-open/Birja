"""Authentic configured0008 runtime grants carried through released migrations."""

import asyncio
import json
import secrets
import subprocess
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from app.db import portfolio_bootstrap as bootstrap
from app.db.portfolio_migrate import require_migrator
from app.db.schema_contract import require_schema
from tests.portfolio_fixtures import economic_snapshot, migrate_to, portfolio_migration_db
from tests.test_migrations import test_migration_url
from tests.test_portfolio_management_grants import sql

__all__ = ["portfolio_migration_db"]

# Exact runtime-grant/default statements from released commit46d24c8,
# deploy/db/bootstrap-roles.sql. The fixture already creates the restricted
# principals and migrator-owned0008 tables; only the historical grants remain.
# No modern GRANTS_SQL is applied before the final migration preflight.
CONFIGURED_0008_GRANTS = """
GRANT SELECT, INSERT ON users TO birja_app;
GRANT SELECT, INSERT, UPDATE ON accounts, auth_sessions, refresh_tokens, holdings TO birja_app;
GRANT SELECT, INSERT ON trades TO birja_app;
GRANT SELECT ON coins, prices TO birja_app;
GRANT SELECT ON coins TO birja_scheduler;
GRANT SELECT, INSERT, UPDATE ON prices TO birja_scheduler;
GRANT USAGE ON SEQUENCE users_id_seq,accounts_id_seq,auth_sessions_id_seq,
 refresh_tokens_id_seq,holdings_id_seq,trades_id_seq TO birja_app;
ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator REVOKE
 SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN
 ON TABLES FROM PUBLIC,birja_app,birja_scheduler;
ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator IN SCHEMA public REVOKE
 SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN
 ON TABLES FROM PUBLIC,birja_app,birja_scheduler;
ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator REVOKE
 USAGE,SELECT,UPDATE ON SEQUENCES FROM PUBLIC,birja_app,birja_scheduler;
ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator IN SCHEMA public REVOKE
 USAGE,SELECT,UPDATE ON SEQUENCES FROM PUBLIC,birja_app,birja_scheduler;
ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator REVOKE
 EXECUTE ON FUNCTIONS FROM PUBLIC,birja_app,birja_scheduler;
"""


async def authority(conn):
    return {
        key: await conn.scalar(text(query))
        for key, query in (
            ("catalogue", bootstrap.CATALOGUE_0023_SQL),
            ("acl", bootstrap.ACL_SQL),
            ("defaults", bootstrap.DEFAULT_ACL_0023_SQL),
        )
    }


async def original_tails(conn):
    return {
        name: tuple((await conn.execute(text(f'SELECT last_value,is_called FROM "{name}"'))).one())  # noqa: S608
        for name in (
            "users_id_seq",
            "accounts_id_seq",
            "auth_sessions_id_seq",
            "refresh_tokens_id_seq",
            "holdings_id_seq",
            "trades_id_seq",
        )
    }


async def admin_bootstrap(*, apply):
    """Real administrator script, credentials on stdin, exact disposable lane."""
    url = make_url(test_migration_url())
    assert url.database == "birja_test"
    password = url.password
    assert password and all(char in "0123456789abcdef" for char in password)
    runtime_password = secrets.token_hex(32)
    source = "\n".join(
        (
            "\\set ON_ERROR_STOP on",
            "\\set bootstrap birja_test",
            "\\set db_name birja_test",
            "\\set apply " + ("true" if apply else "false"),
            "\\set app_password '" + runtime_password + "'",
            "\\set scheduler_password '" + runtime_password + "'",
            "\\set migrator_password '" + password + "'",
            (Path(__file__).parents[2] / "deploy/db/bootstrap-roles.sql").read_text(),
        )
    )
    result = await asyncio.to_thread(
        subprocess.run,
        [
            "/usr/bin/docker",
            "exec",
            "-i",
            "birja-test-postgres-1",
            "psql",
            "-X",
            "-U",
            "birja_test",
            "-d",
            "birja_test",
        ],
        input=source,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode, result.stderr.replace(password, "[redacted]").replace(
        runtime_password, "[redacted]"
    )


async def assert_preserved(conn, before, tails):
    after = await economic_snapshot(conn)
    assert {table: after[table] for table in before} == before
    assert all(not rows for table, rows in after.items() if table not in before)
    assert await original_tails(conn) == tails
    for table in ("holdings", "trades"):
        assert await conn.scalar(
            text(
                f"SELECT bool_and(t.portfolio_id=a.id) FROM {table} t "  # noqa: S608
                "JOIN accounts a ON a.user_id=t.user_id"
            )
        )


@pytest.mark.parametrize("normalizer", ["python", "admin"])
async def test_configured0008_to0023_preserves_books_and_accepts_final_bootstrap(
    portfolio_migration_db,
    normalizer,
):
    await migrate_to("0008")
    async with portfolio_migration_db.begin() as admin:
        assert await admin.scalar(text("SELECT current_database()")) == "birja_test"
        await sql(
            admin,
            "ALTER SCHEMA public OWNER TO pg_database_owner; "
            "REVOKE CREATE ON SCHEMA public FROM PUBLIC,birja_app,birja_scheduler; "
            "GRANT USAGE ON SCHEMA public TO birja_migrator,birja_app,birja_scheduler; "
            "GRANT CREATE ON SCHEMA public TO birja_migrator;",
        )
    child = create_async_engine(test_migration_url())
    try:
        async with child.begin() as conn:
            await sql(conn, CONFIGURED_0008_GRANTS)
            for number, cash in enumerate(("8765.43", "123.45")):
                uid = await conn.scalar(
                    text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                    {"e": f"configured0008-{number}@example.test"},
                )
                await conn.execute(
                    text("INSERT INTO accounts(user_id,cash,starting_cash) VALUES (:u,:c,12500)"),
                    {"u": uid, "c": Decimal(cash)},
                )
                coin = await conn.scalar(text("SELECT id FROM coins WHERE symbol='BTC'"))
                await conn.execute(
                    text(
                        "INSERT INTO holdings(user_id,coin_id,quantity,cost_basis) "
                        "VALUES (:u,:c,0.00123456,123.46)"
                    ),
                    {"u": uid, "c": coin},
                )
                await conn.execute(
                    text("""INSERT INTO trades
                    (user_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
                     exec_price,fee,cash_delta,cash_after,idempotency_key)
                    VALUES (:u,:c,'buy','quantity',0.00123456,0.00123456,99900,
                     TIMESTAMPTZ '2026-10-01 12:00:00+00',100000,0,-123.46,:cash,:key)"""),
                    {"u": uid, "c": coin, "cash": Decimal(cash), "key": uuid4()},
                )
            before = await economic_snapshot(conn)
            tails = await original_tails(conn)
            assert await require_migrator(conn) == "0008"
            print("configured0008_entry=" + json.dumps(await authority(conn), sort_keys=True))
        await migrate_to("0023")
        async with child.connect() as conn:
            state = await authority(conn)
            print("configured0008_after=" + json.dumps(state, sort_keys=True))
            assert state["catalogue"] == bootstrap.CATALOGUE_0023_SHA256
            assert state["defaults"] == bootstrap.DEFAULT_ACL_0023_SHA256
            assert state["acl"] == (
                "b4d138c09ace93ff69484b1b2932a667b17a19ce453a5623cae861e3e5a6ad62"
            )
            after = await economic_snapshot(conn)
            assert {table: after[table] for table in before} == before
            assert all(not rows for table, rows in after.items() if table not in before)
            assert await original_tails(conn) == tails
            assert await conn.scalar(
                text("""SELECT bool_and(h.portfolio_id=a.id)
                FROM holdings h JOIN accounts a ON a.user_id=h.user_id""")
            )
            assert await conn.scalar(
                text("""SELECT bool_and(t.portfolio_id=a.id)
                FROM trades t JOIN accounts a ON a.user_id=t.user_id""")
            )
            projection = "SELECT coalesce(jsonb_agg(v ORDER BY v::text),'[]') FROM ("
            projection += bootstrap.ACL_SQL.split("FROM (", 1)[1]
            permissions = await conn.scalar(text(projection))
            assert len(permissions) == 129
            assert all(row[-1] is False for row in permissions)
            print("configured0008_permission_count=" + str(len(permissions)))
            # The released implementation refuses here despite admitting0008.
            try:
                await conn.execute(text(bootstrap.PREFLIGHT_0023_SQL))
            except DBAPIError:
                await conn.rollback()
                assert await authority(conn) == state
                after = await economic_snapshot(conn)
                assert {table: after[table] for table in before} == before
                assert await original_tails(conn) == tails
                print("configured0008_refusal_preserves_rows_tails_authority=true")
                raise
        code, diagnostic = await admin_bootstrap(apply=False)
        assert code == 0, diagnostic
        # Commit each benign mismatch so both independent gates see the same
        # catalogue; refused bootstrap must preserve its diagnostic evidence.
        for damage, undo in (
            (
                "GRANT SELECT ON accounts TO birja_action_operator",
                "REVOKE SELECT ON accounts FROM birja_action_operator",
            ),
            ("REVOKE SELECT ON prices FROM birja_app", "GRANT SELECT ON prices TO birja_app"),
            (
                "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator "
                "GRANT EXECUTE ON FUNCTIONS TO PUBLIC",
                "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator "
                "REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC",
            ),
            (
                "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator IN SCHEMA public "
                "GRANT SELECT ON TABLES TO birja_app",
                "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator IN SCHEMA public "
                "REVOKE SELECT ON TABLES FROM birja_app",
            ),
        ):
            async with child.begin() as conn:
                await sql(conn, damage)
            try:
                async with child.connect() as conn:
                    damaged = await authority(conn)
                    with pytest.raises(DBAPIError):
                        async with conn.begin_nested():
                            await conn.execute(text(bootstrap.PREFLIGHT_0023_SQL))
                    assert await authority(conn) == damaged
                    await assert_preserved(conn, before, tails)
                code, diagnostic = await admin_bootstrap(apply=True)
                assert code != 0 and ("privileges" in diagnostic or "defaults" in diagnostic)
                async with child.connect() as conn:
                    assert await authority(conn) == damaged
                    await assert_preserved(conn, before, tails)
            finally:
                async with child.begin() as conn:
                    await sql(conn, undo)
        for _ in range(2):
            if normalizer == "admin":
                code, diagnostic = await admin_bootstrap(apply=True)
                assert code == 0, diagnostic
            else:
                async with child.begin() as conn:
                    await conn.execute(text(bootstrap.PREFLIGHT_0023_SQL))
                    await sql(conn, bootstrap.GRANTS_0023_SQL)
            async with child.connect() as conn:
                assert await authority(conn) == {
                    "catalogue": bootstrap.CATALOGUE_0023_SHA256,
                    "acl": bootstrap.ACL_0023_SHA256,
                    "defaults": bootstrap.DEFAULT_ACL_0023_SHA256,
                }
                assert await require_schema(conn) == "0023"
                assert await require_migrator(conn) == "0023"
                await assert_preserved(conn, before, tails)
    finally:
        await child.dispose()
