import asyncio
import io
from pathlib import Path

import pytest
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
from tests.helpers import unique_email

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
    assert await _versions(engine) == ["0008"]

    await asyncio.to_thread(command.downgrade, cfg, "base")
    assert await _versions(engine) == []

    await asyncio.to_thread(command.upgrade, cfg, "head")
    assert await _versions(engine) == ["0008"]


def test_baseline_is_head() -> None:
    script = ScriptDirectory.from_config(_config())
    assert script.get_heads() == ["0008"]


async def test_populated_history_index_roundtrip(engine: AsyncEngine) -> None:
    cfg = _config()
    await asyncio.to_thread(command.upgrade, cfg, "head")
    await asyncio.to_thread(command.downgrade, cfg, "0007")

    async def snapshot():
        async with engine.connect() as conn:
            rows = {
                table: (await conn.execute(text(f"SELECT * FROM {table} ORDER BY id"))).all()
                for table in ("users", "accounts", "holdings", "trades")
            }
            constraints = (
                await conn.execute(text("""SELECT conrelid::regclass::text, conname,
                pg_get_constraintdef(oid) FROM pg_constraint
                WHERE conrelid IN ('accounts'::regclass, 'holdings'::regclass, 'trades'::regclass)
                ORDER BY conrelid, conname"""))
            ).all()
            return rows, constraints

    try:
        async with engine.begin() as conn:
            uid = (await conn.execute(text("INSERT INTO users (email) VALUES (:e) RETURNING id"),
                                      {"e": unique_email("history-index")})).scalar_one()
            cid = (await conn.execute(text("SELECT id FROM coins WHERE symbol = 'BTC'"))).scalar_one()
            await conn.execute(text("""INSERT INTO accounts (user_id, cash, starting_cash)
                VALUES (:u, 9800, 10000)"""), {"u": uid})
            await conn.execute(text("""INSERT INTO holdings (user_id, coin_id, quantity, cost_basis)
                VALUES (:u, :c, 2, 200)"""), {"u": uid, "c": cid})
            await conn.execute(text("""INSERT INTO trades
                (user_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
                 exec_price,fee,cash_delta,cash_after,idempotency_key)
                SELECT :u,:c,'buy','quantity',1,1,99.75,now(),99.75,0.25,-100,
                       10000 - n * 100,gen_random_uuid() FROM generate_series(1,2) AS n"""),
                               {"u": uid, "c": cid})
        before = await snapshot()
        await asyncio.to_thread(command.upgrade, cfg, "0008")
        assert await _versions(engine) == ["0008"]
        async with engine.connect() as conn:
            index = (await conn.execute(text("""SELECT indisvalid, indisready,
                pg_get_indexdef(indexrelid), ARRAY(
                  SELECT a.attname FROM unnest(i.indkey) WITH ORDINALITY AS k(attnum, pos)
                  JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = k.attnum
                  ORDER BY k.pos)
                FROM pg_index i WHERE indexrelid = 'ix_trades_user_created_id'::regclass"""))).one()
        assert index[0] is True and index[1] is True
        assert index[2] == "CREATE INDEX ix_trades_user_created_id ON public.trades USING btree (user_id, created_at, id)"
        assert index[3] == ["user_id", "created_at", "id"]
        assert await snapshot() == before
        await asyncio.to_thread(command.downgrade, cfg, "0007")
        assert await _versions(engine) == ["0007"]
        async with engine.connect() as conn:
            assert (await conn.execute(text("SELECT to_regclass('ix_trades_user_created_id')"))).scalar_one() is None
        assert await snapshot() == before
        await asyncio.to_thread(command.upgrade, cfg, "head")
        assert await _versions(engine) == ["0008"]
        assert await snapshot() == before
    finally:
        await asyncio.to_thread(command.upgrade, cfg, "head")


def test_history_index_offline_transactions() -> None:
    output = io.StringIO()
    cfg = _config()
    cfg.output_buffer = output
    command.upgrade(cfg, "0007:0008", sql=True)
    sql = output.getvalue()
    assert "CREATE INDEX CONCURRENTLY ix_trades_user_created_id ON trades (user_id, created_at, id)" in sql
    assert sql.index("COMMIT;") < sql.index("CREATE INDEX CONCURRENTLY") < sql.rindex("BEGIN;")
    output.seek(0)
    output.truncate()
    command.downgrade(cfg, "0008:0007", sql=True)
    sql = output.getvalue()
    assert "DROP INDEX CONCURRENTLY ix_trades_user_created_id" in sql
    assert sql.index("COMMIT;") < sql.index("DROP INDEX CONCURRENTLY") < sql.rindex("BEGIN;")


async def test_cents_migration_refuses_sub_cent_cash(engine: AsyncEngine) -> None:
    cfg = _config()
    email = unique_email("subcent")
    await asyncio.to_thread(command.upgrade, cfg, "head")
    await asyncio.to_thread(command.downgrade, cfg, "0006")
    try:
        async with engine.begin() as conn:
            user_id = (
                await conn.execute(
                    text("INSERT INTO users (email) VALUES (:e) RETURNING id"), {"e": email}
                )
            ).scalar_one()
            await conn.execute(
                text(
                    "INSERT INTO accounts (user_id, cash, starting_cash) VALUES (:u, 1.005, 10000)"
                ),
                {"u": user_id},
            )
        with pytest.raises(RuntimeError, match="sub-cent cash"):
            await asyncio.to_thread(command.upgrade, cfg, "0007")
        assert await _versions(engine) == ["0006"]
        async with engine.begin() as conn:
            await conn.execute(text("DELETE FROM accounts WHERE user_id = :u"), {"u": user_id})
            await conn.execute(text("DELETE FROM users WHERE id = :u"), {"u": user_id})
        await asyncio.to_thread(command.upgrade, cfg, "0007")
        assert await _versions(engine) == ["0007"]
    finally:
        async with engine.begin() as conn:
            await conn.execute(text("DELETE FROM accounts WHERE cash != round(cash, 2)"))
        await asyncio.to_thread(command.upgrade, cfg, "head")


async def test_models_match_schema(engine: AsyncEngine) -> None:
    await asyncio.to_thread(command.upgrade, _config(), "head")

    def _diff(sync_conn):  # type: ignore[no-untyped-def]
        ctx = MigrationContext.configure(sync_conn, opts={"compare_type": True})
        return compare_metadata(ctx, Base.metadata)

    async with engine.connect() as conn:
        diff = await conn.run_sync(_diff)
    assert diff == []
