"""Explicit migration-only harness; never admit the current app at0018/19."""

import asyncio
from decimal import Decimal
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from tests.portfolio_fixtures import reset_disposable_schema
from tests.test_migrations import run_test_migration, test_migration_url

BACKEND = Path(__file__).resolve().parents[1]


async def migrate(revision, *, down=False):
    assert revision in {"0014", "0017", "0018", "0019"}
    await asyncio.to_thread(run_test_migration, revision, down=down)


@pytest_asyncio.fixture
async def staged(engine):
    await reset_disposable_schema(engine)
    migration_engine = create_async_engine(test_migration_url())
    try:
        yield migration_engine
    finally:
        await migration_engine.dispose()
        # Drop only the guarded disposable schema. No shared head fixture: head
        # is intentionally a migration-only revision during this plan.
        await reset_disposable_schema(engine)


async def user(conn):
    return (
        await conn.execute(
            text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
            {"e": f"management-{uuid4()}@example.test"},
        )
    ).scalar_one()


async def account(conn, owner, name="My portfolio", *, closed=False):
    return (
        await conn.execute(
            text("""INSERT INTO accounts
        (user_id,name,cash,starting_cash,closed_at) VALUES (:u,:n,8765.43,12500,
        CASE WHEN :closed THEN clock_timestamp() ELSE NULL END) RETURNING id"""),
            {"u": owner, "n": name, "closed": closed},
        )
    ).scalar_one()


async def rejected(conn, sql, params=None, state="23514"):
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await conn.execute(text(sql), params or {})
    assert error.value.orig.sqlstate == state


def test_registered_metadata_models():
    from app.models import Account, PortfolioCreation, PortfolioInitialization

    assert Account.__table__.c.description.server_default.arg == ""
    assert not Account.__table__.c.name_key.nullable
    assert Account.__table__.c.name_key.type.collation == "C"
    for model in (PortfolioCreation, PortfolioInitialization):
        assert model.__table__.c.id.identity.always
        assert model.__table__.c.created_at.type.timezone
        assert all(fk.ondelete != "CASCADE" for fk in model.__table__.foreign_keys)
    assert PortfolioCreation.__table__.c.amount.type.scale == 8


@pytest.mark.asyncio
async def test_expansion_preserves_money_and_adds_only_empty_metadata(staged):
    await migrate("0017")
    async with staged.begin() as conn:
        owner = await user(conn)
        root = await account(conn, owner)
        before = (await conn.execute(text("SELECT to_jsonb(a)::text FROM accounts a"))).all()
    await migrate("0018")
    async with staged.begin() as conn:
        assert (
            await conn.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one() == "0018"
        assert (
            await conn.execute(
                text("SELECT (to_jsonb(a)-'description'-'name_key')::text FROM accounts a")
            )
        ).all() == before
        assert (
            await conn.execute(
                text("SELECT description,name_key FROM accounts WHERE id=:p"), {"p": root}
            )
        ).one() == ("", None)
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_initializations"))
        ).scalar_one() == 0
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_creations"))
        ).scalar_one() == 0
        foreign = await user(conn)
        await rejected(
            conn,
            """INSERT INTO portfolio_creations
            (user_id,creation_key,portfolio_id,origin,payload_version,canonical_payload,amount)
            VALUES (:u,:k,:p,'explicit',1,'{"name":"My portfolio","description":""}',10000)""",
            {"u": foreign, "k": uuid4(), "p": root},
            "23503",
        )
        for amount in (Decimal("9999"), Decimal("10000.00000001"), Decimal("NaN")):
            await rejected(
                conn,
                """INSERT INTO portfolio_creations
                (user_id,creation_key,portfolio_id,origin,payload_version,canonical_payload,amount)
                VALUES (:u,:k,:p,'explicit',1,'{"name":"My portfolio","description":""}',:a)""",
                {"u": owner, "k": uuid4(), "p": root, "a": amount},
            )
        await rejected(
            conn,
            """INSERT INTO portfolio_initializations
            (user_id,origin,portfolio_id) VALUES (:u,'legacy',:p)""",
            {"u": owner, "p": root},
        )


@pytest.mark.asyncio
async def test_expansion_refuses_downgrade_before_dropping_evidence(staged):
    await migrate("0018")
    async with staged.begin() as conn:
        owner = await user(conn)
        await conn.execute(
            text("INSERT INTO portfolio_initializations(user_id,origin) VALUES (:u,'legacy')"),
            {"u": owner},
        )
    with pytest.raises(RuntimeError, match="downgrade refused"):
        await migrate("0017", down=True)
    async with staged.connect() as conn:
        assert (
            await conn.execute(text("SELECT user_id,origin FROM portfolio_initializations"))
        ).one() == (owner, "legacy")
        assert (
            await conn.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one() == "0018"


def test_expansion_is_not_a_runtime_schema():
    # Exact admission also has DB-backed coverage below once0019 exists. Source
    # inventory must remain0017 throughout this partial migration plan.
    assert (BACKEND / "alembic/versions/0018_portfolio_management_expansion.py").is_file()
    module = import_module("app.db.schema_contract")
    assert all("0018" not in revisions for revisions in module.SUPPORTED.values())


def backfill_module():
    path = BACKEND / "alembic/versions/0019_portfolio_management_backfill.py"
    spec = spec_from_file_location("management_backfill", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def run_upgrade(conn, module):
    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext

    def upgrade(sync):
        context = MigrationContext.configure(sync, opts={"transaction_per_migration": True})
        with Operations.context(context), context.begin_transaction():
            module.upgrade()

    await conn.run_sync(upgrade)


async def snapshot(conn):
    # Independent full legacy table/row inventory, including oldmetadata, every
    # stored decimal/timestamp/json field. Only the two additive columns differ.
    tables = (
        await conn.execute(
            text(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename NOT IN ('alembic_version','portfolio_creations','portfolio_initializations') ORDER BY tablename"
            )
        )
    ).scalars()
    return {
        table: (
            await conn.execute(
                text(
                    f"SELECT (to_jsonb(t)-'description'-'name_key')::text FROM public.{table} t ORDER BY to_jsonb(t)::text"  # noqa: S608 - catalogue from guarded disposable schema
                )
            )
        )
        .scalars()
        .all()
        for table in tables
    }


@pytest.mark.asyncio
async def test_populated_legacy_and_zero_book_preserve_all_financial_evidence(staged):
    from tests.portfolio_fixtures import seed_legacy_books

    await migrate("0014")
    async with staged.begin() as conn:
        await seed_legacy_books(conn)
    await migrate("0017")
    async with staged.begin() as conn:
        empty = await user(conn)
        ended = await user(conn)
        await account(conn, ended, "Ended", closed=True)
        before = await snapshot(conn)
        users = (await conn.execute(text("SELECT id FROM users ORDER BY id"))).scalars().all()
    await migrate("0019")
    async with staged.begin() as conn:
        assert await snapshot(conn) == before
        assert (
            await conn.execute(
                text(
                    "SELECT user_id,origin,portfolio_id,creation_id FROM portfolio_initializations ORDER BY user_id"
                )
            )
        ).all() == [(u, "legacy", None, None) for u in users]
        assert empty in users and ended in users
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_creations"))
        ).scalar_one() == 0
        assert (
            await conn.execute(
                text("SELECT count(*) FROM accounts WHERE description<>'' OR name_key IS NULL")
            )
        ).scalar_one() == 0
        from app.db.schema_contract import SchemaAdmissionError, require_schema

        with pytest.raises(SchemaAdmissionError, match="incompatible_schema"):
            await require_schema(conn)
    with pytest.raises(RuntimeError, match="downgrade refused"):
        await migrate("0018", down=True)
    async with staged.connect() as conn:
        assert await snapshot(conn) == before
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_initializations"))
        ).scalar_one() == len(users)


@pytest.mark.asyncio
async def test_fresh_canonical_sql_corpus_constraints_and_active_uniqueness(staged):
    await migrate("0019")
    async with staged.begin() as conn:
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_initializations"))
        ).scalar_one() == 0
        # Outputs fixed independently; no Python casefold or SQL-produced oracle.
        for raw, display, key in (
            ("\u00a0Straße\u3000", "Straße", "strasse"),
            ("e\u0301", "é", "é"),
            ("ΟΣ", "ΟΣ", "οσ"),
            ("ς", "ς", "σ"),
            ("İ", "İ", "i\u0307"),
            ("A\u200bB", "A\u200bB", "a\u200bb"),
            ("🦊" * 60, "🦊" * 60, "🦊" * 60),
        ):
            assert (
                await conn.execute(
                    text("SELECT public.portfolio_display_name(:n),public.portfolio_name_key(:n)"),
                    {"n": raw},
                )
            ).one() == (display, key)
        for code in [*range(1, 32), *range(127, 160)]:
            await rejected(
                conn, "SELECT public.portfolio_display_name(:n)", {"n": chr(code) + "Name"}, "22023"
            )
        for raw in ("", "\u2003 \u3000", "a" * 61, "🦊" * 61):
            await rejected(conn, "SELECT public.portfolio_display_name(:n)", {"n": raw}, "22023")
        for raw in ("", " \tline\r\nnext\rlast \n", "🦊" * 1000):
            expected = raw.replace("\r\n", "\n").replace("\r", "\n")
            assert (
                await conn.execute(text("SELECT public.portfolio_description(:d)"), {"d": raw})
            ).scalar_one() == expected
        for raw in ("a" * 1001, "\u0085", "\v", "\x1f"):
            await rejected(conn, "SELECT public.portfolio_description(:d)", {"d": raw}, "22023")
        for helper in ("portfolio_display_name", "portfolio_name_key", "portfolio_description"):
            await rejected(conn, f"SELECT public.{helper}(NULL)", state="22023")
        owner, other = await user(conn), await user(conn)

        async def insert(u, n, k, closed=False, d=""):
            return await conn.execute(
                text("""INSERT INTO accounts(user_id,name,name_key,description,cash,starting_cash,closed_at)
                VALUES (:u,:n,:k,:d,10000,10000,CASE WHEN :closed THEN now() ELSE NULL END) RETURNING id"""),
                {"u": u, "n": n, "k": k, "d": d, "closed": closed},
            )

        root = (await insert(owner, "Straße", "strasse")).scalar_one()
        await insert(other, "STRASSE", "strasse")
        await insert(owner, "STRASSE", "strasse", True)
        await rejected(
            conn,
            """INSERT INTO accounts(user_id,name,name_key,cash,starting_cash)
            VALUES (:u,'STRASSE','strasse',10000,10000)""",
            {"u": owner},
            "23505",
        )
        for field, value in (("name", " padded "), ("name_key", "forged"), ("description", "\r")):
            await rejected(
                conn, f"UPDATE accounts SET {field}=:v WHERE id=:p", {"v": value, "p": root}
            )
        await rejected(conn, "UPDATE accounts SET starting_cash=1 WHERE id=:p", {"p": root})
        assert (
            await conn.execute(text("SELECT starting_cash FROM accounts WHERE id=:p"), {"p": root})
        ).scalar_one() == Decimal("10000")
        # Immutable canonical grant evidence: exact scalar fields, origin linkage,
        # UUIDv4 and durable owner/key/root identity are validated by the schema.
        key = uuid4()
        creation = (
            await conn.execute(
                text("""INSERT INTO portfolio_creations
            (user_id,creation_key,portfolio_id,origin,payload_version,canonical_payload,amount)
            VALUES (:u,:k,:p,'initial',1,'{"name":"Straße","description":""}',10000) RETURNING id"""),
                {"u": owner, "k": key, "p": root},
            )
        ).scalar_one()
        await conn.execute(
            text("""INSERT INTO portfolio_initializations
            (user_id,origin,portfolio_id,creation_id) VALUES (:u,'initial',:p,:c)"""),
            {"u": owner, "p": root, "c": creation},
        )
        for table in ("portfolio_creations", "portfolio_initializations"):
            await rejected(conn, f"DELETE FROM {table}")
            await rejected(conn, f"UPDATE {table} SET created_at=now()")
        for field, value in (("name", " p "), ("description", "\r")):
            payload = {"name": "Straße", "description": "", field: value}
            import json

            await rejected(
                conn,
                """INSERT INTO portfolio_creations
                (user_id,creation_key,portfolio_id,origin,payload_version,canonical_payload,amount)
                VALUES (:u,:k,:p,'explicit',1,CAST(:payload AS jsonb),10000)""",
                {"u": other, "k": uuid4(), "p": root, "payload": json.dumps(payload)},
            )


@pytest.mark.parametrize("bad_name", [" padded ", "e\u0301", "\tHidden", ""])
@pytest.mark.asyncio
async def test_noncanonical_legacy_names_refuse_before_any_backfill(staged, bad_name):
    await migrate("0018")
    async with staged.begin() as conn:
        owner = await user(conn)
        await account(conn, owner, bad_name)
        before = await snapshot(conn)
    with pytest.raises((RuntimeError, DBAPIError), match="legacy|name"):
        await migrate("0019")
    async with staged.connect() as conn:
        assert await snapshot(conn) == before
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_initializations"))
        ).scalar_one() == 0
        assert (
            await conn.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one() == "0018"


@pytest.mark.asyncio
async def test_duplicate_legacy_active_names_refuse_without_rename(staged):
    await migrate("0018")
    async with staged.begin() as conn:
        owner = await user(conn)
        await account(conn, owner, "Straße")
        await account(conn, owner, "STRASSE")
        before = await snapshot(conn)
    with pytest.raises(RuntimeError, match="duplicate"):
        await migrate("0019")
    async with staged.connect() as conn:
        assert await snapshot(conn) == before
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_initializations"))
        ).scalar_one() == 0


@pytest.mark.asyncio
async def test_source_checksum_refuses_before_writes(staged, monkeypatch):
    await migrate("0018")
    module = backfill_module()
    monkeypatch.setattr(module, "SQL_SHA256", "0" * 64)
    async with staged.connect() as conn:
        with pytest.raises(RuntimeError, match="checksum"):
            await run_upgrade(conn, module)
        assert (
            await conn.execute(
                text("SELECT to_regprocedure('public.portfolio_display_name(text)')")
            )
        ).scalar_one() is None


@pytest.mark.asyncio
async def test_bounded_committed_interruption_resume_and_original_guard_restored(
    staged, monkeypatch
):
    await migrate("0018")
    async with staged.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO users(email) SELECT 'batch-'||g||'@example.test' FROM generate_series(1,507) g"
            )
        )
        await conn.execute(
            text("""INSERT INTO accounts(user_id,name,cash,starting_cash,closed_at)
            SELECT id,'Book',123.45,7777,CASE WHEN id%2=0 THEN now() ELSE NULL END FROM users""")
        )
        before = await snapshot(conn)
    module = backfill_module()
    original = module._backfill_batch

    def interrupted(table):
        changed = original(table)
        if table == "users" and changed:
            assert changed == 500
            raise RuntimeError("synthetic committed interruption")
        return changed

    monkeypatch.setattr(module, "_backfill_batch", interrupted)
    async with staged.connect() as conn:
        with pytest.raises(RuntimeError, match="committed interruption"):
            await run_upgrade(conn, module)
    async with staged.connect() as conn:
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_initializations"))
        ).scalar_one() == 500
        assert await snapshot(conn) == before
        await conn.rollback()
    await migrate("0019")
    async with staged.begin() as conn:
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_initializations"))
        ).scalar_one() == 507
        assert (
            await conn.execute(text("SELECT count(*) FROM accounts WHERE name_key='book'"))
        ).scalar_one() == 507
        assert await snapshot(conn) == before
        assert (
            await conn.execute(
                text(
                    "SELECT p.proname FROM pg_trigger t JOIN pg_proc p ON p.oid=t.tgfoid WHERE tgrelid='accounts'::regclass AND tgname='portfolio_root_immutable'"
                )
            )
        ).scalar_one() == "check_portfolio_financial_write"
