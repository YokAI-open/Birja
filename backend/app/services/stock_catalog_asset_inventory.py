"""Bounded Alpaca asset inventories for reviewed catalog reconciliation."""

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
from collections.abc import Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from pydantic import SecretStr

from app.services.stock_catalog_provider import (
    _ASSET_ID,
    _ASSET_ROOTS,
    _DEADLINE,
    AssetEnvironment,
    CatalogAssetError,
    _now,
    _reject_constant,
    _reject_duplicates,
    _retry_after,
)
from app.services.stock_catalog_sources import SYMBOL_PATTERN, ListingExchange

MAX_ASSET_INVENTORY_BYTES = 8 * 1024 * 1024
MAX_ASSET_INVENTORY_ROWS = 20_000
_EXCHANGES: tuple[ListingExchange, ListingExchange] = ("NYSE", "NASDAQ")


@dataclass(frozen=True, slots=True)
class CatalogInventoryAsset:
    provider_asset_id: str
    symbol: str
    name: str
    exchange: ListingExchange
    tradable: bool


@dataclass(frozen=True, slots=True)
class CatalogAssetInventory:
    exchange: ListingExchange
    verified_at: datetime
    sha256: str
    rows: tuple[CatalogInventoryAsset, ...]


@dataclass(frozen=True, slots=True, repr=False)
class _RawInventory:
    body: bytes
    parsed: CatalogAssetInventory


def parse_catalog_asset_inventory(
    body: bytes, *, exchange: ListingExchange, verified_at: datetime
) -> CatalogAssetInventory:
    """Validate and bind exact private response bytes to one venue.

    The endpoint's universe includes other asset types. A successfully parsed
    response still needs completeness and share-class reconciliation.
    """
    if exchange not in _EXCHANGES or verified_at.utcoffset() != timedelta(0):
        raise CatalogAssetError("asset_inventory_scope")
    if len(body) > MAX_ASSET_INVENTORY_BYTES:
        raise CatalogAssetError("asset_inventory_response_limit")
    try:
        assets = json.loads(
            body.decode("utf-8"),
            object_pairs_hook=_reject_duplicates,
            parse_constant=_reject_constant,
        )
    except ValueError, RecursionError:
        raise CatalogAssetError("asset_inventory_json") from None
    if not isinstance(assets, list) or not 1 <= len(assets) <= MAX_ASSET_INVENTORY_ROWS:
        raise CatalogAssetError("asset_inventory_shape")

    rows: list[CatalogInventoryAsset] = []
    symbols: set[str] = set()
    provider_ids: set[str] = set()
    for asset in assets:
        if not isinstance(asset, dict):
            raise CatalogAssetError("asset_inventory_shape")
        provider_id, symbol = asset.get("id"), asset.get("symbol")
        name, tradable = asset.get("name"), asset.get("tradable")
        if isinstance(name, str):
            # Alpaca can include discretionary soft hyphens in security names.
            name = name.replace("\u00ad", "").strip()
        if (
            asset.get("class") != "us_equity"
            or asset.get("status") != "active"
            or asset.get("exchange") != exchange
            or not isinstance(provider_id, str)
            or re.fullmatch(_ASSET_ID, provider_id) is None
            or not isinstance(symbol, str)
            or re.fullmatch(SYMBOL_PATTERN, symbol) is None
            or not isinstance(name, str)
            or not name
            or len(name) > 255
            or not name.isprintable()
            or not isinstance(tradable, bool)
        ):
            raise CatalogAssetError("asset_inventory_identity_or_status")
        if symbol in symbols or provider_id in provider_ids:
            raise CatalogAssetError("asset_inventory_duplicate")
        symbols.add(symbol)
        provider_ids.add(provider_id)
        rows.append(CatalogInventoryAsset(provider_id, symbol, name, exchange, tradable))

    return CatalogAssetInventory(
        exchange, verified_at.astimezone(UTC), hashlib.sha256(body).hexdigest(), tuple(rows)
    )


async def _read_inventory(
    http: httpx.AsyncClient,
    environment: AssetEnvironment,
    exchange: ListingExchange,
    now: datetime,
) -> bytes:
    try:
        async with (
            asyncio.timeout(_DEADLINE),
            http.stream(
                "GET",
                f"{_ASSET_ROOTS[environment]}/v2/assets",
                params={"status": "active", "asset_class": "us_equity", "exchange": exchange},
                headers={"Accept": "application/json", "Accept-Encoding": "identity"},
            ) as response,
        ):
            if response.status_code == 429:
                raise CatalogAssetError(
                    "asset_inventory_rate_limited",
                    retry_after=_retry_after(response.headers.get("Retry-After"), now),
                )
            if response.status_code != 200:
                raise CatalogAssetError("asset_inventory_http")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise CatalogAssetError("asset_inventory_encoding")
            if any(header in response.headers for header in ("Content-Range", "Link")):
                raise CatalogAssetError("asset_inventory_incomplete")
            if response.headers.get("X-Next-Page-Token"):
                raise CatalogAssetError("asset_inventory_incomplete")

            declared_length = response.headers.get("Content-Length")
            if declared_length is not None:
                if re.fullmatch(r"[0-9]{1,8}", declared_length) is None:
                    raise CatalogAssetError("asset_inventory_incomplete")
                if int(declared_length) > MAX_ASSET_INVENTORY_BYTES:
                    raise CatalogAssetError("asset_inventory_response_limit")
            body = bytearray()
            async for part in response.aiter_bytes():
                if len(body) + len(part) > MAX_ASSET_INVENTORY_BYTES:
                    raise CatalogAssetError("asset_inventory_response_limit")
                body.extend(part)
            if declared_length is not None and len(body) != int(declared_length):
                raise CatalogAssetError("asset_inventory_incomplete")
            return bytes(body)
    except TimeoutError, httpx.TimeoutException:
        raise CatalogAssetError("asset_inventory_timeout") from None
    except httpx.HTTPError:
        raise CatalogAssetError("asset_inventory_transport") from None


async def _fetch_catalog_asset_inventories(
    *,
    environment: AssetEnvironment,
    key: SecretStr,
    secret: SecretStr,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[_RawInventory, _RawInventory]:
    if environment not in _ASSET_ROOTS:
        raise CatalogAssetError("asset_inventory_scope")
    credentials = {
        "APCA-API-KEY-ID": key.get_secret_value(),
        "APCA-API-SECRET-KEY": secret.get_secret_value(),
    }
    if any(
        not value or any(not 33 <= ord(char) <= 126 for char in value)
        for value in credentials.values()
    ):
        raise CatalogAssetError("asset_credentials")

    inventories = []
    async with httpx.AsyncClient(
        trust_env=False,
        follow_redirects=False,
        timeout=_DEADLINE,
        headers=credentials,
        transport=transport,
    ) as http:
        for exchange in _EXCHANGES:
            body = await _read_inventory(http, environment, exchange, _now(clock))
            inventories.append(
                _RawInventory(
                    body,
                    parse_catalog_asset_inventory(body, exchange=exchange, verified_at=_now(clock)),
                )
            )

    nyse, nasdaq = inventories
    if {row.symbol for row in nyse.parsed.rows} & {row.symbol for row in nasdaq.parsed.rows} or {
        row.provider_asset_id for row in nyse.parsed.rows
    } & {row.provider_asset_id for row in nasdaq.parsed.rows}:
        raise CatalogAssetError("asset_inventory_duplicate")
    return nyse, nasdaq


async def fetch_catalog_asset_inventories(
    *,
    environment: AssetEnvironment,
    key: SecretStr,
    secret: SecretStr,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[CatalogAssetInventory, CatalogAssetInventory]:
    """Fetch NYSE and Nasdaq once each using a dedicated scoped Alpaca client."""
    nyse, nasdaq = await _fetch_catalog_asset_inventories(
        environment=environment, key=key, secret=secret, clock=clock, transport=transport
    )
    return nyse.parsed, nasdaq.parsed


def _write_private(directory: int, name: str, contents: bytes) -> None:
    descriptor = os.open(
        name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory
    )
    with os.fdopen(descriptor, "wb") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(contents)
        stream.flush()
        os.fsync(stream.fileno())


async def _capture(
    output: Path,
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, int]:
    environment = os.environ.get("ALPACA_ASSET_ENVIRONMENT")
    if environment not in ("paper", "live") or any(
        not value or len(value) > 128 or value != value.strip() or not value.isprintable()
        for value in (
            os.environ.get("STOCK_DATA_ACCOUNT", ""),
            os.environ.get("STOCK_DATA_SERVER", ""),
        )
    ):
        raise CatalogAssetError("asset_inventory_scope")
    key = SecretStr(os.environ.get("ALPACA_API_KEY", ""))
    secret = SecretStr(os.environ.get("ALPACA_SECRET_KEY", ""))

    # Reserve a new private directory before using the provider allowance.
    os.mkdir(output, 0o700)
    directory = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fchmod(directory, 0o700)
        mode: AssetEnvironment = "paper" if environment == "paper" else "live"
        nyse, nasdaq = await _fetch_catalog_asset_inventories(
            environment=mode, key=key, secret=secret, clock=clock, transport=transport
        )
        receipt = {
            record.parsed.exchange: {
                "sha256": record.parsed.sha256,
                "verified_at": record.parsed.verified_at.isoformat(),
            }
            for record in (nyse, nasdaq)
        }
        _write_private(directory, "nyse.json", nyse.body)
        _write_private(directory, "nasdaq.json", nasdaq.body)
        _write_private(directory, "inventories.json", json.dumps(receipt, sort_keys=True).encode())
        os.fsync(directory)
        return {record.parsed.exchange: len(record.parsed.rows) for record in (nyse, nasdaq)}
    except BaseException:
        for name in ("inventories.json", "nasdaq.json", "nyse.json"):
            with suppress(FileNotFoundError):
                os.unlink(name, dir_fd=directory)
        os.rmdir(output)
        raise
    finally:
        os.close(directory)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Capture reviewed Alpaca inventories using the private operator environment."
    )
    parser.add_argument(
        "--output", required=True, type=Path, help="new private directory for both raw inventories"
    )
    args = parser.parse_args(argv)
    try:
        counts = asyncio.run(_capture(args.output))
    except CatalogAssetError as exc:
        print(json.dumps({"disposition": "refused", "reason": exc.reason}), file=sys.stderr)
        return 2
    except OSError:
        print(json.dumps({"disposition": "refused", "reason": "private_output"}), file=sys.stderr)
        return 2
    print(json.dumps({"disposition": "captured", "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
