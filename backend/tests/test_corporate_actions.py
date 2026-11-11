"""Actual isolated PostgreSQL corporate-action financial invariants."""

from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select, update

from app.models.corporate_action import (
    StockActionEvent,
    StockActionObservation,
    StockActionRevision,
    StockActionState,
    StockDividendEntitlement,
)
from app.models.price import Coin
from app.models.stock import StockDataAdmission, StockInstrument
from app.services.alpaca_actions import ActionBatch, ActionCoverage, ActionObservation
from app.services.corporate_actions import ActionHeld, persist_action_batch
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
