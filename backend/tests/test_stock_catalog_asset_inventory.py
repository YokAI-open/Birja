"""Exercise the operator inventory parser and bounded request contract offline."""

import hashlib
import json
import stat
from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import cast

import httpx
import pytest
from pydantic import SecretStr

from app.services import stock_catalog_asset_inventory as service
from app.services.stock_catalog_provider import AssetEnvironment, CatalogAssetError
from app.services.stock_catalog_sources import ListingExchange

NOW = datetime(2026, 11, 25, 19, 59, tzinfo=UTC)
NYSE_ID = "f6210086-1656-50a4-86d1-08dabeef0001"
NASDAQ_ID = "f6210086-1656-50a4-86d1-08dabeef0002"
KEY, SECRET = SecretStr("synthetic-api-key"), SecretStr("synthetic-secret-key")


def _asset(**overrides: object) -> dict[str, object]:
    return {
        "id": NYSE_ID,
        "symbol": "ORCL",
        "name": "Oracle Corporation",
        "class": "us_equity",
        "status": "active",
        "exchange": "NYSE",
        "tradable": True,
        **overrides,
    }


def _body(*assets: object) -> bytes:
    return json.dumps(assets, ensure_ascii=False).encode()


def _parse(body: bytes) -> service.CatalogAssetInventory:
    return service.parse_catalog_asset_inventory(body, exchange="NYSE", verified_at=NOW)


def test_parse_binds_raw_bytes_and_preserves_untradable_listings():
    row = _asset(tradable=False, attributes=["has_options"])
    body = b" \n" + _body(row)
    snapshot = _parse(body)

    assert snapshot.exchange == "NYSE"
    assert snapshot.verified_at == NOW and snapshot.verified_at.tzinfo is UTC
    assert snapshot.sha256 == hashlib.sha256(body).hexdigest()
    assert snapshot.rows == (
        service.CatalogInventoryAsset(NYSE_ID, "ORCL", "Oracle Corporation", "NYSE", False),
    )
    assert _parse(_body(row)).sha256 != snapshot.sha256


def test_parse_normalizes_a_discretionary_soft_hyphen_in_a_name():
    raw = _body(_asset(name="Oracle Corp\u00adoration"))
    snapshot = _parse(raw)

    assert snapshot.rows[0].name == "Oracle Corporation"
    assert snapshot.sha256 == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize(
    "updates",
    [
        {"id": "not-a-uuid"},
        {"symbol": "ORCL:NYSE"},
        {"name": "  "},
        {"name": "Oracle\nCorporation"},
        {"class": "crypto"},
        {"status": "inactive"},
        {"exchange": "NASDAQ"},
        {"tradable": 1},
        {"tradable": "false"},
    ],
)
def test_parse_refuses_mismatched_or_malformed_identity(updates: dict[str, object]):
    with pytest.raises(CatalogAssetError, match="^asset_inventory_identity_or_status$"):
        _parse(_body(_asset(**updates)))


@pytest.mark.parametrize("duplicate", [_asset(id=NASDAQ_ID), _asset(symbol="ORCL.A")])
def test_parse_refuses_duplicate_symbol_or_provider_uuid(duplicate: dict[str, object]):
    with pytest.raises(CatalogAssetError, match="^asset_inventory_duplicate$"):
        _parse(_body(_asset(), duplicate))


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        (b"[]", "shape"),
        (b"{}", "shape"),
        (b"[null]", "shape"),
        (b'[{"id":"first","id":"second"}]', "json"),
        (b"[NaN]", "json"),
        (b'[{"name":"\xff"}]', "json"),
        (b"[", "json"),
    ],
)
def test_parse_refuses_empty_invalid_or_unexpected_payload(body: bytes, reason: str):
    with pytest.raises(CatalogAssetError, match=f"^asset_inventory_{reason}$"):
        _parse(body)


def test_parse_enforces_byte_and_row_limits(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(service, "MAX_ASSET_INVENTORY_ROWS", 1)
    with pytest.raises(CatalogAssetError, match="^asset_inventory_shape$"):
        _parse(_body(_asset(), _asset(symbol="F", id=NASDAQ_ID)))
    monkeypatch.setattr(service, "MAX_ASSET_INVENTORY_BYTES", 5)
    with pytest.raises(CatalogAssetError, match="^asset_inventory_response_limit$"):
        _parse(_body(_asset()))


@pytest.mark.parametrize(
    ("exchange", "stamp"),
    [
        ("NYSE", NOW.replace(tzinfo=None)),
        ("NYSE", NOW.astimezone(timezone(timedelta(hours=1)))),
        ("OTC", NOW),
    ],
)
def test_parse_refuses_unsupported_scope(exchange: str, stamp: datetime):
    with pytest.raises(CatalogAssetError, match="^asset_inventory_scope$"):
        service.parse_catalog_asset_inventory(
            _body(_asset()), exchange=cast(ListingExchange, exchange), verified_at=stamp
        )


async def _fetch(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    environment: AssetEnvironment = "paper",
    key: SecretStr = KEY,
    secret: SecretStr = SECRET,
) -> tuple[service.CatalogAssetInventory, service.CatalogAssetInventory]:
    return await service.fetch_catalog_asset_inventories(
        environment=environment,
        key=key,
        secret=secret,
        clock=lambda: NOW,
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.parametrize(
    ("environment", "hostname"),
    [("paper", "paper-api.alpaca.markets"), ("live", "api.alpaca.markets")],
)
async def test_fetch_exactly_two_reads_with_credentials_only_at_selected_host(
    environment: AssetEnvironment, hostname: str
):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.scheme == "https" and request.url.host == hostname
        assert request.url.path == "/v2/assets"
        assert request.headers["Accept-Encoding"] == "identity"
        assert request.headers["APCA-API-KEY-ID"] == KEY.get_secret_value()
        assert request.headers["APCA-API-SECRET-KEY"] == SECRET.get_secret_value()
        exchange = request.url.params["exchange"]
        assert dict(request.url.params) == {
            "status": "active",
            "asset_class": "us_equity",
            "exchange": exchange,
        }
        seen.append(exchange)
        row = (
            _asset()
            if exchange == "NYSE"
            else _asset(
                id=NASDAQ_ID,
                symbol="AAPL",
                name="Apple Inc.",
                exchange="NASDAQ",
            )
        )
        return httpx.Response(200, content=_body(row))

    nyse, nasdaq = await _fetch(handler, environment=environment)
    assert seen == ["NYSE", "NASDAQ"]
    assert (nyse.exchange, nyse.rows[0].symbol) == ("NYSE", "ORCL")
    assert (nasdaq.exchange, nasdaq.rows[0].symbol) == ("NASDAQ", "AAPL")


@pytest.mark.parametrize(
    ("code", "headers", "reason"),
    [
        (302, {"Location": "https://example.invalid/redirect"}, "http"),
        (206, {}, "http"),
        (200, {"Content-Range": "bytes 0-100/300"}, "incomplete"),
        (200, {"Link": '<https://api.alpaca.markets/v2/assets?page=2>; rel="next"'}, "incomplete"),
        (200, {"X-Next-Page-Token": "next"}, "incomplete"),
        (200, {"Content-Length": "10"}, "incomplete"),
        (200, {"Content-Length": "-1"}, "incomplete"),
        (200, {"Content-Length": str(service.MAX_ASSET_INVENTORY_BYTES + 1)}, "response_limit"),
        (200, {"Content-Encoding": "gzip"}, "encoding"),
        (429, {"Retry-After": "30"}, "rate_limited"),
    ],
)
async def test_fetch_rejects_unsafe_or_incomplete_responses_without_followup(
    code: int, headers: dict[str, str], reason: str
):
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(code, headers=headers, stream=httpx.ByteStream(_body(_asset())))

    with pytest.raises(CatalogAssetError, match=f"^asset_inventory_{reason}$") as error:
        await _fetch(handler)
    assert attempts == 1
    assert error.value.retry_after == (30 if code == 429 else None)


async def test_fetch_enforces_stream_bound_without_a_declared_content_length(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(service, "MAX_ASSET_INVENTORY_BYTES", 4)

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=httpx.ByteStream(b"[123456]"))

    with pytest.raises(CatalogAssetError, match="^asset_inventory_response_limit$"):
        await _fetch(handler)


@pytest.mark.parametrize(
    "other",
    [_asset(id=NYSE_ID, symbol="AAPL", exchange="NASDAQ"), _asset(id=NASDAQ_ID, exchange="NASDAQ")],
)
async def test_fetch_refuses_cross_exchange_symbol_or_identity_duplicates(other: dict[str, object]):
    def handler(request: httpx.Request) -> httpx.Response:
        asset = _asset() if request.url.params["exchange"] == "NYSE" else other
        return httpx.Response(200, content=_body(asset))

    with pytest.raises(CatalogAssetError, match="^asset_inventory_duplicate$"):
        await _fetch(handler)


async def test_fetch_does_not_retry_timeout():
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("mocked timeout", request=request)

    with pytest.raises(CatalogAssetError, match="^asset_inventory_timeout$"):
        await _fetch(handler)
    assert attempts == 1


@pytest.mark.parametrize("bad_key", ["", "contains whitespace", "invalid\nnewline"])
async def test_fetch_never_requests_with_bad_credentials(bad_key: str):
    def handler(_: httpx.Request) -> httpx.Response:
        pytest.fail("invalid credentials reached HTTP transport")

    with pytest.raises(CatalogAssetError, match="^asset_credentials$"):
        await _fetch(handler, key=SecretStr(bad_key))


@pytest.fixture
def capture_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STOCK_DATA_ACCOUNT", "synthetic-account")
    monkeypatch.setenv("STOCK_DATA_SERVER", "synthetic-server")
    monkeypatch.setenv("ALPACA_ASSET_ENVIRONMENT", "paper")
    monkeypatch.setenv("ALPACA_API_KEY", KEY.get_secret_value())
    monkeypatch.setenv("ALPACA_SECRET_KEY", SECRET.get_secret_value())


async def test_private_capture_retains_exact_bytes_and_enrollment_receipts(
    tmp_path: Path, capture_environment: None
) -> None:
    replies = {
        "NYSE": b"\n  " + _body(_asset()),
        "NASDAQ": _body(_asset(id=NASDAQ_ID, symbol="AAPL", exchange="NASDAQ")) + b"\n",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "paper-api.alpaca.markets"
        assert request.headers["APCA-API-SECRET-KEY"] == SECRET.get_secret_value()
        return httpx.Response(200, content=replies[request.url.params["exchange"]])

    output = tmp_path / "capture"
    counts = await service._capture(
        output, clock=lambda: NOW, transport=httpx.MockTransport(handler)
    )
    assert counts == {"NYSE": 1, "NASDAQ": 1}
    assert stat.S_IMODE(output.stat().st_mode) == 0o700
    receipt_path = output / "inventories.json"
    receipt = json.loads(receipt_path.read_bytes())
    assert stat.S_IMODE(receipt_path.stat().st_mode) == 0o600
    for exchange, body in replies.items():
        saved = output / f"{exchange.lower()}.json"
        assert saved.read_bytes() == body
        assert stat.S_IMODE(saved.stat().st_mode) == 0o600
        assert receipt[exchange] == {
            "verified_at": NOW.isoformat(),
            "sha256": hashlib.sha256(body).hexdigest(),
        }


async def test_capture_refuses_existing_target_before_a_request(
    tmp_path: Path, capture_environment: None
) -> None:
    output = tmp_path / "capture"
    output.mkdir()
    existing = output / "keep"
    existing.write_text("existing capture")

    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail("an existing target used provider allowance")

    with pytest.raises(FileExistsError):
        await service._capture(output, transport=httpx.MockTransport(handler))
    assert list(output.iterdir()) == [existing]
    assert existing.read_text() == "existing capture"


async def test_capture_second_venue_failure_leaves_no_usable_capture(
    tmp_path: Path, capture_environment: None
) -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        exchange = request.url.params["exchange"]
        requests.append(exchange)
        return httpx.Response(200, content=_body(_asset()) if exchange == "NYSE" else b"[]")

    output = tmp_path / "capture"
    with pytest.raises(CatalogAssetError, match="^asset_inventory_shape$"):
        await service._capture(output, transport=httpx.MockTransport(handler))
    assert requests == ["NYSE", "NASDAQ"]
    assert not output.exists()


def test_capture_cli_invalid_scope_is_sanitized(
    capture_environment: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("ALPACA_ASSET_ENVIRONMENT", "unsupported")
    assert service.main(["--output", str(tmp_path / "capture")]) == 2
    out, err = capsys.readouterr()
    assert not out
    assert json.loads(err) == {"disposition": "refused", "reason": "asset_inventory_scope"}
    assert not list(tmp_path.iterdir())
