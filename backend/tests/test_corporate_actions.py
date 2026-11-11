"""Actual isolated PostgreSQL corporate-action financial invariants."""

import asyncio
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select, text, update

import app.services.corporate_actions as service
from app.models.corporate_action import (
    StockActionEvent,
    StockActionObservation,
    StockActionRevision,
    StockActionState,
    StockDividendEntitlement,
    StockOwnershipMovement,
    StockSplitApplication,
)
from app.models.price import Coin
from app.models.stock import StockDataAdmission, StockInstrument
from app.models.trade import Holding
from app.services.alpaca_actions import ActionBatch, ActionCoverage, ActionObservation
from app.services.corporate_actions import (
    ActionHeld,
    apply_due_actions,
    derive_dividend_entitlements,
    persist_action_batch,
)
from app.services.stock_ownership import StockMovementInput, append_stock_movement
from app.services.stock_sessions import build_sessions
from tests.stock_action_fixtures import ownership as _ownership
from tests.stock_action_fixtures import synthetic_fill, synthetic_opening
from tests.test_corporate_action_rules import dividend
from tests.test_stock_admission import action_admitted
from tests.test_stock_sessions import evidence as calendar_evidence

ownership = _ownership


async def test_ingest_source_identity_cannot_cross_instruments(actions):
    factory, cid, _, action, auth = actions
    async with factory.begin() as db:
        result = (await persist_action_batch(db, batch(action), auth))[0]
        other = (
            await db.execute(
                select(StockInstrument.coin_id).where(StockInstrument.coin_id != cid).limit(1)
            )
        ).scalar_one()
        await db.execute(
            update(StockActionEvent)
            .where(StockActionEvent.id == result.event_id)
            .values(coin_id=other)
        )
        try:
            with pytest.raises(ActionHeld, match="identity_conflict"):
                await persist_action_batch(db, batch(action), auth)
        finally:
            await db.execute(
                update(StockActionEvent)
                .where(StockActionEvent.id == result.event_id)
                .values(coin_id=cid)
            )


async def test_missing_observation_remains_persistent_source_gap(actions):
    factory, cid, _, action, auth = actions
    async with factory.begin() as db:
        await persist_action_batch(db, batch(action), auth)
        await persist_action_batch(
            db,
            ActionBatch(
                coverage=(
                    ActionCoverage(
                        "known_id",
                        action.provider_event_id,
                        action.provider_event_id,
                        False,
                        "missing_or_uncertain",
                    ),
                )
            ),
            auth,
        )
        assert await service.persistent_action_holds(db, cid) == ("source_gap",)


async def test_split_earlier_late_boundary_stops_later_split(actions):
    factory, cid, uid, action, auth = actions
    early = action.observed_at - timedelta(days=2)
    later = action.observed_at - timedelta(days=1)
    async with factory.begin() as db:
        await persist_action_batch(db, batch(split_action(action, early)), auth)
        await persist_action_batch(
            db, batch(replace(split_action(action, later), provider_event_id="later-split")), auth
        )
        await synthetic_opening(db, cid, uid, early + timedelta(hours=1))
        assert await apply_due_actions(db, cid) == ()
        assert (await db.get(StockActionState, cid)).unit_epoch == 0
        assert (
            await db.execute(select(Holding.quantity).where(Holding.coin_id == cid))
        ).scalar_one() == 2


@pytest.mark.parametrize("operation", ["split", "entitlement"])
async def test_monitor_expiry_after_effect_before_final_sql_rolls_back(
    actions, operation, monkeypatch
):
    factory, cid, uid, action, auth = actions
    if operation == "entitlement":
        event, _ = await prepare_dividend(actions)
    else:
        async with factory.begin() as db:
            cutoff = action.observed_at - timedelta(hours=1)
            await synthetic_opening(db, cid, uid, cutoff - timedelta(hours=1))
            await persist_action_batch(db, batch(split_action(action, cutoff)), auth)
    async with factory.begin() as db:
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        await db.execute(
            update(StockActionState)
            .where(StockActionState.coin_id == cid)
            .values(valid_until=now + timedelta(seconds=1))
        )
    original = service._guard

    async def expire(db, *args, **kwargs):
        await db.execute(text("SELECT pg_sleep(1.1)"))
        await original(db, *args, **kwargs)

    monkeypatch.setattr(service, "_guard", expire)
    with pytest.raises(ActionHeld, match="admission_changed"):
        async with factory.begin() as db:
            if operation == "split":
                await apply_due_actions(db, cid)
            else:
                await derive_dividend_entitlements(db, event.event_id)
    async with factory() as db:
        assert (await db.get(StockActionState, cid)).unit_epoch == 0
        assert (
            await db.execute(select(func.count()).select_from(StockDividendEntitlement))
        ).scalar_one() == 0


@pytest.mark.parametrize("operation", ["ingest", "split", "entitlement"])
async def test_configured_scope_is_used_for_every_authority_check(actions, operation):
    factory, cid, uid, action, auth = actions
    event = None
    if operation == "entitlement":
        event, _ = await prepare_dividend(actions)
    elif operation == "split":
        async with factory.begin() as db:
            cutoff = action.observed_at - timedelta(hours=1)
            await synthetic_opening(db, cid, uid, cutoff - timedelta(hours=1))
            await persist_action_batch(db, batch(split_action(action, cutoff)), auth)
    auth = replace(auth, scope={**auth.scope, "account": "test-account", "server": "test-server"})
    async with factory.begin() as db:
        await db.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "actions")
            .values(**asdict(auth))
        )
        if operation == "entitlement":
            calendar = calendar_evidence(action.observed_at)
            calendar = replace(
                calendar,
                scope={**calendar.scope, "account": "test-account", "server": "test-server"},
            )
            await db.execute(
                update(StockDataAdmission)
                .where(StockDataAdmission.product == "calendar")
                .values(**asdict(calendar))
            )
    with pytest.raises(ActionHeld, match="admission"):
        async with factory.begin() as db:
            if operation == "ingest":
                await persist_action_batch(db, batch(action), auth)
            elif operation == "split":
                await apply_due_actions(db, cid)
            else:
                await derive_dividend_entitlements(db, event.event_id)
    async with factory.begin() as db:
        scope = {"account": "test-account", "server": "test-server"}
        if operation == "ingest":
            assert len(await persist_action_batch(db, batch(action), auth, **scope)) == 1
        elif operation == "split":
            assert len(await apply_due_actions(db, cid, **scope)) == 1
        else:
            assert (await derive_dividend_entitlements(db, event.event_id, **scope))[
                0
            ].state == "eligible"


async def test_split_earlier_fractional_hold_stops_later_split(actions):
    factory, cid, uid, action, auth = actions
    early = action.observed_at - timedelta(days=2)
    later = action.observed_at - timedelta(days=1)
    async with factory.begin() as db:
        await synthetic_opening(
            db, cid, uid, action.observed_at - timedelta(days=3), quantity=Decimal(3)
        )
        await persist_action_batch(
            db, batch(split_action(action, early, new_rate=Decimal("1.5"))), auth
        )
        await persist_action_batch(
            db,
            batch(
                replace(
                    split_action(action, later, new_rate=Decimal(2)),
                    provider_event_id="later-split",
                )
            ),
            auth,
        )
        assert await apply_due_actions(db, cid) == ()
        assert (
            await db.execute(select(Holding.quantity).where(Holding.coin_id == cid))
        ).scalar_one() == 3
        assert (await db.get(StockActionState, cid)).unit_epoch == 0


async def test_entitlement_calendar_review_expiry_at_final_sql_refuses_commit(actions, monkeypatch):
    factory, _, _, _, _ = actions
    event, action = await prepare_dividend(actions)
    now = datetime.now(UTC)
    async with factory.begin() as db:
        calendar = calendar_evidence(now)
        calendar = replace(
            calendar,
            calendar={
                **calendar.calendar,
                "review_valid_until": (now + timedelta(seconds=1)).isoformat(),
            },
        )
        await db.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "calendar")
            .values(**asdict(calendar))
        )
    original = service._guard

    async def expire(db, *args, **kwargs):
        await db.execute(text("SELECT pg_sleep(1.1)"))
        await original(db, *args, **kwargs)

    monkeypatch.setattr(service, "_guard", expire)
    with pytest.raises(ActionHeld, match="admission_changed"):
        async with factory.begin() as db:
            await derive_dividend_entitlements(db, event.event_id)
    async with factory() as db:
        assert (
            await db.execute(select(func.count()).select_from(StockDividendEntitlement))
        ).scalar_one() == 0


@pytest.mark.parametrize(
    "case",
    [
        "not_batch",
        "many_observations",
        "many_coverage",
        "empty",
        "irrelevant_coverage",
        "missing_unknown",
        "two_instruments",
        "future_observed",
        "wrong_symbol",
        "naive_observed",
    ],
)
async def test_ingest_rejects_invalid_input_without_partial_events(actions, case):
    factory, cid, _, action, auth = actions
    value = batch(action)
    message = "invalid_batch"
    if case == "not_batch":
        value = None
    elif case == "many_observations":
        value = ActionBatch(observations=(ActionObservation(action),) * 1025)
    elif case == "many_coverage":
        value = ActionBatch(
            coverage=(ActionCoverage("process_date", "a", "z", False, "source_gap"),) * 1025
        )
    elif case == "empty":
        value = ActionBatch()
    elif case == "irrelevant_coverage":
        value = ActionBatch(
            coverage=(ActionCoverage("process_date", "a", "z", False, "source_gap"),)
        )
    elif case == "missing_unknown":
        value = ActionBatch(
            coverage=(
                ActionCoverage("known_id", "unknown", "unknown", False, "missing_or_uncertain"),
            )
        )
        message = "unknown_missing_identity"
    elif case == "two_instruments":
        value = ActionBatch(
            observations=(
                ActionObservation(action),
                ActionObservation(replace(action, coin_id=cid + 1)),
            )
        )
        message = "one_instrument"
    else:
        changes = {
            "future_observed": {"observed_at": action.observed_at + timedelta(days=1)},
            "wrong_symbol": {"symbol": "MSFT"},
            "naive_observed": {"observed_at": action.observed_at.replace(tzinfo=None)},
        }[case]
        value = batch(replace(action, **changes))
        message = "invalid_observation"
    if case in ("empty", "irrelevant_coverage"):
        async with factory.begin() as db:
            assert await persist_action_batch(db, value, auth) == ()
    else:
        with pytest.raises(ActionHeld, match=message):
            async with factory.begin() as db:
                await persist_action_batch(db, value, auth)
    async with factory() as db:
        assert (
            await db.execute(select(func.count()).select_from(StockActionEvent))
        ).scalar_one() == 0


async def test_ingest_creates_unknown_state_without_granting_health(actions):
    factory, cid, _, action, auth = actions
    async with factory.begin() as db:
        await db.execute(delete(StockActionState).where(StockActionState.coin_id == cid))
        await persist_action_batch(db, batch(action), auth)
        state = await db.get(StockActionState, cid)
        assert state.health == "unknown" and state.complete_from is None


@pytest.mark.parametrize("operation", ["ingest", "split"])
async def test_unverified_mapping_refuses_effects(actions, operation):
    factory, cid, _, action, auth = actions
    async with factory.begin() as db:
        await db.execute(
            update(StockInstrument)
            .where(StockInstrument.coin_id == cid)
            .values(provider_verified_at=None)
        )
    with pytest.raises(ActionHeld, match="mapping"):
        async with factory.begin() as db:
            if operation == "ingest":
                await persist_action_batch(db, batch(action), auth)
            else:
                await apply_due_actions(db, cid)


async def test_revision_historical_terms_reappear_without_rewinding_safe_state(actions):
    factory, _, _, action, auth = actions
    async with factory.begin() as db:
        first = (await persist_action_batch(db, batch(action), auth))[0]
        for rate in ("0.5", "0.25", "0.5", "0.25"):
            last = (
                await persist_action_batch(db, batch(replace(action, rate=Decimal(rate))), auth)
            )[0]
        assert last.classification == "uncertain" and last.revision_id != first.revision_id


@pytest.mark.parametrize("change", ["rate", "cancelled", "units", "ex_date"])
async def test_inclusive_old_mutation_replay_preserves_later_current_revision(actions, change):
    factory, cid, _, action, auth = actions
    async with factory.begin() as db:
        first = (
            await persist_action_batch(db, batch(action, mutation="insert", cursor="old-1"), auth)
        )[0]
    revised = replace(action, rate=Decimal("0.5"))
    async with factory.begin() as db:
        latest = (
            await persist_action_batch(db, batch(revised, mutation="update", cursor="new-2"), auth)
        )[0]
    async with factory.begin() as db:
        epoch = (await db.get(StockActionState, cid)).epoch
        replayed = (
            await persist_action_batch(db, batch(action, mutation="insert", cursor="old-1"), auth)
        )[0]
        assert replayed.revision_id == first.revision_id
        assert (
            await db.get(StockActionEvent, first.event_id)
        ).current_revision_id == latest.revision_id
        assert (await db.get(StockActionState, cid)).epoch == epoch
    with pytest.raises(ActionHeld, match="mutation_conflict"):
        async with factory.begin() as db:
            divergent = replace(
                action,
                **{
                    change: {
                        "rate": Decimal("0.5"),
                        "cancelled": True,
                        "units": "post_split",
                        "ex_date": action.ex_date + timedelta(days=1),
                    }[change]
                },
            )
            await persist_action_batch(
                db, batch(divergent, mutation="insert", cursor="old-1"), auth
            )
    async with factory() as db:
        assert (
            await db.get(StockActionEvent, first.event_id)
        ).current_revision_id == latest.revision_id
        assert (await db.get(StockActionState, cid)).epoch == epoch
        assert (
            await db.execute(select(func.count()).select_from(StockActionRevision))
        ).scalar_one() == 2
        assert (
            await db.execute(select(func.count()).select_from(StockActionObservation))
        ).scalar_one() == 2


async def test_ingest_mutation_replay_and_conflict(actions):
    factory, _, _, action, auth = actions
    async with factory.begin() as db:
        first = await persist_action_batch(
            db, batch(action, mutation="insert", cursor="cursor-1"), auth
        )
        assert (
            await persist_action_batch(
                db, batch(action, mutation="insert", cursor="cursor-1"), auth
            )
            == first
        )
    with pytest.raises(ActionHeld, match="mutation_conflict"):
        async with factory.begin() as db:
            await persist_action_batch(
                db,
                batch(replace(action, rate=Decimal("0.5")), mutation="update", cursor="cursor-1"),
                auth,
            )


async def test_split_persistent_hold_survives_healthy_monitor(actions):
    factory, cid, _, action, auth = actions
    async with factory.begin() as db:
        await persist_action_batch(db, batch(replace(action, event_type="merger")), auth)
        state = await db.get(StockActionState, cid)
        state.health = "current"
        await db.flush()
        assert await apply_due_actions(db, cid) == ()
        assert (await db.get(StockActionState, cid)).health == "reconciling"


@pytest.mark.parametrize(
    "case",
    ["future", "missing_cutoff", "missing_baseline_at_cutoff", "late_after_ingest", "zero_holder"],
)
async def test_split_boundary_and_zero_owner_guards(actions, case):
    factory, cid, uid, action, auth = actions
    cutoff = (
        action.observed_at + timedelta(hours=1)
        if case == "future"
        else action.observed_at - timedelta(hours=1)
    )
    async with factory.begin() as db:
        event = (await persist_action_batch(db, batch(split_action(action, cutoff)), auth))[0]
        if case == "missing_cutoff":
            await db.execute(
                update(StockActionRevision)
                .where(StockActionRevision.id == event.revision_id)
                .values(verified_cutoff=None)
            )
        elif case == "missing_baseline_at_cutoff":
            await db.execute(
                update(StockActionState)
                .where(StockActionState.coin_id == cid)
                .values(complete_from=action.observed_at)
            )
        elif case == "late_after_ingest":
            await synthetic_opening(db, cid, uid, action.observed_at)
        elif case == "zero_holder":
            db.add(Holding(coin_id=cid, user_id=uid, quantity=Decimal(0), cost_basis=Decimal(0)))
        result = await apply_due_actions(db, cid)
        assert len(result) == (1 if case == "zero_holder" else 0)


@pytest.mark.parametrize("operation", ["derive", "latest"])
async def test_entitlement_unknown_event_refused(actions, operation):
    factory, *_ = actions
    with pytest.raises(ActionHeld, match="unknown_event"):
        async with factory.begin() as db:
            await (
                derive_dividend_entitlements(db, 9007199254740991)
                if operation == "derive"
                else service.latest_verified_entitlements(db, 9007199254740991)
            )


async def test_entitlement_missing_revision_and_nondividend_refused(actions):
    factory, cid, _, action, auth = actions
    from uuid import uuid4

    async with factory.begin() as db:
        event = StockActionEvent(
            coin_id=cid, economic_key=str(uuid4()), first_observed_at=action.observed_at
        )
        db.add(event)
        await db.flush()
        with pytest.raises(ActionHeld, match="missing_revision"):
            await derive_dividend_entitlements(db, event.id)
        event = (
            await persist_action_batch(db, batch(split_action(action, action.observed_at)), auth)
        )[0]
        with pytest.raises(ActionHeld, match="not_dividend"):
            await derive_dividend_entitlements(db, event.event_id)


@pytest.mark.parametrize(
    "case", ["declared_same_without_split", "unapplied_split", "unjournaled_owner", "no_owners"]
)
async def test_entitlement_uncertain_units_or_journal_hold(actions, case):
    factory, cid, uid, _, auth = actions
    event, action = await prepare_dividend(
        actions,
        opening=case not in ("unjournaled_owner", "no_owners"),
        same_boundary_split=case == "declared_same_without_split",
        units="pre_split" if case == "declared_same_without_split" else None,
        economic_order=1 if case == "declared_same_without_split" else None,
    )
    async with factory.begin() as db:
        if case == "unjournaled_owner":
            db.add(Holding(coin_id=cid, user_id=uid, quantity=Decimal(2), cost_basis=Decimal(20)))
            await db.flush()
        elif case == "unapplied_split":
            cutoff = datetime.combine(action.ex_date, datetime.min.time(), UTC) + timedelta(
                hours=14, minutes=30
            )
            await persist_action_batch(
                db,
                batch(replace(split_action(action, cutoff), provider_event_id="unapplied-split")),
                auth,
            )
        result = await derive_dividend_entitlements(db, event.event_id)
        if case == "no_owners":
            assert result == ()
        else:
            assert result[0].state == "held" and result[0].eligible_quantity == 0


async def test_latest_verified_entitlements_selects_latest_per_owner(actions):
    factory, _, _, _, auth = actions
    event, action = await prepare_dividend(actions)
    async with factory.begin() as db:
        await derive_dividend_entitlements(db, event.event_id)
        await persist_action_batch(db, batch(replace(action, rate=Decimal("0.5"))), auth)
        latest = await derive_dividend_entitlements(db, event.event_id)
        assert await service.latest_verified_entitlements(db, event.event_id) == latest


@pytest.mark.parametrize(
    "ordering,expected", [("pre", 2), ("post", 8), ("unknown", None), ("before", 8), ("after", 2)]
)
async def test_entitlement_verified_split_unit_order(actions, ordering, expected):
    factory, cid, uid, action, auth = actions
    day = action.observed_at.date() - timedelta(days=1)
    cutoff = datetime.combine(day, datetime.min.time(), UTC) + timedelta(hours=14, minutes=30)
    split_cutoff = cutoff + timedelta(
        hours=-1 if ordering == "before" else 1 if ordering == "after" else 0
    )
    async with factory.begin() as db:
        db.add(StockDataAdmission(**asdict(calendar_evidence(action.observed_at))))
        await synthetic_opening(db, cid, uid, action.observed_at - timedelta(days=3))
        await persist_action_batch(db, batch(split_action(action, split_cutoff)), auth)
        assert len(await apply_due_actions(db, cid)) == 1
        same = ordering in ("pre", "post")
        dividend_action = replace(
            action,
            provider_event_id="dividend-after-split",
            ex_date=day,
            record_date=day,
            payable_date=day + timedelta(days=5),
            same_boundary_split=same,
            units="pre_split"
            if ordering == "pre"
            else "post_split"
            if ordering == "post"
            else None,
            economic_order=1 if ordering == "pre" else 2 if ordering == "post" else None,
        )
        event = (await persist_action_batch(db, batch(dividend_action), auth))[0]
        result = (await derive_dividend_entitlements(db, event.event_id))[0]
        if expected is None:
            assert result.state == "held"
        else:
            assert result.state == "eligible" and result.eligible_quantity == Decimal(expected)


@pytest.mark.parametrize("operation", ["ingest", "split", "entitlement"])
async def test_final_admission_change_rolls_entire_operation_back(actions, operation, monkeypatch):
    factory, cid, uid, action, auth = actions
    event = None
    if operation == "entitlement":
        event, _ = await prepare_dividend(actions)
    elif operation == "split":
        async with factory.begin() as db:
            cutoff = action.observed_at - timedelta(hours=1)
            await synthetic_opening(db, cid, uid, cutoff - timedelta(hours=1))
            await persist_action_batch(db, batch(split_action(action, cutoff)), auth)
    original = service._guard

    async def revoke(db, *args, **kwargs):
        async with factory.begin() as admin:
            await admin.execute(
                update(StockDataAdmission)
                .where(StockDataAdmission.product == "actions")
                .values(state="revoked", generation=2)
            )
        await original(db, *args, **kwargs)

    monkeypatch.setattr(service, "_guard", revoke)
    with pytest.raises(ActionHeld, match="admission_changed"):
        async with factory.begin() as db:
            if operation == "ingest":
                await persist_action_batch(db, batch(action), auth)
            elif operation == "split":
                await apply_due_actions(db, cid)
            else:
                await derive_dividend_entitlements(db, event.event_id)
    async with factory() as db:
        assert (
            await db.execute(select(func.count()).select_from(StockSplitApplication))
        ).scalar_one() == 0
        assert (
            await db.execute(select(func.count()).select_from(StockDividendEntitlement))
        ).scalar_one() == 0
        if operation == "ingest":
            assert (
                await db.execute(select(func.count()).select_from(StockActionEvent))
            ).scalar_one() == 0
        else:
            assert (
                await db.execute(select(Holding.quantity).where(Holding.coin_id == cid))
            ).scalar_one() == 2


async def wait_blocked(factory, pid):
    for _ in range(100):
        async with factory() as observer:
            if (
                await observer.execute(
                    text("SELECT cardinality(pg_blocking_pids(:pid))"), {"pid": pid}
                )
            ).scalar_one() > 0:
                return
        await asyncio.sleep(0.01)
    raise AssertionError("actual PostgreSQL gate wait not observed")


@pytest.mark.parametrize("freeze_first", [True, False])
async def test_ingest_freeze_and_fill_share_actual_instrument_gate(actions, freeze_first):
    factory, cid, uid, action, auth = actions
    from app.services.stock_ownership import OwnershipHeld, acquire_stock_gate

    ready = asyncio.Event()
    pid = None

    async def fill():
        nonlocal pid
        async with factory.begin() as db:
            pid = (await db.execute(text("SELECT pg_backend_pid()"))).scalar_one()
            ready.set()
            await acquire_stock_gate(db, cid)
            trade = await synthetic_fill(db, cid, uid)
            await append_stock_movement(
                db,
                StockMovementInput(
                    uid, cid, Decimal(2), Decimal(20), "fill:" + str(trade.id), trade_id=trade.id
                ),
            )

    async def freeze():
        nonlocal pid
        async with factory.begin() as db:
            pid = (await db.execute(text("SELECT pg_backend_pid()"))).scalar_one()
            ready.set()
            await persist_action_batch(db, batch(replace(action, event_type="reverse_split")), auth)

    async with factory.begin() as first:
        await acquire_stock_gate(first, cid)
        task = asyncio.create_task(fill() if freeze_first else freeze())
        await ready.wait()
        try:
            await wait_blocked(factory, pid)
            if freeze_first:
                await persist_action_batch(
                    first, batch(replace(action, event_type="reverse_split")), auth
                )
            else:
                trade = await synthetic_fill(first, cid, uid)
                await append_stock_movement(
                    first,
                    StockMovementInput(
                        uid,
                        cid,
                        Decimal(2),
                        Decimal(20),
                        "fill:" + str(trade.id),
                        trade_id=trade.id,
                    ),
                )
        except BaseException:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            raise
    if freeze_first:
        with pytest.raises(OwnershipHeld, match="monitor_unavailable"):
            await task
    else:
        await task
    async with factory() as db:
        assert (await db.get(StockActionState, cid)).health == "reconciling"
        quantities = (
            (await db.execute(select(Holding.quantity).where(Holding.coin_id == cid)))
            .scalars()
            .all()
        )
        assert quantities == ([] if freeze_first else [Decimal(2)])


async def prepare_dividend(actions, *, opening=True, **changes):
    factory, cid, uid, action, auth = actions
    day = action.observed_at.date() - timedelta(days=1)
    action = replace(action, ex_date=day, record_date=day, payable_date=day + timedelta(days=5))
    action = replace(action, **changes)
    async with factory.begin() as db:
        db.add(StockDataAdmission(**asdict(calendar_evidence(action.observed_at))))
        if opening:
            await synthetic_opening(db, cid, uid, action.observed_at - timedelta(days=2))
        event = (await persist_action_batch(db, batch(action), auth))[0]
    return event, action


@pytest.mark.parametrize("side,expected", [("buy", "0"), ("sell", "2")])
async def test_entitlement_late_buyer_and_departed_seller(actions, side, expected):
    factory, cid, uid, _, _ = actions
    event, _ = await prepare_dividend(actions, opening=side == "sell")
    async with factory.begin() as db:
        fill = await synthetic_fill(db, cid, uid, side=side)
        await append_stock_movement(
            db,
            StockMovementInput(
                uid,
                cid,
                Decimal(2 if side == "buy" else -2),
                Decimal(20 if side == "buy" else 0),
                "fill:" + str(fill.id),
                trade_id=fill.id,
            ),
        )
        results = await derive_dividend_entitlements(db, event.event_id)
        assert results[0].eligible_quantity == Decimal(expected)
        assert results[0].state == "eligible"


async def test_entitlement_rate_revision_appends_linked_replacement(actions):
    factory, _, _, _, auth = actions
    event, action = await prepare_dividend(actions)
    async with factory.begin() as db:
        first = (await derive_dividend_entitlements(db, event.event_id))[0]
        revised = (
            await persist_action_batch(db, batch(replace(action, rate=Decimal("0.5"))), auth)
        )[0]
        second = (await derive_dividend_entitlements(db, event.event_id))[0]
        assert second.revision_id == revised.revision_id and second.revision_id != first.revision_id
        assert second.supersedes_id == first.id and second.version == 2
        assert second.eligible_quantity == first.eligible_quantity == 2
        old = await db.get(StockDividendEntitlement, first.id)
        assert old.state == "eligible" and old.version == 1


@pytest.mark.parametrize(
    "changes", [{"cancelled": True}, {"currency": None}, {"dates_verified": False}]
)
async def test_entitlement_uncertain_cancelled_keep_prior_terms(actions, changes):
    factory, _, _, _, auth = actions
    event, action = await prepare_dividend(actions)
    async with factory.begin() as db:
        first = (await derive_dividend_entitlements(db, event.event_id))[0]
        await persist_action_batch(db, batch(replace(action, **changes)), auth)
        second = (await derive_dividend_entitlements(db, event.event_id))[0]
        assert second.state == ("cancelled" if changes.get("cancelled") else "held")
        assert second.supersedes_id == first.id and second.eligible_quantity == 0
        assert await service.latest_verified_entitlements(db, event.event_id) == ()


async def test_entitlement_monitor_loss_recovery_loss_preserves_all_versions(actions):
    factory, cid, _, _, _ = actions
    event, _ = await prepare_dividend(actions)
    async with factory.begin() as db:
        first = (await derive_dividend_entitlements(db, event.event_id))[0]
        state = await db.get(StockActionState, cid)
        state.health = "unknown"
        await db.flush()
        held = (await derive_dividend_entitlements(db, event.event_id))[0]
        assert held.state == "held" and held.version == 2
        state.health = "current"
        await db.flush()
        recovered = (await derive_dividend_entitlements(db, event.event_id))[0]
        assert recovered.state == "eligible" and recovered.version == 3
        state.health = "unknown"
        await db.flush()
        held_again = (await derive_dividend_entitlements(db, event.event_id))[0]
        assert held_again.state == "held" and held_again.version == 4
        assert await service.latest_verified_entitlements(db, event.event_id) == ()
        assert (await db.get(StockDividendEntitlement, first.id)).state == "eligible"


async def test_entitlement_historical_quantity_and_idempotent_snapshot(actions):
    factory, cid, uid, action, auth = actions
    now = action.observed_at
    day = now.date() - timedelta(days=1)
    dividend_action = replace(
        action, ex_date=day, record_date=day, payable_date=now.date() + timedelta(days=2)
    )
    async with factory.begin() as db:
        db.add(StockDataAdmission(**asdict(calendar_evidence(now))))
        await synthetic_opening(db, cid, uid, now - timedelta(days=2))
        event = (await persist_action_batch(db, batch(dividend_action), auth))[0]
        entitlements = await derive_dividend_entitlements(db, event.event_id)
        assert len(entitlements) == 1
        assert entitlements[0].eligible_quantity == Decimal(2)
        assert entitlements[0].state == "eligible"
        assert await derive_dividend_entitlements(db, event.event_id) == entitlements


@pytest_asyncio.fixture
async def actions(ownership):
    factory, cid, uid = ownership
    now = datetime.now(UTC)
    auth = replace(
        action_admitted(),
        generation=1,
        reviewed_at=now - timedelta(hours=1),
        valid_from=now - timedelta(hours=2),
        valid_until=now + timedelta(hours=2),
    )
    async with factory.begin() as db:
        instrument = await db.get(StockInstrument, cid)
        saved = instrument.provider_asset_id, instrument.provider_verified_at
        instrument.provider_asset_id = f"synthetic-{cid}"
        instrument.provider_verified_at = now - timedelta(days=1)
        symbol = (await db.execute(select(Coin.symbol).where(Coin.id == cid))).scalar_one()
        db.add(StockDataAdmission(**asdict(auth)))
    action = replace(
        dividend(),
        coin_id=cid,
        symbol=symbol,
        observed_at=now,
        ex_date=now.date() + timedelta(days=2),
        record_date=now.date() + timedelta(days=2),
        payable_date=now.date() + timedelta(days=10),
    )
    try:
        yield factory, cid, uid, action, auth
    finally:
        async with factory.begin() as db:
            events = select(StockActionEvent.id).where(StockActionEvent.coin_id == cid)
            await db.execute(
                delete(StockActionObservation).where(StockActionObservation.event_id.in_(events))
            )
            await db.execute(
                delete(StockDividendEntitlement).where(
                    StockDividendEntitlement.event_id.in_(events)
                )
            )
            await db.execute(
                delete(StockDataAdmission).where(
                    StockDataAdmission.product.in_(["actions", "calendar"])
                )
            )
            await db.execute(
                update(StockInstrument)
                .where(StockInstrument.coin_id == cid)
                .values(provider_asset_id=saved[0], provider_verified_at=saved[1])
            )


def batch(action, **changes):
    return ActionBatch(
        records=(action,), observations=(ActionObservation(action, **changes),), complete=True
    )


async def test_revision_repeated_terms_append_observations_only(actions):
    factory, _, _, action, auth = actions
    async with factory.begin() as db:
        result = await persist_action_batch(db, batch(action), auth)
        assert len(result) == 1
        await persist_action_batch(
            db,
            batch(replace(action, observed_at=action.observed_at + timedelta(microseconds=1))),
            auth,
        )
        assert (
            await db.execute(select(func.count()).select_from(StockActionRevision))
        ).scalar_one() == 1
        assert (
            await db.execute(select(func.count()).select_from(StockActionObservation))
        ).scalar_one() == 2


async def test_revision_changes_preserve_history_and_cancel_hold(actions):
    factory, cid, _, action, auth = actions
    async with factory.begin() as db:
        first = (await persist_action_batch(db, batch(action), auth))[0]
        second = (
            await persist_action_batch(db, batch(replace(action, rate=Decimal("0.5"))), auth)
        )[0]
        deleted = (
            await persist_action_batch(
                db,
                batch(replace(action, cancelled=True), mutation="delete", cursor="mutation-1"),
                auth,
            )
        )[0]
        assert len({first.revision_id, second.revision_id, deleted.revision_id}) == 3
        revisions = (
            (await db.execute(select(StockActionRevision).order_by(StockActionRevision.ordinal)))
            .scalars()
            .all()
        )
        assert [r.ordinal for r in revisions] == [1, 2, 3]
        assert revisions[0].normalized_terms["rate"] == "0.25"
        assert deleted.classification == "cancelled"
        state = await db.get(StockActionState, cid)
        assert state.health == "reconciling" and state.next_blocking_at is not None


async def test_ingest_suspected_alias_is_separate_held_event(actions):
    factory, cid, _, action, auth = actions
    async with factory.begin() as db:
        first = (await persist_action_batch(db, batch(action), auth))[0]
        candidate = (
            await persist_action_batch(
                db, batch(replace(action, provider_event_id="replacement-id")), auth
            )
        )[0]
        assert candidate.event_id != first.event_id
        assert candidate.classification == "uncertain"
        assert (await db.get(StockActionState, cid)).health == "reconciling"


async def test_ingest_known_missing_preserves_revision_and_audits(actions):
    factory, cid, _, action, auth = actions
    async with factory.begin() as db:
        first = (await persist_action_batch(db, batch(action), auth))[0]
        await persist_action_batch(
            db,
            ActionBatch(
                coverage=(
                    ActionCoverage(
                        "known_id",
                        action.provider_event_id,
                        action.provider_event_id,
                        False,
                        "missing_or_uncertain",
                    ),
                )
            ),
            auth,
        )
        assert (
            await db.get(StockActionEvent, first.event_id)
        ).current_revision_id == first.revision_id
        assert (
            await db.execute(
                select(StockActionObservation.source_kind).order_by(StockActionObservation.id)
            )
        ).scalars().all() == ["rest", "missing_or_uncertain"]
        assert (await db.get(StockActionState, cid)).health == "reconciling"


async def test_late_effective_event_freezes_without_quantity_rewrite(actions):
    factory, cid, uid, action, auth = actions
    async with factory.begin() as db:
        await synthetic_opening(db, cid, uid, action.observed_at - timedelta(hours=1))
        result = (
            await persist_action_batch(
                db,
                batch(replace(action, economic_at=action.observed_at - timedelta(hours=2))),
                auth,
            )
        )[0]
        assert result.classification == "uncertain"
        assert (await db.get(StockActionRevision, result.revision_id)).normalized_terms[
            "ingest_hold"
        ] == "late_effective_event"


@pytest.mark.parametrize(
    "changes",
    [
        {"state": "revoked"},
        {"generation": 2},
        {"derived_allowed": False},
        {"retention_allowed": False},
        {"collection_allowed": False},
    ],
)
async def test_ingest_current_authority_required(actions, changes):
    factory, _, _, action, auth = actions
    async with factory.begin() as db:
        await db.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "actions")
            .values(**changes)
        )
    with pytest.raises(ActionHeld, match="admission"):
        async with factory.begin() as db:
            await persist_action_batch(db, batch(action), auth)


def split_action(action, cutoff, **changes):
    base = replace(
        action,
        event_type="forward_split",
        rate=None,
        new_rate=Decimal(4),
        old_rate=Decimal(1),
        economic_at=cutoff,
        ex_date=cutoff.date(),
        record_date=cutoff.date(),
        units="pre_split",
    )
    return replace(base, **changes)


async def test_split_exact_quantity_and_basis_once(actions):
    factory, cid, uid, action, auth = actions
    cutoff = action.observed_at - timedelta(hours=1)
    async with factory.begin() as db:
        await synthetic_opening(db, cid, uid, cutoff - timedelta(hours=1))
        await persist_action_batch(db, batch(split_action(action, cutoff)), auth)
        applied = await apply_due_actions(db, cid)
        assert len(applied) == 1
        holding = (await db.execute(select(Holding).where(Holding.coin_id == cid))).scalar_one()
        assert (holding.quantity, holding.cost_basis) == (Decimal(8), Decimal(20))
        assert await apply_due_actions(db, cid) == applied


@pytest.mark.parametrize(
    "quantity,rate,expected",
    [
        ("2", "4", "8"),
        ("2", "1.5", "3"),
        ("0", "4", "0"),
        ("3", "1.5", None),
        ("999999999999", "4", None),
    ],
)
async def test_split_all_owner_exact_or_none(actions, new_user, quantity, rate, expected):
    factory, cid, uid, action, auth = actions
    second = await new_user()
    cutoff = action.observed_at - timedelta(hours=1)
    async with factory.begin() as db:
        if quantity != "0":
            await synthetic_opening(
                db, cid, uid, cutoff - timedelta(hours=1), quantity=Decimal(quantity)
            )
            await synthetic_opening(
                db, cid, second, cutoff - timedelta(minutes=30), quantity=Decimal(2), sequence=2
            )
        await persist_action_batch(
            db, batch(split_action(action, cutoff, new_rate=Decimal(rate))), auth
        )
        result = await apply_due_actions(db, cid)
        assert len(result) == (0 if expected is None else 1)
        holdings = (
            (
                await db.execute(
                    select(Holding).where(Holding.coin_id == cid).order_by(Holding.user_id)
                )
            )
            .scalars()
            .all()
        )
        assert all(h.cost_basis == Decimal(20) for h in holdings)
        if expected is not None and holdings:
            assert holdings[0].quantity == Decimal(expected)
        if expected is None:
            assert holdings[0].quantity == Decimal(quantity)
            assert (await db.get(StockActionState, cid)).health == "reconciling"


async def test_split_failure_after_first_owner_rolls_everything_back(
    actions, new_user, monkeypatch
):
    factory, cid, uid, action, auth = actions
    second = await new_user()
    cutoff = action.observed_at - timedelta(hours=1)
    async with factory.begin() as db:
        await synthetic_opening(db, cid, uid, cutoff - timedelta(hours=1))
        await synthetic_opening(db, cid, second, cutoff - timedelta(minutes=30), sequence=2)
        await persist_action_batch(db, batch(split_action(action, cutoff)), auth)
    original = service.append_stock_movement

    async def broken(db, movement):
        await original(db, movement)
        raise RuntimeError("injected")

    monkeypatch.setattr(service, "append_stock_movement", broken)
    with pytest.raises(RuntimeError, match="injected"):
        async with factory.begin() as db:
            await apply_due_actions(db, cid)
    async with factory() as db:
        assert (
            await db.execute(select(func.count()).select_from(StockSplitApplication))
        ).scalar_one() == 0
        assert (
            await db.execute(
                select(func.count())
                .select_from(StockOwnershipMovement)
                .where(StockOwnershipMovement.cause_kind == "split")
            )
        ).scalar_one() == 0
        assert (await db.get(StockActionState, cid)).unit_epoch == 0
        assert (
            await db.execute(select(Holding.quantity).where(Holding.coin_id == cid))
        ).scalars().all() == [Decimal(2), Decimal(2)]


async def test_split_concurrent_processors_one_economic_effect(actions):
    factory, cid, uid, action, auth = actions
    cutoff = action.observed_at - timedelta(hours=1)
    async with factory.begin() as db:
        await synthetic_opening(db, cid, uid, cutoff - timedelta(hours=1))
        await persist_action_batch(db, batch(split_action(action, cutoff)), auth)

    async def apply():
        async with factory.begin() as db:
            return await apply_due_actions(db, cid)

    results = await asyncio.gather(apply(), apply(), apply())
    assert results[0] == results[1] == results[2] and len(results[0]) == 1
    async with factory() as db:
        assert (
            await db.execute(select(Holding.quantity).where(Holding.coin_id == cid))
        ).scalar_one() == 8


async def test_split_changed_applied_terms_never_reapply(actions):
    factory, cid, uid, action, auth = actions
    cutoff = action.observed_at - timedelta(hours=1)
    split = split_action(action, cutoff)
    async with factory.begin() as db:
        await synthetic_opening(db, cid, uid, cutoff - timedelta(hours=1))
        await persist_action_batch(db, batch(split), auth)
        await apply_due_actions(db, cid)
        result = (await persist_action_batch(db, batch(replace(split, new_rate=Decimal(5))), auth))[
            0
        ]
        assert result.classification == "uncertain"
        assert await apply_due_actions(db, cid) == ()
        assert (
            await db.execute(select(Holding.quantity).where(Holding.coin_id == cid))
        ).scalar_one() == 8


async def test_applied_split_cached_boundary_and_new_quote_project_current(actions, settings):
    from app.models.stock import StockQuote, StockSession
    from app.services.stock_quote_rules import RawStockQuote, validate_quote
    from app.services.stock_quotes import load_stock_catalog, upsert_stock_quotes
    from app.services.stocks import list_stocks
    from tests.test_stock_admission import admitted

    factory, cid, _, action, auth = actions
    observed = datetime.now(UTC)
    cutoff = observed - timedelta(hours=1)
    calendar = calendar_evidence(observed)
    try:
        async with factory.begin() as db:
            db.add(
                StockDataAdmission(
                    **asdict(
                        replace(
                            admitted(),
                            reviewed_at=observed - timedelta(hours=1),
                            valid_from=observed - timedelta(hours=2),
                            valid_until=observed + timedelta(hours=2),
                        )
                    )
                )
            )
            db.add(StockDataAdmission(**asdict(calendar)))
            for session in build_sessions(observed, calendar):
                db.add(StockSession(**asdict(session)))
            await persist_action_batch(db, batch(split_action(action, cutoff)), auth)
            assert len(await apply_due_actions(db, cid)) == 1
            state = await db.get(StockActionState, cid)
            assert state.next_blocking_at == cutoff
            mapping = next(item for item in await load_stock_catalog(db) if item.coin_id == cid)
            quote = validate_quote(
                RawStockQuote(
                    mapping,
                    Decimal(100),
                    Decimal(102),
                    observed,
                    ["R"],
                    tape="C" if mapping.listing_exchange == "NASDAQ" else "A",
                ),
                observed,
                4,
            )
            assert await upsert_stock_quotes(db, [quote], 4, now=lambda: observed) == 1
            response = await list_stocks(db, settings, now=lambda: observed)
            item = next(item for item in response.items if item.id == cid)
            assert item.action.state == "current" and item.action.reason == "none"
            assert item.quote.mid == Decimal(101)
            assert item.valuation_reason == "available"
            # The stale consumed marker cannot mask a different unresolved boundary.
            future = observed + timedelta(seconds=30)
            from tests.stock_action_fixtures import synthetic_split

            pending = await synthetic_split(db, cid, future, boundary=0, prior_epoch=1)
            await db.delete(pending)
            state.unit_epoch = 1
            await db.flush()
            response = await list_stocks(db, settings, now=lambda: observed)
            item = next(item for item in response.items if item.id == cid)
            assert item.action.valid_until == future
            response = await list_stocks(db, settings, now=lambda: future)
            item = next(item for item in response.items if item.id == cid)
            assert item.quote is None and item.action.state == "reconciling"
    finally:
        async with factory.begin() as db:
            await db.execute(delete(StockQuote))
            await db.execute(delete(StockSession))
            await db.execute(
                delete(StockDataAdmission).where(StockDataAdmission.product == "quotes")
            )
