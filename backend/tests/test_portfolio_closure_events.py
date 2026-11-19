"""Public deletion freezes retained events while independent books continue."""

import asyncio
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.services import corporate_actions as actions
from app.services import dividends
from tests.test_corporate_actions import batch, split_action
from tests.test_portfolio_closure_api import CSRF, create, delete, intent
from tests.test_portfolio_strategy_events import (
    authority,
    closure_api,
    cycle,
    management_api,
    strategy_books,
    strategy_events,
)
from tests.test_portfolio_strategy_lifecycle import ledger, scheduler

__all__ = ["authority", "closure_api", "management_api", "strategy_books", "strategy_events"]


async def target(api, root, event):
    async with api.migrator.connect() as db:
        row = (
            (
                await db.execute(
                    text("""SELECT e.id AS entitlement_id,e.event_id,e.portfolio_id,
                r.fingerprint AS revision_fingerprint,e.fingerprint AS entitlement_fingerprint
                FROM stock_dividend_entitlements e
                JOIN stock_action_revisions r ON r.id=e.revision_id
                WHERE e.portfolio_id=:p AND e.event_id=:e
                ORDER BY e.version DESC,e.id DESC LIMIT 1"""),
                    {"p": int(root), "e": event},
                )
            )
            .mappings()
            .one()
        )
        return dict(row)


async def pay(engine, work):
    async with scheduler(engine) as db:
        return await dividends.process_dividend(
            db,
            portfolio_id=work["portfolio_id"],
            event_id=work["event_id"],
            entitlement_id=work["entitlement_id"],
            expected_revision_fingerprint=work["revision_fingerprint"],
            expected_entitlement_fingerprint=work["entitlement_fingerprint"],
        )


async def frozen(api, root):
    from tests.portfolio_closure_fixtures import frozen_financial_snapshot

    async with api.migrator.connect() as db:
        return await frozen_financial_snapshot(db, int(root))


async def disposition(engine, work):
    from app.services.portfolio_lifecycle import lifecycle_effect_disposition

    async with scheduler(engine) as db:
        return await lifecycle_effect_disposition(
            db,
            portfolio_id=work["portfolio_id"],
            event_id=work["event_id"],
            revision_fingerprint=work["revision_fingerprint"],
            entitlement_id=work["entitlement_id"],
        )


async def test_unpaid_closed_disposition_keeps_causal_rows_and_active_sibling(strategy_events):
    api, roots, _, _, _, _, event, engine = strategy_events
    work = await target(api, roots[0], event)
    assert await disposition(engine, work) == "active"
    response = await delete(api, roots[0], intent("Patient"))
    assert response.status_code == 200, response.text
    before = await frozen(api, roots[0])
    assert await disposition(engine, work) == "not_applied_portfolio_closed"
    with pytest.raises(dividends.DividendRefused) as refused:
        await pay(engine, work)
    assert refused.value.code == "portfolio_unavailable"
    assert refused.value.disposition == "not_applied_portfolio_closed"
    assert (await cycle(engine)).accepted == 1
    assert (await cycle(engine)).accepted == 1
    assert await frozen(api, roots[0]) == before
    async with api.migrator.connect() as db:
        assert (
            await db.execute(text("SELECT cash FROM accounts WHERE id=:p"), {"p": int(roots[1])})
        ).scalar_one() == Decimal("10001")


async def test_negative_or_positive_correction_after_close_never_advances_original(strategy_events):
    api, roots, _, _, action, admission, event, engine = strategy_events
    work = await target(api, roots[0], event)
    await pay(engine, work)
    assert (await delete(api, roots[0], intent("Patient"))).status_code == 200
    before = await frozen(api, roots[0])
    assert await disposition(engine, work) == "recorded_before_closure"
    for rate in (Decimal(".75"), Decimal(".1")):
        async with scheduler(engine) as db:
            await actions.persist_action_batch(db, batch(replace(action, rate=rate)), admission)
            derived = await actions.derive_dividend_entitlements(db, event)
            assert [e.portfolio_id for e in derived] == [int(roots[1])]
            await db.commit()
        await cycle(engine)
        assert await frozen(api, roots[0]) == before


async def test_unpaid_disposition_rejects_unknown_or_cross_root_cause(strategy_events):
    from app.services.portfolio_lifecycle import (
        LifecycleEvidenceUnavailable,
        lifecycle_effect_disposition,
    )

    api, roots, _, _, _, _, event, engine = strategy_events
    work = await target(api, roots[0], event)
    async with scheduler(engine) as db:
        original = dict(
            portfolio_id=work["portfolio_id"],
            event_id=event,
            entitlement_id=work["entitlement_id"],
            revision_fingerprint=work["revision_fingerprint"],
        )
        for changes in (
            {"portfolio_id": True},
            {"event_id": 0},
            {"entitlement_id": None},
            {"payment_id": 1},
            {"revision_fingerprint": "F" * 64},
            {"portfolio_id": int(roots[1])},
            {"entitlement_id": 999999},
            {"revision_fingerprint": "f" * 64},
        ):
            with pytest.raises(LifecycleEvidenceUnavailable):
                await lifecycle_effect_disposition(db, **{**original, **changes})


async def test_selected_unpaid_worker_refuses_closed_target_without_skip_rows(
    strategy_events, monkeypatch
):
    from app.tasks import dividends as worker

    api, roots, _, _, _, _, _, engine = strategy_events
    selected, release = asyncio.Event(), asyncio.Event()
    page = worker._page

    async def observed(*args):
        rows = await page(*args)
        if args[1] == worker.VERIFIED:
            selected.set()
            await release.wait()
        return rows

    with monkeypatch.context() as patch:
        patch.setattr(worker, "_page", observed)
        pending = asyncio.create_task(cycle(engine))
        try:
            await asyncio.wait_for(selected.wait(), timeout=10)
            response = await delete(api, roots[0], intent("Patient"))
            assert response.status_code == 200, response.text
            before = await frozen(api, roots[0])
            release.set()
            result = await asyncio.wait_for(pending, timeout=15)
            assert (result.status, result.accepted, result.rejected) == ("ok", 1, 1)
            assert await frozen(api, roots[0]) == before
        finally:
            release.set()
            if not pending.done():
                pending.cancel()
                await asyncio.gather(pending, return_exceptions=True)


async def blocked(api, blocker, routine):
    """Observe an actual PostgreSQL waiter; no delay is evidence of ordering."""
    async with asyncio.timeout(1.5):
        while True:
            async with api.admin.connect() as observer:
                pid = (
                    await observer.execute(
                        text(
                            "SELECT pid FROM pg_stat_activity WHERE datname=current_database() "
                            "AND wait_event_type='Lock' AND :blocker=ANY(pg_blocking_pids(pid)) "
                            "AND query LIKE :routine ORDER BY pid LIMIT 1"
                        ),
                        {"blocker": blocker, "routine": "%" + routine + "%"},
                    )
                ).scalar_one_or_none()
            if pid is not None:
                return pid
            await asyncio.sleep(0)


async def revise_event(engine, action, admission, event, rate):
    async with scheduler(engine) as db:
        await actions.persist_action_batch(db, batch(replace(action, rate=rate)), admission)
        rows = await actions.derive_dividend_entitlements(db, event)
        await db.commit()
        return rows


@pytest.mark.parametrize("correction", [False, True])
@pytest.mark.parametrize("close_first", [False, True])
async def test_selected_job_actual_lock_boundary_both_orders(
    strategy_events, correction, close_first
):
    api, roots, cid, _, action, admission, event, engine = strategy_events
    work = await target(api, roots[0], event)
    if correction:
        await pay(engine, work)
        await revise_event(engine, action, admission, event, Decimal(".75"))
        work = await target(api, roots[0], event)
    pending = financial = None
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
                gate_pid = (await gate.execute(text("SELECT pg_backend_pid()"))).scalar_one()
                pending = asyncio.create_task(delete(api, roots[0], intent("Patient")))
                closer_pid = await blocked(api, gate_pid, "close_portfolio")
                # The target is still active when the service discovers it;
                # SQL must recheck lifecycle after its queued instrument lock.
                financial = asyncio.create_task(pay(engine, work))
                await blocked(api, closer_pid, "apply_stock_dividend")
                await gate.commit()
            response = await asyncio.wait_for(pending, 10)
            assert response.status_code == 200, response.text
            with pytest.raises(dividends.DividendRefused):
                await asyncio.wait_for(financial, 10)
        else:
            async with scheduler(engine) as db:
                row = (
                    await db.execute(
                        text("SELECT * FROM apply_stock_dividend(:e,:en,:r,:fp)"),
                        {
                            "e": event,
                            "en": work["entitlement_id"],
                            "r": work["revision_fingerprint"],
                            "fp": work["entitlement_fingerprint"],
                        },
                    )
                ).one()
                assert row.outcome == ("applied" if correction else "original")
                pid = (await db.execute(text("SELECT pg_backend_pid()"))).scalar_one()
                pending = asyncio.create_task(delete(api, roots[0], intent("Patient")))
                await blocked(api, pid, "close_portfolio")
                await db.commit()
            response = await asyncio.wait_for(pending, 10)
            assert response.status_code == 200, response.text
        before = await frozen(api, roots[0])
        async with api.migrator.connect() as db:
            cash = (
                await db.execute(
                    text("SELECT cash FROM accounts WHERE id=:p"), {"p": int(roots[0])}
                )
            ).scalar_one()
        assert cash == Decimal(
            "10000.50"
            if correction and close_first
            else "10001.50"
            if correction
            else "10000"
            if close_first
            else "10000.50"
        )
        # Duplicate workers can only affect the independently active sibling.
        results = await asyncio.gather(cycle(engine), cycle(engine))
        assert all((r.status, r.accepted, r.rejected) == ("ok", 1, 0) for r in results)
        assert await frozen(api, roots[0]) == before
        with pytest.raises(dividends.DividendRefused):
            await pay(engine, work)
        assert await disposition(engine, work) == (
            "not_applied_portfolio_closed" if close_first else "recorded_before_closure"
        )
        assert await frozen(api, roots[0]) == before
    finally:
        for task in (pending, financial):
            if task is not None and not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)


async def test_held_negative_correction_and_later_split_never_resume_closed_book(strategy_events):
    api, roots, cid, now, action, admission, event, engine = strategy_events
    work = await target(api, roots[0], event)
    original = await pay(engine, work)
    # Actual crypto spending makes the negative correction unaffordable; no
    # privileged cash rewrite creates this acceptance state.
    spent = await api.client.post(
        f"/api/v2/portfolios/{roots[0]}/trades",
        json={
            "symbol": "BTC",
            "side": "buy",
            "amount_usd": "10000.40",
            "expected_mid": "100",
            "idempotency_key": str(uuid4()),
        },
        headers=CSRF,
    )
    assert spent.status_code == 201, spent.text
    assert (await ledger(api, roots[0]))[0][0] == Decimal(".10")
    await revise_event(engine, action, admission, event, Decimal(".1"))
    work = await target(api, roots[0], event)
    held = await pay(engine, work)
    assert held.outcome == "held_unaffordable"
    assert (await delete(api, roots[0], intent("Patient"))).status_code == 200
    before = await frozen(api, roots[0])
    assert await disposition(engine, work) == "recorded_before_closure"
    await revise_event(engine, action, admission, event, Decimal(".75"))
    await asyncio.gather(cycle(engine), cycle(engine))
    # Restore source certainty then execute a genuine split for active books.
    split = split_action(
        replace(action, provider_event_id=str(uuid4()), payable_date=now.date()),
        now - timedelta(hours=1),
        new_rate=Decimal(2),
    )
    async with scheduler(engine) as db:
        await actions.persist_action_batch(db, batch(split), admission)
        applied = await actions.apply_due_actions(db, cid)
        assert len(applied) == 1
        await db.commit()
    async with scheduler(engine) as db:
        assert await actions.apply_due_actions(db, cid) == applied
        await db.commit()
    assert await frozen(api, roots[0]) == before
    sibling = await ledger(api, roots[1])
    assert sibling == ((Decimal("10003"), Decimal(10000)), [("AAPL", Decimal(8), Decimal(40))])
    async with scheduler(engine) as db:
        with pytest.raises(dividends.DividendRefused):
            await dividends.record_dividend_hold(
                db,
                portfolio_id=int(roots[0]),
                payment_id=original.payment_id,
                expected_revision_fingerprint=work["revision_fingerprint"],
            )
    assert await frozen(api, roots[0]) == before


async def test_uncertain_hold_anchor_after_close_and_foreign_owner_continue(strategy_events):
    from tests.stock_action_fixtures import synthetic_opening

    api, roots, cid, now, action, admission, event, engine = strategy_events
    foreign = (await create(api, "Foreign", client=api.other)).json()["id"]
    async with api.migrator.begin() as conn:
        from sqlalchemy.ext.asyncio import AsyncSession

        await conn.execute(
            text(
                "SELECT pg_advisory_xact_lock(hashtextextended("
                "'birja.stock.instrument:' || CAST(:c AS text),0))"
            ),
            {"c": str(cid)},
        )
        async with AsyncSession(bind=conn, join_transaction_mode="create_savepoint") as db:
            await synthetic_opening(
                db,
                cid,
                api.other_uid,
                now - timedelta(days=10),
                quantity=Decimal(6),
                basis=Decimal(60),
                sequence=3,
                portfolio_id=int(foreign),
            )
            await db.commit()
    async with scheduler(engine) as db:
        await actions.derive_dividend_entitlements(db, event)
        await db.commit()
    assert (await cycle(engine)).accepted == 3
    payment = await target(api, roots[0], event)
    async with api.migrator.connect() as db:
        payment_id = (
            await db.execute(
                text("SELECT id FROM stock_dividend_payments WHERE portfolio_id=:p"),
                {"p": int(roots[0])},
            )
        ).scalar_one()
    await revise_event(engine, action, admission, event, None)
    assert (await delete(api, roots[0], intent("Patient"))).status_code == 200
    before = await frozen(api, roots[0])
    async with api.migrator.connect() as db:
        revision = (
            await db.execute(
                text(
                    "SELECT r.fingerprint FROM stock_action_events e "
                    "JOIN stock_action_revisions r ON r.id=e.current_revision_id WHERE e.id=:e"
                ),
                {"e": event},
            )
        ).scalar_one()
    async with scheduler(engine) as db:
        from app.services.portfolio_lifecycle import lifecycle_effect_disposition

        assert (
            await lifecycle_effect_disposition(
                db,
                portfolio_id=int(roots[0]),
                event_id=event,
                payment_id=payment_id,
                revision_fingerprint=revision,
            )
            == "not_applied_portfolio_closed"
        )
        await db.rollback()
        with pytest.raises(dividends.DividendRefused) as refused:
            await dividends.record_dividend_hold(
                db,
                portfolio_id=int(roots[0]),
                payment_id=payment_id,
                expected_revision_fingerprint=revision,
            )
        assert refused.value.disposition == "not_applied_portfolio_closed"
    results = await asyncio.gather(cycle(engine), cycle(engine))
    assert all(r.accepted == 2 and not r.rejected for r in results)
    assert await frozen(api, roots[0]) == before
    assert (await ledger(api, roots[1]))[0][0] == Decimal(10001)
    assert (await ledger(api, foreign))[0][0] == Decimal("10001.50")
    assert await disposition(engine, payment) == "recorded_before_closure"


@pytest.mark.parametrize("corrupt", ["confirmation", "missing", "active_ghost"])
async def test_closed_causal_disposition_refuses_inconsistent_terminal_evidence(
    strategy_events, corrupt
):
    from app.services.portfolio_lifecycle import LifecycleEvidenceUnavailable

    api, roots, _, _, _, _, event, engine = strategy_events
    work = await target(api, roots[0], event)
    assert (await delete(api, roots[0], intent("Patient"))).status_code == 200
    # Deliberate privileged retained-evidence corruption only, never a closure
    # acceptance shortcut. Re-enable all triggers before the read under test.
    async with api.admin.begin() as db:
        await db.execute(text("ALTER TABLE portfolio_lifecycle_closures DISABLE TRIGGER ALL"))
        if corrupt == "confirmation":
            await db.execute(text("ALTER TABLE portfolio_closure_intents DISABLE TRIGGER ALL"))
            await db.execute(
                text(
                    "UPDATE portfolio_lifecycle_closures "
                    "SET confirmation_name='Wrong retained name'"
                )
            )
            await db.execute(
                text("UPDATE portfolio_closure_intents SET confirmation_name='Wrong retained name'")
            )
            await db.execute(text("ALTER TABLE portfolio_closure_intents ENABLE TRIGGER ALL"))
        elif corrupt == "missing":
            await db.execute(text("DELETE FROM portfolio_lifecycle_closures"))
        else:
            await db.execute(
                text("""INSERT INTO portfolio_lifecycle_closures
                (portfolio_id,user_id,closed_at,policy_version,provenance)
                SELECT id,user_id,clock_timestamp(),'freeze_at_closure_v1','retained_boundary'
                FROM accounts WHERE id=:p"""),
                {"p": int(roots[1])},
            )
            work = await target(api, roots[1], event)
        await db.execute(text("ALTER TABLE portfolio_lifecycle_closures ENABLE TRIGGER ALL"))
    before = await frozen(api, str(work["portfolio_id"]))
    with pytest.raises(LifecycleEvidenceUnavailable):
        await disposition(engine, work)
    if corrupt != "active_ghost":
        with pytest.raises(dividends.DividendRefused) as refused:
            await pay(engine, work)
        assert refused.value.code == "authority_unavailable"
        assert refused.value.disposition is None
    assert await frozen(api, str(work["portfolio_id"])) == before
