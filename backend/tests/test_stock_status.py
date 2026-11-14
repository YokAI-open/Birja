"""Finite synthetic status proofs do not activate a provider transport."""

from dataclasses import replace
from datetime import timedelta

import pytest

from app.services.stock_status_rules import (
    StatusBatch,
    StatusEvent,
    normalize_status_batch,
    status_batch_within_bounds,
)
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


@pytest.mark.parametrize(
    "value",
    [
        None,
        batch(events=()),
        batch(admission_generation=True),
        batch(events=(replace(batch().events[0], source_ref="x" * 2049),)),
    ],
)
def test_untrusted_finite_envelope_is_rejected_before_partitioning(value):
    assert not status_batch_within_bounds(value)


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
        assert set(
            (await db.scalars(select(StockSession.calendar_admission_generation))).all()
        ) == {4}
        state = (
            await db.execute(select(StockActionState).where(StockActionState.coin_id == cid))
        ).scalar_one()
        assert state.complete_from is not None and state.journal_start_at is not None
        status = await load_status(db, cid)
        assert status_current(status, now)


async def test_real_snapshot_requires_all_independent_evidence(stock_trade_case, settings):
    from decimal import Decimal

    from app.services.stock_eligibility import load_execution_evidence

    factory, cid, uid, now = stock_trade_case
    before = await financial_snapshot(factory)
    async with factory() as db:
        loaded = await load_execution_evidence(db, cid, settings)
    assert loaded.decision.allowed, loaded.decision.reason
    assert loaded.evidence.quote.bid == Decimal("100")
    assert loaded.evidence.quote.ask == Decimal("102")
    assert loaded.evidence.status.state == "normal"
    assert {a.product for a in loaded.evidence.admissions} == {
        "reference",
        "quotes",
        "actions",
        "status",
        "calendar",
    }
    assert all(a.approved and len(a.row_hash) == 64 for a in loaded.evidence.admissions)
    assert loaded.decision.valid_until <= now + timedelta(seconds=60)
    assert await financial_snapshot(factory) == before


@pytest.mark.parametrize("product", ["quotes", "status"])
async def test_expired_source_retention_is_not_executable(stock_trade_case, settings, product):
    from sqlalchemy import text

    from app.services.stock_eligibility import load_execution_evidence

    factory, cid, uid, now = stock_trade_case
    async with factory.begin() as db:
        await db.execute(
            text("""UPDATE stock_data_admissions
            SET quota=jsonb_set(quota,'{retention_seconds}','1') WHERE product=:product"""),
            {"product": product},
        )
        if product == "quotes":
            await db.execute(
                text("""UPDATE stock_quotes SET event_at=event_at-interval '2 seconds',
                collected_at=collected_at-interval '2 seconds'""")
            )
        else:
            await db.execute(
                text("""UPDATE stock_status_evidence
                SET observed_at=observed_at-interval '2 seconds',
                    valid_until=observed_at+interval '58 seconds'""")
            )
    async with factory() as db:
        loaded = await load_execution_evidence(db, cid, settings)
    assert not loaded.decision.allowed and loaded.decision.reason == "permission_unavailable"
    if product == "status":
        from app.services.stocks import list_stocks

        async with factory() as db:
            view = await list_stocks(db, settings)
        assert next(item for item in view.items if item.id == cid).status.state == "unknown"


async def test_eligibility_deadline_includes_source_retention(stock_trade_case, settings):
    from sqlalchemy import text

    from app.services.stock_eligibility import load_execution_evidence

    factory, cid, uid, now = stock_trade_case
    async with factory.begin() as db:
        await db.execute(
            text("""UPDATE stock_data_admissions
            SET quota=jsonb_set(quota,'{retention_seconds}','10') WHERE product='quotes'""")
        )
    async with factory() as db:
        loaded = await load_execution_evidence(db, cid, settings)
    assert loaded.decision.allowed
    assert loaded.decision.valid_until <= now + timedelta(seconds=10)


@pytest.mark.parametrize("product", ["reference", "quotes", "actions", "status", "calendar"])
async def test_current_display_rights_do_not_grant_durable_receipts(
    stock_trade_case, settings, product
):
    from sqlalchemy import text

    from app.services.stock_eligibility import load_execution_evidence

    factory, cid, uid, now = stock_trade_case
    async with factory.begin() as db:
        await db.execute(
            text("""UPDATE stock_data_admissions
            SET scope=scope-'durable_accounting' WHERE product=:product"""),
            {"product": product},
        )
    async with factory() as db:
        loaded = await load_execution_evidence(db, cid, settings)
    assert not loaded.decision.allowed and loaded.decision.reason == "permission_unavailable"


async def test_short_term_halt_display_does_not_grant_receipt_rights(stock_trade_case, settings):
    from sqlalchemy import text

    from app.services.stocks import list_stocks

    factory, cid, uid, now = stock_trade_case
    async with factory.begin() as db:
        await db.execute(
            text("""UPDATE stock_data_admissions
            SET scope=scope-'durable_accounting' WHERE product='status'""")
        )
        await db.execute(text("UPDATE stock_status_evidence SET state='halted'"))
    async with factory() as db:
        result = await list_stocks(db, settings)
    item = next(item for item in result.items if item.id == cid)
    assert item.status.state == "halted" and item.quote is not None
    assert not item.execution_enabled and item.execution_reason == "permission_unavailable"


@pytest.mark.parametrize(
    "sql,reason",
    [
        ("UPDATE stock_status_evidence SET state='halted'", "halted"),
        ("UPDATE stock_status_evidence SET state='frozen'", "frozen"),
        ("UPDATE stock_status_evidence SET continuity_current=false", "status_unavailable"),
        (
            "UPDATE stock_status_evidence SET state='unknown', bootstrap_verified=false, "
            "continuity_current=false, valid_until=NULL, event_at=NULL, observed_at=NULL, "
            "session_date=NULL",
            "status_unavailable",
        ),
        (
            "UPDATE stock_status_evidence SET valid_until=observed_at+interval '1 microsecond'",
            "status_unavailable",
        ),
        ("UPDATE stock_action_state SET health='reconciling'", "action_unavailable"),
        ("UPDATE stock_action_state SET next_blocking_at=clock_timestamp()", "action_unavailable"),
        ("UPDATE stock_quotes SET unit_epoch=1", "units_changed"),
        ("UPDATE stock_quotes SET event_at=event_at-interval '120 seconds'", "quote_stale"),
        ("UPDATE stock_quotes SET admission_generation=5", "quote_unavailable"),
        (
            "UPDATE stock_data_admissions SET display_allowed=false WHERE product='quotes'",
            "permission_unavailable",
        ),
        (
            "UPDATE stock_instruments SET provider_verified_at=NULL "
            "WHERE provider_asset_id='synthetic-status-asset'",
            "permission_unavailable",
        ),
        ("UPDATE stock_sessions SET opens_at=opens_at-interval '1 second'", "session_unavailable"),
    ],
)
async def test_snapshot_refusals_never_authorize_or_change_finances(
    stock_trade_case, settings, sql, reason
):
    from sqlalchemy import text

    from app.services.stock_eligibility import load_execution_evidence

    factory, cid, uid, now = stock_trade_case
    before = await financial_snapshot(factory)
    async with factory.begin() as db:
        await db.execute(text(sql))
    async with factory() as db:
        loaded = await load_execution_evidence(db, cid, settings)
    assert not loaded.decision.allowed and loaded.decision.reason == reason
    assert loaded.decision.evidence is None
    assert await financial_snapshot(factory) == before


async def test_discovery_reports_verified_status_and_full_eligibility(stock_trade_case, settings):
    from app.services.stocks import list_stocks

    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        result = await list_stocks(db, settings)
    item = next(item for item in result.items if item.id == cid)
    assert item.status.state == "normal"
    assert item.execution_enabled and item.execution_reason == "available"
    assert item.quote is not None and item.session.state == "open"


@pytest.mark.parametrize("stock_trade_case", ["closed"], indirect=True)
async def test_verified_closed_calendar_denies_execution(stock_trade_case, settings):
    from app.services.stock_eligibility import load_execution_evidence
    from app.services.stocks import list_stocks

    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        loaded = await load_execution_evidence(db, cid, settings)
        result = await list_stocks(db, settings)
    assert not loaded.decision.allowed and loaded.decision.reason == "market_closed"
    item = next(item for item in result.items if item.id == cid)
    assert item.session.state == "closed" and item.status.state == "normal"
    assert not item.execution_enabled and item.execution_reason == "market_closed"


async def test_verified_halt_does_not_override_action_uncertainty(stock_trade_case, settings):
    from sqlalchemy import text

    from app.services.stocks import list_stocks

    factory, cid, uid, now = stock_trade_case
    async with factory.begin() as db:
        await db.execute(text("UPDATE stock_status_evidence SET state='halted'"))
        await db.execute(text("UPDATE stock_action_state SET health='reconciling'"))
    async with factory() as db:
        result = await list_stocks(db, settings)
    item = next(item for item in result.items if item.id == cid)
    assert item.status.state == "halted" and item.quote is None
    assert not item.execution_enabled and item.execution_reason == "action_unavailable"


async def test_finite_scheduler_source_reaches_authenticated_discovery(
    stock_trade_case, settings, auth_client, outbox
):
    from app.tasks.stock_status import run_stock_status_cycle
    from tests.helpers import sign_in, unique_email

    factory, cid, uid, now = stock_trade_case
    await sign_in(auth_client, outbox, unique_email("finite-status"))
    before = await financial_snapshot(factory)
    assert (await run_stock_status_cycle(factory)).rejected == 1
    source = persisted_batch(cid, now, continuity_generation=3)
    result = await run_stock_status_cycle(factory, source, settings=settings)
    assert result.status == "ok" and result.accepted == 1
    response = await auth_client.get("/api/v1/stocks")
    assert response.status_code == 200
    item = next(item for item in response.json()["items"] if item["id"] == cid)
    assert item["status"]["state"] == "normal" and item["execution_enabled"]
    assert item["execution_reason"] == "available"
    assert await financial_snapshot(factory) == before


@pytest.mark.parametrize(
    "change", [{"lost": True}, {"reconnected": True}, {"complete": False}, {"end_marker": False}]
)
async def test_incomplete_finite_source_clears_prior_continuity(status_case, settings, change):
    from app.services.stock_status import load_status, persist_status_batch
    from app.tasks.stock_status import run_stock_status_cycle

    factory, cid, now = status_case
    source = persisted_batch(cid, now)
    async with factory.begin() as db:
        await persist_status_batch(db, source, coin_id=cid)
    before = await financial_snapshot(factory)
    result = await run_stock_status_cycle(factory, replace(source, **change), settings=settings)
    assert result.status == "source_error" and result.rejected == 1
    async with factory() as db:
        status = await load_status(db, cid)
        assert status.state == "unknown" and not status.continuity_current
    assert await financial_snapshot(factory) == before


async def test_finite_source_is_not_a_production_configuration_path(status_case, settings):
    from app.services.stock_status import load_status
    from app.tasks.stock_status import run_stock_status_cycle

    factory, cid, now = status_case
    with pytest.raises(ValueError, match="test settings"):
        await run_stock_status_cycle(
            factory, persisted_batch(cid, now), settings=settings.model_copy(update={"env": "prod"})
        )
    async with factory() as db:
        assert await load_status(db, cid) is None


async def test_total_batch_limit_applies_before_partitioning(status_case, settings):
    from sqlalchemy import select

    from app.models.stock import StockInstrument
    from app.services.stock_status import load_status, persist_status_batch
    from app.tasks.stock_status import run_stock_status_cycle

    factory, cid, now = status_case
    source = persisted_batch(cid, now)
    async with factory.begin() as db:
        await persist_status_batch(db, source, coin_id=cid)
        ids = (
            await db.scalars(select(StockInstrument.coin_id).order_by(StockInstrument.coin_id))
        ).all()
    events = tuple(
        replace(source.events[0], coin_id=instrument, sequence=i, source_ref="x" * 2048)
        for instrument in ids
        for i in range(50)
    )
    assert len(events) == 1000
    result = await run_stock_status_cycle(
        factory, replace(source, events=events, continuity_generation=2), settings=settings
    )
    assert result.status == "source_error" and result.rejected == 1
    async with factory() as db:
        assert (await load_status(db, cid)).state == "unknown"


async def test_terminal_generation_removes_authority_without_wrapping(status_case):
    from app.services.stock_status import invalidate_status, load_status, persist_status_batch

    factory, cid, now = status_case
    async with factory.begin() as db:
        await persist_status_batch(
            db, persisted_batch(cid, now, continuity_generation=MAX_SAFE), coin_id=cid
        )
    async with factory.begin() as db:
        assert await invalidate_status(db, cid)
    async with factory() as db:
        value = await load_status(db, cid)
        assert value.continuity_generation == MAX_SAFE
        assert value.state == "unknown" and value.valid_until is None
        assert not value.bootstrap_verified and not value.continuity_current


async def test_status_lease_is_capped_by_retention(status_case):
    from sqlalchemy import text

    from app.services.stock_status import persist_status_batch

    factory, cid, now = status_case
    async with factory.begin() as db:
        await db.execute(
            text("""UPDATE stock_data_admissions
            SET quota=jsonb_set(quota,'{retention_seconds}','1') WHERE product='status'""")
        )
        result = await persist_status_batch(db, persisted_batch(cid, now), coin_id=cid)
    assert result.valid_until <= now + timedelta(seconds=1)


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


@pytest.mark.parametrize(
    "case", ["same_generation_change", "mapping_change", "expiry", "lease_expiry"]
)
async def test_permission_change_or_expiry_during_real_write_wait_rolls_back(status_case, case):
    import asyncio

    from sqlalchemy import select, text, update

    from app.models.stock import StockDataAdmission, StockInstrument
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
    elif case == "lease_expiry":
        async with factory.begin() as db:
            await db.execute(
                text("""UPDATE stock_data_admissions
                SET quota=jsonb_set(quota,'{retention_seconds}','3') WHERE product='status'""")
            )

    async def writer():
        reason = {
            "same_generation_change": "authority_changed",
            "mapping_change": "authority_changed",
            "expiry": "admission_unavailable",
            "lease_expiry": "status_expired",
        }[case]
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
            elif case == "mapping_change":
                async with factory.begin() as editor:
                    await editor.execute(
                        update(StockInstrument)
                        .where(StockInstrument.coin_id == cid)
                        .values(provider_asset_id="synthetic-replaced-asset")
                    )
            else:
                await blocker.execute(text("SELECT pg_sleep(3.1)"))
    finally:
        if task is not None:
            await asyncio.wait_for(task, 5)
    async with factory() as db:
        assert await load_status(db, cid) == saved
    assert await financial_snapshot(factory) == before


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM stock_data_admissions WHERE product='status'",
        "UPDATE stock_instruments SET provider_verified_at=NULL "
        "WHERE provider_asset_id='synthetic-status-asset'",
    ],
)
async def test_missing_independent_status_authority_does_not_publish(status_case, sql):
    from sqlalchemy import text

    from app.services.stock_status import StatusUnavailable, load_status, persist_status_batch

    factory, cid, now = status_case
    before = await financial_snapshot(factory)
    async with factory.begin() as db:
        await db.execute(text(sql))
    with pytest.raises(StatusUnavailable):
        async with factory.begin() as db:
            await persist_status_batch(db, persisted_batch(cid, now), coin_id=cid)
    async with factory() as db:
        assert await load_status(db, cid) is None
    assert await financial_snapshot(factory) == before


async def test_status_service_refuses_mixed_instrument_transaction(status_case):
    from app.services.stock_status import load_status, persist_status_batch

    factory, cid, now = status_case
    source = persisted_batch(cid, now)
    with pytest.raises(ValueError, match="One instrument"):
        async with factory.begin() as db:
            await persist_status_batch(
                db,
                replace(
                    source, events=(source.events[0], replace(source.events[0], coin_id=cid + 1))
                ),
                coin_id=cid,
            )
    async with factory() as db:
        assert await load_status(db, cid) is None


@pytest.mark.parametrize("failure", ["permission", "no_baseline"])
async def test_finite_cycle_refuses_unverified_or_unadmitted_frames(status_case, settings, failure):
    from sqlalchemy import text

    from app.services.stock_status import load_status, persist_status_batch
    from app.tasks.stock_status import run_stock_status_cycle

    factory, cid, now = status_case
    source = persisted_batch(cid, now)
    if failure == "permission":
        async with factory.begin() as db:
            await persist_status_batch(db, source, coin_id=cid)
            await db.execute(
                text("UPDATE stock_data_admissions SET generation=5 WHERE product='status'")
            )
    else:
        source = replace(source, baseline_verified=False)
    before = await financial_snapshot(factory)
    result = await run_stock_status_cycle(factory, source, settings=settings)
    assert result.status == "ok" and result.accepted == 0 and result.rejected == 1
    async with factory() as db:
        assert (await load_status(db, cid)).state == "unknown"
    assert await financial_snapshot(factory) == before


async def test_absent_instrument_snapshot_has_no_executable_fallback(status_case, settings):
    from app.services.stock_eligibility import load_execution_evidence

    factory, cid, now = status_case
    async with factory() as db:
        loaded = await load_execution_evidence(db, 9223372036854775807, settings)
    assert not loaded.decision.allowed and loaded.decision.evidence is None
    assert loaded.symbol == "" and loaded.evidence.quote.bid is None


def test_malformed_action_projection_cannot_expose_price():
    from app.services.stocks import _action_projection
    from tests.test_stock_admission import action_admitted

    permission = replace(
        action_admitted(),
        reviewed_at=NOW - timedelta(hours=1),
        valid_from=NOW - timedelta(hours=1),
        valid_until=NOW + timedelta(hours=1),
    )
    action, safe = _action_projection(
        {"checked_at": "invalid-source-time"},
        permission,
        NOW + timedelta(hours=1),
        NOW,
        {"account": "birja", "server": "birja"},
        0,
        NOW,
    )
    assert action.state == "unknown" and not safe


async def test_unapproved_universe_growth_cannot_be_truncated_into_authority(
    stock_trade_case, settings, redis_client, monkeypatch, caplog
):
    import httpx
    from sqlalchemy import delete, insert, select
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.models.price import Coin
    from app.models.stock import StockInstrument
    from app.models.stock_execution import StockStatusEvidence
    from app.services import stock_eligibility, stocks
    from app.tasks.stock_scheduler import run_stock_cycle

    factory, cid, uid, now = stock_trade_case
    before = await financial_snapshot(factory)
    new_cid = None
    created_statuses = []
    try:
        async with factory.begin() as db:
            old_ids = set((await db.scalars(select(StockStatusEvidence.coin_id))).all())
            new_cid = (
                await db.execute(
                    insert(Coin)
                    .values(
                        symbol="SCOPECAP",
                        name="Synthetic scope",
                        asset_class="stock",
                        kraken_pair=None,
                        sort_order=9999,
                    )
                    .returning(Coin.id)
                )
            ).scalar_one()
            await db.execute(
                insert(StockInstrument).values(
                    coin_id=new_cid,
                    listing_exchange="NASDAQ",
                    source="sec",
                    source_ref="synthetic-only",
                )
            )
            ids = (await db.scalars(select(StockInstrument.coin_id))).all()
            created_statuses = [instrument for instrument in ids if instrument not in old_ids]
            await db.execute(
                pg_insert(StockStatusEvidence).values(
                    [
                        dict(
                            coin_id=instrument,
                            provider_asset_id="synthetic-scope-" + str(instrument),
                            source_ref="synthetic-width-test",
                        )
                        for instrument in created_statuses
                    ]
                )
            )
        for module in (stocks, stock_eligibility):
            monkeypatch.setattr(module, "CURATED_SYMBOLS", module.CURATED_SYMBOLS | {"SCOPECAP"})
        async with factory() as db:
            loaded = await stock_eligibility.load_execution_evidence(db, cid, settings)
            view = await stocks.list_stocks(db, settings)
        assert not loaded.decision.allowed and loaded.symbol == ""
        assert all(not item.execution_enabled and item.quote is None for item in view.items)

        def no_http(request):
            raise AssertionError("Oversized status scope must stop before provider requests")

        async with httpx.AsyncClient(transport=httpx.MockTransport(no_http)) as http:
            result = await run_stock_cycle(
                sessionmaker=factory, redis=redis_client, http=http, settings=settings
            )
        assert result.status == "source_error"
        assert "synthetic-width-test" not in caplog.text
        assert await financial_snapshot(factory) == before
    finally:
        async with factory.begin() as db:
            if created_statuses:
                await db.execute(
                    delete(StockStatusEvidence).where(
                        StockStatusEvidence.coin_id.in_(created_statuses)
                    )
                )
            if new_cid is not None:
                await db.execute(delete(StockInstrument).where(StockInstrument.coin_id == new_cid))
                await db.execute(delete(Coin).where(Coin.id == new_cid))


async def test_more_than_twenty_source_instruments_invalidates_continuity(status_case, settings):
    from app.services.stock_status import load_status, persist_status_batch
    from app.tasks.stock_status import run_stock_status_cycle

    factory, cid, now = status_case
    source = persisted_batch(cid, now)
    async with factory.begin() as db:
        await persist_status_batch(db, source, coin_id=cid)
    events = tuple(replace(source.events[0], coin_id=cid + i) for i in range(21))
    result = await run_stock_status_cycle(
        factory, replace(source, events=events), settings=settings
    )
    assert result.status == "source_error" and result.rejected == 1
    async with factory() as db:
        assert (await load_status(db, cid)).state == "unknown"


async def test_denied_nullable_admission_is_not_execution_authority(stock_trade_case, settings):
    from sqlalchemy import text

    from app.services.stock_eligibility import load_execution_evidence

    factory, cid, uid, now = stock_trade_case
    async with factory.begin() as db:
        await db.execute(
            text("""UPDATE stock_data_admissions SET state='denied',
            reviewed_at=NULL, valid_from=NULL, valid_until=NULL WHERE product='status'""")
        )
    async with factory() as db:
        loaded = await load_execution_evidence(db, cid, settings)
    assert not loaded.decision.allowed and loaded.decision.reason == "permission_unavailable"


@pytest.mark.parametrize("cached_boundary", [False, True])
async def test_post_split_quote_uses_current_applied_unit_boundary(
    stock_trade_case, settings, cached_boundary
):
    from sqlalchemy import update

    from app.models.corporate_action import StockActionState
    from app.models.stock import StockQuote
    from app.services.stock_eligibility import load_execution_evidence
    from app.services.stocks import list_stocks
    from tests.stock_action_fixtures import synthetic_split

    factory, cid, uid, now = stock_trade_case
    cutoff = now - timedelta(minutes=1)
    async with factory.begin() as db:
        await synthetic_split(db, cid, cutoff, boundary=0)
        await db.execute(
            update(StockActionState)
            .where(StockActionState.coin_id == cid)
            .values(quote_not_before=cutoff, next_blocking_at=cutoff if cached_boundary else None)
        )
        await db.execute(update(StockQuote).where(StockQuote.coin_id == cid).values(unit_epoch=1))
    async with factory() as db:
        loaded = await load_execution_evidence(db, cid, settings)
        view = await list_stocks(db, settings)
    assert loaded.decision.allowed is (not cached_boundary)
    if cached_boundary:
        assert loaded.decision.reason == "action_unavailable"
    item = next(item for item in view.items if item.id == cid)
    assert item.quote is not None and item.action.state == "current"
    assert item.execution_enabled is (not cached_boundary)
    assert loaded.evidence.unit_epoch == loaded.evidence.quote.unit_epoch == 1
