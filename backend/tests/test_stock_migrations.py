"""Real isolated PostgreSQL upgrade, invariant and downgrade proofs."""

import asyncio
import io
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.test_migrations import _config, _versions

STOCK_TABLES = {"stock_instruments", "stock_quotes", "stock_sessions", "stock_data_admissions"}


async def migrate(target: str, *, down: bool = False) -> None:
    await asyncio.to_thread(command.downgrade if down else command.upgrade, _config(), target)


async def test_head_has_separate_stock_storage(engine: AsyncEngine, migrated: None) -> None:
    async with engine.connect() as conn:
        columns = set(
            (
                await conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns WHERE table_name='coins'"
                    )
                )
            ).scalars()
        )
        assert "asset_class" in columns, "Existing identity storage needs an asset discriminator"
        tables = set(
            (
                await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
                )
            ).scalars()
        )
        assert tables >= STOCK_TABLES


async def _financial_snapshot(engine: AsyncEngine) -> list[list[tuple]]:
    async with engine.connect() as conn:
        result = []
        for table in ("users", "accounts", "holdings", "trades", "auth_sessions", "refresh_tokens"):
            result.append(
                [
                    tuple(row)
                    for row in (
                        await conn.execute(text(f"SELECT * FROM {table} ORDER BY id"))  # noqa: S608 - fixed table allowlist
                    ).all()
                ]
            )
        result.append(
            [
                tuple(row)
                for row in (
                    await conn.execute(
                        text(
                            "SELECT id,symbol,name,kraken_pair,sort_order,is_active FROM coins "
                            "WHERE kraken_pair IS NOT NULL ORDER BY id"
                        )
                    )
                ).all()
            ]
        )
        return result


async def test_populated_0008_preserves_exact_financial_identity(engine: AsyncEngine) -> None:
    await migrate("head")
    await migrate("0008", down=True)
    try:
        async with engine.begin() as conn:
            uid = (
                await conn.execute(
                    text(
                        "INSERT INTO users(email) VALUES ('stock-migration@example.test') RETURNING id"
                    )
                )
            ).scalar_one()
            cid = (await conn.execute(text("SELECT id FROM coins WHERE symbol='BTC'"))).scalar_one()
            await conn.execute(
                text("INSERT INTO accounts(user_id,cash,starting_cash) VALUES (:u,9876.54,10000)"),
                {"u": uid},
            )
            await conn.execute(
                text(
                    "INSERT INTO holdings(user_id,coin_id,quantity,cost_basis) "
                    "VALUES (:u,:c,0.00123456,123.46)"
                ),
                {"u": uid, "c": cid},
            )
            await conn.execute(
                text("""INSERT INTO trades
                (user_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
                 exec_price,fee,cash_delta,cash_after,idempotency_key)
                VALUES (:u,:c,'buy','quantity',0.00123456,0.00123456,99900,now(),100000,
                        0,-123.46,9876.54,'11111111-1111-4111-8111-111111111111')"""),
                {"u": uid, "c": cid},
            )
        before = await _financial_snapshot(engine)
        await migrate("0009")
        assert await _versions(engine) == ["0009"]
        assert await _financial_snapshot(engine) == before
        # No production roles are provisioned by the migration in development.
        async with engine.connect() as conn:
            assert not (
                await conn.execute(
                    text(
                        "SELECT rolname FROM pg_roles WHERE rolname IN "
                        "('birja_app','birja_scheduler','birja_migrator')"
                    )
                )
            ).all()
        await migrate("0008", down=True)
        assert await _financial_snapshot(engine) == before
    finally:
        async with engine.begin() as conn:
            for table in ("trades", "holdings", "accounts"):
                await conn.execute(text(f"DELETE FROM {table} WHERE user_id=:u"), {"u": uid})  # noqa: S608 - fixed table allowlist
            await conn.execute(text("DELETE FROM users WHERE id=:u"), {"u": uid})
        await migrate("head")


@pytest.mark.parametrize(
    "asset,pair",
    [
        ("crypto", None),  # crypto requires Kraken mapping
        ("stock", "BADUSD"),  # stock must not acquire a Kraken mapping
        ("bond", None),
    ],
)
async def test_invalid_asset_discriminator_refused(
    engine: AsyncEngine, migrated: None, asset: str, pair: str | None
) -> None:
    async with engine.begin() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(
                text(
                    "INSERT INTO coins(symbol,name,kraken_pair,sort_order,asset_class) "
                    "VALUES ('BAD','Bad',:pair,99,:asset)"
                ),
                {"pair": pair, "asset": asset},
            )


async def test_same_symbol_distinct_classes_and_unique_crypto_mapping(
    engine: AsyncEngine, migrated: None
) -> None:
    async with engine.connect() as conn:
        async with conn.begin():
            await conn.execute(
                text(
                    "INSERT INTO coins(symbol,name,kraken_pair,sort_order,asset_class) "
                    "VALUES ('BTC','Stock BTC',NULL,99,'stock')"
                )
            )
            with pytest.raises(IntegrityError):
                await conn.execute(
                    text(
                        "INSERT INTO coins(symbol,name,kraken_pair,sort_order) "
                        "VALUES ('OTHER','Other','XXBTZUSD',99)"
                    )
                )


@pytest.mark.parametrize(
    "bid,ask,mid",
    [
        ("0", "2", "1"),
        ("2", "1", "1.5"),
        ("NaN", "NaN", "NaN"),
        ("Infinity", "Infinity", "Infinity"),
        ("1", "3", "1"),
    ],
)
async def test_invalid_quote_refused(
    engine: AsyncEngine, migrated: None, bid: str, ask: str, mid: str
) -> None:
    async with engine.begin() as conn:
        cid = (
            await conn.execute(
                text(
                    "INSERT INTO coins(symbol,name,asset_class,sort_order) "
                    "VALUES ('TST','Test','stock',99) RETURNING id"
                )
            )
        ).scalar_one()
        with pytest.raises(IntegrityError):
            await conn.execute(
                text("""INSERT INTO stock_quotes
                (coin_id,bid,ask,mid,source,feed,event_at,collected_at,session_date,admission_generation)
                VALUES (:c,:b,:a,:m,'alpaca','iex',now(),now(),current_date,1)"""),
                {"c": cid, "b": Decimal(bid), "a": Decimal(ask), "m": Decimal(mid)},
            )


@pytest.mark.parametrize(
    "opening,closing",
    [
        (0, None),
        (None, 0),
        (0, 0),
        (0, -1),
    ],
)
async def test_impossible_sessions_refused(
    engine: AsyncEngine, migrated: None, opening: int | None, closing: int | None
) -> None:
    async with engine.begin() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(
                text("""INSERT INTO stock_sessions
                (exchange,session_date,opens_at,closes_at,coverage_start,coverage_end,
                 calendar_admission_generation)
                VALUES ('NYSE',current_date,:opening,:closing,current_date,current_date,1)"""),
                {
                    "opening": None
                    if opening is None
                    else datetime.now(UTC) + timedelta(hours=opening),
                    "closing": None
                    if closing is None
                    else datetime.now(UTC).replace(microsecond=0) + timedelta(hours=closing),
                },
            )


async def test_sessions_have_no_authority_columns(engine: AsyncEngine, migrated: None) -> None:
    async with engine.connect() as conn:
        columns = set(
            (
                await conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name='stock_sessions'"
                    )
                )
            ).scalars()
        )
        assert columns == {
            "id",
            "exchange",
            "session_date",
            "opens_at",
            "closes_at",
            "coverage_start",
            "coverage_end",
            "calendar_admission_generation",
        }


def test_migration_owns_conditional_least_privilege_grants() -> None:
    output = io.StringIO()
    cfg = _config()
    cfg.output_buffer = output
    command.upgrade(cfg, "0008:0009", sql=True)
    sql = output.getvalue()
    assert "pg_roles" in sql
    assert "REVOKE ALL" in sql and "FROM PUBLIC" in sql
    assert "GRANT SELECT ON TABLE" in sql
    assert "GRANT SELECT, INSERT, UPDATE ON TABLE" in sql
    assert "GRANT USAGE ON SEQUENCE public.stock_sessions_id_seq TO birja_scheduler" in sql
    assert "ALTER DEFAULT PRIVILEGES" not in sql and "CREATE ROLE" not in sql
