"""Actual revision admission and refusal before startup or request writes."""

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.schema_contract import SchemaAdmissionError, require_schema
from app.main import create_app
from tests.portfolio_fixtures import (
    economic_snapshot,
    migrate_to,
    portfolio_migration_db,
    seed_owned_crypto_trade,
    seed_portfolio_world,
)
from tests.test_migrations import install_current_test_grants, test_migration_url

__all__ = ["portfolio_migration_db"]


@pytest.mark.parametrize("revision", ["0015", "0016"])
async def test_intermediate_startup_refuses_explicit_migration_only(
    portfolio_migration_db, settings, revision
):
    engine = portfolio_migration_db
    await migrate_to(revision)
    async with engine.connect() as conn:
        before = await economic_snapshot(conn)
    app = create_app(settings)
    with pytest.raises(SchemaAdmissionError) as failure:
        async with app.router.lifespan_context(app):
            pytest.fail("intermediate runtime started")
    assert failure.value.reason == "migration_only"
    async with engine.connect() as conn:
        assert await economic_snapshot(conn) == before


@pytest.mark.parametrize("revision", ["0015", "0016"])
async def test_intermediate_request_write_gate_refuses_before_endpoint(
    portfolio_migration_db, settings, revision
):
    engine = portfolio_migration_db
    await migrate_to(revision)
    app = create_app(settings)
    # ASGI tests explicitly omit startup to exercise the independent write gate.
    # This route exists only in the test app and is never added to product code.
    app.state.engine = engine
    reached = []

    @app.post("/write-probe")
    async def probe():
        reached.append(True)
        return {"written": True}

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://test"
    ) as client:
        result = await client.post("/write-probe")
    assert result.status_code == 503
    assert result.json()["detail"]["code"] == "schema_unavailable"
    assert reached == []


@pytest.mark.parametrize(
    "revision",
    [
        "0007",
        "0008",
        "0009",
        "0010",
        "0011",
        "0012",
        "0013",
        "0014",
        "0017",
        "0023",
        "0024",
        "0025",
    ],
)
async def test_current_startup_refuses_retained_schema_without_repair(
    portfolio_migration_db, settings, revision
):
    engine = portfolio_migration_db
    await migrate_to(revision)
    app = create_app(settings)
    with pytest.raises(SchemaAdmissionError) as failure:
        async with app.router.lifespan_context(app):
            pytest.fail("old schema admitted")
    assert failure.value.reason == "incompatible_schema"
    async with engine.connect() as conn:
        assert (
            await conn.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one() == revision


@pytest.mark.parametrize("consumer", ["retained0008", "retained0014"])
async def test_retained_consumer_refuses_final_schema_without_changes(
    portfolio_migration_db, consumer
):
    engine = portfolio_migration_db
    await migrate_to("0017")
    async with engine.connect() as conn:
        before = await economic_snapshot(conn)
        with pytest.raises(SchemaAdmissionError) as failure:
            await require_schema(conn, consumer=consumer)
        assert failure.value.reason == "incompatible_schema"
        assert await economic_snapshot(conn) == before


@pytest.mark.parametrize(
    "revision,consumer",
    [
        ("0007", "retained0008"),
        ("0008", "retained0008"),
        ("0013", "retained0014"),
        ("0014", "retained0014"),
        ("0023", "retained0023"),
        ("0024", "retained0024"),
        ("0025", "retained0025"),
    ],
)
async def test_retained_lane_admits_only_its_reviewed_schema(
    portfolio_migration_db, revision, consumer
):
    await migrate_to(revision)
    if revision in {"0023", "0024", "0025"}:
        await install_current_test_grants()
    async with portfolio_migration_db.connect() as conn:
        assert await require_schema(conn, consumer=consumer) == revision


async def test_final_startup_and_write_admission_accepts_actual_final_schema(
    portfolio_migration_db, settings
):
    await migrate_to("head")
    await install_current_test_grants()
    app = create_app(settings)
    reached = []

    @app.post("/write-probe")
    async def probe():
        reached.append(True)
        return {"written": True}

    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://test"
        ) as client,
    ):
        result = await client.post("/write-probe")
    assert result.status_code == 200
    assert reached == [True]


async def test_catalog_current_upgrade_preserves_retained_0025_ledger(portfolio_migration_db):
    engine = portfolio_migration_db
    await migrate_to("0025")
    migrator = create_async_engine(test_migration_url())
    try:
        async with migrator.begin() as conn:
            world = await seed_portfolio_world(conn)
            await seed_owned_crypto_trade(conn, world, world.first)
            before = await economic_snapshot(conn)
            assert before["trades"]
    finally:
        await migrator.dispose()
    await install_current_test_grants()
    async with engine.connect() as conn:
        assert await require_schema(conn, consumer="retained0025") == "0025"

    await migrate_to("head")
    await install_current_test_grants()
    async with engine.connect() as conn:
        assert await require_schema(conn) == "0026"
        with pytest.raises(SchemaAdmissionError, match="incompatible_schema"):
            await require_schema(conn, consumer="retained0025")
        assert await economic_snapshot(conn) == before


@pytest.mark.parametrize(
    "drift",
    [
        "CREATE INDEX unexpected_catalog_index ON public.stock_catalog_financial_quotes (source)",
        "REVOKE SELECT ON public.stock_catalog_instruments FROM birja_app",
        "GRANT SELECT (reference) ON public.stock_catalog_admissions TO birja_app",
    ],
    ids=["unexpected-index", "missing-read", "additional-read"],
)
async def test_catalog_runtime_refuses_schema_or_authority_drift(engine, migrated, drift):
    async with engine.connect() as conn, conn.begin():
        assert await require_schema(conn) == "0026"
        with pytest.raises(SchemaAdmissionError, match="incompatible_authority"):
            async with conn.begin_nested():
                await conn.execute(text(drift))
                await require_schema(conn)
        assert await require_schema(conn) == "0026"


async def test_uninitialized_schema_refuses_instead_of_auto_migrating(portfolio_migration_db):
    async with portfolio_migration_db.connect() as conn:
        with pytest.raises(SchemaAdmissionError) as failure:
            await require_schema(conn)
        assert failure.value.reason == "schema_unavailable"


@pytest.mark.parametrize("malformation", ["multiple", "wrong_column_type"])
async def test_actual_malformed_revision_metadata_refuses(portfolio_migration_db, malformation):
    await migrate_to("0014")
    async with portfolio_migration_db.connect() as conn, conn.begin():
        if malformation == "multiple":
            await conn.execute(text("INSERT INTO alembic_version(version_num) VALUES ('0013')"))
        else:
            # Deliberate disposable catalogue corruption, never a valid schema
            # migration: the admitted protocol requires a text revision value.
            await conn.execute(
                text(
                    "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE integer "
                    "USING version_num::integer"
                )
            )
    # Fresh driver metadata must actually return the malformed integer rather
    # than stop earlier at a stale prepared-plan error from ALTER COLUMN.
    fresh = create_async_engine(portfolio_migration_db.url)
    try:
        async with fresh.connect() as conn:
            if malformation == "wrong_column_type":
                assert (
                    type(
                        (
                            await conn.execute(text("SELECT version_num FROM alembic_version"))
                        ).scalar_one()
                    )
                    is int
                )
            with pytest.raises(SchemaAdmissionError) as failure:
                await require_schema(conn)
            assert failure.value.reason == "schema_unavailable"
    finally:
        await fresh.dispose()


@pytest.mark.parametrize("role", ["birja_app", "birja_scheduler"])
async def test_restricted_runtime_role_can_read_schema_admission(engine, migrated, role):
    async with engine.connect() as conn, conn.begin():
        await conn.execute(text(f"SET LOCAL ROLE {role}"))  # noqa: S608 - fixed role matrix
        assert await require_schema(conn) == "0026"
        assert not (
            await conn.execute(
                text("SELECT has_table_privilege(current_user,'alembic_version','UPDATE')")
            )
        ).scalar_one()
        await conn.execute(text("SELECT id, ticker FROM public.stock_catalog_listings"))
        await conn.execute(text("SELECT id, fields, scope FROM public.stock_catalog_admissions"))
        await conn.execute(
            text("SELECT catalog_id, listing_id FROM public.stock_catalog_instruments")
        )
        await conn.execute(
            text("SELECT coin_id, bid, ask FROM public.stock_catalog_financial_quotes")
        )
        assert (
            await conn.execute(
                text("""SELECT
                  has_column_privilege(current_user,'stock_catalog_admissions','reference','SELECT'),
                  has_table_privilege(current_user,'stock_catalog_listings','INSERT,UPDATE,DELETE'),
                  has_sequence_privilege(current_user,'stock_catalog_listings_id_seq','USAGE,UPDATE'),
                  has_table_privilege(current_user,'stock_catalog_admissions','INSERT,UPDATE,DELETE')
                """)
            )
        ).one() == (False, False, False, False)
        assert (
            await conn.execute(
                text("""SELECT
                  has_table_privilege(current_user,'stock_catalog_instruments','INSERT,UPDATE,DELETE'),
                  has_table_privilege(current_user,'stock_catalog_fill_evidence','UPDATE,DELETE'),
                  has_table_privilege(current_user,'stock_catalog_financial_quotes','UPDATE'),
                  has_table_privilege(current_user,'stock_catalog_action_coverage','UPDATE'),
                  has_table_privilege(current_user,'stock_catalog_status','UPDATE'),
                  has_table_privilege(current_user,'stock_catalog_status','DELETE'),
                  has_table_privilege(current_user,'stock_catalog_fill_evidence','INSERT'),
                  has_function_privilege(current_user,
                    'assert_catalog_stock_execution_current(bigint,bigint,jsonb)','EXECUTE'),
                  has_function_privilege(current_user,
                    'apply_stock_action_resolution(bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text)',
                    'EXECUTE')
                """)
            )
        ).one() == (
            False,
            False,
            role == "birja_scheduler",
            role == "birja_scheduler",
            role == "birja_scheduler",
            False,
            role == "birja_app",
            role == "birja_app",
            False,
        )


async def test_catalog_operator_grant_is_limited_to_checked_resolution(engine, migrated):
    async with engine.connect() as conn, conn.begin():
        await conn.execute(text("SET LOCAL ROLE birja_action_operator"))
        assert (
            await conn.execute(
                text("""SELECT
                  has_function_privilege(current_user,
                    'apply_stock_action_resolution(bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text)',
                    'EXECUTE'),
                  has_table_privilege(current_user,'stock_catalog_action_coverage','SELECT,INSERT,UPDATE,DELETE'),
                  has_table_privilege(current_user,'stock_catalog_fill_evidence','SELECT,INSERT,UPDATE,DELETE')
                """)
            )
        ).one() == (True, False, False)
