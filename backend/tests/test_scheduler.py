import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import pytest
import pytest_asyncio
import respx
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.models.price import Coin, Price
from app.services.kraken import TICKER_URL, KrakenError
from app.services.price_rules import Candidate
from app.services.prices import AcceptedPrice, load_active_coins, upsert_prices
from app.tasks import scheduler
from app.tasks.scheduler import LOCK_KEY, CycleResult, build_source, run_cycle

FIXTURE = Path(__file__).parent / "fixtures" / "kraken_ticker_ok.json"
NOW = datetime(2026, 10, 28, 12, 0, 0, tzinfo=UTC)


def _body() -> dict[str, Any]:
    body: dict[str, Any] = json.loads(FIXTURE.read_text())
    return body


def _router() -> respx.MockRouter:
    return respx.mock(assert_all_mocked=True, assert_all_called=False)


@pytest_asyncio.fixture
async def sm(engine: AsyncEngine, clean_prices: None) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def http() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient() as client:
        yield client


async def _coin_ids(sm: async_sessionmaker[AsyncSession]) -> dict[str, int]:
    async with sm() as s:
        rows = await s.execute(select(Coin.symbol, Coin.id))
        return {sym: cid for sym, cid in rows}


async def _prices(sm: async_sessionmaker[AsyncSession]) -> dict[str, Price]:
    async with sm() as s:
        rows = await s.execute(select(Coin.symbol, Price).join(Price, Price.coin_id == Coin.id))
        return {sym: price for sym, price in rows}


async def _cycle(
    sm: async_sessionmaker[AsyncSession],
    redis: Redis,
    http: httpx.AsyncClient,
    settings: Settings,
    candidates: dict[int, Candidate],
    now: datetime = NOW,
) -> CycleResult:
    return await run_cycle(
        sessionmaker=sm,
        redis=redis,
        source=build_source(settings, http),
        settings=settings,
        candidates=candidates,
        now=lambda: now,
    )


async def test_happy_path_writes_15_prices_with_one_call(
    sm: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    http: httpx.AsyncClient,
    settings: Settings,
) -> None:
    with _router() as mock:
        route = mock.get(TICKER_URL).respond(200, json=_body())
        result = await _cycle(sm, redis_client, http, settings, {})
    assert result == CycleResult("ok", accepted=15, rejected=0)
    assert route.call_count == 1
    sent_pairs = set(route.calls.last.request.url.params["pair"].split(","))
    assert sent_pairs == set(_body()["result"])
    prices = await _prices(sm)
    assert len(prices) == 15
    assert all(p.as_of == NOW and p.source == "kraken" for p in prices.values())
    assert await redis_client.exists(LOCK_KEY) == 0


async def test_spike_rejected_then_confirmed_on_third_poll(
    sm: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    http: httpx.AsyncClient,
    settings: Settings,
) -> None:
    ids = await _coin_ids(sm)
    btc = ids["BTC"]
    old_time = NOW - timedelta(minutes=1)
    async with sm() as s:
        await upsert_prices(s, [AcceptedPrice(btc, Decimal("80000"), old_time)], "kraken")
        await s.commit()
    body = _body()
    body["result"]["XXBTZUSD"]["a"][0] = "120010"
    body["result"]["XXBTZUSD"]["b"][0] = "119990"
    candidates: dict[int, Candidate] = {}
    with _router() as mock:
        mock.get(TICKER_URL).respond(200, json=body)
        first = await _cycle(sm, redis_client, http, settings, candidates, NOW)
        assert first == CycleResult("ok", accepted=14, rejected=1)
        row = (await _prices(sm))["BTC"]
        assert row.mid == Decimal("80000") and row.as_of == old_time
        assert candidates[btc].count == 1
        second = await _cycle(sm, redis_client, http, settings, candidates, NOW)
        assert second.rejected == 1
        assert (await _prices(sm))["BTC"].mid == Decimal("80000")
        third = await _cycle(
            sm, redis_client, http, settings, candidates, NOW + timedelta(seconds=1)
        )
    assert third == CycleResult("ok", accepted=15, rejected=0)
    row = (await _prices(sm))["BTC"]
    assert row.mid == Decimal("120000")
    assert btc not in candidates


async def test_invalid_and_missing_entries_keep_last_good(
    sm: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    http: httpx.AsyncClient,
    settings: Settings,
) -> None:
    ids = await _coin_ids(sm)
    old_time = NOW - timedelta(minutes=2)
    async with sm() as s:
        await upsert_prices(
            s,
            [
                AcceptedPrice(ids["DOGE"], Decimal("0.08"), old_time),
                AcceptedPrice(ids["SOL"], Decimal("100"), old_time),
            ],
            "kraken",
        )
        await s.commit()
    body = _body()
    body["result"]["XDGUSD"]["b"][0] = "0"
    del body["result"]["SOLUSD"]
    with _router() as mock:
        mock.get(TICKER_URL).respond(200, json=body)
        result = await _cycle(sm, redis_client, http, settings, {})
    assert result == CycleResult("ok", accepted=13, rejected=2)
    prices = await _prices(sm)
    assert prices["DOGE"].mid == Decimal("0.08") and prices["DOGE"].as_of == old_time
    assert prices["SOL"].mid == Decimal("100") and prices["SOL"].as_of == old_time
    assert prices["BTC"].as_of == NOW


async def test_kraken_error_writes_nothing_and_releases_lock(
    sm: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    http: httpx.AsyncClient,
    settings: Settings,
) -> None:
    with _router() as mock:
        mock.get(TICKER_URL).respond(200, json={"error": ["EQuery:Unknown asset pair"]})
        result = await _cycle(sm, redis_client, http, settings, {})
    assert result == CycleResult("source_error")
    assert await _prices(sm) == {}
    assert await redis_client.exists(LOCK_KEY) == 0


async def test_one_unknown_pair_does_not_stall_the_other_coins(
    sm: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    http: httpx.AsyncClient,
    settings: Settings,
) -> None:
    full = _body()["result"]

    def respond(request: httpx.Request) -> httpx.Response:
        pairs = request.url.params["pair"].split(",")
        if "DOTUSD" in pairs:
            return httpx.Response(200, json={"error": ["EQuery:Unknown asset pair"]})
        return httpx.Response(200, json={"error": [], "result": {p: full[p] for p in pairs}})

    with _router() as mock:
        mock.get(TICKER_URL).mock(side_effect=respond)
        result = await _cycle(sm, redis_client, http, settings, {})
    assert result == CycleResult("ok", accepted=14, rejected=1)
    prices = await _prices(sm)
    assert len(prices) == 14 and "DOT" not in prices


async def test_decimal_overflow_rejects_only_that_coin(
    sm: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    http: httpx.AsyncClient,
    settings: Settings,
) -> None:
    body = _body()
    # 39 digits at 8 dp exceed the 28-digit Decimal context: quantize raises.
    body["result"]["XDGUSD"]["a"][0] = "1e30"
    body["result"]["XDGUSD"]["b"][0] = "1e30"
    with _router() as mock:
        mock.get(TICKER_URL).respond(200, json=body)
        result = await _cycle(sm, redis_client, http, settings, {})
    assert result == CycleResult("ok", accepted=14, rejected=1)
    prices = await _prices(sm)
    assert len(prices) == 14 and "DOGE" not in prices


@pytest.mark.parametrize("error", [ValueError("bad"), ArithmeticError("bad")])
async def test_per_coin_errors_reject_only_that_coin(
    sm: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    http: httpx.AsyncClient,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    caplog: pytest.LogCaptureFixture,
) -> None:
    real = scheduler.mid_from_ticker
    btc_entry = _body()["result"]["XXBTZUSD"]

    def flaky(entry: object) -> Decimal | None:
        if entry == btc_entry:
            raise error
        return real(entry)

    monkeypatch.setattr(scheduler, "mid_from_ticker", flaky)
    with _router() as mock:
        mock.get(TICKER_URL).respond(200, json=_body())
        with caplog.at_level("WARNING", logger="app.tasks.scheduler"):
            result = await _cycle(sm, redis_client, http, settings, {})
    assert result == CycleResult("ok", accepted=14, rejected=1)
    assert "symbol=BTC reason=invalid" in caplog.text
    assert "BTC" not in await _prices(sm)


async def test_lock_held_makes_no_call_and_keeps_other_lock(
    sm: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    http: httpx.AsyncClient,
    settings: Settings,
) -> None:
    await redis_client.set(LOCK_KEY, "someone-else", px=30_000)
    with _router() as mock:
        route = mock.get(TICKER_URL).respond(200, json=_body())
        result = await _cycle(sm, redis_client, http, settings, {})
    assert result.status == "locked"
    assert route.call_count == 0
    assert await redis_client.get(LOCK_KEY) == "someone-else"
    assert await _prices(sm) == {}


async def test_release_never_deletes_a_foreign_lock(
    sm: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    settings: Settings,
) -> None:
    async def hijack(pairs: Any) -> dict[str, Any]:
        await redis_client.set(LOCK_KEY, "other-owner", px=30_000)
        raise KrakenError("boom", retryable=False)

    result = await run_cycle(
        sessionmaker=sm, redis=redis_client, source=hijack, settings=settings, candidates={}
    )
    assert result.status == "source_error"
    assert await redis_client.get(LOCK_KEY) == "other-owner"


async def test_unexpected_exception_is_contained_and_lock_released(
    sm: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    settings: Settings,
) -> None:
    async def broken(pairs: Any) -> dict[str, Any]:
        raise RuntimeError("bug")

    result = await run_cycle(
        sessionmaker=sm, redis=redis_client, source=broken, settings=settings, candidates={}
    )
    assert result.status == "source_error"
    assert await redis_client.exists(LOCK_KEY) == 0


async def test_source_timeout_gives_source_error_and_releases_lock(
    sm: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    http: httpx.AsyncClient,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import asyncio

    monkeypatch.setattr(scheduler, "SOURCE_TIMEOUT_S", 0.05)

    async def slow(pairs: Any) -> dict[str, Any]:
        await asyncio.sleep(2)
        return {}

    result = await run_cycle(
        sessionmaker=sm, redis=redis_client, source=slow, settings=settings, candidates={}
    )
    assert result.status == "source_error"
    assert await redis_client.exists(LOCK_KEY) == 0
    assert scheduler.SOURCE_TIMEOUT_S < scheduler.LOCK_TTL_MS


def test_source_timeout_is_below_lock_ttl() -> None:
    assert scheduler.LOCK_TTL_MS > 35 * 1000
    assert scheduler.SOURCE_TIMEOUT_S == 35


async def test_redis_unavailable_gives_lock_error(
    sm: async_sessionmaker[AsyncSession],
    http: httpx.AsyncClient,
    settings: Settings,
) -> None:
    dead = Redis.from_url("redis://127.0.0.1:1/0", socket_connect_timeout=1)
    try:
        with _router() as mock:
            route = mock.get(TICKER_URL).respond(200, json=_body())
            result = await _cycle(sm, dead, http, settings, {})
    finally:
        await dead.aclose()
    assert result.status == "lock_error"
    assert route.call_count == 0
    assert await _prices(sm) == {}


async def test_release_failure_is_logged_not_raised(
    sm: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def failing_eval(*args: Any, **kwargs: Any) -> None:
        raise RedisError("gone")

    monkeypatch.setattr(redis_client, "eval", failing_eval)

    async def empty(pairs: Any) -> dict[str, Any]:
        return {}

    result = await run_cycle(
        sessionmaker=sm, redis=redis_client, source=empty, settings=settings, candidates={}
    )
    assert result.status == "ok"
    await redis_client.delete(LOCK_KEY)


async def test_no_active_coins_is_ok_without_source_call(
    sm: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    settings: Settings,
) -> None:
    async with sm() as s:
        await s.execute(update(Coin).values(is_active=False))
        await s.commit()
    called = False

    async def source(pairs: Any) -> dict[str, Any]:
        nonlocal called
        called = True
        return {}

    try:
        result = await run_cycle(
            sessionmaker=sm, redis=redis_client, source=source, settings=settings, candidates={}
        )
    finally:
        async with sm() as s:
            await s.execute(update(Coin).values(is_active=True))
            await s.commit()
    assert result == CycleResult("ok")
    assert not called


async def test_older_observation_does_not_move_as_of_back(
    sm: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    http: httpx.AsyncClient,
    settings: Settings,
) -> None:
    with _router() as mock:
        mock.get(TICKER_URL).respond(200, json=_body())
        await _cycle(sm, redis_client, http, settings, {}, NOW)
        before = await _prices(sm)
        await _cycle(sm, redis_client, http, settings, {}, NOW - timedelta(minutes=5))
    after = await _prices(sm)
    assert {k: (v.mid, v.as_of) for k, v in after.items()} == {
        k: (v.mid, v.as_of) for k, v in before.items()
    }


async def test_load_active_coins_and_upsert_directly(
    sm: async_sessionmaker[AsyncSession],
) -> None:
    ids = await _coin_ids(sm)
    async with sm() as s:
        coins = await load_active_coins(s)
        assert [c.symbol for c in coins][:2] == ["BTC", "ETH"]
        assert all(c.last_mid is None for c in coins)
        assert await upsert_prices(s, [], "kraken") == 0
        n = await upsert_prices(s, [AcceptedPrice(ids["BTC"], Decimal("1.5"), NOW)], "fake")
        assert n == 1
        newer = AcceptedPrice(ids["BTC"], Decimal("2.5"), NOW + timedelta(seconds=1))
        assert await upsert_prices(s, [newer], "kraken") == 1
        older = AcceptedPrice(ids["BTC"], Decimal("9"), NOW - timedelta(seconds=1))
        assert await upsert_prices(s, [older], "fake") == 0
        await s.commit()
    row = (await _prices(sm))["BTC"]
    assert (row.mid, row.source) == (Decimal("2.5"), "kraken")
    async with sm() as s:
        assert (await load_active_coins(s))[0].last_mid == Decimal("2.5")


async def test_build_source_fake_returns_seeded_pairs(
    sm: async_sessionmaker[AsyncSession], http: httpx.AsyncClient, settings: Settings
) -> None:
    fake_settings = settings.model_copy(update={"price_source": "fake"})
    source = build_source(fake_settings, http)
    async with sm() as s:
        pairs = [c.kraken_pair for c in await load_active_coins(s)]
    assert len(await source(pairs)) == 15


def test_build_source_fake_refused_in_prod(http: httpx.AsyncClient, settings: Settings) -> None:
    bad = settings.model_copy(update={"price_source": "fake", "env": "prod"})
    with pytest.raises(RuntimeError, match="not allowed in prod"):
        build_source(bad, http)


async def test_build_source_kraken_calls_fetch_tickers(
    http: httpx.AsyncClient, settings: Settings
) -> None:
    source = build_source(settings, http)
    with _router() as mock:
        route = mock.get(TICKER_URL).respond(200, json=_body())
        result = await source(["XXBTZUSD"])
    assert route.call_count == 1
    assert "XXBTZUSD" in result
