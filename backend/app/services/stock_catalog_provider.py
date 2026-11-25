"""Operator-scoped Alpaca Assets lookups for exact stock catalog versions."""

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Literal
from urllib.parse import quote

import httpx
from pydantic import AwareDatetime, Field, SecretStr

from app.services.stock_catalog_classification import SHA256, CatalogModel
from app.services.stock_catalog_sources import SYMBOL_PATTERN, ListingExchange

_ASSET_ID = r"^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$"
_ASSET_ROOTS = {"paper": "https://paper-api.alpaca.markets", "live": "https://api.alpaca.markets"}
_PURPOSES = frozenset({"collection", "internal_use", "derived_use", "display", "storage", "backup"})
_RESPONSE_BYTES = 32_768
_DEADLINE = 5.0
AssetEnvironment = Literal["paper", "live"]


class CatalogAssetError(Exception):
    """A redacted outcome safe to record in an operator receipt."""

    def __init__(self, reason: str, *, retry_after: int | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.retry_after = retry_after


class CatalogAssetTarget(CatalogModel):
    catalog_id: int = Field(gt=0, le=2**63 - 1)
    listing_version: int = Field(gt=0, le=2**63 - 1)
    listing_exchange: ListingExchange
    provider_symbol: str = Field(pattern=rf"^{SYMBOL_PATTERN}$")
    provider_asset_id: str | None = Field(default=None, pattern=_ASSET_ID)


class CatalogUnitEvidence(CatalogModel):
    target: CatalogAssetTarget
    currency: Literal["USD"]
    units_per_share: int = Field(ge=1, le=1)
    classification: Literal["common_stock", "ordinary_shares"]
    reviewed_at: AwareDatetime
    valid_until: AwareDatetime
    evidence_digest: str = Field(pattern=SHA256)


class CatalogAssetAdmission(CatalogModel):
    account: str = Field(min_length=1, max_length=128)
    server: str = Field(min_length=1, max_length=128)
    environment: AssetEnvironment
    reviewed_at: AwareDatetime
    valid_until: AwareDatetime
    evidence_digest: str = Field(pattern=SHA256)
    targets: tuple[CatalogAssetTarget, ...] = Field(min_length=1, max_length=2)
    purposes: frozenset[str] = Field(max_length=len(_PURPOSES))
    request_limit: int = Field(ge=1, le=2)


class CatalogAssetMapping(CatalogModel):
    target: CatalogAssetTarget
    unit_evidence: CatalogUnitEvidence
    verified_at: AwareDatetime
    valid_until: AwareDatetime
    admission_digest: str = Field(pattern=SHA256)
    evidence_digest: str = Field(pattern=SHA256)


def _now(clock: Callable[[], datetime]) -> datetime:
    now = clock()
    if now.utcoffset() != timedelta(0):
        raise CatalogAssetError("invalid_clock")
    return now.astimezone(UTC)


def _window_current(reviewed_at: datetime, valid_until: datetime, now: datetime) -> bool:
    return (
        reviewed_at.utcoffset() == valid_until.utcoffset() == timedelta(0)
        and reviewed_at <= now < valid_until
    )


def _admitted(
    admission: CatalogAssetAdmission, now: datetime, *, account: str, server: str
) -> bool:
    return (
        admission.account == account
        and admission.server == server
        and admission.purposes == _PURPOSES
        and _window_current(admission.reviewed_at, admission.valid_until, now)
    )


def _unique_targets(targets: Sequence[CatalogAssetTarget]) -> bool:
    provider_ids = [target.provider_asset_id for target in targets if target.provider_asset_id]
    return (
        len({target.catalog_id for target in targets}) == len(targets)
        and len({target.listing_version for target in targets}) == len(targets)
        and len({target.listing_exchange for target in targets}) == len(targets)
        and len({target.provider_symbol for target in targets}) == len(targets)
        and len(set(provider_ids)) == len(provider_ids)
    )


def _check_target(
    unit: CatalogUnitEvidence,
    admission: CatalogAssetAdmission,
    expected_listings: Mapping[int, CatalogAssetTarget],
    now: datetime,
) -> None:
    expected = expected_listings.get(unit.target.catalog_id)
    if unit.target not in admission.targets or expected != unit.target:
        raise CatalogAssetError("listing_version_or_scope")
    if not _window_current(unit.reviewed_at, unit.valid_until, now):
        raise CatalogAssetError("unit_evidence_expired")


def _retry_after(value: str | None, now: datetime) -> int | None:
    if not value or len(value) > 64:
        return None
    if value.isascii() and value.isdecimal():
        return int(value)
    try:
        retry_at = parsedate_to_datetime(value)
    except ValueError, OverflowError:
        return None
    if retry_at.tzinfo is None:
        return None
    return max(0, int((retry_at - now).total_seconds()))


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate field")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError("invalid number")


def _mapped_id(body: bytes, target: CatalogAssetTarget) -> str:
    try:
        asset = json.loads(
            body, object_pairs_hook=_reject_duplicates, parse_constant=_reject_constant
        )
    except ValueError, RecursionError:
        raise CatalogAssetError("asset_json") from None
    if not isinstance(asset, dict):
        raise CatalogAssetError("asset_shape")

    candidate = asset.get("id")
    if (
        not isinstance(candidate, str)
        or asset.get("class") != "us_equity"
        or asset.get("status") != "active"
        or asset.get("exchange") != target.listing_exchange
        or asset.get("symbol") != target.provider_symbol
        or (target.provider_asset_id is not None and candidate != target.provider_asset_id)
    ):
        raise CatalogAssetError("asset_identity_or_status")
    return candidate


async def _read_asset(
    http: httpx.AsyncClient,
    target: CatalogAssetTarget,
    environment: AssetEnvironment,
    now: datetime,
) -> bytes:
    identifier = quote(target.provider_asset_id or target.provider_symbol, safe="")
    url = f"{_ASSET_ROOTS[environment]}/v2/assets/{identifier}"
    try:
        async with (
            asyncio.timeout(_DEADLINE),
            http.stream(
                "GET",
                url,
                headers={"Accept": "application/json", "Accept-Encoding": "identity"},
                follow_redirects=False,
                timeout=_DEADLINE,
            ) as response,
        ):
            if response.status_code == 429:
                raise CatalogAssetError(
                    "asset_rate_limited",
                    retry_after=_retry_after(response.headers.get("Retry-After"), now),
                )
            if response.status_code == 404:
                raise CatalogAssetError("asset_missing")
            if response.status_code != 200:
                raise CatalogAssetError("asset_http")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise CatalogAssetError("asset_encoding")

            body = bytearray()
            async for part in response.aiter_bytes():
                if len(body) + len(part) > _RESPONSE_BYTES:
                    raise CatalogAssetError("asset_response_limit")
                body.extend(part)
            return bytes(body)
    except TimeoutError, httpx.TimeoutException:
        raise CatalogAssetError("asset_timeout") from None
    except httpx.HTTPError:
        raise CatalogAssetError("asset_transport") from None


def _mapping_digest(
    target: CatalogAssetTarget,
    unit: CatalogUnitEvidence,
    admission_digest: str,
    verified_at: datetime,
    valid_until: datetime,
) -> str:
    normalized = {
        "target": target.model_dump(mode="json"),
        "unit_evidence": unit.model_dump(mode="json"),
        "admission": admission_digest,
        "verified_at": verified_at.isoformat(),
        "valid_until": valid_until.isoformat(),
    }
    return hashlib.sha256(
        json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def mapping_evidence_matches(mapping: CatalogAssetMapping) -> bool:
    """Validate normalized receipt integrity before comparing current DB authority."""
    return mapping.evidence_digest == _mapping_digest(
        mapping.target,
        mapping.unit_evidence,
        mapping.admission_digest,
        mapping.verified_at,
        mapping.valid_until,
    )


def _mapping(
    body: bytes, unit: CatalogUnitEvidence, admission: CatalogAssetAdmission, now: datetime
) -> CatalogAssetMapping:
    try:
        target = CatalogAssetTarget.model_validate(
            {**unit.target.model_dump(), "provider_asset_id": _mapped_id(body, unit.target)}
        )
    except ValueError:
        raise CatalogAssetError("asset_identity_or_status") from None
    valid_until = min(admission.valid_until, unit.valid_until)
    return CatalogAssetMapping(
        target=target,
        unit_evidence=unit,
        verified_at=now,
        valid_until=valid_until,
        admission_digest=admission.evidence_digest,
        evidence_digest=_mapping_digest(target, unit, admission.evidence_digest, now, valid_until),
    )


async def stage_catalog_assets(
    http: httpx.AsyncClient,
    targets_with_units: Sequence[CatalogUnitEvidence],
    admission: CatalogAssetAdmission,
    *,
    account: str,
    server: str,
    expected_listings: Mapping[int, CatalogAssetTarget],
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    before_attempt: Callable[[], Awaitable[None]] | None = None,
) -> tuple[CatalogAssetMapping, ...]:
    """Perform one approved batch, with one attempt per selected listing and no retries."""
    now = _now(clock)
    if not _admitted(admission, now, account=account, server=server):
        raise CatalogAssetError("asset_admission")
    if not 1 <= len(targets_with_units) <= admission.request_limit:
        raise CatalogAssetError("asset_request_limit")
    units = tuple(targets_with_units)
    if not _unique_targets(admission.targets) or not _unique_targets(
        [unit.target for unit in units]
    ):
        raise CatalogAssetError("asset_ambiguous_targets")
    for unit in units:
        _check_target(unit, admission, expected_listings, now)

    mappings = []
    for unit in units:
        if before_attempt is not None:
            await before_attempt()
        now = _now(clock)
        if not _admitted(admission, now, account=account, server=server):
            raise CatalogAssetError("asset_admission")
        _check_target(unit, admission, expected_listings, now)
        body = await _read_asset(http, unit.target, admission.environment, now)
        now = _now(clock)
        if not _admitted(admission, now, account=account, server=server):
            raise CatalogAssetError("asset_admission")
        _check_target(unit, admission, expected_listings, now)
        mappings.append(_mapping(body, unit, admission, now))
    if not _unique_targets([entry.target for entry in mappings]):
        raise CatalogAssetError("asset_ambiguous_results")
    if any(entry.valid_until <= now for entry in mappings):
        raise CatalogAssetError("unit_evidence_expired")
    return tuple(mappings)


async def stage_reviewed_assets(
    admission: CatalogAssetAdmission,
    units: Sequence[CatalogUnitEvidence],
    *,
    account: str,
    server: str,
    environment: AssetEnvironment,
    expected_listings: Mapping[int, CatalogAssetTarget],
    key: SecretStr,
    secret: SecretStr,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    transport: httpx.AsyncBaseTransport | None = None,
    before_attempt: Callable[[], Awaitable[None]] | None = None,
) -> tuple[CatalogAssetMapping, ...]:
    """Use the independently configured account's credentials in a dedicated HTTP client."""
    if environment != admission.environment:
        raise CatalogAssetError("asset_admission")
    credentials = {
        "APCA-API-KEY-ID": key.get_secret_value(),
        "APCA-API-SECRET-KEY": secret.get_secret_value(),
    }
    if any(
        not value or any(not 33 <= ord(char) <= 126 for char in value)
        for value in credentials.values()
    ):
        raise CatalogAssetError("asset_credentials")
    async with httpx.AsyncClient(
        trust_env=False, follow_redirects=False, headers=credentials, transport=transport
    ) as http:
        return await stage_catalog_assets(
            http,
            units,
            admission,
            account=account,
            server=server,
            expected_listings=expected_listings,
            clock=clock,
            before_attempt=before_attempt,
        )
