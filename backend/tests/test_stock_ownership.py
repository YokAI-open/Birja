"""Real PostgreSQL journal, cutoff and shared-gate behavioral tests."""

import asyncio
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select, text, update

from app.models.corporate_action import StockActionState, StockOwnershipMovement
from app.models.trade import Holding
from app.services.stock_ownership import (
    OwnershipHeld,
    StockMovementInput,
    acquire_stock_gate,
    append_stock_movement,
    assert_ownership_consistent,
    reconstruct_stock_quantity,
)
from app.services.corporate_action_rules import CutoffEvidence
from tests.stock_action_fixtures import synthetic_fill, synthetic_opening

pytest_plugins = ["tests.stock_action_fixtures"]


async def test_movement_updates_holding_once_and_replays(ownership):
    factory, coin_id, user_id = ownership
    async with factory.begin() as db:
        trade = await synthetic_fill(db, coin_id, user_id)
        movement = StockMovementInput(
            user_id, coin_id, Decimal(2), Decimal(20), "fill:" + str(trade.id), trade.id
        )
        first = await append_stock_movement(db, movement)
        replay = await append_stock_movement(db, movement)
        assert first.id == replay.id
        holding = (
            await db.execute(
                select(Holding).where(Holding.user_id == user_id, Holding.coin_id == coin_id)
            )
        ).scalar_one()
        assert (holding.quantity, holding.cost_basis) == (Decimal(2), Decimal(20))


async def filled(ownership):
    factory, coin_id, user_id = ownership
    async with factory.begin() as db:
        trade = await synthetic_fill(db, coin_id, user_id)
        return StockMovementInput(
            user_id, coin_id, Decimal(2), Decimal(20), "fill:" + str(trade.id), trade.id
        )


async def test_movement_race_same_cause_one_effect(ownership):
    factory, coin_id, _ = ownership
    movement = await filled(ownership)

    async def append():
        async with factory.begin() as db:
            return (await append_stock_movement(db, movement)).id

    results = await asyncio.wait_for(asyncio.gather(*(append() for _ in range(4))), 10)
    assert len(set(results)) == 1
    async with factory() as db:
        assert (
            await db.execute(
                select(func.count())
                .select_from(StockOwnershipMovement)
                .where(StockOwnershipMovement.coin_id == coin_id)
            )
        ).scalar_one() == 1


@pytest.mark.parametrize(
    "changes", [{"quantity": Decimal(3)}, {"after_basis": Decimal(30)}, {"causal_key": "different"}]
)
async def test_movement_replay_conflicts(ownership, changes):
    factory, _, _ = ownership
    movement = await filled(ownership)
    async with factory.begin() as db:
        await append_stock_movement(db, movement)
    async with factory.begin() as db:
        with pytest.raises(OwnershipHeld, match="causal_conflict"):
            await append_stock_movement(db, replace(movement, **changes))


@pytest.mark.parametrize(
    "changes",
    [
        {"user_id": True},
        {"quantity": Decimal("NaN")},
        {"quantity": Decimal("Infinity")},
        {"quantity": Decimal("1.5")},
        {"quantity": Decimal(0)},
        {"quantity": Decimal("1e12")},
        {"quantity": 1},
        {"after_basis": Decimal("1.001")},
        {"after_basis": Decimal("1e12")},
        {"causal_key": ""},
        {"trade_id": None},
        {"trade_id": True},
    ],
)
async def test_movement_invalid_payload_refused(ownership, changes):
    factory, _, _ = ownership
    movement = await filled(ownership)
    async with factory.begin() as db:
        with pytest.raises(OwnershipHeld, match="invalid_movement"):
            await append_stock_movement(db, replace(movement, **changes))


async def wait_blocked(engine, pid):
    """Observe an actual server lock waiter; delay alone is never the assertion."""
    async with asyncio.timeout(4):
        while True:
            async with engine.connect() as conn:
                if (
                    await conn.execute(
                        text("SELECT cardinality(pg_blocking_pids(:pid))>0"), {"pid": pid}
                    )
                ).scalar_one():
                    return
            await asyncio.sleep(0.01)


@pytest.mark.parametrize("expired", ["valid_until", "next_blocking_at"])
async def test_lock_race_reads_post_lock_expiry(ownership, engine, expired):
    factory, coin_id, _ = ownership
    movement = await filled(ownership)
    async with factory() as blocker, factory() as waiter:
        await acquire_stock_gate(blocker, coin_id)
        pid = (await waiter.execute(select(func.pg_backend_pid()))).scalar_one()
        task = asyncio.create_task(append_stock_movement(waiter, movement))
        await wait_blocked(engine, pid)
        # Commit changed authority while the real append is waiting on our gate.
        await blocker.execute(
            update(StockActionState)
            .where(StockActionState.coin_id == coin_id)
            .values({expired: func.clock_timestamp()})
        )
        await blocker.commit()
        with pytest.raises(OwnershipHeld, match="monitor_unavailable"):
            await asyncio.wait_for(task, 5)
        await waiter.rollback()


async def test_lock_cancellation_releases_and_next_transaction_succeeds(ownership, engine):
    factory, coin_id, _ = ownership
    async with factory() as blocker, factory() as waiter:
        await acquire_stock_gate(blocker, coin_id)
        pid = (await waiter.execute(select(func.pg_backend_pid()))).scalar_one()
        task = asyncio.create_task(acquire_stock_gate(waiter, coin_id))
        await wait_blocked(engine, pid)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await waiter.rollback()
        await blocker.rollback()
    async with factory.begin() as db:
        await asyncio.wait_for(acquire_stock_gate(db, coin_id), 2)


async def test_movement_rollback_and_actual_clock_ignore_ingestion(ownership):
    factory, coin_id, user_id = ownership
    async with factory() as db:
        trade = await synthetic_fill(db, coin_id, user_id)
        trade.created_at = trade.price_as_of - timedelta(days=4)
        before = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        row = await append_stock_movement(
            db, StockMovementInput(user_id, coin_id, Decimal(2), Decimal(20), "fill", trade.id)
        )
        assert row.economic_at >= before > trade.created_at
        await db.rollback()
    async with factory() as db:
        assert (
            await db.execute(
                select(func.count()).select_from(Holding).where(Holding.coin_id == coin_id)
            )
        ).scalar_one() == 0


async def test_gate_one_instrument_and_transaction_reset(ownership):
    factory, coin_id, _ = ownership
    async with factory() as db:
        await acquire_stock_gate(db, coin_id)
        with pytest.raises(OwnershipHeld, match="one_instrument"):
            await acquire_stock_gate(db, coin_id + 1)
        await db.rollback()
        await acquire_stock_gate(db, coin_id + 1)


@pytest.mark.parametrize("coin", [False, 0, -1, 9007199254740992])
async def test_gate_invalid_instrument(ownership, coin):
    async with ownership[0]() as db:
        with pytest.raises(OwnershipHeld, match="invalid_instrument"):
            await acquire_stock_gate(db, coin)


async def test_gate_nonstock_and_repeatable_read_refused(ownership):
    async with ownership[0]() as db:
        with pytest.raises(OwnershipHeld, match="invalid_instrument"):
            await acquire_stock_gate(db, 9007199254740990)
        await db.rollback()
        await db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
        with pytest.raises(OwnershipHeld, match="read_committed_required"):
            await acquire_stock_gate(db, ownership[1])


@pytest.mark.parametrize("drift", ["holding", "basis", "sequence", "baseline", "backdate"])
async def test_movement_integrity_held_for_global_drift(ownership, drift):
    factory, coin_id, user_id = ownership
    movement = await filled(ownership)
    async with factory.begin() as db:
        row = await append_stock_movement(db, movement)
        if drift == "holding":
            await db.execute(update(Holding).where(Holding.coin_id == coin_id).values(quantity=3))
        elif drift == "basis":
            await db.execute(
                update(Holding).where(Holding.coin_id == coin_id).values(cost_basis=21)
            )
        elif drift == "sequence":
            row.sequence = 2
        elif drift == "baseline":
            await db.execute(
                update(StockActionState)
                .where(StockActionState.coin_id == coin_id)
                .values(complete_from=None)
            )
        else:
            row.economic_at = row.economic_at - timedelta(days=6)
    async with factory() as db:
        with pytest.raises(OwnershipHeld):
            await assert_ownership_consistent(db, coin_id)


def cutoff_at(at):
    return CutoffEvidence(at, "NASDAQ", at.date(), 1, "synthetic-reviewed-calendar")


@pytest.mark.parametrize("offset,expected", [(-1, 2), (0, 0), (1, 0)])
async def test_reconstruction_exclusive_cutoff(ownership, offset, expected):
    factory, coin_id, user_id = ownership
    async with factory.begin() as db:
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        cutoff = cutoff_at(now - timedelta(days=1))
        await synthetic_opening(db, coin_id, user_id, cutoff.cutoff + timedelta(seconds=offset))
        result = await reconstruct_stock_quantity(db, user_id, coin_id, cutoff, 0)
        assert result.quantity == Decimal(expected)
        assert result.cutoff == cutoff
