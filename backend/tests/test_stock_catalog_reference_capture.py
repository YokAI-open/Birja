import json
from argparse import Namespace
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import pytest

from app.services.stock_catalog_pillar import parse_cat_snapshot, parse_pillar_snapshot
from app.services.stock_catalog_sources import CatalogSourceError, parse_directory
from app.tasks import stock_catalog_reference_capture as runner
from app.tasks.stock_catalog_inventory import _lock_cursor
from app.tasks.stock_catalog_reference_inventory import _read_mappings
from tests.test_stock_catalog_pillar import CAT, CAT_TIME, DAY, FILENAME, PILLAR
from tests.test_stock_catalog_sources import directory, mapping


class Clock:
    def __init__(self) -> None:
        self.now = CAT_TIME

    def read(self) -> datetime:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


def plan() -> runner.CapturePlan:
    nasdaq = parse_directory(
        "nasdaqlisted",
        directory(
            "nasdaqlisted",
            "FXCO|Fixture ordinary|Q|N|N|100|N|N",
            "FXOU|Fixture closed-end fund|Q|N|N|100|N|N",
            time="1125202614:11",
        ),
    )
    cat = parse_cat_snapshot(CAT, published_at=CAT_TIME, expected_trade_date=DAY)
    pillar = parse_pillar_snapshot(PILLAR, filename=FILENAME, expected_trade_date=DAY)
    return runner.plan_capture(nasdaq, cat, pillar, CAT_TIME)


def check_scope(at: datetime) -> None:
    assert at.utcoffset() == timedelta(0)


def test_exact_reference_targets_preserve_exchange_and_distinct_share_classes() -> None:
    capture_plan = plan()
    assert capture_plan.digest == plan().digest
    assert [(job.venue, job.symbol, job.exchange) for job in capture_plan.targets] == [
        ("NASDAQ", "FXCO", "UW"),
        ("NYSE", "FXCA.A", "UN"),
        ("NYSE", "FXCA.B", "UN"),
    ]


async def test_capture_persists_before_sending_and_exports_compatible_reusable_fields(
    tmp_path: Path,
) -> None:
    capture_plan = plan()
    clock = Clock()
    checkpoints: list[runner.CaptureCursor] = []

    def mapping_response(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url) == runner.OPENFIGI_URL
        assert "Authorization" not in request.headers
        assert "X-OPENFIGI-APIKEY" not in request.headers
        assert checkpoints[-1].recent_attempts == (CAT_TIME,)
        assert not checkpoints[-1].observations
        jobs = json.loads(request.content)
        return httpx.Response(
            200,
            json=[
                {
                    "data": [
                        mapping(job["idValue"], job["exchCode"])
                        | {"name": "Fixture issuer", "securityDescription": "Unused provider text"}
                    ]
                }
                for job in jobs
            ],
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(mapping_response)) as client:
        completed = await runner.capture(
            capture_plan,
            runner.CaptureCursor(plan_digest=capture_plan.digest),
            client,
            checkpoints.append,
            clock=clock.read,
            sleeper=clock.sleep,
            check_scope=check_scope,
        )
    output = tmp_path / "mapping.jsonl"
    runner._write_lines(output, (item.model_dump_json() for item in completed.observations))
    assert output.stat().st_mode & 0o077 == 0
    readback = _read_mappings(output)
    assert set(readback["NYSE"]) == {"FXCA.A", "FXCA.B"}
    assert set(readback["NASDAQ"]) == {"FXCO"}
    assert "securityDescription" not in output.read_text()
    assert "Fixture issuer" in output.read_text()
    assert "Unused provider text" not in output.read_text()


async def test_provider_failure_does_not_retry_and_resumed_cursor_respects_cooldown() -> None:
    capture_plan = plan()
    clock = Clock()
    calls = 0
    checkpoints: list[runner.CaptureCursor] = []

    def read(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "75"})
        return httpx.Response(200, json=[{"warning": "Unused warning text"}] * 3)

    async with httpx.AsyncClient(transport=httpx.MockTransport(read)) as client:
        cursor = runner.CaptureCursor(plan_digest=capture_plan.digest)
        for _ in range(2):
            cursor = await runner.capture(
                capture_plan,
                cursor,
                client,
                checkpoints.append,
                clock=clock.read,
                sleeper=clock.sleep,
                check_scope=check_scope,
            )
        assert calls == 1 and cursor.retry_after == CAT_TIME + timedelta(seconds=75)
        assert cursor.recent_attempts == (CAT_TIME,) and not cursor.observations
        await clock.sleep(75)
        recovered = await runner.capture(
            capture_plan,
            runner.CaptureCursor.model_validate_json(cursor.model_dump_json()),
            client,
            checkpoints.append,
            clock=clock.read,
            sleeper=clock.sleep,
            check_scope=check_scope,
        )
    assert calls == 2 and len(recovered.observations) == 3
    assert recovered.retry_after is None
    assert recovered.observations[0].observation.result == {"warning": "No current mapping"}


@pytest.mark.parametrize(
    "replies",
    [
        [{"warning": "No mapping"}],
        [{"warning": "No mapping"}, {"error": "source failed"}, {"warning": "No mapping"}],
        [{"data": [{"name": 12}]}] * 3,
    ],
)
async def test_malformed_batch_keeps_a_reserved_attempt_and_no_partial_results(replies) -> None:
    capture_plan = plan()
    clock = Clock()
    checkpoints: list[runner.CaptureCursor] = []
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=replies))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(CatalogSourceError):
            await runner.capture(
                capture_plan,
                runner.CaptureCursor(plan_digest=capture_plan.digest),
                client,
                checkpoints.append,
                clock=clock.read,
                sleeper=clock.sleep,
                check_scope=check_scope,
            )
    assert len(checkpoints) == 1
    assert checkpoints[0].recent_attempts == (CAT_TIME,)
    assert not checkpoints[0].observations


async def test_limits_hold_across_a_full_invocation_and_a_resumed_invocation() -> None:
    capture_plan = runner.CapturePlan(
        "a" * 64,
        tuple(
            runner.CaptureTarget(venue="NYSE", symbol=f"FX{ordinal}", exchange="UN")
            for ordinal in range(1001)
        ),
    )
    clock = Clock()
    timestamps: list[datetime] = []

    def read(request: httpx.Request) -> httpx.Response:
        jobs = json.loads(request.content)
        assert 1 <= len(jobs) <= 10
        timestamps.append(clock.now)
        return httpx.Response(200, json=[{"warning": "No mapping"}] * len(jobs))

    async with httpx.AsyncClient(transport=httpx.MockTransport(read)) as client:
        cursor = await runner.capture(
            capture_plan,
            runner.CaptureCursor(plan_digest=capture_plan.digest),
            client,
            lambda _: None,
            clock=clock.read,
            sleeper=clock.sleep,
            check_scope=check_scope,
        )
        assert len(cursor.observations) == 1000 and len(timestamps) == 100
        cursor = await runner.capture(
            capture_plan,
            cursor,
            client,
            lambda _: None,
            clock=clock.read,
            sleeper=clock.sleep,
            check_scope=check_scope,
        )
    assert len(cursor.observations) == 1001 and len(timestamps) == 101
    for index, at in enumerate(timestamps[20:]):
        assert at - timestamps[index] >= timedelta(minutes=1)


async def test_cursor_with_different_inputs_refuses_before_network() -> None:
    clock = Clock()

    def unexpected(request: httpx.Request) -> httpx.Response:
        raise AssertionError(request.url)

    async with httpx.AsyncClient(transport=httpx.MockTransport(unexpected)) as client:
        with pytest.raises(CatalogSourceError, match="input digests"):
            await runner.capture(
                plan(),
                runner.CaptureCursor(plan_digest="a" * 64),
                client,
                lambda _: None,
                clock=clock.read,
                sleeper=clock.sleep,
                check_scope=check_scope,
            )


async def test_host_lock_prevents_overlapping_capture_even_with_a_different_cursor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    host_lock = tmp_path / "host"
    monkeypatch.setattr(runner, "_HOST_CURSOR_LOCK", host_lock)
    args = Namespace(
        cursor=tmp_path / "other-cursor.json",
        output=tmp_path / "other-output.jsonl",
        nasdaq=tmp_path / "nasdaq.txt",
        cat=tmp_path / "cat.txt",
        pillar=tmp_path / FILENAME,
        rights=tmp_path / "rights.json",
    )
    with _lock_cursor(host_lock), pytest.raises(CatalogSourceError, match="already owns"):
        await runner._run(args)
