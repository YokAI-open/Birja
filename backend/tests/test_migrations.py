import asyncio
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import command

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
    assert await _versions(engine) == ["0001"]

    await asyncio.to_thread(command.downgrade, cfg, "base")
    assert await _versions(engine) == []

    await asyncio.to_thread(command.upgrade, cfg, "head")
    assert await _versions(engine) == ["0001"]


def test_baseline_is_head() -> None:
    script = ScriptDirectory.from_config(_config())
    assert script.get_heads() == ["0001"]
