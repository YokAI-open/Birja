"""Bind a reviewed catalog issue to the financial ledger without creating ownership."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.corporate_action import StockActionState
from app.models.price import Coin
from app.models.stock import StockInstrument
from app.models.stock_catalog import (
    StockCatalogAdmission,
    StockCatalogGeneration,
    StockCatalogListing,
)
from app.models.stock_catalog_finance import StockCatalogInstrument
from app.services.stock_catalog_publish import CatalogPublishError, _lock_catalog
from app.services.stock_catalog_quotes import _live_source_expiry, load_catalog_asset_mapping
from app.services.stock_catalog_search import _permitted_listing
from app.services.stock_quote_rules import utc

_EXECUTION_FIELDS = {
    field: ["collection", "execution", "storage", "backup"]
    for field in ("bid", "ask", "event_at", "collected_at")
}
_MARK_FIELDS = {
    field: ["collection", "display", "derivation", "storage", "backup"]
    for field in _EXECUTION_FIELDS
}
CATALOG_ACTION_FIELDS = {
    field: ["collection", "derivation", "storage", "backup"]
    for field in ("provider_event_id", "symbol", "event_type", "process_date", "terms")
}
_FinancialScope = Literal["catalog_execution", "catalog_mark", "catalog_actions"]
_REQUIRED_FIELDS = {
    "catalog_execution": _EXECUTION_FIELDS,
    "catalog_mark": _MARK_FIELDS,
    "catalog_actions": CATALOG_ACTION_FIELDS,
}


@dataclass(frozen=True, slots=True)
class CatalogFinancialBinding:
    catalog_id: int
    coin_id: int
    listing_id: int
    admission_id: int
    account: str
    server: str
    provider_asset_id: str
    provider_admission_id: int
    provider_symbol: str
    listing_exchange: str
    valid_until: datetime
    identity_valid_until: datetime | None = None


@dataclass(frozen=True, slots=True)
class _PromotionScope:
    listing: StockCatalogListing
    account: str
    server: str
    provider_asset_id: str
    provider_admission_id: int
    provider_symbol: str
    valid_until: datetime
    identity_valid_until: datetime

    def binding(self, coin_id: int, admission_id: int) -> CatalogFinancialBinding:
        return CatalogFinancialBinding(
            self.listing.security_id,
            coin_id,
            self.listing.id,
            admission_id,
            self.account,
            self.server,
            self.provider_asset_id,
            self.provider_admission_id,
            self.provider_symbol,
            self.listing.listing_exchange,
            self.valid_until,
            self.identity_valid_until,
        )


def _catalog_id(value: int) -> bool:
    return type(value) is int and 0 < value < 2**63


async def _current_promotion_scope(
    db: AsyncSession,
    catalog_id: int,
    listing_id: int,
    admission_id: int,
    now: datetime,
    allow_fixture: bool,
    *,
    artifact: _FinancialScope = "catalog_execution",
) -> _PromotionScope | None:
    listing = StockCatalogListing
    generation = StockCatalogGeneration
    row = (
        await db.execute(
            select(listing, generation.mode, generation.valid_until)
            .join(generation, generation.id == listing.generation_id)
            .where(
                listing.id == listing_id,
                listing.security_id == catalog_id,
                listing.state == "active",
                listing.valid_until > now,
                listing.classification.in_(("common_stock", "ordinary_shares")),
                listing.currency == "USD",
                listing.units_per_share == 1,
                generation.is_active,
                generation.mode.in_(("live", "fixture") if allow_fixture else ("live",)),
                generation.published_at <= now,
                generation.valid_until > now,
                _permitted_listing(now, generation.mode == "fixture"),
            )
            .execution_options(populate_existing=True)
        )
    ).one_or_none()
    if row is None:
        return None
    current, mode, source_until = row
    asset_id = current.provider_asset_id
    provider_admission_id = current.provider_admission_id
    symbol = current.provider_symbol
    if asset_id is None or provider_admission_id is None or symbol is None:
        return None

    if mode == "live":
        live_source_until = await _live_source_expiry(db, current, now)
        if live_source_until is None:
            return None
        source_until = min(source_until, live_source_until)

    grant = StockCatalogAdmission
    authority = (
        await db.execute(
            select(grant.scope, grant.valid_until).where(
                grant.id == admission_id,
                grant.artifact == artifact,
                grant.is_fixture == (mode == "fixture"),
                grant.reviewed_at <= now,
                grant.valid_until > now,
                grant.revoked_at.is_(None),
                grant.fields.contains(_REQUIRED_FIELDS[artifact]),
                grant.scope.contains(
                    {
                        "catalog_id": str(catalog_id),
                        "listing_id": str(listing_id),
                        "provider_asset_id": asset_id,
                        "feed": "alpaca-corporate-actions"
                        if artifact == "catalog_actions"
                        else "iex",
                    }
                ),
            )
        )
    ).one_or_none()
    if authority is None:
        return None
    scope, grant_until = authority
    account, server = scope.get("account"), scope.get("server")
    if not all(
        isinstance(value, str) and 0 < len(value) <= 128 and value == value.strip()
        for value in (account, server)
    ):
        return None
    mapping = await load_catalog_asset_mapping(db, current, now, account=account, server=server)
    if mapping is None:
        return None
    _, mapping_until = mapping
    identity_until = min(source_until, mapping_until)
    return _PromotionScope(
        current,
        account,
        server,
        asset_id,
        provider_admission_id,
        symbol,
        min(identity_until, grant_until),
        identity_until,
    )


async def load_catalog_financial_binding(
    db: AsyncSession,
    catalog_id: int,
    listing_id: int,
    now: datetime,
    *,
    allow_fixture: bool = False,
) -> CatalogFinancialBinding | None:
    """Check every current identity and grant before admitting financial use."""
    return await _load_catalog_binding(db, catalog_id, listing_id, now, allow_fixture)


async def load_catalog_mark_binding(
    db: AsyncSession,
    catalog_id: int,
    listing_id: int,
    admission_id: int,
    now: datetime,
    *,
    allow_fixture: bool = False,
) -> CatalogFinancialBinding | None:
    """Recheck the same promoted identity under its original mark permission."""
    if not _catalog_id(admission_id):
        return None
    return await _load_catalog_binding(
        db,
        catalog_id,
        listing_id,
        now,
        allow_fixture,
        admission_id=admission_id,
        artifact="catalog_mark",
    )


async def load_catalog_action_binding(
    db: AsyncSession,
    catalog_id: int,
    listing_id: int,
    admission_id: int,
    now: datetime,
    *,
    allow_fixture: bool = False,
) -> CatalogFinancialBinding | None:
    """Resolve the promoted issue under accounting rights even after execution expires."""
    if not _catalog_id(admission_id):
        return None
    return await _load_catalog_binding(
        db,
        catalog_id,
        listing_id,
        now,
        allow_fixture,
        admission_id=admission_id,
        artifact="catalog_actions",
    )


async def _load_catalog_binding(
    db: AsyncSession,
    catalog_id: int,
    listing_id: int,
    now: datetime,
    allow_fixture: bool,
    *,
    admission_id: int | None = None,
    artifact: _FinancialScope = "catalog_execution",
) -> CatalogFinancialBinding | None:
    if not (_catalog_id(catalog_id) and _catalog_id(listing_id) and utc(now)):
        return None
    instrument = StockCatalogInstrument
    binding = await db.scalar(
        select(instrument)
        .where(instrument.catalog_id == catalog_id, instrument.listing_id == listing_id)
        .execution_options(populate_existing=True)
    )
    if binding is None or binding.promoted_at > now:
        return None
    selected_admission = admission_id if admission_id is not None else binding.admission_id
    scope = await _current_promotion_scope(
        db,
        catalog_id,
        listing_id,
        selected_admission,
        now,
        allow_fixture,
        artifact=artifact,
    )
    if scope is None:
        return None
    matches = await db.scalar(
        select(StockInstrument.coin_id)
        .join(Coin, Coin.id == StockInstrument.coin_id)
        .where(
            StockInstrument.coin_id == binding.coin_id,
            StockInstrument.provider_asset_id == scope.provider_asset_id,
            StockInstrument.provider_verified_at == scope.listing.provider_verified_at,
            StockInstrument.listing_exchange == scope.listing.listing_exchange,
            Coin.asset_class == "stock",
            Coin.symbol == f"@{catalog_id}",
        )
    )
    return scope.binding(binding.coin_id, selected_admission) if matches is not None else None


async def promote_catalog_instrument(
    db: AsyncSession,
    catalog_id: int,
    listing_id: int,
    admission_id: int,
    now: datetime,
    *,
    allow_fixture: bool = False,
    account: str | None = None,
    server: str | None = None,
) -> CatalogFinancialBinding:
    """Promote an exact issue in a caller-owned authenticated migrator transaction."""
    if not (
        all(_catalog_id(value) for value in (catalog_id, listing_id, admission_id)) and utc(now)
    ):
        raise CatalogPublishError("Promotion requires canonical IDs and a UTC clock")
    await _lock_catalog(db)
    if not await db.scalar(
        text("SELECT session_user = 'birja_migrator' AND current_user = session_user")
    ):
        raise CatalogPublishError("Promotion requires authenticated birja_migrator")
    scope = await _current_promotion_scope(
        db, catalog_id, listing_id, admission_id, now, allow_fixture
    )
    if (
        scope is None
        or (account is not None and account != scope.account)
        or (server is not None and server != scope.server)
    ):
        raise CatalogPublishError("No current reviewed financial scope matches this listing")

    binding = await db.get(StockCatalogInstrument, catalog_id, populate_existing=True)
    provider_owner = await db.scalar(
        select(StockInstrument.coin_id).where(
            StockInstrument.provider_asset_id == scope.provider_asset_id
        )
    )
    if provider_owner is not None and (binding is None or provider_owner != binding.coin_id):
        raise CatalogPublishError("Provider asset already has a financial identity")
    symbol = f"@{catalog_id}"
    if binding is not None:
        coin = await db.get(Coin, binding.coin_id)
        instrument = await db.get(StockInstrument, binding.coin_id)
        if (
            coin is None
            or instrument is None
            or coin.asset_class != "stock"
            or coin.symbol != symbol
        ):
            raise CatalogPublishError(
                "Existing financial identity does not match the catalog issue"
            )
        if now < binding.promoted_at:
            raise CatalogPublishError("Catalog financial promotion clock regressed")
        binding.listing_id = listing_id
        binding.admission_id = admission_id
        instrument.provider_asset_id = scope.provider_asset_id
        instrument.provider_verified_at = scope.listing.provider_verified_at
        instrument.listing_exchange = scope.listing.listing_exchange
        return scope.binding(binding.coin_id, admission_id)

    if await db.scalar(select(Coin.id).where(Coin.asset_class == "stock", Coin.symbol == symbol)):
        raise CatalogPublishError("Reserved stock symbol already has a financial identity")
    # Existing curated lookups still filter on legacy active coins. Catalog use
    # enters through the exact issue/version binding and its own authority.
    coin = Coin(
        symbol=symbol, name="Catalog stock", asset_class="stock", sort_order=0, is_active=False
    )
    db.add(coin)
    await db.flush()
    db.add(
        StockInstrument(
            coin_id=coin.id,
            provider_asset_id=scope.provider_asset_id,
            provider_verified_at=scope.listing.provider_verified_at,
            listing_exchange=scope.listing.listing_exchange,
            source="stock-catalog",
            source_ref=f"catalog:{catalog_id}",
        )
    )
    await db.flush()
    db.add_all(
        [
            StockCatalogInstrument(
                catalog_id=catalog_id,
                coin_id=coin.id,
                listing_id=listing_id,
                admission_id=admission_id,
                promoted_at=now,
            ),
            StockActionState(coin_id=coin.id, admission_generation=admission_id),
        ]
    )
    await db.flush()
    return scope.binding(coin.id, admission_id)
