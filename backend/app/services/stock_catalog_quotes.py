"""Authority and ephemeral display prices for one selected catalog identity."""

import asyncio
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, TypeAdapter
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import SchedulerSettings, Settings
from app.models.stock import StockDataAdmission
from app.models.stock_catalog import (
    StockCatalogAdmission,
    StockCatalogAlias,
    StockCatalogGeneration,
    StockCatalogListing,
)
from app.services.stock_admission import ProductAdmission
from app.services.stock_catalog_classification import CatalogModel
from app.services.stock_catalog_provider import (
    CatalogAssetAdmission,
    CatalogAssetMapping,
    CatalogAssetTarget,
    CatalogUnitEvidence,
    mapping_evidence_matches,
)
from app.services.stock_catalog_quote_demand import (
    CatalogQuoteRequest,
    catalog_quote_key,
    complete_catalog_quote,
)
from app.services.stock_catalog_search import get_catalog_listing
from app.services.stock_catalog_sources import ListingExchange
from app.services.stock_quote_rules import RawIexQuote, ValidIexQuote, utc, validate_iex_quote
from app.services.stock_sessions import SessionDecision, load_sessions, session_at

_SCOPE_ARTIFACT = "alpaca_iex_quotes"
_QUOTE_FIELDS = {
    field: ["collection", "display", "cache"] for field in ("symbol", "bid", "ask", "event_at")
}
_MAPPING_FIELDS = {
    "provider_asset_id",
    "provider_symbol",
    "asset_evidence",
    "currency",
    "units_per_share",
    "unit_evidence",
}
_MAPPING_PURPOSES = frozenset(
    {"collection", "internal_use", "derived_use", "display", "storage", "backup"}
)
_UNIT_EVIDENCE = TypeAdapter(tuple[CatalogUnitEvidence, ...])
_CACHE_AGE = timedelta(minutes=10)
_MAX_CACHE_BYTES = 1024

CatalogQuoteReadiness = Literal[
    "ready",
    "missing_permission",
    "mapping_review",
    "identity_review",
    "market_closed",
    "session_unavailable",
    "price_disabled",
]


class CatalogIexQuoteScope(CatalogModel):
    """An independently reviewed IEX display and transient cache grant."""

    account: str = Field(min_length=1, max_length=128)
    server: str = Field(min_length=1, max_length=128)
    feed: Literal["iex"]
    currency: Literal["USD"]
    listing_exchanges: tuple[ListingExchange, ...] = Field(min_length=1, max_length=2)
    requests_per_minute: int = Field(ge=1, le=200)
    max_response_bytes: int = Field(ge=4096, le=1048576)
    symbols_per_request: int = Field(default=1, ge=1, le=8)


@dataclass(frozen=True, slots=True)
class CatalogQuoteBinding:
    catalog_id: int
    listing_version: int
    fingerprint: str
    provider_symbol: str
    listing_exchange: ListingExchange
    valid_until: datetime
    requests_per_minute: int
    max_response_bytes: int
    symbols_per_request: int = 1


@dataclass(frozen=True, slots=True)
class CatalogQuoteContext:
    listing: StockCatalogListing | None
    session: SessionDecision
    binding: CatalogQuoteBinding | None
    reason: CatalogQuoteReadiness


class CatalogDisplayQuote(BaseModel):
    """Prices cached without a durable financial instrument or provider identifier."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    bid: Decimal
    ask: Decimal
    mid: Decimal
    event_at: AwareDatetime
    collected_at: AwareDatetime


async def _session(
    db: AsyncSession, settings: Settings | SchedulerSettings, exchange: str, now: datetime
) -> SessionDecision:
    calendar = StockDataAdmission
    columns = [column for column in calendar.__table__.columns if column.name != "id"]
    row = (
        (await db.execute(select(*columns).where(calendar.product == "calendar")))
        .mappings()
        .one_or_none()
    )
    return session_at(
        exchange,
        now,
        await load_sessions(db, now),
        ProductAdmission(**row) if row else None,
        account=settings.stock_data_account,
        server=settings.stock_data_server,
    )


async def _display_grant(
    db: AsyncSession,
    settings: Settings | SchedulerSettings,
    exchange: str,
    fixture: bool,
    now: datetime,
) -> tuple[int, datetime, datetime, CatalogIexQuoteScope] | None:
    grant = StockCatalogAdmission
    account, server = settings.stock_data_account, settings.stock_data_server
    rows = (
        await db.execute(
            select(grant.id, grant.reviewed_at, grant.valid_until, grant.scope)
            .where(
                grant.artifact == _SCOPE_ARTIFACT,
                grant.is_fixture == fixture,
                grant.reviewed_at <= now,
                grant.valid_until > now,
                grant.revoked_at.is_(None),
                grant.fields.contains(_QUOTE_FIELDS),
                grant.scope.contains(
                    {
                        "account": account,
                        "server": server,
                        "listing_exchanges": [exchange],
                    }
                ),
            )
            .order_by(grant.id)
            .limit(2)
        )
    ).all()
    if len(rows) != 1:
        return None
    review_id, reviewed_at, valid_until, data = rows[0]
    try:
        scope = CatalogIexQuoteScope.model_validate_json(json.dumps(data))
    except TypeError, ValueError:
        return None
    if len(set(scope.listing_exchanges)) != len(scope.listing_exchanges):
        return None
    return review_id, reviewed_at, valid_until, scope


async def _mapping(
    db: AsyncSession,
    listing: StockCatalogListing,
    settings: Settings | SchedulerSettings,
    now: datetime,
) -> tuple[CatalogAssetMapping, datetime] | None:
    if (
        listing.provider_admission_id is None
        or listing.provider_asset_id is None
        or listing.provider_symbol is None
        or listing.provider_evidence_digest is None
        or listing.provider_verified_at is None
        or listing.provider_valid_until is None
        or not listing.provider_verified_at <= now < listing.provider_valid_until
        or listing.currency != "USD"
        or listing.units_per_share != 1
    ):
        return None
    grant = StockCatalogAdmission
    row = (
        await db.execute(
            select(grant.reviewed_at, grant.valid_until, grant.scope).where(
                grant.id == listing.provider_admission_id,
                grant.artifact == "alpaca_assets",
                ~grant.is_fixture,
                grant.reviewed_at <= now,
                grant.valid_until > now,
                grant.revoked_at.is_(None),
                grant.fields.contains(
                    {field: sorted(_MAPPING_PURPOSES) for field in _MAPPING_FIELDS}
                ),
            )
        )
    ).one_or_none()
    if row is None:
        return None
    reviewed_at, valid_until, scope = row
    try:
        provider = CatalogAssetAdmission.model_validate_json(json.dumps(scope["provider"]))
        units = _UNIT_EVIDENCE.validate_json(json.dumps(scope["units"]))
        matches = [unit for unit in units if unit.target.catalog_id == listing.security_id]
        if len(matches) != 1:
            return None
        unit = matches[0]
        if (
            provider.account != settings.stock_data_account
            or provider.server != settings.stock_data_server
            or provider.reviewed_at != reviewed_at
            or provider.valid_until != valid_until
            or provider.purposes != _MAPPING_PURPOSES
            or len(units) != len(provider.targets)
            or {evidence.target for evidence in units} != set(provider.targets)
            or unit.target.listing_version != listing.id
            or unit.target.listing_exchange != listing.listing_exchange
            or unit.target.provider_symbol != listing.provider_symbol
            or unit.target.provider_asset_id not in (None, listing.provider_asset_id)
            or unit.classification != listing.classification
            or unit.evidence_digest != listing.unit_evidence_digest
            or unit.reviewed_at != listing.unit_evidence_at
            or not max(reviewed_at, unit.reviewed_at)
            <= listing.provider_verified_at
            <= now
            < unit.valid_until
        ):
            return None
        target = CatalogAssetTarget.model_validate(
            {
                **unit.target.model_dump(),
                "provider_asset_id": listing.provider_asset_id,
            }
        )
        mapping_valid_until = min(valid_until, unit.valid_until)
        mapping = CatalogAssetMapping(
            target=target,
            unit_evidence=unit,
            verified_at=listing.provider_verified_at,
            valid_until=mapping_valid_until,
            admission_digest=provider.evidence_digest,
            evidence_digest=listing.provider_evidence_digest,
        )
    except KeyError, TypeError, ValueError:
        return None
    if not mapping_evidence_matches(mapping):
        return None
    expires = min(mapping_valid_until, listing.provider_valid_until, listing.valid_until)
    if mapping.target.provider_symbol != listing.ticker:
        alias = StockCatalogAlias
        alias_until = await db.scalar(
            select(alias.valid_until)
            .where(
                alias.listing_id == listing.id,
                alias.security_id == listing.security_id,
                alias.namespace != "former",
                alias.symbol == listing.provider_symbol,
                alias.verified_at <= now,
                alias.valid_until > now,
            )
            .order_by(alias.valid_until.desc())
            .limit(1)
        )
        if alias_until is None:
            return None
        expires = min(expires, alias_until)
    return mapping, expires


async def _live_source_expiry(
    db: AsyncSession, listing: StockCatalogListing, now: datetime
) -> datetime | None:
    # Use the current permission expiry, in case it was shortened after publication.
    ids = {
        listing.directory_admission_id,
        listing.name_admission_id,
        listing.classification_admission_id,
    }
    if None in ids:
        return None
    grant = StockCatalogAdmission
    rows = (
        (
            await db.execute(
                select(grant.id, grant.valid_until).where(
                    grant.id.in_(ids),
                    grant.reviewed_at <= now,
                    grant.valid_until > now,
                    grant.revoked_at.is_(None),
                    ~grant.is_fixture,
                )
            )
        )
        .tuples()
        .all()
    )
    if {admission_id for admission_id, _ in rows} != ids:
        return None
    return min(expiry for _, expiry in rows)


async def load_catalog_quote_context(
    db: AsyncSession, settings: Settings | SchedulerSettings, catalog_id: int, *, now: datetime
) -> CatalogQuoteContext:
    """Read current quote rights with the runtime's limited admission columns."""
    listing = await get_catalog_listing(db, settings, catalog_id, now=now)
    if listing is None:
        return CatalogQuoteContext(None, SessionDecision(), None, "identity_review")
    session = await _session(db, settings, listing.listing_exchange, now)
    if listing.state != "active" or listing.valid_until <= now:
        return CatalogQuoteContext(listing, session, None, "identity_review")
    if session.state == "unknown" or session.current is None or session.valid_until is None:
        return CatalogQuoteContext(listing, session, None, "session_unavailable")
    if not settings.stock_data_enabled:
        reason: CatalogQuoteReadiness = (
            "market_closed" if session.state == "closed" else "price_disabled"
        )
        return CatalogQuoteContext(listing, session, None, reason)
    generation = StockCatalogGeneration
    row = (
        await db.execute(
            select(generation.mode, generation.valid_until).where(
                generation.id == listing.generation_id,
                generation.is_active,
                generation.valid_until > now,
            )
        )
    ).one_or_none()
    if row is None or (row.mode == "fixture" and settings.env != "test"):
        return CatalogQuoteContext(listing, session, None, "identity_review")
    source_until = row.valid_until
    if row.mode == "live":
        live_source_until = await _live_source_expiry(db, listing, now)
        if live_source_until is None:
            return CatalogQuoteContext(None, session, None, "identity_review")
        source_until = min(source_until, live_source_until)
    quote_grant = await _display_grant(
        db, settings, listing.listing_exchange, row.mode == "fixture", now
    )
    if quote_grant is None:
        reason = "market_closed" if session.state == "closed" else "missing_permission"
        return CatalogQuoteContext(listing, session, None, reason)
    provider = await _mapping(db, listing, settings, now)
    if provider is None:
        reason = "market_closed" if session.state == "closed" else "mapping_review"
        return CatalogQuoteContext(listing, session, None, reason)
    mapping, mapping_until = provider
    review_id, reviewed_at, grant_until, scope = quote_grant
    fingerprint = sha256(
        json.dumps(
            [
                listing.generation_id,
                listing.security_id,
                listing.id,
                listing.provider_admission_id,
                source_until.isoformat(),
                session.current.calendar_admission_generation,
                session.valid_until.isoformat(),
                mapping.evidence_digest,
                review_id,
                reviewed_at.isoformat(),
                grant_until.isoformat(),
                scope.model_dump(mode="json"),
            ],
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    binding = CatalogQuoteBinding(
        catalog_id=listing.security_id,
        listing_version=listing.id,
        fingerprint=fingerprint,
        provider_symbol=mapping.target.provider_symbol,
        listing_exchange=mapping.target.listing_exchange,
        valid_until=min(source_until, mapping_until, grant_until, session.valid_until),
        requests_per_minute=scope.requests_per_minute,
        max_response_bytes=scope.max_response_bytes,
        symbols_per_request=scope.symbols_per_request,
    )
    return CatalogQuoteContext(
        listing, session, binding, "market_closed" if session.state == "closed" else "ready"
    )


def catalog_quote_valid_until(quote: CatalogDisplayQuote, binding: CatalogQuoteBinding) -> datetime:
    return min(binding.valid_until, quote.collected_at + _CACHE_AGE)


def catalog_quote_is_current(
    quote: CatalogDisplayQuote, context: CatalogQuoteContext, *, now: datetime
) -> bool:
    binding = context.binding
    if (
        binding is None
        or not utc(now)
        or not utc(quote.collected_at)
        or not quote.collected_at <= now < catalog_quote_valid_until(quote, binding)
    ):
        return False
    parsed = validate_iex_quote(
        RawIexQuote(
            quote.bid,
            quote.ask,
            quote.event_at,
            ["R"],
            tape="C" if binding.listing_exchange == "NASDAQ" else "A",
        ),
        listing_exchange=binding.listing_exchange,
        collected_at=quote.collected_at,
    )
    if parsed is None or parsed.mid != quote.mid:
        return False
    if context.session.state == "closed":
        return context.reason == "market_closed"
    current = context.session.current
    return (
        context.session.state == "open"
        and current is not None
        and current.opens_at is not None
        and current.closes_at is not None
        and current.opens_at <= quote.event_at <= quote.collected_at <= now < current.closes_at
        and now - quote.event_at < timedelta(seconds=120)
    )


async def read_catalog_quote(
    redis: Redis, context: CatalogQuoteContext, *, account: str, server: str, now: datetime
) -> CatalogDisplayQuote | None:
    binding = context.binding
    if binding is None:
        return None
    try:
        async with asyncio.timeout(1):
            raw = await redis.get(
                catalog_quote_key(
                    account=account,
                    server=server,
                    catalog_id=binding.catalog_id,
                    listing_version=binding.listing_version,
                    fingerprint=binding.fingerprint,
                )
            )
        if raw is None or len(raw) > _MAX_CACHE_BYTES:
            return None
        quote = CatalogDisplayQuote.model_validate_json(raw)
    except RedisError, TimeoutError, ValueError:
        return None
    return quote if catalog_quote_is_current(quote, context, now=now) else None


async def publish_catalog_quote(
    redis: Redis,
    request: CatalogQuoteRequest,
    binding: CatalogQuoteBinding,
    session: SessionDecision,
    price: ValidIexQuote,
    *,
    account: str,
    server: str,
    now: datetime,
) -> bool:
    """Write only a fresh IEX mark for the matching, still-pending selection."""
    if (
        request.catalog_id != binding.catalog_id
        or request.listing_version != binding.listing_version
        or request.fingerprint != binding.fingerprint
        or session.state != "open"
    ):
        return False
    quote = CatalogDisplayQuote(
        bid=price.bid,
        ask=price.ask,
        mid=price.mid,
        event_at=price.event_at,
        collected_at=price.collected_at,
    )
    if not catalog_quote_is_current(
        quote, CatalogQuoteContext(None, session, binding, "ready"), now=now
    ):
        return False
    lifetime = catalog_quote_valid_until(quote, binding) - now
    ttl_ms = math.floor(lifetime.total_seconds() * 1000)
    if ttl_ms < 1:
        return False
    return await complete_catalog_quote(
        redis,
        request,
        account=account,
        server=server,
        reason="ready",
        quote_json=quote.model_dump_json(),
        quote_ttl_ms=ttl_ms,
    )
