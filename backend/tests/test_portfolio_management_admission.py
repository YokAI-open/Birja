"""Current admission and genuine finite migration identities on disposable PostgreSQL."""

import asyncio
import subprocess
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.portfolio_migrate import require_migrator, require_source
from app.db.schema_contract import SchemaAdmissionError, require_schema
from tests.portfolio_fixtures import reset_disposable_schema
from tests.test_migrations import run_test_migration, test_migration_url


@pytest_asyncio.fixture
async def staged(engine):
    await reset_disposable_schema(engine)
    try:
        yield engine
    finally:
        await reset_disposable_schema(engine)


@pytest.mark.parametrize(
    "revision", ["0007", "0008", "0014", "0015", "0016", "0017", "0018", "0019"]
)
async def test_current_refuses_every_retained_or_partial_before_writes(staged, revision):
    await asyncio.to_thread(run_test_migration, revision)
    async with staged.connect() as conn:
        before = (await conn.execute(text("SELECT count(*) FROM users"))).scalar_one()
        with pytest.raises(SchemaAdmissionError):
            await require_schema(conn)
        assert (await conn.execute(text("SELECT count(*) FROM users"))).scalar_one() == before


async def test_complete_current_and_actual_retained_source_refusal(staged):
    await asyncio.to_thread(run_test_migration, "0020")
    old_source = (
        await asyncio.to_thread(
            subprocess.run,
            ["/usr/bin/git", "show", "4b4320b:backend/app/db/schema_contract.py"],
            check=True,
            capture_output=True,
            text=True,
        )
    ).stdout
    namespace = {}
    exec(compile(old_source, "retained0017/schema_contract.py", "exec"), namespace)  # noqa: S102 - pinned trusted git source
    async with staged.connect() as conn:
        assert await require_schema(conn) == "0020"
        with pytest.raises(namespace["SchemaAdmissionError"], match="incompatible_schema"):
            await namespace["require_schema"](conn)


@pytest.mark.parametrize("versions", [[], ["0020", "0017"], ["0020x"], ["9999"]])
async def test_malformed_revision_refuses(staged, versions):
    await asyncio.to_thread(run_test_migration, "0020")
    async with staged.begin() as conn:
        await conn.execute(text("DELETE FROM alembic_version"))
        for revision in versions:
            await conn.execute(text("INSERT INTO alembic_version VALUES (:v)"), {"v": revision})
        with pytest.raises(SchemaAdmissionError):
            await require_schema(conn)


async def test_genuine_migrator_admits_finite_forward_path_and_denies_admin(staged):
    # public CREATE is explicitly removed, even in this disposable admin schema.
    async with staged.begin() as conn:
        await conn.execute(text("ALTER SCHEMA public OWNER TO pg_database_owner"))
        await conn.execute(
            text("REVOKE CREATE ON SCHEMA public FROM PUBLIC,birja_app,birja_scheduler")
        )
    migrator = create_async_engine(test_migration_url())
    try:
        for revision in ("0017", "0018", "0019", "0020"):
            await asyncio.to_thread(run_test_migration, revision)
            async with migrator.connect() as conn:
                assert await require_migrator(conn) == revision
            async with staged.connect() as conn:
                with pytest.raises(ValueError, match="Authenticated restricted migrator"):
                    await require_migrator(conn)
    finally:
        await migrator.dispose()


def test_source_assets_are_finite_and_tampering_refuses(tmp_path):
    from app.db.portfolio_migrate import SOURCE

    assert set(SOURCE) >= {
        "alembic/versions/0018_portfolio_management_expansion.py",
        "alembic/versions/0019_portfolio_management_backfill.py",
        "alembic/versions/0020_portfolio_management_authority.py",
        "alembic/sql/0019_portfolio_metadata.sql",
        "alembic/sql/0020_portfolio_management.sql",
    }
    require_source()
    root = Path(__file__).resolve().parents[1]
    for name in SOURCE:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((root / name).read_bytes())
    target = tmp_path / "alembic/sql/0020_portfolio_management.sql"
    target.write_bytes(target.read_bytes() + b"\n-- drift\n")
    with pytest.raises(ValueError, match="Untrusted"):
        require_source(tmp_path)
