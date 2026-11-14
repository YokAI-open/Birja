"""Real PostgreSQL journal, cutoff and shared-gate behavioral tests."""

import asyncio
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import DBAPIError

from app.models.corporate_action import StockActionState, StockOwnershipMovement
from app.models.trade import Holding
from app.services.corporate_action_rules import CutoffEvidence
from app.services.stock_ownership import (
    OwnershipHeld,
    StockMovementInput,
    acquire_stock_gate,
    append_stock_movement,
    assert_ownership_consistent,
    reconstruct_stock_quantity,
    require_supported_transaction_epoch,
)
from tests.stock_action_fixtures import ownership as _ownership_fixture
from tests.stock_action_fixtures import (
    synthetic_corruption,
    synthetic_fill,
    synthetic_opening,
    synthetic_split,
)
from tests.test_stock_action_migrations import runtime_roles as _runtime_roles

ownership = _ownership_fixture
runtime_roles = _runtime_roles


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
        movement = StockMovementInput(
            user_id, coin_id, Decimal(2), Decimal(20), "fill:" + str(trade.id), trade.id
        )
        await append_stock_movement(db, movement)
        return movement


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
    async with factory() as blocker, factory() as waiter:
        await acquire_stock_gate(blocker, coin_id)
        trade = await synthetic_fill(waiter, coin_id, ownership[2])
        movement = StockMovementInput(
            ownership[2], coin_id, Decimal(2), Decimal(20), "expiry-fill", trade.id
        )
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
        before = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        trade = await synthetic_fill(db, coin_id, user_id, created_at=before - timedelta(days=4))
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
            async with synthetic_corruption(db, "stock_ownership_movements"):
                row.sequence = 2
        elif drift == "baseline":
            await db.execute(
                update(StockActionState)
                .where(StockActionState.coin_id == coin_id)
                .values(complete_from=None)
            )
        else:
            async with synthetic_corruption(db, "stock_ownership_movements"):
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


async def test_reconstruction_sold_out_retains_past_entitlement(ownership):
    factory, coin_id, user_id = ownership
    async with factory.begin() as db:
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        cutoff = cutoff_at(now - timedelta(days=1))
        await synthetic_opening(db, coin_id, user_id, cutoff.cutoff - timedelta(seconds=1))
        trade = await synthetic_fill(db, coin_id, user_id, side="sell")
        await append_stock_movement(
            db, StockMovementInput(user_id, coin_id, Decimal(-2), Decimal(0), "sell", trade.id)
        )
        result = await reconstruct_stock_quantity(db, user_id, coin_id, cutoff, 0)
        assert result.quantity == Decimal(2)
        holding = (await db.execute(select(Holding).where(Holding.coin_id == coin_id))).scalar_one()
        assert holding.quantity == 0


async def split_history(db, coin_id, user_id):
    now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
    cutoff = cutoff_at(now - timedelta(days=1))
    await synthetic_opening(db, coin_id, user_id, cutoff.cutoff - timedelta(seconds=1))
    app = await synthetic_split(db, coin_id, cutoff.cutoff)
    await append_stock_movement(
        db,
        StockMovementInput(
            user_id, coin_id, Decimal(2), Decimal(20), "split:" + str(app.id), application_id=app.id
        ),
    )
    return cutoff, app


async def test_reconstruction_split_units_and_immutable_replay(ownership):
    factory, coin_id, user_id = ownership
    async with factory.begin() as db:
        cutoff, app = await split_history(db, coin_id, user_id)
        before = await reconstruct_stock_quantity(db, user_id, coin_id, cutoff, 0)
        after = await reconstruct_stock_quantity(db, user_id, coin_id, cutoff, 1)
        assert (before.quantity, after.quantity) == (Decimal(2), Decimal(4))
        assert before.last_movement_sequence == 1 and after.last_movement_sequence == 2
        row = await append_stock_movement(
            db,
            StockMovementInput(
                user_id,
                coin_id,
                Decimal(2),
                Decimal(20),
                "split:" + str(app.id),
                application_id=app.id,
            ),
        )
        assert row.sequence == 2
        later = await reconstruct_stock_quantity(
            db, user_id, coin_id, cutoff_at(cutoff.cutoff + timedelta(seconds=1)), 1
        )
        assert later.quantity == 4
        with pytest.raises(OwnershipHeld, match="ambiguous_units"):
            await reconstruct_stock_quantity(
                db, user_id, coin_id, cutoff_at(cutoff.cutoff + timedelta(seconds=1)), 0
            )


async def test_reconstruction_multi_owner_partial_split_is_held(ownership, new_user):
    factory, coin_id, user_id = ownership
    other = await new_user()
    async with factory.begin() as db:
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        cutoff = cutoff_at(now - timedelta(days=1))
        await synthetic_opening(db, coin_id, user_id, cutoff.cutoff - timedelta(seconds=2))
        await synthetic_opening(
            db, coin_id, other, cutoff.cutoff - timedelta(seconds=1), sequence=2
        )
        app = await synthetic_split(db, coin_id, cutoff.cutoff, boundary=2)
        for uid in (user_id, other):
            await append_stock_movement(
                db,
                StockMovementInput(
                    uid,
                    coin_id,
                    Decimal(2),
                    Decimal(20),
                    "split:" + str(app.id),
                    application_id=app.id,
                ),
            )
            if uid == user_id:
                with pytest.raises(OwnershipHeld, match="unit_gap"):
                    await reconstruct_stock_quantity(db, user_id, coin_id, cutoff, 1)
        assert (await reconstruct_stock_quantity(db, other, coin_id, cutoff, 1)).quantity == 4


@pytest.mark.parametrize(
    "damage",
    [
        "unit",
        "boundary",
        "split_time",
        "split_ratio",
        "epoch",
        "late_fill",
        "state_sequence",
        "uncharted_owner",
    ],
)
async def test_reconstruction_corrupt_units_or_causality_held(ownership, new_user, damage):
    factory, coin_id, user_id = ownership
    other = await new_user()
    async with factory() as db:
        cutoff, app = await split_history(db, coin_id, user_id)
        rows = (
            (
                await db.execute(
                    select(StockOwnershipMovement)
                    .where(StockOwnershipMovement.coin_id == coin_id)
                    .order_by(StockOwnershipMovement.sequence)
                )
            )
            .scalars()
            .all()
        )
        if damage == "unit":
            async with synthetic_corruption(db, "stock_ownership_movements"):
                rows[0].unit_epoch = 1
        elif damage == "boundary":
            app.sequence_boundary = 3
        elif damage == "split_time":
            async with synthetic_corruption(db, "stock_ownership_movements"):
                rows[1].economic_at += timedelta(seconds=1)
        elif damage == "split_ratio":
            app.new_rate = "3"
        elif damage == "epoch":
            (await db.get(StockActionState, coin_id)).unit_epoch = 2
        elif damage == "state_sequence":
            (await db.get(StockActionState, coin_id)).sequence = 9
        elif damage == "uncharted_owner":
            db.add(
                Holding(coin_id=coin_id, user_id=other, quantity=Decimal(1), cost_basis=Decimal(10))
            )
        else:
            trade = await synthetic_fill(db, coin_id, other)
            # A separate, unjournaled causal fill is an incomplete economic history.
            assert trade.id > 0
        await db.flush()
        with pytest.raises(OwnershipHeld):
            await reconstruct_stock_quantity(db, user_id, coin_id, cutoff, 0)


@pytest.mark.parametrize(
    "changes",
    [
        {"exclusive": False},
        {"rule": "guess"},
        {"exchange": "X"},
        {"calendar_generation": 0},
        {"calendar_version": ""},
        {"ex_date": None},
    ],
)
async def test_reconstruction_invalid_cutoff(ownership, changes):
    factory, coin_id, user_id = ownership
    async with factory() as db:
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        with pytest.raises(OwnershipHeld, match="invalid_cutoff"):
            await reconstruct_stock_quantity(
                db, user_id, coin_id, replace(cutoff_at(now), **changes), 0
            )


@pytest.mark.parametrize("days", [-6, 1])
async def test_reconstruction_unknown_coverage_or_future(ownership, days):
    factory, coin_id, user_id = ownership
    async with factory() as db:
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        with pytest.raises(OwnershipHeld, match="missing_baseline"):
            await reconstruct_stock_quantity(
                db, user_id, coin_id, cutoff_at(now + timedelta(days=days)), 0
            )


async def test_movement_committed_unmatched_fill_refused(ownership):
    factory, coin_id, user_id = ownership
    async with factory.begin() as db:
        async with (
            synthetic_corruption(db, "trades", trigger="stock_fill_integrity"),
            synthetic_corruption(db, "stock_fill_facts", trigger="stock_fill_integrity"),
        ):
            trade = await synthetic_fill(db, coin_id, user_id)
        movement = StockMovementInput(user_id, coin_id, Decimal(2), Decimal(20), "late", trade.id)
    async with factory() as db:
        with pytest.raises(OwnershipHeld, match="non_atomic_fill"):
            await append_stock_movement(db, movement)


async def test_movement_real_app_append_replay_and_authority_denied(
    engine, runtime_roles, new_user
):
    # Exact existing source statements; no widened test grants or schema change.
    from sqlalchemy import delete
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.models.stock import StockInstrument
    from app.models.stock_execution import StockFillFacts
    from app.models.trade import Trade

    factory = async_sessionmaker(engine, expire_on_commit=False)
    uid = await new_user()
    source = (Path(__file__).parents[2] / "deploy/db/bootstrap-roles.sql").read_text()
    grant_lines = [
        line
        for line in source.splitlines()
        if line.startswith("GRANT ") and line.endswith(" TO birja_app;")
    ]
    async with factory.begin() as db:
        for statement in grant_lines:
            await db.execute(text(statement))
        # Actual0009 conditional grant, already verified by02; use its source verbatim.
        statement = next(
            line.strip()
            for line in source.splitlines()
            if line.strip().startswith("GRANT SELECT ON stock_instruments,")
            and line.strip().endswith(" TO birja_app;")
        )
        await db.execute(text(statement))
        cid = (
            (await db.execute(select(StockInstrument.coin_id).order_by(StockInstrument.coin_id)))
            .scalars()
            .first()
        )
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        db.add(
            StockActionState(
                coin_id=cid,
                admission_generation=1,
                health="current",
                checked_at=now - timedelta(seconds=1),
                valid_until=now + timedelta(hours=1),
                journal_start_at=now - timedelta(days=1),
                complete_from=now - timedelta(days=1),
            )
        )
    try:
        async with factory.begin() as db:
            await db.execute(text("SET LOCAL ROLE birja_app"))
            trade = await synthetic_fill(db, cid, uid)
            request = StockMovementInput(uid, cid, Decimal(2), Decimal(20), "role-fill", trade.id)
            first = await append_stock_movement(db, request)
            assert first.sequence == 1
            assert (await append_stock_movement(db, request)).id == first.id
            cutoff = cutoff_at((await db.execute(select(func.clock_timestamp()))).scalar_one())
            assert (await reconstruct_stock_quantity(db, uid, cid, cutoff, 0)).quantity == 2
            with pytest.raises(DBAPIError) as error:
                async with db.begin_nested():
                    await db.execute(
                        update(StockActionState)
                        .where(StockActionState.coin_id == cid)
                        .values(health="unknown")
                    )
            assert error.value.orig.sqlstate == "42501"
    finally:
        async with factory.begin() as db:
            async with synthetic_corruption(db, "stock_fill_facts"):
                await db.execute(delete(StockFillFacts).where(StockFillFacts.coin_id == cid))
            async with synthetic_corruption(db, "stock_ownership_movements"):
                await db.execute(
                    delete(StockOwnershipMovement).where(StockOwnershipMovement.coin_id == cid)
                )
            await db.execute(delete(Holding).where(Holding.coin_id == cid))
            async with synthetic_corruption(db, "trades"):
                await db.execute(delete(Trade).where(Trade.coin_id == cid))
            await db.execute(delete(StockActionState).where(StockActionState.coin_id == cid))


@pytest.mark.parametrize(
    "damage", ["quantity", "side", "basis", "owner", "oversell", "emptybasis", "account"]
)
async def test_movement_fill_must_match_real_cause_and_result(ownership, new_user, damage):
    from sqlalchemy import delete

    from app.models.user import Account

    factory, cid, uid = ownership
    other = await new_user()
    async with factory() as db:
        if damage == "account":
            await db.execute(delete(Account).where(Account.user_id == uid))
        trade = await synthetic_fill(
            db, cid, uid, side="sell" if damage in ("oversell", "emptybasis", "side") else "buy"
        )
        request = StockMovementInput(uid, cid, Decimal(2), Decimal(20), "bad-fill", trade.id)
        if damage == "quantity":
            request = replace(request, quantity=Decimal(3))
        elif damage == "side":
            pass  # INSERT already supplies the mismatched sell cause.
        elif damage == "basis":
            request = replace(request, after_basis=Decimal(21))
        elif damage == "owner":
            request = replace(request, user_id=other)
        elif damage in ("oversell", "emptybasis"):
            request = replace(request, quantity=Decimal(-2), after_basis=Decimal(0))
        with pytest.raises(OwnershipHeld):
            await append_stock_movement(db, request)


@pytest.mark.parametrize("damage", ["missing", "basis", "ratio"])
async def test_movement_split_mismatch_held(ownership, damage):
    factory, cid, uid = ownership
    async with factory.begin() as db:
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        await synthetic_opening(db, cid, uid, now - timedelta(days=2))
        app = (
            await synthetic_split(db, cid, now - timedelta(days=1)) if damage != "missing" else None
        )
        request = StockMovementInput(
            uid,
            cid,
            Decimal(2),
            Decimal(21) if damage == "basis" else Decimal(20),
            "bad-split",
            application_id=app.id if app else 9007199254740991,
        )
        if damage == "ratio":
            request = replace(request, quantity=Decimal(3))
        with pytest.raises(OwnershipHeld, match="split_mismatch"):
            await append_stock_movement(db, request)


async def test_reconstruction_split_boundary_precedes_existing_movement_held(ownership):
    factory, cid, uid = ownership
    async with factory.begin() as db:
        cutoff, app = await split_history(db, cid, uid)
        app.cutoff -= timedelta(seconds=2)
        with pytest.raises(OwnershipHeld, match="unit_gap"):
            await reconstruct_stock_quantity(db, uid, cid, cutoff, 0)


async def test_movement_first_commit_duplicate_causal_lock_race(ownership, engine):
    factory, cid, uid = ownership
    async with factory() as first, factory() as second:
        trade = await synthetic_fill(first, cid, uid)
        request = StockMovementInput(uid, cid, Decimal(2), Decimal(20), "first-commit", trade.id)
        original = await append_stock_movement(first, request)
        pid = (await second.execute(select(func.pg_backend_pid()))).scalar_one()
        waiting = asyncio.create_task(append_stock_movement(second, request))
        await wait_blocked(engine, pid)
        await first.commit()
        replay = await asyncio.wait_for(waiting, 5)
        assert replay.id == original.id and replay.sequence == 1
        await second.commit()
    async with factory() as db:
        _, rows = await assert_ownership_consistent(db, cid)
        assert len(rows) == 1 and rows[0].after_quantity == 2


async def test_movement_concurrent_gap_commit_is_not_hidden_by_snapshot(ownership, engine):
    factory, cid, uid = ownership
    async with factory.begin() as db:
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        opening = await synthetic_opening(db, cid, uid, now - timedelta(days=1))
        opening_id = opening.id
    async with factory() as blocker, factory() as waiter:
        await acquire_stock_gate(blocker, cid)
        trade = await synthetic_fill(waiter, cid, uid)
        request = StockMovementInput(uid, cid, Decimal(2), Decimal(40), "gap-race", trade.id)
        pid = (await waiter.execute(select(func.pg_backend_pid()))).scalar_one()
        task = asyncio.create_task(append_stock_movement(waiter, request))
        await wait_blocked(engine, pid)
        async with synthetic_corruption(blocker, "stock_ownership_movements"):
            await blocker.execute(
                update(StockOwnershipMovement)
                .where(StockOwnershipMovement.id == opening_id)
                .values(sequence=2)
            )
        await blocker.commit()
        with pytest.raises(OwnershipHeld, match="history_gap"):
            await asyncio.wait_for(task, 5)
        await waiter.rollback()


async def test_lock_timeout_is_bounded_and_transaction_can_release(ownership, engine):
    factory, cid, _ = ownership
    async with factory() as blocker, factory() as waiter:
        await acquire_stock_gate(blocker, cid)
        pid = (await waiter.execute(select(func.pg_backend_pid()))).scalar_one()
        task = asyncio.create_task(acquire_stock_gate(waiter, cid))
        await wait_blocked(engine, pid)
        with pytest.raises(DBAPIError) as error:
            await asyncio.wait_for(task, 7)
        assert error.value.orig.sqlstate == "55P03"
        await waiter.rollback()
        await blocker.rollback()
    async with factory.begin() as db:
        await acquire_stock_gate(db, cid)


async def test_movement_committed_partial_split_not_adopted(ownership):
    factory, cid, uid = ownership
    async with factory.begin() as db:
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        await synthetic_opening(db, cid, uid, now - timedelta(days=2))
        app = await synthetic_split(db, cid, now - timedelta(days=1))
        request = StockMovementInput(
            uid, cid, Decimal(2), Decimal(20), "late-split", application_id=app.id
        )
    async with factory() as db:
        with pytest.raises(OwnershipHeld, match="non_atomic_split"):
            await append_stock_movement(db, request)


async def test_movement_same_transaction_savepoint_is_atomic(ownership):
    factory, cid, uid = ownership
    async with factory.begin() as db:
        await acquire_stock_gate(db, cid)
        async with db.begin_nested():
            trade = await synthetic_fill(db, cid, uid)
            row = await append_stock_movement(
                db,
                StockMovementInput(uid, cid, Decimal(2), Decimal(20), "savepoint-fill", trade.id),
            )
            assert row.sequence == 1
        _, rows = await assert_ownership_consistent(db, cid)
        assert len(rows) == 1


async def test_real_scheduler_can_validate_shared_ownership(engine, runtime_roles, ownership):
    factory, cid, _ = ownership
    source = (Path(__file__).parents[2] / "deploy/db/bootstrap-roles.sql").read_text()
    async with factory.begin() as db:
        statement = next(
            line.strip()
            for line in source.splitlines()
            if line.strip().startswith("GRANT SELECT ON stock_instruments,")
            and line.strip().endswith(" TO birja_scheduler;")
        )
        await db.execute(text(statement))
        await db.execute(text("SET LOCAL ROLE birja_scheduler"))
        state, rows = await assert_ownership_consistent(db, cid)
        assert state.unit_epoch == 0 and rows == []


@pytest.mark.parametrize("side", ["buy", "sell"])
async def test_reconstruction_old_unit_fill_exact_split_boundary_is_held(ownership, side):
    factory, cid, uid = ownership
    async with factory.begin() as db:
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        cutoff = cutoff_at(now - timedelta(days=1))
        await synthetic_opening(
            db,
            cid,
            uid,
            cutoff.cutoff - timedelta(seconds=1),
            quantity=Decimal(10),
            basis=Decimal(100),
        )
        trade = await synthetic_fill(db, cid, uid, quantity=Decimal(5), side=side)
        delta = Decimal(5 if side == "buy" else -5)
        quantity = Decimal(10) + delta
        basis = quantity * 10
        db.add(
            StockOwnershipMovement(
                coin_id=cid,
                user_id=uid,
                sequence=2,
                economic_at=cutoff.cutoff,
                recorded_at=cutoff.cutoff,
                quantity=delta,
                before_quantity=Decimal(10),
                after_quantity=quantity,
                before_basis=Decimal(100),
                after_basis=basis,
                unit_epoch=0,
                cause_kind="fill",
                trade_id=trade.id,
                causal_key="synthetic-same-boundary-fill",
            )
        )
        holding = (
            await db.execute(select(Holding).where(Holding.coin_id == cid, Holding.user_id == uid))
        ).scalar_one()
        holding.quantity = quantity
        holding.cost_basis = basis
        app = await synthetic_split(db, cid, cutoff.cutoff, boundary=2)
        db.add(
            StockOwnershipMovement(
                coin_id=cid,
                user_id=uid,
                sequence=3,
                economic_at=cutoff.cutoff,
                recorded_at=now,
                quantity=quantity,
                before_quantity=quantity,
                after_quantity=quantity * 2,
                before_basis=basis,
                after_basis=basis,
                unit_epoch=1,
                cause_kind="split",
                application_id=app.id,
                causal_key="synthetic-same-boundary-split",
            )
        )
        holding.quantity = quantity * 2
        await db.flush()
        with pytest.raises(OwnershipHeld, match="unit_gap"):
            await reconstruct_stock_quantity(db, uid, cid, cutoff, 1)


@pytest.mark.parametrize("full_xid", [False, 0, 2, 4294967296, 4294967297, 8589934592])
def test_atomic_cause_refuses_wrapped_transaction_epoch(full_xid):
    with pytest.raises(OwnershipHeld, match="transaction_epoch_unverified"):
        require_supported_transaction_epoch(full_xid)


@pytest.mark.parametrize("full_xid", [3, 4294967295])
def test_atomic_cause_first_transaction_epoch_supported(full_xid):
    assert require_supported_transaction_epoch(full_xid) is None


async def test_movement_other_transactions_pending_fill_is_not_owned(ownership):
    factory, cid, uid = ownership
    async with factory() as other, factory() as db:
        trade = await synthetic_fill(other, cid, uid)
        request = StockMovementInput(uid, cid, Decimal(2), Decimal(20), "other-pending", trade.id)
        with pytest.raises(OwnershipHeld, match="non_atomic_fill"):
            await append_stock_movement(db, request)
        await db.rollback()
        await other.rollback()
