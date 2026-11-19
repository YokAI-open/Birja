"""Exact successor authority on owned disposable PostgreSQL, never production."""

import asyncio
import re
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from tests.portfolio_fixtures import reset_disposable_schema, restore_current_test_schema
from tests.test_migrations import run_test_migration, test_migration_url
from tests.test_portfolio_management_grants import production_bootstrap, sql


async def authorize(engine):
    from app.db.portfolio_bootstrap import GRANTS_0023_SQL, PREFLIGHT_0023_SQL

    async with engine.begin() as conn:
        await conn.execute(text(PREFLIGHT_0023_SQL))
        await sql(conn, GRANTS_0023_SQL)


@pytest_asyncio.fixture(params=[False, True], ids=["builtin-default", "private-default"])
async def granted20_transition(engine, request):
    from tests.test_portfolio_migrate import prepare_pre_closure

    await reset_disposable_schema(engine)
    child, _ = await prepare_pre_closure(engine, "0020", private=request.param)
    await asyncio.to_thread(run_test_migration, "0023")
    try:
        yield engine, child
    finally:
        await child.dispose()
        await restore_current_test_schema(engine)


@pytest_asyncio.fixture(params=[False, True], ids=["builtin-default", "private-default"])
async def legacy14_transition(engine, request):
    from tests.test_portfolio_migrate import prepare_legacy14

    await reset_disposable_schema(engine)
    child, _ = await prepare_legacy14(engine, private=request.param)
    await asyncio.to_thread(run_test_migration, "0023")
    try:
        yield engine, child
    finally:
        await child.dispose()
        await restore_current_test_schema(engine)


async def transition_evidence(child):
    from app.db.portfolio_bootstrap import ACL_SQL, CATALOGUE_0023_SQL, DEFAULT_ACL_0023_SQL

    async with child.connect() as conn:
        return (
            await complete_snapshot(conn),
            await conn.scalar(text(ACL_SQL)),
            await conn.scalar(text(CATALOGUE_0023_SQL)),
            await conn.scalar(text(DEFAULT_ACL_0023_SQL)),
        )


async def assert_transition_refusal(child):
    from app.db.portfolio_bootstrap import PREFLIGHT_0023_SQL

    before = await transition_evidence(child)
    async with child.connect() as conn:
        with pytest.raises(DBAPIError):
            async with conn.begin_nested():
                await conn.execute(text(PREFLIGHT_0023_SQL))
    code, _ = await production_bootstrap()
    assert code != 0
    assert await transition_evidence(child) == before


async def test_genuine_granted20_transition_requires_explicit_runtime_bootstrap(
    granted20_transition,
):
    from app.db.portfolio_bootstrap import (
        ACL_0023_FROM_0020_SHA256,
        GRANTS_0023_SQL,
        PREFLIGHT_0023_SQL,
    )
    from app.db.schema_contract import SchemaAdmissionError, require_schema

    _, child = granted20_transition
    before = await transition_evidence(child)
    assert before[1] == ACL_0023_FROM_0020_SHA256
    async with child.connect() as conn:
        await conn.execute(text(PREFLIGHT_0023_SQL))
        with pytest.raises(SchemaAdmissionError, match="incompatible_authority"):
            await require_schema(conn)
    code, diagnostic = await production_bootstrap()
    assert code == 0, diagnostic
    async with child.begin() as conn:
        assert await require_schema(conn) == "0023"
        assert await complete_snapshot(conn) == before[0]
        await sql(conn, GRANTS_0023_SQL)
        assert await require_schema(conn) == "0023"
        assert await complete_snapshot(conn) == before[0]


async def test_genuine_legacy14_transition_requires_explicit_runtime_bootstrap(legacy14_transition):
    from app.db.portfolio_bootstrap import (
        ACL_0023_FROM_0014_SHA256,
        GRANTS_0023_SQL,
        PREFLIGHT_0023_SQL,
    )
    from app.db.schema_contract import SchemaAdmissionError, require_schema

    _, child = legacy14_transition
    before = await transition_evidence(child)
    assert before[1] == ACL_0023_FROM_0014_SHA256
    async with child.connect() as conn:
        await conn.execute(text(PREFLIGHT_0023_SQL))
        with pytest.raises(SchemaAdmissionError, match="incompatible_authority"):
            await require_schema(conn)
    code, diagnostic = await production_bootstrap()
    assert code == 0, diagnostic
    async with child.begin() as conn:
        assert await require_schema(conn) == "0023"
        assert await complete_snapshot(conn) == before[0]
        await sql(conn, GRANTS_0023_SQL)
        assert await require_schema(conn) == "0023"
        assert await complete_snapshot(conn) == before[0]


async def test_every_partial_or_missing_lifecycle_read_refuses_both_bootstraps(
    granted20_transition,
):
    _, child = granted20_transition
    reads = [
        (table, role)
        for table in ("portfolio_lifecycle_closures", "portfolio_closure_intents")
        for role in ("birja_app", "birja_scheduler")
    ]
    # Each added read is an incomplete upgrade, never a finite entry profile.
    for table, role in reads:
        async with child.begin() as conn:
            await sql(conn, f"GRANT SELECT ON {table} TO {role}")  # noqa: S608 - fixed matrix
        await assert_transition_refusal(child)
        async with child.begin() as conn:
            await sql(conn, f"REVOKE SELECT ON {table} FROM {role}")  # noqa: S608
    code, diagnostic = await production_bootstrap()
    assert code == 0, diagnostic
    # Each missing read from final authority also refuses without repair.
    for table, role in reads:
        async with child.begin() as conn:
            await sql(conn, f"REVOKE SELECT ON {table} FROM {role}")  # noqa: S608
        await assert_transition_refusal(child)
        async with child.begin() as conn:
            await sql(conn, f"GRANT SELECT ON {table} TO {role}")  # noqa: S608


async def test_legacy14_partial_or_missing_lifecycle_read_refuses_both_bootstraps(
    legacy14_transition,
):
    await test_every_partial_or_missing_lifecycle_read_refuses_both_bootstraps(legacy14_transition)


async def test_transition_extra_grant_and_unsafe_future_default_refuse(granted20_transition):
    _, child = granted20_transition
    for damage, undo in (
        (
            "GRANT UPDATE ON accounts TO birja_scheduler",
            "REVOKE UPDATE ON accounts FROM birja_scheduler",
        ),
        (
            "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator GRANT SELECT ON TABLES TO birja_app",
            "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator "
            "REVOKE SELECT ON TABLES FROM birja_app",
        ),
        (
            "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator IN SCHEMA public "
            "GRANT EXECUTE ON FUNCTIONS TO PUBLIC",
            "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator IN SCHEMA public "
            "REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC",
        ),
    ):
        async with child.begin() as conn:
            await sql(conn, damage)
        await assert_transition_refusal(child)
        async with child.begin() as conn:
            await sql(conn, undo)


async def test_legacy14_extra_grant_and_unsafe_future_default_refuse(legacy14_transition):
    await test_transition_extra_grant_and_unsafe_future_default_refuse(legacy14_transition)


async def closed_evidence_fixture(engine):
    """Synthetic SQL lifecycle fixture, not public API acceptance evidence."""
    async with engine.begin() as conn:
        user = (
            await conn.execute(
                text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                {"e": f"closed-bootstrap-{uuid4()}@example.test"},
            )
        ).scalar_one()
        portfolio = (
            await conn.execute(text("SELECT initialize_portfolio(:u)"), {"u": user})
        ).scalar_one()
        name = (
            await conn.execute(text("SELECT name FROM accounts WHERE id=:p"), {"p": portfolio})
        ).scalar_one()
    # As with actual create then delete requests, commit initialization before
    # starting the distinct terminal operation and its deferred constraints.
    async with engine.begin() as conn:
        assert (
            await conn.execute(
                text("SELECT outcome FROM close_portfolio(:u,:p,:k,:n,'freeze_at_closure_v1')"),
                {"u": user, "p": portfolio, "k": uuid4(), "n": name},
            )
        ).scalar_one() == "closed"
        return portfolio


async def complete_snapshot(conn):
    from tests.portfolio_closure_fixtures import retained_snapshot

    result = await retained_snapshot(conn)
    for table in ("portfolio_lifecycle_closures", "portfolio_closure_intents"):
        result[table] = tuple(
            (
                await conn.execute(
                    text(f"SELECT to_jsonb(t)::text FROM {table} t ORDER BY id")  # noqa: S608
                )
            ).scalars()
        )
        result[f"{table}_id_seq"] = tuple(
            (
                await conn.execute(text(f"SELECT last_value,is_called FROM {table}_id_seq"))  # noqa: S608
            ).one()
        )
    return result


async def test_closed_evidence_bootstrap_admits_valid_and_refuses_corrupt_names(successor):
    from app.db.portfolio_bootstrap import PREFLIGHT_0023_SQL
    from app.db.schema_contract import require_schema

    await authorize(successor)
    portfolio = await closed_evidence_fixture(successor)
    async with successor.connect() as conn:
        assert await require_schema(conn) == "0023"
        before = await complete_snapshot(conn)
    code, diagnostic = await production_bootstrap()
    assert code == 0, diagnostic
    async with successor.begin() as conn:
        assert await complete_snapshot(conn) == before
        for table in ("portfolio_lifecycle_closures", "portfolio_closure_intents"):
            # Declared privileged retained-corruption fixture; re-enable all
            # user triggers before invoking either actual bootstrap path.
            await conn.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER USER"))  # noqa: S608
            await conn.execute(
                text(
                    f"UPDATE {table} SET confirmation_name='Corrupt retained name' "  # noqa: S608
                    "WHERE portfolio_id=:p"
                ),
                {"p": portfolio},
            )
            await conn.execute(text(f"ALTER TABLE {table} ENABLE TRIGGER USER"))  # noqa: S608
        before_refusal = await complete_snapshot(conn)
        with pytest.raises(DBAPIError, match="closure lifecycle evidence"):
            async with conn.begin_nested():
                await conn.execute(text(PREFLIGHT_0023_SQL))
    code, _ = await production_bootstrap()
    assert code != 0
    async with successor.connect() as conn:
        assert await complete_snapshot(conn) == before_refusal


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


@pytest_asyncio.fixture(params=["fresh", "upgraded"], ids=["empty-source", "populated-source"])
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
        await restore_current_test_schema(engine)


async def test_fresh_upgraded_exact_successor_admission_and_sql_parity(successor):
    from app.db.portfolio_bootstrap import (
        ACL_0023_SHA256,
        ACL_SQL,
        CATALOGUE_0023_SHA256,
        CATALOGUE_0023_SQL,
        DEFAULT_ACL_0023_SHA256,
        DEFAULT_ACL_0023_SQL,
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
        assert (
            await conn.execute(text(DEFAULT_ACL_0023_SQL))
        ).scalar_one() == DEFAULT_ACL_0023_SHA256
    code, diagnostic = await production_bootstrap()
    assert code == 0, diagnostic
    async with successor.connect() as conn:
        assert await require_schema(conn) == "0023"
        assert (
            await conn.execute(text(DEFAULT_ACL_0023_SQL))
        ).scalar_one() == DEFAULT_ACL_0023_SHA256
        assert (
            await conn.execute(text("SELECT id,cash,starting_cash FROM accounts"))
        ).all() == before


async def test_fresh_quarantine_entry_requires_exact_regrant_before_runtime(successor):
    from app.db.portfolio_bootstrap import (
        ACL_0023_QUARANTINE_SHA256,
        ACL_SQL,
        GRANTS_SQL,
        PREFLIGHT_0023_SQL,
    )
    from app.db.schema_contract import SchemaAdmissionError, require_schema

    await authorize(successor)
    # Declared privilege-quarantine fixture, not an archive-restore claim.
    # Revoke all non-owner relation/column/sequence/routine privileges using
    # the established finite reset after catalogue authentication.
    reset = GRANTS_SQL.split("END $management_reset$;", 1)[0] + "END $management_reset$;"
    async with successor.begin() as conn:
        await sql(conn, reset)
        assert (await conn.execute(text(ACL_SQL))).scalar_one() == ACL_0023_QUARANTINE_SHA256
        await conn.execute(text(PREFLIGHT_0023_SQL))
        with pytest.raises(SchemaAdmissionError, match="incompatible_authority"):
            await require_schema(conn)
    code, diagnostic = await production_bootstrap()
    assert code == 0, diagnostic
    async with successor.connect() as conn:
        assert await require_schema(conn) == "0023"


async def test_fresh_implicit_public_function_defaults_refuse_runtime_and_bootstrap(successor):
    from app.db.portfolio_bootstrap import PREFLIGHT_0023_SQL
    from app.db.schema_contract import SchemaAdmissionError, require_schema

    await authorize(successor)
    async with successor.connect() as conn:
        tx = await conn.begin()
        try:
            await conn.execute(
                text(
                    "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator "
                    "GRANT EXECUTE ON FUNCTIONS TO PUBLIC"
                )
            )
            # PostgreSQL canonically removes the explicit row when defaults
            # become the built-in PUBLIC EXECUTE policy. Missing is unsafe.
            assert not (
                await conn.execute(
                    text(
                        "SELECT EXISTS(SELECT FROM pg_default_acl "
                        "WHERE defaclrole='birja_migrator'::regrole "
                        "AND defaclnamespace=0 AND defaclobjtype='f')"
                    )
                )
            ).scalar_one()
            with pytest.raises(SchemaAdmissionError, match="incompatible_authority"):
                async with conn.begin_nested():
                    await require_schema(conn)
            with pytest.raises(DBAPIError, match="effective closure default"):
                async with conn.begin_nested():
                    await conn.execute(text(PREFLIGHT_0023_SQL))
        finally:
            await tx.rollback()


@pytest.mark.parametrize("revision", ["0021", "0022", "9999"])
async def test_partial_and_unknown_runtime_refuse_without_grants(engine, revision):
    from app.db.portfolio_bootstrap import ACL_SQL
    from app.db.schema_contract import SchemaAdmissionError, require_schema

    await reset_disposable_schema(engine)
    await asyncio.to_thread(run_test_migration, "0022" if revision == "9999" else revision)
    try:
        async with engine.begin() as conn:
            if revision == "9999":
                await conn.execute(text("UPDATE alembic_version SET version_num='9999'"))
            before = (await conn.execute(text(ACL_SQL))).scalar_one()
            with pytest.raises(SchemaAdmissionError):
                await require_schema(conn)
        code, _ = await production_bootstrap()
        assert code != 0
        async with engine.connect() as conn:
            assert (await conn.execute(text(ACL_SQL))).scalar_one() == before
    finally:
        await restore_current_test_schema(engine)


async def test_successor_downgrade_refuses_before_financial_or_lifecycle_loss(successor):
    await closed_evidence_fixture(successor)
    async with successor.connect() as conn:
        before = await complete_snapshot(conn)
        version = (await conn.execute(text("SELECT version_num FROM alembic_version"))).scalar_one()
    with pytest.raises(RuntimeError, match="irreversible|refus"):
        await asyncio.to_thread(run_test_migration, "0020", down=True)
    async with successor.connect() as conn:
        assert (
            await conn.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one() == version
        assert await complete_snapshot(conn) == before


async def test_fresh_developer_bootstrap_authorizes_only_exact_current(successor):
    from app.db.dev_bootstrap import _authorize_portfolios
    from app.db.schema_contract import require_schema

    async with successor.begin() as conn:
        raw = await conn.get_raw_connection()
        await _authorize_portfolios(raw.driver_connection)
        assert await require_schema(conn) == "0023"
        counts = (
            await conn.execute(
                text(
                    "SELECT count(*) FILTER(WHERE relkind='r'), "
                    "count(*) FILTER(WHERE relkind='S') FROM pg_class "
                    "WHERE relnamespace='public'::regnamespace"
                )
            )
        ).one()
        assert counts == (31, 24)


async def test_repeated_bootstrap_leaves_current_for_next_pytest_process(engine):
    from app.db.schema_contract import require_schema
    from tests.test_migrations import ensure_dividend_test_owner, install_current_test_grants

    await reset_disposable_schema(engine)
    await asyncio.to_thread(run_test_migration, "0023")
    await install_current_test_grants()
    for _ in range(2):
        await ensure_dividend_test_owner()
        await install_current_test_grants()
        async with engine.connect() as conn:
            assert await require_schema(conn) == "0023"
    # Deliberately leave the supported current schema. The next independent
    # pytest process must pass its finite session-autouse prerequisite on0023.
