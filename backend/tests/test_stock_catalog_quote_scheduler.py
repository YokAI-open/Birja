"""Selected display requests use disposable PostgreSQL, Redis and mocked provider HTTP."""

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
import respx
from redis.asyncio import Redis
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import SchedulerSettings
from app.models.stock import StockQuote
from app.models.stock_catalog import StockCatalogAdmission
from app.services.alpaca import LATEST_QUOTES_URL
from app.services.stock_catalog_quote_demand import (
    CatalogQuoteOutcome,
    catalog_quote_key,
    pending_catalog_quotes,
    request_catalog_quote,
)
from app.services.stock_catalog_quotes import CatalogQuoteBinding, load_catalog_quote_context
from app.tasks import scheduler, stock_catalog_quotes, stock_halts, stock_scheduler
from tests.test_stock_catalog_publish import catalog_factory as catalog_factory
from tests.test_stock_catalog_quotes import seed_catalog_quote_fixture


@dataclass(frozen=True)
class Selected:
    sessions: async_sessionmaker[AsyncSession]
    redis: Redis
    settings: SchedulerSettings
    now: datetime
    binding: CatalogQuoteBinding

    @property
    def scope(self) -> dict[str, str]:
        return {
            "account": self.settings.stock_data_account,
            "server": self.settings.stock_data_server,
        }

    @property
    def cache_key(self) -> str:
        return catalog_quote_key(
            **self.scope,
            catalog_id=self.binding.catalog_id,
            listing_version=self.binding.listing_version,
            fingerprint=self.binding.fingerprint,
        )

    @property
    def queue(self) -> str:
        account = self.settings.stock_data_account.encode()
        return "sim:stock-catalog-demand:" + sha256(account).hexdigest()

    @property
    def account_window(self) -> str:
        account = self.settings.stock_data_account.encode()
        return stock_scheduler.ACCOUNT_WINDOW_PREFIX + sha256(account).hexdigest()

    async def request(self, catalog_id: int | None = None) -> CatalogQuoteOutcome:
        return await request_catalog_quote(
            self.redis,
            **self.scope,
            catalog_id=self.binding.catalog_id if catalog_id is None else catalog_id,
            listing_version=self.binding.listing_version,
            fingerprint=self.binding.fingerprint,
        )

    async def run(self, http: httpx.AsyncClient) -> scheduler.CycleResult:
        return await stock_catalog_quotes.run_catalog_quote_cycle(
            sessionmaker=self.sessions,
            redis=self.redis,
            http=http,
            settings=self.settings,
            now=lambda: self.now,
        )

    def quote_reply(self, request: httpx.Request) -> httpx.Response:
        assert request.url.params["symbols"] == self.binding.provider_symbol
        assert request.url.params["feed"] == "iex"
        assert request.url.params["currency"] == "USD"
        return httpx.Response(
            200,
            json={
                "quotes": {
                    self.binding.provider_symbol: {
                        "bp": 101,
                        "ap": 103,
                        "t": self.now.isoformat(),
                        "c": ["R"],
                        "bx": "V",
                        "ax": "V",
                        "bs": 1,
                        "as": 1,
                        "z": "C",
                    }
                }
            },
        )


@pytest_asyncio.fixture
async def selected(
    engine: AsyncEngine,
    catalog_factory: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    clean_stock_discovery: None,
) -> AsyncIterator[Selected]:
    sessions = catalog_factory
    account = "fixture-catalog-" + uuid4().hex
    settings = SchedulerSettings(
        env="test",
        database_url=str(engine.url),
        redis_url="redis://:test@127.0.0.1:56379/0",
        stock_data_enabled=True,
        stock_data_account=account,
        stock_data_server="fixture-server",
        alpaca_api_key="synthetic-key",
        alpaca_secret_key="synthetic-secret",
        stock_max_retries=1,
        price_source="fake",
    )
    now = datetime(2026, 11, 24, 14, 30, 1, tzinfo=UTC)
    async with sessions.begin() as db:
        catalog_id, version = await seed_catalog_quote_fixture(
            db, now, account=account, server=settings.stock_data_server, symbols_per_request=1
        )
    async with sessions() as db:
        ctx = await load_catalog_quote_context(db, settings, catalog_id, now=now)
    assert ctx.binding is not None, ctx.reason
    assert ctx.binding.listing_version == version
    state = Selected(sessions, redis_client, settings, now, ctx.binding)
    try:
        yield state
    finally:
        for pattern in (f"{state.queue}*", state.account_window):
            async for key in redis_client.scan_iter(match=pattern):
                await redis_client.delete(key)


async def one_request(
    state: Selected,
    responder: Callable[[httpx.Request], httpx.Response | Awaitable[httpx.Response]],
) -> tuple[scheduler.CycleResult, CatalogQuoteOutcome, int]:
    with respx.mock as mock:
        route = mock.get(LATEST_QUOTES_URL).mock(side_effect=responder)
        async with httpx.AsyncClient() as http, asyncio.TaskGroup() as group:
            waiting = group.create_task(state.request())
            async with asyncio.timeout(2):
                while not await pending_catalog_quotes(state.redis, **state.scope):  # noqa: ASYNC110
                    await asyncio.sleep(0.01)
            result = await state.run(http)
    return result, waiting.result(), route.call_count


async def test_only_selected_symbol_without_idle_transaction_or_financial_quote(selected: Selected):
    async def reply(request):
        async with selected.sessions() as db:
            idle = await db.scalar(
                text(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = "
                    "current_database() AND state = 'idle in transaction'"
                )
            )
        assert idle == 0
        return selected.quote_reply(request)

    async with selected.sessions() as db:
        before = await db.scalar(select(func.count()).select_from(StockQuote))
    await selected.redis.set(stock_scheduler.LOCK_KEY, "curated-lease", ex=30)
    assert await one_request(selected, reply) == (
        scheduler.CycleResult("ok", accepted=1),
        "ready",
        1,
    )
    raw = await selected.redis.get(selected.cache_key)
    assert raw is not None
    assert json.loads(raw)["mid"] == "102.00000000"
    async with selected.sessions() as db:
        assert await db.scalar(select(func.count()).select_from(StockQuote)) == before
    assert await selected.redis.zcard(selected.account_window) == 1
    assert await selected.redis.exists(stock_catalog_quotes.CATALOG_LOCK_KEY) == 0
    assert await selected.redis.get(stock_scheduler.LOCK_KEY) == "curated-lease"
    await selected.redis.delete(stock_scheduler.LOCK_KEY)


@pytest.mark.parametrize("prior_attempt", [False, True])
async def test_retries_reserve_the_same_account_window(selected: Selected, prior_attempt: bool):
    settings = selected.settings
    settings.stock_account_requests_per_minute = 2
    if prior_attempt:
        assert await stock_scheduler.reserve_account_attempt(
            selected.redis, settings, {}, at=selected.now
        )
    calls = 0

    def reply(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return selected.quote_reply(request)

    result, outcome, actual_attempts = await one_request(selected, reply)
    assert await selected.redis.zcard(selected.account_window) == 2
    assert actual_attempts == (1 if prior_attempt else 2)
    assert outcome == ("throttled" if prior_attempt else "ready")
    assert result.accepted == (0 if prior_attempt else 1)


async def test_retry_after_exceeding_cycle_preserves_throttle_reason(selected: Selected):
    result, outcome, calls = await one_request(
        selected, lambda _: httpx.Response(429, headers={"Retry-After": "30"})
    )
    assert (result.rejected, outcome, calls) == (1, "throttled", 1)
    assert await selected.redis.get(selected.cache_key) is None


@pytest.mark.parametrize("upstream_status", [200, 503])
async def test_recheck_discards_response_and_retries_after_committed_revocation(
    selected: Selected, upstream_status: int
):
    async def revoke(request):
        async with selected.sessions.begin() as db:
            await db.execute(
                update(StockCatalogAdmission)
                .where(StockCatalogAdmission.artifact == "alpaca_iex_quotes")
                .values(revoked_at=selected.now)
            )
        if upstream_status == 200:
            return selected.quote_reply(request)
        return httpx.Response(upstream_status)

    result, outcome, calls = await one_request(selected, revoke)
    assert (result.rejected, outcome, calls) == (1, "failed_check", 1)
    assert await selected.redis.get(selected.cache_key) is None
    assert await selected.redis.zcard(selected.account_window) == 1


async def test_pre_session_event_completes_without_price_or_replay(selected: Selected):
    async with selected.sessions() as db:
        ctx = await load_catalog_quote_context(
            db, selected.settings, selected.binding.catalog_id, now=selected.now
        )
    assert ctx.session.current is not None
    opens_at = ctx.session.current.opens_at
    assert opens_at is not None
    state = replace(selected, now=opens_at + timedelta(seconds=1))

    def pre_session_reply(request):
        reply = state.quote_reply(request)
        body = reply.json()
        body["quotes"][state.binding.provider_symbol]["t"] = (
            opens_at - timedelta(seconds=1)
        ).isoformat()
        return httpx.Response(200, json=body)

    result, outcome, calls = await one_request(state, pre_session_reply)
    assert (result.rejected, outcome, calls) == (1, "quote_unavailable", 1)
    assert await selected.redis.get(selected.cache_key) is None
    assert not await pending_catalog_quotes(selected.redis, **selected.scope)


async def test_expired_pending_request_is_not_replayed(selected: Selected):
    async def expire(_):
        pending_key = selected.cache_key.replace(":display:", ":pending:")
        assert await selected.redis.pexpire(pending_key, 1)
        return httpx.Response(503)

    result, outcome, calls = await one_request(selected, expire)
    assert (result.rejected, outcome, calls) == (1, "quote_unavailable", 1)
    assert await selected.redis.get(selected.cache_key) is None
    assert await selected.redis.zcard(selected.account_window) == 1


async def test_empty_or_disabled_cycle_does_no_provider_or_quota_work(selected: Selected):
    with respx.mock as mock:
        route = mock.get(LATEST_QUOTES_URL)
        async with httpx.AsyncClient() as http:
            assert await selected.run(http) == scheduler.CycleResult("ok")
            selected.settings.stock_data_enabled = False
            assert await selected.run(http) == scheduler.CycleResult("ok")
    assert not route.called
    assert await selected.redis.exists(selected.account_window) == 0


async def test_dispatch_reads_at_most_eight_pending_identities(selected: Selected):
    with respx.mock as mock:
        route = mock.get(LATEST_QUOTES_URL).mock(side_effect=selected.quote_reply)
        async with httpx.AsyncClient() as http, asyncio.TaskGroup() as group:
            work = [group.create_task(selected.request())]
            async with asyncio.timeout(2):
                while not await pending_catalog_quotes(selected.redis, **selected.scope):  # noqa: ASYNC110
                    await asyncio.sleep(0.01)
            for offset in range(1, 9):
                work.append(
                    group.create_task(selected.request(selected.binding.catalog_id + offset))
                )
            async with asyncio.timeout(2):
                while await selected.redis.zcard(selected.queue) < 9:  # noqa: ASYNC110
                    await asyncio.sleep(0.01)
            first = await selected.run(http)
            assert first.accepted + first.rejected == 8
            second = await selected.run(http)
            assert second.accepted + second.rejected == 1
    assert sum(job.result() == "ready" for job in work) == 1
    assert route.call_count == 1


async def test_reviewed_per_request_cap_leaves_selected_work_pending(selected: Selected):
    async with selected.sessions.begin() as db:
        second_id, _ = await seed_catalog_quote_fixture(
            db, selected.now, **selected.scope, ticker="FQB", symbols_per_request=1
        )
    async with selected.sessions() as db:
        ctx = await load_catalog_quote_context(db, selected.settings, second_id, now=selected.now)
    assert ctx.binding is not None, ctx.reason
    assert selected.binding.symbols_per_request == ctx.binding.symbols_per_request == 1
    second = replace(selected, binding=ctx.binding)
    selections = {state.binding.provider_symbol: state for state in (selected, second)}

    def reply(request):
        return selections[request.url.params["symbols"]].quote_reply(request)

    with respx.mock as mock:
        route = mock.get(LATEST_QUOTES_URL).mock(side_effect=reply)
        async with httpx.AsyncClient() as http, asyncio.TaskGroup() as group:
            waiters = [group.create_task(state.request()) for state in selections.values()]
            async with asyncio.timeout(2):
                while await selected.redis.zcard(selected.queue) < 2:  # noqa: ASYNC110
                    await asyncio.sleep(0.01)
            assert await selected.run(http) == scheduler.CycleResult("ok", accepted=1)
            assert len(await pending_catalog_quotes(selected.redis, **selected.scope)) == 1
            assert route.call_count == 1
            assert await selected.run(http) == scheduler.CycleResult("ok", accepted=1)
    assert [job.result() for job in waiters] == ["ready", "ready"]
    assert {call.request.url.params["symbols"] for call in route.calls} == set(selections)


async def test_catalog_backpressure_keeps_curated_and_crypto_ticks(
    selected: Selected, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    stopped, started, closed = asyncio.Event(), asyncio.Event(), asyncio.Event()
    crypto_ticks, curated_ticks = [], []
    real_run = scheduler.run

    async def crypto(**kwargs):
        crypto_ticks.append(True)
        return scheduler.CycleResult("ok")

    async def curated(**kwargs):
        if not kwargs["on_demand"]:
            curated_ticks.append(True)
            if len(curated_ticks) == 3:
                stopped.set()
        return scheduler.CycleResult("ok")

    async def slow_catalog(**kwargs):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            closed.set()

    async def no_halts(**kwargs):
        return scheduler.CycleResult("ok")

    async def accelerated(**kwargs):
        await real_run(**{**kwargs, "interval": 0.04, "heartbeat": tmp_path / "hb"})

    monkeypatch.setattr(scheduler, "get_scheduler_settings", lambda: selected.settings)
    monkeypatch.setattr(scheduler, "run", accelerated)
    monkeypatch.setattr(scheduler, "run_cycle", crypto)
    monkeypatch.setattr(stock_scheduler, "run_stock_cycle", curated)
    monkeypatch.setattr(stock_catalog_quotes, "run_catalog_quote_cycle", slow_catalog)
    monkeypatch.setattr(stock_halts, "run_stock_halt_cycle", no_halts)

    async with asyncio.timeout(2):
        await scheduler.amain(stopped)
    assert started.is_set() and closed.is_set()
    assert len(crypto_ticks) >= 2
    assert len(curated_ticks) == 3
