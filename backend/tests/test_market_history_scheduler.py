"""Use disposable datastore loops with bounded, synthetic provider responses."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256

import httpx
import pytest
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import SchedulerSettings
from app.models.stock import StockDataAdmission
from app.models.stock_catalog import StockCatalogAdmission, StockCatalogListing
from app.models.trade import Trade
from app.schemas.market_history import MarketHistoryQuery, MarketHistoryScopes
from app.services.kraken import TICKER_URL, fetch_tickers_isolated
from app.services.market_history_authority import resolve_history
from app.services.market_history_demand import _queue, complete_history, request_history
from app.services.market_history_providers import (
    COIN_METRICS_HISTORY_URL,
    IEX_BARS_URL,
    KRAKEN_OHLC_URL,
)
from app.tasks import market_history, stock_scheduler
from tests.helpers import put_price, sign_in, unique_email
from tests.test_market_history_api import BTC, URL, crypto_scope, scope_fields
from tests.test_market_history_api import history_server as history_server
from tests.test_market_history_providers import _row
from tests.test_stock_catalog_publish import catalog_factory as catalog_factory
from tests.test_stock_catalog_quotes import seed_catalog_quote_fixture

NOW = datetime(2026, 11, 24, 16, 2, tzinfo=UTC)
PAIR = "XXBTZUSD"


def schedule(settings, scope, account="birja", **kwargs) -> SchedulerSettings:
    return SchedulerSettings(
        env="test",
        database_url=settings.database_url,
        redis_url=settings.redis_url,
        stock_data_server=settings.stock_data_server,
        stock_data_account=account,
        market_history_scope_json=scope,
        **kwargs,
    )


def ticker_budget(*, initially_ready: bool = True):
    time = [0.0]
    tracker = market_history.KrakenHistoryBudget(60, monotonic=lambda: time[0])
    for _ in range(2 if initially_ready else 1):
        tracker.start_ticker()
        tracker.set_pairs([PAIR, "XETHZUSD"])
        tracker.record_ticker_attempt([PAIR, "XETHZUSD"])
        tracker.finish_ticker()
        time[0] += 60.0
    time[0] -= 58.0
    return tracker, time


async def enqueue(factory, redis, settings, query, now=NOW):
    async with factory() as db:
        authority = await resolve_history(db, settings, query, now)
    assert authority is not None
    result, _ = await request_history(
        redis,
        server=settings.stock_data_server,
        owner_id=7,
        query=query,
        fingerprint=authority.fingerprint,
    )
    assert result.state == "pending"
    return authority


def forbidden(_: httpx.Request) -> httpx.Response:
    pytest.fail("Unexpected provider request from an ineligible chart job")


async def test_production_history_switch_disallows_legacy_sources(db, settings, history_server):
    legacy = crypto_scope(NOW, history_server)
    config = schedule(settings, legacy).model_copy(update={"env": "prod"})
    query = MarketHistoryQuery.model_validate(BTC)
    assert not config.market_history_enabled
    assert await resolve_history(db, config, query, NOW) is None

    config.market_history_coin_metrics_enabled = True
    current = await resolve_history(db, config, query, NOW)
    assert current is not None and current.window.source == "coin_metrics"
    stock = MarketHistoryQuery.model_validate(
        {"instrument": {"kind": "featured", "symbol": "AAPL"}, "range": "1W"}
    )
    assert await resolve_history(db, config, stock, NOW) is None


async def test_coin_metrics_serves_authenticated_chart_and_honors_independent_quota(
    engine, settings, redis_client, history_server, auth_client, outbox, monkeypatch
) -> None:
    from app.api.v2 import market_history as api

    # Freeze the API and worker on the same window, with enough TTL for real Redis.
    now = datetime.now(UTC) + timedelta(minutes=2)

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now

    monkeypatch.setattr(api, "datetime", Clock)
    monkeypatch.setattr(settings, "market_history_coin_metrics_enabled", True)
    config = schedule(settings, None, market_history_coin_metrics_enabled=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    await sign_in(auth_client, outbox, unique_email())
    headers = {"X-CSRF-Token": auth_client.cookies["bj_csrf"]}
    assert (await auth_client.post(URL, json=BTC, headers=headers)).json()["state"] == "pending"
    authority = await enqueue(
        factory, redis_client, config, MarketHistoryQuery.model_validate(BTC), now
    )
    attempts = 0

    def upstream(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        assert str(request.url).split("?")[0] == COIN_METRICS_HISTORY_URL
        assert request.url.params["assets"] == "btc"
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "asset": "btc",
                        "time": (slot.start + authority.window.step).isoformat(),
                        "ReferenceRateUSD": "62000.12345678",
                    }
                    for slot in authority.window.slots
                ],
            },
        )

    quota_key = market_history._COIN_METRICS_QUOTA_KEY
    await redis_client.delete(quota_key)
    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as http:
            results = await market_history.run_history_cycle(
                sessionmaker=factory,
                redis=redis_client,
                quota_redis=redis_client,
                http=http,
                stock_http=None,
                settings=config,
                now=lambda: now,
            )
            assert results.accepted == 1
        response = await auth_client.post(URL, json=BTC, headers=headers)
        assert "no-store" in response.headers["cache-control"]
        body = response.json()
        assert body["state"] == "ready"
        assert body["series"]["source"] == "coin_metrics"
        assert body["series"]["points"][-1]["close"] == "62000.12345678"
        assert await redis_client.zcard(quota_key) == attempts == 1

        second_query = MarketHistoryQuery.model_validate({**BTC, "range": "1D"})
        await enqueue(factory, redis_client, config, second_query, now)
        limit = market_history._COIN_METRICS_REQUESTS_PER_MINUTE
        seconds, microseconds = await redis_client.time()
        timestamp = seconds * 1000 + microseconds // 1000
        await redis_client.zadd(quota_key, {f"prior-{index}": timestamp for index in range(limit)})
        async with httpx.AsyncClient(transport=httpx.MockTransport(forbidden)) as http:
            results = await market_history.run_history_cycle(
                sessionmaker=factory,
                redis=redis_client,
                quota_redis=redis_client,
                http=http,
                stock_http=None,
                settings=config,
                now=lambda: now,
            )
            assert results.accepted == 0 and results.rejected == 1
        response = await auth_client.post(URL, json={**BTC, "range": "1D"}, headers=headers)
        assert response.json()["state"] == "unavailable"
    finally:
        await redis_client.delete(quota_key)


async def test_kraken_history_publishes_once_and_keeps_current_price(
    engine,
    settings,
    redis_client,
    history_server,
    auth_client,
    outbox,
    monkeypatch,
    clean_prices,
) -> None:
    # A stable UTC minute groups the real authenticated browser reads and worker.
    from app.api.v2 import market_history as api

    now = datetime.now(UTC).replace(microsecond=0)
    time = [now]

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return time[0]

    monkeypatch.setattr(api, "datetime", Clock)
    scope = crypto_scope(now, history_server, retention_seconds=15)
    monkeypatch.setattr(settings, "market_history_scope_json", scope)
    config = schedule(settings, scope)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    await put_price(engine, "BTC", "75000", datetime.now(UTC))
    await sign_in(auth_client, outbox, unique_email())
    prices_before = (await auth_client.get("/api/v1/prices")).json()["items"]
    assert any(
        row["symbol"] == "BTC" and Decimal(row["price"]) == Decimal("75000")
        for row in prices_before
    )
    async with factory() as db:
        trades_before = await db.scalar(select(func.count(Trade.id)))
    headers = {"X-CSRF-Token": auth_client.cookies["bj_csrf"]}
    assert (await auth_client.post(URL, json=BTC, headers=headers)).json()["state"] == "pending"
    query = MarketHistoryQuery.model_validate(BTC)
    authority = await enqueue(factory, redis_client, config, query, now)
    tracker, _ = ticker_budget()
    count = 0

    def upstream(request: httpx.Request) -> httpx.Response:
        nonlocal count
        count += 1
        assert str(request.url).split("?")[0] == KRAKEN_OHLC_URL
        assert request.url.params["pair"] == PAIR
        rows = [_row(slot.start, "61000.00000001") for slot in authority.window.slots]
        rows.append(_row(authority.window.end_at, "80000"))
        return httpx.Response(200, json={"error": [], "result": {PAIR: rows, "last": 1}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as http:
        for accepted in (1, 0):
            result = await market_history.run_history_cycle(
                sessionmaker=factory,
                redis=redis_client,
                quota_redis=redis_client,
                http=http,
                stock_http=None,
                settings=config,
                tracker=tracker,
                now=lambda: now,
            )
            assert result.accepted == accepted
    assert count == 1
    body = (await auth_client.post(URL, json=BTC, headers=headers)).json()
    assert body["state"] == "ready" and body["series"]["source"] == "kraken"
    assert body["series"]["points"][-1]["close"] == "61000.00000001"
    assert all(point["close"] != "80000" for point in body["series"]["points"])
    key = f"{_queue(history_server)}:result:{authority.fingerprint}"
    assert 0 < await redis_client.pttl(key) <= 15000
    assert await redis_client.pexpiretime(key) == int(now.timestamp() * 1000) + 15000

    resolve = api.resolve_history
    checks = 0

    async def expire_during_check(*args):
        nonlocal checks
        outcome = await resolve(*args)
        checks += 1
        if checks == 2:
            time[0] += timedelta(seconds=16)
        return outcome

    monkeypatch.setattr(api, "resolve_history", expire_during_check)
    expired = await auth_client.post(URL, json=BTC, headers=headers)
    assert checks == 2 and expired.json() == {**BTC, "state": "unavailable", "series": None}
    prices_after = (await auth_client.get("/api/v1/prices")).json()["items"]
    assert [(row["symbol"], row["price"], row["as_of"]) for row in prices_after] == [
        (row["symbol"], row["price"], row["as_of"]) for row in prices_before
    ]
    async with factory() as db:
        assert await db.scalar(select(func.count(Trade.id))) == trades_before


@pytest.mark.parametrize(
    "reason", ["unknown", "due", "overlap", "revoked", "disabled", "ticker_after_reservation"]
)
async def test_kraken_history_defers_without_known_capacity_or_fresh_scope(
    reason,
    engine,
    settings,
    redis_client,
    history_server,
    monkeypatch,
) -> None:
    changes = {"aggregate_pair_requests_per_minute": 5} if reason == "overlap" else {}
    scope = crypto_scope(NOW, history_server, **changes)
    config = schedule(settings, scope)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    query = MarketHistoryQuery.model_validate(BTC)
    await enqueue(factory, redis_client, config, query)
    tracker, time = ticker_budget(initially_ready=reason != "unknown")
    if reason == "due":
        time[0] += 55
    if reason == "disabled":
        config.market_history_scope_json = None
    lease_checks = 0
    if reason == "ticker_after_reservation":
        current_history_job = market_history.current_history_job

        async def recheck_after_ticker(*args):
            nonlocal lease_checks
            result = await current_history_job(*args)
            lease_checks += 1
            if lease_checks == 2:
                tracker.record_ticker_attempt(["XETHZUSD"])
            return result

        monkeypatch.setattr(market_history, "current_history_job", recheck_after_ticker)
    at = NOW + timedelta(minutes=10) if reason == "revoked" else NOW
    async with httpx.AsyncClient(transport=httpx.MockTransport(forbidden)) as http:
        result = await market_history.run_history_cycle(
            sessionmaker=factory,
            redis=redis_client,
            quota_redis=redis_client,
            http=http,
            stock_http=None,
            settings=config,
            tracker=tracker,
            now=lambda: at,
        )
    assert result.status == "ok" and result.accepted == 0
    if reason == "ticker_after_reservation":
        assert lease_checks == 2


async def test_kraken_counts_each_retry_and_pair_fallback(settings, history_server) -> None:
    seen: list[str] = []
    timestamps = [0.0]
    tracker = market_history.KrakenHistoryBudget(60, monotonic=lambda: timestamps[0])
    pairs = [PAIR, "XETHZUSD"]

    async def no_sleep(seconds: float) -> None:
        timestamps[0] += seconds

    def upstream(request: httpx.Request) -> httpx.Response:
        assert str(request.url).split("?")[0] == TICKER_URL
        sent = request.url.params["pair"]
        seen.append(sent)
        result = (
            httpx.Response(503)
            if len(seen) == 1
            else httpx.Response(200, json={"error": ["Unknown asset pair"]})
            if len(seen) == 2
            else httpx.Response(200, json={"error": [], "result": {sent: {}}})
        )
        return result

    tracker.start_ticker()
    tracker.set_pairs(pairs)
    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as http:
        outcome = await fetch_tickers_isolated(
            http,
            pairs,
            sleep=no_sleep,
            jitter=lambda: 0,
            record_attempt=tracker.record_ticker_attempt,
        )
    tracker.finish_ticker()
    assert set(outcome) == set(pairs)
    assert seen == [",".join(pairs), ",".join(pairs), *pairs]
    assert len(tracker.attempts) == 4
    assert sum(PAIR in attempted for _, attempted in tracker.attempts) == 3


def test_kraken_ticker_priority_uses_fixed_cadence_after_late_wakeup(history_server) -> None:
    scope = crypto_scope(NOW, history_server).kraken
    assert scope is not None
    tracker, clock = ticker_budget()
    scheduled_start = tracker.next_due
    assert scheduled_start is not None
    clock[0] = scheduled_start + 3
    tracker.start_ticker()
    tracker.record_ticker_attempt([PAIR])
    tracker.finish_ticker()
    assert tracker.next_due == scheduled_start + 60
    clock[0] = scheduled_start + 55
    assert tracker.headroom(scope, PAIR) is None


def test_kraken_history_waits_one_second_after_any_ticker_attempt(history_server) -> None:
    scope = crypto_scope(NOW, history_server).kraken
    assert scope is not None
    tracker, clock = ticker_budget()
    # Another pair's fallback still uses the same request IP.
    tracker.record_ticker_attempt(["XETHZUSD"])
    last_attempt = clock[0]
    clock[0] = last_attempt + 0.999
    assert tracker.headroom(scope, PAIR) is None
    clock[0] = last_attempt + 1
    assert tracker.headroom(scope, PAIR) == (6, 7)


async def test_timed_out_history_demand_leaves_the_next_job_claimable(
    engine, settings, redis_client, history_server, monkeypatch
) -> None:
    config = schedule(settings, crypto_scope(NOW, history_server))
    factory = async_sessionmaker(engine, expire_on_commit=False)
    newest = MarketHistoryQuery.model_validate({**BTC, "range": "1D"})
    oldest = MarketHistoryQuery.model_validate(BTC)
    first = await enqueue(factory, redis_client, config, oldest)
    await enqueue(factory, redis_client, config, newest)
    await redis_client.zincrby(_queue(history_server), -500, first.fingerprint)
    attempted = []

    async def consume(_factory, cache, _quota, _http, _stock, _settings, job, _tracker, _now):
        attempted.append(job.query)
        if job.query == oldest:
            await asyncio.sleep(5)
        await complete_history(cache, history_server, job)
        return 0

    monkeypatch.setattr(market_history, "_consume", consume)
    monkeypatch.setattr(market_history, "_WALL_SECONDS", 0.1)
    async with httpx.AsyncClient(transport=httpx.MockTransport(forbidden)) as http:
        for status in ("source_error", "ok"):
            result = await market_history.run_history_cycle(
                sessionmaker=factory,
                redis=redis_client,
                quota_redis=redis_client,
                http=http,
                stock_http=None,
                settings=config,
            )
            assert result.status == status
    assert attempted == [oldest, newest]


async def test_kraken_reservations_share_the_seconds_and_minute_window(
    redis_client,
    history_server,
) -> None:
    scope = crypto_scope(NOW, history_server).kraken
    assert scope is not None
    tracker, _ = ticker_budget()
    assert await market_history._reserve_kraken(redis_client, scope, PAIR, tracker)
    assert not await market_history._reserve_kraken(redis_client, scope, PAIR, tracker)

    history_quota = "sim:history-quota:v1:kraken:" + sha256(history_server.encode()).hexdigest()
    seconds, micros = await redis_client.time()
    past = seconds * 1000 + micros // 1000 - 1500
    await redis_client.zadd(history_quota, {f"prior-{index}": past for index in range(6)})
    assert not await market_history._reserve_kraken(redis_client, scope, PAIR, tracker)
    assert await redis_client.zcard(history_quota) == 7


async def catalog_history(factory, settings, history_server, *, cap=20):
    async with factory.begin() as db:
        catalog_id, version = await seed_catalog_quote_fixture(
            db,
            NOW,
            account=history_server,
            server=history_server,
        )
        listing = await db.get(StockCatalogListing, version)
        assert listing is not None
        instrument = {
            "kind": "catalog",
            "catalog_id": str(catalog_id),
            "listing_version": str(version),
        }
        scope = MarketHistoryScopes.model_validate_json(
            json.dumps(
                {
                    "alpaca_iex": {
                        **scope_fields(NOW, history_server),
                        "account": history_server,
                        "admitted_requests_per_minute": cap,
                        "observed_requests_per_minute": 20,
                        "targets": [
                            {
                                "instrument": instrument,
                                "provider_symbol": listing.provider_symbol,
                                "provider_asset_id": listing.provider_asset_id,
                                "exchange": listing.listing_exchange,
                                "identity_since": (NOW - timedelta(days=45)).isoformat(),
                            }
                        ],
                    },
                }
            )
        )
    config = schedule(
        settings,
        scope,
        account=history_server,
        stock_data_enabled=True,
        alpaca_api_key="synthetic",
        alpaca_secret_key="synthetic",
    )
    return config, instrument, version


@pytest.mark.parametrize(("cap", "existing", "expected"), [(1, 0, 0), (5, 1, 1), (5, 0, 2)])
async def test_alpaca_pages_debit_the_shared_account_window(
    cap,
    existing,
    expected,
    catalog_factory,
    settings,
    redis_client,
    history_server,
) -> None:
    config, instrument, _ = await catalog_history(
        catalog_factory, settings, history_server, cap=cap
    )
    query = MarketHistoryQuery.model_validate({"instrument": instrument, "range": "1W"})
    authority = await enqueue(catalog_factory, redis_client, config, query)
    account_key = (
        stock_scheduler.ACCOUNT_WINDOW_PREFIX + sha256(history_server.encode()).hexdigest()
    )
    for _ in range(existing):
        assert await stock_scheduler.reserve_account_attempt(redis_client, config, {}, at=NOW)

    sent = 0

    def upstream(request: httpx.Request) -> httpx.Response:
        nonlocal sent
        sent += 1
        assert str(request.url).split("?")[0] == IEX_BARS_URL
        assert request.url.params["symbols"] == authority.provider_symbol
        assert request.url.params["adjustment"] == "split"
        if sent == 2:
            return httpx.Response(503)
        return httpx.Response(200, json={"bars": {}, "next_page_token": "next"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as http:
        result = await market_history.run_history_cycle(
            sessionmaker=catalog_factory,
            redis=redis_client,
            quota_redis=redis_client,
            http=http,
            stock_http=http,
            settings=config,
            now=lambda: NOW,
        )
    assert result.status == "ok" and result.accepted == 0 and sent == expected
    assert await redis_client.zcard(account_key) == existing + expected
    # Current quote/action attempts can still use the reserved part of the shared window.
    assert await stock_scheduler.reserve_account_attempt(redis_client, config, {}, at=NOW)


@pytest.mark.parametrize("change", ["mapping", "calendar"])
async def test_equity_rechecks_authority_before_publication(
    change,
    catalog_factory,
    settings,
    redis_client,
    history_server,
) -> None:
    config, instrument, version = await catalog_history(catalog_factory, settings, history_server)
    query = MarketHistoryQuery.model_validate({"instrument": instrument, "range": "1M"})
    authority = await enqueue(catalog_factory, redis_client, config, query)
    assert authority.window.identity_since is not None
    sent = 0

    async def upstream(request: httpx.Request) -> httpx.Response:
        nonlocal sent
        sent += 1
        assert request.url.params["symbols"] == authority.provider_symbol
        async with catalog_factory.begin() as db:
            listing = await db.get(StockCatalogListing, version)
            assert listing is not None
            if change == "mapping":
                await db.execute(
                    update(StockCatalogAdmission)
                    .where(
                        StockCatalogAdmission.id == listing.provider_admission_id,
                    )
                    .values(revoked_at=NOW)
                )
            else:
                await db.execute(
                    update(StockDataAdmission)
                    .where(
                        StockDataAdmission.product == "calendar",
                    )
                    .values(generation=StockDataAdmission.generation + 1)
                )
        return httpx.Response(
            200,
            json={
                "bars": {
                    authority.provider_symbol: [
                        {"c": 123, "t": authority.window.slots[-1].start.isoformat()}
                    ],
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as http:
        result = await market_history.run_history_cycle(
            sessionmaker=catalog_factory,
            redis=redis_client,
            quota_redis=redis_client,
            http=http,
            stock_http=http,
            settings=config,
            now=lambda: NOW,
        )
    assert result.status == "ok" and sent == 1 and result.accepted == 0
    assert not await redis_client.exists(f"{_queue(history_server)}:result:{authority.fingerprint}")
