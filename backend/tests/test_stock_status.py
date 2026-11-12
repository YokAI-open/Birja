"""Finite synthetic status proofs do not activate a provider transport."""

from dataclasses import replace
from datetime import timedelta

import pytest

from app.services.stock_status_rules import StatusBatch, StatusEvent, normalize_status_batch
from app.services.stock_trading_rules import MAX_SAFE, status_current
from tests.stock_trade_fixtures import ownership as _ownership
from tests.stock_trade_fixtures import status_case as _status_case
from tests.stock_trade_fixtures import stock_trade_case as _stock_trade_case
from tests.test_stock_trading_rules import NOW

status_case = _status_case
stock_trade_case = _stock_trade_case
ownership = _ownership


def batch(**changes):
    fields = dict(
        events=(
            StatusEvent(
                16,
                "fixture-aapl",
                "normal",
                NOW - timedelta(hours=1),
                NOW.date(),
                10,
                "synthetic-baseline",
            ),
        ),
        observed_at=NOW,
        admission_generation=1,
        continuity_generation=1,
        baseline_verified=True,
        contiguous=True,
        complete=True,
        end_marker=True,
    )
    fields.update(changes)
    return StatusBatch(**fields)


def test_verified_complete_baseline_accepts_old_unchanged_normal_event():
    result = normalize_status_batch(
        batch(), {}, {16: "fixture-aapl"}, admission_until=NOW + timedelta(hours=1), now=NOW
    )[16]
    assert result.state == "normal"
    assert status_current(result, NOW)
    assert result.valid_until == NOW + timedelta(seconds=60)


def normalize(value, previous=None, *, now=NOW, deadline=None):
    return normalize_status_batch(
        value,
        previous or {},
        {16: "fixture-aapl"},
        admission_until=deadline or NOW + timedelta(hours=1),
        now=now,
    )[16]


@pytest.mark.parametrize(
    "change",
    [
        {"baseline_verified": False},
        {"baseline_verified": 1},
        {"complete": False},
        {"contiguous": False},
        {"end_marker": False},
        {"lost": True},
        {"reconnected": True},
        {"admission_generation": 0},
        {"continuity_generation": 0},
        {"admission_generation": True},
        {"observed_at": NOW + timedelta(seconds=1)},
        {"observed_at": NOW.replace(tzinfo=None)},
        {"events": ()},
    ],
)
def test_missing_or_ambiguous_proof_cannot_mint_normal(change):
    result = normalize(batch(**change))
    assert result.state == "unknown"
    assert not result.bootstrap_verified and not result.continuity_current
    assert result.valid_until is None


def test_strict_expiry_and_admission_cap():
    assert normalize(batch(), now=NOW + timedelta(seconds=60)).state == "unknown"
    assert normalize(batch(), deadline=NOW).state == "unknown"
    result = normalize(batch(), deadline=NOW + timedelta(seconds=12))
    assert result.valid_until == NOW + timedelta(seconds=12)
    assert not status_current(result, result.valid_until)


def test_duplicate_frame_is_idempotent_without_extending_lease():
    first = normalize(batch())
    assert normalize(batch(), {16: first}, now=NOW + timedelta(seconds=1)) == first


def test_contiguous_halt_and_explicit_resume_keep_monotone_source_order():
    first = normalize(batch())
    halted_frame = replace(batch().events[0], state="halted", event_at=NOW, sequence=11)
    halted = normalize(batch(events=(halted_frame,), baseline_verified=False), {16: first})
    assert halted.state == "halted" and status_current(halted, NOW)
    resumed_frame = replace(
        halted_frame, state="normal", event_at=NOW + timedelta(seconds=1), sequence=12
    )
    resumed = normalize(
        batch(
            events=(resumed_frame,), baseline_verified=False, observed_at=NOW + timedelta(seconds=1)
        ),
        {16: halted},
        now=NOW + timedelta(seconds=1),
    )
    assert resumed.state == "normal" and resumed.sequence == 12
    older = replace(resumed_frame, event_at=NOW - timedelta(seconds=1))
    refused = normalize(batch(events=(older,), baseline_verified=False), {16: halted})
    assert refused.state == "unknown" and refused.valid_until is None


@pytest.mark.parametrize("state", ["frozen", "halted"])
def test_later_hold_is_not_cleared_by_older_bootstrap(state):
    old = replace(normalize(batch()), state=state, event_at=NOW)
    result = normalize(batch(continuity_generation=2), {16: old})
    assert result.state == "unknown" and not result.continuity_current


def test_loss_clears_current_baseline_and_resume_needs_new_verified_baseline():
    normal = normalize(batch())
    lost = normalize(batch(lost=True), {16: normal})
    assert lost.state == "unknown" and lost.continuity_generation == 2
    frame = replace(batch().events[0], event_at=NOW, sequence=11)
    assert (
        normalize(
            batch(events=(frame,), baseline_verified=False, continuity_generation=2), {16: lost}
        ).state
        == "unknown"
    )
    restored = normalize(batch(events=(frame,), continuity_generation=3), {16: lost})
    assert restored.state == "normal" and restored.continuity_generation == 3


@pytest.mark.parametrize(
    "change",
    [
        {"state": "unreviewed-code"},
        {"state": "unknown"},
        {"sequence": True},
        {"sequence": MAX_SAFE + 1},
        {"coin_id": True},
        {"coin_id": 17},
        {"provider_asset_id": "another-asset"},
        {"event_at": NOW + timedelta(seconds=1)},
        {"event_at": NOW.replace(tzinfo=None)},
        {"source_ref": ""},
        {"source_ref": " " * 3000 + "x"},
    ],
)
def test_bad_frame_cannot_authorize_status(change):
    result = normalize(batch(events=(replace(batch().events[0], **change),)))
    assert result.state == "unknown" and not result.bootstrap_verified


def test_bounded_events_bytes_and_scope():
    frame = replace(batch().events[0], source_ref="x" * 2048)
    assert normalize(batch(events=(frame,) * 1001)).state == "unknown"
    assert (
        normalize(batch(events=tuple(replace(frame, sequence=i) for i in range(1000)))).state
        == "unknown"
    )
    with pytest.raises(ValueError, match="bounded"):
        normalize_status_batch(
            batch(),
            {},
            {i: str(i) for i in range(1, 22)},
            admission_until=NOW + timedelta(hours=1),
            now=NOW,
        )


def test_generation_cannot_wrap_on_loss():
    old = replace(normalize(batch()), continuity_generation=MAX_SAFE)
    with pytest.raises(ValueError, match="generation"):
        normalize(batch(lost=True), {16: old})


def persisted_batch(cid, now, **changes):
    return replace(
        batch(),
        events=(
            StatusEvent(
                cid,
                "synthetic-status-asset",
                "normal",
                now - timedelta(hours=1),
                now.date(),
                10,
                "synthetic-status-baseline",
            ),
        ),
        observed_at=now,
        admission_generation=4,
        **changes,
    )


async def test_real_status_persistence_and_restart_invalidation(status_case):
    from app.services.stock_status import invalidate_status, load_status, persist_status_batch

    factory, cid, now = status_case
    before = await financial_snapshot(factory)
    source = persisted_batch(cid, now)
    async with factory.begin() as db:
        saved = await persist_status_batch(db, source, coin_id=cid)
    assert saved.state == "normal" and status_current(saved, now)
    async with factory.begin() as db:
        assert await load_status(db, cid) == saved
        assert await persist_status_batch(db, source, coin_id=cid) == saved
    async with factory.begin() as db:
        assert await invalidate_status(db, cid)
    async with factory.begin() as db:
        lost = await load_status(db, cid)
        assert lost.state == "unknown" and lost.valid_until is None
        assert lost.continuity_generation == saved.continuity_generation + 1
        assert not await invalidate_status(db, cid)
    assert await financial_snapshot(factory) == before


@pytest.mark.parametrize(
    "change",
    [
        {"state": "denied"},
        {"retention_allowed": False},
        {"scope": {}},
        {"allowed_fields": []},
        {"generation": 5},
    ],
)
async def test_unadmitted_status_never_persists_normal(status_case, change):
    from sqlalchemy import update

    from app.models.stock import StockDataAdmission
    from app.services.stock_status import StatusUnavailable, load_status, persist_status_batch

    factory, cid, now = status_case
    before = await financial_snapshot(factory)
    async with factory.begin() as db:
        await db.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "status")
            .values(**change)
        )
    with pytest.raises(StatusUnavailable):
        async with factory.begin() as db:
            await persist_status_batch(db, persisted_batch(cid, now), coin_id=cid)
    async with factory() as db:
        assert await load_status(db, cid) is None
    assert await financial_snapshot(factory) == before


async def financial_snapshot(factory):
    from sqlalchemy import func, select

    from app.models.corporate_action import StockOwnershipMovement
    from app.models.trade import Holding, Trade
    from app.models.user import Account

    async with factory() as db:
        return tuple(
            (
                await db.execute(
                    select(
                        select(func.count(Account.id)).scalar_subquery(),
                        select(func.sum(Account.cash)).scalar_subquery(),
                        select(func.count(Trade.id)).scalar_subquery(),
                        select(func.sum(Holding.quantity)).scalar_subquery(),
                        select(func.sum(Holding.cost_basis)).scalar_subquery(),
                        select(func.count(StockOwnershipMovement.id)).scalar_subquery(),
                    )
                )
            ).one()
        )


async def test_shared_stock_fixture_has_real_independent_authority(stock_trade_case):
    from sqlalchemy import func, select

    from app.models.corporate_action import StockActionState
    from app.models.stock import StockDataAdmission, StockQuote, StockSession
    from app.services.stock_status import load_status

    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        assert (
            await db.execute(select(func.count()).select_from(StockDataAdmission))
        ).scalar_one() == 5
        assert (await db.execute(select(StockQuote.coin_id))).scalar_one() == cid
        assert (
            await db.execute(select(StockSession.calendar_admission_generation))
        ).scalar_one() == 4
        state = (
            await db.execute(select(StockActionState).where(StockActionState.coin_id == cid))
        ).scalar_one()
        assert state.complete_from is not None and state.journal_start_at is not None
        status = await load_status(db, cid)
        assert status_current(status, now)


async def test_stock_scheduler_default_invalidates_pre_restart_status(
    status_case, settings, redis_client
):
    import httpx

    from app.services.stock_status import load_status, persist_status_batch
    from app.tasks.stock_scheduler import run_stock_cycle

    factory, cid, now = status_case
    async with factory.begin() as db:
        await persist_status_batch(db, persisted_batch(cid, now), coin_id=cid)
    before = await financial_snapshot(factory)

    def no_http(request):
        raise AssertionError("Default status transport must not make provider calls")

    async with httpx.AsyncClient(transport=httpx.MockTransport(no_http)) as http:
        result = await run_stock_cycle(
            sessionmaker=factory,
            redis=redis_client,
            http=http,
            settings=settings.model_copy(update={"stock_data_enabled": False}),
        )
    assert result.status == "ok"
    async with factory() as db:
        status = await load_status(db, cid)
        assert status.state == "unknown" and not status.continuity_current
    assert await financial_snapshot(factory) == before


@pytest.mark.parametrize("case", ["same_generation_change", "expiry"])
async def test_permission_change_or_expiry_during_real_write_wait_rolls_back(status_case, case):
    import asyncio

    from sqlalchemy import select, text, update

    from app.models.stock import StockDataAdmission
    from app.models.stock_execution import StockStatusEvidence
    from app.services.stock_status import StatusUnavailable, load_status, persist_status_batch

    factory, cid, now = status_case
    before = await financial_snapshot(factory)
    source = persisted_batch(cid, now)
    async with factory.begin() as db:
        saved = await persist_status_batch(db, source, coin_id=cid)
    frame = replace(source.events[0], sequence=11, event_at=now - timedelta(minutes=30))
    pending = replace(source, events=(frame,), baseline_verified=False)
    if case == "expiry":
        async with factory.begin() as db:
            await db.execute(
                text("""UPDATE stock_data_admissions
                SET valid_until=clock_timestamp()+interval '3 seconds' WHERE product='status'""")
            )

    async def writer():
        reason = (
            "authority_changed" if case == "same_generation_change" else "admission_unavailable"
        )
        with pytest.raises(StatusUnavailable, match=reason):
            async with factory.begin() as db:
                await db.execute(text("SET LOCAL application_name='birja-status-wait-test'"))
                await persist_status_batch(db, pending, coin_id=cid)

    task = None
    try:
        async with factory.begin() as blocker:
            await blocker.execute(
                select(StockStatusEvidence.coin_id)
                .where(StockStatusEvidence.coin_id == cid)
                .with_for_update()
            )
            task = asyncio.create_task(writer())
            async with asyncio.timeout(5):
                while True:
                    if task.done():
                        await task
                        raise AssertionError("Status writer did not reach the row wait")
                    async with factory() as observer:
                        waiting = (
                            await observer.execute(
                                text("""SELECT EXISTS(
                            SELECT FROM pg_stat_activity
                            WHERE application_name='birja-status-wait-test'
                            AND wait_event_type='Lock')""")
                            )
                        ).scalar_one()
                    if waiting:
                        break
                    await asyncio.sleep(0.01)
            if case == "same_generation_change":
                async with factory.begin() as editor:
                    await editor.execute(
                        update(StockDataAdmission)
                        .where(StockDataAdmission.product == "status")
                        .values(attribution="changed-synthetic-attribution")
                    )
            else:
                await blocker.execute(text("SELECT pg_sleep(3.1)"))
    finally:
        if task is not None:
            await asyncio.wait_for(task, 5)
    async with factory() as db:
        assert await load_status(db, cid) == saved
    assert await financial_snapshot(factory) == before
