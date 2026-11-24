"""Read the admitted catalog without consulting pricing or session caches."""

from datetime import UTC, datetime

from sqlalchemy import and_, case, exists, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import Exists

from app.core.config import Settings
from app.models.stock_catalog import (
    StockCatalogAdmission,
    StockCatalogAlias,
    StockCatalogGeneration,
    StockCatalogListing,
)
from app.schemas.stock_catalog import StockCatalogItem, StockCatalogSearch

_SEARCH_LIMIT = 20


def _admitted(
    admission_id: ColumnElement[int | None],
    artifact: ColumnElement[bool],
    fields: dict[str, list[str]],
    now: datetime,
) -> Exists:
    admission = StockCatalogAdmission
    return (
        select(admission.id)
        .where(
            admission.id == admission_id,
            artifact,
            ~admission.is_fixture,
            admission.reviewed_at <= now,
            admission.valid_until > now,
            admission.revoked_at.is_(None),
            admission.fields.contains(fields),
        )
        .exists()
    )


def _permitted_listing(now: datetime, fixture: ColumnElement[bool]) -> ColumnElement[bool]:
    listing = StockCatalogListing
    admission = StockCatalogAdmission
    return or_(
        fixture,
        and_(
            _admitted(
                listing.directory_admission_id.expression,
                admission.artifact == listing.source,
                {
                    "ticker": ["display"],
                    "listing_exchange": ["display"],
                    "share_class": ["display"],
                    "eligibility": ["derived_use"],
                },
                now,
            ),
            _admitted(
                listing.name_admission_id.expression,
                admission.artifact == listing.source,
                {"company_name": ["display"]},
                now,
            ),
            _admitted(
                listing.classification_admission_id.expression,
                admission.artifact.in_(("openfigi", "issuer_exception")),
                {"classification": ["derived_use"], "identity_key": ["derived_use"]},
                now,
            ),
        ),
    )


def _active_generation(settings: Settings, now: datetime) -> ColumnElement[bool]:
    generation = StockCatalogGeneration
    modes = ("live",) if settings.env == "prod" else ("live", "fixture")
    return and_(
        generation.is_active,
        generation.mode.in_(modes),
        generation.published_at <= now,
        generation.valid_until > now,
    )


def _alias_match(
    listing_id: ColumnElement[int],
    admission_allows_match: ColumnElement[bool],
    now: datetime,
    symbols: ColumnElement[bool],
) -> Exists:
    alias = StockCatalogAlias
    return (
        select(alias.id)
        .where(
            alias.listing_id == listing_id,
            alias.verified_at <= now,
            alias.valid_until > now,
            admission_allows_match,
            symbols,
        )
        .exists()
    )


async def search_catalog(
    db: AsyncSession, settings: Settings, q: str, *, now: datetime | None = None
) -> StockCatalogSearch:
    """Return the current generation and its first twenty exact ranked matches."""
    checked_at = now or datetime.now(UTC)
    ticker = q.strip().upper()
    name = q.strip().casefold()
    generation = StockCatalogGeneration
    listing = StockCatalogListing
    admission = StockCatalogAdmission
    alias = StockCatalogAlias
    active = (
        select(generation.id, generation.published_at, generation.mode)
        .where(_active_generation(settings, checked_at))
        .cte("active_catalog")
    )
    visible = (
        select(
            listing.security_id.label("catalog_id"),
            listing.id.label("listing_version"),
            listing.ticker,
            listing.company_name,
            listing.listing_exchange,
            listing.share_class,
            listing.state,
            listing.reason,
            listing.normalized_ticker,
            listing.normalized_name,
            listing.classification_admission_id,
            listing.directory_admission_id,
            listing.source,
            active.c.mode,
        )
        .join(active, active.c.id == listing.generation_id)
        .where(
            listing.state == "active",
            listing.valid_until > checked_at,
            listing.classification.in_(("common_stock", "ordinary_shares")),
            _permitted_listing(checked_at, active.c.mode == "fixture"),
        )
        .cte("visible_catalog")
    )
    rows = visible.c
    # An alias may only influence search under its source's current derived-use grant.
    provider_alias = _admitted(
        rows.classification_admission_id,
        admission.artifact == "openfigi",
        {"aliases": ["derived_use"]},
        checked_at,
    ).correlate(visible)
    directory_alias = _admitted(
        rows.directory_admission_id,
        admission.artifact == rows.source,
        {"aliases": ["derived_use"]},
        checked_at,
    ).correlate(visible)
    alias_permission = or_(
        rows.mode == "fixture",
        and_(alias.namespace == "openfigi", provider_alias),
        and_(alias.namespace != "openfigi", directory_alias),
    )
    alias_is = _alias_match(
        rows.listing_version,
        alias_permission,
        checked_at,
        alias.normalized_symbol == ticker,
    ).correlate(visible)
    alias_starts = _alias_match(
        rows.listing_version,
        alias_permission,
        checked_at,
        alias.normalized_symbol.startswith(ticker, autoescape=True),
    ).correlate(visible)
    rank = case(
        (rows.normalized_ticker == ticker, 1),
        (alias_is, 2),
        (or_(rows.normalized_ticker.startswith(ticker, autoescape=True), alias_starts), 3),
        (rows.normalized_name.startswith(name, autoescape=True), 4),
        (rows.normalized_name.contains(name, autoescape=True), 5),
        else_=0,
    ).label("rank")
    ranked = (
        select(
            rows.catalog_id,
            rows.listing_version,
            rows.ticker,
            rows.company_name,
            rows.listing_exchange,
            rows.share_class,
            rows.state,
            rows.reason,
            rows.normalized_ticker,
            rank,
        )
        .select_from(visible)
        .where(rank > 0)
        .order_by(rank, rows.normalized_ticker, rows.listing_exchange, rows.catalog_id)
        .limit(_SEARCH_LIMIT + 1)
        .subquery()
    )
    # One statement keeps the generation, current rights and ranked page coherent.
    response_rows = (
        await db.execute(
            select(active.c.id.label("generation_id"), active.c.published_at, ranked)
            .select_from(active.outerjoin(ranked, true()))
            .where(exists().select_from(visible))
            .order_by(
                ranked.c.rank,
                ranked.c.normalized_ticker,
                ranked.c.listing_exchange,
                ranked.c.catalog_id,
            )
        )
    ).all()
    if not response_rows:
        return StockCatalogSearch(state="unavailable")
    generation_id, published_at = response_rows[0][:2]
    return StockCatalogSearch(
        state="ready",
        generation_id=generation_id,
        published_at=published_at,
        has_more=len(response_rows) > _SEARCH_LIMIT,
        items=[
            StockCatalogItem.model_validate(row, from_attributes=True)
            for row in response_rows[:_SEARCH_LIMIT]
            if row.catalog_id is not None
        ],
    )


async def get_catalog_listing(
    db: AsyncSession, settings: Settings, catalog_id: int, *, now: datetime | None = None
) -> StockCatalogListing | None:
    """Resolve a durable identity to its current admitted version, including retirement."""
    checked_at = now or datetime.now(UTC)
    generation = StockCatalogGeneration
    listing = StockCatalogListing
    result = await db.execute(
        select(listing)
        .join(generation, generation.id == listing.generation_id)
        .where(
            _active_generation(settings, checked_at),
            listing.security_id == catalog_id,
            or_(listing.state != "active", listing.valid_until > checked_at),
            _permitted_listing(checked_at, generation.mode == "fixture"),
        )
        .execution_options(populate_existing=True)
    )
    return result.scalar_one_or_none()


def catalog_item(listing: StockCatalogListing) -> StockCatalogItem:
    """Expose only the permitted public listing metadata."""
    return StockCatalogItem.model_validate(listing, from_attributes=True)
