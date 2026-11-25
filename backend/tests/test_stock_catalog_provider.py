import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Literal

import httpx
import pytest
from pydantic import SecretStr, ValidationError

from app.services.stock_catalog_provider import (
    CatalogAssetAdmission,
    CatalogAssetError,
    CatalogAssetMapping,
    CatalogAssetTarget,
    CatalogUnitEvidence,
    mapping_evidence_matches,
    stage_catalog_assets,
    stage_reviewed_assets,
)

NOW = datetime(2026, 11, 24, 15, tzinfo=UTC)
NYSE_ID = "10000000-1234-4567-b89a-000000000001"
NASDAQ_ID = "10000000-1234-4567-b89a-000000000002"
NYSE = CatalogAssetTarget(
    catalog_id=1, listing_version=11, listing_exchange="NYSE", provider_symbol="BRK.B"
)
NASDAQ = CatalogAssetTarget(
    catalog_id=2,
    listing_version=12,
    listing_exchange="NASDAQ",
    provider_symbol="EXPG",
    provider_asset_id=NASDAQ_ID,
)
PURPOSES = frozenset({"collection", "internal_use", "derived_use", "display", "storage", "backup"})


def _admission(
    *targets: CatalogAssetTarget, environment: Literal["paper", "live"] = "paper"
) -> CatalogAssetAdmission:
    return CatalogAssetAdmission(
        account="fixture-account",
        server="fixture-server",
        environment=environment,
        reviewed_at=NOW - timedelta(hours=1),
        valid_until=NOW + timedelta(hours=1),
        evidence_digest="a" * 64,
        targets=targets,
        purposes=PURPOSES,
        request_limit=len(targets),
    )


def _unit(target: CatalogAssetTarget) -> CatalogUnitEvidence:
    return CatalogUnitEvidence(
        target=target,
        currency="USD",
        units_per_share=1,
        classification="common_stock" if target.listing_exchange == "NYSE" else "ordinary_shares",
        reviewed_at=NOW - timedelta(hours=2),
        valid_until=NOW + timedelta(minutes=30),
        evidence_digest="b" * 64,
    )


def _response(target: CatalogAssetTarget, **changes: object) -> dict[str, object]:
    return {
        "id": target.provider_asset_id or NYSE_ID,
        "class": "us_equity",
        "status": "active",
        "exchange": target.listing_exchange,
        "symbol": target.provider_symbol,
        "name": "Unused fixture provider field",
        "tradable": False,
        "currency": "unused fixture field",
        **changes,
    }


async def test_mapping_stages_both_venues_without_retaining_provider_fields() -> None:
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, str(request.url)))
        assert request.headers["Accept-Encoding"] == "identity"
        return httpx.Response(200, json=_response(NYSE if len(calls) == 1 else NASDAQ))

    units = (_unit(NYSE), _unit(NASDAQ))
    admission = _admission(NYSE, NASDAQ)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        mappings = await stage_catalog_assets(
            client,
            units,
            admission,
            account="fixture-account",
            server="fixture-server",
            expected_listings={1: NYSE, 2: NASDAQ},
            clock=lambda: NOW,
        )
    assert calls == [
        ("GET", "https://paper-api.alpaca.markets/v2/assets/BRK.B"),
        ("GET", f"https://paper-api.alpaca.markets/v2/assets/{NASDAQ_ID}"),
    ]
    assert [mapping.target.provider_asset_id for mapping in mappings] == [NYSE_ID, NASDAQ_ID]
    assert [mapping.target.listing_version for mapping in mappings] == [11, 12]
    assert [mapping.unit_evidence for mapping in mappings] == list(units)
    assert all(mapping.admission_digest == admission.evidence_digest for mapping in mappings)
    assert all(mapping.valid_until == units[0].valid_until for mapping in mappings)
    assert all(mapping.verified_at == NOW for mapping in mappings)
    assert mappings[0].evidence_digest != mappings[1].evidence_digest
    for mapping in mappings:
        staged_json = mapping.model_dump_json()
        assert "fixture provider field" not in staged_json
        assert "tradable" not in staged_json
        restored = CatalogAssetMapping.model_validate_json(staged_json)
        assert restored == mapping
        assert mapping_evidence_matches(restored)
        assert not mapping_evidence_matches(
            restored.model_copy(update={"valid_until": NOW + timedelta(days=1)})
        )


async def test_claim_change_between_assets_stops_the_second_request() -> None:
    calls: list[str] = []
    checks = 0

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(200, json=_response(NYSE))

    async def verify_claim() -> None:
        nonlocal checks
        checks += 1
        if calls:
            raise CatalogAssetError("asset_admission")

    with pytest.raises(CatalogAssetError, match="asset_admission"):
        await stage_reviewed_assets(
            _admission(NYSE, NASDAQ),
            (_unit(NYSE), _unit(NASDAQ)),
            account="fixture-account",
            server="fixture-server",
            environment="paper",
            expected_listings={1: NYSE, 2: NASDAQ},
            key=SecretStr("synthetic-key"),
            secret=SecretStr("synthetic-secret"),
            clock=lambda: NOW,
            transport=httpx.MockTransport(respond),
            before_attempt=verify_claim,
        )
    assert checks == 2
    assert calls == ["/v2/assets/BRK.B"]


async def test_mapping_uses_only_matching_configured_environment_for_credentials() -> None:
    calls: list[str] = []
    key, secret = SecretStr("fixture-key"), SecretStr("fixture-secret")

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.host)
        assert request.headers["APCA-API-KEY-ID"] == key.get_secret_value()
        assert request.headers["APCA-API-SECRET-KEY"] == secret.get_secret_value()
        return httpx.Response(200, json=_response(NYSE))

    with pytest.raises(CatalogAssetError, match="^asset_admission$"):
        await stage_reviewed_assets(
            _admission(NYSE),
            (_unit(NYSE),),
            account="fixture-account",
            server="fixture-server",
            environment="live",
            expected_listings={1: NYSE},
            key=key,
            secret=secret,
            clock=lambda: NOW,
            transport=httpx.MockTransport(handler),
        )
    assert calls == []

    (mapping,) = await stage_reviewed_assets(
        _admission(NYSE),
        (_unit(NYSE),),
        account="fixture-account",
        server="fixture-server",
        environment="paper",
        expected_listings={1: NYSE},
        key=key,
        secret=secret,
        clock=lambda: NOW,
        transport=httpx.MockTransport(handler),
    )
    assert calls == ["paper-api.alpaca.markets"]
    assert mapping.target.provider_asset_id == NYSE_ID
    assert "fixture-key" not in mapping.model_dump_json()
    assert "fixture-secret" not in mapping.model_dump_json()


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("account", "asset_admission"),
        ("server", "asset_admission"),
        ("expired_admission", "asset_admission"),
        ("missing_backup", "asset_admission"),
        ("stale_version", "listing_version_or_scope"),
        ("wrong_spelling", "listing_version_or_scope"),
        ("expired_unit", "unit_evidence_expired"),
        ("duplicate", "asset_ambiguous_targets"),
        ("request_cap", "asset_request_limit"),
    ],
)
async def test_mapping_refuses_unapproved_batch_before_first_call(case: str, reason: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid batch made an outbound request")

    account = "unapproved-account" if case == "account" else "fixture-account"
    server = "unapproved-server" if case == "server" else "fixture-server"
    admission = _admission(NYSE, NASDAQ)
    unit = _unit(NASDAQ)
    expected = {1: NYSE, 2: NASDAQ}
    if case == "expired_admission":
        admission = admission.model_copy(update={"valid_until": NOW})
    elif case == "missing_backup":
        admission = admission.model_copy(update={"purposes": PURPOSES - {"backup"}})
    elif case == "expired_unit":
        unit = unit.model_copy(update={"valid_until": NOW})
    elif case == "stale_version":
        expected[2] = NASDAQ.model_copy(update={"listing_version": 13})
    elif case == "wrong_spelling":
        expected[2] = NASDAQ.model_copy(update={"provider_symbol": "EXPG.A"})
    elif case == "duplicate":
        unit = _unit(NYSE)
    elif case == "request_cap":
        admission = admission.model_copy(update={"request_limit": 1})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CatalogAssetError, match=f"^{reason}$"):
            await stage_catalog_assets(
                client,
                (_unit(NYSE), unit),
                admission,
                account=account,
                server=server,
                expected_listings=expected,
                clock=lambda: NOW,
            )


@pytest.mark.parametrize(
    "change", [{"currency": "EUR"}, {"classification": "out_of_scope"}, {"units_per_share": 2}]
)
def test_mapping_requires_reviewed_usd_common_share_units(change: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        CatalogUnitEvidence.model_validate({**dict(_unit(NYSE)), **change})


@pytest.mark.parametrize(
    "change",
    [
        {"class": "us_option"},
        {"exchange": "NYSE"},
        {"id": NYSE_ID},
        {"status": "inactive"},
        {"symbol": "expg"},
        {"symbol": "EXPG.A"},
    ],
)
async def test_mapping_rejects_mismatched_provider_identity(change: dict[str, object]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.alpaca.markets"
        return httpx.Response(200, json=_response(NASDAQ, **change))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CatalogAssetError, match="^asset_identity_or_status$"):
            await stage_catalog_assets(
                client,
                (_unit(NASDAQ),),
                _admission(NASDAQ, environment="live"),
                account="fixture-account",
                server="fixture-server",
                expected_listings={2: NASDAQ},
                clock=lambda: NOW,
            )


@pytest.mark.parametrize(
    ("response", "reason", "retry_after"),
    [
        (httpx.Response(429, headers={"Retry-After": "53"}), "asset_rate_limited", 53),
        (
            httpx.Response(429, headers={"Retry-After": "Tue, 24 Nov 2026 15:00:29 GMT"}),
            "asset_rate_limited",
            29,
        ),
        (
            httpx.Response(302, headers={"Location": "https://example.test/asset"}),
            "asset_http",
            None,
        ),
        (httpx.Response(404), "asset_missing", None),
        (httpx.Response(200, content=b" " * 32_769), "asset_response_limit", None),
        (httpx.Response(200, content=b'{"symbol":"BRK.B","symbol":"BRK.B"}'), "asset_json", None),
        (httpx.Response(200, content=json.dumps([_response(NYSE)])), "asset_shape", None),
    ],
)
async def test_mapping_stops_after_first_refusal_and_reports_safe_reason(
    response: httpx.Response, reason: str, retry_after: int | None
) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return response

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), follow_redirects=True
    ) as client:
        with pytest.raises(CatalogAssetError, match=f"^{reason}$") as exc_info:
            await stage_catalog_assets(
                client,
                (_unit(NYSE), _unit(NASDAQ)),
                _admission(NYSE, NASDAQ),
                account="fixture-account",
                server="fixture-server",
                expected_listings={1: NYSE, 2: NASDAQ},
                clock=lambda: NOW,
            )
    assert len(calls) == 1
    assert exc_info.value.retry_after == retry_after


async def test_mapping_rechecks_expiry_on_response_boundary() -> None:
    calls: list[httpx.Request] = []
    admission = _admission(NYSE, NASDAQ).model_copy(
        update={"valid_until": NOW + timedelta(seconds=1)}
    )
    readings: Iterator[datetime] = iter((NOW, NOW, NOW + timedelta(seconds=1)))

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=_response(NYSE))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CatalogAssetError, match="^asset_admission$"):
            await stage_catalog_assets(
                client,
                (_unit(NYSE), _unit(NASDAQ)),
                admission,
                account="fixture-account",
                server="fixture-server",
                expected_listings={1: NYSE, 2: NASDAQ},
                clock=lambda: next(readings),
            )
    assert len(calls) == 1
