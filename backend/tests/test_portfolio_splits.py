"""Real root-aware split effects, global evidence and frozen siblings."""

from dataclasses import asdict, replace
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select, text, update
from sqlalchemy.exc import DBAPIError

from app.models.corporate_action import StockOwnershipMovement, StockSplitApplication
from app.models.price import Coin
from app.models.stock import StockDataAdmission
from app.models.trade import Holding
from app.services import corporate_actions as actions
from app.services.stock_ownership import assert_ownership_consistent
from tests.test_corporate_action_rules import dividend
from tests.test_corporate_actions import batch, split_action
from tests.test_portfolio_stock_ownership import journal_case
from tests.test_portfolio_strategy_events import (
    authority,
    closure_api,
    management_api,
    strategy_events,
)
from tests.test_portfolio_strategy_lifecycle import strategy_books
from tests.test_stock_admission import action_admitted

__all__ = [
    "authority",
    "strategy_events",
    "closure_api",
    "management_api",
    "strategy_books",
    "stock_authority_case",
    "journal_case",
]


@pytest_asyncio.fixture
async def stock_authority_case(strategy_books, engine):
    """Retained split scenarios on current authority, with a real public closure."""
    import json

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.services.stock_eligibility import load_execution_evidence
    from app.services.stock_trading import _encoded
    from tests.test_portfolio_closure_api import create, delete, intent

    api, roots, cid, now = strategy_books
    closed = (await create(api, "Retained closed")).json()["id"]
    foreign = (await create(api, "Foreign", client=api.other)).json()["id"]
    assert (await delete(api, closed, intent("Retained closed"))).status_code == 200
    async with AsyncSession(engine) as db:
        loaded = await load_execution_evidence(db, cid, api.app.state.settings)
        snapshot = json.loads(json.dumps(asdict(loaded.evidence), default=_encoded))
        snapshot["portfolio_id"] = int(roots[0])
    async with engine.connect() as conn:
        tx = await conn.begin()
        assert (
            await conn.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one() == "0024"
        await conn.execute(
            text(
                "SELECT pg_advisory_xact_lock(hashtextextended("
                "'birja.stock.instrument:' || CAST(:c AS text),0))"
            ),
            {"c": str(cid)},
        )
        await conn.execute(
            text("UPDATE stock_action_state SET admission_generation=1 WHERE coin_id=:c"),
            {"c": cid},
        )
        for root in roots:
            await conn.execute(
                text(
                    "INSERT INTO holdings(portfolio_id,user_id,coin_id,quantity,cost_basis) "
                    "VALUES (:p,:u,:c,2,20)"
                ),
                {"p": int(root), "u": api.uid, "c": cid},
            )
        try:
            yield (
                conn,
                {
                    "coin": cid,
                    "owner": api.uid,
                    "foreign_owner": api.other_uid,
                    "first": int(roots[0]),
                    "sibling": int(roots[1]),
                    "closed": int(closed),
                    "foreign": int(foreign),
                    "now": now,
                    "snapshot": snapshot,
                },
            )
        finally:
            await tx.rollback()


@pytest_asyncio.fixture
async def split_case(journal_case):
    db, conn, case = journal_case
    now = case["now"]
    evidence = replace(
        action_admitted(),
        generation=1,
        reviewed_at=now - timedelta(hours=1),
        valid_from=now - timedelta(hours=2),
        valid_until=now + timedelta(hours=2),
    )
    await db.execute(
        update(StockDataAdmission)
        .where(StockDataAdmission.product == "actions")
        .values(**asdict(evidence))
    )
    symbol = (await db.execute(select(Coin.symbol).where(Coin.id == case["coin"]))).scalar_one()
    action = replace(
        dividend(),
        coin_id=case["coin"],
        symbol=symbol,
        provider_event_id=str(uuid4()),
        observed_at=now,
        payable_date=now.date(),
    )
    yield db, conn, case, action, evidence


async def record_split(db, case, action, evidence, *, hours=24, **changes):
    cutoff = case["now"] - timedelta(hours=hours)
    changes.setdefault("new_rate", Decimal(2))
    action = split_action(replace(action, provider_event_id=str(uuid4())), cutoff, **changes)
    await actions.persist_action_batch(db, batch(action), evidence)
    return await actions.apply_due_actions(db, case["coin"])


async def test_active_siblings_split_once_with_one_reloaded_global_application(split_case):
    db, _, case, action, evidence = split_case
    result = await record_split(db, case, action, evidence)
    assert len(result) == 1
    assert await actions.apply_due_actions(db, case["coin"]) == result
    db.expire_all()
    application = await db.get(StockSplitApplication, result[0])
    assert application.owner_digest_version == 2
    rows = list(
        (
            await db.execute(
                select(StockOwnershipMovement).where(
                    StockOwnershipMovement.application_id == result[0]
                )
            )
        ).scalars()
    )
    assert {r.portfolio_id for r in rows} == {case["first"], case["sibling"]}
    assert len(rows) == 2 and {r.after_quantity for r in rows} == {Decimal(4)}
    holdings = list(
        (
            await db.execute(
                select(Holding)
                .where(Holding.coin_id == case["coin"])
                .order_by(Holding.portfolio_id)
            )
        ).scalars()
    )
    assert [(r.quantity, r.cost_basis) for r in holdings] == [(Decimal(4), Decimal(20))] * 2
    await assert_ownership_consistent(db, case["coin"])


async def test_actual_scheduler_applies_split_without_account_update_grant(split_case):
    db, conn, case, action, evidence = split_case
    await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
    assert len(await record_split(db, case, action, evidence)) == 1
    assert not (
        await conn.execute(
            text("SELECT has_column_privilege('birja_scheduler','accounts','cash','UPDATE')")
        )
    ).scalar_one()


async def test_lock_helper_exact_inventory_and_no_economic_write_authority(split_case):
    _, conn, _, _, _ = split_case
    row = (
        await conn.execute(
            text("""SELECT pg_get_userbyid(proowner),prosecdef,proconfig,
       has_function_privilege('public',oid,'EXECUTE'),
       has_function_privilege('birja_scheduler',oid,'EXECUTE'),
       has_function_privilege('birja_app',oid,'EXECUTE'),pg_get_functiondef(oid)
       FROM pg_proc WHERE oid='public.lock_stock_portfolio_roots(bigint)'::regprocedure""")
        )
    ).one()
    assert row[:6] == (
        "birja_migrator",
        True,
        ["search_path=pg_catalog, public, pg_temp"],
        False,
        True,
        False,
    )
    assert "ORDER BY a.id FOR UPDATE" in row[6]
    assert "pg_advisory_xact_lock" in row[6]
    assert (
        "INSERT INTO" not in row[6]
        and "UPDATE public." not in row[6]
        and "DELETE FROM" not in row[6]
    )


async def test_app_cannot_invoke_scheduler_root_lock(split_case):
    db, _, case, _, _ = split_case
    with pytest.raises(DBAPIError) as rejected:
        async with db.begin_nested():
            await db.execute(text("SET LOCAL ROLE birja_app"))
            await db.execute(
                text("SELECT public.lock_stock_portfolio_roots(:c)"), {"c": case["coin"]}
            )
    assert rejected.value.orig.sqlstate == "42501"


@pytest.mark.parametrize("coin", [None, 0, -1, 999999999])
async def test_scheduler_lock_rejects_unknown_instrument_without_writes(split_case, coin):
    db, _, _, _, _ = split_case
    with pytest.raises(DBAPIError) as rejected:
        async with db.begin_nested():
            await db.execute(text("SET LOCAL ROLE birja_scheduler"))
            await db.execute(text("SELECT public.lock_stock_portfolio_roots(:c)"), {"c": coin})
    assert rejected.value.orig.sqlstate == "22023"


async def test_closed_sibling_remains_exact_through_two_later_epochs(strategy_events):
    from tests.portfolio_closure_fixtures import frozen_financial_snapshot
    from tests.test_portfolio_closure_api import delete, intent
    from tests.test_portfolio_strategy_lifecycle import ledger, scheduler

    api, roots, cid, now, action, evidence, _, engine = strategy_events
    assert (await delete(api, roots[0], intent("Patient"))).status_code == 200
    async with api.migrator.connect() as conn:
        before = await frozen_financial_snapshot(conn, int(roots[0]))
    for hours, quantity, epoch in ((24, 8, 1), (1, 16, 2)):
        split = split_action(
            replace(action, provider_event_id=str(uuid4()), payable_date=now.date()),
            now - timedelta(hours=hours),
            new_rate=Decimal(2),
        )
        async with scheduler(engine) as db:
            await actions.persist_action_batch(db, batch(split), evidence)
            applied = await actions.apply_due_actions(db, cid)
            assert len(applied) == epoch
            await db.commit()
        async with scheduler(engine) as db:
            assert await actions.apply_due_actions(db, cid) == applied
            state, _ = await assert_ownership_consistent(db, cid)
            assert state.unit_epoch == epoch
            await db.commit()
        assert await ledger(api, roots[1]) == (
            (Decimal(10000), Decimal(10000)),
            [("AAPL", Decimal(quantity), Decimal(40))],
        )
        async with api.migrator.connect() as conn:
            assert await frozen_financial_snapshot(conn, int(roots[0])) == before


@pytest.mark.parametrize(
    "changes", [{"new_rate": Decimal(1), "old_rate": Decimal(2)}, {"cancelled": True}]
)
async def test_uncertain_or_reverse_split_holds_without_root_mutations(split_case, changes):
    db, _, case, action, evidence = split_case
    assert await record_split(db, case, action, evidence, **changes) == ()
    assert (
        list(
            (
                await db.execute(select(Holding.quantity).where(Holding.coin_id == case["coin"]))
            ).scalars()
        )
        == [Decimal(2)] * 2
    )
    assert list((await db.execute(select(StockSplitApplication))).scalars()) == []


async def test_failure_after_first_root_rolls_back_all_split_effects(split_case, monkeypatch):
    db, conn, case, action, evidence = split_case
    await actions.persist_action_batch(
        db, batch(split_action(action, case["now"] - timedelta(days=1))), evidence
    )
    original = actions.append_stock_movement
    calls = 0

    async def fail_after_first(db, movement):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("synthetic crash")
        return await original(db, movement)

    monkeypatch.setattr(actions, "append_stock_movement", fail_after_first)
    with pytest.raises(RuntimeError, match="synthetic crash"):
        async with db.begin_nested():
            await actions.apply_due_actions(db, case["coin"])
    db.expire_all()
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_split_applications"))
    ).scalar_one() == 0
    assert (
        list(
            (
                await db.execute(select(Holding.quantity).where(Holding.coin_id == case["coin"]))
            ).scalars()
        )
        == [Decimal(2)] * 2
    )
    monkeypatch.setattr(actions, "append_stock_movement", original)
    assert len(await actions.apply_due_actions(db, case["coin"])) == 1
    await assert_ownership_consistent(db, case["coin"])
