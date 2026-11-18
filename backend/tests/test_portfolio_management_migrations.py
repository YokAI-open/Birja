"""Explicit migration-only harness; never admit the current app at0018/19."""

import asyncio
from decimal import Decimal
from importlib import import_module
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
