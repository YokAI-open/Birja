import asyncio
import os
import signal
import sys
from pathlib import Path
from typing import Any

import pytest

from app.core.config import get_scheduler_settings
from app.tasks import scheduler
from app.tasks.scheduler import CycleResult, run

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Clock:
    """Fake monotonic clock; a fake ``wait_for`` advances it by the requested delay."""

    def __init__(self) -> None:
        self.now = 0.0
        self.delays: list[float] = []

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> Clock:
    c = Clock()

    async def fake_wait_for(aw: Any, timeout: float) -> None:  # noqa: ASYNC109
        aw.close()
        c.delays.append(timeout)
        c.now += timeout
        raise TimeoutError

    monkeypatch.setattr(scheduler.asyncio, "wait_for", fake_wait_for)
    return c


async def test_first_cycle_immediate_then_fixed_cadence(clock: Clock, tmp_path: Path) -> None:
    stop = asyncio.Event()
    times: list[float] = []

    async def cycle() -> CycleResult:
        times.append(clock.now)
        clock.now += 7  # cycle duration must not cause drift
        if len(times) == 3:
            stop.set()
        return CycleResult("ok")

    await run(cycle=cycle, interval=60, stop=stop, heartbeat=tmp_path / "hb", monotonic=clock)
    assert times == [0.0, 60.0, 120.0]
    assert clock.delays[0] == 53.0


async def test_overrun_schedules_one_interval_after_now(clock: Clock, tmp_path: Path) -> None:
    stop = asyncio.Event()
    times: list[float] = []

    async def cycle() -> CycleResult:
        times.append(clock.now)
        clock.now += 100  # overruns the 60 s interval
        if len(times) == 2:
            stop.set()
        return CycleResult("ok")

    await run(cycle=cycle, interval=60, stop=stop, heartbeat=tmp_path / "hb", monotonic=clock)
    assert times == [0.0, 160.0]  # no catch-up burst
    assert clock.delays[0] == 60.0


@pytest.mark.parametrize("status", ["source_error", "lock_error", "locked"])
async def test_heartbeat_touched_after_failed_cycles(
    clock: Clock, tmp_path: Path, status: Any
) -> None:
    stop = asyncio.Event()
    hb = tmp_path / "hb"

    async def cycle() -> CycleResult:
        assert not hb.exists()
        stop.set()
        return CycleResult(status)

    await run(cycle=cycle, interval=60, stop=stop, heartbeat=hb, monotonic=clock)
    assert hb.exists()


async def test_stop_set_before_start_runs_no_cycle(tmp_path: Path) -> None:
    stop = asyncio.Event()
    stop.set()
    calls = 0

    async def cycle() -> CycleResult:
        nonlocal calls
        calls += 1
        return CycleResult("ok")

    await run(cycle=cycle, interval=60, stop=stop, heartbeat=tmp_path / "hb")
    assert calls == 0


async def test_stop_during_wait_ends_promptly(tmp_path: Path) -> None:
    stop = asyncio.Event()
    calls = 0

    async def cycle() -> CycleResult:
        nonlocal calls
        calls += 1
        asyncio.get_running_loop().call_later(0.05, stop.set)
        return CycleResult("ok")

    await asyncio.wait_for(
        run(cycle=cycle, interval=60, stop=stop, heartbeat=tmp_path / "hb"), timeout=5
    )
    assert calls == 1


def test_heartbeat_path_is_in_tmp() -> None:
    assert scheduler.HEARTBEAT_PATH.name == "birja-scheduler-heartbeat"


async def test_amain_runs_with_shared_candidates_and_closes_resources(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PRICE_SOURCE", "fake")
    monkeypatch.setattr(scheduler, "HEARTBEAT_PATH", tmp_path / "hb")
    monkeypatch.setattr(scheduler, "run", _with_heartbeat(scheduler.run, tmp_path / "hb"))
    get_scheduler_settings.cache_clear()
    stop = asyncio.Event()
    seen: list[dict[int, Any]] = []

    async def fake_cycle(**kw: Any) -> CycleResult:
        seen.append(kw["candidates"])
        stop.set()
        return CycleResult("ok")

    monkeypatch.setattr(scheduler, "run_cycle", fake_cycle)
    try:
        await scheduler.amain(stop)
    finally:
        get_scheduler_settings.cache_clear()
    assert len(seen) == 1
    assert (tmp_path / "hb").exists()


async def test_amain_real_cycle_against_test_stack(
    monkeypatch: pytest.MonkeyPatch, migrated: None, tmp_path: Path
) -> None:
    monkeypatch.setenv("PRICE_SOURCE", "fake")
    monkeypatch.setattr(scheduler, "run", _with_heartbeat(scheduler.run, tmp_path / "hb"))
    get_scheduler_settings.cache_clear()
    stop = asyncio.Event()
    real = scheduler.run_cycle

    async def once(**kw: Any) -> CycleResult:
        try:
            return await real(**kw)
        finally:
            stop.set()

    monkeypatch.setattr(scheduler, "run_cycle", once)
    try:
        await scheduler.amain(stop)
    finally:
        get_scheduler_settings.cache_clear()
    assert (tmp_path / "hb").exists()


async def test_amain_installs_signal_handlers_when_no_stop_given(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PRICE_SOURCE", "fake")
    get_scheduler_settings.cache_clear()
    loop = asyncio.get_running_loop()
    handlers: dict[int, Any] = {}
    monkeypatch.setattr(loop, "add_signal_handler", lambda sig, cb: handlers.__setitem__(sig, cb))

    async def stub_run(*, cycle: Any, interval: float, stop: asyncio.Event) -> None:
        handlers[scheduler.signal.SIGTERM]()
        assert stop.is_set()

    monkeypatch.setattr(scheduler, "run", stub_run)
    try:
        await scheduler.amain()
    finally:
        get_scheduler_settings.cache_clear()
    assert set(handlers) == {scheduler.signal.SIGTERM, scheduler.signal.SIGINT}


def test_main_runs_amain(monkeypatch: pytest.MonkeyPatch) -> None:
    called = []

    async def fake_amain(stop: Any = None) -> None:
        called.append(1)

    monkeypatch.setattr(scheduler, "amain", fake_amain)
    scheduler.main()
    assert called == [1]


def _with_heartbeat(real_run: Any, path: Path) -> Any:
    async def wrapped(**kw: Any) -> None:
        await real_run(heartbeat=path, **kw)

    return wrapped


async def test_python_m_entrypoint_logs_cycles_to_stderr(
    clean_prices: None, tmp_path: Path
) -> None:
    """Runs the scheduler exactly like the container does and reads its stderr."""
    # Least privilege: the scheduler must start without any app secret (WR-06).
    secrets = {"OTP_HMAC_SECRET", "JWT_SECRET", "RESEND_API_KEY", "EMAIL_FROM", "EMAIL_BACKEND"}
    env = {k: v for k, v in os.environ.items() if k not in secrets}
    env.update(PRICE_SOURCE="fake", TMPDIR=str(tmp_path))
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "app.tasks.scheduler",
        cwd=BACKEND_DIR,
        env=env,
        stderr=asyncio.subprocess.PIPE,
    )
    assert proc.stderr is not None
    lines: list[str] = []
    try:
        async with asyncio.timeout(20):
            while not any("price cycle:" in line for line in lines):
                raw = await proc.stderr.readline()
                if not raw:
                    break
                lines.append(raw.decode())
    except TimeoutError:
        pass
    finally:
        if proc.returncode is None:
            proc.send_signal(signal.SIGTERM)
        await asyncio.wait_for(proc.wait(), timeout=20)
    text = "".join(lines)
    assert "INFO app.tasks.scheduler: price scheduler started source=fake" in text
    assert "INFO app.tasks.scheduler: price cycle: status=ok accepted=15" in text
