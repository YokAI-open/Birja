"""Finite migration orchestration: trusted bytes, child failure and lock cleanup.

Subprocess/engine construction are isolated here. Authentication and catalogue
checks are separately exercised against PostgreSQL, never a fabricated ledger.
"""

import json
import runpy
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.db import portfolio_migrate as migration
from tests.portfolio_fixtures import migrate_to, portfolio_migration_db
from tests.test_migrations import test_migration_url

__all__ = ["portfolio_migration_db"]

URL = "postgresql+asyncpg://birja_migrator:synthetic@postgres:5432/birja"

PRIOR_OBJECT_DRIFT = [
    (
        "policy",
        "CREATE POLICY unexpected_review_policy ON accounts USING (true)",
        "SELECT EXISTS(SELECT FROM pg_policy WHERE polname='unexpected_review_policy')",
    ),
    (
        "view",
        "CREATE VIEW unexpected_review_view AS SELECT id FROM accounts",
        "SELECT to_regclass('public.unexpected_review_view') IS NOT NULL",
    ),
    (
        "materialized",
        "CREATE MATERIALIZED VIEW unexpected_review_materialized AS "
        "SELECT id FROM accounts WITH NO DATA",
        "SELECT to_regclass('public.unexpected_review_materialized') IS NOT NULL",
    ),
    (
        "foreign",
        "CREATE FOREIGN DATA WRAPPER review_cr01_fdw; "
        "CREATE SERVER review_cr01_server FOREIGN DATA WRAPPER review_cr01_fdw; "
        "CREATE FOREIGN TABLE unexpected_review_foreign(id bigint) SERVER review_cr01_server",
        "SELECT to_regclass('public.unexpected_review_foreign') IS NOT NULL",
    ),
    (
        "rule",
        "CREATE RULE unexpected_review_rule AS ON UPDATE TO accounts DO INSTEAD NOTHING",
        "SELECT EXISTS(SELECT FROM pg_rewrite WHERE rulename='unexpected_review_rule')",
    ),
    (
        "rls",
        "ALTER TABLE accounts ENABLE ROW LEVEL SECURITY",
        "SELECT relrowsecurity FROM pg_class WHERE oid='accounts'::regclass",
    ),
    (
        "force-rls",
        "ALTER TABLE accounts FORCE ROW LEVEL SECURITY",
        "SELECT relforcerowsecurity FROM pg_class WHERE oid='accounts'::regclass",
    ),
    (
        "partitioned",
        "CREATE TABLE unexpected_review_partitioned(id bigint) PARTITION BY RANGE(id)",
        "SELECT to_regclass('public.unexpected_review_partitioned') IS NOT NULL",
    ),
    (
        "type",
        "CREATE TYPE unexpected_review_enum AS ENUM ('a')",
        "SELECT to_regtype('public.unexpected_review_enum') IS NOT NULL",
    ),
    (
        "collation",
        'CREATE COLLATION unexpected_review_collation FROM pg_catalog."C"',
        "SELECT EXISTS(SELECT FROM pg_collation WHERE collname='unexpected_review_collation')",
    ),
    (
        "operator",
        "CREATE OPERATOR public.=== (FUNCTION=pg_catalog.int8eq,LEFTARG=bigint,RIGHTARG=bigint)",
        "SELECT EXISTS(SELECT FROM pg_operator WHERE oprnamespace='public'::regnamespace "
        "AND oprname='===')",
    ),
    (
        "statistics",
        "CREATE STATISTICS unexpected_review_statistics ON user_id,cash FROM accounts",
        "SELECT EXISTS(SELECT FROM pg_statistic_ext WHERE stxname='unexpected_review_statistics')",
    ),
    (
        "unlogged",
        "ALTER TABLE prices SET UNLOGGED",
        "SELECT relpersistence='u' FROM pg_class WHERE oid='prices'::regclass",
    ),
    (
        "composite",
        "CREATE TYPE unexpected_review_composite AS (id bigint)",
        "SELECT to_regtype('public.unexpected_review_composite') IS NOT NULL",
    ),
    (
        "conversion",
        "CREATE CONVERSION unexpected_review_conversion FOR 'UTF8' TO 'LATIN1' "
        "FROM pg_catalog.utf8_to_iso8859_1",
        "SELECT EXISTS(SELECT FROM pg_conversion WHERE conname='unexpected_review_conversion')",
    ),
    (
        "opclass-family",
        "CREATE OPERATOR CLASS public.unexpected_review_opclass FOR TYPE bigint USING btree AS "
        "OPERATOR 1 <(bigint,bigint), OPERATOR 2 <=(bigint,bigint), "
        "OPERATOR 3 =(bigint,bigint), OPERATOR 4 >=(bigint,bigint), "
        "OPERATOR 5 >(bigint,bigint), FUNCTION 1 pg_catalog.btint8cmp(bigint,bigint)",
        "SELECT EXISTS(SELECT FROM pg_opclass WHERE opcname='unexpected_review_opclass')",
    ),
    (
        "extension",
        # Package-free privileged drift fixture: the builtin extension is not
        # relocatable through DDL. Restore only this owned catalogue field after
        # asserting that application admission kept the hostile state intact.
        "UPDATE pg_extension SET extnamespace='public'::regnamespace WHERE extname='plpgsql'",
        "SELECT EXISTS(SELECT FROM pg_extension WHERE extname='plpgsql' "
        "AND extnamespace='public'::regnamespace)",
    ),
]


async def prior_object_evidence(admin, identity):
    from app.db.portfolio_bootstrap import CATALOGUE_0023_SQL, CATALOGUE_SQL
    from tests.portfolio_closure_fixtures import retained_snapshot

    async with admin.connect() as conn:
        revision = await conn.scalar(text("SELECT version_num FROM alembic_version"))
        rows = (
            await legacy14_snapshot(conn) if revision == "0014" else await retained_snapshot(conn)
        )
        for table in ("portfolio_lifecycle_closures", "portfolio_closure_intents"):
            if await conn.scalar(text("SELECT to_regclass(:t)"), {"t": "public." + table}):
                rows[table] = tuple(
                    (
                        await conn.execute(
                            text(f"SELECT to_jsonb(t)::text FROM {table} t ORDER BY id")  # noqa: S608
                        )
                    ).scalars()
                )
                rows[table + "_id_seq"] = tuple(
                    (
                        await conn.execute(
                            text(f"SELECT last_value,is_called FROM {table}_id_seq")  # noqa: S608
                        )
                    ).one()
                )
        return (
            await conn.scalar(text("SELECT version_num FROM alembic_version")),
            await conn.scalar(text(CATALOGUE_SQL)),
            await conn.scalar(text(CATALOGUE_0023_SQL)),
            rows,
            await conn.scalar(text(identity)),
        )


@pytest.mark.parametrize("revision", ["0014", "0020", "0021", "0022"])
@pytest.mark.parametrize(
    "kind,damage,identity", PRIOR_OBJECT_DRIFT, ids=[case[0] for case in PRIOR_OBJECT_DRIFT]
)
async def test_unrecognized_prior_objects_refuse_without_child_or_mutation(
    portfolio_migration_db, revision, kind, damage, identity
):
    from tests.test_portfolio_management_grants import sql

    child, _ = (
        await prepare_legacy14(portfolio_migration_db)
        if revision == "0014"
        else await prepare_pre_closure(portfolio_migration_db, revision)
    )
    foreign_created = False
    try:
        async with child.connect() as conn:
            assert await migration.require_migrator(conn) == revision
        async with portfolio_migration_db.begin() as admin:
            if kind == "foreign":
                assert not await admin.scalar(
                    text(
                        "SELECT EXISTS(SELECT FROM pg_foreign_data_wrapper "
                        "WHERE fdwname='review_cr01_fdw')"
                    )
                )
            await sql(admin, damage)
        foreign_created = kind == "foreign"
        before = await prior_object_evidence(portfolio_migration_db, identity)
        assert before[-1] is True
        # The first RED case is exactly the reviewer's disabled-policy gap.
        with pytest.raises(ValueError, match="Unrecognized"):
            async with child.connect() as conn:
                await migration.require_migrator(conn)
        with (
            patch.object(migration, "create_async_engine", return_value=child),
            patch.object(migration, "database_connect_args", return_value={}),
            patch.object(migration.asyncio, "create_subprocess_exec", AsyncMock()) as spawn,
        ):
            with pytest.raises(ValueError, match="Unrecognized"):
                await migration.migrate(SimpleNamespace(env="prod", database_url=URL))
            spawn.assert_not_awaited()
        after = await prior_object_evidence(portfolio_migration_db, identity)
        assert after == before
        assert after[-1] is True  # Keep the unrecognized object for diagnosis.
    finally:
        await child.dispose()
        if foreign_created:
            # Only test-owned cluster objects, after retention/no-mutation proof.
            async with portfolio_migration_db.begin() as admin:
                await sql(admin, "DROP FOREIGN DATA WRAPPER review_cr01_fdw CASCADE")
        if kind == "extension":
            async with portfolio_migration_db.begin() as admin:
                await sql(
                    admin,
                    "UPDATE pg_extension SET extnamespace='pg_catalog'::regnamespace "
                    "WHERE extname='plpgsql'",
                )


async def legacy14_snapshot(conn):
    from tests.test_migrations import MIGRATION_TABLES

    result = {}
    for table in sorted(MIGRATION_TABLES - {"alembic_version"}):
        if await conn.scalar(text("SELECT to_regclass(:t)"), {"t": "public." + table}):
            result[table] = tuple(
                (
                    await conn.execute(
                        text(
                            f'SELECT to_jsonb(t)::text FROM "{table}" t ORDER BY to_jsonb(t)::text'  # noqa: S608
                        )
                    )
                ).scalars()  # noqa: S608
            )
        sequence = table + "_id_seq"
        if await conn.scalar(text("SELECT to_regclass(:t)"), {"t": "public." + sequence}):
            result[sequence] = tuple(
                (await conn.execute(text(f'SELECT last_value,is_called FROM "{sequence}"'))).one()  # noqa: S608
            )
    return result


async def prepare_legacy14(engine, *, private=True):
    """Reproduce dev's real14 source before runtime principals are provisioned."""
    from tests.test_portfolio_management_grants import sql

    async with engine.begin() as admin:
        assert await admin.scalar(text("SELECT current_database()")) == "birja_test"
        # This is an empty owned test schema. It models a genuine old dev DB,
        # not a permission repair performed on an admitted application database.
        await sql(
            admin,
            "DROP OWNED BY birja_app,birja_scheduler; "
            "DROP ROLE birja_app; DROP ROLE birja_scheduler;",
        )
    await migrate_to("0014")
    async with engine.begin() as admin:
        await sql(
            admin,
            "CREATE ROLE birja_app NOLOGIN NOINHERIT; "
            "CREATE ROLE birja_scheduler NOLOGIN NOINHERIT; "
            "ALTER SCHEMA public OWNER TO pg_database_owner; "
            "GRANT USAGE ON SCHEMA public TO birja_app,birja_scheduler;",
        )
    child = create_async_engine(test_migration_url())
    async with child.begin() as conn:
        await sql(
            conn,
            "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator "
            + (
                "REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC"
                if private
                else "GRANT EXECUTE ON FUNCTIONS TO PUBLIC"
            ),
        )
        uid = await conn.scalar(
            text("INSERT INTO users(email) VALUES ('legacy14@example.test') RETURNING id")
        )
        root = await conn.scalar(
            text(
                "INSERT INTO accounts(user_id,cash,starting_cash) "
                "VALUES (:u,321.12,8765) RETURNING id"
            ),
            {"u": uid},
        )
    return child, root


@pytest.mark.parametrize("private", [False, True], ids=["builtin-default", "private-default"])
async def test_real_legacy14_entry_and_final_bootstrap_preserve_original_finances(
    portfolio_migration_db, private
):
    from app.db.portfolio_bootstrap import (
        ACL_SQL,
        CATALOGUE_0023_SQL,
        DEFAULT_ACL_0023_SQL,
        PREFLIGHT_0023_SQL,
    )

    child, root = await prepare_legacy14(portfolio_migration_db, private=private)
    try:
        async with child.connect() as conn:
            before = await legacy14_snapshot(conn)
            state = {
                key: await conn.scalar(text(query))
                for key, query in (
                    ("catalogue", CATALOGUE_0023_SQL),
                    ("acl", ACL_SQL),
                    ("defaults", DEFAULT_ACL_0023_SQL),
                )
            }
            print("legacy14_entry=" + json.dumps(state, sort_keys=True))
            assert await migration.require_migrator(conn) == "0014"
        await migrate_to("0023")
        async with child.connect() as conn:
            state = {
                key: await conn.scalar(text(query))
                for key, query in (
                    ("catalogue", CATALOGUE_0023_SQL),
                    ("acl", ACL_SQL),
                    ("defaults", DEFAULT_ACL_0023_SQL),
                )
            }
            print("legacy14_after=" + json.dumps(state, sort_keys=True))
            assert before["users"] == (await legacy14_snapshot(conn))["users"]
            assert (
                await conn.execute(
                    text("SELECT cash,starting_cash FROM accounts WHERE id=:p"), {"p": root}
                )
            ).one() == (Decimal("321.12"), Decimal(8765))
            await conn.execute(text(PREFLIGHT_0023_SQL))
    finally:
        await child.dispose()


@pytest.mark.parametrize(
    "damage",
    [
        "CREATE INDEX unexpected_legacy14_index ON accounts(id)",
        "REVOKE SELECT ON stock_instruments FROM birja_action_operator",
        "GRANT UPDATE ON accounts TO birja_scheduler",
        "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator GRANT SELECT ON TABLES TO birja_app",
        "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator IN SCHEMA public "
        "GRANT EXECUTE ON FUNCTIONS TO PUBLIC",
    ],
    ids=["catalogue", "missing-grant", "extra-grant", "table-default", "function-default"],
)
async def test_legacy14_authority_refuses_before_child_and_preserves_state(
    portfolio_migration_db, damage
):
    from tests.test_portfolio_management_grants import sql

    child, _ = await prepare_legacy14(portfolio_migration_db)
    try:
        async with child.connect() as conn:
            assert await migration.require_migrator(conn) == "0014"
        async with child.begin() as conn:
            await sql(conn, damage)
        before = await prior_object_evidence(portfolio_migration_db, "SELECT true")
        with (
            patch.object(migration, "create_async_engine", return_value=child),
            patch.object(migration, "database_connect_args", return_value={}),
            patch.object(migration.asyncio, "create_subprocess_exec", AsyncMock()) as spawn,
        ):
            with pytest.raises(ValueError, match="Unrecognized"):
                await migration.migrate(SimpleNamespace(env="prod", database_url=URL))
            spawn.assert_not_awaited()
        assert await prior_object_evidence(portfolio_migration_db, "SELECT true") == before
    finally:
        if damage.startswith("ALTER DEFAULT"):
            async with portfolio_migration_db.begin() as admin:
                await sql(admin, damage.replace("GRANT", "REVOKE").replace(" TO ", " FROM "))
        await child.dispose()


async def prepare_pre_closure(engine, revision, *, runtime=True, private=True):
    from uuid import uuid4

    from app.db.portfolio_bootstrap import GRANTS_SQL
    from tests.test_portfolio_management_grants import sql

    await migrate_to("0020")
    child = create_async_engine(test_migration_url())
    async with engine.begin() as admin:
        await admin.execute(text("ALTER SCHEMA public OWNER TO pg_database_owner"))
    async with child.begin() as conn:
        await sql(
            conn,
            "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator "
            + ("REVOKE" if private else "GRANT")
            + " EXECUTE ON FUNCTIONS "
            + ("FROM" if private else "TO")
            + " PUBLIC;",
        )
        if runtime:
            await sql(conn, GRANTS_SQL)
        uid = await conn.scalar(
            text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
            {"e": f"migration-transition-{uuid4()}@example.test"},
        )
        root = await conn.scalar(text("SELECT initialize_portfolio(:u)"), {"u": uid})
        await conn.execute(text("UPDATE accounts SET cash=123.45 WHERE id=:p"), {"p": root})
    if revision != "0020":
        await migrate_to(revision)
    return child, root


@pytest.mark.parametrize("revision", ["0020", "0021", "0022"])
@pytest.mark.parametrize("runtime", [False, True], ids=["initial", "runtime"])
@pytest.mark.parametrize("private", [False, True], ids=["builtin-default", "private-default"])
async def test_exact_pre_closure_initial_runtime_and_resume_authentication(
    portfolio_migration_db, revision, runtime, private
):
    from app.db.portfolio_bootstrap import GRANTS_0023_SQL, PREFLIGHT_0023_SQL
    from app.db.schema_contract import SchemaAdmissionError, require_schema
    from tests.test_portfolio_management_grants import sql

    child, root = await prepare_pre_closure(
        portfolio_migration_db, revision, runtime=runtime, private=private
    )
    try:
        async with child.connect() as conn:
            assert await migration.require_migrator(conn) == revision
        await migrate_to("0023")
        async with child.begin() as conn:
            await conn.execute(text(PREFLIGHT_0023_SQL))
            with pytest.raises(SchemaAdmissionError, match="incompatible_authority"):
                await require_schema(conn)
            await sql(conn, GRANTS_0023_SQL)
            assert await require_schema(conn) == "0023"
            assert (
                await conn.execute(
                    text("SELECT cash,starting_cash FROM accounts WHERE id=:p"), {"p": root}
                )
            ).one() == (Decimal("123.45"), Decimal(10000))
    finally:
        await child.dispose()


@pytest.mark.parametrize("revision", ["0020", "0021", "0022", "0023"])
@pytest.mark.parametrize(
    "damage",
    [
        "CREATE INDEX unexpected_transition_index ON accounts(id)",
        "REVOKE SELECT ON users FROM birja_app",
        "GRANT UPDATE ON accounts TO birja_scheduler",
        "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator GRANT SELECT ON TABLES TO birja_app",
    ],
    ids=["schema", "missing-grant", "extra-grant", "unsafe-default"],
)
async def test_prior_authority_drift_refuses_before_any_migration_child(
    portfolio_migration_db, revision, damage
):
    from app.db.portfolio_bootstrap import ACL_SQL, DEFAULT_ACL_0023_SQL
    from tests.test_portfolio_management_grants import sql

    child, root = await prepare_pre_closure(portfolio_migration_db, revision)
    try:
        async with child.begin() as conn:
            await sql(conn, damage)
        async with child.connect() as conn:
            before = (
                await conn.scalar(text(ACL_SQL)),
                await conn.scalar(text(DEFAULT_ACL_0023_SQL)),
                (await conn.execute(text("SELECT version_num FROM alembic_version"))).scalar_one(),
                (
                    await conn.execute(
                        text("SELECT cash,starting_cash FROM accounts WHERE id=:p"), {"p": root}
                    )
                ).one(),
            )
        with (
            patch.object(migration, "create_async_engine", return_value=child),
            patch.object(migration, "database_connect_args", return_value={}),
            patch.object(migration.asyncio, "create_subprocess_exec", AsyncMock()) as spawn,
        ):
            with pytest.raises(ValueError, match="Unrecognized (?:pre-)?closure"):
                await migration.migrate(SimpleNamespace(env="prod", database_url=URL))
            spawn.assert_not_awaited()
        async with child.connect() as conn:
            after = (
                await conn.scalar(text(ACL_SQL)),
                await conn.scalar(text(DEFAULT_ACL_0023_SQL)),
                (await conn.execute(text("SELECT version_num FROM alembic_version"))).scalar_one(),
                (
                    await conn.execute(
                        text("SELECT cash,starting_cash FROM accounts WHERE id=:p"), {"p": root}
                    )
                ).one(),
            )
        assert after == before
    finally:
        if damage.startswith("ALTER DEFAULT"):
            # This deliberately committed hostile default must be undone only
            # after the no-mutation assertion, before shared fixture teardown.
            async with portfolio_migration_db.begin() as admin:
                await sql(
                    admin,
                    "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator "
                    "REVOKE SELECT ON TABLES FROM birja_app",
                )
        await child.dispose()


def test_successor_source_authentication_pins_every_closure_asset():
    required = {
        "alembic/versions/0021_portfolio_closure_schema.py",
        "alembic/versions/0022_portfolio_closure_provenance.py",
        "alembic/versions/0023_portfolio_closure_authority.py",
        "alembic/sql/0023_portfolio_closure.sql",
    }
    assert required <= migration.SOURCE.keys()
    migration.require_source()


async def test_successor_authenticated_migrator_accepts_complete_closure_revision(
    portfolio_migration_db,
):
    """Migration authentication supports the declared successor, not arbitrary head."""
    import asyncio

    from tests.test_migrations import run_test_migration

    for revision in ("0020", "0021", "0022", "0023"):
        await asyncio.to_thread(run_test_migration, revision)
        async with portfolio_migration_db.begin() as conn:
            await conn.execute(text("ALTER SCHEMA public OWNER TO pg_database_owner"))
        child = create_async_engine(test_migration_url())
        try:
            async with child.connect() as conn:
                assert await migration.require_migrator(conn) == revision
        finally:
            await child.dispose()
    # A familiar name on an unexpected function or table is not an admitted
    # revision, and a historical schema stamp cannot masquerade as successor.
    child = create_async_engine(test_migration_url())
    try:
        async with child.connect() as conn:
            with pytest.raises(ValueError, match="Unexpected migration routine"):
                async with conn.begin_nested():
                    await conn.execute(
                        text(
                            "CREATE FUNCTION public.close_portfolio(text) RETURNS bigint "
                            "LANGUAGE sql AS $$SELECT 1::bigint$$"
                        )
                    )
                    await migration.require_migrator(conn)
    finally:
        await child.dispose()


@pytest.mark.parametrize("damage", ["relation", "substitution", "function_owner", "operator"])
async def test_successor_migrator_refuses_unknown_or_substituted_inventory(
    portfolio_migration_db, damage
):
    import asyncio

    from tests.test_migrations import run_test_migration

    await asyncio.to_thread(run_test_migration, "0020" if damage == "substitution" else "0023")
    async with portfolio_migration_db.begin() as conn:
        await conn.execute(text("ALTER SCHEMA public OWNER TO pg_database_owner"))
        if damage == "relation":
            await conn.execute(text("CREATE TABLE unexpected_successor(id bigint)"))
        elif damage == "substitution":
            await conn.execute(text("UPDATE alembic_version SET version_num='0023'"))
        elif damage == "function_owner":
            await conn.execute(
                text(
                    "ALTER FUNCTION close_portfolio(bigint,bigint,uuid,text,text) "
                    "OWNER TO birja_test"
                )
            )
        else:
            await conn.execute(text("ALTER ROLE birja_action_operator LOGIN"))
    child = create_async_engine(test_migration_url())
    try:
        async with child.connect() as conn:
            with pytest.raises(ValueError):
                await migration.require_migrator(conn)
    finally:
        await child.dispose()
        if damage == "operator":
            async with portfolio_migration_db.begin() as conn:
                await conn.execute(text("ALTER ROLE birja_action_operator NOLOGIN"))


def test_trusted_source_requires_exact_regular_files(tmp_path):
    migration.require_source()
    for name in migration.SOURCE:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((migration.BACKEND_DIR / name).read_bytes())
    migration.require_source(tmp_path)
    path = tmp_path / next(iter(migration.SOURCE))
    original = path.read_bytes()
    path.write_bytes(original + b"\n")
    with pytest.raises(ValueError, match="Untrusted"):
        migration.require_source(tmp_path)
    path.unlink()
    with pytest.raises(ValueError, match="Untrusted"):
        migration.require_source(tmp_path)
    path.symlink_to(migration.BACKEND_DIR / next(iter(migration.SOURCE)))
    with pytest.raises(ValueError, match="Untrusted"):
        migration.require_source(tmp_path)


@pytest.mark.parametrize(
    "env,url",
    [("test", URL)]
    + [
        ("prod", URL.replace(old, new))
        for old, new in (
            ("@postgres:", "@other:"),
            (":5432/", ":5433/"),
            ("//birja_migrator:", "//other:"),
            ("/birja", "/other"),
            (":synthetic@", ":@"),
            ("/birja", "/birja?options=x"),
        )
    ],
)
async def test_misrouted_identity_never_constructs_engine(env, url):
    with patch.object(migration, "create_async_engine") as create:
        with pytest.raises(ValueError, match="Explicit Compose"):
            await migration.migrate(SimpleNamespace(env=env, database_url=url))
        create.assert_not_called()


@pytest.mark.parametrize(
    "outcome", ["success", "timeout", "child", "revision", "preflight", "identity"]
)
async def test_child_finalization_and_failure_cleanup(outcome, capsys):
    conn = MagicMock()
    conn.execute = AsyncMock()
    conn.commit = AsyncMock()
    conn.rollback = AsyncMock()
    engine = MagicMock()
    engine.connect.return_value.__aenter__ = AsyncMock(return_value=conn)
    engine.connect.return_value.__aexit__ = AsyncMock(return_value=False)
    engine.dispose = AsyncMock()
    child = SimpleNamespace(
        communicate=AsyncMock(side_effect=TimeoutError if outcome == "timeout" else None),
        kill=MagicMock(),
        wait=AsyncMock(),
        returncode=1 if outcome == "child" else 0,
    )
    identity = AsyncMock(
        side_effect=ValueError("identity")
        if outcome == "identity"
        else ["0014", "0016" if outcome == "revision" else "0023"]
    )
    if outcome == "preflight":

        async def execute(statement):
            if str(statement) == migration.PREFLIGHT_SQL:
                raise ValueError("preflight")

        conn.execute.side_effect = execute
    with (
        patch.object(migration, "create_async_engine", return_value=engine) as create,
        patch.object(migration, "database_connect_args", return_value={}) as args,
        patch.object(migration, "require_migrator", identity),
        patch.object(
            migration.asyncio, "create_subprocess_exec", AsyncMock(return_value=child)
        ) as spawn,
    ):
        settings = SimpleNamespace(env="prod", database_url=URL)
        if outcome == "success":
            await migration.migrate(settings)
            assert (
                capsys.readouterr().out
                == "portfolio_migration_to_final=true source_revision=0014 final=0023\n"
            )
            conn.rollback.assert_awaited_once()
        else:
            with pytest.raises(ValueError):
                await migration.migrate(settings)
            assert capsys.readouterr().out == ""
        args.assert_called_once_with(settings, migration=True)
        create.assert_called_once_with(URL, connect_args={})
    engine.dispose.assert_awaited_once()
    statements = [str(c.args[0]) for c in conn.execute.call_args_list]
    if outcome == "identity":
        assert statements == []
        spawn.assert_not_awaited()
    else:
        assert statements[0] == "SELECT pg_advisory_lock(1026016017)"
        assert statements[-1] == "SELECT pg_advisory_unlock(1026016017)"
        assert conn.commit.await_count == 2
        assert spawn.call_args.args[-2:] == ("upgrade", "0023")
        assert spawn.call_args.kwargs["cwd"] == migration.BACKEND_DIR
    assert child.kill.call_count == (outcome == "timeout")
    assert child.wait.await_count == (outcome == "timeout")


def test_cli_reports_only_redacted_failure_and_checks_source_first(capsys):
    async def fail(_settings):
        raise ValueError("sensitive child diagnostics")

    with (
        patch.object(migration, "require_source") as source,
        patch.object(migration, "get_settings", return_value=object()),
        patch.object(migration, "migrate", side_effect=fail),
        pytest.raises(SystemExit) as failure,
    ):
        migration.main()
    source.assert_called_once()
    assert failure.value.code == 1
    assert capsys.readouterr().err == "portfolio_migration_failed=true diagnostics=redacted\n"


def test_module_entrypoint_invokes_the_finite_main(monkeypatch):
    monkeypatch.setenv("ENV", "test")
    with patch("asyncio.run", side_effect=lambda coroutine: coroutine.close()) as run:
        runpy.run_module("app.db.portfolio_migrate", run_name="__main__")
    run.assert_called_once()


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "schema",
        "versions",
        "relation",
        "owner",
        "routine",
        "routine_owner",
        "identity",
        "fresh",
        "missing",
    ],
)
async def test_actual_authenticated_migrator_catalogue_refusals(portfolio_migration_db, damage):
    """Use a real credentialed restricted connection and real hostile catalogues."""
    if damage not in {"fresh", "missing"}:
        await migrate_to("0017")
    async with portfolio_migration_db.begin() as admin:
        assert (await admin.execute(text("SELECT current_database(),session_user"))).one() == (
            "birja_test",
            "birja_test",
        )
        await admin.execute(text("ALTER SCHEMA public OWNER TO pg_database_owner"))
        await admin.execute(
            text("REVOKE CREATE ON SCHEMA public FROM PUBLIC,birja_app,birja_scheduler")
        )
        if damage == "schema":
            await admin.execute(text("GRANT CREATE ON SCHEMA public TO birja_app"))
        elif damage == "versions":
            await admin.execute(text("INSERT INTO alembic_version VALUES ('0013')"))
        elif damage == "relation":
            await admin.execute(text("CREATE TABLE public.unexpected_relation(id bigint)"))
        elif damage == "owner":
            await admin.execute(text("ALTER TABLE public.accounts OWNER TO birja_test"))
        elif damage == "routine":
            await admin.execute(
                text(
                    "CREATE FUNCTION public.unexpected_routine() RETURNS int "
                    "LANGUAGE sql AS 'SELECT 1'"
                )
            )
        elif damage == "routine_owner":
            await admin.execute(
                text("ALTER FUNCTION public.check_portfolio_financial_write() OWNER TO birja_test")
            )
    child = create_async_engine(test_migration_url())
    try:
        if damage == "identity":
            async with portfolio_migration_db.connect() as conn:
                with pytest.raises(ValueError, match="Authenticated restricted"):
                    await migration.require_migrator(conn)
        else:
            async with child.connect() as conn:
                assert (await conn.execute(text("SELECT session_user,current_user"))).one() == (
                    "birja_migrator",
                    "birja_migrator",
                )
                if damage in {None, "fresh"}:
                    assert await migration.require_migrator(conn, fresh=damage == "fresh") == (
                        None if damage == "fresh" else "0017"
                    )
                else:
                    with pytest.raises(ValueError):
                        await migration.require_migrator(conn)
    finally:
        await child.dispose()
