"""Selected display requests use disposable PostgreSQL, Redis and mocked provider HTTP."""

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
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
from app.models.corporate_action import StockActionState
from app.models.stock import StockDataAdmission, StockQuote, StockSession
from app.models.stock_catalog import StockCatalogAdmission
from app.models.stock_catalog_finance import StockCatalogFinancialQuote
from app.models.trade import Holding
from app.services.alpaca import LATEST_QUOTES_URL
from app.services.stock_catalog_financial_quotes import (
    held_catalog_quote_page,
    load_catalog_financial_quote_context,
    read_catalog_financial_mark,
)
from app.services.stock_catalog_promotion import CatalogFinancialBinding
from app.services.stock_catalog_quote_demand import (
    CatalogQuoteOutcome,
    catalog_quote_key,
    pending_catalog_quotes,
    request_catalog_quote,
)
from app.services.stock_catalog_quotes import CatalogQuoteBinding, load_catalog_quote_context
from app.services.stock_sessions import build_sessions
from app.tasks import scheduler, stock_catalog_quotes, stock_halts, stock_scheduler
from tests.portfolio_fixtures import PortfolioWorld, seed_portfolio_world
from tests.test_stock_catalog_promotion import (
    ACCOUNT,
    FIRST_ASSET,
    OTHER_ASSET,
    SERVER,
    _listing,
    _promote,
    _reviewed_grant,
)
from tests.test_stock_catalog_promotion import finance_0025 as finance_0025
from tests.test_stock_catalog_promotion import finance_0026 as finance_0026
from tests.test_stock_catalog_publish import Factory, _manifest, _publish
from tests.test_stock_catalog_publish import catalog_factory as catalog_factory
from tests.test_stock_catalog_quotes import seed_catalog_quote_fixture
from tests.test_stock_sessions import evidence as calendar_evidence


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

    async def run(
        self, http: httpx.AsyncClient, *, quota_redis: Redis | None = None
    ) -> scheduler.CycleResult:
        return await stock_catalog_quotes.run_catalog_quote_cycle(
            sessionmaker=self.sessions,
            redis=self.redis,
            quota_redis=self.redis if quota_redis is None else quota_redis,
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
    *,
    quota_redis: Redis | None = None,
) -> tuple[scheduler.CycleResult, CatalogQuoteOutcome, int]:
    with respx.mock as mock:
        route = mock.get(LATEST_QUOTES_URL).mock(side_effect=responder)
        async with httpx.AsyncClient() as http, asyncio.TaskGroup() as group:
            waiting = group.create_task(state.request())
            async with asyncio.timeout(2):
                while not await pending_catalog_quotes(state.redis, **state.scope):  # noqa: ASYNC110
                    await asyncio.sleep(0.01)
            result = await state.run(http, quota_redis=quota_redis)
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


async def test_split_catalog_cache_keeps_one_quota_and_atomic_result(selected: Selected):
    state_redis = selected.redis
    selected.settings.stock_account_requests_per_minute = 1
    # Separate logical databases suffice here to detect incorrect client use.
    # The release Compose check separately verifies distinct Redis instances.
    cache_url = selected.settings.redis_url.rsplit("/", 1)[0] + "/1"
    async with Redis.from_url(cache_url, decode_responses=True) as cache:
        split = replace(selected, redis=cache)
        try:
            assert await stock_scheduler.reserve_account_attempt(
                state_redis, selected.settings, {}, at=selected.now
            )
            result, outcome, calls = await one_request(
                split, selected.quote_reply, quota_redis=state_redis
            )
            assert (result.accepted, outcome, calls) == (0, "throttled", 0)
            assert not await pending_catalog_quotes(cache, **selected.scope)
            assert await cache.get(selected.cache_key) is None

            await state_redis.delete(selected.account_window)
            async with asyncio.TaskGroup() as group:
                demand = group.create_task(
                    request_catalog_quote(
                        cache,
                        **selected.scope,
                        catalog_id=selected.binding.catalog_id,
                        listing_version=selected.binding.listing_version,
                        fingerprint=selected.binding.fingerprint,
                        purpose="financial",
                    )
                )
                async with asyncio.timeout(2):
                    while not await pending_catalog_quotes(cache, **selected.scope):  # noqa: ASYNC110
                        await asyncio.sleep(0.01)
                target = (selected.binding.catalog_id, selected.binding.listing_version)
                async with selected.sessions() as db:
                    assert target in await stock_halts._catalog_targets(
                        db, cache, stock_halts.CatalogHaltWindow(), selected.now, **selected.scope
                    )
                    assert target not in await stock_halts._catalog_targets(
                        db,
                        state_redis,
                        stock_halts.CatalogHaltWindow(),
                        selected.now,
                        **selected.scope,
                    )
                demand.cancel()
            async for key in cache.scan_iter(match=f"{selected.queue}*"):
                await cache.delete(key)

            result, outcome, calls = await one_request(
                split, selected.quote_reply, quota_redis=state_redis
            )
            assert (result.accepted, outcome, calls) == (1, "ready", 1)
            assert not await pending_catalog_quotes(cache, **selected.scope)
            assert await cache.get(selected.cache_key) is not None
            assert await cache.zcard(selected.account_window) == 0
            assert await state_redis.zcard(selected.account_window) == 1
            assert await state_redis.get(selected.cache_key) is None
            assert not await pending_catalog_quotes(state_redis, **selected.scope)
        finally:
            async for key in cache.scan_iter(match=f"{selected.queue}*"):
                await cache.delete(key)


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
    settings = selected.settings.model_copy(
        update={"catalog_quote_redis_url": "redis://127.0.0.1:56380/0"}
    )

    async def crypto(**kwargs):
        assert kwargs["redis"].connection_pool.connection_kwargs["port"] == 56379
        crypto_ticks.append(True)
        return scheduler.CycleResult("ok")

    async def curated(**kwargs):
        assert kwargs["redis"].connection_pool.connection_kwargs["port"] == 56379
        if not kwargs["on_demand"]:
            curated_ticks.append(True)
            if len(curated_ticks) == 3:
                stopped.set()
        return scheduler.CycleResult("ok")

    async def slow_catalog(**kwargs):
        assert kwargs["redis"].connection_pool.connection_kwargs["port"] == 56380
        assert kwargs["quota_redis"].connection_pool.connection_kwargs["port"] == 56379
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            closed.set()

    async def no_halts(**kwargs):
        assert kwargs["redis"].connection_pool.connection_kwargs["port"] == 56379
        assert kwargs["catalog_redis"].connection_pool.connection_kwargs["port"] == 56380
        return scheduler.CycleResult("ok")

    async def accelerated(**kwargs):
        await real_run(**{**kwargs, "interval": 0.04, "heartbeat": tmp_path / "hb"})

    monkeypatch.setattr(scheduler, "get_scheduler_settings", lambda: settings)
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


@dataclass(frozen=True)
class FinancialMarket:
    factory: Factory
    redis: Redis
    settings: SchedulerSettings
    now: datetime
    world: PortfolioWorld
    instruments: tuple[CatalogFinancialBinding, ...]

    async def request(self, instrument: CatalogFinancialBinding) -> CatalogQuoteOutcome:
        async with self.factory() as db:
            context = await load_catalog_financial_quote_context(
                db, self.settings, instrument.catalog_id, instrument.listing_id, self.now
            )
        assert context is not None
        return await request_catalog_quote(
            self.redis,
            account=ACCOUNT,
            server=SERVER,
            catalog_id=instrument.catalog_id,
            listing_version=instrument.listing_id,
            fingerprint=context.fingerprint,
            purpose="financial",
        )

    async def cycle(self, http: httpx.AsyncClient, *, cursor=None) -> scheduler.CycleResult:
        return await stock_catalog_quotes.run_catalog_quote_cycle(
            sessionmaker=self.factory,
            redis=self.redis,
            quota_redis=self.redis,
            http=http,
            settings=self.settings,
            now=lambda: self.now,
            cursor=cursor,
        )

    def reply(self, request: httpx.Request) -> httpx.Response:
        symbols = request.url.params["symbols"].split(",")
        return httpx.Response(
            200,
            json={
                "quotes": {
                    symbol: {
                        "bp": 101,
                        "ap": 103,
                        "t": self.now.isoformat(),
                        "c": ["R"],
                        "bx": "V",
                        "ax": "V",
                        "bs": 1,
                        "as": 1,
                        "z": "C" if symbol == "FQA" else "A",
                    }
                    for symbol in symbols
                }
            },
        )


@pytest_asyncio.fixture
async def financial_market(
    finance_0026: Factory, redis_client: Redis, engine: AsyncEngine
) -> AsyncIterator[FinancialMarket]:
    now = datetime(2026, 11, 24, 20, 59, tzinfo=UTC)
    origin = now - timedelta(minutes=10)
    publication = await _publish(finance_0026, _manifest(origin), None, now=origin)
    instruments = []
    for ticker, asset in (("FQA", FIRST_ASSET), ("FQN", OTHER_ASSET)):
        listing = await _listing(finance_0026, publication.generation_id, ticker)
        execution = await _reviewed_grant(finance_0026, listing, asset, origin)
        instruments.append(await _promote(finance_0026, listing, execution, origin))
    async with finance_0026.begin() as db:
        world = await seed_portfolio_world(await db.connection())
        calendar = calendar_evidence(now)
        db.add(StockDataAdmission(**asdict(calendar)))
        db.add_all(StockSession(**asdict(session)) for session in build_sessions(now, calendar))
        for instrument in instruments:
            db.add(
                StockCatalogAdmission(
                    artifact="catalog_mark",
                    reference="Synthetic financial mark scope",
                    is_fixture=True,
                    reviewed_at=origin,
                    valid_until=now + timedelta(minutes=20),
                    fields={
                        key: ["collection", "display", "derivation", "storage", "backup"]
                        for key in ("bid", "ask", "event_at", "collected_at")
                    },
                    scope={
                        "account": ACCOUNT,
                        "server": SERVER,
                        "feed": "iex",
                        "catalog_id": str(instrument.catalog_id),
                        "listing_id": str(instrument.listing_id),
                        "provider_asset_id": instrument.provider_asset_id,
                        "symbols_per_request": 1,
                    },
                )
            )
            await db.execute(
                update(StockActionState)
                .where(
                    StockActionState.coin_id == instrument.coin_id,
                )
                .values(health="current", checked_at=origin, valid_until=now + timedelta(hours=2))
            )
    settings = SchedulerSettings(
        env="test",
        database_url=str(engine.url),
        redis_url="redis://:test@127.0.0.1:56379/0",
        stock_data_enabled=True,
        stock_data_account=ACCOUNT,
        stock_data_server=SERVER,
        alpaca_api_key="synthetic-key",
        alpaca_secret_key="synthetic-secret",
        price_source="fake",
    )
    try:
        yield FinancialMarket(finance_0026, redis_client, settings, now, world, tuple(instruments))
    finally:
        digest = sha256(ACCOUNT.encode()).hexdigest()
        for pattern in (
            f"sim:stock-catalog-demand:{digest}*",
            stock_scheduler.ACCOUNT_WINDOW_PREFIX + digest,
        ):
            async for key in redis_client.scan_iter(match=pattern):
                await redis_client.delete(key)


async def _financial_request_and_tick(market, instrument, reply, *, cursor=None):
    with respx.mock as mock:
        quote = mock.get(LATEST_QUOTES_URL).mock(side_effect=reply)
        async with httpx.AsyncClient() as http, asyncio.TaskGroup() as group:
            waiting = group.create_task(market.request(instrument))
            async with asyncio.timeout(2):
                while not await pending_catalog_quotes(  # noqa: ASYNC110
                    market.redis, account=ACCOUNT, server=SERVER
                ):
                    await asyncio.sleep(0.01)
            result = await market.cycle(http, cursor=cursor)
    return result, waiting.result(), quote.call_count


async def test_catalog_financial_selection_retains_closed_mark_with_scope(financial_market):
    market = financial_market
    instrument = market.instruments[0]
    async with market.factory.begin() as db:
        execution = await db.get(StockCatalogAdmission, instrument.admission_id)
        assert execution is not None
        execution.valid_until = market.now + timedelta(minutes=2)
    assert await _financial_request_and_tick(market, instrument, market.reply) == (
        scheduler.CycleResult("ok", accepted=1),
        "ready",
        1,
    )
    async with market.factory.begin() as db:
        quote = await db.get(StockCatalogFinancialQuote, instrument.coin_id)
        assert quote is not None and quote.mark_admission_id is not None
        assert quote.execution_admission_id == instrument.admission_id
        # The Redis-independent reader has only a dated, permitted mark at close.
        at_close = market.now + timedelta(minutes=4)
        mark = await read_catalog_financial_mark(
            db,
            instrument.catalog_id,
            instrument.listing_id,
            at_close,
            allow_fixture=True,
        )
        assert mark is not None
        assert (mark.mode, mark.mid, mark.event_at) == ("closed", Decimal("102"), market.now)
        # The separately approved mark outlives the original execution lease.
        assert mark.valid_until == market.now + timedelta(minutes=20)
        assert (
            await read_catalog_financial_mark(
                db,
                instrument.catalog_id,
                instrument.listing_id,
                at_close,
            )
            is None
        )
        await db.execute(
            update(StockActionState)
            .where(StockActionState.coin_id == instrument.coin_id)
            .values(unit_epoch=quote.unit_epoch + 1)
        )
        assert (
            await read_catalog_financial_mark(
                db,
                instrument.catalog_id,
                instrument.listing_id,
                at_close,
                allow_fixture=True,
            )
            is None
        )
        await db.execute(
            update(StockActionState)
            .where(StockActionState.coin_id == instrument.coin_id)
            .values(unit_epoch=quote.unit_epoch)
        )
        permission = await db.get(StockCatalogAdmission, quote.mark_admission_id)
        assert permission is not None
        permission.revoked_at = at_close
        await db.flush()
        assert (
            await read_catalog_financial_mark(
                db,
                instrument.catalog_id,
                instrument.listing_id,
                at_close,
                allow_fixture=True,
            )
            is None
        )


async def test_catalog_held_cursor_favors_later_issues_after_first_quote_failure(financial_market):
    market = financial_market
    first, later = market.instruments
    async with market.factory.begin() as db:
        for instrument in (first, later):
            db.add(
                Holding(
                    coin_id=instrument.coin_id,
                    portfolio_id=market.world.first,
                    user_id=market.world.owner,
                    quantity=Decimal(1),
                    cost_basis=Decimal(101),
                )
            )
    cursor = stock_catalog_quotes.CatalogQuoteCursor()

    def reply(request):
        if request.url.params["symbols"] == first.provider_symbol:
            return httpx.Response(200, json={"quotes": {}})
        return market.reply(request)

    with respx.mock as mock:
        route = mock.get(LATEST_QUOTES_URL).mock(side_effect=reply)
        async with httpx.AsyncClient() as http:
            assert await market.cycle(http, cursor=cursor) == scheduler.CycleResult(
                "ok", rejected=1
            )
            assert await market.cycle(http, cursor=cursor) == scheduler.CycleResult(
                "ok", accepted=1
            )
            assert await market.cycle(http, cursor=cursor) == scheduler.CycleResult("ok")
        assert [call.request.url.params["symbols"] for call in route.calls] == ["FQA", "FQN"]
    async with market.factory.begin() as db:
        assert await db.get(StockCatalogFinancialQuote, first.coin_id) is None
        assert await db.get(StockCatalogFinancialQuote, later.coin_id) is not None
        await db.execute(
            update(Holding)
            .where(Holding.coin_id.in_([first.coin_id, later.coin_id]))
            .values(quantity=0, cost_basis=0)
        )
        assert not await held_catalog_quote_page(
            db,
            now=market.now + timedelta(minutes=2),
            after=None,
            limit=8,
        )


async def test_catalog_financial_transport_discards_quote_after_scope_revocation(financial_market):
    market = financial_market
    instrument = market.instruments[0]

    async def reply(request):
        async with market.factory.begin() as db:
            await db.execute(
                update(StockCatalogAdmission)
                .where(
                    StockCatalogAdmission.id == instrument.admission_id,
                )
                .values(revoked_at=market.now)
            )
        return market.reply(request)

    result, outcome, calls = await _financial_request_and_tick(market, instrument, reply)
    assert (result.rejected, outcome, calls) == (1, "quote_unavailable", 1)
    async with market.factory() as db:
        assert await db.get(StockCatalogFinancialQuote, instrument.coin_id) is None
