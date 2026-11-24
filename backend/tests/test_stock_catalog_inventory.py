import json
from argparse import Namespace
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import pytest

from app.services.stock_catalog_sources import (
    CatalogSourceError,
    parse_directory,
    validate_directory_pair,
)
from app.tasks.stock_catalog_inventory import (
    OPENFIGI_URL,
    CatalogManifest,
    Cursor,
    _inventory_inputs,
    _resume_mapping,
    _run,
    inventory,
    validate_manifest,
)
from tests.test_stock_catalog_sources import AS_OF, NASDAQ_COMMON, NYSE_COMMON, directory, mapping


def fixture_paths(tmp_path: Path, *, conflict: bool = False) -> Namespace:
    paths = Namespace(
        mode="fixture",
        as_of=AS_OF,
        nasdaq=tmp_path / "nasdaq.txt",
        other=tmp_path / "other.txt",
        mapping=tmp_path / "mapping.json",
        output=tmp_path / "candidate.json",
        rights=None,
        exceptions=None,
    )
    nasdaq = [NASDAQ_COMMON, NASDAQ_COMMON, "FETF|Fixture ETF|G|N|N|100|Y|N"]
    if conflict:
        nasdaq.append(NASDAQ_COMMON.replace("Fixture Alpha", "Fixture Beta"))
    paths.nasdaq.write_bytes(directory("nasdaqlisted", *nasdaq))
    paths.other.write_bytes(
        directory("otherlisted", NYSE_COMMON, "FOS|Fixture Other|P|FOS|N|100|N|FOS")
    )
    mappings = {"otherlisted:1": {"data": [mapping("FST/B", "UN", "BBG000000013")]}}
    if not conflict:
        mappings["nasdaqlisted:1"] = {"data": [mapping("FSTA", "UW")]}
    paths.mapping.write_text(json.dumps(mappings), encoding="utf-8")
    return paths


@pytest.mark.asyncio
async def test_fixture_command_has_complete_reproducible_receipt(tmp_path: Path) -> None:
    args = fixture_paths(tmp_path)
    assert await _run(args)
    payload = args.output.read_bytes()
    assert await _run(args)
    assert args.output.read_bytes() == payload
    candidate = CatalogManifest.model_validate_json(payload)
    validate_manifest(candidate, AS_OF)
    assert candidate.complete and candidate.mode == "fixture"
    assert candidate.coverage["NASDAQ"].model_dump() == {
        "included": 1,
        "duplicate": 1,
        "excluded": 1,
        "unresolved": 0,
        "total": 3,
    }
    assert candidate.coverage["NYSE"].included == 1
    assert candidate.coverage["out_of_scope"].excluded == 1
    assert "Unused provider text" not in payload.decode()
    with pytest.raises(CatalogSourceError, match="coverage does not reconcile"):
        validate_manifest(candidate.model_copy(update={"complete": False}), AS_OF)
    with pytest.raises(CatalogSourceError, match="explicit rights"):
        validate_manifest(candidate.model_copy(update={"mode": "live"}), AS_OF)


@pytest.mark.asyncio
async def test_conflicting_source_rows_and_reused_issue_identifiers_stay_unresolved(
    tmp_path: Path,
) -> None:
    args = fixture_paths(tmp_path, conflict=True)
    assert not await _run(args)
    candidate = CatalogManifest.model_validate_json(args.output.read_bytes())
    assert candidate.coverage["NASDAQ"].unresolved == 3
    assert candidate.coverage["NYSE"].included == 1

    args = fixture_paths(tmp_path)
    payload = json.loads(args.mapping.read_bytes())
    payload["otherlisted:1"] = {"data": [mapping("FST/B", "UN")]}
    args.mapping.write_text(json.dumps(payload), encoding="utf-8")
    assert not await _run(args)
    candidate = CatalogManifest.model_validate_json(args.output.read_bytes())
    assert candidate.coverage["NASDAQ"].unresolved == candidate.coverage["NYSE"].unresolved == 1
    assert candidate.rows[0].reason == "conflicting_issue_identity"


def _rights_payload() -> list[dict[str, object]]:
    directory_fields = (
        "ticker",
        "listing_exchange",
        "company_name",
        "aliases",
        "share_class",
        "eligibility",
        "source_evidence",
    )
    scopes = {
        "nasdaqlisted": directory_fields,
        "otherlisted": directory_fields,
        "openfigi": ("classification", "identity_key", "aliases", "source_evidence"),
    }
    return [
        {
            "artifact": source,
            "reference": "synthetic approval for transport test",
            "reviewed_at": (AS_OF - timedelta(days=1)).isoformat(),
            "valid_until": (AS_OF + timedelta(days=1)).isoformat(),
            "fields": {
                name: ["collection", "internal_use", "derived_use", "display", "storage", "backup"]
                for name in fields
            },
        }
        for source, fields in scopes.items()
    ]


@pytest.mark.asyncio
async def test_unknown_rights_refuse_before_live_requests_and_source_failure_refuses(
    tmp_path: Path,
) -> None:
    rights = tmp_path / "rights.json"
    args = Namespace(mode="live", rights=rights, exceptions=None, cursor=tmp_path / "cursor.json")
    requested = []

    def transport(request: httpx.Request) -> httpx.Response:
        requested.append(request.url)
        if request.url.path.endswith("nasdaqlisted.txt"):
            return httpx.Response(200, content=directory("nasdaqlisted", NASDAQ_COMMON))
        return httpx.Response(503)

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        rights.write_text(json.dumps(_rights_payload()[:1]), encoding="utf-8")
        with pytest.raises(CatalogSourceError, match="explicit rights required for otherlisted"):
            await inventory(args, client, AS_OF)
        assert requested == []
        rights.write_text(json.dumps(_rights_payload()), encoding="utf-8")
        with pytest.raises(CatalogSourceError, match="HTTP 503"):
            await inventory(args, client, AS_OF)
    assert len(requested) == 2
    assert all(url.host == "www.nasdaqtrader.com" for url in requested)
    assert not args.cursor.exists()


class FakeClock:
    now = AS_OF

    def read(self) -> datetime:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


@pytest.mark.asyncio
async def test_resume_caps_jobs_attempts_minute_and_run() -> None:
    clock = FakeClock()
    template = parse_directory("nasdaqlisted", directory("nasdaqlisted", NASDAQ_COMMON)).rows[0]
    pending = [replace(template, row_key=f"nasdaqlisted:{ordinal}") for ordinal in range(1, 1012)]
    calls = []
    checkpoints = []

    def transport(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == OPENFIGI_URL
        assert "x-openfigi-apikey" not in request.headers
        jobs = json.loads(request.content)
        assert len(jobs) <= 10
        assert jobs[0] == {"idType": "TICKER", "idValue": "FSTA", "exchCode": "UW"}
        calls.append(clock.now)
        return httpx.Response(200, json=[{"warning": "no mapping"}] * len(jobs))

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        starting = Cursor(source_digests=("1" * 64, "2" * 64))
        first = await _resume_mapping(
            client,
            pending,
            starting,
            checkpoints.append,
            clock=clock.read,
            sleeper=clock.sleep,
            check_scope=lambda _: None,
        )
        assert len(calls) == 100
        assert first.source_digests == starting.source_digests
        assert len(first.outcomes) == 1000
        assert all(row.disposition == "unresolved" for row in first.outcomes)
        second = await _resume_mapping(
            client,
            pending[1000:],
            Cursor.model_validate_json(first.model_dump_json()),
            checkpoints.append,
            clock=clock.read,
            sleeper=clock.sleep,
            check_scope=lambda _: None,
        )
    assert len(second.outcomes) == 1011
    assert len(calls) == 102
    assert all(
        tick - calls[index - 20] >= timedelta(minutes=1)
        for index, tick in enumerate(calls)
        if index >= 20
    )


@pytest.mark.asyncio
async def test_retry_after_and_incomplete_mapping_do_not_commit_failed_batch() -> None:
    clock = FakeClock()
    snapshot = parse_directory("nasdaqlisted", directory("nasdaqlisted", NASDAQ_COMMON))
    attempts = []
    checkpoints = []

    def transport(request: httpx.Request) -> httpx.Response:
        attempts.append(clock.now)
        if len(attempts) == 1:
            return httpx.Response(429, headers={"Retry-After": "5"})
        return httpx.Response(200, json=[])

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        with pytest.raises(CatalogSourceError, match="does not match its jobs"):
            await _resume_mapping(
                client,
                list(snapshot.rows),
                Cursor(source_digests=(snapshot.sha256, "2" * 64)),
                checkpoints.append,
                clock=clock.read,
                sleeper=clock.sleep,
                check_scope=lambda _: None,
            )
    assert attempts[1] - attempts[0] == timedelta(seconds=5)
    assert not any(state.outcomes for state in checkpoints)
    assert checkpoints[-1].recent_attempts == tuple(attempts)


@pytest.mark.asyncio
async def test_refresh_rebinds_unchanged_evidence_and_reclassifies_expired_or_changed_rows() -> (
    None
):
    first = parse_directory("nasdaqlisted", directory("nasdaqlisted", NASDAQ_COMMON))
    second = parse_directory("otherlisted", directory("otherlisted", NYSE_COMMON))
    snapshots = validate_directory_pair(first, second, AS_OF)
    _, _, pending = _inventory_inputs(snapshots, (), AS_OF, ())
    assert len(pending) == 2

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json=[{"data": [mapping("FSTA", "UW")]}, {"warning": "missing"}],
            )
        )
    ) as client:
        clock = FakeClock()
        saved = await _resume_mapping(
            client,
            pending,
            Cursor(source_digests=(first.sha256, second.sha256)),
            lambda _: None,
            clock=clock.read,
            sleeper=clock.sleep,
            check_scope=lambda _: None,
        )

    changed = parse_directory(
        "otherlisted", directory("otherlisted", NYSE_COMMON.replace("Fixture", "Updated"))
    )
    _, reusable, pending = _inventory_inputs((first, changed), (), AS_OF, saved.outcomes)
    assert list(reusable) == ["nasdaqlisted:1"]
    assert [row.row_key for row in pending] == ["otherlisted:1"]
    _, reusable, pending = _inventory_inputs(
        snapshots, (), AS_OF + timedelta(days=2), saved.outcomes
    )
    assert list(reusable) == ["nasdaqlisted:1"]
    assert [row.row_key for row in pending] == ["otherlisted:1"]
    _, reusable, pending = _inventory_inputs(
        snapshots, (), AS_OF + timedelta(days=8), saved.outcomes
    )
    assert not reusable and len(pending) == 2


@pytest.mark.asyncio
async def test_scope_expiry_during_provider_wait_refuses_retry() -> None:
    clock = FakeClock()
    snapshot = parse_directory("nasdaqlisted", directory("nasdaqlisted", NASDAQ_COMMON))
    calls = []

    def transport(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(429, headers={"Retry-After": "5"})

    def check_scope(at: datetime) -> None:
        if at >= AS_OF + timedelta(seconds=3):
            raise CatalogSourceError("Mapping rights expired")

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        with pytest.raises(CatalogSourceError, match="Mapping rights expired"):
            await _resume_mapping(
                client,
                list(snapshot.rows),
                Cursor(source_digests=(snapshot.sha256, "2" * 64)),
                lambda _: None,
                clock=clock.read,
                sleeper=clock.sleep,
                check_scope=check_scope,
            )
    assert len(calls) == 1
