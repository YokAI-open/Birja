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
