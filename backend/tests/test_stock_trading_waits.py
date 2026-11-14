# ruff: noqa: F811
"""Actual independent PostgreSQL waits around financial and authority boundaries."""

import asyncio
from decimal import Decimal

import pytest
from sqlalchemy import func, select, text

from app.services import stock_trading
from tests.stock_trade_fixtures import ownership, status_case, stock_trade_case  # noqa: F401
from tests.test_stock_status import financial_snapshot
from tests.test_stock_trading_service import trade_order


async def wait_for_lock(factory, pid, task):
    async with asyncio.timeout(5):
        while True:
            if task.done():
                await task
                raise AssertionError("Writer never reached the PostgreSQL wait")
            async with factory() as db:
                waiting = await db.scalar(select(func.cardinality(func.pg_blocking_pids(pid))))
            if waiting:
                return
            await asyncio.sleep(0.01)


@pytest.mark.parametrize("boundary", ["helper_read", "helper_flush"])
async def test_opposite_side_quote_after_staging_needs_no_reconfirmation(
    stock_trade_case, settings, monkeypatch, boundary
):
    factory, cid, uid, now = stock_trade_case
    gate = 91090701
    async with factory() as writer, factory() as blocker:
        await blocker.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": gate})
        pid = await writer.scalar(select(func.pg_backend_pid()))
        real_execute, real_flush = writer.execute, writer.flush
        blocked = False
        flushes = 0

        async def execute(statement, *args, **kwargs):
            nonlocal blocked
            if (
                boundary == "helper_read"
                and not blocked
                and "stock_ownership_movements.causal_key" in str(statement)
            ):
                blocked = True
                await real_execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": gate})
            return await real_execute(statement, *args, **kwargs)

        async def flush(*args, **kwargs):
            nonlocal blocked, flushes
            flushes += 1
            if boundary == "helper_flush" and not blocked and flushes == 2:
                blocked = True
                await real_execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": gate})
            return await real_flush(*args, **kwargs)

        monkeypatch.setattr(writer, "execute", execute)
        monkeypatch.setattr(writer, "flush", flush)
        task = asyncio.create_task(
            stock_trading.execute(writer, user_id=uid, order=trade_order(), settings=settings)
        )
        try:
            await wait_for_lock(factory, pid, task)
            async with factory.begin() as editor:
                await editor.execute(
                    text("UPDATE stock_quotes SET bid=101,mid=101.5 WHERE coin_id=:cid"),
                    {"cid": cid},
                )
            await blocker.rollback()
            fill, created = await asyncio.wait_for(task, 10)
            assert (
                created
                and fill.bid == 101
                and fill.ask == 102
                and fill.exact_mid == Decimal("101.5")
            )
            assert fill.cash_after == 9796 and fill.held_after == 2
        finally:
            await blocker.rollback()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)


MUTATIONS = {
    "permission": "UPDATE stock_data_admissions SET state='denied' WHERE product='quotes'",
    "quote_stale": "UPDATE stock_quotes SET event_at=clock_timestamp()-interval '120 seconds'",
    "selected": "UPDATE stock_quotes SET ask=103,mid=101.5",
    "opposite": "UPDATE stock_quotes SET bid=101,mid=101.5",
    "halt": "UPDATE stock_status_evidence SET state='halted'",
    "continuity": "UPDATE stock_status_evidence SET continuity_current=false",
    "status_expiry": (
        "UPDATE stock_status_evidence SET valid_until=clock_timestamp()-interval '1 millisecond'"
    ),
    "action": "UPDATE stock_action_state SET health='unknown'",
    "cutoff": (
        "UPDATE stock_action_state SET next_blocking_at=clock_timestamp()-interval '1 millisecond'"
    ),
    "units": "UPDATE stock_action_state SET unit_epoch=1",
    "close": (
        "UPDATE stock_sessions SET closes_at=clock_timestamp()-interval '1 millisecond' "
        "WHERE session_date=current_date"
    ),
}


MUTATIONS.update(
    {
        "attribution": (
            "UPDATE stock_data_admissions SET attribution='changed' WHERE product='quotes'"
        ),
        "safety_epoch": "UPDATE stock_action_state SET epoch=epoch+1",
        "status_sequence": "UPDATE stock_status_evidence SET sequence=sequence+1",
    }
)


@pytest.mark.parametrize(
    "boundary,mutation",
    [
        (boundary, mutation)
        for boundary in (
            "instrument",
            "account",
            "holding",
            "helper_flush",
            "constraints",
            "final_guard",
        )
        for mutation in MUTATIONS
        if mutation not in ("attribution", "safety_epoch", "status_sequence")
    ]
    + [
        (boundary, mutation)
        for boundary in ("constraints", "final_guard")
        for mutation in ("attribution", "safety_epoch", "status_sequence")
    ],
)
async def test_adversarial_change_at_actual_wait_boundary(
    stock_trade_case, settings, monkeypatch, boundary, mutation
):
    from app.models.trade import Holding
    from app.models.user import Account
    from app.services.stock_ownership import acquire_stock_gate
    from app.services.trade_math import TradeRefused

    factory, cid, uid, now = stock_trade_case
    # A real existing holding makes the helper's sorted row lock observable.
    async with factory() as db:
        await stock_trading.execute(
            db, user_id=uid, order=trade_order(quantity="1"), settings=settings
        )
    before = await financial_snapshot(factory)
    gate = 91090702
    async with factory() as writer, factory() as blocker:
        pid = await writer.scalar(select(func.pg_backend_pid()))
        real_execute, real_flush = writer.execute, writer.flush
        blocked, flushes = False, 0
        if boundary == "instrument":
            await acquire_stock_gate(blocker, cid)
        elif boundary == "account":
            await blocker.execute(
                select(Account.user_id).where(Account.user_id == uid).with_for_update()
            )
        elif boundary == "holding":
            await blocker.execute(
                select(Holding.id)
                .where(Holding.user_id == uid, Holding.coin_id == cid)
                .with_for_update()
            )
        else:
            await blocker.execute(text("SELECT pg_advisory_xact_lock(:gate)"), {"gate": gate})

        async def execute(statement, *args, **kwargs):
            nonlocal blocked
            if (
                boundary == "constraints"
                and not blocked
                and "SET CONSTRAINTS ALL IMMEDIATE" in str(statement)
            ):
                blocked = True
                await real_execute(text("SELECT pg_advisory_xact_lock(:gate)"), {"gate": gate})
            if (
                boundary == "final_guard"
                and not blocked
                and "SELECT public.assert_stock_execution_current" in str(statement)
            ):
                blocked = True
                await real_execute(text("SELECT pg_advisory_xact_lock(:gate)"), {"gate": gate})
            return await real_execute(statement, *args, **kwargs)

        async def flush(*args, **kwargs):
            nonlocal blocked, flushes
            flushes += 1
            if boundary == "helper_flush" and not blocked and flushes == 2:
                blocked = True
                await real_execute(text("SELECT pg_advisory_xact_lock(:gate)"), {"gate": gate})
            return await real_flush(*args, **kwargs)

        monkeypatch.setattr(writer, "execute", execute)
        monkeypatch.setattr(writer, "flush", flush)
        task = asyncio.create_task(
            stock_trading.execute(writer, user_id=uid, order=trade_order(), settings=settings)
        )
        try:
            await wait_for_lock(factory, pid, task)
            # The instrument/cash/holding writer locks remain held. These are
            # independently committed authority changes, not mocked evidence.
            async with factory.begin() as editor:
                await editor.execute(text(MUTATIONS[mutation]))
            await blocker.commit()
            if mutation == "opposite":
                fill, created = await asyncio.wait_for(task, 10)
                assert created and fill.bid == 101 and fill.ask == 102
                assert fill.cash_after == 9694 and fill.held_after == 3
            else:
                with pytest.raises(TradeRefused) as exc:
                    await asyncio.wait_for(task, 10)
                if mutation == "selected":
                    assert exc.value.code == "price_changed"
                    assert exc.value.detail.quote.exec_price == 103
                assert await financial_snapshot(factory) == before
        finally:
            await blocker.rollback()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        assert not writer.in_transaction()


@pytest.mark.parametrize("offset,expected", [(-1, 0), (0, 0), (1, 2)])
async def test_actual_first_fill_has_exclusive_dividend_ownership_boundary(
    stock_trade_case, settings, offset, expected
):
    from datetime import timedelta

    from app.services.stock_ownership import reconstruct_stock_quantity
    from tests.test_stock_ownership import cutoff_at

    factory, cid, uid, now = stock_trade_case
    order = trade_order()
    async with factory() as db:
        fill, _ = await stock_trading.execute(db, user_id=uid, order=order, settings=settings)
        await stock_trading.execute(
            db,
            user_id=uid,
            order=trade_order(side="sell", expected_exec_price="100"),
            settings=settings,
        )
    async with factory.begin() as db:
        quantity = await reconstruct_stock_quantity(
            db, uid, cid, cutoff_at(fill.executed_at + timedelta(microseconds=offset)), 0
        )
        assert quantity.quantity == expected
    # Sold-out current holdings never erase a historical original receipt.
    async with factory() as db:
        again, created = await stock_trading.execute(
            db, user_id=uid, order=order, settings=settings
        )
        assert not created and again == fill and again.held_after == 2


async def test_actual_first_fill_then_matched_forward_split_preserves_units_and_receipt(
    stock_trade_case, settings
):
    from datetime import timedelta

    from sqlalchemy import update

    from app.models.corporate_action import StockActionState
    from app.models.stock import StockQuote
    from app.services.stock_ownership import (
        StockMovementInput,
        append_stock_movement,
        reconstruct_stock_quantity,
    )
    from tests.stock_action_fixtures import synthetic_split
    from tests.test_stock_ownership import cutoff_at

    factory, cid, uid, now = stock_trade_case
    order = trade_order()
    async with factory() as db:
        fill, _ = await stock_trading.execute(db, user_id=uid, order=order, settings=settings)
    async with factory.begin() as db:
        cutoff = await db.scalar(select(func.clock_timestamp()))
        # The synthetic terms are explicit; the causal application, ownership
        # transition, immutable journal and subsequent stock service are real.
        application = await synthetic_split(db, cid, cutoff, boundary=1)
        await append_stock_movement(
            db,
            StockMovementInput(
                uid,
                cid,
                Decimal(2),
                Decimal(204),
                "split:" + str(application.id),
                application_id=application.id,
            ),
        )
        await db.execute(
            update(StockActionState)
            .where(StockActionState.coin_id == cid)
            .values(quote_not_before=cutoff, next_blocking_at=None)
        )
        quote_at = await db.scalar(select(func.clock_timestamp()))
        await db.execute(
            update(StockQuote)
            .where(StockQuote.coin_id == cid)
            .values(
                bid=Decimal(50),
                ask=Decimal(51),
                mid=Decimal("50.5"),
                unit_epoch=1,
                event_at=quote_at,
                collected_at=quote_at,
            )
        )
        old = await reconstruct_stock_quantity(db, uid, cid, cutoff_at(cutoff), 0)
        new = await reconstruct_stock_quantity(db, uid, cid, cutoff_at(cutoff), 1)
        assert old.quantity == 2 and new.quantity == 4
    async with factory() as db:
        again, created = await stock_trading.execute(
            db, user_id=uid, order=order, settings=settings
        )
        assert not created and again == fill
        sale, created = await stock_trading.execute(
            db,
            user_id=uid,
            order=trade_order(side="sell", quantity="4", expected_exec_price="50"),
            settings=settings,
        )
        assert created and sale.held_before == 4 and sale.held_after == 0
        assert sale.cash_after == 9996 and sale.authority.unit_epoch == 1
    async with factory.begin() as db:
        historical = await reconstruct_stock_quantity(
            db, uid, cid, cutoff_at(cutoff + timedelta(microseconds=1)), 1
        )
        assert historical.quantity == 4


async def test_final_guard_is_last_business_statement(stock_trade_case, settings, monkeypatch):
    import inspect

    factory, cid, uid, now = stock_trade_case
    calls = []
    async with factory() as db:
        real_execute, real_flush, real_commit = db.execute, db.flush, db.commit

        async def execute(statement, *args, **kwargs):
            calls.append(str(statement))
            return await real_execute(statement, *args, **kwargs)

        async def flush(*args, **kwargs):
            calls.append("flush")
            return await real_flush(*args, **kwargs)

        async def commit():
            calls.append("commit")
            return await real_commit()

        monkeypatch.setattr(db, "execute", execute)
        monkeypatch.setattr(db, "flush", flush)
        monkeypatch.setattr(db, "commit", commit)
        await stock_trading.execute(db, user_id=uid, order=trade_order(), settings=settings)
    assert calls[-2].startswith("SELECT public.assert_stock_execution_current")
    assert calls[-1] == "commit"
    assert calls[-3] == "SET CONSTRAINTS ALL IMMEDIATE"
    source = inspect.getsource(stock_trading._execute_once)
    tail = source.split('"SELECT public.assert_stock_execution_current', 1)[1].split(
        "except IntegrityError", 1
    )[0]
    assert tail.count("await ") == 1 and "await db.commit()" in tail


async def test_cancellation_during_actual_account_wait_releases_everything(
    stock_trade_case, settings
):
    from app.models.user import Account

    factory, cid, uid, now = stock_trade_case
    before = await financial_snapshot(factory)
    async with factory() as writer, factory() as blocker:
        await blocker.execute(
            select(Account.user_id).where(Account.user_id == uid).with_for_update()
        )
        pid = await writer.scalar(select(func.pg_backend_pid()))
        task = asyncio.create_task(
            stock_trading.execute(writer, user_id=uid, order=trade_order(), settings=settings)
        )
        try:
            await wait_for_lock(factory, pid, task)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert not writer.in_transaction()
        finally:
            await blocker.rollback()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    assert await financial_snapshot(factory) == before
    async with factory() as db:
        _, created = await stock_trading.execute(
            db, user_id=uid, order=trade_order(), settings=settings
        )
        assert created


async def test_runtime_calls_wrapped_xid_refusal_before_financial_commit(
    stock_trade_case, settings, monkeypatch
):
    from app.services import stock_ownership
    from app.services.trade_math import TradeRefused

    factory, cid, uid, now = stock_trade_case
    before = await financial_snapshot(factory)
    original = stock_ownership.require_supported_transaction_epoch
    seen = []

    def reject_wrapped(actual):
        seen.append(actual)
        # Inject only the epoch guard input; never pretend to wrap PostgreSQL.
        return original(2**32)

    monkeypatch.setattr(stock_ownership, "require_supported_transaction_epoch", reject_wrapped)
    async with factory() as db:
        with pytest.raises(TradeRefused) as exc:
            await stock_trading.execute(db, user_id=uid, order=trade_order(), settings=settings)
        assert exc.value.code == "action_unavailable" and len(seen) == 1
    assert await financial_snapshot(factory) == before


async def test_actual_action_processor_waits_for_first_fill_gate(
    stock_trade_case, settings, monkeypatch
):
    from dataclasses import replace
    from datetime import timedelta

    from app.services import corporate_actions
    from tests.test_corporate_action_rules import dividend
    from tests.test_corporate_actions import batch, split_action

    factory, cid, uid, now = stock_trade_case
    # The event is known before its future cutoff, so no late historical event
    # is invented. Current action monitoring remains independent of fills.
    cutoff = now + timedelta(seconds=1)
    async with factory.begin() as db:
        admission = await corporate_actions._load_admission(db, "actions")
        action = replace(dividend(), coin_id=cid, symbol="AAPL", observed_at=now)
        await corporate_actions.persist_action_batch(
            db, batch(split_action(action, cutoff)), admission
        )
    # Hold the first real fill immediately after its final guard. The processor
    # must wait for its instrument gate, never invent opening ownership.
    ready, release = asyncio.Event(), asyncio.Event()
    order = trade_order()
    async with factory() as writer, factory() as processor:
        real_commit = writer.commit

        async def commit():
            ready.set()
            await release.wait()
            return await real_commit()

        monkeypatch.setattr(writer, "commit", commit)
        fill_task = asyncio.create_task(
            stock_trading.execute(writer, user_id=uid, order=order, settings=settings)
        )
        processor_task = None
        try:
            await asyncio.wait_for(ready.wait(), 5)
            await processor.execute(
                text(
                    "SELECT pg_sleep(GREATEST(0,EXTRACT(EPOCH FROM "
                    "CAST(:cutoff AS timestamptz)-clock_timestamp()))+0.01)"
                ),
                {"cutoff": cutoff},
            )
            pid = await processor.scalar(select(func.pg_backend_pid()))
            processor_task = asyncio.create_task(
                corporate_actions.apply_due_actions(processor, cid)
            )
            await wait_for_lock(factory, pid, processor_task)
            release.set()
            fill, created = await asyncio.wait_for(fill_task, 5)
            assert created and fill.executed_at < cutoff
            applications = await asyncio.wait_for(processor_task, 5)
            await processor.commit()
            assert len(applications) == 1
        finally:
            release.set()
            for task in (fill_task, processor_task):
                if task is not None:
                    if not task.done():
                        task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
            await processor.rollback()
    from app.models.trade import Holding

    async with factory() as db:
        row = (
            await db.execute(
                select(Holding.quantity, Holding.cost_basis).where(
                    Holding.user_id == uid, Holding.coin_id == cid
                )
            )
        ).one()
        assert tuple(row) == (Decimal(8), Decimal(204))
        again, created = await stock_trading.execute(
            db, user_id=uid, order=order, settings=settings
        )
        assert not created and again == fill


@pytest.mark.parametrize("expires", ["status", "quote", "admission", "action"])
async def test_actual_clock_expires_while_waiting_before_final_guard(
    stock_trade_case, settings, monkeypatch, expires
):
    from app.services.trade_math import TradeRefused

    factory, cid, uid, now = stock_trade_case
    setup = {
        "status": (
            "UPDATE stock_status_evidence SET valid_until=clock_timestamp()+interval '1 second'"
        ),
        "quote": "UPDATE stock_quotes SET event_at=clock_timestamp()-interval '119 seconds'",
        "admission": (
            "UPDATE stock_data_admissions SET valid_until="
            "clock_timestamp()+interval '1 second' WHERE product='quotes'"
        ),
        "action": "UPDATE stock_action_state SET valid_until=clock_timestamp()+interval '1 second'",
    }
    async with factory.begin() as db:
        await db.execute(text(setup[expires]))
    before = await financial_snapshot(factory)
    gate = 91090703
    async with factory() as writer, factory() as blocker:
        pid = await writer.scalar(select(func.pg_backend_pid()))
        await blocker.execute(text("SELECT pg_advisory_xact_lock(:gate)"), {"gate": gate})
        original = writer.execute
        blocked = False

        async def execute(statement, *args, **kwargs):
            nonlocal blocked
            if not blocked and "SELECT public.assert_stock_execution_current" in str(statement):
                blocked = True
                await original(text("SELECT pg_advisory_xact_lock(:gate)"), {"gate": gate})
            return await original(statement, *args, **kwargs)

        monkeypatch.setattr(writer, "execute", execute)
        task = asyncio.create_task(
            stock_trading.execute(writer, user_id=uid, order=trade_order(), settings=settings)
        )
        try:
            await wait_for_lock(factory, pid, task)
            await blocker.execute(text("SELECT pg_sleep(1.05)"))
            await blocker.rollback()
            with pytest.raises(TradeRefused):
                await asyncio.wait_for(task, 5)
        finally:
            await blocker.rollback()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    assert await financial_snapshot(factory) == before
