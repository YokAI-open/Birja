"""Independent current catalogue and authenticated least privilege contracts."""

import asyncio
import secrets
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.portfolio_bootstrap import GRANTS_SQL, PREFLIGHT_SQL
from tests.portfolio_fixtures import reset_disposable_schema
from tests.test_migrations import run_test_migration, test_migration_url


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
            await conn.execute(text("INSERT INTO accounts(user_id,name,cash,starting_cash) "
                                    "SELECT id,'Legacy',123.45,7777 FROM users"))
        await migrator.dispose()
    await asyncio.to_thread(run_test_migration, "0020")
    passwords = {role: secrets.token_hex(32) for role in ("birja_app", "birja_scheduler")}
    async with engine.begin() as conn:
        await conn.execute(text("REVOKE CREATE ON SCHEMA public FROM PUBLIC,birja_app,birja_scheduler"))
        await conn.execute(text(PREFLIGHT_SQL))
        await sql(conn, GRANTS_SQL)
        for role, password in passwords.items():
            await conn.execute(text(f"ALTER ROLE {role} LOGIN PASSWORD '{password}'"))  # noqa: S608
    roles = {role: create_async_engine(make_url(engine.url).set(username=role,password=password))
             for role,password in passwords.items()}
    try:
        yield engine, roles
    finally:
        for db in roles.values():
            await db.dispose()
        await reset_disposable_schema(engine)


async def test_bootstrap_preserves_money_and_exact_roles(current):
    engine, roles = current
    async with roles["birja_app"].begin() as conn:
        assert (await conn.execute(text("SELECT session_user,current_user"))).one() == (
            "birja_app", "birja_app")
        uid = (await conn.execute(text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                                 {"e":f"grants-{uuid4()}@example.test"})).scalar_one()
        root = (await conn.execute(text("SELECT initialize_portfolio(:u)"),{"u":uid})).scalar_one()
        await conn.execute(text("UPDATE accounts SET cash=cash-1 WHERE id=:p"),{"p":root})
        assert (await conn.execute(text("SELECT cash,starting_cash FROM accounts WHERE id=:p"),
                                   {"p":root})).one() == (9999,10000)
    async with engine.connect() as conn:
        legacy = (await conn.execute(text("SELECT cash,starting_cash FROM accounts "
                                          "WHERE name='Legacy'"))).all()
        assert all(str(r.cash)=="123.45000000" and r.starting_cash==7777 for r in legacy)
        routines = (await conn.execute(text("SELECT count(*) FROM pg_proc "
                    "WHERE pronamespace='public'::regnamespace"))).scalar_one()
        assert routines == 17
        assert not (await conn.execute(text("SELECT has_table_privilege('birja_app',"
            "'accounts','INSERT'),has_table_privilege('birja_app','users','UPDATE')"))).one()[0]


@pytest.mark.parametrize("statement", [
    "INSERT INTO accounts(user_id,cash,starting_cash) VALUES (1,10000,10000)",
    "UPDATE accounts SET name='forged'", "UPDATE accounts SET name_key='forged'",
    "UPDATE accounts SET description='forged'", "UPDATE accounts SET starting_cash=20000",
    "UPDATE accounts SET closed_at=clock_timestamp()", "UPDATE users SET email='forged'",
    "INSERT INTO portfolio_initializations(user_id,origin) VALUES (1,'legacy')",
    "UPDATE portfolio_creations SET amount=20000", "DELETE FROM portfolio_creations",
    "SELECT nextval('accounts_id_seq')", "CREATE TABLE public.forged(id bigint)",
    "SELECT portfolio_name_key('private')", "SELECT check_portfolio_management_metadata()",
    "SELECT * FROM create_portfolio(1,gen_random_uuid(),'forged','',20000)",
])
async def test_ordinary_forgery_denied(current, statement):
    _, roles = current
    with pytest.raises(DBAPIError) as error:
        async with roles['birja_app'].begin() as conn:
            await conn.execute(text(statement))
    assert error.value.orig.sqlstate in {'42501','42883'}


async def test_scheduler_cannot_execute_management_or_private_helpers(current):
    _,roles = current
    for statement in ("SELECT initialize_portfolio(1)",
        "SELECT * FROM create_portfolio(1,gen_random_uuid(),'Name','')",
        "SELECT * FROM update_portfolio_metadata(1,1,'Name','',true,true)",
        "SELECT portfolio_display_name('Name')", "SELECT portfolio_description('')"):
        with pytest.raises(DBAPIError) as error:
            async with roles['birja_scheduler'].begin() as conn:
                await conn.execute(text(statement))
        assert error.value.orig.sqlstate == '42501'


@pytest.mark.parametrize('drift',[
    'ALTER FUNCTION initialize_portfolio(bigint) SET search_path=public',
    'ALTER FUNCTION portfolio_name_key(text) SECURITY DEFINER',
    'ALTER TABLE portfolio_creations DROP CONSTRAINT fk_portfolio_creation_owner',
    'ALTER TABLE accounts ALTER COLUMN name_key DROP NOT NULL',
    'ALTER TABLE accounts DISABLE TRIGGER portfolio_management_metadata',
    'CREATE FUNCTION public.initialize_portfolio(text) RETURNS bigint LANGUAGE sql AS $$SELECT 1::bigint$$',
    'GRANT EXECUTE ON FUNCTION portfolio_name_key(text) TO PUBLIC',
    'GRANT CREATE ON SCHEMA public TO birja_app',
])
async def test_drift_refuses_before_grants(current,drift):
    engine,_ = current
    async with engine.begin() as conn:
        await conn.execute(text(drift))
        with pytest.raises(DBAPIError):
            async with conn.begin_nested():
                await conn.execute(text(PREFLIGHT_SQL))
