"""Real PostgreSQL continuity; private provider traffic is always mocked."""

from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import pytest_asyncio
import respx
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import SchedulerSettings
from app.models.corporate_action import (
    StockActionEvent,
    StockActionObservation,
    StockActionRevision,
    StockActionSource,
    StockActionState,
    StockDividendEntitlement,
)
from app.models.stock import StockDataAdmission, StockInstrument
from app.tasks import stock_actions, stock_scheduler
from tests.test_stock_admission import action_admitted, admitted
from tests.test_stock_sessions import evidence


@pytest_asyncio.fixture(autouse=True)
async def clean_account_attempts(redis_client):
    async for key in redis_client.scan_iter(match=stock_scheduler.ACCOUNT_WINDOW_PREFIX + "*"):
        await redis_client.delete(key)
    yield
    async for key in redis_client.scan_iter(match=stock_scheduler.ACCOUNT_WINDOW_PREFIX + "*"):
        await redis_client.delete(key)


@pytest_asyncio.fixture
async def monitor(engine, clean_stock_discovery, redis_client):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)
    baseline = now - timedelta(days=2)
    async with factory.begin() as db:
        rows = (await db.execute(select(StockInstrument))).scalars().all()
        saved = [(r.coin_id, r.provider_asset_id, r.provider_verified_at) for r in rows]
        for row in rows:
            row.provider_asset_id = f"synthetic-{row.coin_id}"
            row.provider_verified_at = baseline - timedelta(days=1)
        for auth in (action_admitted(), evidence(now), admitted("reference")):
            db.add(
                StockDataAdmission(
                    **asdict(
                        replace(
                            auth,
                            reviewed_at=now - timedelta(hours=1),
                            valid_from=now - timedelta(hours=2),
                            valid_until=now + timedelta(hours=2),
                            quota={**auth.quota, "requests_per_minute": 200},
                        )
                    )
                )
            )
    settings = SchedulerSettings(
        env="test",
        database_url=str(engine.url),
        redis_url="redis://:test@127.0.0.1:56379/0",
        alpaca_api_key="synthetic",
        alpaca_secret_key="synthetic",
    )
    settings = settings.model_copy(
        update={
            "stock_actions_enabled": True,
            "stock_actions_coverage_start": baseline,
            "stock_actions_segment_days": 100,
        }
    )
    try:
        yield factory, settings, baseline
    finally:
        async with factory.begin() as db:
            for model in (StockActionObservation, StockDividendEntitlement):
                await db.execute(delete(model))
            await db.execute(update(StockActionEvent).values(current_revision_id=None))
            await db.execute(delete(StockActionRevision))
            await db.execute(delete(StockActionSource))
            await db.execute(delete(StockActionEvent))
            await db.execute(delete(StockActionState))
            for cid, pid, checked in saved:
                await db.execute(
                    update(StockInstrument)
                    .where(StockInstrument.coin_id == cid)
                    .values(provider_asset_id=pid, provider_verified_at=checked)
                )
        async for key in redis_client.scan_iter(match="sim:stock:actions:*"):
            await redis_client.delete(key)


async def states(factory):
    async with factory() as db:
        return (
            (await db.execute(select(StockActionState).order_by(StockActionState.coin_id)))
            .scalars()
            .all()
        )


async def cycle(monitor, redis, http):
    factory, settings, _ = monitor
    return await stock_actions.run_stock_action_cycle(
        sessionmaker=factory, redis=redis, http=http, settings=settings
    )


async def test_complete_snapshot_and_replay_publish_twenty_durable_current_states(
    monitor, redis_client
):
    with respx.mock(assert_all_called=False) as router:
        router.get("https://data.alpaca.markets/v1/corporate-actions").respond(
            200, json={"corporate_actions": {}, "next_page_token": None}
        )
        router.get(url__startswith="https://stream.data.alpaca.markets/").respond(
            200, content=b"", headers={"content-type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            result = await cycle(monitor, redis_client, http)
    rows = await states(monitor[0])
    assert len(rows) == 20
    assert all(row.health == "current" for row in rows), [
        (r.health, r.staged_continuation) for r in rows[:1]
    ]
    assert all(row.covered_until > monitor[2] for row in rows)
    assert result.status == "ok"


def routes(router, *, rest_status=200, replay_status=200, body=None):
    rest = router.get("https://data.alpaca.markets/v1/corporate-actions").respond(
        rest_status, json=body or {"corporate_actions": {}, "next_page_token": None}
    )
    replay = router.get(url__startswith="https://stream.data.alpaca.markets/").respond(
        replay_status, content=b"", headers={"content-type": "text/event-stream"}
    )
    return rest, replay


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500])
async def test_failed_replay_never_publishes_current(monitor, redis_client, status):
    with respx.mock(assert_all_called=False) as router:
        routes(router, replay_status=status)
        async with httpx.AsyncClient(trust_env=False) as http:
            result = await cycle(monitor, redis_client, http)
    rows = await states(monitor[0])
    assert result.status == "source_error"
    assert len(rows) == 20 and all(r.health == "reconciling" for r in rows)
    assert all(r.covered_until is None and r.valid_until is None for r in rows)


async def test_durable_segments_resume_until_future_horizon_complete(monitor, redis_client):
    factory, settings, _ = monitor
    settings.stock_actions_segment_days = 31
    with respx.mock(assert_all_called=False) as router:
        rest, _ = routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            starts = []
            for _index in range(2):
                await redis_client.delete(stock_actions.WINDOW_KEY)
                assert (await cycle(monitor, redis_client, http)).status == "source_error"
                rows = await states(factory)
                assert all(r.health == "reconciling" and r.valid_until is None for r in rows)
                starts.append(rest.calls.last.request.url.params["start"])
            await redis_client.delete(stock_actions.WINDOW_KEY)
            assert (await cycle(monitor, redis_client, http)).status == "ok"
            assert len(set(starts)) == 2
    assert all(r.health == "current" for r in await states(factory))


async def test_incomplete_pagination_keeps_start_and_records_continuation(monitor, redis_client):
    with respx.mock(assert_all_called=False) as router:
        routes(router, body={"corporate_actions": {}, "next_page_token": "same-page"})
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
    rows = await states(monitor[0])
    assert all(r.staged_continuation["next_date"] == monitor[2].date().isoformat() for r in rows)
    assert all(r.health == "reconciling" for r in rows)


@pytest.mark.parametrize("product", ["actions", "calendar", "reference"])
async def test_revoked_rights_create_no_http_or_monitor_authority(monitor, redis_client, product):
    async with monitor[0].begin() as db:
        await db.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == product)
            .values(collection_allowed=False)
        )
    with respx.mock() as router:
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
        assert not router.calls
    assert not await states(monitor[0])


async def test_disabled_needs_no_datastore_or_provider(monitor, redis_client):
    monitor[1].stock_actions_enabled = False
    async with httpx.AsyncClient(trust_env=False) as http:
        assert (await cycle(monitor, redis_client, http)).status == "ok"
    assert not await states(monitor[0])


@pytest.mark.parametrize("key", [stock_actions.LOCK_KEY, stock_actions.WINDOW_KEY])
async def test_duplicate_cycle_and_cadence_are_independently_owned(monitor, redis_client, key):
    await redis_client.set(key, "other", px=60000)
    async with httpx.AsyncClient(trust_env=False) as http:
        assert (await cycle(monitor, redis_client, http)).status == "locked"
    assert await redis_client.get(key) == "other"


async def test_shared_account_budget_counts_real_attempts_and_rejects_excess(monitor, redis_client):
    from app.tasks.stock_scheduler import _admissions, reserve_account_attempt

    settings = monitor[1]
    settings.stock_account_requests_per_minute = 2
    async with monitor[0]() as db:
        auth = await _admissions(db)
    assert await reserve_account_attempt(redis_client, settings, auth)
    with respx.mock(assert_all_called=False) as router:
        rest, replay = routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
            assert http.event_hooks["request"] == []
    assert rest.call_count == 1 and replay.call_count == 0
    assert all(row.health == "reconciling" for row in await states(monitor[0]))
    assert not await reserve_account_attempt(redis_client, settings, auth)


async def test_account_budget_is_atomic_across_concurrent_products(monitor, redis_client):
    import asyncio

    from app.tasks.stock_scheduler import _admissions, reserve_account_attempt

    settings = monitor[1]
    settings.stock_account_requests_per_minute = 3
    async with monitor[0]() as db:
        auth = await _admissions(db)
    results = await asyncio.gather(
        *(reserve_account_attempt(redis_client, settings, auth) for _ in range(12))
    )
    assert sum(results) == 3
    settings.stock_data_account = "other-account"
    assert await reserve_account_attempt(redis_client, settings, auth)


@pytest.mark.parametrize("phase", ["acquire", "release"])
async def test_redis_failure_is_bounded_and_sanitized(monitor, redis_client, monkeypatch, phase):
    from redis.exceptions import RedisError

    async def failed(*args, **kwargs):
        raise RedisError("private-credential-never-log")

    monkeypatch.setattr(redis_client, "set" if phase == "acquire" else "eval", failed)
    with respx.mock(assert_all_called=False) as router:
        routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            result = await cycle(monitor, redis_client, http)
    assert result.status == ("lock_error" if phase == "acquire" else "source_error")


async def test_hung_source_cancels_and_releases_only_own_lease(monitor, redis_client):
    import asyncio

    entered = asyncio.Event()

    async def hang(request):
        entered.set()
        await asyncio.Event().wait()

    with respx.mock(assert_all_called=False) as router:
        router.get("https://data.alpaca.markets/v1/corporate-actions").mock(side_effect=hang)
        async with httpx.AsyncClient(trust_env=False) as http:
            task = asyncio.create_task(cycle(monitor, redis_client, http))
            await asyncio.wait_for(entered.wait(), 3)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert http.event_hooks["request"] == []
    assert not await redis_client.exists(stock_actions.LOCK_KEY)
    assert all(r.health == "reconciling" for r in await states(monitor[0]))


async def test_health_deadline_never_outlives_reviewed_calendar(monitor, redis_client):
    reviewed_until = datetime.now(UTC) + timedelta(seconds=10)
    async with monitor[0].begin() as db:
        row = (
            await db.execute(
                select(StockDataAdmission).where(StockDataAdmission.product == "calendar")
            )
        ).scalar_one()
        row.calendar = {**row.calendar, "review_valid_until": reviewed_until.isoformat()}
    with respx.mock() as router:
        routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "ok"
    assert all(r.valid_until == reviewed_until for r in await states(monitor[0]))


def mixed_body():
    from uuid import UUID

    today = datetime.now(UTC).date()
    base = {
        "symbol": "AAPL",
        "cusip": "037833100",
        "process_date": today.isoformat(),
        "ex_date": (today + timedelta(days=2)).isoformat(),
    }
    return {
        "corporate_actions": {
            "cash_dividends": [
                {
                    **base,
                    "id": str(UUID(int=1)),
                    "rate": 1,
                    "currency": "USD",
                    "foreign": False,
                    "special": False,
                    "record_date": base["ex_date"],
                    "payable_date": (today + timedelta(days=5)).isoformat(),
                }
            ],
            "forward_splits": [{**base, "id": str(UUID(int=2)), "old_rate": 1, "new_rate": 2}],
            "reverse_splits": [{**base, "id": str(UUID(int=3)), "old_rate": 2, "new_rate": 1}],
        },
        "next_page_token": None,
    }


async def test_mixed_events_only_cash_dividends_receive_entitlement_derivation(
    monitor, redis_client
):
    from app.services.corporate_actions import persistent_action_holds

    with respx.mock() as router:
        routes(router, body=mixed_body())
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "ok"
    async with monitor[0]() as db:
        event = (await db.execute(select(StockActionEvent).limit(1))).scalar_one()
        assert await persistent_action_holds(db, event.coin_id)
    assert len(await states(monitor[0])) == 20


async def test_retained_old_ids_recheck_and_missing_hold_survives_recovery(monitor, redis_client):
    from app.services.corporate_actions import persistent_action_holds

    original = mixed_body()
    for group in original["corporate_actions"].values():
        for event in group:
            event["process_date"] = monitor[2].date().isoformat()
    phase = 0
    requests = []

    def respond(request):
        requests.append(dict(request.url.params))
        body = (
            original
            if phase == 0 or (phase == 2 and "ids" in request.url.params)
            else {"corporate_actions": {}, "next_page_token": None}
        )
        return httpx.Response(200, json=body)

    with respx.mock(assert_all_called=False) as router:
        routes(router)
        router.get("https://data.alpaca.markets/v1/corporate-actions").mock(side_effect=respond)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "ok"
            for phase in (1, 2):
                await redis_client.delete(stock_actions.WINDOW_KEY)
                result = await cycle(monitor, redis_client, http)
                assert result.status == ("source_error" if phase == 1 else "ok")
    known_requests = [request for request in requests if "ids" in request]
    assert len(known_requests) == 2
    assert all(set(request) == {"ids", "limit"} for request in known_requests)
    async with monitor[0]() as db:
        cid = (await db.execute(select(StockActionEvent.coin_id).limit(1))).scalar_one()
        assert "source_gap" in await persistent_action_holds(db, cid)
        assert (await db.get(StockActionState, cid)).health == "reconciling"


async def test_eight_attempt_rest_bound_resumes_token_after_process_restart(monitor, redis_client):
    def page(request):
        token = int(request.url.params.get("page_token", "0"))
        return httpx.Response(
            200,
            json={
                "corporate_actions": {},
                "next_page_token": str(token + 1) if token < 8 else None,
            },
        )

    with respx.mock(assert_all_called=False) as router:
        rest = router.get("https://data.alpaca.markets/v1/corporate-actions").mock(side_effect=page)
        replay = router.get(url__startswith="https://stream.data.alpaca.markets/").respond(
            200, content=b"", headers={"content-type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
        rows = await states(monitor[0])
        assert rest.call_count == 8 and replay.call_count == 0
        assert all(r.staged_continuation["continuation"] == "8" for r in rows)
        target = rows[0].staged_continuation["target_until"]
        await redis_client.delete(stock_actions.WINDOW_KEY)
        # New HTTP client and service invocation use SQL-only recovery state.
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "ok"
        assert rest.calls[8].request.url.params["page_token"] == "8"
        assert replay.calls.last.request.url.params["until"] == target
    assert all(r.health == "current" for r in await states(monitor[0]))


async def test_large_replay_gap_bisects_and_advances_only_completed_frontier(monitor, redis_client):
    monitor[1].stock_actions_max_response_bytes = 1024
    intervals = []

    def replay(request):
        start = datetime.fromisoformat(request.url.params["since"])
        end = datetime.fromisoformat(request.url.params["until"])
        intervals.append((start, end))
        body = b":" * 1025 if end - start > timedelta(days=1, seconds=1) else b""
        return httpx.Response(200, content=body, headers={"content-type": "text/event-stream"})

    with respx.mock(assert_all_called=False) as router:
        rest, _ = routes(router)
        router.get(url__startswith="https://stream.data.alpaca.markets/").mock(side_effect=replay)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
            first = (await states(monitor[0]))[0]
            assert first.staged_continuation["replay_frontier"] == monitor[2].isoformat()
            assert first.covered_until is None
            await redis_client.delete(stock_actions.WINDOW_KEY)
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
            second = (await states(monitor[0]))[0]
            assert second.covered_until is None
            assert second.staged_continuation["replay_frontier"] == intervals[1][1].isoformat()
            await redis_client.delete(stock_actions.WINDOW_KEY)
            assert (await cycle(monitor, redis_client, http)).status == "ok"
    assert rest.call_count == 1
    assert intervals[0][0] == intervals[1][0] == monitor[2]
    assert intervals[1][1] == intervals[2][0]  # Inclusive shared endpoint; no gap.
    assert intervals[0][1] == intervals[2][1]


async def test_unfinishable_same_instant_density_stays_explicitly_held(
    monitor, redis_client, monkeypatch
):
    fixed = datetime.now(UTC)
    monitor[1].stock_actions_coverage_start = fixed - timedelta(microseconds=1)
    monitor[1].stock_actions_max_response_bytes = 1024

    async def clock(db):
        return fixed

    monkeypatch.setattr(stock_actions, "_clock", clock)
    with respx.mock(assert_all_called=False) as router:
        routes(router)
        router.get(url__startswith="https://stream.data.alpaca.markets/").respond(
            200, content=b":" * 1025, headers={"content-type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
    rows = await states(monitor[0])
    assert all(r.staged_continuation["reason"] == "replay_density_limit" for r in rows)
    assert all(r.covered_until is None and r.health == "reconciling" for r in rows)


@pytest.mark.parametrize("problem", ["baseline", "future", "mapping", "journal"])
async def test_invalid_baseline_mapping_or_journal(monitor, redis_client, problem):
    factory, settings, baseline = monitor
    if problem == "baseline":
        settings.stock_actions_coverage_start = None
    elif problem == "future":
        settings.stock_actions_coverage_start = datetime.now(UTC) + timedelta(days=1)
    else:
        async with factory.begin() as db:
            if problem == "mapping":
                await db.execute(update(StockInstrument).values(provider_verified_at=None))
            else:
                cid = (await db.execute(select(StockInstrument.coin_id).limit(1))).scalar_one()
                db.add(StockActionState(coin_id=cid, admission_generation=4))
    with respx.mock() as router:
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
        assert not router.calls


@pytest.mark.parametrize("problem", ["permission", "lease"])
async def test_post_await_authority_or_lease_loss(monitor, redis_client, problem):
    async def response(request):
        if problem == "permission":
            async with monitor[0].begin() as db:
                await db.execute(
                    update(StockDataAdmission)
                    .where(StockDataAdmission.product == "actions")
                    .values(derived_allowed=False)
                )
        else:
            await redis_client.set(stock_actions.LOCK_KEY, "new-owner", px=60000)
        return httpx.Response(200, json={"corporate_actions": {}, "next_page_token": None})

    with respx.mock(assert_all_called=False) as router:
        router.get("https://data.alpaca.markets/v1/corporate-actions").mock(side_effect=response)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
    assert all(
        r.health == "reconciling" and r.valid_until is None for r in await states(monitor[0])
    )
    if problem == "lease":
        assert await redis_client.get(stock_actions.LOCK_KEY) == "new-owner"


@pytest.mark.parametrize("race", ["epoch", "delete", "covered", "permission", "expired"])
async def test_global_publication_race_rolls_back_all_twenty(
    monitor, redis_client, monkeypatch, race
):
    original = AsyncSession.execute
    clock = stock_actions._clock
    raced = False

    async def execute(db, statement, *args, **kwargs):
        nonlocal raced
        if (
            not raced
            and getattr(statement, "_for_update_arg", None) is not None
            and "stock_gate" not in db.info
            and "stock_action_state" in str(statement)
        ):
            raced = True
            async with monitor[0].begin() as other:
                cid = (
                    await other.execute(
                        select(StockActionState.coin_id).order_by(StockActionState.coin_id).limit(1)
                    )
                ).scalar_one()
                if race == "delete":
                    await other.execute(
                        delete(StockActionState).where(StockActionState.coin_id == cid)
                    )
                elif race == "permission":
                    await other.execute(
                        update(StockDataAdmission)
                        .where(StockDataAdmission.product == "actions")
                        .values(collection_allowed=False)
                    )
                elif race != "expired":
                    await other.execute(
                        update(StockActionState)
                        .where(StockActionState.coin_id == cid)
                        .values(
                            **(
                                {"epoch": StockActionState.epoch + 1}
                                if race == "epoch"
                                else {"covered_until": monitor[2]}
                            )
                        )
                    )
        return await original(db, statement, *args, **kwargs)

    async def checked_clock(db):
        value = await clock(db)
        return (
            value + timedelta(days=1)
            if race == "expired" and raced and "stock_gate" not in db.info
            else value
        )

    monkeypatch.setattr(AsyncSession, "execute", execute)
    monkeypatch.setattr(stock_actions, "_clock", checked_clock)
    with respx.mock() as router:
        routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
    assert raced
    assert all(
        r.health == "reconciling" and r.valid_until is None for r in await states(monitor[0])
    )


@pytest.mark.parametrize("overflow", ["known", "entitlements"])
async def test_event_capacity_refuses_without_silent_truncation(monitor, redis_client, overflow):
    from uuid import uuid4

    factory = monitor[0]
    async with factory.begin() as db:
        cid = (await db.execute(select(StockInstrument.coin_id).limit(1))).scalar_one()
        for _ in range(1001):
            event = StockActionEvent(
                coin_id=cid, economic_key=str(uuid4()), first_observed_at=datetime.now(UTC)
            )
            db.add(event)
            await db.flush()
            source = StockActionSource(
                event_id=event.id,
                provider="alpaca" if overflow == "known" else "synthetic",
                product="actions",
                provider_event_id=str(uuid4()),
            )
            db.add(source)
            await db.flush()
            if overflow == "entitlements":
                revision = StockActionRevision(
                    event_id=event.id,
                    source_id=source.id,
                    ordinal=1,
                    fingerprint="a" * 64,
                    mutation_kind="snapshot",
                    observed_at=datetime.now(UTC),
                    admission_generation=4,
                    normalized_terms={"event_type": "cash_dividend"},
                    classification="supported_dividend",
                    reason="synthetic capacity proof",
                )
                db.add(revision)
                await db.flush()
                event.current_revision_id = revision.id
    with respx.mock(assert_all_called=False) as router:
        routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
