# ruff: noqa: F811
"""Real retained work discovery and restricted cash publication."""

import asyncio
from contextlib import asynccontextmanager
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.services.accounts import get_or_create_user
from app.services.corporate_actions import latest_verified_entitlements
from app.services.event_history import list_event_history
from app.tasks import dividends
from app.tasks.dividends import run_dividend_cycle
from tests.dividend_fixtures import (  # noqa: F401
    books,
    dividend_case,
    ownership,
    revise,
    scheduler,
    status_case,
    stock_trade_case,
    waiting,
)
from tests.helpers import unique_email

__all__ = ["dividend_case"]


@pytest_asyncio.fixture
async def worker(dividend_case):
    factory, _ = dividend_case
    async with factory.begin() as db:
        await db.execute(
            text(
                "GRANT SELECT ON stock_dividend_entitlements,stock_action_events,"
                "stock_action_revisions,stock_dividend_payments,stock_action_state,"
                "stock_action_observations TO birja_scheduler"
            )
        )
    return lambda: scheduler(factory)


async def test_retained_due_target_credits_once(dividend_case, worker):
    factory, ids = dividend_case
    settings = SimpleNamespace(stock_actions_enabled=True)
    first = await run_dividend_cycle(sessionmaker=worker, settings=settings)
    second = await run_dividend_cycle(sessionmaker=worker, settings=settings)
    assert first.accepted == second.accepted == 1
    cash, rows = await books(factory, ids["user_id"])
    assert cash == 101 and len(rows[0]) == 1


@pytest.mark.parametrize("classification", ["uncertain", "cancelled"])
async def test_uncertain_paid_anchor_helper_empty_dedup_and_reconciliation(
    dividend_case, worker, classification
):
    factory, ids = dividend_case
    settings = SimpleNamespace(stock_actions_enabled=True)
    cursor = dividends.DividendCursor()
    await run_dividend_cycle(sessionmaker=worker, settings=settings, cursor=cursor)
    original = (await books(factory, ids["user_id"]))[1][0]
    changed = await revise(factory, ids, classification=classification, eligible=False)
    async with factory() as db:
        assert not await latest_verified_entitlements(db, ids["event_id"])
    for _ in range(3):
        result = await run_dividend_cycle(sessionmaker=worker, settings=settings, cursor=cursor)
        assert result.accepted == 1
    cash, rows = await books(factory, ids["user_id"])
    assert cash == 101 and rows[0] == original and len(rows[1]) == 1
    assert rows[1][0]["outcome"] == "held_uncertain"
    async with factory() as db:
        page = await list_event_history(db, user_id=ids["user_id"])
    assert page.items[0].kind == "dividend_correction"
    assert page.items[0].applied_delta == "0.00000000"
    assert page.items[0].desired_total is None
    corrected = await revise(factory, changed, rate=".75")
    # Existing audit reconciliation is required after a retained uncertain revision.
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
    for _ in range(2):
        await run_dividend_cycle(sessionmaker=worker, settings=settings, cursor=cursor)
    cash, rows = await books(factory, ids["user_id"])
    assert cash == Decimal("101.5") and rows[0] == original and len(rows[1]) == 2
    assert rows[1][1]["outcome"] == "applied"


async def test_uncertainty_before_anchor_publishes_nothing(dividend_case, worker):
    factory, ids = dividend_case
    await revise(factory, ids, classification="uncertain", eligible=False)
    for _ in range(2):
        result = await run_dividend_cycle(
            sessionmaker=worker, settings=SimpleNamespace(stock_actions_enabled=True)
        )
        assert result.accepted == result.rejected == 0
    assert (await books(factory, ids["user_id"])) == (100, [[], [], []])


async def test_bounded_retained_keyset_reaches_later_owners_and_wraps(dividend_case, worker):
    factory, ids = dividend_case
    owners = []
    try:
        async with factory.begin() as db:
            for index in range(104):
                uid, _ = await get_or_create_user(db, unique_email())
                owners.append(uid)
                await db.execute(
                    text(
                        "INSERT INTO stock_dividend_entitlements(event_id,user_id,revision_id,"
                        "cutoff,cutoff_rule,units_basis,unit_epoch,last_movement_sequence,"
                        "eligible_quantity,state,version,fingerprint) SELECT event_id,:u,"
                        "revision_id,cutoff,cutoff_rule,units_basis,unit_epoch,"
                        "last_movement_sequence,0,'eligible',1,:fp "
                        "FROM stock_dividend_entitlements WHERE id=:en"
                    ),
                    {"u": uid, "en": ids["entitlement_id"], "fp": f"{index + 100:064x}"},
                )
        cursor = dividends.DividendCursor()
        counts = []
        for _ in range(4):
            result = await run_dividend_cycle(
                sessionmaker=worker,
                settings=SimpleNamespace(stock_actions_enabled=True),
                cursor=cursor,
            )
            counts.append(result.accepted + result.rejected)
        assert counts == [50, 50, 5, 50]
        async with factory() as db:
            assert (
                await db.scalar(
                    text("SELECT count(*) FROM stock_dividend_payments WHERE event_id=:event_id"),
                    ids,
                )
                == 105
            )
        assert (await books(factory, owners[-1]))[0] == 10000
        async with factory.begin() as db:
            await db.execute(
                text("UPDATE stock_action_state SET health='unknown' WHERE coin_id=:coin_id"), ids
            )
        mixed = await run_dividend_cycle(
            sessionmaker=worker, settings=SimpleNamespace(stock_actions_enabled=True), cursor=cursor
        )
        assert mixed.accepted + mixed.rejected == 100
        async with factory() as db:
            assert (
                await db.scalar(
                    text("SELECT count(*) FROM stock_dividend_decisions WHERE event_id=:event_id"),
                    ids,
                )
                == 50
            )
    finally:
        if owners:
            async with factory.begin() as db:
                # Same guarded disposable-owner maintenance as dividend_case.
                assert await db.scalar(
                    text("SELECT current_database()='birja_test' AND current_user='birja_test'")
                )
                await db.execute(
                    text(
                        "ALTER TABLE stock_dividend_decisions "
                        "DISABLE TRIGGER stock_dividend_immutable"
                    )
                )
                await db.execute(
                    text("DELETE FROM stock_dividend_decisions WHERE user_id=ANY(:owners)"),
                    {"owners": owners},
                )
                await db.execute(
                    text(
                        "ALTER TABLE stock_dividend_decisions "
                        "ENABLE TRIGGER stock_dividend_immutable"
                    )
                )
                await db.execute(
                    text(
                        "ALTER TABLE stock_dividend_payments "
                        "DISABLE TRIGGER stock_dividend_immutable"
                    )
                )
                await db.execute(
                    text("DELETE FROM stock_dividend_payments WHERE user_id=ANY(:owners)"),
                    {"owners": owners},
                )
                await db.execute(
                    text(
                        "ALTER TABLE stock_dividend_payments "
                        "ENABLE TRIGGER stock_dividend_immutable"
                    )
                )
                await db.execute(
                    text("DELETE FROM stock_dividend_entitlements WHERE user_id=ANY(:owners)"),
                    {"owners": owners},
                )
                await db.execute(
                    text("DELETE FROM accounts WHERE user_id=ANY(:owners)"), {"owners": owners}
                )
                await db.execute(
                    text("DELETE FROM users WHERE id=ANY(:owners)"), {"owners": owners}
                )


async def test_disabled_cycle_never_opens_database():
    def forbidden():
        raise AssertionError("disabled cycle must not access data")

    assert (
        await run_dividend_cycle(
            sessionmaker=forbidden, settings=SimpleNamespace(stock_actions_enabled=False)
        )
    ).accepted == 0


async def test_revoked_rights_refuse_each_candidate_without_publication(dividend_case, worker):
    factory, ids = dividend_case
    async with factory.begin() as db:
        await db.execute(text("UPDATE stock_data_admissions SET state='denied'"))
    result = await run_dividend_cycle(
        sessionmaker=worker, settings=SimpleNamespace(stock_actions_enabled=True)
    )
    assert result.rejected == 1 and result.accepted == 0
    assert (await books(factory, ids["user_id"])) == (100, [[], [], []])


async def test_timeout_includes_discovery_and_cancels_cleanup(monkeypatch):
    closed = asyncio.Event()

    async def blocked(*args):
        try:
            await asyncio.Event().wait()
        finally:
            closed.set()

    monkeypatch.setattr(dividends, "_page", blocked)
    monkeypatch.setattr(dividends, "CYCLE_SECONDS", 0.01)
    result = await run_dividend_cycle(
        sessionmaker=None, settings=SimpleNamespace(stock_actions_enabled=True)
    )
    assert result.status == "source_error" and closed.is_set()


async def test_external_cancellation_propagates_after_cleanup(monkeypatch):
    started, closed = asyncio.Event(), asyncio.Event()

    async def blocked(*args):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            closed.set()

    monkeypatch.setattr(dividends, "_page", blocked)
    task = asyncio.create_task(
        run_dividend_cycle(sessionmaker=None, settings=SimpleNamespace(stock_actions_enabled=True))
    )
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert closed.is_set()


async def test_bounded_cycle_cancels_actual_financial_account_wait(
    dividend_case, worker, monkeypatch
):
    factory, ids = dividend_case
    seen = []
    started = asyncio.Event()

    @asynccontextmanager
    async def observed():
        async with worker() as db:
            seen.append(db.info["pid"])
            if len(seen) == 3:
                started.set()
            yield db

    monkeypatch.setattr(dividends, "CYCLE_SECONDS", 0.3)
    async with factory.begin() as blocker:
        await blocker.execute(text("SELECT FROM accounts WHERE user_id=:user_id FOR UPDATE"), ids)
        task = asyncio.create_task(
            run_dividend_cycle(
                sessionmaker=observed, settings=SimpleNamespace(stock_actions_enabled=True)
            )
        )
        await started.wait()
        await waiting(factory, seen[-1], task)
        result = await task
    assert result.status == "source_error"
    assert (await books(factory, ids["user_id"])) == (100, [[], [], []])


async def test_duplicate_unaffordable_target_later_funded_once(dividend_case, worker):
    factory, ids = dividend_case
    settings = SimpleNamespace(stock_actions_enabled=True)
    await run_dividend_cycle(sessionmaker=worker, settings=settings)
    await revise(factory, ids, rate=".1")
    async with factory.begin() as db:
        await db.execute(text("UPDATE accounts SET cash=.79 WHERE user_id=:user_id"), ids)
    for _ in range(2):
        result = await run_dividend_cycle(sessionmaker=worker, settings=settings)
        assert result.accepted == 1
    cash, rows = await books(factory, ids["user_id"])
    assert cash == Decimal(".79") and len(rows[1]) == 1
    assert rows[1][0]["outcome"] == "held_unaffordable"
    async with factory.begin() as db:
        await db.execute(text("UPDATE accounts SET cash=.80 WHERE user_id=:user_id"), ids)
    for _ in range(2):
        await run_dividend_cycle(sessionmaker=worker, settings=settings)
    cash, rows = await books(factory, ids["user_id"])
    assert cash == 0 and len(rows[1]) == 2
    assert rows[1][1]["outcome"] == "applied"


async def test_retained_entitlement_discovered_after_actual_sale(dividend_case, worker, settings):
    from tests.test_stock_trading_concurrency import stock_request
    from tests.test_stock_trading_service import trade_order

    factory, ids = dividend_case
    receipt, created = await stock_request(
        factory,
        ids["user_id"],
        settings,
        trade_order(side="sell", quantity="2", expected_exec_price="100"),
    )
    assert created and receipt.held_after == 0
    before = (await books(factory, ids["user_id"]))[0]
    result = await run_dividend_cycle(
        sessionmaker=worker, settings=SimpleNamespace(stock_actions_enabled=True)
    )
    cash, rows = await books(factory, ids["user_id"])
    assert result.accepted == 1 and cash == before + 1
    assert rows[0][0]["eligible_quantity"] == 2
