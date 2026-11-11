"""Explicit synthetic ownership seeds. Never imported by application code."""

from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest_asyncio
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.corporate_action import (
    StockActionEvent,
    StockActionRevision,
    StockActionSource,
    StockActionState,
    StockOwnershipMovement,
    StockSplitApplication,
)
from app.models.stock import StockInstrument
from app.models.trade import Holding, Trade


@pytest_asyncio.fixture
async def ownership(engine, migrated, new_user):
    user_id = await new_user()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory.begin() as db:
        coin_id = (
            (await db.execute(select(StockInstrument.coin_id).order_by(StockInstrument.coin_id)))
            .scalars()
            .first()
        )
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        db.add(
            StockActionState(
                coin_id=coin_id,
                admission_generation=1,
                health="current",
                checked_at=now - timedelta(seconds=1),
                valid_until=now + timedelta(hours=1),
                journal_start_at=now - timedelta(days=5),
                complete_from=now - timedelta(days=5),
                coverage_start=now - timedelta(days=5),
                covered_until=now,
            )
        )
    try:
        yield factory, coin_id, user_id
    finally:
        async with factory.begin() as db:
            await db.execute(
                delete(StockOwnershipMovement).where(StockOwnershipMovement.coin_id == coin_id)
            )
            await db.execute(
                delete(StockSplitApplication).where(StockSplitApplication.coin_id == coin_id)
            )
            events = select(StockActionEvent.id).where(StockActionEvent.coin_id == coin_id)
            await db.execute(
                update(StockActionEvent)
                .where(StockActionEvent.coin_id == coin_id)
                .values(current_revision_id=None)
            )
            await db.execute(
                delete(StockActionRevision).where(StockActionRevision.event_id.in_(events))
            )
            await db.execute(
                delete(StockActionSource).where(StockActionSource.event_id.in_(events))
            )
            await db.execute(delete(StockActionEvent).where(StockActionEvent.coin_id == coin_id))
            await db.execute(delete(Holding).where(Holding.coin_id == coin_id))
            await db.execute(delete(Trade).where(Trade.coin_id == coin_id))
            await db.execute(delete(StockActionState).where(StockActionState.coin_id == coin_id))


async def synthetic_fill(db, coin_id, user_id, *, quantity=Decimal(2), side="buy"):
    """Fill-like caller only; no production cash service or stock execution."""
    now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
    trade = Trade(
        coin_id=coin_id,
        user_id=user_id,
        side=side,
        input_kind="quantity",
        input_value=quantity,
        quantity=quantity,
        mid_price=Decimal(10),
        price_as_of=now,
        exec_price=Decimal(10),
        fee=Decimal(0),
        cash_delta=quantity * Decimal(-10 if side == "buy" else 10),
        cash_after=Decimal(10000),
        idempotency_key=uuid4(),
    )
    db.add(trade)
    await db.flush()
    return trade


async def synthetic_opening(
    db, coin_id, user_id, at, *, quantity=Decimal(2), basis=Decimal(20), sequence=1
):
    """Test-only prehistory; deliberately unavailable from production services."""
    row = StockOwnershipMovement(
        coin_id=coin_id,
        user_id=user_id,
        sequence=sequence,
        economic_at=at,
        recorded_at=at,
        quantity=quantity,
        before_quantity=Decimal(0),
        after_quantity=quantity,
        before_basis=Decimal(0),
        after_basis=basis,
        unit_epoch=0,
        cause_kind="opening",
        causal_key="synthetic-opening:" + str(user_id),
    )
    db.add(row)
    db.add(Holding(coin_id=coin_id, user_id=user_id, quantity=quantity, cost_basis=basis))
    await db.flush()
    return row


async def synthetic_split(db, coin_id, cutoff, *, boundary=1, prior_epoch=0):
    """Explicit matched event/revision/application; never false-causal shortcuts."""
    event = StockActionEvent(coin_id=coin_id, economic_key=str(uuid4()), first_observed_at=cutoff)
    db.add(event)
    await db.flush()
    source = StockActionSource(
        event_id=event.id, provider="synthetic", product="actions", provider_event_id=str(uuid4())
    )
    db.add(source)
    await db.flush()
    revision = StockActionRevision(
        event_id=event.id,
        source_id=source.id,
        ordinal=1,
        fingerprint="a" * 64,
        mutation_kind="snapshot",
        observed_at=cutoff,
        admission_generation=1,
        normalized_terms={"synthetic": True},
        classification="supported_forward_split",
        reason="verified synthetic fixture",
        verified_cutoff=cutoff,
        units="pre_split",
    )
    db.add(revision)
    await db.flush()
    event.current_revision_id = revision.id
    now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
    application = StockSplitApplication(
        coin_id=coin_id,
        economic_event_id=event.id,
        revision_id=revision.id,
        new_rate="2",
        old_rate="1",
        cutoff=cutoff,
        prior_unit_epoch=prior_epoch,
        new_unit_epoch=prior_epoch + 1,
        sequence_boundary=boundary,
        before_digest="b" * 64,
        after_digest="c" * 64,
        processed_at=now,
    )
    db.add(application)
    state = await db.get(StockActionState, coin_id)
    state.unit_epoch = prior_epoch + 1
    await db.flush()
    return application
