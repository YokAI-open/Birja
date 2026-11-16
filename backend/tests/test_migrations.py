import asyncio
import io
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from tests.helpers import unique_email

BACKEND_DIR = Path(__file__).resolve().parent.parent
EXPECTED_HEAD = "0014"

# Fixed application inventory: never REASSIGN OWNED or transfer arbitrary objects.
MIGRATION_TABLES = frozenset(
    {
        "alembic_version",
        "users",
        "accounts",
        "coins",
        "prices",
        "holdings",
        "trades",
        "auth_sessions",
        "refresh_tokens",
        "stock_instruments",
        "stock_quotes",
        "stock_sessions",
        "stock_data_admissions",
        "stock_action_events",
        "stock_action_sources",
        "stock_action_revisions",
        "stock_action_observations",
        "stock_action_state",
        "stock_split_applications",
        "stock_ownership_movements",
        "stock_dividend_entitlements",
        "stock_action_resolutions",
        "stock_fill_facts",
        "stock_status_evidence",
        "stock_dividend_payments",
        "stock_dividend_decisions",
        "portfolio_stock_closures",
    }
)
MIGRATION_FUNCTIONS = frozenset(
    {
        "reject_stock_action_mutation()",
        "reject_stock_record_mutation()",
        "reject_stock_dividend_mutation()",
        "check_stock_fill_integrity()",
        "assert_stock_execution_current(bigint,bigint,jsonb)",
        "apply_stock_action_resolution(bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text)",
        "stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb)",
        "apply_stock_dividend(bigint,bigint,text,text)",
        "record_stock_dividend_hold(bigint,text)",
        "associate_legacy_portfolio_only()",
    }
)
_MIGRATOR_PASSWORD = secrets.token_hex(32)

_MIGRATION_CHILD = """
import json, sys
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import DBAPIError
try:
    getattr(command, sys.argv[1])(Config('alembic.ini'), sys.argv[2])
except Exception as exc:
    print(json.dumps({'database': isinstance(exc, DBAPIError),
        'message': str(exc), 'sqlstate': getattr(getattr(exc, 'orig', None), 'sqlstate', None)}))
    sys.exit(1)
"""


class MigrationDatabaseError(RuntimeError):
    def __init__(self, message: str, sqlstate: str | None):
        super().__init__(message)
        self.sqlstate = sqlstate


def test_migration_url(database_url: str | None = None, redis_url: str | None = None) -> str:
    """A private in-memory child DSN; reject even otherwise valid alternate test DBs."""
    from tests.guard import ensure_test_stack

    database_url = database_url or os.environ["DATABASE_URL"]
    redis_url = redis_url or os.environ["REDIS_URL"]
    ensure_test_stack(database_url, redis_url)
    url = make_url(database_url)
    if url.username != "birja_test" or url.database != "birja_test" or url.query:
        raise RuntimeError("migration bootstrap requires exact disposable test admin")
    return url.set(username="birja_migrator", password=_MIGRATOR_PASSWORD).render_as_string(
        hide_password=False
    )


test_migration_url.__test__ = False


def run_test_migration(target: str, *, down: bool = False) -> None:
    """Authenticate a fresh interpreter; never mutate parent Settings or environment."""
    child_env = {**os.environ, "DATABASE_URL": test_migration_url(), "ENV": "test"}
    result = subprocess.run(  # noqa: S603 - fixed local interpreter, no shell
        [
            sys.executable,
            "-c",
            _MIGRATION_CHILD,
            "downgrade" if down else "upgrade",
            target,
        ],
        cwd=BACKEND_DIR,
        env=child_env,
        text=True,
        capture_output=True,
        timeout=120,
    )
    if result.returncode:
        # Child diagnostics may include connection arguments; redact the in-memory credential.
        detail = (
            json.loads(result.stdout)
            if result.stdout.strip()
            else {"message": result.stderr, "database": False}
        )
        message = detail["message"].replace(_MIGRATOR_PASSWORD, "[redacted]")
        if detail["database"]:
            raise DBAPIError(None, None, MigrationDatabaseError(message, detail.get("sqlstate")))
        raise RuntimeError(message)


async def ensure_dividend_test_owner() -> None:
    """Only guarded disposable DB administration, no production provisioning."""
    url = os.environ["DATABASE_URL"]
    test_migration_url(url)
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            assert (
                await conn.execute(
                    text(
                        "SELECT current_database()='birja_test' AND current_user='birja_test' "
                        "AND rolsuper FROM pg_roles WHERE rolname=current_user"
                    )
                )
            ).scalar_one()
            schema_owner = (
                await conn.execute(
                    text(
                        "SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname='public'"
                    )
                )
            ).scalar_one()
            if schema_owner not in {"birja_test", "birja_migrator", "pg_database_owner"}:
                raise RuntimeError("unexpected disposable migration schema owner")
            await conn.execute(
                text("""DO $test$ BEGIN
              IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='birja_migrator') THEN
                CREATE ROLE birja_migrator NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB
                  NOCREATEROLE NOREPLICATION NOBYPASSRLS;
              END IF;
              IF EXISTS(SELECT FROM pg_roles WHERE rolname='birja_migrator' AND
                (rolinherit OR rolsuper OR rolcreatedb OR rolcreaterole
                 OR rolreplication OR rolbypassrls)) THEN
                RAISE EXCEPTION 'unsafe disposable migration owner'; END IF;
              IF EXISTS(SELECT FROM pg_auth_members WHERE
                member=(SELECT oid FROM pg_roles WHERE rolname='birja_migrator') OR
                roleid=(SELECT oid FROM pg_roles WHERE rolname='birja_migrator')) THEN
                RAISE EXCEPTION 'unsafe disposable migration membership'; END IF;
              IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='birja_action_operator') THEN
                CREATE ROLE birja_action_operator NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB
                  NOCREATEROLE NOREPLICATION NOBYPASSRLS;
              END IF;
            END $test$""")
            )
            # Validate every object before any ownership transfer. Index ownership follows tables.
            relations = (
                await conn.execute(
                    text("""SELECT c.relname,c.relkind::text,
                pg_get_userbyid(c.relowner) FROM pg_class c JOIN pg_namespace n
                ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','S')
                ORDER BY c.relkind,c.relname""")
                )
            ).all()
            for name, kind, owner in relations:
                allowed = (
                    MIGRATION_TABLES if kind == "r" else {f"{t}_id_seq" for t in MIGRATION_TABLES}
                )
                if name not in allowed or owner not in {"birja_test", "birja_migrator"}:
                    raise RuntimeError("unexpected disposable migration relation inventory")
            functions = (
                await conn.execute(
                    text("""SELECT p.oid::regprocedure::text,
                pg_get_userbyid(p.proowner) FROM pg_proc p JOIN pg_namespace n
                ON n.oid=p.pronamespace WHERE n.nspname='public'""")
                )
            ).all()
            for signature, owner in functions:
                if signature.replace(" ", "") not in MIGRATION_FUNCTIONS or owner not in {
                    "birja_test",
                    "birja_migrator",
                }:
                    raise RuntimeError("unexpected disposable migration function inventory")
            await conn.execute(text("GRANT USAGE,CREATE ON SCHEMA public TO birja_migrator"))
            # Password is generated as hex and never emitted or persisted outside the disposable DB.
            await conn.execute(
                text(
                    f"ALTER ROLE birja_migrator LOGIN PASSWORD '{_MIGRATOR_PASSWORD}'"  # noqa: S608
                )
            )
            for name, kind, _ in relations:
                if kind == "r":
                    await conn.execute(text(f'ALTER TABLE public."{name}" OWNER TO birja_migrator'))  # noqa: S608
            for name, kind, _ in relations:
                if kind == "S":
                    await conn.execute(
                        text(f'ALTER SEQUENCE public."{name}" OWNER TO birja_migrator')
                    )  # noqa: S608
            for signature, _ in functions:
                await conn.execute(
                    text(f"ALTER FUNCTION public.{signature} OWNER TO birja_migrator")
                )  # noqa: S608
    finally:
        await engine.dispose()


def _config() -> Config:
    return Config(str(BACKEND_DIR / "alembic.ini"))


async def _versions(engine: AsyncEngine) -> list[str]:
    try:
        async with engine.connect() as conn:
            rows = await conn.execute(text("SELECT version_num FROM alembic_version"))
            return [r[0] for r in rows]
    except ProgrammingError:
        return []


async def test_upgrade_downgrade_roundtrip(engine: AsyncEngine) -> None:
    # Alembic's async env.py calls asyncio.run, so run it in a worker thread
    # with no running loop; the session loop is never touched.
    await asyncio.to_thread(run_test_migration, "head")
    assert await _versions(engine) == [EXPECTED_HEAD]

    await asyncio.to_thread(run_test_migration, "base", down=True)
    assert await _versions(engine) == []

    await asyncio.to_thread(run_test_migration, "head")
    assert await _versions(engine) == [EXPECTED_HEAD]


def test_baseline_is_head() -> None:
    script = ScriptDirectory.from_config(_config())
    assert script.get_heads() == [EXPECTED_HEAD]


async def test_populated_history_index_roundtrip(engine: AsyncEngine) -> None:
    await asyncio.to_thread(run_test_migration, "head")
    await asyncio.to_thread(run_test_migration, "0007", down=True)

    async def snapshot():
        async with engine.connect() as conn:
            rows = []
            for query in (
                "SELECT * FROM users ORDER BY id",
                "SELECT * FROM accounts ORDER BY id",
                "SELECT * FROM holdings ORDER BY id",
                "SELECT * FROM trades ORDER BY id",
            ):
                rows.append((await conn.execute(text(query))).all())
            # Compare the original financial rules. Successor0011 adds a
            # composite causal key and0013 adds a stock-only constraint trigger.
            # Their separate successor tests verify both; retain the original
            # crypto financial CHECK/FK comparison at the history-index boundary.
            constraints = (
                await conn.execute(
                    text("""SELECT conrelid::regclass::text, conname,
                pg_get_constraintdef(oid) FROM pg_constraint
                WHERE conrelid IN ('accounts'::regclass, 'holdings'::regclass, 'trades'::regclass)
                  AND conname <> 'uq_trades_id_coin_user'
                  AND NOT (contype='t' AND conname='stock_fill_integrity')
                ORDER BY conrelid, conname""")
                )
            ).all()
            return rows, constraints

    try:
        async with engine.begin() as conn:
            uid = (
                await conn.execute(
                    text("INSERT INTO users (email) VALUES (:e) RETURNING id"),
                    {"e": unique_email("history-index")},
                )
            ).scalar_one()
            cid = (
                await conn.execute(text("SELECT id FROM coins WHERE symbol = 'BTC'"))
            ).scalar_one()
            await conn.execute(
                text("""INSERT INTO accounts (user_id, cash, starting_cash)
                VALUES (:u, 9800, 10000)"""),
                {"u": uid},
            )
            await conn.execute(
                text("""INSERT INTO holdings (user_id, coin_id, quantity, cost_basis)
                VALUES (:u, :c, 2, 200)"""),
                {"u": uid, "c": cid},
            )
            await conn.execute(
                text("""INSERT INTO trades
                (user_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
                 exec_price,fee,cash_delta,cash_after,idempotency_key)
                SELECT :u,:c,'buy','quantity',1,1,99.75,now(),99.75,0.25,-100,
                       10000 - n * 100,gen_random_uuid() FROM generate_series(1,2) AS n"""),
                {"u": uid, "c": cid},
            )
        before = await snapshot()
        await asyncio.to_thread(run_test_migration, "0008")
        assert await _versions(engine) == ["0008"]
        async with engine.connect() as conn:
            index = (
                await conn.execute(
                    text("""SELECT indisvalid, indisready,
                pg_get_indexdef(indexrelid), ARRAY(
                  SELECT a.attname FROM unnest(i.indkey) WITH ORDINALITY AS k(attnum, pos)
                  JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = k.attnum
                  ORDER BY k.pos)
                FROM pg_index i WHERE indexrelid = 'ix_trades_user_created_id'::regclass""")
                )
            ).one()
        assert index[0] is True and index[1] is True
        assert (
            index[2] == "CREATE INDEX ix_trades_user_created_id ON public.trades "
            "USING btree (user_id, created_at, id)"
        )
        assert index[3] == ["user_id", "created_at", "id"]
        assert await snapshot() == before
        await asyncio.to_thread(run_test_migration, "0007", down=True)
        assert await _versions(engine) == ["0007"]
        async with engine.connect() as conn:
            assert (
                await conn.execute(text("SELECT to_regclass('ix_trades_user_created_id')"))
            ).scalar_one() is None
        assert await snapshot() == before
        await asyncio.to_thread(run_test_migration, "head")
        assert await _versions(engine) == [EXPECTED_HEAD]
        assert await snapshot() == before
    finally:
        await asyncio.to_thread(run_test_migration, "head")


def test_history_index_offline_transactions() -> None:
    output = io.StringIO()
    cfg = _config()
    cfg.output_buffer = output
    command.upgrade(cfg, "0007:0008", sql=True)
    sql = output.getvalue()
    assert (
        "CREATE INDEX CONCURRENTLY ix_trades_user_created_id ON trades (user_id, created_at, id)"
        in sql
    )
    assert sql.index("COMMIT;") < sql.index("CREATE INDEX CONCURRENTLY") < sql.rindex("BEGIN;")
    output.seek(0)
    output.truncate()
    command.downgrade(cfg, "0008:0007", sql=True)
    sql = output.getvalue()
    assert "DROP INDEX CONCURRENTLY ix_trades_user_created_id" in sql
    assert sql.index("COMMIT;") < sql.index("DROP INDEX CONCURRENTLY") < sql.rindex("BEGIN;")


async def test_earlier_revision_commits_before_later_guard_failure(engine: AsyncEngine) -> None:
    await asyncio.to_thread(run_test_migration, "head")
    await asyncio.to_thread(run_test_migration, "0005", down=True)
    try:
        async with engine.begin() as conn:
            uid = (
                await conn.execute(
                    text("INSERT INTO users (email) VALUES (:e) RETURNING id"),
                    {"e": unique_email("per-revision")},
                )
            ).scalar_one()
            await conn.execute(
                text("""INSERT INTO accounts (user_id, cash, starting_cash)
                VALUES (:u, 1.005, 10000)"""),
                {"u": uid},
            )
        with pytest.raises(RuntimeError, match="sub-cent cash"):
            await asyncio.to_thread(run_test_migration, "head")
        # 0006 must stay committed even though 0007's validation failed.
        assert await _versions(engine) == ["0006"]
        async with engine.connect() as conn:
            assert (
                await conn.execute(text("SELECT to_regclass('trades')"))
            ).scalar_one() == "trades"
    finally:
        async with engine.begin() as conn:
            await conn.execute(text("DELETE FROM accounts WHERE cash != round(cash, 2)"))
        await asyncio.to_thread(run_test_migration, "head")


async def test_cents_migration_refuses_sub_cent_cash(engine: AsyncEngine) -> None:
    email = unique_email("subcent")
    await asyncio.to_thread(run_test_migration, "head")
    await asyncio.to_thread(run_test_migration, "0006", down=True)
    try:
        async with engine.begin() as conn:
            user_id = (
                await conn.execute(
                    text("INSERT INTO users (email) VALUES (:e) RETURNING id"), {"e": email}
                )
            ).scalar_one()
            await conn.execute(
                text(
                    "INSERT INTO accounts (user_id, cash, starting_cash) VALUES (:u, 1.005, 10000)"
                ),
                {"u": user_id},
            )
        with pytest.raises(RuntimeError, match="sub-cent cash"):
            await asyncio.to_thread(run_test_migration, "0007")
        assert await _versions(engine) == ["0006"]
        async with engine.begin() as conn:
            await conn.execute(text("DELETE FROM accounts WHERE user_id = :u"), {"u": user_id})
            await conn.execute(text("DELETE FROM users WHERE id = :u"), {"u": user_id})
        await asyncio.to_thread(run_test_migration, "0007")
        assert await _versions(engine) == ["0007"]
    finally:
        async with engine.begin() as conn:
            await conn.execute(text("DELETE FROM accounts WHERE cash != round(cash, 2)"))
        await asyncio.to_thread(run_test_migration, "head")


async def test_models_match_schema(engine: AsyncEngine) -> None:
    await asyncio.to_thread(run_test_migration, "head")

    def _diff(sync_conn):  # type: ignore[no-untyped-def]
        ctx = MigrationContext.configure(sync_conn, opts={"compare_type": True})
        return compare_metadata(ctx, Base.metadata)

    async with engine.connect() as conn:
        diff = await conn.run_sync(_diff)
    assert diff == []
