"""Review and enroll an ordered batch from two retained Alpaca asset inventories.

The private JSON scope identifies the live catalog generation and its manifest,
the exact account/server/environment, both raw inventory receipts, and reviewed
field-purpose grants for assets, execution, marks, halts and corporate actions.
It also records the USD single-share unit evidence and the action replay terms.
The operator reviews the resulting digest before applying the same batch.
Repeat with the returned next_after_listing until it is null.
"""

import argparse
import asyncio
import hashlib
import json
import os
import stat
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, Field, TypeAdapter, ValidationError
from sqlalchemy import false, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import SchedulerSettings
from app.db.connection import database_connect_args
from app.db.portfolio_migrate import require_source
from app.models.corporate_action import StockActionState
from app.models.stock import StockInstrument
from app.models.stock_catalog import StockCatalogAdmission, StockCatalogListing
from app.models.stock_catalog_finance import StockCatalogActionCoverage, StockCatalogInstrument
from app.services.stock_catalog_asset_inventory import (
    MAX_ASSET_INVENTORY_BYTES,
    CatalogInventoryAsset,
    parse_catalog_asset_inventory,
)
from app.services.stock_catalog_classification import SHA256, CatalogModel
from app.services.stock_catalog_promotion import promote_catalog_instrument
from app.services.stock_catalog_provider import (
    AssetEnvironment,
    CatalogAssetAdmission,
    CatalogAssetError,
    CatalogAssetTarget,
    CatalogUnitEvidence,
    _mapping,
    _reject_constant,
    _reject_duplicates,
)
from app.services.stock_catalog_publish import (
    CatalogPublishError,
    _active_generation,
    _lock_catalog,
    promote_catalog_mappings,
)
from app.services.stock_catalog_quotes import _MAPPING_PURPOSES
from app.services.stock_catalog_search import _permitted_listing
from app.services.stock_catalog_sources import ListingExchange
from app.services.stock_quote_rules import CURATED_SYMBOLS
from app.tasks.stock_catalog_import import (
    _FINANCIAL_FEEDS,
    _Admission,
    _canonical_id,
    _check_account,
    _check_admission_fields,
    _check_connection,
    _check_listing_scope,
    _database_settings,
)

_MAX_BATCH = 100
_MAX_SCOPE_BYTES = 64 * 1024
_PROVENANCE = "bulk-alpaca-assets-v1:"
_LOOKAHEAD_FIELD = SchedulerSettings.model_fields["stock_actions_future_days"]
_LOOKAHEAD: TypeAdapter[int] = TypeAdapter(_LOOKAHEAD_FIELD.rebuild_annotation())


class _Evidence(CatalogModel):
    reference: str = Field(min_length=8, max_length=350)
    reviewed_at: AwareDatetime
    valid_until: AwareDatetime
    fields: dict[str, list[str]]


class _Units(CatalogModel):
    reference: str = Field(min_length=8, max_length=350)
    reviewed_at: AwareDatetime
    valid_until: AwareDatetime
    currency: Literal["USD"]
    units_per_share: Literal[1]


class _TradingLimits(CatalogModel):
    requests_per_minute: int = Field(ge=1, le=200)
    max_response_bytes: int = Field(ge=4096, le=1048576)
    symbols_per_request: int = Field(ge=1, le=8)


class _ActionPolicy(CatalogModel):
    all_us_replay_ingress: Literal[True]
    replay_region: Literal["us"]
    known_id_recheck: Literal[True]
    history_start: date
    future_through: date
    mutation_start: AwareDatetime
    requests_per_minute: int = Field(ge=1, le=200)
    max_response_bytes: int = Field(ge=1, le=262144)
    symbols_per_request: int = Field(ge=1, le=8)


class _InventoryReceipt(CatalogModel):
    sha256: str = Field(pattern=SHA256)
    verified_at: AwareDatetime


class _Scope(CatalogModel):
    version: Literal[1]
    generation_id: int = Field(gt=0, lt=2**63)
    manifest_sha256: str = Field(pattern=SHA256)
    account: str = Field(min_length=1, max_length=128)
    server: str = Field(min_length=1, max_length=128)
    environment: AssetEnvironment
    inventories: dict[ListingExchange, _InventoryReceipt]
    assets: _Evidence
    units: _Units
    execution: _Evidence
    mark: _Evidence
    halt: _Evidence
    actions: _Evidence
    execution_limits: _TradingLimits
    mark_limits: _TradingLimits
    halt_limits: _TradingLimits
    action_policy: _ActionPolicy
    replace_bulk_grants: bool = False


@dataclass(frozen=True, slots=True, repr=False)
class _Inputs:
    scope: _Scope
    digest: str
    assets: dict[tuple[str, str], CatalogInventoryAsset]
    ambiguous_symbols: frozenset[str]


@dataclass(frozen=True, slots=True, repr=False)
class _Candidate:
    listing_id: int
    catalog_id: int
    decision: str
    evidence_digest: str
    admission_ids: tuple[int, ...] = ()
    state_digest: str = ""


@dataclass(frozen=True, slots=True, repr=False)
class _Batch:
    candidates: tuple[_Candidate, ...]
    digest: str
    next_after: int | None


def _hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def _private_file(path: Path, limit: int) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o600:
            raise CatalogPublishError("Expected a regular mode-0600 input file")
        payload = stream.read(limit + 1)
    if len(payload) > limit:
        raise CatalogPublishError("Bulk enrollment input exceeds its size bound")
    return payload


def _inputs(scope_path: Path, nyse_path: Path, nasdaq_path: Path) -> _Inputs:
    encoded = _private_file(scope_path, _MAX_SCOPE_BYTES)
    json.loads(encoded, object_pairs_hook=_reject_duplicates, parse_constant=_reject_constant)
    scope = _Scope.model_validate_json(encoded)
    if set(scope.inventories) != {"NYSE", "NASDAQ"}:
        raise CatalogPublishError("Both exchange inventory receipts are required")
    paths: tuple[tuple[ListingExchange, Path], ...] = (
        ("NYSE", nyse_path),
        ("NASDAQ", nasdaq_path),
    )
    assets: dict[tuple[str, str], CatalogInventoryAsset] = {}
    provider_ids = set()
    for exchange, path in paths:
        receipt = scope.inventories[exchange]
        body = _private_file(path, MAX_ASSET_INVENTORY_BYTES)
        if hashlib.sha256(body).hexdigest() != receipt.sha256:
            raise CatalogPublishError("Inventory SHA-256 differs from the reviewed scope")
        snapshot = parse_catalog_asset_inventory(
            body, exchange=exchange, verified_at=receipt.verified_at
        )
        for row in snapshot.rows:
            if row.provider_asset_id in provider_ids:
                raise CatalogPublishError("Provider inventory repeats an asset across exchanges")
            provider_ids.add(row.provider_asset_id)
            assets[exchange, row.symbol] = row
    occurrences = Counter(asset.symbol for asset in assets.values())
    return _Inputs(
        scope,
        hashlib.sha256(encoded).hexdigest(),
        assets,
        frozenset(symbol for symbol, count in occurrences.items() if count > 1),
    )


def _evidence(scope: _Scope) -> tuple[tuple[str, _Evidence], ...]:
    return (
        ("alpaca_assets", scope.assets),
        ("catalog_execution", scope.execution),
        ("catalog_mark", scope.mark),
        ("catalog_halt", scope.halt),
        ("catalog_actions", scope.actions),
    )


def _validate_inputs(inputs: _Inputs, now: datetime) -> None:
    scope = inputs.scope
    _check_account(scope.account, scope.server)
    if scope.environment != os.environ.get("ALPACA_ASSET_ENVIRONMENT"):
        raise CatalogPublishError("Bulk enrollment environment differs from operator scope")
    for artifact, evidence in _evidence(scope):
        if evidence.reference != evidence.reference.strip() or not evidence.reference.isprintable():
            raise CatalogPublishError("Bulk grant evidence reference is invalid")
        _check_admission_fields(
            _Admission(artifact=artifact, scope={}, **evidence.model_dump()), now
        )
    units, policy = scope.units, scope.action_policy
    try:
        lookahead = _LOOKAHEAD.validate_python(
            os.environ.get("STOCK_ACTIONS_FUTURE_DAYS", _LOOKAHEAD_FIELD.default)
        )
    except ValidationError:
        raise CatalogPublishError("Invalid configured stock-action lookahead") from None
    last_active_day = (scope.actions.valid_until - timedelta(microseconds=1)).date()
    if (policy.future_through - last_active_day).days < lookahead:
        raise CatalogPublishError(
            "Reviewed action horizon does not cover runtime lookahead through grant expiry"
        )
    if (
        not units.reviewed_at <= now < units.valid_until
        or units.reviewed_at.utcoffset() != timedelta(0)
        or units.valid_until.utcoffset() != timedelta(0)
        or not units.reference.isprintable()
        or units.reference != units.reference.strip()
        or policy.mutation_start.utcoffset() != timedelta(0)
        or not policy.history_start <= now.date() <= policy.future_through
        or policy.mutation_start > now
        or any(
            not max(scope.assets.reviewed_at, units.reviewed_at) <= receipt.verified_at <= now
            or receipt.verified_at.utcoffset() != timedelta(0)
            for receipt in scope.inventories.values()
        )
    ):
        raise CatalogPublishError("Bulk unit, inventory or action policy evidence is not current")


def _reference(digest: str, evidence: _Evidence) -> str:
    return f"{_PROVENANCE}{digest}:{evidence.reference}"


def _enrollment_digest(
    inputs: _Inputs, listing: StockCatalogListing, asset: CatalogInventoryAsset
) -> str:
    return _hash(
        {
            "scope": inputs.digest,
            "listing": listing.id,
            "security": listing.security_id,
            "row": listing.row_digest,
            "classification": listing.evidence_digest,
            "asset": asdict(asset),
        }
    )


def _finance_identity(
    listing: StockCatalogListing, scope: _Scope, asset: CatalogInventoryAsset
) -> dict[str, str]:
    return {
        "catalog_id": str(listing.security_id),
        "listing_id": str(listing.id),
        "provider_asset_id": asset.provider_asset_id,
        "account": scope.account,
        "server": scope.server,
    }


def _provider_identity(scope: _Scope) -> dict[str, str]:
    return {"account": scope.account, "server": scope.server, "environment": scope.environment}


def _provider_target(
    listing: StockCatalogListing, asset: CatalogInventoryAsset
) -> dict[str, object]:
    return {
        "catalog_id": listing.security_id,
        "listing_version": listing.id,
        "listing_exchange": asset.exchange,
        "provider_symbol": asset.symbol,
    }


async def _applicable_grants(
    db: AsyncSession,
    listing: StockCatalogListing,
    scope: _Scope,
    asset: CatalogInventoryAsset,
    now: datetime,
    digest: str,
) -> list[StockCatalogAdmission]:
    grant = StockCatalogAdmission
    finance = grant.artifact.in_(_FINANCIAL_FEEDS) & grant.scope.contains(
        _finance_identity(listing, scope, asset)
    )
    mapping = (
        (grant.artifact == "alpaca_assets")
        & grant.scope.contains(
            {
                "provider": {
                    **_provider_identity(scope),
                    "targets": [_provider_target(listing, asset)],
                }
            }
        )
        & (
            (grant.id == listing.provider_admission_id)
            | grant.reference.startswith(f"{_PROVENANCE}{digest}:")
        )
    )
    return list(
        await db.scalars(
            select(grant)
            .where(~grant.is_fixture, finance | mapping, grant.valid_until > now)
            .order_by(grant.id)
            .with_for_update()
        )
    )


def _same_provider_scope(
    grant: StockCatalogAdmission,
    listing: StockCatalogListing,
    scope: _Scope,
    asset: CatalogInventoryAsset,
) -> bool:
    if grant.artifact == "alpaca_assets":
        provider = grant.scope.get("provider")
        return (
            grant.id == listing.provider_admission_id
            and listing.provider_asset_id == asset.provider_asset_id
            and isinstance(provider, dict)
            and all(provider.get(key) == value for key, value in _provider_identity(scope).items())
            and isinstance(targets := provider.get("targets"), list)
            and any(
                isinstance(target, dict)
                and target.get("provider_asset_id") in (None, asset.provider_asset_id)
                and all(
                    target.get(key) == value
                    for key, value in _provider_target(listing, asset).items()
                )
                for target in targets
            )
        )
    return (
        grant.artifact in _FINANCIAL_FEEDS
        and grant.scope.get("feed") == _FINANCIAL_FEEDS[grant.artifact]
        and all(
            grant.scope.get(key) == value
            for key, value in _finance_identity(listing, scope, asset).items()
        )
    )


async def _mapping_scope_matches(
    db: AsyncSession, listing: StockCatalogListing, scope: _Scope, asset: CatalogInventoryAsset
) -> bool:
    if listing.provider_admission_id is None:
        return True
    provider = await db.get(StockCatalogAdmission, listing.provider_admission_id)
    return provider is not None and _same_provider_scope(provider, listing, scope, asset)


async def _candidate(
    db: AsyncSession,
    inputs: _Inputs,
    listing: StockCatalogListing,
    permitted: bool,
    now: datetime,
) -> _Candidate:
    def candidate(
        decision: str, digest: str = "", ids: tuple[int, ...] = (), state_digest: str = ""
    ) -> _Candidate:
        return _Candidate(listing.id, listing.security_id, decision, digest, ids, state_digest)

    if listing.ticker in CURATED_SYMBOLS:
        return candidate("legacy")
    if listing.state != "active" or listing.classification not in {
        "common_stock",
        "ordinary_shares",
    }:
        return candidate("ineligible")
    if not permitted or listing.valid_until <= now:
        return candidate("listing_rights_unavailable")
    asset = inputs.assets.get((listing.listing_exchange, listing.ticker))
    if asset is None:
        return candidate("asset_missing")
    if asset.symbol in inputs.ambiguous_symbols:
        return candidate("asset_ambiguous")
    if not asset.tradable:
        return candidate("asset_not_tradable")
    if listing.provider_asset_id is not None and (
        listing.provider_asset_id != asset.provider_asset_id
        or listing.provider_symbol != asset.symbol
    ):
        return candidate("mapping_conflict")
    prior_owner = await db.scalar(
        select(StockCatalogListing.id)
        .where(
            StockCatalogListing.provider_asset_id == asset.provider_asset_id,
            StockCatalogListing.security_id != listing.security_id,
        )
        .limit(1)
    )
    binding = await db.get(StockCatalogInstrument, listing.security_id)
    provider_owner = await db.scalar(
        select(StockInstrument.coin_id).where(
            StockInstrument.provider_asset_id == asset.provider_asset_id
        )
    )
    if prior_owner is not None or (
        provider_owner is not None and (binding is None or provider_owner != binding.coin_id)
    ):
        return candidate("mapping_conflict")
    if not await _mapping_scope_matches(db, listing, inputs.scope, asset):
        return candidate("mapping_conflict")
    origin = None
    if binding is not None:
        prior_listing = await db.get(StockCatalogListing, binding.listing_id)
        prior_execution = await db.get(StockCatalogAdmission, binding.admission_id)
        state = await db.get(StockActionState, binding.coin_id)
        coverage = await db.get(StockCatalogActionCoverage, binding.coin_id)
        origin = (
            coverage.journal_origin
            if coverage is not None
            else (
                state.journal_start_at
                if state is not None and state.journal_start_at is not None
                else binding.promoted_at
            )
        )
        policy = inputs.scope.action_policy
        instrument = await db.get(StockInstrument, binding.coin_id)
        if (
            prior_listing is None
            or prior_listing.ticker != listing.ticker
            or prior_execution is None
            or not _same_provider_scope(prior_execution, prior_listing, inputs.scope, asset)
            or not await _mapping_scope_matches(db, prior_listing, inputs.scope, asset)
            or state is None
            or instrument is None
            or instrument.provider_asset_id != asset.provider_asset_id
            or origin < binding.promoted_at
            or not policy.history_start <= origin.date() <= policy.future_through
            or policy.mutation_start > origin
            or state.journal_start_at not in (None, origin)
        ):
            return candidate("journal_or_identity_conflict")

    digest = _enrollment_digest(inputs, listing, asset)
    grants = await _applicable_grants(db, listing, inputs.scope, asset, now, digest)
    refs = {
        artifact: _reference(digest, evidence) for artifact, evidence in _evidence(inputs.scope)
    }
    if any(row.revoked_at is not None and row.reference in refs.values() for row in grants):
        return candidate("revoked_bulk_scope", digest)
    current = [row for row in grants if row.revoked_at is None]
    ids = tuple(row.id for row in current)
    state_digest = _hash(
        {
            "binding": (binding.listing_id, binding.coin_id, binding.admission_id)
            if binding
            else None,
            "journal_origin": origin.isoformat() if origin is not None else None,
            "provider_admission": listing.provider_admission_id,
            "source_admissions": (
                listing.directory_admission_id,
                listing.name_admission_id,
                listing.classification_admission_id,
            ),
            "previous_grants": [
                (
                    row.id,
                    row.reference,
                    row.reviewed_at.isoformat(),
                    row.valid_until.isoformat(),
                    row.fields,
                    row.scope,
                )
                for row in current
            ],
        }
    )
    same = {row.artifact: row for row in current if row.reference == refs.get(row.artifact)}
    if current and len(current) == len(same) == len(refs):
        if (
            binding is not None
            and binding.listing_id == listing.id
            and binding.admission_id == same["catalog_execution"].id
            and listing.provider_admission_id == same["alpaca_assets"].id
            and listing.provider_valid_until is not None
            and listing.provider_valid_until > now
        ):
            return candidate("already_enrolled", digest, ids, state_digest)
        return candidate("admission_conflict", digest, ids, state_digest)
    if current and (
        not inputs.scope.replace_bulk_grants
        or any(
            not row.reference.startswith(_PROVENANCE) or row.reviewed_at > now for row in current
        )
        or len({row.artifact for row in current}) != len(current)
    ):
        return candidate("admission_conflict", digest, ids, state_digest)
    return candidate("renew" if binding is not None else "enroll", digest, ids, state_digest)


async def _plan(db: AsyncSession, inputs: _Inputs, now: datetime, after: int, limit: int) -> _Batch:
    if not 0 <= after < 2**63 or not 1 <= limit <= _MAX_BATCH:
        raise CatalogPublishError("Bulk batch cursor or size is out of range")
    _validate_inputs(inputs, now)
    generation = await _active_generation(db)
    scope = inputs.scope
    if generation is None or (
        generation.id != scope.generation_id
        or generation.manifest_sha256 != scope.manifest_sha256
        or generation.mode != "live"
        or not generation.published_at <= now < generation.valid_until
    ):
        raise CatalogPublishError("The reviewed live catalog generation has changed")

    rows = (
        await db.execute(
            select(StockCatalogListing, _permitted_listing(now, false()))
            .where(
                StockCatalogListing.generation_id == generation.id,
                StockCatalogListing.id > after,
            )
            .order_by(StockCatalogListing.id)
            .limit(limit + 1)
        )
    ).all()
    candidates = tuple(
        [
            await _candidate(db, inputs, listing, permitted, now)
            for listing, permitted in rows[:limit]
        ]
    )
    next_after = candidates[-1].listing_id if len(rows) > limit else None
    return _Batch(
        candidates,
        _hash(
            {
                "scope": inputs.digest,
                "after_listing": after,
                "limit": limit,
                "next_after_listing": next_after,
                "results": [asdict(item) for item in candidates],
            }
        ),
        next_after,
    )


def _record(row: _Admission, now: datetime) -> StockCatalogAdmission:
    _check_admission_fields(row, now)
    return StockCatalogAdmission(**row.model_dump(), is_fixture=False)


async def _apply_candidate(
    db: AsyncSession, inputs: _Inputs, candidate: _Candidate, now: datetime
) -> None:
    scope = inputs.scope
    listing = await db.get(StockCatalogListing, candidate.listing_id)
    if listing is None or listing.classification not in ("common_stock", "ordinary_shares"):
        raise CatalogPublishError("A reviewed batch listing has changed")
    classification: Literal["common_stock", "ordinary_shares"] = (
        "common_stock" if listing.classification == "common_stock" else "ordinary_shares"
    )
    asset = inputs.assets[listing.listing_exchange, listing.ticker]
    for admission_id in candidate.admission_ids:
        previous = await db.get(StockCatalogAdmission, admission_id)
        if (
            previous is None
            or previous.revoked_at is not None
            or not _same_provider_scope(previous, listing, scope, asset)
        ):
            raise CatalogPublishError("A reviewed batch admission has changed")
        previous.revoked_at = now

    target = CatalogAssetTarget(
        catalog_id=listing.security_id,
        listing_version=listing.id,
        listing_exchange=asset.exchange,
        provider_symbol=asset.symbol,
        provider_asset_id=listing.provider_asset_id,
    )
    provider = CatalogAssetAdmission(
        account=scope.account,
        server=scope.server,
        environment=scope.environment,
        reviewed_at=scope.assets.reviewed_at,
        valid_until=scope.assets.valid_until,
        evidence_digest=candidate.evidence_digest,
        targets=(target,),
        purposes=_MAPPING_PURPOSES,
        request_limit=1,
    )
    units = CatalogUnitEvidence(
        target=target,
        currency=scope.units.currency,
        units_per_share=scope.units.units_per_share,
        classification=classification,
        reviewed_at=scope.units.reviewed_at,
        valid_until=scope.units.valid_until,
        evidence_digest=_hash(
            {
                "scope_listing_and_bulk_row": candidate.evidence_digest,
                "unit_review": scope.units.model_dump(mode="json"),
            }
        ),
    )
    provider_grant = _record(
        _Admission(
            artifact="alpaca_assets",
            **{
                **scope.assets.model_dump(),
                "reference": _reference(candidate.evidence_digest, scope.assets),
            },
            scope={
                "provider": provider.model_dump(mode="json"),
                "units": [units.model_dump(mode="json")],
            },
        ),
        now,
    )
    db.add(provider_grant)
    await db.flush()
    # This normalized record comes from the reviewed bulk row. It is never
    # represented as a separate provider request in the retained evidence.
    bulk_row = json.dumps(
        {
            "id": asset.provider_asset_id,
            "symbol": asset.symbol,
            "exchange": asset.exchange,
            "class": "us_equity",
            "status": "active",
        }
    ).encode()
    await promote_catalog_mappings(
        db,
        provider_grant.id,
        [_mapping(bulk_row, units, provider, scope.inventories[asset.exchange].verified_at)],
        now=now,
    )

    grants = {}
    common_scope = _finance_identity(listing, scope, asset)
    specifications = (
        ("catalog_execution", scope.execution, scope.execution_limits.model_dump()),
        ("catalog_mark", scope.mark, scope.mark_limits.model_dump()),
        ("catalog_halt", scope.halt, scope.halt_limits.model_dump()),
        (
            "catalog_actions",
            scope.actions,
            {**scope.action_policy.model_dump(mode="json"), "rest_symbols": [asset.symbol]},
        ),
    )
    for artifact, evidence, parameters in specifications:
        row = _Admission(
            artifact=artifact,
            reference=_reference(candidate.evidence_digest, evidence),
            reviewed_at=evidence.reviewed_at,
            valid_until=evidence.valid_until,
            fields=evidence.fields,
            scope={**common_scope, **parameters, "feed": _FINANCIAL_FEEDS[artifact]},
        )
        await _check_listing_scope(db, row, scope.generation_id, now)
        grant = _record(row, now)
        db.add(grant)
        grants[artifact] = grant
    await db.flush()
    await promote_catalog_instrument(
        db,
        listing.security_id,
        listing.id,
        grants["catalog_execution"].id,
        now,
        account=scope.account,
        server=scope.server,
    )


async def _execute_batch(
    db: AsyncSession,
    inputs: _Inputs,
    *,
    after: int,
    limit: int,
    now: datetime,
    expected_sha: str | None = None,
) -> dict[str, object]:
    await _lock_catalog(db)
    batch = await _plan(db, inputs, now, after, limit)
    if expected_sha is not None:
        if expected_sha != batch.digest:
            raise CatalogPublishError("Apply requires the exact reviewed bulk batch SHA-256")
        for candidate in batch.candidates:
            if candidate.decision in {"enroll", "renew"}:
                await _apply_candidate(db, inputs, candidate, now)

    return {
        "disposition": "reviewed" if expected_sha is None else "applied",
        "generation_id": inputs.scope.generation_id,
        "batch_sha256": batch.digest,
        "scope_sha256": inputs.digest,
        "next_after_listing": batch.next_after,
        "count": len(batch.candidates),
        "outcomes": dict(Counter(candidate.decision for candidate in batch.candidates)),
    }


def _args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", required=True, type=Path)
    parser.add_argument("--nyse", required=True, type=Path)
    parser.add_argument("--nasdaq", required=True, type=Path)
    parser.add_argument("--after-listing", type=_canonical_id, default=0)
    parser.add_argument("--limit", type=int, default=_MAX_BATCH, help="batch size from 1 to 100")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-batch-sha")
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> dict[str, object]:
    if args.apply != (args.expected_batch_sha is not None):
        raise CatalogPublishError("Apply requires the exact reviewed bulk batch SHA-256")
    require_source()
    inputs = _inputs(args.scope, args.nyse, args.nasdaq)
    settings = _database_settings(False)
    engine = create_async_engine(
        settings.database_url,
        connect_args=database_connect_args(settings, migration=True),
        hide_parameters=True,
    )
    try:
        async with AsyncSession(engine) as db, db.begin():
            await _check_connection(await db.connection(), False, for_finance=True)
            return await _execute_batch(
                db,
                inputs,
                after=args.after_listing,
                limit=args.limit,
                now=datetime.now(UTC),
                expected_sha=args.expected_batch_sha,
            )
    finally:
        await engine.dispose()


def main(argv: Sequence[str] | None = None) -> int:
    args = _args(argv)
    try:
        receipt = asyncio.run(_run(args))
    except CatalogPublishError as exc:
        print(json.dumps({"disposition": "refused", "reason": str(exc)}), file=sys.stderr)
        return 2
    except CatalogAssetError, ValueError, OSError, SQLAlchemyError:
        print(
            json.dumps(
                {"disposition": "refused", "reason": "invalid input or operator connection"}
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
