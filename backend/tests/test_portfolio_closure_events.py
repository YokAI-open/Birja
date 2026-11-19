"""Public deletion freezes retained events while independent books continue."""

import asyncio
from dataclasses import replace
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.services import corporate_actions as actions
from app.services import dividends
from tests.test_corporate_actions import batch
from tests.test_portfolio_closure_api import delete, intent
from tests.test_portfolio_strategy_events import (
    authority,
    closure_api,
    cycle,
    management_api,
    strategy_books,
    strategy_events,
)
from tests.test_portfolio_strategy_lifecycle import scheduler

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
