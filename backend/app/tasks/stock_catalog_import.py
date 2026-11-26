"""Explicit operator publication for prepared stock catalogs and selected mappings."""

import argparse
import asyncio
import hashlib
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, Field, SecretStr, TypeAdapter
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import aliased

from app.db.connection import database_connect_args
from app.db.portfolio_migrate import require_migrator, require_source
from app.models.stock_catalog import StockCatalogAdmission, StockCatalogAlias, StockCatalogListing
from app.services.stock_admission import catalog_action_policy
from app.services.stock_catalog_classification import CatalogModel
from app.services.stock_catalog_promotion import _REQUIRED_FIELDS, promote_catalog_instrument
from app.services.stock_catalog_provider import (
    CatalogAssetAdmission,
    CatalogAssetError,
    CatalogUnitEvidence,
    _check_target,
    _reject_constant,
    _reject_duplicates,
    _unique_targets,
    stage_reviewed_assets,
)
from app.services.stock_catalog_publish import (
    CatalogPublishError,
    ReviewedMappingScope,
    _active_generation,
    _current_admissions,
    _lock_catalog,
    _retirements,
    current_mapping_targets,
    promote_catalog_mappings,
    publish_catalog,
    reviewed_mapping_scope,
)
from app.services.stock_catalog_quotes import (
    _MAPPING_FIELDS,
    _MAPPING_PURPOSES,
    _QUOTE_FIELDS,
    CatalogIexQuoteScope,
    load_catalog_asset_mapping,
)
from app.tasks.stock_catalog_inventory import (
    _CLASSIFICATION_FIELDS,
    _DIRECTORY_FIELDS,
    _DURABLE_PURPOSES,
    MAX_STAGE_BYTES,
    CatalogManifest,
)

_PACKET_BYTES = 256 * 1024
_JSON_BYTES = 16384
_DIRECTORY_RIGHTS = {
    "nasdaqlisted": _DIRECTORY_FIELDS,
    "otherlisted": _DIRECTORY_FIELDS,
    "openfigi_nyse": _DIRECTORY_FIELDS,
    "openfigi": _CLASSIFICATION_FIELDS | {"aliases"},
    "issuer_exception": _CLASSIFICATION_FIELDS,
}
_FINANCIAL_FEEDS = {
    "catalog_execution": "iex",
    "catalog_mark": "iex",
    "catalog_halt": "nasdaq-rss",
    "catalog_actions": "alpaca-corporate-actions",
}
_FINANCIAL_FIELDS: dict[str, dict[str, list[str]]] = {
    **_REQUIRED_FIELDS,
    "catalog_halt": {
        field: ["collection", "execution", "storage", "backup"]
        for field in ("report_digest", "event_at", "valid_until", "state")
    },
}
_REVIEWED_UNITS = TypeAdapter(tuple[CatalogUnitEvidence, ...])


class _Admission(CatalogModel):
    artifact: str = Field(pattern=r"^[a-zA-Z0-9_.:-]{1,96}$")
    reference: str = Field(min_length=8, max_length=512)
    reviewed_at: AwareDatetime
    valid_until: AwareDatetime
    fields: dict[str, list[str]]
    scope: dict[str, object]


class _AdmissionPacket(CatalogModel):
    version: Literal[1]
    admissions: tuple[_Admission, ...] = Field(min_length=1, max_length=32)
    revoke_ids: tuple[int, ...] = Field(default=(), max_length=32)


class _ExactListingScope(CatalogModel):
    catalog_id: str = Field(pattern=r"^[1-9][0-9]{0,18}$")
    listing_id: str = Field(pattern=r"^[1-9][0-9]{0,18}$")
    provider_asset_id: str = Field(min_length=1, max_length=128)
    account: str = Field(min_length=1, max_length=128)
    server: str = Field(min_length=1, max_length=128)
    feed: str
    requests_per_minute: int = Field(default=200, ge=1, le=200)
    max_response_bytes: int = Field(default=1048576, ge=4096, le=1048576)
    symbols_per_request: int = Field(default=1, ge=1, le=8)


class _CatalogActionsScope(_ExactListingScope):
    all_us_replay_ingress: Literal[True]
    replay_region: Literal["us"]
    known_id_recheck: Literal[True]
    rest_symbols: list[str]
    history_start: str
    future_through: str
    mutation_start: str
    requests_per_minute: int = Field(ge=1, le=200)
    symbols_per_request: int = Field(ge=1, le=8)
    max_response_bytes: int = Field(ge=1, le=262144)


@dataclass(frozen=True, slots=True, repr=False)
class _OperatorConnection:
    env: str
    database_url: str
    database_ssl_ca_file: str | None


def _database_settings(fixture: bool) -> _OperatorConnection:
    url = os.environ.get("BIRJA_CATALOG_DATABASE_URL", "")
    if fixture:
        parsed = make_url(url)
        if (
            os.environ.get("ENV") not in {"dev", "test"}
            or parsed.drivername != "postgresql+asyncpg"
            or parsed.host not in {"localhost", "127.0.0.1"}
            or parsed.port != 55432
            or not parsed.database
            or not parsed.database.endswith("_test")
            or parsed.query
        ):
            raise CatalogPublishError("Fixtures require the isolated local test database")
        return _OperatorConnection("test", url, None)
    if make_url(url).username != "birja_migrator":
        raise CatalogPublishError("The restricted catalog operator connection is required")
    return _OperatorConnection("prod", url, os.environ.get("DATABASE_SSL_CA_FILE"))


async def _check_connection(
    conn: AsyncConnection, fixture: bool, *, for_finance: bool = False
) -> None:
    if fixture:
        database, session_role, current_role = (
            await conn.execute(text("SELECT current_database(), session_user, current_user"))
        ).one()
        if not database.endswith("_test") or session_role != current_role:
            raise CatalogPublishError("Fixtures require the isolated local test database")
        revision = (
            await conn.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one()
    else:
        revision = await require_migrator(conn)
    allowed = ("0026", "0027", "0028") if for_finance else ("0025", "0026", "0027", "0028")
    if revision not in allowed:
        raise CatalogPublishError("Catalog import requires the admitted catalog migration")


def _read_manifest(path: Path) -> CatalogManifest:
    if path.is_symlink() or not path.is_file():
        raise CatalogPublishError("Expected a reviewed regular manifest file")
    with path.open("rb") as stream:
        payload = stream.read(MAX_STAGE_BYTES + 1)
    if len(payload) > MAX_STAGE_BYTES:
        raise CatalogPublishError("Manifest exceeds its size bound")
    return CatalogManifest.model_validate_json(payload)


def _generation(value: str) -> int | None:
    if value == "empty":
        return None
    return _positive_id(value)


def _positive_id(value: str) -> int:
    try:
        result = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Expected a positive ID") from None
    if not 0 < result < 2**63:
        raise argparse.ArgumentTypeError("Expected a positive ID")
    return result


def _canonical_id(value: str) -> int:
    result = _positive_id(value)
    if value != str(result):
        raise argparse.ArgumentTypeError("Expected a canonical positive ID")
    return result


def _args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True, dest="command")
    publish = commands.add_parser("publish", help="Publish a complete reviewed catalog")
    publish.add_argument("manifest", type=Path)
    publish.add_argument("--expect-generation", type=_generation, required=True)
    publish.add_argument("--fixture", action="store_true")
    publish.add_argument("--fixture-as-of", type=datetime.fromisoformat)
    admit = commands.add_parser("admit", help="Review or apply an exact catalog scope packet")
    admit.add_argument("packet", type=Path)
    admit.add_argument("--expect-generation", type=_generation, required=True)
    admit.add_argument("--apply", action="store_true")
    admit.add_argument("--expected-packet-sha")
    admit.set_defaults(fixture=False)
    stage = commands.add_parser("stage-assets", help="Stage and promote the exact reviewed assets")
    stage.add_argument("--admission-id", type=_positive_id, required=True)
    stage.set_defaults(fixture=False)
    promote = commands.add_parser(
        "promote-instrument", help="Bind an exact reviewed issue to finance"
    )
    promote.add_argument("--catalog-id", type=_canonical_id, required=True)
    promote.add_argument("--listing-id", type=_canonical_id, required=True)
    promote.add_argument("--admission-id", type=_canonical_id, required=True)
    promote.set_defaults(fixture=False)
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> dict[str, object]:
    settings = _database_settings(args.fixture)
    engine = create_async_engine(
        settings.database_url,
        connect_args=database_connect_args(settings, migration=True),
        hide_parameters=True,
    )
    try:
        if args.command == "publish":
            manifest = _read_manifest(args.manifest)
            if args.fixture != (manifest.mode == "fixture") or (
                args.fixture_as_of is not None and not args.fixture
            ):
                raise CatalogPublishError("Manifest and operator mode must agree")
            now = args.fixture_as_of
            if now is not None and now.tzinfo is None:
                raise CatalogPublishError("A timezone-aware clock is required")
            async with AsyncSession(engine) as db, db.begin():
                await _check_connection(await db.connection(), args.fixture)
                receipt = await publish_catalog(
                    db, manifest, args.expect_generation, now=now, allow_fixture=args.fixture
                )
            return asdict(receipt)
        if args.command == "promote-instrument":
            return await _promote_instrument(
                engine, args.catalog_id, args.listing_id, args.admission_id
            )
        if args.command == "admit":
            return await _admit(engine, args)
        return await _stage_assets(engine, args.admission_id)
    finally:
        await engine.dispose()


def _read_packet(path: Path) -> tuple[_AdmissionPacket, str]:
    if path.is_symlink() or not path.is_file():
        raise CatalogPublishError("Expected a reviewed regular admission packet file")
    with path.open("rb") as stream:
        payload = stream.read(_PACKET_BYTES + 1)
    if len(payload) > _PACKET_BYTES:
        raise CatalogPublishError("Admission packet exceeds its size bound")
    json.loads(payload, object_pairs_hook=_reject_duplicates, parse_constant=_reject_constant)
    return _AdmissionPacket.model_validate_json(payload), hashlib.sha256(payload).hexdigest()


def _required_fields(row: _Admission) -> dict[str, set[str]]:
    if row.artifact in _DIRECTORY_RIGHTS:
        expected = {
            field: _DURABLE_PURPOSES | {"display"}
            if field in {"ticker", "company_name", "listing_exchange", "share_class"}
            else _DURABLE_PURPOSES
            for field in _DIRECTORY_RIGHTS[row.artifact]
        }
        if row.artifact == "issuer_exception" and set(row.scope) == {"retirements"}:
            return {**expected, "retirement": _DURABLE_PURPOSES}
        if row.scope:
            raise CatalogPublishError("Unexpected directory admission scope")
        return expected
    if row.artifact == "alpaca_assets":
        return {field: set(_MAPPING_PURPOSES) for field in _MAPPING_FIELDS}
    fields = (
        _QUOTE_FIELDS
        if row.artifact == "alpaca_iex_quotes"
        else _FINANCIAL_FIELDS.get(row.artifact)
    )
    if fields is None:
        raise CatalogPublishError("Unknown catalog admission artifact")
    return {field: set(purposes) for field, purposes in fields.items()}


def _check_admission_fields(row: _Admission, now: datetime) -> None:
    if (
        not row.reviewed_at <= now < row.valid_until
        or row.reviewed_at.utcoffset() != timedelta(0)
        or row.valid_until.utcoffset() != timedelta(0)
        or row.reference != row.reference.strip()
        or not row.reference.isprintable()
        or any(len(json.dumps(value).encode()) > _JSON_BYTES for value in (row.fields, row.scope))
    ):
        raise CatalogPublishError("Admission reference, scope or UTC validity is invalid")
    expected = _required_fields(row)
    allowed_purposes = _DURABLE_PURPOSES | {"display", "derivation", "cache", "execution"}
    if row.fields.keys() != expected.keys() or any(
        len(set(purposes)) != len(purposes)
        or not expected[field] <= set(purposes) <= allowed_purposes
        for field, purposes in row.fields.items()
    ):
        raise CatalogPublishError("Catalog admission has missing or contradictory field purposes")


def _check_account(account: str, server: str) -> None:
    if (account, server) != (
        os.environ.get("STOCK_DATA_ACCOUNT"),
        os.environ.get("STOCK_DATA_SERVER"),
    ) or any(value.strip() != value or not value.isprintable() for value in (account, server)):
        raise CatalogPublishError("Admission account or server differs from operator scope")


async def _check_asset_scope(db: AsyncSession, row: _Admission, now: datetime) -> None:
    if set(row.scope) != {"provider", "units"}:
        raise CatalogPublishError("Asset scope must contain exact provider and unit evidence")
    provider = CatalogAssetAdmission.model_validate_json(json.dumps(row.scope["provider"]))
    units = _REVIEWED_UNITS.validate_json(json.dumps(row.scope["units"]))
    _check_account(provider.account, provider.server)
    if (
        provider.environment != os.environ.get("ALPACA_ASSET_ENVIRONMENT")
        or provider.reviewed_at != row.reviewed_at
        or provider.valid_until != row.valid_until
        or provider.purposes != _MAPPING_PURPOSES
        or not _unique_targets(provider.targets)
        or provider.request_limit < len(provider.targets)
        or len(units) != len(provider.targets)
        or {unit.target for unit in units} != set(provider.targets)
    ):
        raise CatalogPublishError("Provider scope does not match the reviewed grant")
    scope = ReviewedMappingScope(0, provider, units)
    targets = await current_mapping_targets(db, scope, now)
    for unit in units:
        _check_target(unit, provider, targets, now)


async def _check_listing_scope(
    db: AsyncSession, row: _Admission, generation: int, now: datetime
) -> None:
    scope_type = _CatalogActionsScope if row.artifact == "catalog_actions" else _ExactListingScope
    scope = scope_type.model_validate(row.scope)
    _check_account(scope.account, scope.server)
    catalog_id, listing_id = int(scope.catalog_id), int(scope.listing_id)
    if scope.feed != _FINANCIAL_FEEDS[row.artifact] or max(catalog_id, listing_id) >= 2**63:
        raise CatalogPublishError("Admission feed or identity differs from the artifact")
    listing = await db.scalar(
        select(StockCatalogListing).where(
            StockCatalogListing.id == listing_id,
            StockCatalogListing.security_id == catalog_id,
            StockCatalogListing.generation_id == generation,
            StockCatalogListing.state == "active",
            StockCatalogListing.valid_until > now,
            StockCatalogListing.provider_asset_id == scope.provider_asset_id,
        )
    )
    mapping = (
        await load_catalog_asset_mapping(
            db, listing, now, account=scope.account, server=scope.server
        )
        if listing is not None
        else None
    )
    if listing is None or mapping is None:
        raise CatalogPublishError("Admission listing or provider mapping is no longer current")
    if row.artifact == "catalog_actions":
        provider_symbol = mapping[0].target.provider_symbol
        policy = catalog_action_policy(row.scope)
        if (
            policy is None
            or provider_symbol not in policy.rest_symbols
            or len(policy.rest_symbols) > policy.symbols_per_request
            or policy.history_start > now.date()
            or policy.mutation_start > now
        ):
            raise CatalogPublishError("Admission action policy differs from the reviewed listing")
        former_symbols = set(policy.rest_symbols) - {provider_symbol, listing.ticker}
        if former_symbols:
            alias, prior = StockCatalogAlias, aliased(StockCatalogListing)
            verified = set(
                await db.scalars(
                    select(alias.symbol).where(
                        alias.security_id == catalog_id,
                        alias.listing_id == listing_id,
                        alias.namespace == "former",
                        alias.symbol.in_(former_symbols),
                        alias.verified_at <= now,
                        alias.valid_until > now,
                        select(prior.id)
                        .where(
                            prior.security_id == catalog_id,
                            prior.id != listing_id,
                            prior.ticker == alias.symbol,
                            prior.provider_asset_id == scope.provider_asset_id,
                        )
                        .exists(),
                    )
                )
            )
            if verified != former_symbols:
                raise CatalogPublishError("Admission action symbols lack verified listing aliases")


def _overlap(a: StockCatalogAdmission, b: StockCatalogAdmission) -> bool:
    if a.artifact != b.artifact:
        return False
    if a.artifact == "alpaca_iex_quotes":
        return (
            (a.scope.get("account"), a.scope.get("server"))
            == (b.scope["account"], b.scope["server"])
            and isinstance(exchanges := a.scope.get("listing_exchanges"), list)
            and any(exchange in b.scope["listing_exchanges"] for exchange in exchanges)
        )
    if a.artifact in _FINANCIAL_FEEDS:
        return all(
            a.scope.get(field) == b.scope[field]
            for field in ("account", "server", "catalog_id", "listing_id")
        )
    return (
        (a.reference, a.reviewed_at, a.valid_until) == (b.reference, b.reviewed_at, b.valid_until)
        and a.fields.keys() == b.fields.keys()
        and all(
            isinstance(prior := a.fields[field], list)
            and len(prior) == len(purposes)
            and all(purpose in prior for purpose in purposes)
            for field, purposes in b.fields.items()
        )
    )


async def _admit(engine: AsyncEngine, args: argparse.Namespace) -> dict[str, object]:
    packet, digest = _read_packet(args.packet)
    if (args.apply and args.expected_packet_sha != digest) or (
        not args.apply and args.expected_packet_sha is not None
    ):
        raise CatalogPublishError("Apply requires the exact reviewed admission packet SHA-256")
    if len(set(packet.revoke_ids)) != len(packet.revoke_ids) or any(
        not 0 < proof_id < 2**63 for proof_id in packet.revoke_ids
    ):
        raise CatalogPublishError("Invalid or duplicate revocation identifiers")
    require_source()
    async with AsyncSession(engine) as db, db.begin():
        await _check_connection(await db.connection(), False, for_finance=True)
        await _lock_catalog(db)
        generation = await _active_generation(db)
        current_id = generation.id if generation else None
        if current_id != args.expect_generation or (generation and generation.mode != "live"):
            raise CatalogPublishError("Expected live catalog generation has changed")
        now = datetime.now(UTC)
        prior = list(await db.scalars(_current_admissions(now).with_for_update()))
        retired = [row for row in prior if row.id in packet.revoke_ids]
        if len(retired) != len(packet.revoke_ids):
            raise CatalogPublishError("A revocation does not match a current live admission")
        remaining = [row for row in prior if row.id not in packet.revoke_ids]
        for record in retired:
            record.revoked_at = now
        prepared: list[StockCatalogAdmission] = []
        for row in packet.admissions:
            _check_admission_fields(row, now)
            record = StockCatalogAdmission(**row.model_dump(), is_fixture=False)
            if row.artifact == "alpaca_assets":
                await _check_asset_scope(db, row, now)
            elif row.artifact == "alpaca_iex_quotes":
                scope = CatalogIexQuoteScope.model_validate_json(json.dumps(row.scope))
                _check_account(scope.account, scope.server)
                if len(scope.listing_exchanges) != len(set(scope.listing_exchanges)):
                    raise CatalogPublishError("Admission repeats the same listing exchange")
            elif row.artifact in _FINANCIAL_FEEDS:
                if (
                    generation is None
                    or not generation.published_at <= now < generation.valid_until
                ):
                    raise CatalogPublishError("A current live catalog generation is required")
                await _check_listing_scope(db, row, generation.id, now)
            elif row.artifact == "issuer_exception":
                _retirements({"issuer_exception": record}, now)
            if any(_overlap(existing, record) for existing in [*remaining, *prepared]):
                raise CatalogPublishError(
                    "Admission duplicates or overlaps existing reviewed scope"
                )
            prepared.append(record)
        receipt: dict[str, object] = {
            "disposition": "applied" if args.apply else "reviewed",
            "packet_sha256": digest,
            "count": len(prepared),
        }
        if args.apply:
            db.add_all(prepared)
            await db.flush()
            receipt["admission_ids"] = [str(record.id) for record in prepared]
        else:
            await db.rollback()
        if retired:
            receipt["revoked_count"] = len(retired)
        return receipt


async def _promote_instrument(
    engine: AsyncEngine, catalog_id: int, listing_id: int, admission_id: int
) -> dict[str, object]:
    account = os.environ.get("STOCK_DATA_ACCOUNT", "")
    server = os.environ.get("STOCK_DATA_SERVER", "")
    if not account or not server:
        raise CatalogPublishError("Explicit operator provider account and server are required")
    require_source()
    async with AsyncSession(engine) as db, db.begin():
        await _check_connection(await db.connection(), False, for_finance=True)
        binding = await promote_catalog_instrument(
            db,
            catalog_id,
            listing_id,
            admission_id,
            datetime.now(UTC),
            account=account,
            server=server,
        )
    return {
        "disposition": "promoted",
        "catalog_id": str(binding.catalog_id),
        "coin_id": str(binding.coin_id),
        "listing_id": str(binding.listing_id),
        "admission_id": str(binding.admission_id),
    }


async def _stage_assets(engine: AsyncEngine, admission_id: int) -> dict[str, object]:
    account = os.environ.get("STOCK_DATA_ACCOUNT", "")
    server = os.environ.get("STOCK_DATA_SERVER", "")
    environment = os.environ.get("ALPACA_ASSET_ENVIRONMENT", "")
    key = SecretStr(os.environ.get("ALPACA_API_KEY", ""))
    secret = SecretStr(os.environ.get("ALPACA_SECRET_KEY", ""))
    if (
        not account
        or not server
        or environment not in {"paper", "live"}
        or not key.get_secret_value().strip()
        or not secret.get_secret_value().strip()
    ):
        raise CatalogPublishError(
            "Explicit operator provider settings and credentials are required"
        )

    async with AsyncSession(engine) as db, db.begin():
        await _check_connection(await db.connection(), False)
        now = datetime.now(UTC)
        scope = await reviewed_mapping_scope(db, admission_id, now, lock=True)
        if (scope.provider.account, scope.provider.server, scope.provider.environment) != (
            account,
            server,
            environment,
        ):
            raise CatalogPublishError("Provider admission does not match the configured account")
        expected_targets = await current_mapping_targets(db, scope, now)
        record = await db.get(StockCatalogAdmission, admission_id)
        if record is None:
            raise CatalogPublishError("Provider admission disappeared")
        if "attempted_at" in record.scope:
            raise CatalogPublishError("This single-use provider admission was already attempted")
        # The claim survives request failure and process interruption, so a
        # restart cannot spend the same bounded reviewed provider allowance.
        claimed_at = now.isoformat()
        record.scope = {**record.scope, "attempted_at": claimed_at}

    async def before_attempt() -> None:
        async with AsyncSession(engine) as db, db.begin():
            await _check_connection(await db.connection(), False)
            checked_at = datetime.now(UTC)
            current = await reviewed_mapping_scope(db, admission_id, checked_at)
            claimed = await db.get(StockCatalogAdmission, admission_id)
            if (
                current != scope
                or claimed is None
                or claimed.scope.get("attempted_at") != claimed_at
                or await current_mapping_targets(db, current, checked_at) != expected_targets
            ):
                raise CatalogPublishError("The provider claim or selected listing has changed")

    staged = await stage_reviewed_assets(
        scope.provider,
        scope.units,
        account=account,
        server=server,
        environment=scope.provider.environment,
        expected_listings=expected_targets,
        key=key,
        secret=secret,
        before_attempt=before_attempt,
    )
    async with AsyncSession(engine) as db, db.begin():
        await _check_connection(await db.connection(), False)
        promoted = await promote_catalog_mappings(db, admission_id, staged, now=datetime.now(UTC))
    return {
        "disposition": "promoted",
        "count": promoted,
        "evidence_digests": [mapping.evidence_digest for mapping in staged],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _args(argv)
    try:
        receipt = asyncio.run(_run(args))
    except CatalogPublishError as exc:
        print(json.dumps({"disposition": "refused", "reason": str(exc)}), file=sys.stderr)
        return 2
    except CatalogAssetError as exc:
        receipt = {"disposition": "refused", "reason": exc.reason}
        print(json.dumps(receipt), file=sys.stderr)
        return 2
    except ValueError, OSError, SQLAlchemyError:
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
