import asyncio
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine

import app.models  # noqa: F401
from app.db.base import Base

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _config() -> Config:
    return Config(str(BACKEND_DIR / "alembic.ini"))


async def _versions(engine: AsyncEngine) -> list[str]:
    try:
        async with engine.connect() as conn:
            rows = await conn.execute(text("SELECT version_num FROM alembic_version"))
            return [r[0] for r in rows]
    except ProgrammingError:
        return []


async def test_upgrade_downgrade_roundtrip(engine: AsyncEngine) -> None:
    cfg = _config()
    # Alembic's async env.py calls asyncio.run, so run it in a worker thread
    # with no running loop; the session loop is never touched.
    await asyncio.to_thread(command.upgrade, cfg, "head")
    assert await _versions(engine) == ["0005"]

    await asyncio.to_thread(command.downgrade, cfg, "base")
    assert await _versions(engine) == []

    await asyncio.to_thread(command.upgrade, cfg, "head")
    assert await _versions(engine) == ["0005"]


def test_baseline_is_head() -> None:
    script = ScriptDirectory.from_config(_config())
    assert script.get_heads() == ["0005"]


async def test_models_match_schema(engine: AsyncEngine) -> None:
    await asyncio.to_thread(command.upgrade, _config(), "head")

    def _diff(sync_conn):  # type: ignore[no-untyped-def]
        ctx = MigrationContext.configure(sync_conn, opts={"compare_type": True})
        return compare_metadata(ctx, Base.metadata)

    async with engine.connect() as conn:
        diff = await conn.run_sync(_diff)
    assert diff == []
