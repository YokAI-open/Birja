"""Actual isolated PostgreSQL corporate-action financial invariants."""

import asyncio
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select, update

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
from app.services.corporate_actions import ActionHeld, apply_due_actions, persist_action_batch
from tests.stock_action_fixtures import ownership as _ownership
from tests.stock_action_fixtures import synthetic_opening
from tests.test_corporate_action_rules import dividend
from tests.test_stock_admission import action_admitted

ownership = _ownership


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
