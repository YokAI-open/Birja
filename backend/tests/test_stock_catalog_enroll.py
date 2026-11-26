"""Offline coverage of bulk enrollment and the authenticated disposable migrator."""

import hashlib
import json
from collections import Counter
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import func, select

from app.models.corporate_action import StockActionState
from app.models.stock_catalog import StockCatalogAdmission, StockCatalogListing
from app.models.stock_catalog_finance import StockCatalogInstrument
from app.services.stock_catalog_publish import CatalogPublishError
from app.services.stock_catalog_quotes import _MAPPING_FIELDS, _MAPPING_PURPOSES
from app.tasks.stock_catalog_enroll import _execute_batch, _inputs, _validate_inputs
from app.tasks.stock_catalog_import import _FINANCIAL_FIELDS
from tests.test_stock_catalog_finance_migration import finance_0025 as finance_0025
from tests.test_stock_catalog_promotion import finance_0026 as finance_0026
from tests.test_stock_catalog_publish import NOW, SECOND, Factory, _manifest, _publish, _rights

ACCOUNT = "bulk-test-account"
SERVER = "bulk-test-server"


@pytest.fixture(autouse=True)
def provider_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STOCK_DATA_ACCOUNT", ACCOUNT)
    monkeypatch.setenv("STOCK_DATA_SERVER", SERVER)
    monkeypatch.setenv("ALPACA_ASSET_ENVIRONMENT", "paper")


def _private(path: Path, body: bytes) -> None:
    path.write_bytes(body)
    path.chmod(0o600)


def _scope(generation: int, manifest_digest: str) -> dict[str, Any]:
    reviewed = (NOW - timedelta(hours=1)).isoformat()
    expires_at = NOW + timedelta(hours=5)
    expires = expires_at.isoformat()

    def evidence(fields: dict[str, list[str]]) -> dict[str, Any]:
        return {
            "reference": "Synthetic explicitly reviewed scope and retention",
            "reviewed_at": reviewed,
            "valid_until": expires,
            "fields": fields,
        }

    limits = {"requests_per_minute": 180, "max_response_bytes": 4096, "symbols_per_request": 8}
    return {
        "version": 1,
        "generation_id": generation,
        "manifest_sha256": manifest_digest,
        "account": ACCOUNT,
        "server": SERVER,
        "environment": "paper",
        "assets": evidence({field: sorted(_MAPPING_PURPOSES) for field in _MAPPING_FIELDS}),
        "units": {
            "reference": "Synthetic USD single whole-share unit review",
            "reviewed_at": reviewed,
            "valid_until": expires,
            "currency": "USD",
            "units_per_share": 1,
        },
        "execution": evidence(_FINANCIAL_FIELDS["catalog_execution"]),
        "mark": evidence(_FINANCIAL_FIELDS["catalog_mark"]),
        "halt": evidence(_FINANCIAL_FIELDS["catalog_halt"]),
        "actions": evidence(_FINANCIAL_FIELDS["catalog_actions"]),
        "execution_limits": limits,
        "mark_limits": limits,
        "halt_limits": limits,
        "action_policy": {
            **limits,
            "all_us_replay_ingress": True,
            "replay_region": "us",
            "known_id_recheck": True,
            "history_start": "2026-11-23",
            "future_through": (expires_at.date() + timedelta(days=90)).isoformat(),
            "mutation_start": reviewed,
        },
    }


def _asset(exchange: str, symbol: str, number: int, *, tradable: bool = True) -> dict[str, Any]:
    return {
        "id": f"31000000-1234-4567-b89a-{number:012d}",
        "class": "us_equity",
        "exchange": exchange,
        "symbol": symbol,
        "name": f"Synthetic issue {symbol}",
        "status": "active",
        "tradable": tradable,
    }


def _files(
    path: Path, generation: int = 1, manifest_sha256: str = "a" * 64, *, duplicate: bool = False
) -> tuple[dict[str, Any], tuple[Path, Path, Path]]:
    packet = _scope(generation, manifest_sha256)
    scope, nyse, nasdaq = (path / name for name in ("scope.json", "nyse.json", "nasdaq.json"))
    rows = {
        "NYSE": [_asset("NYSE", "FQN", 1)],
        "NASDAQ": [
            _asset("NASDAQ", "FQA", 1 if duplicate else 2),
            _asset("NASDAQ", "AAPL", 3),
            _asset("NASDAQ", "FQB", 4, tradable=False),
        ],
    }
    packet["inventories"] = {}
    for exchange, file in (("NYSE", nyse), ("NASDAQ", nasdaq)):
        body = json.dumps(rows[exchange]).encode()
        _private(file, body)
        packet["inventories"][exchange] = {
            "sha256": hashlib.sha256(body).hexdigest(),
            "verified_at": (NOW - timedelta(minutes=10)).isoformat(),
        }
    _private(scope, json.dumps(packet).encode())
    return packet, (scope, nyse, nasdaq)


def test_private_scope_binds_both_hashes_and_exact_scope_bytes(tmp_path: Path) -> None:
    _, files = _files(tmp_path)
    scope, nyse, _ = files
    first = _inputs(*files)
    _validate_inputs(first, NOW)
    assert len(first.assets) == 4
    scope.write_bytes(scope.read_bytes() + b"\n")
    assert _inputs(*files).digest != first.digest
    nyse.write_bytes(nyse.read_bytes() + b"\n")
    with pytest.raises(CatalogPublishError, match="SHA-256"):
        _inputs(*files)


def test_private_scope_limits_and_rejects_symlinks(tmp_path: Path) -> None:
    _, files = _files(tmp_path)
    scope, nyse, nasdaq = files
    scope.chmod(0o644)
    with pytest.raises(CatalogPublishError, match="mode-0600"):
        _inputs(*files)
    scope.chmod(0o600)
    link = tmp_path / "link"
    link.symlink_to(nyse)
    with pytest.raises(OSError):
        _inputs(scope, link, nasdaq)


def test_duplicate_asset_across_exchanges_refused(tmp_path: Path) -> None:
    _, files = _files(tmp_path, duplicate=True)
    with pytest.raises(CatalogPublishError, match="across exchanges"):
        _inputs(*files)


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"account": "different"}, "account or server"),
        ({"environment": "live"}, "environment"),
        ({"mark": {"fields": {}}}, "field purposes"),
        ({"units": {"reviewed_at": NOW.isoformat()}}, "evidence is not current"),
        (
            {"actions": {"valid_until": NOW.isoformat()}},
            "UTC validity",
        ),
        ({"inventories": {"NYSE": {"verified_at": SECOND.isoformat()}}}, "evidence is not current"),
    ],
)
def test_scope_refuses_missing_or_wrong_authority(
    tmp_path: Path, change: dict[str, Any], reason: str
) -> None:
    packet, files = _files(tmp_path)
    for name, value in change.items():
        if name == "inventories":
            packet[name]["NYSE"].update(value["NYSE"])
        elif isinstance(value, dict):
            packet[name].update(value)
        else:
            packet[name] = value
    _private(files[0], json.dumps(packet).encode())
    with pytest.raises(CatalogPublishError, match=reason):
        _validate_inputs(_inputs(*files), NOW)


def test_action_horizon_covers_the_full_scope_validity(tmp_path: Path) -> None:
    packet, files = _files(tmp_path)
    packet["actions"]["valid_until"] = (NOW + timedelta(days=3)).isoformat()
    _private(files[0], json.dumps(packet).encode())
    with pytest.raises(CatalogPublishError, match="through grant expiry"):
        _validate_inputs(_inputs(*files), NOW)

    packet["action_policy"]["future_through"] = (NOW.date() + timedelta(days=93)).isoformat()
    _private(files[0], json.dumps(packet).encode())
    _validate_inputs(_inputs(*files), NOW)


def test_action_horizon_uses_the_runtime_setting_validator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, files = _files(tmp_path)
    monkeypatch.setenv("STOCK_ACTIONS_FUTURE_DAYS", "90")
    _validate_inputs(_inputs(*files), NOW)
    monkeypatch.setenv("STOCK_ACTIONS_FUTURE_DAYS", "89")
    with pytest.raises(CatalogPublishError, match="Invalid configured stock-action lookahead"):
        _validate_inputs(_inputs(*files), NOW)


async def test_locked_review_apply_retry_and_renew_preserve_journal(
    finance_0026: Factory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rights = _rights()
    async with finance_0026.begin() as db:
        db.add_all(
            StockCatalogAdmission(**right.model_dump(), scope={}, is_fixture=False)
            for right in rights
        )
    manifest = _manifest(
        nasdaq=(
            ("FQA", "fixture-nasdaq"),
            ("AAPL", "fixture-legacy"),
            ("FQB", "fixture-not-tradable"),
            ("FQC", "fixture-missing"),
        ),
        rights=rights,
    )
    published = await _publish(finance_0026, manifest, None)
    packet, files = _files(tmp_path, published.generation_id, published.digest)
    inputs = _inputs(*files)

    seen: Counter[str] = Counter()
    after = 0
    while True:
        async with finance_0026.begin() as db:
            with pytest.raises(CatalogPublishError, match="cursor or size"):
                await _execute_batch(db, inputs, now=NOW, after=after, limit=101)
            reviewed = await _execute_batch(db, inputs, now=NOW, after=after, limit=2)
        async with finance_0026.begin() as db:
            with pytest.raises(CatalogPublishError, match="exact reviewed bulk batch"):
                await _execute_batch(db, inputs, now=NOW, after=after, limit=2, expected_sha="x")
            applied = await _execute_batch(
                db, inputs, now=NOW, after=after, limit=2, expected_sha=reviewed["batch_sha256"]
            )
        assert applied["disposition"] == "applied"
        seen.update(applied["outcomes"])
        if reviewed["next_after_listing"] is None:
            break
        after = reviewed["next_after_listing"]
    assert seen == {"legacy": 1, "enroll": 2, "asset_not_tradable": 1, "asset_missing": 1}

    async with finance_0026.begin() as db:
        replay = await _execute_batch(db, inputs, now=NOW, after=0, limit=100)
        assert replay["outcomes"]["already_enrolled"] == 2
        bindings = (await db.scalars(select(StockCatalogInstrument))).all()
        assert len(bindings) == 2
        old = {row.catalog_id: (row.coin_id, row.admission_id, row.promoted_at) for row in bindings}
        for binding in bindings:
            listing = await db.get(StockCatalogListing, binding.listing_id)
            assert listing is not None
            assert listing.provider_verified_at == NOW - timedelta(minutes=10)
            state = await db.get(StockActionState, binding.coin_id)
            assert state is not None
            state.journal_start_at = NOW + timedelta(minutes=1)
        execution = await db.get(StockCatalogAdmission, bindings[0].admission_id)
        assert execution is not None
        unrelated = [
            StockCatalogAdmission(
                artifact=execution.artifact,
                reference="bulk-alpaca-assets-v1:other reviewed scope",
                reviewed_at=execution.reviewed_at,
                valid_until=execution.valid_until,
                fields=execution.fields,
                scope={**execution.scope, key: value},
                is_fixture=False,
            )
            for key, value in (
                ("account", "different-account"),
                ("server", "different-server"),
                ("provider_asset_id", _asset("NYSE", "FQZ", 88)["id"]),
            )
        ]
        db.add_all(unrelated)
        await db.flush()
        unrelated_ids = [grant.id for grant in unrelated]

    packet["replace_bulk_grants"] = True
    packet["execution"]["reference"] += " (renewed)"
    _private(files[0], json.dumps(packet).encode())
    renewal = _inputs(*files)
    async with finance_0026.begin() as db:
        reviewed = await _execute_batch(db, renewal, now=SECOND, after=0, limit=100)
        assert reviewed["outcomes"]["renew"] == 2
        await _execute_batch(
            db, renewal, now=SECOND, after=0, limit=100, expected_sha=reviewed["batch_sha256"]
        )
    async with finance_0026.begin() as db:
        retried = await _execute_batch(db, inputs, now=SECOND, after=0, limit=100)
        assert retried["outcomes"]["revoked_bulk_scope"] == 2
        for binding in await db.scalars(select(StockCatalogInstrument)):
            old_coin, old_grant, original_promotion = old[binding.catalog_id]
            state = await db.get(StockActionState, binding.coin_id)
            assert state is not None
            assert state.journal_start_at == NOW + timedelta(minutes=1)
            assert binding.coin_id == old_coin and binding.promoted_at == original_promotion
            assert binding.admission_id != old_grant
        for admission_id in unrelated_ids:
            grant = await db.get(StockCatalogAdmission, admission_id)
            assert grant is not None and grant.revoked_at is None
        assert (
            await db.scalar(
                select(func.count())
                .select_from(StockCatalogAdmission)
                .where(
                    StockCatalogAdmission.reference.startswith("bulk-alpaca-assets-v1:"),
                    StockCatalogAdmission.revoked_at.is_(None),
                    StockCatalogAdmission.id.not_in(unrelated_ids),
                )
            )
            == 10
        )
        verified_at = (
            await db.scalars(
                select(StockCatalogListing.provider_verified_at).where(
                    StockCatalogListing.provider_asset_id.is_not(None)
                )
            )
        ).all()
        assert verified_at == [NOW - timedelta(minutes=10)] * 2

    packet["environment"] = "live"
    _private(files[0], json.dumps(packet).encode())
    monkeypatch.setenv("ALPACA_ASSET_ENVIRONMENT", "live")
    async with finance_0026.begin() as db:
        mismatched = await _execute_batch(db, _inputs(*files), now=SECOND, after=0, limit=100)
        assert mismatched["outcomes"]["mapping_conflict"] == 2
