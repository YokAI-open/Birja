"""Publish reconciled stock catalog generations and reviewed mappings."""

import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from pydantic import AwareDatetime, BaseModel, ConfigDict, TypeAdapter
from sqlalchemy import Select, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock_catalog import (
    StockCatalogAdmission,
    StockCatalogAlias,
    StockCatalogGeneration,
    StockCatalogListing,
    StockCatalogSecurity,
)
from app.services.stock_catalog_classification import CORROBORATION_AGE, InventoryRow
from app.services.stock_catalog_provider import (
    CatalogAssetAdmission,
    CatalogAssetMapping,
    CatalogAssetTarget,
    CatalogUnitEvidence,
    mapping_evidence_matches,
)
from app.services.stock_catalog_sources import SYMBOL_PATTERN, CatalogSourceError
from app.tasks.stock_catalog_inventory import CatalogManifest, SourceEvidence, validate_manifest

_CATALOG_LOCK = 1026019025
_DIRECTORY_LIFETIME = timedelta(days=4)
_UNIT_EVIDENCE = TypeAdapter(tuple[CatalogUnitEvidence, ...])
_MAPPING_FIELDS = {
    "provider_asset_id",
    "provider_symbol",
    "asset_evidence",
    "currency",
    "units_per_share",
    "unit_evidence",
}
_MAPPING_PURPOSES = {"collection", "internal_use", "derived_use", "display", "storage", "backup"}


class CatalogPublishError(ValueError):
    """A staged catalog change was refused."""


@dataclass(frozen=True, slots=True)
class PublicationReceipt:
    generation_id: int
    digest: str
    disposition: str
    mode: str
    coverage: dict[str, object]
    active: int
    review: int
    retired: int


class _Retirement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    identity_key: str
    listing_version: int
    listing_exchange: str
    ticker: str
    evidence_digest: str
    evidence_at: AwareDatetime


def _canonical_digest(manifest: CatalogManifest) -> str:
    payload = json.dumps(
        manifest.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _valid_listing_fields(row: InventoryRow) -> bool:
    return (
        re.fullmatch(SYMBOL_PATTERN, row.ticker) is not None
        and 0 < len(row.company_name) <= 255
        and row.company_name == row.company_name.strip()
        and row.company_name.isprintable()
        and (
            row.share_class is None
            or re.fullmatch(r"[A-Z][A-Z0-9]{0,4}", row.share_class) is not None
        )
        and row.reason in {"reviewed_issue_evidence", "corroborated_share_class"}
        and len(row.aliases) < 10
        and all(re.fullmatch(SYMBOL_PATTERN, alias.symbol) for alias in row.aliases)
    )


async def _lock_catalog(db: AsyncSession) -> None:
    if not db.in_transaction():
        raise CatalogPublishError("Catalog writes require a transaction")
    await db.execute(text("SELECT pg_catalog.pg_advisory_xact_lock(:key)"), {"key": _CATALOG_LOCK})


async def _active_generation(db: AsyncSession) -> StockCatalogGeneration | None:
    result = await db.execute(
        select(StockCatalogGeneration).where(StockCatalogGeneration.is_active)
    )
    return result.scalars().one_or_none()


def _current_admissions(now: datetime) -> Select[tuple[StockCatalogAdmission]]:
    return select(StockCatalogAdmission).where(
        StockCatalogAdmission.revoked_at.is_(None),
        StockCatalogAdmission.reviewed_at <= now,
        StockCatalogAdmission.valid_until > now,
        ~StockCatalogAdmission.is_fixture,
    )


async def _reviewed_rights(
    db: AsyncSession, manifest: CatalogManifest, now: datetime
) -> dict[str, StockCatalogAdmission]:
    if manifest.mode == "fixture":
        if manifest.rights:
            raise CatalogPublishError("Fixture catalog includes live rights")
        return {}
    candidates = (
        await db.scalars(
            _current_admissions(now)
            .where(StockCatalogAdmission.artifact.in_(item.artifact for item in manifest.rights))
            .with_for_update()
        )
    ).all()
    trusted: dict[str, StockCatalogAdmission] = {}
    for item in manifest.rights:
        fields = {key: set(purposes) for key, purposes in item.fields.items()}
        admitted = [
            candidate
            for candidate in candidates
            if candidate.artifact == item.artifact
            and candidate.reference == item.reference
            and candidate.reviewed_at == item.reviewed_at
            and candidate.valid_until == item.valid_until
            and {key: set(purposes) for key, purposes in candidate.fields.items()} == fields
        ]
        if len(admitted) != 1:
            raise CatalogPublishError("Manifest rights do not match a trusted operator admission")
        trusted[item.artifact] = admitted[0]
    return trusted


def _check_directory_refresh(
    old: StockCatalogGeneration, sources: tuple[SourceEvidence, SourceEvidence]
) -> None:
    try:
        previous = [
            SourceEvidence.model_validate_json(json.dumps(old.sources[src.artifact]))
            for src in sources
        ]
    except KeyError, TypeError, ValueError:
        raise CatalogPublishError("Stored directory evidence has an invalid shape") from None
    if any(
        new.artifact != prior.artifact
        or new.published_at <= prior.published_at
        or new.sha256 == prior.sha256
        for prior, new in zip(previous, sources, strict=True)
    ):
        raise CatalogPublishError("Publication requires a newer pair of directory artifacts")


def _retirements(
    trusted: dict[str, StockCatalogAdmission], now: datetime
) -> dict[str, _Retirement]:
    decision = trusted.get("issuer_exception")
    if decision is None or "retirements" not in decision.scope:
        return {}
    if not _MAPPING_PURPOSES.difference({"display"}).issubset(
        decision.fields.get("retirement", ())
    ):
        raise CatalogPublishError("Reviewed retirements lack durable rights")
    payload = decision.scope["retirements"]
    if not isinstance(payload, list):
        raise CatalogPublishError("Reviewed retirements have an invalid shape")
    evidence_by_identity = {}
    for value in payload:
        try:
            evidence = _Retirement.model_validate(value)
        except ValueError:
            raise CatalogPublishError("Reviewed retirement evidence is malformed") from None
        if (
            not re.fullmatch(r"[0-9a-f]{64}", evidence.evidence_digest)
            or not timedelta(0) <= now - evidence.evidence_at <= CORROBORATION_AGE
            or evidence.identity_key in evidence_by_identity
        ):
            raise CatalogPublishError("Reviewed retirement evidence is stale or ambiguous")
        evidence_by_identity[evidence.identity_key] = evidence
    return evidence_by_identity


def _inactive_listing(
    prior: StockCatalogListing,
    generation_id: int,
    identity: str,
    occupancy: set[tuple[str, str]],
    retirements: dict[str, _Retirement],
) -> StockCatalogListing:
    state, reason = "review", "missing_without_retirement_evidence"
    retirement = retirements.get(identity)
    if prior.state == "retired":
        state, reason = prior.state, prior.reason
    elif retirement is not None and (
        retirement.listing_version == prior.id
        and retirement.listing_exchange == prior.listing_exchange
        and retirement.ticker == prior.ticker
    ):
        state, reason = "retired", "confirmed_retirement"
    elif (prior.listing_exchange, prior.ticker) in occupancy:
        state, reason = "retired", "verified_ticker_reuse"
    return StockCatalogListing(
        generation_id=generation_id,
        security_id=prior.security_id,
        ticker=prior.ticker,
        normalized_ticker=prior.normalized_ticker,
        listing_exchange=prior.listing_exchange,
        company_name=prior.company_name,
        normalized_name=prior.normalized_name,
        share_class=prior.share_class,
        classification=prior.classification,
        state=state,
        reason=reason,
        source=prior.source,
        row_key=prior.row_key,
        row_digest=prior.row_digest,
        evidence_digest=prior.evidence_digest,
        evidence_at=prior.evidence_at,
        valid_until=prior.valid_until,
        directory_admission_id=prior.directory_admission_id,
        name_admission_id=prior.name_admission_id,
        classification_admission_id=prior.classification_admission_id,
    )


async def _receipt(
    db: AsyncSession, generation: StockCatalogGeneration, disposition: str
) -> PublicationReceipt:
    states = list(
        await db.scalars(
            select(StockCatalogListing.state).where(
                StockCatalogListing.generation_id == generation.id
            )
        )
    )
    return PublicationReceipt(
        generation.id,
        generation.manifest_sha256,
        disposition,
        generation.mode,
        generation.coverage,
        states.count("active"),
        states.count("review"),
        states.count("retired"),
    )


async def _prior_listings(
    db: AsyncSession, old: StockCatalogGeneration | None
) -> dict[str, StockCatalogListing]:
    if old is None:
        return {}
    previous = await db.execute(
        select(StockCatalogSecurity.identity_key, StockCatalogListing)
        .join(StockCatalogListing, StockCatalogListing.security_id == StockCatalogSecurity.id)
        .where(StockCatalogListing.generation_id == old.id)
    )
    return {identity: listing for identity, listing in previous}


async def _issue_ids(db: AsyncSession, identities: set[str], now: datetime) -> dict[str, int]:
    found = {
        identity: issue_id
        for identity, issue_id in await db.execute(
            select(StockCatalogSecurity.identity_key, StockCatalogSecurity.id).where(
                StockCatalogSecurity.identity_key.in_(identities)
            )
        )
    }
    new_issues = {
        identity: StockCatalogSecurity(identity_key=identity, created_at=now)
        for identity in sorted(identities - found.keys())
    }
    db.add_all(new_issues.values())
    await db.flush()
    found.update({identity: issue.id for identity, issue in new_issues.items()})
    return found


def _active_listing(
    row: InventoryRow,
    generation: StockCatalogGeneration,
    trusted: dict[str, StockCatalogAdmission],
    security_id: int,
) -> StockCatalogListing:
    if row.evidence_at is None or row.listing_exchange is None:
        raise CatalogPublishError("Listing evidence is incomplete")
    directory = trusted.get(row.source)
    classification = trusted.get(
        "issuer_exception" if row.reason == "reviewed_issue_evidence" else "openfigi"
    )
    return StockCatalogListing(
        generation_id=generation.id,
        security_id=security_id,
        ticker=row.ticker,
        normalized_ticker=row.ticker,
        listing_exchange=row.listing_exchange,
        company_name=row.company_name,
        normalized_name=row.company_name.casefold(),
        share_class=row.share_class,
        classification=row.classification,
        state="active",
        reason=row.reason,
        source=row.source,
        row_key=row.row_key,
        row_digest=row.row_digest,
        evidence_digest=row.evidence_digest,
        evidence_at=row.evidence_at,
        valid_until=min(row.evidence_at + CORROBORATION_AGE, generation.valid_until),
        directory_admission_id=directory.id if directory else None,
        name_admission_id=directory.id if directory else None,
        classification_admission_id=classification.id if classification else None,
    )


async def publish_catalog(
    db: AsyncSession,
    manifest: CatalogManifest,
    expected_generation_id: int | None,
    *,
    now: datetime | None = None,
    allow_fixture: bool = False,
) -> PublicationReceipt:
    """Write a reconciled replacement under a caller-owned transaction."""
    if manifest.mode == "fixture" and not allow_fixture:
        raise CatalogPublishError("Fixture publication requires an isolated test database")
    await _lock_catalog(db)
    now = now or datetime.now(UTC)
    try:
        validate_manifest(manifest, now)
    except CatalogSourceError as exc:
        raise CatalogPublishError(str(exc)) from None
    rows = [row for row in manifest.rows if row.disposition == "included"]
    if not manifest.complete or not all(_valid_listing_fields(row) for row in rows):
        raise CatalogPublishError("Catalog candidate is incomplete or has invalid listing fields")
    sources_end = min(source.published_at + _DIRECTORY_LIFETIME for source in manifest.sources)
    if not now < sources_end:
        raise CatalogPublishError("Directory evidence has expired")
    if any(
        row.evidence_at is None or not now < row.evidence_at + CORROBORATION_AGE for row in rows
    ):
        raise CatalogPublishError("Classification evidence has expired")

    digest = _canonical_digest(manifest)
    trusted = await _reviewed_rights(db, manifest, now)
    old = await _active_generation(db)
    if old is not None and old.mode != manifest.mode:
        raise CatalogPublishError("Fixture and live catalog generations cannot be mixed")
    if old is not None and old.manifest_sha256 == digest:
        return await _receipt(db, old, "already_published")
    if (old.id if old else None) != expected_generation_id:
        raise CatalogPublishError("The expected catalog generation has changed")
    if old is not None:
        _check_directory_refresh(old, manifest.sources)

    retirements = _retirements(trusted, now)
    incoming = {row.identity_key: row for row in rows if row.identity_key is not None}
    occupancy: set[tuple[str, str]] = {
        (row.listing_exchange, row.ticker) for row in rows if row.listing_exchange
    }
    prior_listings = await _prior_listings(db, old)
    for venue in ("NASDAQ", "NYSE"):
        previous_active = [
            identity
            for identity, listing in prior_listings.items()
            if listing.state == "active" and listing.listing_exchange == venue
        ]
        missing = sum(identity not in incoming for identity in previous_active)
        if len(previous_active) >= 10 and missing * 5 > len(previous_active):
            raise CatalogPublishError("Directory refresh would unexpectedly remove many listings")

    generation = StockCatalogGeneration(
        mode=manifest.mode,
        manifest_sha256=digest,
        sources={src.artifact: src.model_dump(mode="json") for src in manifest.sources},
        coverage={
            venue: counts.model_dump(mode="json") for venue, counts in manifest.coverage.items()
        },
        is_active=True,
        published_at=now,
        valid_until=min([sources_end] + [scope.valid_until for scope in trusted.values()]),
    )
    if old is not None:
        old.is_active = False
        await db.flush()
    db.add(generation)
    await db.flush()

    issue_ids = await _issue_ids(db, set(incoming), now)
    inserted = [
        (
            _active_listing(row, generation, trusted, issue_ids[identity]),
            row,
            prior_listings.get(identity),
        )
        for identity, row in incoming.items()
    ]
    db.add_all(listing for listing, _, _ in inserted)
    for identity, prior in prior_listings.items():
        if identity not in incoming:
            db.add(_inactive_listing(prior, generation.id, identity, occupancy, retirements))
    await db.flush()
    await _add_aliases(db, inserted, occupancy, now)
    return await _receipt(db, generation, "published")


async def _add_aliases(
    db: AsyncSession,
    inserted: list[tuple[StockCatalogListing, InventoryRow, StockCatalogListing | None]],
    occupancy: set[tuple[str, str]],
    now: datetime,
) -> None:
    prior_ids = [prior.id for _, _, prior in inserted if prior is not None]
    prior_aliases: dict[int, list[StockCatalogAlias]] = {}
    if prior_ids:
        for alias in await db.scalars(
            select(StockCatalogAlias).where(
                StockCatalogAlias.listing_id.in_(prior_ids),
                StockCatalogAlias.namespace == "former",
                StockCatalogAlias.valid_until > now,
            )
        ):
            prior_aliases.setdefault(alias.listing_id, []).append(alias)
    aliases: list[StockCatalogAlias] = []
    for listing, row, prior in inserted:
        previous_aliases = {}
        if prior is not None and prior.directory_admission_id == listing.directory_admission_id:
            previous_aliases = {
                alias.symbol: (alias.verified_at, alias.valid_until)
                for alias in prior_aliases.get(prior.id, ())
            }
            if prior.ticker != listing.ticker and now < prior.valid_until:
                previous_aliases[prior.ticker] = (now, prior.valid_until)
        symbols = {(alias.namespace, alias.symbol) for alias in row.aliases}
        if row.evidence_at is None:
            raise CatalogPublishError("Listing alias evidence is incomplete")
        entries: dict[tuple[str, str], tuple[datetime, datetime]] = {
            (namespace, symbol): (row.evidence_at, listing.valid_until)
            for namespace, symbol in symbols
        }
        entries.update(
            {
                ("former", symbol): (verified, min(listing.valid_until, expires))
                for symbol, (verified, expires) in previous_aliases.items()
                if symbol != listing.ticker
                and (listing.listing_exchange, symbol) not in occupancy
                and verified < min(listing.valid_until, expires)
            }
        )
        aliases.extend(
            StockCatalogAlias(
                listing_id=listing.id,
                security_id=listing.security_id,
                namespace=namespace,
                symbol=symbol,
                normalized_symbol=symbol,
                verified_at=verified,
                valid_until=expires,
            )
            for (namespace, symbol), (verified, expires) in entries.items()
        )
    db.add_all(aliases)
    await db.flush()


@dataclass(frozen=True, slots=True)
class ReviewedMappingScope:
    id: int
    provider: CatalogAssetAdmission
    units: tuple[CatalogUnitEvidence, ...]


async def reviewed_mapping_scope(
    db: AsyncSession, admission_id: int, now: datetime, *, lock: bool = False
) -> ReviewedMappingScope:
    """Read separately retained field rights and exact selected unit evidence."""
    query = _current_admissions(now).where(
        StockCatalogAdmission.id == admission_id, StockCatalogAdmission.artifact == "alpaca_assets"
    )
    record = await db.scalar(query.with_for_update() if lock else query)
    if record is None or any(
        not _MAPPING_PURPOSES.issubset(record.fields.get(field, ())) for field in _MAPPING_FIELDS
    ):
        raise CatalogPublishError("Selected provider fields lack current reviewed rights")
    try:
        provider = CatalogAssetAdmission.model_validate_json(json.dumps(record.scope["provider"]))
        units = _UNIT_EVIDENCE.validate_json(json.dumps(record.scope["units"]))
    except KeyError, ValueError, TypeError:
        raise CatalogPublishError("Provider admission or unit evidence is malformed") from None
    if (
        provider.reviewed_at != record.reviewed_at
        or provider.valid_until != record.valid_until
        or provider.purposes != _MAPPING_PURPOSES
        or len({unit.target for unit in units}) != len(units)
        or {unit.target for unit in units} != set(provider.targets)
    ):
        raise CatalogPublishError("Provider scope differs from the retained admission")
    return ReviewedMappingScope(record.id, provider, units)


async def _selected_listings(
    db: AsyncSession,
    scope: ReviewedMappingScope,
    now: datetime,
    *,
    allow_fixture: bool,
) -> dict[int, StockCatalogListing]:
    gen = await _active_generation(db)
    if gen is None or now >= gen.valid_until or (gen.mode == "fixture" and not allow_fixture):
        raise CatalogPublishError("A current admitted catalog is required")
    listings = {
        listing.id: listing
        for listing in await db.scalars(
            select(StockCatalogListing).where(
                StockCatalogListing.generation_id == gen.id,
                StockCatalogListing.id.in_(
                    target.listing_version for target in scope.provider.targets
                ),
                StockCatalogListing.state == "active",
                StockCatalogListing.valid_until > now,
            )
        )
    }
    rights_ids = {
        value
        for listing in listings.values()
        for value in (
            listing.directory_admission_id,
            listing.name_admission_id,
            listing.classification_admission_id,
        )
        if value is not None
    }
    if rights_ids:
        eligible = set(
            await db.scalars(
                _current_admissions(now)
                .where(StockCatalogAdmission.id.in_(rights_ids))
                .with_only_columns(StockCatalogAdmission.id)
            )
        )
        if eligible != rights_ids:
            raise CatalogPublishError("Selected listing rights have expired or been revoked")
    elif gen.mode != "fixture":
        raise CatalogPublishError("Selected listing has no durable field admission")

    for unit in scope.units:
        target = unit.target
        listing = listings.get(target.listing_version)
        if (
            listing is None
            or target.catalog_id != listing.security_id
            or target.listing_exchange != listing.listing_exchange
            or target.provider_asset_id != listing.provider_asset_id
            or listing.classification != unit.classification
            or not unit.reviewed_at <= now < unit.valid_until
        ):
            raise CatalogPublishError("Selected listing version or unit evidence has changed")
        if target.provider_symbol != listing.ticker and not (
            await db.scalar(
                select(StockCatalogAlias.id).where(
                    StockCatalogAlias.listing_id == listing.id,
                    StockCatalogAlias.namespace != "former",
                    StockCatalogAlias.symbol == target.provider_symbol,
                    StockCatalogAlias.verified_at <= now,
                    StockCatalogAlias.valid_until > now,
                )
            )
        ):
            raise CatalogPublishError("Provider symbol lacks verified current listing evidence")
    return listings


async def current_mapping_targets(
    db: AsyncSession, scope: ReviewedMappingScope, now: datetime
) -> dict[int, CatalogAssetTarget]:
    """Resolve admitted active versions before an operator's bounded reference stage."""
    await _selected_listings(db, scope, now, allow_fixture=False)
    return {target.catalog_id: target for target in scope.provider.targets}


async def promote_catalog_mappings(
    db: AsyncSession,
    admission_id: int,
    mappings: Sequence[CatalogAssetMapping],
    *,
    now: datetime | None = None,
    allow_fixture: bool = False,
) -> int:
    """Bind verified responses to unchanged active listing versions as one write."""
    await _lock_catalog(db)
    now = now or datetime.now(UTC)
    scope = await reviewed_mapping_scope(db, admission_id, now, lock=True)
    listings = await _selected_listings(db, scope, now, allow_fixture=allow_fixture)
    assets = {mapping.target.provider_asset_id for mapping in mappings}
    if (
        len(mappings) != len(scope.units)
        or len(assets) != len(mappings)
        or None in assets
        or {mapping.unit_evidence for mapping in mappings} != set(scope.units)
    ):
        raise CatalogPublishError("Staged mappings do not match the selected reviewed scope")
    existing_bindings = set(
        await db.execute(
            select(StockCatalogListing.provider_asset_id, StockCatalogListing.security_id).where(
                StockCatalogListing.provider_asset_id.in_(assets)
            )
        )
    )
    validated = []
    for mapping in mappings:
        target, unit = mapping.target, mapping.unit_evidence
        listing = listings[unit.target.listing_version]
        expires = min(mapping.valid_until, listing.valid_until)
        if (
            target.model_copy(update={"provider_asset_id": unit.target.provider_asset_id})
            != unit.target
            or (
                unit.target.provider_asset_id is not None
                and unit.target.provider_asset_id != target.provider_asset_id
            )
            or mapping.admission_digest != scope.provider.evidence_digest
            or not scope.provider.reviewed_at <= mapping.verified_at <= now < expires
            or not unit.reviewed_at <= mapping.verified_at
            or mapping.valid_until > min(scope.provider.valid_until, unit.valid_until)
            or not mapping_evidence_matches(mapping)
            or any(
                asset_id == target.provider_asset_id and security_id != listing.security_id
                for asset_id, security_id in existing_bindings
            )
        ):
            raise CatalogPublishError("Staged provider or share-unit evidence was refused")
        validated.append((listing, mapping, expires))

    for listing, mapping, expires in validated:
        target, unit = mapping.target, mapping.unit_evidence
        listing.provider_asset_id = target.provider_asset_id
        listing.provider_symbol = target.provider_symbol
        listing.provider_evidence_digest = mapping.evidence_digest
        listing.provider_verified_at = mapping.verified_at
        listing.provider_valid_until = expires
        listing.provider_admission_id = scope.id
        listing.unit_evidence_digest = unit.evidence_digest
        listing.unit_evidence_at = unit.reviewed_at
        listing.currency = unit.currency
        listing.units_per_share = unit.units_per_share
    await db.flush()
    return len(mappings)
