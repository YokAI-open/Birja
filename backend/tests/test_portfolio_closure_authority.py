"""Real authenticated0023 SQL authority; runtime admission belongs to Plan04."""

import asyncio
import hashlib
import secrets
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from tests.portfolio_fixtures import reset_disposable_schema
from tests.test_migrations import ensure_dividend_test_owner, run_test_migration, test_migration_url
from tests.test_portfolio_closure_migrations import root

CLOSE = "SELECT * FROM public.close_portfolio(:u,:p,:k,:n,:policy)"
POLICY = "freeze_at_closure_v1"
BACKEND = Path(__file__).parents[1]


@pytest_asyncio.fixture
async def authority(engine):
    await reset_disposable_schema(engine)
    await asyncio.to_thread(run_test_migration, "0022")
    if (BACKEND / "alembic/versions/0023_portfolio_closure_authority.py").exists():
        await asyncio.to_thread(run_test_migration, "0023")
    password = secrets.token_hex(32)
    async with engine.begin() as conn:
        await conn.execute(text(f"ALTER ROLE birja_app LOGIN PASSWORD '{password}'"))  # noqa: S608
    app = create_async_engine(make_url(engine.url).set(username="birja_app", password=password))
    migrator = create_async_engine(test_migration_url())
    try:
        yield app, migrator, engine
    finally:
        await app.dispose()
        await migrator.dispose()
        await reset_disposable_schema(engine)
        await asyncio.to_thread(run_test_migration, "0020")


def intent(owner, portfolio, name="Strategy", key=None):
    return {"u": owner, "p": portfolio, "k": key or uuid4(), "n": name, "policy": POLICY}


async def call(app, payload):
    async with app.begin() as conn:
        return (await conn.execute(text(CLOSE), payload)).one()


async def reject(app, payload, state, message=None):
    with pytest.raises(DBAPIError) as error:
        await call(app, payload)
    assert error.value.orig.sqlstate == state, str(error.value.orig)
    if message:
        assert message in str(error.value.orig)


async def test_named_closure_is_atomic_immutable_and_preserves_finances(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
        before = (await conn.execute(text("SELECT cash,starting_cash FROM accounts WHERE id=:p"),
                                     {"p": portfolio})).one()
    result = await call(app, intent(owner, portfolio))
    assert tuple(result) == (portfolio, "closed", False)
    async with migrator.connect() as conn:
        after = (await conn.execute(text("SELECT cash,starting_cash FROM accounts WHERE id=:p"),
                                    {"p": portfolio})).one()
        assert before == after
        assert (await conn.execute(text("""SELECT a.closed_at=c.closed_at,
            c.provenance,c.confirmation_name,c.closed_at=i.recorded_at,i.outcome
            FROM accounts a JOIN portfolio_lifecycle_closures c ON c.portfolio_id=a.id
            JOIN portfolio_closure_intents i ON i.id=c.intent_id WHERE a.id=:p"""),
                                   {"p": portfolio})).one() == (
                                       True, "owner_confirmation", "Strategy", True, "closed")
        for table in ("trades", "stock_dividend_payments", "stock_ownership_movements"):
            assert (await conn.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one() == 0  # noqa: S608


async def test_replay_original_never_retargets_reused_name(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
    payload = intent(owner, portfolio)
    await call(app, payload)
    async with app.begin() as conn:
        replacement = (await conn.execute(text(
            "SELECT portfolio_id FROM create_portfolio(:u,:k,'Strategy','')"),
            {"u": owner, "k": uuid4()})).scalar_one()
    assert tuple(await call(app, payload)) == (portfolio, "closed", True)
    await reject(app, {**payload, "p": replacement}, "23505", "closure_intent_conflict")
    async with migrator.connect() as conn:
        assert (await conn.execute(text("SELECT closed_at,cash FROM accounts WHERE id=:p"),
                                   {"p": replacement})).one() == (None, 10000)
        assert (await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))).scalar_one() == 1


async def test_replay_key_body_and_foreign_input_refusals(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
        foreign, _ = await root(conn)
    payload = intent(owner, portfolio)
    for changes in ({"u": foreign}, {"p": 999999999}):
        await reject(app, {**payload, **changes}, "P0002", "portfolio_unavailable")
    for changes in ({"policy": "other"}, {"n": " Strategy "}, {"k": None}):
        await reject(app, {**payload, **changes}, "22023")
    await call(app, payload)
    await reject(app, {**payload, "n": "Other"}, "23505", "closure_intent_conflict")


async def test_rollback_leaves_no_boundary_or_outcome(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
    async with app.connect() as conn:
        await conn.execute(text(CLOSE), intent(owner, portfolio))
        await conn.rollback()
    async with migrator.connect() as conn:
        assert (await conn.execute(text("SELECT closed_at FROM accounts WHERE id=:p"),
                                   {"p": portfolio})).scalar_one() is None
        for table in ("portfolio_closure_intents", "portfolio_lifecycle_closures"):
            assert (await conn.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one() == 0  # noqa: S608


async def test_named_only_exact_app_signature_has_authority(authority):
    app, migrator, admin = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
    async with admin.begin() as conn:
        for role in ("birja_app", "birja_scheduler"):
            assert (await conn.execute(text("SELECT has_function_privilege(:r,"
                "'public.close_portfolio(bigint,bigint,uuid,text,text)','EXECUTE')"),
                {"r": role})).scalar_one() is (role == "birja_app")
            await conn.execute(text(f"SET LOCAL ROLE {role}"))  # noqa: S608
            with pytest.raises(DBAPIError) as error:
                async with conn.begin_nested():
                    await conn.execute(text("UPDATE accounts SET closed_at=clock_timestamp() WHERE id=:p"),
                                       {"p": portfolio})
            assert error.value.orig.sqlstate == "42501"
            await conn.execute(text("RESET ROLE"))
    assert tuple(await call(app, intent(owner, portfolio))) == (portfolio, "closed", False)


async def test_replay_concurrent_original_has_one_outcome(authority):
    app, migrator, _ = authority
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
    payload = intent(owner, portfolio)
    results = await asyncio.gather(call(app, payload), call(app, payload))
    assert sorted(r.replayed for r in results) == [False, True]
    async with migrator.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))).scalar_one() == 1


async def test_migration_checksum_and_authenticated_owner_are_required(authority):
    app, _, _ = authority
    from importlib.util import module_from_spec, spec_from_file_location

    path = BACKEND / "alembic/versions/0023_portfolio_closure_authority.py"
    spec = spec_from_file_location("closure_authority", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hashlib.sha256((BACKEND / "alembic/sql/0023_portfolio_closure.sql").read_bytes()).hexdigest() == module.SQL_SHA256
    async with app.connect() as conn:
        settings = (await conn.execute(text("SELECT proconfig FROM pg_proc WHERE oid="
            "'public.close_portfolio(bigint,bigint,uuid,text,text)'::regprocedure"))).scalar_one()
        assert {"search_path=pg_catalog, public, pg_temp", "lock_timeout=2s",
                "statement_timeout=10s", "idle_in_transaction_session_timeout=30s"} <= set(settings)
    await ensure_dividend_test_owner()
