"""Independent current catalogue and authenticated least privilege contracts."""

import asyncio
import json
import secrets
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.portfolio_bootstrap import (
    GRANTS_0023_SQL as GRANTS_SQL,
)
from app.db.portfolio_bootstrap import (
    PREFLIGHT_0023_SQL as PREFLIGHT_SQL,
)
from app.db.schema_contract import SchemaAdmissionError, require_schema
from tests.portfolio_fixtures import reset_disposable_schema, restore_current_test_schema
from tests.test_migrations import run_test_migration, test_migration_url


def test_retained0017_contract_literals_are_unchanged():
    from app.db.portfolio_bootstrap import GRANTS_0017_SQL, PREFLIGHT_0017_SQL

    source = subprocess.run(
        ["/usr/bin/git", "show", "4b4320b:backend/app/db/portfolio_bootstrap.py"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    namespace = {}
    exec(compile(source, "retained0017/bootstrap.py", "exec"), namespace)  # noqa: S102 - fixed trusted source
    assert namespace["PREFLIGHT_SQL"] == PREFLIGHT_0017_SQL
    assert namespace["GRANTS_SQL"] == GRANTS_0017_SQL


async def sql(conn, source):
    raw = await conn.get_raw_connection()
    await raw.driver_connection.execute(source)


@pytest_asyncio.fixture(params=["fresh", "upgraded"])
async def current(engine, request):
    await reset_disposable_schema(engine)
    if request.param == "upgraded":
        await asyncio.to_thread(run_test_migration, "0017")
        migrator = create_async_engine(test_migration_url())
        async with migrator.begin() as conn:
            await conn.execute(text("INSERT INTO users(email) VALUES ('legacy@example.test')"))
            await conn.execute(
                text(
                    "INSERT INTO accounts(user_id,name,cash,starting_cash) "
                    "SELECT id,'Legacy',123.45,7777 FROM users"
                )
            )
        await migrator.dispose()
    await asyncio.to_thread(run_test_migration, "0023")
    passwords = {role: secrets.token_hex(32) for role in ("birja_app", "birja_scheduler")}
    async with engine.begin() as conn:
        await conn.execute(
            text("REVOKE CREATE ON SCHEMA public FROM PUBLIC,birja_app,birja_scheduler")
        )
        await conn.execute(text(PREFLIGHT_SQL))
        await sql(conn, GRANTS_SQL)
        for role, password in passwords.items():
            await conn.execute(text(f"ALTER ROLE {role} LOGIN PASSWORD '{password}'"))  # noqa: S608
    roles = {
        role: create_async_engine(make_url(engine.url).set(username=role, password=password))
        for role, password in passwords.items()
    }
    try:
        yield engine, roles
    finally:
        for db in roles.values():
            await db.dispose()
        await restore_current_test_schema(engine)


async def test_bootstrap_preserves_money_and_exact_roles(current):
    engine, roles = current
    async with roles["birja_app"].begin() as conn:
        assert await require_schema(conn) == "0023"
        assert (await conn.execute(text("SELECT session_user,current_user"))).one() == (
            "birja_app",
            "birja_app",
        )
        uid = (
            await conn.execute(
                text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                {"e": f"grants-{uuid4()}@example.test"},
            )
        ).scalar_one()
        root = (
            await conn.execute(text("SELECT initialize_portfolio(:u)"), {"u": uid})
        ).scalar_one()
        await conn.execute(text("UPDATE accounts SET cash=cash-1 WHERE id=:p"), {"p": root})
        assert (
            await conn.execute(
                text("SELECT cash,starting_cash FROM accounts WHERE id=:p"), {"p": root}
            )
        ).one() == (9999, 10000)
        created = (
            await conn.execute(
                text(
                    "SELECT * FROM create_portfolio(:u,:key,'Independent','Original description')"
                ),
                {"u": uid, "key": uuid4()},
            )
        ).one()
        edited = (
            await conn.execute(
                text("SELECT * FROM update_portfolio_metadata(:u,:root,'Renamed','',true,true)"),
                {"u": uid, "root": created.portfolio_id},
            )
        ).one()
        assert (edited.portfolio_id, edited.name, edited.description) == (
            created.portfolio_id,
            "Renamed",
            "",
        )
        assert (
            await conn.execute(text("SELECT initialize_portfolio(:u)"), {"u": uid})
        ).scalar_one() == root
        assert (
            await conn.execute(
                text("SELECT cash,starting_cash FROM accounts WHERE id=:root"),
                {"root": created.portfolio_id},
            )
        ).one() == (10000, 10000)
    async with engine.connect() as conn:
        legacy = (
            await conn.execute(text("SELECT cash,starting_cash FROM accounts WHERE name='Legacy'"))
        ).all()
        assert all(str(r.cash) == "123.45000000" and r.starting_cash == 7777 for r in legacy)
        routines = (
            await conn.execute(
                text("SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace")
            )
        ).scalar_one()
        # Frozen0020's17 routines plus lifecycle/terminal-root/clock guards and
        # the single narrow closure definer; no extra overload is admitted.
        assert routines == 21
        assert (
            await conn.execute(
                text(
                    "SELECT has_table_privilege('birja_app',"
                    "'accounts','INSERT'),has_table_privilege('birja_app','users','UPDATE')"
                )
            )
        ).one() == (False, False)
        assert await require_schema(conn) == "0023"


@pytest.mark.parametrize(
    "statement",
    [
        "INSERT INTO accounts(user_id,cash,starting_cash) VALUES (1,10000,10000)",
        "UPDATE accounts SET name='forged'",
        "UPDATE accounts SET name_key='forged'",
        "UPDATE accounts SET description='forged'",
        "UPDATE accounts SET starting_cash=20000",
        "UPDATE accounts SET closed_at=clock_timestamp()",
        "UPDATE users SET email='forged'",
        "INSERT INTO portfolio_initializations(user_id,origin) VALUES (1,'legacy')",
        "UPDATE portfolio_creations SET amount=20000",
        "DELETE FROM portfolio_creations",
        "SELECT nextval('accounts_id_seq')",
        "CREATE TABLE public.forged(id bigint)",
        "SELECT portfolio_name_key('private')",
        "SELECT * FROM create_portfolio(1,gen_random_uuid(),'forged','',20000)",
    ],
)
async def test_ordinary_forgery_denied(current, statement):
    _, roles = current
    with pytest.raises(DBAPIError) as error:
        async with roles["birja_app"].begin() as conn:
            await conn.execute(text(statement))
    assert error.value.orig.sqlstate in {"42501", "42883"}


async def test_scheduler_cannot_execute_management_or_private_helpers(current):
    _, roles = current
    for statement in (
        "SELECT initialize_portfolio(1)",
        "SELECT * FROM create_portfolio(1,gen_random_uuid(),'Name','')",
        "SELECT * FROM update_portfolio_metadata(1,1,'Name','',true,true)",
        "SELECT portfolio_display_name('Name')",
        "SELECT portfolio_description('')",
    ):
        with pytest.raises(DBAPIError) as error:
            async with roles["birja_scheduler"].begin() as conn:
                await conn.execute(text(statement))
        assert error.value.orig.sqlstate == "42501"


@pytest.mark.parametrize(
    "drift",
    [
        "ALTER FUNCTION initialize_portfolio(bigint) SET search_path=public",
        "ALTER FUNCTION portfolio_name_key(text) SECURITY DEFINER",
        "ALTER TABLE portfolio_creations DROP CONSTRAINT fk_portfolio_creation_owner",
        "ALTER TABLE accounts ALTER COLUMN name_key DROP NOT NULL",
        "ALTER TABLE accounts DISABLE TRIGGER portfolio_metadata_canonical",
        "CREATE FUNCTION public.initialize_portfolio(text) RETURNS bigint "
        "LANGUAGE sql AS $$SELECT 1::bigint$$",
        "GRANT EXECUTE ON FUNCTION portfolio_name_key(text) TO PUBLIC",
        "GRANT CREATE ON SCHEMA public TO birja_app",
        "ALTER ROLE birja_action_operator LOGIN",
    ],
)
async def test_drift_refuses_before_grants(current, drift):
    engine, _ = current
    async with engine.connect() as conn:
        await conn.execute(text(drift))
        with pytest.raises(DBAPIError):
            async with conn.begin_nested():
                await conn.execute(text(PREFLIGHT_SQL))


@pytest.mark.parametrize(
    "drift",
    [
        "REVOKE EXECUTE ON FUNCTION initialize_portfolio(bigint) FROM birja_app",
        "GRANT UPDATE ON users TO birja_app",
        "GRANT INSERT ON accounts TO birja_app",
        "GRANT SELECT ON portfolio_creations TO birja_app",
    ],
)
async def test_missing_or_excess_grants_refuse_current_writes(current, drift):
    engine, _ = current
    async with engine.begin() as conn:
        await conn.execute(text(drift))
        with pytest.raises(SchemaAdmissionError, match="incompatible_authority"):
            async with conn.begin_nested():
                await require_schema(conn)


async def test_all_private_helpers_have_no_nonowner_execute(current):
    engine, _ = current
    private = {
        "check_portfolio_lifecycle_integrity()",
        "check_portfolio_terminal_root()",
        "check_stock_terminal_clock()",
        "check_portfolio_financial_write()",
        "check_stock_fill_integrity()",
        "check_stock_split_digest_version()",
        "reject_stock_dividend_mutation()",
        "stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb)",
        "portfolio_display_name(text)",
        "portfolio_name_key(text)",
        "portfolio_description(text)",
        "check_portfolio_management_metadata()",
    }
    async with engine.connect() as conn:
        actual = (
            (
                await conn.execute(
                    text(
                        "SELECT p.oid::regprocedure::text FROM pg_proc p "
                        "WHERE p.pronamespace='public'::regnamespace AND NOT EXISTS(SELECT FROM "
                        "aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) x "
                        "WHERE x.grantee<>p.proowner)"
                    )
                )
            )
            .scalars()
            .all()
        )
        assert set(actual) == private


async def production_bootstrap():
    path = Path(__file__).parents[2] / "deploy/db/bootstrap-roles.sql"
    password = secrets.token_hex(32)
    found = await asyncio.to_thread(
        subprocess.run,
        ["/usr/bin/docker", "ps", "--filter", "publish=55432", "--format", "{{.ID}}"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    containers = found.stdout.split()
    assert len(containers) == 1
    inspected = await asyncio.to_thread(
        subprocess.run,
        ["/usr/bin/docker", "inspect", containers[0]],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    container = json.loads(inspected.stdout)[0]
    assert container["Config"]["Labels"]["com.docker.compose.service"] == "postgres"
    assert container["NetworkSettings"]["Ports"]["5432/tcp"] == [
        {"HostIp": "127.0.0.1", "HostPort": "55432"}
    ]
    command = [
        "/usr/bin/docker",
        "exec",
        "-i",
        containers[0],
        "psql",
        "-X",
        "-U",
        "birja_test",
        "-d",
        "birja_test",
        "-v",
        "ON_ERROR_STOP=1",
        "-v",
        "apply=true",
        "-v",
        "bootstrap=birja_test",
        "-v",
        "db_name=birja_test",
        "-v",
        f"app_password={password}",
        "-v",
        f"scheduler_password={password}",
        "-v",
        f"migrator_password={password}",
    ]
    result = await asyncio.to_thread(
        subprocess.run, command, input=path.read_text(), capture_output=True, text=True, timeout=30
    )
    return result.returncode, result.stderr.replace(password, "[redacted]")


async def test_production_admin_bootstrap_agrees_with_current_grants(current):
    engine, _ = current
    code, diagnostic = await production_bootstrap()
    assert code == 0, diagnostic
    async with engine.connect() as conn:
        assert await require_schema(conn) == "0023"


@pytest.mark.parametrize("disabled", [False, True])
async def test_unexpected_grant_rewrite_refuses_runtime_and_bootstrap(current, disabled):
    engine, roles = current
    async with engine.begin() as conn:
        await conn.execute(
            text("""CREATE RULE unexpected_grant AS
            ON INSERT TO public.portfolio_creations DO ALSO UPDATE public.accounts
            SET cash=cash+NEW.amount WHERE id=NEW.portfolio_id""")
        )
        if disabled:
            await conn.execute(
                text("ALTER TABLE portfolio_creations DISABLE RULE unexpected_grant")
            )
        before = (await conn.execute(text("SELECT count(*),sum(cash) FROM accounts"))).one()
    async with roles["birja_app"].connect() as conn:
        with pytest.raises(SchemaAdmissionError, match="incompatible_authority"):
            await require_schema(conn)
    async with engine.connect() as conn:
        with pytest.raises(DBAPIError, match="rewrite"):
            async with conn.begin_nested():
                await conn.execute(text(PREFLIGHT_SQL))
    code, diagnostic = await production_bootstrap()
    assert code != 0 and "rewrite" in diagnostic, diagnostic
    async with engine.connect() as conn:
        assert (await conn.execute(text("SELECT count(*),sum(cash) FROM accounts"))).one() == before
        assert not (await conn.execute(text("SELECT id FROM portfolio_creations"))).all()


@pytest.mark.parametrize("role", ["birja_app", "birja_scheduler"])
async def test_implicit_database_owner_create_refuses_admission_and_bootstrap(current, role):
    engine, roles = current
    async with engine.begin() as conn:
        assert (await conn.execute(text("SELECT current_database(),current_user"))).one() == (
            "birja_test",
            "birja_test",
        )
        await conn.execute(text("ALTER SCHEMA public OWNER TO pg_database_owner"))
        await conn.execute(text(f"ALTER DATABASE birja_test OWNER TO {role}"))  # noqa: S608 - fixed role matrix
    try:
        async with roles[role].connect() as conn:
            assert (
                await conn.execute(
                    text("SELECT has_schema_privilege(current_user,'public','CREATE')")
                )
            ).scalar_one() is True
            with pytest.raises(SchemaAdmissionError, match="incompatible_authority"):
                await require_schema(conn)
        async with engine.connect() as conn:
            with pytest.raises(DBAPIError, match="ownership|schema"):
                async with conn.begin_nested():
                    await conn.execute(text(PREFLIGHT_SQL))
        code, _ = await production_bootstrap()
        assert code != 0
    finally:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER DATABASE birja_test OWNER TO birja_test"))
            await conn.execute(text("ALTER SCHEMA public OWNER TO birja_test"))


@pytest.mark.parametrize("schema_owner", ["birja_test", "pg_database_owner"])
async def test_valid_administrative_schema_ownership_is_admitted(current, schema_owner):
    engine, roles = current
    async with engine.begin() as conn:
        await conn.execute(text(f"ALTER SCHEMA public OWNER TO {schema_owner}"))  # noqa: S608 - fixed owner matrix
    async with roles["birja_app"].connect() as conn:
        assert await require_schema(conn) == "0023"
