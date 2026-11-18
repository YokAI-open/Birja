"""Active accounting on public-created books with distinct historical owners."""

import asyncio
import importlib.util
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
import respx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import SchedulerSettings
from app.services import corporate_actions as actions
from app.services.kraken import TICKER_URL
from app.services.stock_ownership import assert_ownership_consistent
from app.tasks import dividends as worker
from app.tasks import scheduler as price_worker
from tests.stock_action_fixtures import synthetic_opening
from tests.test_corporate_action_rules import dividend
from tests.test_corporate_actions import batch, split_action
from tests.test_portfolio_creation import authority, management_api, patch, post
from tests.test_portfolio_entitlements import completed_entitlement_session
from tests.test_portfolio_strategy_lifecycle import ledger, scheduler, strategy_books, trade

__all__ = ["authority", "management_api", "strategy_books"]
BACKUP_PATH = Path(__file__).resolve().parents[2] / "deploy/backup-snapshot.py"


@pytest_asyncio.fixture
async def strategy_events(strategy_books, engine):
    api, roots, cid, now = strategy_books
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory.begin() as db:
        admission = await actions._load_admission(db, "actions")
        calendar = await actions._load_admission(db, "calendar")
        session = completed_entitlement_session(now, calendar, "NASDAQ")
        for seq, (root, quantity) in enumerate(zip(roots, (2, 4), strict=True), 1):
            await synthetic_opening(
                db,
                cid,
                api.uid,
                now - timedelta(days=10),
                quantity=Decimal(quantity),
                basis=Decimal(quantity * 10),
                sequence=seq,
                portfolio_id=int(root),
            )
        await db.execute(
            text("UPDATE stock_action_state SET coverage_start=journal_start_at WHERE coin_id=:c"),
            {"c": cid},
        )
        action = dividend(
            coin_id=cid,
            symbol="AAPL",
            provider_event_id=str(uuid4()),
            observed_at=now,
            process_date=session.session_date,
            ex_date=session.session_date,
            record_date=session.session_date,
            payable_date=session.session_date,
        )
    async with scheduler(engine) as db:
        result = (await actions.persist_action_batch(db, batch(action), admission))[0]
        entitlements = await actions.derive_dividend_entitlements(db, result.event_id)
        await db.commit()
    assert [(e.portfolio_id, e.eligible_quantity, e.state) for e in entitlements] == [
        (int(roots[0]), Decimal(2), "eligible"),
        (int(roots[1]), Decimal(4), "eligible"),
    ]
    yield api, roots, cid, now, action, admission, result.event_id, engine


async def cycle(engine):
    return await worker.run_dividend_cycle(
        sessionmaker=lambda: scheduler(engine), settings=SimpleNamespace(stock_actions_enabled=True)
    )


async def evidence(api, table):
    assert table in {
        "stock_dividend_payments",
        "stock_dividend_decisions",
        "trades",
    }
    async with api.migrator.connect() as conn:
        return (
            (
                await conn.execute(
                    text(
                        f"SELECT to_jsonb(t) FROM {table} t ORDER BY id"  # noqa: S608 - fixed inventory above
                    )
                )
            )
            .scalars()
            .all()
        )


async def test_new_books_duplicate_workers_correct_exact_historical_amounts_and_originals(
    strategy_events,
):
    api, roots, _, _, action, admission, event, engine = strategy_events
    async with asyncio.timeout(20):
        results = await asyncio.gather(cycle(engine), cycle(engine))
    assert all(r.status == "ok" and r.accepted == 2 and not r.rejected for r in results)
    assert [(await ledger(api, root))[0][0] for root in roots] == [
        Decimal("10000.50"),
        Decimal(10001),
    ]
    originals = await evidence(api, "stock_dividend_payments")
    assert len(originals) == 2
    async with scheduler(engine) as db:
        await actions.persist_action_batch(
            db, batch(replace(action, rate=Decimal(".75"))), admission
        )
        corrected = await actions.derive_dividend_entitlements(db, event)
        assert [e.eligible_quantity for e in corrected] == [Decimal(2), Decimal(4)]
        await db.commit()
    assert (await cycle(engine)).accepted == 2
    assert (await cycle(engine)).accepted == 2
    assert await evidence(api, "stock_dividend_payments") == originals
    assert [(await ledger(api, root))[0][0] for root in roots] == [
        Decimal("10001.50"),
        Decimal(10003),
    ]
    decisions = await evidence(api, "stock_dividend_decisions")
    assert [Decimal(str(r["applied_delta"])) for r in decisions] == [Decimal(1), Decimal(2)]
    for root, original, amount in zip(roots, originals, ("1", "2"), strict=True):
        response = await api.client.get(f"/api/v2/portfolios/{root}/event-history")
        assert response.status_code == 200, response.text
        rows = response.json()["items"]
        assert {r["kind"] for r in rows} == {"dividend", "dividend_correction"}
        correction = next(r for r in rows if r["kind"] == "dividend_correction")
        assert Decimal(correction["applied_delta"]) == Decimal(amount)
        assert Decimal(correction["original"]["credited_amount"]) == Decimal(
            str(original["original_amount"])
        )
    overview = (await api.client.get("/api/v2/portfolios/overview")).json()
    assert [Decimal(r["cash"]) for r in overview] == [Decimal("10001.50"), Decimal(10003)]


async def test_new_books_active_split_conserves_basis_and_historical_dividend_units(
    strategy_events,
):
    api, roots, cid, now, action, admission, event, engine = strategy_events
    before = [await ledger(api, root) for root in roots]
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

    async with asyncio.timeout(20):
        first, duplicate = await asyncio.gather(apply(), apply())
    assert first == duplicate and len(first) == 1
    applied = first
    async with scheduler(engine) as db:
        assert await actions.apply_due_actions(db, cid) == applied
        entitlements = await actions.derive_dividend_entitlements(db, event)
        assert [(e.eligible_quantity, e.unit_epoch) for e in entitlements] == [
            (Decimal(2), 0),
            (Decimal(4), 0),
        ]
        await assert_ownership_consistent(db, cid)
        await db.commit()
    for root, old, qty, basis in zip(roots, before, (4, 8), (20, 40), strict=True):
        assert await ledger(api, root) == (old[0], [("AAPL", Decimal(qty), Decimal(basis))])
        response = await api.client.get(f"/api/v2/portfolios/{root}/event-history")
        assert response.status_code == 200, response.text
        (row,) = response.json()["items"]
        assert row["kind"] == "split" and Decimal(row["quantity_after"]) == qty
        assert Decimal(row["cost_basis_before"]) == Decimal(row["cost_basis_after"]) == basis
    assert (await cycle(engine)).accepted == 2
    assert [(await ledger(api, root))[0][0] for root in roots] == [
        Decimal("10000.50"),
        Decimal(10001),
    ]


async def test_new_books_uncertain_correction_holds_each_original_without_cash_effect(
    strategy_events,
):
    api, roots, _, _, action, admission, event, engine = strategy_events
    assert (await cycle(engine)).accepted == 2
    originals = await evidence(api, "stock_dividend_payments")
    before = [await ledger(api, root) for root in roots]
    async with scheduler(engine) as db:
        await actions.persist_action_batch(db, batch(replace(action, rate=None)), admission)
        held = await actions.derive_dividend_entitlements(db, event)
        assert {e.state for e in held} == {"held"}
        await db.commit()
    for _ in range(2):
        result = await cycle(engine)
        assert result.status == "ok" and result.accepted == 2 and not result.rejected
    assert [await ledger(api, root) for root in roots] == before
    assert await evidence(api, "stock_dividend_payments") == originals
    decisions = await evidence(api, "stock_dividend_decisions")
    assert len(decisions) == 2 and {r["outcome"] for r in decisions} == {"held_uncertain"}
    assert {Decimal(str(r["applied_delta"])) for r in decisions} == {Decimal(0)}


async def test_new_books_dividend_metadata_create_crypto_lock_order(strategy_events):
    api, roots, _, _, _, _, _, engine = strategy_events
    async with asyncio.timeout(20):
        paid, renamed, created, filled = await asyncio.gather(
            cycle(engine),
            patch(api, roots[0], {"description": "Changed during payment"}),
            post(api, "Third during payment"),
            trade(api, roots[0]),
        )
    assert paid.status == "ok" and paid.accepted == 2 and not paid.rejected
    assert (renamed.status_code, created.status_code, filled.status_code) == (200, 201, 201)
    assert [(await ledger(api, root))[0][0] for root in roots] == [Decimal(9900), Decimal(10001)]
    assert (await ledger(api, created.json()["id"])) == ((Decimal(10000), Decimal(10000)), [])


async def test_created_roots_worker_pages_remain_bounded_and_restart_safe(
    strategy_events, monkeypatch
):
    api, roots, _, _, _, _, _, engine = strategy_events
    monkeypatch.setattr(worker, "MAX_CANDIDATES", 2)
    cursor = worker.DividendCursor()
    for expected in (roots[0], roots[1]):
        result = await worker.run_dividend_cycle(
            sessionmaker=lambda: scheduler(engine),
            settings=SimpleNamespace(stock_actions_enabled=True),
            cursor=cursor,
        )
        assert result.status == "ok" and result.accepted == 1 and not result.rejected
        paid = await evidence(api, "stock_dividend_payments")
        assert str(paid[-1]["portfolio_id"]) == expected
    for _ in range(2):
        assert (await cycle(engine)).accepted == 1
    assert len(await evidence(api, "stock_dividend_payments")) == 2
    assert [(await ledger(api, root))[0][0] for root in roots] == [
        Decimal("10000.50"),
        Decimal(10001),
    ]


async def test_two_or_ten_created_books_share_one_http_market_poll(
    strategy_books, engine, redis_client
):
    from tests.test_scheduler import _body

    api, _, _, now = strategy_books
    settings = SchedulerSettings(price_source="kraken")
    async with (
        httpx.AsyncClient(trust_env=False) as http,
        respx.mock(assert_all_mocked=True) as router,
    ):
        route = router.get(TICKER_URL).mock(return_value=httpx.Response(200, json=_body()))
        for count in (2, 10):
            if count == 10:
                for n in range(8):
                    assert (await post(api, f"Additional {n}")).status_code == 201
            result = await price_worker.run_cycle(
                sessionmaker=async_sessionmaker(engine, expire_on_commit=False),
                redis=redis_client,
                source=price_worker.build_source(settings, http),
                settings=settings,
                candidates={},
                now=lambda: now,
            )
            assert result.status == "ok" and result.accepted > 0
            assert route.call_count == (1 if count == 2 else 2)
    assert api.app.state.settings.stock_data_enabled is False


async def test_created_books_do_not_bypass_existing_backup_storage_capacity(strategy_books):
    api, roots, _, _ = strategy_books
    before = [await ledger(api, root) for root in roots]
    spec = importlib.util.spec_from_file_location("strategy_backup_capacity", BACKUP_PATH)
    backup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backup)
    # Exercise the actual production guard before it could invoke any external
    # backup process; fake quota evidence cannot purchase or authorize capacity.
    job = SimpleNamespace(
        c={
            "quota": {
                "free_controls_verified": True,
                "dedicated_repository": True,
                "visible_bytes": 900,
                "hidden_bytes": 0,
                "unfinished_bytes": 0,
                "other_bytes": 0,
                "upload_reserve_bytes": 100,
                "repack_reserve_bytes": 100,
                "storage_limit_bytes": 1000,
            }
        }
    )
    with pytest.raises(ValueError):
        backup.Job.quota(job, fresh=False)
    assert [await ledger(api, root) for root in roots] == before


async def test_later_stock_fill_and_metadata_preserve_originals_through_correction(strategy_events):
    api, roots, _, _, action, admission, event, engine = strategy_events
    filled = await trade(api, roots[0], stock=True)
    assert filled.status_code == 201, filled.text
    original_trades = await evidence(api, "trades")
    # stock_fill_facts is keyed by trade_id rather than a synthetic row id.
    async with api.migrator.connect() as conn:
        original_facts = (
            (
                await conn.execute(
                    text("SELECT to_jsonb(f) FROM stock_fill_facts f ORDER BY trade_id")
                )
            )
            .scalars()
            .all()
        )
    async with scheduler(engine) as db:
        rows = await actions.derive_dividend_entitlements(db, event)
        assert [r.eligible_quantity for r in rows] == [Decimal(2), Decimal(4)]
        await db.commit()
    assert (await cycle(engine)).accepted == 2
    async with scheduler(engine) as db:
        await actions.persist_action_batch(
            db, batch(replace(action, rate=Decimal(".75"))), admission
        )
        await actions.derive_dividend_entitlements(db, event)
        await db.commit()
    assert (
        await patch(api, roots[0], {"name": "Renamed after fill", "description": "Stable"})
    ).status_code == 200
    assert (await cycle(engine)).accepted == 2
    assert [(await ledger(api, root))[0][0] for root in roots] == [
        Decimal("9899.50"),
        Decimal(10003),
    ]
    assert await evidence(api, "trades") == original_trades
    async with api.migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT to_jsonb(f) FROM stock_fill_facts f ORDER BY trade_id"))
        ).scalars().all() == original_facts
    history = await api.client.get(f"/api/v2/portfolios/{roots[0]}/event-history")
    assert history.status_code == 200, history.text
    assert {r["kind"] for r in history.json()["items"]} == {
        "trade",
        "dividend",
        "dividend_correction",
    }


async def test_active_split_gate_does_not_invert_management_or_waiting_stock_order(
    strategy_events,
    monkeypatch,
):
    from app.services import stock_trading

    api, roots, cid, now, action, admission, _, engine = strategy_events
    entered = asyncio.Event()
    acquire = stock_trading.acquire_stock_gate

    async def observed(db, coin_id):
        entered.set()
        return await acquire(db, coin_id)

    monkeypatch.setattr(stock_trading, "acquire_stock_gate", observed)
    split = split_action(
        replace(action, provider_event_id=str(uuid4()), payable_date=now.date()),
        now - timedelta(hours=1),
        new_rate=Decimal(2),
    )
    async with asyncio.timeout(20):
        async with scheduler(engine) as db:
            await actions.persist_action_batch(db, batch(split), admission)
            # Action owns the real instrument gate while an independent HTTP
            # stock transaction reaches it; metadata/create must still finish.
            pending = asyncio.create_task(trade(api, roots[0], stock=True))
            await entered.wait()
            renamed, created = await asyncio.gather(
                patch(api, roots[0], {"name": "Split concurrent rename"}),
                post(api, "Created while instrument locked"),
            )
            assert (renamed.status_code, created.status_code) == (200, 201)
            assert len(await actions.apply_due_actions(db, cid)) == 1
            await db.commit()
        refused = await pending
    assert refused.status_code == 409, refused.text
    assert [await ledger(api, root) for root in roots] == [
        ((Decimal(10000), Decimal(10000)), [("AAPL", Decimal(4), Decimal(20))]),
        ((Decimal(10000), Decimal(10000)), [("AAPL", Decimal(8), Decimal(40))]),
    ]
    assert await evidence(api, "trades") == []
