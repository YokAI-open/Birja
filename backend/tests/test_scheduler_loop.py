import asyncio
import json
import os
import signal
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from app.core.config import SchedulerSettings, Settings, get_scheduler_settings
from app.tasks import scheduler
from app.tasks.scheduler import CycleResult, run
from tests.test_portfolio_daily_schema import authorize_dev, run_migration, scratch_database

__all__ = ["scratch_database"]

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


async def test_enabled_amain_runs_independent_stock_loop_and_private_http(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from app.tasks import stock_scheduler

    monkeypatch.setenv("PRICE_SOURCE", "fake")
    monkeypatch.setenv("STOCK_DATA_ENABLED", "true")
    monkeypatch.setenv("ALPACA_API_KEY", "synthetic-private-key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "synthetic-private-secret")
    get_scheduler_settings.cache_clear()
    stop = asyncio.Event()
    stock_started = asyncio.Event()
    crypto_calls = []
    stock_cancelled = asyncio.Event()
    clients = []

    async def crypto(**kw: Any) -> CycleResult:
        assert not kw["source"].__dict__.get("headers")
        crypto_calls.append(asyncio.get_running_loop().time())
        if len(crypto_calls) == 3:
            stop.set()
        return CycleResult("ok")

    async def hanging_stock(**kw: Any) -> CycleResult:
        clients.append(kw["http"])
        assert kw["http"].headers["APCA-API-KEY-ID"] == "synthetic-private-key"
        assert kw["http"].headers["APCA-API-SECRET-KEY"] == "synthetic-private-secret"
        stock_started.set()
        try:
            await asyncio.Event().wait()
        finally:
            stock_cancelled.set()
        return CycleResult("ok")

    real_run = scheduler.run

    async def accelerated_run(**kw: Any) -> None:
        await real_run(**{**kw, "interval": 0.04, "heartbeat": tmp_path / "hb"})

    monkeypatch.setattr(scheduler, "run_cycle", crypto)
    monkeypatch.setattr(stock_scheduler, "run_stock_cycle", hanging_stock)
    monkeypatch.setattr(scheduler, "run", accelerated_run)
    try:
        async with asyncio.timeout(2):
            await scheduler.amain(stop)
    finally:
        get_scheduler_settings.cache_clear()
    assert stock_started.is_set()
    assert stock_cancelled.is_set()
    assert clients[0].is_closed
    assert len(crypto_calls) == 3
    assert 0.06 <= crypto_calls[-1] - crypto_calls[0] < 1
    assert (tmp_path / "hb").exists()


async def test_stock_exception_does_not_kill_crypto_loop(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from app.tasks import stock_scheduler

    monkeypatch.setenv("PRICE_SOURCE", "fake")
    monkeypatch.setenv("STOCK_DATA_ENABLED", "true")
    monkeypatch.setenv("ALPACA_API_KEY", "synthetic-key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "synthetic-secret")
    get_scheduler_settings.cache_clear()
    stop = asyncio.Event()
    calls = []

    async def crypto(**kw: Any) -> CycleResult:
        calls.append(1)
        if len(calls) == 3:
            stop.set()
        return CycleResult("ok")

    async def broken(**kw: Any) -> CycleResult:
        raise RuntimeError("synthetic")

    real_run = scheduler.run

    async def accelerated_run(**kw: Any) -> None:
        await real_run(**{**kw, "interval": 0.04, "heartbeat": tmp_path / "hb"})

    monkeypatch.setattr(scheduler, "run_cycle", crypto)
    monkeypatch.setattr(stock_scheduler, "run_stock_cycle", broken)
    monkeypatch.setattr(scheduler, "run", accelerated_run)
    try:
        async with asyncio.timeout(2):
            await scheduler.amain(stop)
    finally:
        get_scheduler_settings.cache_clear()
    assert len(calls) == 3


@pytest.mark.parametrize("mode", ["off", "kraken", "iex"])
async def test_amain_wires_history_with_its_own_cache_and_clients(
    monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    from app.core.config import SchedulerSettings
    from app.schemas.market_history import MarketHistoryScopes
    from app.tasks import market_history
    from tests.test_market_history_api import crypto_scope, scope_fields

    now = datetime.now(UTC)
    scope = None
    stock_enabled = mode == "iex"
    if mode == "kraken":
        scope = crypto_scope(now, "birja")
    elif stock_enabled:
        scope = MarketHistoryScopes.model_validate_json(
            json.dumps(
                {
                    "alpaca_iex": {
                        **scope_fields(now, "birja"),
                        "account": "birja",
                        "targets": [
                            {
                                "instrument": {"kind": "featured", "symbol": "AAPL"},
                                "provider_symbol": "AAPL",
                                "provider_asset_id": "synthetic-apple-id",
                                "exchange": "NASDAQ",
                                "identity_since": (now - timedelta(days=30)).isoformat(),
                            }
                        ],
                    },
                }
            )
        )
    config = SchedulerSettings(
        env="test",
        price_source="kraken",
        market_history_scope_json=scope,
        catalog_quote_redis_url="redis://127.0.0.1:57379/0",
        stock_data_enabled=stock_enabled,
        alpaca_api_key="synthetic-key",
        alpaca_secret_key="synthetic-secret",
    )
    monkeypatch.setattr(scheduler, "get_scheduler_settings", lambda: config)
    ticker_callbacks = []
    history_calls = []
    pairs = ["XXBTZUSD"]

    async def current_ticker(_http, symbols, *, record_attempt):
        assert symbols == pairs
        ticker_callbacks.append(record_attempt)
        if record_attempt is not None:
            record_attempt(symbols)
        return {pairs[0]: {}}

    async def current_cycle(**kw: Any) -> CycleResult:
        assert await kw["source"](pairs) == {pairs[0]: {}}
        return CycleResult("ok")

    async def history_cycle(**kw: Any) -> CycleResult:
        assert kw["redis"] is not kw["quota_redis"]
        assert "APCA-API-KEY-ID" not in kw["http"].headers
        if stock_enabled:
            assert kw["stock_http"].headers["APCA-API-KEY-ID"] == "synthetic-key"
        else:
            assert kw["stock_http"] is None
        history_calls.append(kw)
        return CycleResult("ok")

    async def one_cycle(*, cycle, interval, stop, heartbeat=scheduler.HEARTBEAT_PATH):
        if cycle.__name__ == "history_cycle":
            assert heartbeat is None and interval == market_history.HISTORY_CHECK_INTERVAL_SECONDS
        if cycle.__name__ in {"cycle", "history_cycle"}:
            await cycle()

    monkeypatch.setattr(scheduler.kraken, "fetch_tickers_isolated", current_ticker)
    monkeypatch.setattr(scheduler, "run_cycle", current_cycle)
    monkeypatch.setattr(scheduler, "run", one_cycle)
    monkeypatch.setattr(market_history, "run_history_cycle", history_cycle)
    await scheduler.amain(asyncio.Event())

    assert len(ticker_callbacks) == 1 and bool(ticker_callbacks[0]) == (mode == "kraken")
    assert len(history_calls) == int(mode != "off")
    if mode == "kraken":
        tracker = history_calls[0]["tracker"]
        assert tracker.pairs == frozenset(pairs)
        assert len(tracker.attempts) == 1 and not tracker.running
    if mode == "iex":
        assert history_calls[0]["tracker"] is None and history_calls[0]["stock_http"].is_closed


@pytest.mark.parametrize("filename", ["docker-compose.yml", "docker-compose.prod.yml"])
def test_compose_stock_keys_only_reach_disabled_scheduler(filename: str) -> None:
    content = (BACKEND_DIR.parent / filename).read_text()
    # Service-local indentation avoids a new YAML dependency for this contract.
    import re

    services = re.split(r"(?m)^  ([a-z][a-z_]*):\s*$", content)
    found = {}
    for i in range(1, len(services), 2):
        found[services[i]] = services[i + 1]
    stock = found["scheduler"]
    assert "STOCK_DATA_ENABLED: ${STOCK_DATA_ENABLED:-false}" in stock
    assert "ALPACA_API_KEY: ${ALPACA_API_KEY:-}" in stock
    assert "ALPACA_SECRET_KEY: ${ALPACA_SECRET_KEY:-}" in stock
    assert "PORTFOLIO_DAILY_CAPTURE_ENABLED: ${PORTFOLIO_DAILY_CAPTURE_ENABLED:-true}" in stock
    for threshold in (
        "PRICE_FRESH_SECONDS: ${PRICE_FRESH_SECONDS:-120}",
        "PRICE_STALE_SECONDS: ${PRICE_STALE_SECONDS:-300}",
    ):
        assert threshold in stock and threshold in found["backend"]
    for name, value in found.items():
        if name != "scheduler":
            assert "ALPACA_" not in value
            assert "PORTFOLIO_DAILY_CAPTURE_ENABLED" not in value
    assert "VITE_ALPACA" not in content


def test_shared_valuation_threshold_environment(monkeypatch):
    monkeypatch.setenv("PRICE_FRESH_SECONDS", "37")
    monkeypatch.setenv("PRICE_STALE_SECONDS", "45")
    for config in (SchedulerSettings(), Settings()):
        assert (config.price_fresh_seconds, config.price_stale_seconds) == (37, 45)


@pytest.mark.parametrize("mode", ["disabled", "predecessor", "successor", "unavailable"])
async def test_amain_admits_private_daily_cycle_only_on_supported_schema(
    monkeypatch, scratch_database, mode
):
    from app.tasks import portfolio_daily_values as daily

    admin, migrator = scratch_database
    if mode in {"predecessor", "successor"}:
        revision = "0027" if mode == "predecessor" else "0028"
        await run_migration(migrator, revision)
        await authorize_dev(admin, revision)
    config = SchedulerSettings(
        price_source="fake",
        database_url=admin.url.render_as_string(hide_password=False),
        portfolio_daily_capture_enabled=mode != "disabled",
    )
    calls = []
    schema_checks = []
    real = daily.daily_capture_schema_available

    async def check(engine):
        schema_checks.append(engine)
        return await real(engine)

    async def current_cycle(**kwargs):
        calls.append("current")
        return CycleResult("ok")

    async def daily_cycle(**kwargs):
        assert set(kwargs) == {"sessionmaker", "settings", "cursor"}
        assert kwargs["settings"] is config
        assert kwargs["cursor"] == daily.DailyValueCursor()
        calls.append("daily")
        return CycleResult("ok")

    async def one_cycle(*, cycle, interval, stop, heartbeat=scheduler.HEARTBEAT_PATH):
        if cycle.__name__ == "daily_capture_cycle":
            assert interval == 60 and heartbeat is None
        await cycle()

    monkeypatch.setattr(scheduler, "get_scheduler_settings", lambda: config)
    monkeypatch.setattr(scheduler, "run", one_cycle)
    monkeypatch.setattr(scheduler, "run_cycle", current_cycle)
    monkeypatch.setattr(daily, "daily_capture_schema_available", check)
    monkeypatch.setattr(daily, "run_portfolio_daily_capture", daily_cycle)
    await scheduler.amain(asyncio.Event())
    assert calls == (["current", "daily"] if mode == "successor" else ["current"])
    assert len(schema_checks) == int(mode != "disabled")


@pytest.mark.parametrize("failure", [False, True])
async def test_dividend_loop_is_independent_and_awaits_cancellation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, failure: bool
) -> None:
    from app.core.config import SchedulerSettings
    from app.tasks import dividends, stock_actions

    settings = SchedulerSettings(
        env="test",
        price_source="fake",
        database_url="postgresql+asyncpg://birja_test:test@127.0.0.1:55432/birja_test",
        redis_url="redis://:test@127.0.0.1:56379/0",
        stock_actions_enabled=True,
        stock_actions_coverage_start="2026-11-01T00:00:00Z",
        alpaca_api_key="synthetic-key",
        alpaca_secret_key="synthetic-secret",
    )
    monkeypatch.setattr(scheduler, "get_scheduler_settings", lambda: settings)
    started, cleaned, stop = asyncio.Event(), asyncio.Event(), asyncio.Event()
    calls = []

    async def crypto(**kwargs: Any) -> CycleResult:
        calls.append(1)
        if len(calls) == 3:
            stop.set()
        return CycleResult("ok")

    async def actions(**kwargs: Any) -> CycleResult:
        return CycleResult("ok")

    async def dividend(**kwargs: Any) -> CycleResult:
        assert "http" not in kwargs and "redis" not in kwargs
        started.set()
        try:
            if failure:
                raise RuntimeError("private-synthetic-payload")
            await asyncio.Event().wait()
        finally:
            cleaned.set()
        return CycleResult("ok")

    real_run = scheduler.run

    async def accelerated(**kwargs: Any) -> None:
        await real_run(**{**kwargs, "interval": 0.02, "heartbeat": tmp_path / "hb"})

    monkeypatch.setattr(scheduler, "run_cycle", crypto)
    monkeypatch.setattr(stock_actions, "run_stock_action_cycle", actions)
    monkeypatch.setattr(dividends, "run_dividend_cycle", dividend)
    monkeypatch.setattr(scheduler, "run", accelerated)
    async with asyncio.timeout(2):
        await scheduler.amain(stop)
    assert started.is_set() and cleaned.is_set() and len(calls) == 3


async def test_due_check_does_not_touch_main_heartbeat(monkeypatch):
    from unittest.mock import Mock

    stop = asyncio.Event()
    heartbeat = Mock()
    monkeypatch.setattr(scheduler, "touch_heartbeat", heartbeat)
    ran = False

    async def due_check() -> CycleResult:
        nonlocal ran
        ran = True
        asyncio.get_running_loop().call_later(0.01, stop.set)
        return CycleResult("locked")

    async with asyncio.timeout(1):
        await run(cycle=due_check, interval=60, stop=stop, heartbeat=None)
    assert ran
    heartbeat.assert_not_called()
