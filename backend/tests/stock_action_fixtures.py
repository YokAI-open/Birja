"""Explicit synthetic ownership seeds. Never imported by application code."""

from contextlib import asynccontextmanager
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest_asyncio
from sqlalchemy import delete, func, select, text, update
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
from app.models.stock_execution import StockFillFacts
from app.models.trade import Holding, Trade


@asynccontextmanager
async def synthetic_corruption(db, table, *, trigger="stock_record_immutable"):
    """Privileged isolated corruption SETUP only; restore before tested reads.

    Failed DDL/DML aborts its transaction, so rollback restores trigger state.
    Never call around production behavior or a restricted-role assertion.
    """
    if table not in ("trades", "stock_fill_facts", "stock_ownership_movements") or trigger not in (
        "stock_record_immutable",
        "stock_fill_integrity",
    ):
        raise RuntimeError("Fixed corruption target required")
    allowed = (
        await db.execute(
            text("""SELECT current_database()='birja_test'
      AND current_user='birja_test' AND rolsuper FROM pg_roles WHERE rolname=current_user""")
        )
    ).scalar_one()
    if not allowed:
        raise RuntimeError("Privileged isolated corruption setup only")
    await db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    await db.execute(text(f"ALTER TABLE public.{table} DISABLE TRIGGER {trigger}"))
    try:
        yield
        await db.flush()
    finally:
        await db.execute(text(f"ALTER TABLE public.{table} ENABLE TRIGGER {trigger}"))


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
            # Explicit test-only DDL maintenance, never a production escape or
            # behavior-under-test. Transaction rollback restores trigger state
            # if cleanup fails; never disable ALL/constraint/FK triggers.
            allowed = (
                await db.execute(
                    text("""SELECT current_database()='birja_test'
              AND current_user='birja_test' AND rolsuper FROM pg_roles
              WHERE rolname=current_user""")
                )
            ).scalar_one()
            if not allowed:
                raise RuntimeError("Test-only immutable cleanup identity required")
            for table in ("stock_fill_facts", "stock_ownership_movements", "trades"):
                await db.execute(
                    text(f"ALTER TABLE public.{table} DISABLE TRIGGER stock_record_immutable")
                )
            await db.execute(delete(StockFillFacts).where(StockFillFacts.coin_id == coin_id))
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
            for table in ("stock_fill_facts", "stock_ownership_movements", "trades"):
                await db.execute(
                    text(f"ALTER TABLE public.{table} ENABLE TRIGGER stock_record_immutable")
                )


async def synthetic_fill(db, coin_id, user_id, *, quantity=Decimal(2), side="buy", created_at=None):
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
        **({"created_at": created_at} if created_at is not None else {}),
    )
    db.add(trade)
    await db.flush()
    held = (
        await db.execute(
            select(Holding.quantity).where(Holding.coin_id == coin_id, Holding.user_id == user_id)
        )
    ).scalar_one_or_none() or Decimal(0)
    db.add(
        StockFillFacts(
            trade_id=trade.id,
            coin_id=coin_id,
            user_id=user_id,
            provider_asset_id="synthetic-asset",
            symbol="SYNTH",
            company_name="Synthetic fixture",
            listing_exchange="NASDAQ",
            source="alpaca",
            feed="iex",
            bid=Decimal(10),
            ask=Decimal(10),
            exact_mid=Decimal(10),
            # Invalid oversell fixtures are rolled back by refusal tests before
            # any movement; keep receipt locally valid to reach that behavior.
            held_after=max(Decimal(0), held + (quantity if side == "buy" else -quantity)),
            event_at=now,
            collected_at=now,
            observed_at=now,
            session_date=now.date(),
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(hours=1),
            authority={},
        )
    )
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
