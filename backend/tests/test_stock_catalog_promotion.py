"""Promotion and retirement checks using the enrolled disposable migrator."""

import asyncio
from datetime import datetime, timedelta
from typing import get_args

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.models.corporate_action import StockActionState
from app.models.price import Coin
from app.models.stock import StockInstrument
from app.models.stock_catalog import StockCatalogAdmission, StockCatalogListing
from app.models.stock_catalog_finance import StockCatalogInstrument
from app.services.stock_catalog_promotion import (
    CatalogFinancialBinding,
    load_catalog_financial_binding,
    promote_catalog_instrument,
)
from app.services.stock_catalog_provider import (
    CatalogAssetAdmission,
    CatalogAssetTarget,
    CatalogUnitEvidence,
    stage_catalog_assets,
)
from app.services.stock_catalog_publish import CatalogPublishError, promote_catalog_mappings
from app.services.stock_catalog_sources import ListingExchange
from app.tasks.stock_catalog_inventory import Purpose
from tests.portfolio_fixtures import (
    economic_snapshot,
    seed_owned_crypto_trade,
    seed_portfolio_world,
)
from tests.test_migrations import run_test_migration
from tests.test_stock_catalog_finance_migration import finance_0025 as finance_0025
from tests.test_stock_catalog_publish import (
    NOW,
    SECOND,
    Factory,
    _listings,
    _manifest,
    _publish,
    _sha,
)

ACCOUNT = SERVER = "birja"
FIRST_ASSET = "31000000-1234-4567-b89a-000000000001"
OTHER_ASSET = "31000000-1234-4567-b89a-000000000002"


@pytest_asyncio.fixture
async def finance_0026(finance_0025: AsyncEngine) -> Factory:
    await asyncio.to_thread(run_test_migration, "0026")
    return async_sessionmaker(finance_0025, expire_on_commit=False)


async def _listing(factory: Factory, generation_id: int, ticker: str) -> StockCatalogListing:
    async with factory() as db:
        return next(
            row
            for row in await _listings(db, generation_id)
            if row.ticker == ticker and row.state == "active"
        )


async def _reviewed_grant(
    factory: Factory,
    listing: StockCatalogListing,
    asset_id: str,
    now: datetime,
    *,
    asset_valid_until: datetime | None = None,
) -> int:
    exchange: ListingExchange = "NASDAQ" if listing.listing_exchange == "NASDAQ" else "NYSE"
    target = CatalogAssetTarget(
        catalog_id=listing.security_id,
        listing_version=listing.id,
        listing_exchange=exchange,
        provider_symbol=listing.ticker,
    )
    units = CatalogUnitEvidence(
        target=target,
        currency="USD",
        units_per_share=1,
        classification="common_stock",
        reviewed_at=now - timedelta(hours=2),
        valid_until=asset_valid_until or now + timedelta(hours=4),
        evidence_digest=_sha(f"synthetic units {listing.id}"),
    )
    provider = CatalogAssetAdmission(
        account=ACCOUNT,
        server=SERVER,
        environment="paper",
        reviewed_at=now - timedelta(hours=1),
        valid_until=units.valid_until,
        evidence_digest=_sha(f"synthetic asset review {listing.id}"),
        targets=(target,),
        purposes=frozenset(get_args(Purpose)),
        request_limit=1,
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "id": asset_id,
                "symbol": listing.ticker,
                "class": "us_equity",
                "status": "active",
                "exchange": exchange,
            },
        )
    )
    async with httpx.AsyncClient(transport=transport) as client:
        proofs = await stage_catalog_assets(
            client,
            (units,),
            provider,
            account=ACCOUNT,
            server=SERVER,
            expected_listings={listing.security_id: target},
            clock=lambda: now,
        )

    async with factory.begin() as db:
        reference = StockCatalogAdmission(
            artifact="alpaca_assets",
            reference="Synthetic exact provider and USD share-unit review",
            reviewed_at=provider.reviewed_at,
            valid_until=provider.valid_until,
            fields={
                field: sorted(provider.purposes)
                for field in (
                    "provider_asset_id",
                    "provider_symbol",
                    "asset_evidence",
                    "currency",
                    "units_per_share",
                    "unit_evidence",
                )
            },
            scope={
                "provider": provider.model_dump(mode="json"),
                "units": [units.model_dump(mode="json")],
            },
        )
        db.add(reference)
        await db.flush()
        assert (
            await promote_catalog_mappings(db, reference.id, proofs, now=now, allow_fixture=True)
            == 1
        )
        execution = StockCatalogAdmission(
            artifact="catalog_execution",
            reference="Synthetic execution, storage and recovery review",
            reviewed_at=provider.reviewed_at,
            valid_until=now + timedelta(minutes=30),
            fields={
                field: ["collection", "execution", "storage", "backup"]
                for field in ("bid", "ask", "event_at", "collected_at")
            },
            scope={
                "account": ACCOUNT,
                "server": SERVER,
                "catalog_id": str(listing.security_id),
                "listing_id": str(listing.id),
                "provider_asset_id": asset_id,
                "feed": "iex",
            },
            is_fixture=True,
        )
        db.add(execution)
        await db.flush()
        return execution.id


async def _promote(
    factory: Factory,
    listing: StockCatalogListing,
    grant_id: int,
    now: datetime,
    *,
    allow_fixture: bool = True,
) -> CatalogFinancialBinding:
    async with factory.begin() as db:
        return await promote_catalog_instrument(
            db,
            listing.security_id,
            listing.id,
            grant_id,
            now,
            allow_fixture=allow_fixture,
            account=ACCOUNT,
            server=SERVER,
        )


async def test_replay_and_verified_rename_keep_coin_and_book(finance_0026: Factory) -> None:
    async with finance_0026.begin() as db:
        conn = await db.connection()
        world = await seed_portfolio_world(conn)
        await seed_owned_crypto_trade(conn, world, world.first)
        before = await economic_snapshot(conn)
        crypto = Coin(symbol="FQA", name="Synthetic crypto", kraken_pair="FQAUSD", sort_order=0)
        db.add(crypto)
        await db.flush()
        crypto_id = crypto.id
    initial = await _publish(finance_0026, _manifest(), None)
    first = await _listing(finance_0026, initial.generation_id, "FQA")
    grant = await _reviewed_grant(finance_0026, first, FIRST_ASSET, NOW)

    with pytest.raises(CatalogPublishError):
        await _promote(finance_0026, first, grant, NOW, allow_fixture=False)
    with pytest.raises(CatalogPublishError):
        await _promote(finance_0026, first, grant, NOW + timedelta(minutes=30))
    async with finance_0026() as db:
        assert await db.scalar(select(StockCatalogInstrument.catalog_id)) is None

    promoted = await _promote(finance_0026, first, grant, NOW)
    replay = await _promote(finance_0026, first, grant, NOW)
    assert replay == promoted
    assert (promoted.catalog_id, promoted.listing_id) == (first.security_id, first.id)
    assert promoted.coin_id != crypto_id

    changes = _manifest(SECOND, nasdaq=(("FQR", "fixture-nasdaq"),))
    next_generation = await _publish(finance_0026, changes, initial.generation_id, now=SECOND)
    renamed = await _listing(finance_0026, next_generation.generation_id, "FQR")
    assert renamed.security_id == first.security_id
    assert renamed.id != first.id
    renamed_grant = await _reviewed_grant(finance_0026, renamed, FIRST_ASSET, SECOND)
    with pytest.raises(CatalogPublishError):
        await _promote(finance_0026, first, renamed_grant, SECOND)
    updated = await _promote(finance_0026, renamed, renamed_grant, SECOND)
    assert updated.coin_id == promoted.coin_id
    assert updated.listing_id == renamed.id

    with pytest.raises(RuntimeError, match="Catalog finance downgrade refused"):
        await asyncio.to_thread(run_test_migration, "0025", down=True)
    async with finance_0026() as db:
        assert await db.scalar(text("SELECT version_num FROM alembic_version")) == "0026"
        assert (
            await load_catalog_financial_binding(
                db, renamed.security_id, renamed.id, SECOND, allow_fixture=True
            )
            == updated
        )
        assert (
            await load_catalog_financial_binding(
                db, first.security_id, first.id, SECOND, allow_fixture=True
            )
            is None
        )
        stock = await db.get(Coin, promoted.coin_id)
        assert stock is not None
        assert (stock.asset_class, stock.symbol) == ("stock", f"@{first.security_id}")
        crypto = await db.get(Coin, crypto_id)
        assert crypto is not None
        assert (crypto.asset_class, crypto.symbol) == ("crypto", "FQA")
        action = await db.get(StockActionState, promoted.coin_id)
        assert action is not None
        assert action.health == "unknown"
        assert await economic_snapshot(await db.connection()) == before


async def test_ticker_reuse_needs_independent_identity_and_provider_asset(
    finance_0026: Factory,
) -> None:
    initial = await _publish(finance_0026, _manifest(), None)
    first = await _listing(finance_0026, initial.generation_id, "FQA")
    grant = await _reviewed_grant(finance_0026, first, FIRST_ASSET, NOW)
    promoted = await _promote(finance_0026, first, grant, NOW)

    changes = _manifest(SECOND, nasdaq=(("FQA", "replacement-issue"),))
    next_generation = await _publish(finance_0026, changes, initial.generation_id, now=SECOND)
    replacement = await _listing(finance_0026, next_generation.generation_id, "FQA")
    assert replacement.security_id != first.security_id
    with pytest.raises(CatalogPublishError):
        await _reviewed_grant(finance_0026, replacement, FIRST_ASSET, SECOND)
    replacement_grant = await _reviewed_grant(finance_0026, replacement, OTHER_ASSET, SECOND)

    async with finance_0026.begin() as db:
        curated_id = await db.scalar(select(Coin.id).where(Coin.symbol == "AAPL"))
        assert curated_id is not None
        curated = await db.get(StockInstrument, curated_id)
        assert curated is not None
        curated.provider_asset_id = OTHER_ASSET
    with pytest.raises(CatalogPublishError):
        await _promote(finance_0026, replacement, grant, SECOND)
    with pytest.raises(CatalogPublishError):
        await _promote(finance_0026, replacement, replacement_grant, SECOND)
    async with finance_0026.begin() as db:
        assert await db.get(StockCatalogInstrument, replacement.security_id) is None
        curated = await db.get(StockInstrument, curated_id)
        assert curated is not None
        assert curated.provider_asset_id == OTHER_ASSET
        curated.provider_asset_id = None

    new_binding = await _promote(finance_0026, replacement, replacement_grant, SECOND)
    assert new_binding.coin_id != promoted.coin_id
    async with finance_0026() as db:
        original = await db.get(StockCatalogInstrument, first.security_id)
        assert original is not None
        assert (original.coin_id, original.listing_id) == (promoted.coin_id, first.id)
        assert (
            await load_catalog_financial_binding(
                db, first.security_id, first.id, SECOND, allow_fixture=True
            )
            is None
        )
        assert (
            await load_catalog_financial_binding(
                db, replacement.security_id, replacement.id, SECOND, allow_fixture=True
            )
            == new_binding
        )
