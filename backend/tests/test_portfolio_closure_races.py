"""Public operations overlap on real PostgreSQL locks, with exact terminal books."""

import asyncio
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import event, text

from tests.portfolio_closure_fixtures import frozen_financial_snapshot, seed_public_stock_positions
from tests.test_portfolio_closure_api import CSRF, create, delete, intent
from tests.test_portfolio_closure_events import blocked
from tests.test_portfolio_closure_identity import counts
from tests.test_portfolio_strategy_events import (
    authority,
    closure_api,
    management_api,
    strategy_events,
)
from tests.test_portfolio_strategy_lifecycle import ledger, strategy_books, trade

__all__ = ["authority", "closure_api", "management_api", "strategy_books", "strategy_events"]


async def finish(*tasks):
    for task in tasks:
        if not task.done():
            task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


async def test_duplicate_closers_opposite_stock_insertion_order(strategy_books):
    from datetime import timedelta

    api, roots, cid, now = strategy_books
    foreign = (await create(api, "Foreign", client=api.other)).json()["id"]
    roots = [roots[0], foreign]
    async with api.migrator.connect() as conn:
        other = (
            await conn.execute(
                text("SELECT min(coin_id) FROM stock_instruments WHERE coin_id<>:c"), {"c": cid}
            )
        ).scalar_one()
    # Distinct roots have inverse physical insertion order, with global tails.
    for coin, root, qty, basis in (
        (cid, roots[0], 2, 20),
        (other, roots[1], 3, 30),
        (other, roots[0], 4, 40),
        (cid, roots[1], 5, 50),
    ):
        await seed_public_stock_positions(
            api,
            coin,
            now - timedelta(days=3),
            [(api.uid if root == roots[0] else api.other_uid, root, qty, basis)],
        )
    async with api.migrator.connect() as gate:
        await gate.execute(
            text(
                "SELECT pg_advisory_xact_lock(hashtextextended("
                "'birja.stock.instrument:' || CAST(:c AS text),0))"
            ),
            {"c": str(min(cid, other))},
        )
        pid = (await gate.execute(text("SELECT pg_backend_pid()"))).scalar_one()
        tasks = []
        try:
            payloads = [intent("Patient"), intent("Foreign")]
            tasks.append(asyncio.create_task(delete(api, roots[0], payloads[0])))
            closer = await blocked(api, pid, "close_portfolio")
            tasks.append(asyncio.create_task(delete(api, roots[1], payloads[1], client=api.other)))
            await blocked(api, closer, "close_portfolio")
            await gate.commit()
            responses = await asyncio.wait_for(asyncio.gather(*tasks), 8)
            assert [r.status_code for r in responses] == [200, 200], [r.text for r in responses]
            assert await counts(api) == (3, 3, 30000, 2)
            async with api.migrator.connect() as conn:
                assert (
                    await conn.execute(
                        text(
                            "SELECT portfolio_id,coin_id,closing_sequence,unit_epoch "
                            "FROM portfolio_stock_closures ORDER BY portfolio_id,coin_id"
                        )
                    )
                ).all() == [
                    (int(root), coin, 2, 0) for root in roots for coin in sorted((cid, other))
                ]
                before = [await frozen_financial_snapshot(conn, int(root)) for root in roots]
            for root, payload in zip(roots, payloads, strict=True):
                assert (
                    await delete(
                        api, root, payload, client=api.client if root == roots[0] else api.other
                    )
                ).status_code == 200
            async with api.migrator.connect() as conn:
                assert [
                    await frozen_financial_snapshot(conn, int(root)) for root in roots
                ] == before
        finally:
            await gate.rollback()
            await finish(*tasks)


@pytest.mark.parametrize("close_first", [True, False])
async def test_split_writer_real_instrument_gate_both_orders(strategy_events, close_first):
    from dataclasses import replace
    from datetime import timedelta

    from app.services import corporate_actions as actions
    from tests.test_corporate_actions import batch, split_action
    from tests.test_portfolio_strategy_lifecycle import scheduler

    api, roots, cid, now, action, admission, _, engine = strategy_events
    split = split_action(
        replace(action, provider_event_id=str(uuid4()), payable_date=now.date()),
        now - timedelta(hours=1),
        new_rate=Decimal(2),
    )
    async with scheduler(engine) as db:
        await actions.persist_action_batch(db, batch(split), admission)
        await db.commit()

    async def apply():
        async with scheduler(engine) as db:
            result = await actions.apply_due_actions(db, cid)
            await db.commit()
            return result

    tasks = []
    try:
        if close_first:
            async with api.migrator.connect() as gate:
                await gate.execute(
                    text(
                        "SELECT pg_advisory_xact_lock(hashtextextended("
                        "'birja.stock.instrument:' || CAST(:c AS text),0))"
                    ),
                    {"c": str(cid)},
                )
                pid = (await gate.execute(text("SELECT pg_backend_pid()"))).scalar_one()
                closing = asyncio.create_task(delete(api, roots[0], intent("Patient")))
                tasks.append(closing)
                closer = await blocked(api, pid, "close_portfolio")
                writer = asyncio.create_task(apply())
                tasks.append(writer)
                await blocked(api, closer, "pg_advisory_xact_lock")
                await gate.commit()
                assert (await asyncio.wait_for(closing, 8)).status_code == 200
                assert len(await asyncio.wait_for(writer, 8)) == 1
        else:
            async with scheduler(engine) as db:
                applied = await actions.apply_due_actions(db, cid)
                assert len(applied) == 1
                pid = (await db.execute(text("SELECT pg_backend_pid()"))).scalar_one()
                closing = asyncio.create_task(delete(api, roots[0], intent("Patient")))
                tasks.append(closing)
                await blocked(api, pid, "close_portfolio")
                await db.commit()
                assert (await asyncio.wait_for(closing, 8)).status_code == 200
        expected = 2 if close_first else 4
        assert await ledger(api, roots[0]) == (
            (Decimal(10000), Decimal(10000)),
            [("AAPL", Decimal(expected), Decimal(20))],
        )
        assert await ledger(api, roots[1]) == (
            (Decimal(10000), Decimal(10000)),
            [("AAPL", Decimal(8), Decimal(40))],
        )
        async with api.migrator.connect() as conn:
            frozen = await frozen_financial_snapshot(conn, int(roots[0]))
            assert (
                await conn.execute(
                    text("SELECT unit_epoch FROM portfolio_stock_closures WHERE portfolio_id=:p"),
                    {"p": int(roots[0])},
                )
            ).scalar_one() == (0 if close_first else 1)
        assert len(await apply()) == 1
        async with api.migrator.connect() as conn:
            assert await frozen_financial_snapshot(conn, int(roots[0])) == frozen
        assert await counts(api) == (2, 2, 20000, 1)
    finally:
        await finish(*tasks)


async def test_first_buy_omitted_discovery_retries_entire_public_closure(
    strategy_books, monkeypatch
):
    from app.services import stock_trading

    api, roots, cid, _ = strategy_books
    ready, release = asyncio.Event(), asyncio.Event()
    original = stock_trading.append_stock_movement
    writer_pid = None
    calls = []

    async def hold_actual_writer(db, movement):
        nonlocal writer_pid
        result = await original(db, movement)
        writer_pid = (await db.execute(text("SELECT pg_backend_pid()"))).scalar_one()
        ready.set()
        await release.wait()
        return result

    def observe(conn, cursor, statement, parameters, context, executemany):
        if "SELECT * FROM public.close_portfolio(" in statement:
            calls.append(statement)

    monkeypatch.setattr(stock_trading, "append_stock_movement", hold_actual_writer)
    event.listen(api.app.state.engine.sync_engine, "before_cursor_execute", observe)
    tasks = []
    try:
        buy = asyncio.create_task(trade(api, roots[0], stock=True))
        tasks.append(buy)
        await asyncio.wait_for(ready.wait(), 5)
        closing = asyncio.create_task(delete(api, roots[0], intent("Patient")))
        tasks.append(closing)
        await blocked(api, writer_pid, "close_portfolio")
        release.set()
        bought, closed = await asyncio.wait_for(asyncio.gather(*tasks), 8)
        assert bought.status_code == 201, bought.text
        assert closed.status_code == 200, closed.text
        assert len(calls) == 2  # real 40001 rollback and complete rediscovery
        assert (await ledger(api, roots[0])) == (
            (Decimal(9898), Decimal(10000)),
            [("AAPL", Decimal(1), Decimal(102))],
        )
        assert await counts(api) == (2, 2, 20000, 1)
        async with api.migrator.connect() as conn:
            assert (
                await conn.execute(
                    text(
                        "SELECT closing_sequence,unit_epoch FROM portfolio_stock_closures "
                        "WHERE portfolio_id=:p AND coin_id=:c"
                    ),
                    {"p": int(roots[0]), "c": cid},
                )
            ).one() == (1, 0)
        assert (await trade(api, roots[0], stock=True)).status_code == 404
        assert (await ledger(api, roots[1])) == ((Decimal(10000), Decimal(10000)), [])
    finally:
        release.set()
        await finish(*tasks)
        event.remove(api.app.state.engine.sync_engine, "before_cursor_execute", observe)


async def test_crypto_fill_before_closure_preserves_exact_fill_and_basis(
    strategy_books, monkeypatch
):
    from app.services import trading

    api, roots, _, _ = strategy_books
    original = trading._account
    ready, release = asyncio.Event(), asyncio.Event()
    writer_pid = None

    async def holding_after_real_root_lock(db, portfolio, *, lock=False):
        nonlocal writer_pid
        result = await original(db, portfolio, lock=lock)
        if lock:
            writer_pid = (await db.execute(text("SELECT pg_backend_pid()"))).scalar_one()
            ready.set()
            await release.wait()
        return result

    monkeypatch.setattr(trading, "_account", holding_after_real_root_lock)
    tasks = []
    try:
        buying = asyncio.create_task(trade(api, roots[0]))
        tasks.append(buying)
        await asyncio.wait_for(ready.wait(), 5)
        closing = asyncio.create_task(delete(api, roots[0], intent("Patient")))
        tasks.append(closing)
        await blocked(api, writer_pid, "close_portfolio")
        release.set()
        bought, closed = await asyncio.wait_for(asyncio.gather(*tasks), 8)
        assert bought.status_code == 201, bought.text
        assert closed.status_code == 200, closed.text
        assert await ledger(api, roots[0]) == (
            (Decimal("9899.50"), Decimal(10000)),
            [("BTC", Decimal(1), Decimal("100.50"))],
        )
        assert await counts(api) == (2, 2, 20000, 1)
        async with api.migrator.connect() as conn:
            before = await frozen_financial_snapshot(conn, int(roots[0]))
        assert (await trade(api, roots[0])).status_code == 404
        async with api.migrator.connect() as conn:
            assert await frozen_financial_snapshot(conn, int(roots[0])) == before
    finally:
        release.set()
        await finish(*tasks)


@pytest.mark.parametrize("stock", [False, True])
async def test_closure_before_crypto_or_stock_fill_keeps_original_frozen(strategy_books, stock):
    api, roots, _, _ = strategy_books
    async with api.admin.connect() as gate:
        tx = await gate.begin()
        await gate.execute(
            text("SELECT id FROM accounts WHERE id=:p FOR UPDATE"), {"p": int(roots[0])}
        )
        pid = (await gate.execute(text("SELECT pg_backend_pid()"))).scalar_one()
        tasks = []
        try:
            closing = asyncio.create_task(delete(api, roots[0], intent("Patient")))
            tasks.append(closing)
            closer = await blocked(api, pid, "close_portfolio")
            buying = asyncio.create_task(trade(api, roots[0], stock=stock))
            tasks.append(buying)
            # Both genuine writers queue behind the held original root.
            await blocked(api, closer, "accounts")
            await tx.commit()
            closed, rejected = await asyncio.wait_for(asyncio.gather(*tasks), 8)
            assert closed.status_code == 200, closed.text
            assert rejected.status_code == 404, rejected.text
            assert await counts(api) == (2, 2, 20000, 1)
            assert await ledger(api, roots[0]) == ((Decimal(10000), Decimal(10000)), [])
            async with api.migrator.connect() as conn:
                before = await frozen_financial_snapshot(conn, int(roots[0]))
            assert (await trade(api, roots[1], stock=stock)).status_code == 201
            async with api.migrator.connect() as conn:
                assert await frozen_financial_snapshot(conn, int(roots[0])) == before
        finally:
            if tx.is_active:
                await tx.rollback()
            await finish(*tasks)


@pytest.mark.parametrize("delete_first", [True, False])
async def test_management_creation_cap_freed_name_slot_and_original_key(closure_api, delete_first):
    api = closure_api
    creation_key = uuid4()
    first = (await create(api, "Strategy", key=creation_key)).json()["id"]
    for i in range(9):
        assert (await create(api, f"Strategy {i}")).status_code == 201
    async with api.admin.connect() as gate:
        tx = await gate.begin()
        await gate.execute(
            text("SELECT id FROM users WHERE id=:u FOR NO KEY UPDATE"), {"u": api.uid}
        )
        pid = (await gate.execute(text("SELECT pg_backend_pid()"))).scalar_one()
        tasks = []
        try:
            operations = [lambda: delete(api, first), lambda: create(api, "STRATEGY")]
            if not delete_first:
                operations.reverse()
            tasks.append(asyncio.create_task(operations[0]()))
            first_pid = await blocked(
                api, pid, "close_portfolio" if delete_first else "create_portfolio"
            )
            tasks.append(asyncio.create_task(operations[1]()))
            await blocked(api, first_pid, "create_portfolio" if delete_first else "close_portfolio")
            await tx.commit()
            responses = await asyncio.wait_for(asyncio.gather(*tasks), 8)
            closed, created = responses if delete_first else responses[::-1]
            assert closed.status_code == 200, closed.text
            if delete_first:
                assert created.status_code == 201, created.text
                replacement = created.json()["id"]
                assert replacement != first
                assert await counts(api) == (11, 11, 110000, 1)
            else:
                assert created.status_code == 409, created.text
                assert await counts(api) == (10, 10, 100000, 1)
            assert (await create(api, "Strategy", key=creation_key)).status_code == 404
            active = (await api.client.get("/api/v2/portfolios")).json()
            assert len(active) == (10 if delete_first else 9)
            assert first not in {row["id"] for row in active}
        finally:
            if tx.is_active:
                await tx.rollback()
            await finish(*tasks)


@pytest.mark.parametrize("rename_first", [True, False])
async def test_management_rename_delete_preserves_original_terminal_intent(
    closure_api, rename_first
):
    api = closure_api
    root = (await create(api)).json()["id"]
    payload = intent()
    async with api.admin.connect() as gate:
        tx = await gate.begin()
        await gate.execute(
            text("SELECT id FROM users WHERE id=:u FOR NO KEY UPDATE"), {"u": api.uid}
        )
        pid = (await gate.execute(text("SELECT pg_backend_pid()"))).scalar_one()
        tasks = []
        try:
            operations = [
                lambda: api.client.patch(
                    f"/api/v2/portfolios/{root}", json={"name": "Renamed"}, headers=CSRF
                ),
                lambda: delete(api, root, payload),
            ]
            if not rename_first:
                operations.reverse()
            tasks.append(asyncio.create_task(operations[0]()))
            first_pid = await blocked(
                api, pid, "update_portfolio" if rename_first else "close_portfolio"
            )
            tasks.append(asyncio.create_task(operations[1]()))
            await blocked(api, first_pid, "close_portfolio" if rename_first else "update_portfolio")
            await tx.commit()
            responses = await asyncio.wait_for(asyncio.gather(*tasks), 8)
            renamed, closed = responses if rename_first else responses[::-1]
            assert renamed.status_code == (200 if rename_first else 404), renamed.text
            assert closed.status_code == (409 if rename_first else 200), closed.text
            assert (await delete(api, root, payload)).status_code == closed.status_code
            assert await counts(api) == (1, 1, 10000, 1)
        finally:
            if tx.is_active:
                await tx.rollback()
            await finish(*tasks)
