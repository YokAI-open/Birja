# ruff: noqa: F811
"""Real independent clients exercise once-only cash and immutable History."""

import asyncio
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.services import dividends, trading
from app.services.trade_math import TradeRefused
from tests.dividend_fixtures import (  # noqa: F401
    books,
    dividend_case,
    hold,
    ownership,
    process,
    revise,
    scheduler,
    status_case,
    stock_trade_case,
    work,
)
from tests.helpers import put_price
from tests.test_stock_trading_concurrency import stock_request
from tests.test_stock_trading_service import trade_order

__all__ = ["dividend_case"]


async def test_duplicate_workers_credit_once(dividend_case):
    factory, ids = dividend_case
    async with asyncio.timeout(15):
        results = await asyncio.gather(*(process(factory, ids) for _ in range(8)))
    assert len(set(results)) == 1
    cash, rows = await books(factory, ids["user_id"])
    assert cash == Decimal(101) and len(rows[0]) == 1 and not rows[1]
    async with factory() as db:
        assert (
            await db.scalar(
                text("SELECT starting_cash FROM accounts WHERE user_id=:u"), {"u": ids["user_id"]}
            )
            == 10000
        )


async def test_duplicate_corrections_a_b_a_keep_original(dividend_case):
    factory, ids = dividend_case
    original = await process(factory, ids)
    saved = (await books(factory, ids["user_id"]))[1][0]
    for rate, expected in ((".75", "101.50"), (".5", "101.00")):
        ids = await revise(factory, ids, rate=rate)
        async with asyncio.timeout(15):
            results = await asyncio.gather(*(process(factory, ids) for _ in range(6)))
        assert len(set(results)) == 1 and results[0].outcome == "applied"
        assert (await books(factory, ids["user_id"]))[0] == Decimal(expected)
    cash, rows = await books(factory, ids["user_id"])
    assert rows[0] == saved and len(rows[1]) == 2 and cash == 101
    assert rows[1][1]["previous_decision_id"] == rows[1][0]["id"]
    assert original.payment_id == rows[0][0]["id"]


@pytest.mark.parametrize("asset", ["stock", "crypto"])
@pytest.mark.parametrize("correction", [False, True])
async def test_spend_races_credit_or_debit_exactly(
    dividend_case, settings, engine, clean_prices, asset, correction
):
    factory, ids = dividend_case
    if correction:
        await process(factory, ids)
        ids = await revise(factory, ids, rate=".1")
    async with factory.begin() as db:
        await db.execute(
            text("UPDATE accounts SET cash=:cash WHERE user_id=:u"),
            {"cash": Decimal(102 if correction else 101), "u": ids["user_id"]},
        )
    async with factory() as db:
        now = await db.scalar(text("SELECT clock_timestamp()"))
    await put_price(engine, "BTC", "100", now)

    async def spend():
        if asset == "stock":
            return await stock_request(factory, ids["user_id"], settings, trade_order(quantity="1"))
        async with factory() as db:
            try:
                return await trading.execute(
                    db,
                    user_id=ids["user_id"],
                    order=trading.Order("BTC", "buy", "usd", Decimal(102)),
                    expected_mid=Decimal(100),
                    idempotency_key=uuid4(),
                    settings=settings,
                )
            except TradeRefused as exc:
                return exc.code

    async with asyncio.timeout(15):
        payment, spent = await asyncio.gather(process(factory, ids), spend())
    cash, rows = await books(factory, ids["user_id"])
    filled = isinstance(spent, tuple)
    assert len(rows[2]) == int(filled) and len(rows[0]) == 1 and cash >= 0
    if correction:
        assert len(rows[1]) == 1
        delta = Decimal(str(rows[1][0]["applied_delta"]))
        assert delta in (Decimal("-.80"), Decimal(0))
        assert payment.outcome == ("held_unaffordable" if filled else "applied")
        assert cash == Decimal(102) + delta - (Decimal(102) if filled else Decimal(0))
        assert filled or spent == "insufficient_cash"
    else:
        assert payment.outcome == "original" and not rows[1]
        assert cash == (Decimal(0) if filled else Decimal(102))
        assert filled or spent == "insufficient_cash"


@pytest.mark.parametrize("correction", [False, True])
async def test_rollback_after_actual_sql_before_commit(dividend_case, monkeypatch, correction):
    factory, ids = dividend_case
    if correction:
        await process(factory, ids)
        ids = await revise(factory, ids)
    before = await books(factory, ids["user_id"])
    async with scheduler(factory) as db:
        execute = db.execute

        async def failed_response(*args, **kwargs):
            await execute(*args, **kwargs)
            raise RuntimeError("synthetic failure after actual SQL before commit")

        monkeypatch.setattr(db, "execute", failed_response)
        with pytest.raises(RuntimeError, match="after actual SQL"):
            await dividends.process_dividend(db, **work(ids))
        assert not db.in_transaction()
    assert await books(factory, ids["user_id"]) == before
    assert (await process(factory, ids)).outcome == ("applied" if correction else "original")


@pytest.mark.parametrize("correction", [False, True])
async def test_commit_response_loss_retry_does_not_repeat_cash(dividend_case, correction):
    factory, ids = dividend_case
    if correction:
        await process(factory, ids)
        ids = await revise(factory, ids)
    committed = []

    async def lost_response():
        committed.append(await process(factory, ids))
        raise ConnectionError("synthetic caller loses response after genuine commit")

    with pytest.raises(ConnectionError, match="after genuine commit"):
        await lost_response()
    saved = await books(factory, ids["user_id"])
    assert await process(factory, ids) == committed[0]
    assert await books(factory, ids["user_id"]) == saved
    assert saved[0] == Decimal("101.5" if correction else "101")


async def test_duplicate_uncertain_holds_then_reviewed_successor(dividend_case):
    factory, ids = dividend_case
    original = await process(factory, ids)
    before = await books(factory, ids["user_id"])
    unknown = await revise(factory, ids, classification="uncertain", eligible=False)
    async with asyncio.timeout(15):
        held = await asyncio.gather(
            *(hold(factory, original.payment_id, unknown["revision_fingerprint"]) for _ in range(6))
        )
    assert len(set(held)) == 1 and held[0].outcome == "held_uncertain"
    cash, rows = await books(factory, ids["user_id"])
    assert cash == before[0] and rows[0] == before[1][0] and len(rows[1]) == 1
    assert rows[1][0]["desired_total"] is None and rows[1][0]["applied_delta"] == 0
    corrected = await revise(factory, unknown)
    async with factory.begin() as db:
        await db.execute(
            text(
                "INSERT INTO stock_action_resolutions(event_id,coin_id,expected_revision,"
                "admission_generation,epoch,decision,decision_key,evidence,evidence_hash,"
                "before_digest,after_digest,actor_ref,created_at) SELECT :event_id,:coin_id,"
                ":revision_id,4,3,'accept_corrected_supported_revision',:key,"
                "jsonb_build_object('format',1,'held_revision_ids',"
                "(SELECT jsonb_agg(r.id ORDER BY r.id) FROM stock_action_revisions r "
                "WHERE r.event_id=:event_id)),repeat('a',64),repeat('b',64),repeat('c',64),"
                "'synthetic-reviewed-operator',clock_timestamp()"
            ),
            {**corrected, "key": str(uuid4())},
        )
    async with asyncio.timeout(15):
        paid = await asyncio.gather(*(process(factory, corrected) for _ in range(6)))
    assert len(set(paid)) == 1 and paid[0].outcome == "applied"
    cash, rows = await books(factory, ids["user_id"])
    assert cash == Decimal("101.5") and len(rows[1]) == 2 and rows[0] == before[1][0]
    assert rows[1][1]["previous_decision_id"] == held[0].decision_id


async def test_duplicate_deficit_then_funded_success_once(dividend_case):
    factory, ids = dividend_case
    await process(factory, ids)
    revised = await revise(factory, ids, rate=".1")
    async with factory.begin() as db:
        await db.execute(text("UPDATE accounts SET cash=.79 WHERE user_id=:user_id"), ids)
    held = await asyncio.gather(*(process(factory, revised) for _ in range(4)))
    assert len(set(held)) == 1 and held[0].outcome == "held_unaffordable"
    before = await books(factory, ids["user_id"])
    assert before[0] == Decimal(".79") and len(before[1][1]) == 1
    async with factory.begin() as db:
        await db.execute(text("UPDATE accounts SET cash=.80 WHERE user_id=:user_id"), ids)
    paid = await asyncio.gather(*(process(factory, revised) for _ in range(4)))
    assert len(set(paid)) == 1 and paid[0].outcome == "applied"
    cash, rows = await books(factory, ids["user_id"])
    assert cash == 0 and len(rows[1]) == 2
    assert rows[1][1]["previous_decision_id"] == held[0].decision_id


async def test_uncommitted_cash_and_history_are_both_invisible(dividend_case, monkeypatch):
    from app.services.event_history import list_event_history

    factory, ids = dividend_case
    ready, release = asyncio.Event(), asyncio.Event()
    async with scheduler(factory) as db:
        execute = db.execute

        async def pause(*args, **kwargs):
            result = await execute(*args, **kwargs)
            ready.set()
            await release.wait()
            return result

        monkeypatch.setattr(db, "execute", pause)
        task = asyncio.create_task(dividends.process_dividend(db, **work(ids)))
        try:
            await asyncio.wait_for(ready.wait(), 5)
            assert (await books(factory, ids["user_id"]))[0] == Decimal(100)
            async with factory() as reader:
                assert not (await list_event_history(reader, user_id=ids["user_id"])).items
            release.set()
            result = await asyncio.wait_for(task, 5)
        finally:
            release.set()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    assert (await books(factory, ids["user_id"]))[0] == 101
    async with factory() as reader:
        page = await list_event_history(reader, user_id=ids["user_id"])
        assert len(page.items) == 1 and page.items[0].id == f"dividend:{result.payment_id}"
