"""Actual revision admission and refusal before startup or request writes."""

import httpx
import pytest

from app.db.schema_contract import SchemaAdmissionError, require_schema
from app.main import create_app
from tests.portfolio_fixtures import economic_snapshot, migrate_to, portfolio_migration_db

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
    "revision", ["0007", "0008", "0009", "0010", "0011", "0012", "0013", "0014"]
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
        from sqlalchemy import text

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
    ],
)
async def test_retained_lane_admits_only_its_reviewed_schema(
    portfolio_migration_db, revision, consumer
):
    await migrate_to(revision)
    async with portfolio_migration_db.connect() as conn:
        assert await require_schema(conn, consumer=consumer) == revision


async def test_final_startup_and_write_admission_accepts_actual_final_schema(
    portfolio_migration_db, settings
):
    await migrate_to("0017")
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


async def test_uninitialized_schema_refuses_instead_of_auto_migrating(portfolio_migration_db):
    async with portfolio_migration_db.connect() as conn:
        with pytest.raises(SchemaAdmissionError) as failure:
            await require_schema(conn)
        assert failure.value.reason == "schema_unavailable"


@pytest.mark.parametrize("role", ["birja_app", "birja_scheduler"])
async def test_restricted_runtime_role_can_read_schema_admission(engine, migrated, role):
    from sqlalchemy import text

    async with engine.connect() as conn, conn.begin():
        await conn.execute(text(f"SET LOCAL ROLE {role}"))  # noqa: S608 - fixed role matrix
        assert await require_schema(conn) == "0017"
        assert not (
            await conn.execute(
                text("SELECT has_table_privilege(current_user,'alembic_version','UPDATE')")
            )
        ).scalar_one()
