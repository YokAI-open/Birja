"""Staged 0025–0026 PostgreSQL checks without starting the runtime."""

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.db.portfolio_bootstrap import CATALOGUE_0025_SQL, CURRENT_PORTFOLIO_REVISION
from app.models.price import Coin
from app.models.stock_catalog import StockCatalogAdmission
from tests.portfolio_fixtures import (
    economic_snapshot,
    reset_disposable_schema,
    seed_owned_crypto_trade,
    seed_portfolio_world,
)
from tests.test_migrations import (
    install_current_test_grants,
    run_test_migration,
    test_migration_url,
)

FINANCE_TABLES = (
    "stock_catalog_instruments",
    "stock_catalog_financial_quotes",
    "stock_catalog_status",
    "stock_catalog_action_coverage",
    "stock_catalog_fill_evidence",
)


@pytest_asyncio.fixture
async def finance_0025(engine: AsyncEngine) -> AsyncIterator[AsyncEngine]:
    await reset_disposable_schema(engine)
    migrator = create_async_engine(test_migration_url())
    try:
        await asyncio.to_thread(run_test_migration, "0025")
        yield migrator
    finally:
        await migrator.dispose()
        await reset_disposable_schema(engine)
        await asyncio.to_thread(run_test_migration, CURRENT_PORTFOLIO_REVISION)
        await install_current_test_grants()


async def test_upgrade_preserves_books_and_empty_downgrade_restores_0025(
    finance_0025: AsyncEngine,
) -> None:
    async with finance_0025.begin() as conn:
        world = await seed_portfolio_world(conn)
        await seed_owned_crypto_trade(conn, world, world.first)
        before = await economic_snapshot(conn)
        assert before["holdings"]
        assert before["trades"]
        schema_before = await conn.scalar(text(CATALOGUE_0025_SQL))

    await asyncio.to_thread(run_test_migration, "0026")
    async with finance_0025.connect() as conn:
        assert await conn.scalar(text("SELECT version_num FROM alembic_version")) == "0026"
        assert await economic_snapshot(conn) == before
        for table in FINANCE_TABLES:
            assert await conn.scalar(text("SELECT to_regclass(:table)"), {"table": table})

    await asyncio.to_thread(run_test_migration, "0025", down=True)
    async with finance_0025.connect() as conn:
        assert await conn.scalar(text("SELECT version_num FROM alembic_version")) == "0025"
        assert await conn.scalar(text(CATALOGUE_0025_SQL)) == schema_before
        assert await economic_snapshot(conn) == before


@pytest.mark.parametrize("retained", ["stock", "grant"])
async def test_downgrade_refuses_retained_namespace_or_scope(
    finance_0025: AsyncEngine, retained: str
) -> None:
    await asyncio.to_thread(run_test_migration, "0026")
    factory = async_sessionmaker(finance_0025)
    if retained == "stock":
        async with factory.begin() as db:
            for symbol in ("@01", "@9223372036854775808"):
                with pytest.raises(IntegrityError), db.no_autoflush:
                    async with db.begin_nested():
                        db.add(
                            Coin(
                                symbol=symbol,
                                name="Synthetic issue",
                                asset_class="stock",
                                sort_order=0,
                            )
                        )
                        await db.flush()
            db.add(
                Coin(
                    symbol="@9223372036854775807",
                    name="Synthetic issue",
                    asset_class="stock",
                    sort_order=0,
                )
            )
    else:
        now = datetime(2026, 11, 24, 15, tzinfo=UTC)
        async with factory.begin() as db:
            db.add(
                StockCatalogAdmission(
                    artifact="catalog_execution",
                    reference="Disposable reviewed scope",
                    reviewed_at=now,
                    valid_until=now + timedelta(hours=1),
                    scope={"account": "birja"},
                    fields={"bid": ["storage"]},
                    is_fixture=True,
                )
            )

    with pytest.raises(RuntimeError, match="Catalog finance downgrade refused"):
        await asyncio.to_thread(run_test_migration, "0025", down=True)

    async with factory() as db:
        assert await db.scalar(text("SELECT version_num FROM alembic_version")) == "0026"
        if retained == "stock":
            assert await db.scalar(select(Coin.id).where(Coin.symbol == "@9223372036854775807"))
        else:
            assert await db.scalar(
                select(StockCatalogAdmission.id).where(
                    StockCatalogAdmission.artifact == "catalog_execution"
                )
            )
