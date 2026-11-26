"""Independent real clients qualify owned dividend services and worker discovery."""

import asyncio
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services import corporate_actions as actions
from app.services import dividends, trading
from app.services.portfolios import OwnedActivePortfolio
from app.services.trade_math import TradeRefused
from app.tasks import dividends as worker
from tests.helpers import put_price
from tests.stock_action_fixtures import synthetic_opening
from tests.test_corporate_actions import batch
from tests.test_portfolio_creation import authority, management_api, post
from tests.test_portfolio_creation import close as public_close
from tests.test_portfolio_dividend_authority import successor
from tests.test_portfolio_strategy_events import strategy_events
from tests.test_portfolio_strategy_lifecycle import scheduler, strategy_books

__all__ = ["authority", "management_api", "strategy_books", "strategy_events"]


@pytest_asyncio.fixture
async def dividend_books(strategy_events):
    """Payment checks on financial roots created through the public path on 0027."""
    api, roots, cid, now, action, admission, event, engine = strategy_events
    response = await post(api, "Foreign dividend", client=api.other)
    assert response.status_code == 201, response.text
    foreign = int(response.json()["id"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory.begin() as db:
        assert (
            await db.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one() == "0027"
        await db.execute(
            text(
                "SELECT pg_advisory_xact_lock(hashtextextended("
                "'birja.stock.instrument:' || CAST(:c AS text),0))"
            ),
            {"c": str(cid)},
        )
        await synthetic_opening(
            db,
            cid,
            api.other_uid,
            now - timedelta(days=10),
            quantity=Decimal(6),
            basis=Decimal(0),
            sequence=3,
            portfolio_id=foreign,
        )
        # Preserve existing100cash correction/spending oracles as explicit
        # synthetic financial setup, without changing once-only grant evidence.
        await db.execute(text("UPDATE accounts SET cash=100"))
    async with scheduler(engine) as db:
        await actions.persist_action_batch(
            db, batch(replace(action, rate=Decimal(".5"))), admission
        )
        entitlements = await actions.derive_dividend_entitlements(db, event)
        targets = [
            {
                "event_id": event,
                "coin_id": cid,
                "user_id": row.user_id,
                "portfolio_id": row.portfolio_id,
                "revision_id": row.revision_id,
                "revision_fingerprint": (
                    await db.execute(
                        text("SELECT fingerprint FROM stock_action_revisions WHERE id=:r"),
                        {"r": row.revision_id},
                    )
                ).scalar_one(),
                "entitlement_id": row.id,
                "entitlement_fingerprint": row.fingerprint,
            }
            for row in entitlements
        ]
        await db.commit()
    assert [t["portfolio_id"] for t in targets] == [int(r) for r in roots] + [foreign]
    yield engine, factory, targets


def work(target, **changes):
    return {
        "portfolio_id": target["portfolio_id"],
        "event_id": target["event_id"],
        "entitlement_id": target["entitlement_id"],
        "expected_revision_fingerprint": target["revision_fingerprint"],
        "expected_entitlement_fingerprint": target["entitlement_fingerprint"],
        **changes,
    }


async def pay(engine, target, **changes):
    async with scheduler(engine) as db:
        return await dividends.process_dividend(db, **work(target, **changes))


async def books(factory, targets):
    async with factory() as db:
        cash = [
            await db.scalar(text("SELECT cash FROM accounts WHERE id=:p"), {"p": t["portfolio_id"]})
            for t in targets
        ]
        rows = []
        for table in ("stock_dividend_payments", "stock_dividend_decisions"):
            rows.append(
                (
                    await db.execute(
                        text(
                            f"SELECT to_jsonb(t) FROM {table} t ORDER BY id"  # noqa: S608 - fixed inventory
                        )
                    )
                )
                .scalars()
                .all()
            )
        return cash, rows


async def revise(factory, target, **changes):
    async with factory.begin() as db:
        changed = await successor(db, target, **changes)
        if changes.get("eligible", True):
            # A global source revision needs separately derived replacement
            # evidence for each active portfolio. Never pretend the old sibling
            # snapshot authorizes payment under the new source revision.
            await db.execute(
                text("""INSERT INTO stock_dividend_entitlements
              (event_id,portfolio_id,user_id,revision_id,cutoff,cutoff_rule,units_basis,
               unit_epoch,last_movement_sequence,eligible_quantity,state,version,supersedes_id,fingerprint)
              SELECT e.event_id,e.portfolio_id,e.user_id,:r,e.cutoff,e.cutoff_rule,e.units_basis,
               e.unit_epoch,e.last_movement_sequence,e.eligible_quantity,'eligible',e.version+1,e.id,
               encode(sha256(convert_to(e.id::text||:fp,'UTF8')),'hex')
              FROM stock_dividend_entitlements e JOIN accounts a
                ON (a.id,a.user_id)=(e.portfolio_id,e.user_id)
              WHERE e.event_id=:event AND e.portfolio_id<>:p AND a.closed_at IS NULL
                AND NOT EXISTS(SELECT FROM stock_dividend_entitlements newer
                  WHERE newer.event_id=e.event_id AND newer.portfolio_id=e.portfolio_id
                  AND (newer.version,newer.id)>(e.version,e.id))"""),
                {
                    "r": changed["revision_id"],
                    "fp": changed["revision_fingerprint"],
                    "event": target["event_id"],
                    "p": target["portfolio_id"],
                },
            )
        return changed


async def close(api, target):
    await public_close(api, target["portfolio_id"])


async def test_independent_sibling_payments_and_original_replay(dividend_books):
    engine, factory, targets = dividend_books
    first, sibling = await pay(engine, targets[0]), await pay(engine, targets[1])
    assert first.payment_id != sibling.payment_id
    assert await pay(engine, targets[0]) == first
    assert await pay(engine, targets[1]) == sibling
    cash, rows = await books(factory, targets)
    assert cash == [Decimal(101), Decimal(102), Decimal(100)]
    assert len(rows[0]) == 2 and not rows[1]


@pytest.mark.parametrize("wrong", [1, 2])
async def test_discovered_target_cannot_retarget_cause_to_sibling_or_foreign(dividend_books, wrong):
    engine, factory, targets = dividend_books
    with pytest.raises(dividends.DividendRefused, match="unavailable") as exc:
        await pay(engine, targets[0], portfolio_id=targets[wrong]["portfolio_id"])
    assert exc.value.code == "portfolio_unavailable"
    assert await books(factory, targets) == ([Decimal(100)] * 3, [[], []])


async def test_service_duplicate_workers_credit_once(dividend_books):
    engine, factory, targets = dividend_books
    async with asyncio.timeout(20):
        results = await asyncio.gather(*(pay(engine, targets[0]) for _ in range(6)))
    assert len(set(results)) == 1
    assert (await books(factory, targets))[0] == [Decimal(101), Decimal(100), Decimal(100)]
    assert len((await books(factory, targets))[1][0]) == 1


async def test_worker_discovers_each_same_owner_root_and_duplicate_delivery(dividend_books):
    engine, factory, targets = dividend_books
    settings = SimpleNamespace(stock_actions_enabled=True)
    cursor = worker.DividendCursor()
    for _ in range(2):
        result = await worker.run_dividend_cycle(
            sessionmaker=lambda: scheduler(engine), settings=settings, cursor=cursor
        )
        assert result.status == "ok" and result.accepted == 3 and not result.rejected
    cash, rows = await books(factory, targets)
    assert cash == [Decimal(101), Decimal(102), Decimal(103)]
    assert len(rows[0]) == 3 and not rows[1]


async def test_two_actual_worker_cycles_produce_one_effect_per_root(dividend_books):
    engine, factory, targets = dividend_books
    settings = SimpleNamespace(stock_actions_enabled=True)
    async with asyncio.timeout(20):
        results = await asyncio.gather(
            *(
                worker.run_dividend_cycle(sessionmaker=lambda: scheduler(engine), settings=settings)
                for _ in range(2)
            )
        )
    assert all(r.status == "ok" and r.accepted == 3 and not r.rejected for r in results)
    cash, rows = await books(factory, targets)
    assert cash == [Decimal(101), Decimal(102), Decimal(103)]
    assert len(rows[0]) == 3 and len({r["portfolio_id"] for r in rows[0]}) == 3
    assert not rows[1]


async def test_service_boundary_rejects_bad_identity_fingerprint_and_nested_transaction(
    dividend_books,
):
    engine, factory, targets = dividend_books
    for changes in (
        {"portfolio_id": 0},
        {"portfolio_id": True},
        {"event_id": -1},
        {"entitlement_id": 0},
        {"expected_revision_fingerprint": "wrong"},
        {"expected_entitlement_fingerprint": "F" * 64},
    ):
        with pytest.raises(dividends.DividendRefused) as exc:
            await pay(engine, targets[0], **changes)
        assert exc.value.code == "invalid_identity"
    async with scheduler(engine) as db, db.begin():
        with pytest.raises(dividends.DividendRefused) as exc:
            await dividends.process_dividend(db, **work(targets[0]))
        assert exc.value.code == "transaction_active"
    with pytest.raises(dividends.DividendRefused):
        await pay(engine, targets[0], expected_entitlement_fingerprint="f" * 64)
    assert await books(factory, targets) == ([Decimal(100)] * 3, [[], []])


async def test_hold_target_cannot_use_sibling_payment_and_app_cannot_publish(dividend_books):
    engine, factory, targets = dividend_books
    first = await pay(engine, targets[0])
    uncertain = await revise(factory, targets[0], classification="uncertain", eligible=False)
    async with scheduler(engine) as db:
        with pytest.raises(dividends.DividendRefused) as exc:
            await dividends.record_dividend_hold(
                db,
                portfolio_id=targets[1]["portfolio_id"],
                payment_id=first.payment_id,
                expected_revision_fingerprint=uncertain["revision_fingerprint"],
            )
        assert exc.value.code == "portfolio_unavailable"
    async with engine.connect() as conn:
        await conn.execute(text("SET ROLE birja_app"))
        await conn.commit()
        try:
            async with AsyncSession(bind=conn) as db:
                with pytest.raises(dividends.DividendRefused) as exc:
                    await dividends.process_dividend(db, **work(targets[1]))
                assert exc.value.code == "financial_unavailable"
        finally:
            await conn.rollback()
            await conn.execute(text("RESET ROLE"))
            await conn.commit()
    cash, rows = await books(factory, targets)
    assert cash == [Decimal(101), Decimal(100), Decimal(100)]
    assert len(rows[0]) == 1 and not rows[1]


@pytest.mark.parametrize("paid", [False, True])
async def test_closed_earned_or_correction_target_is_ignored_without_history_effect(
    dividend_books, paid, management_api
):
    engine, factory, targets = dividend_books
    target = targets[0]
    if paid:
        await pay(engine, target)
        target = await revise(factory, target)
    await close(management_api, target)
    before = await books(factory, targets)
    with pytest.raises(dividends.DividendRefused) as exc:
        await pay(engine, target)
    assert exc.value.code == "portfolio_unavailable"
    result = await worker.run_dividend_cycle(
        sessionmaker=lambda: scheduler(engine), settings=SimpleNamespace(stock_actions_enabled=True)
    )
    assert result.status == "ok" and result.accepted == 2 and not result.rejected
    after = await books(factory, targets)
    assert after[0][0] == before[0][0] and not after[1][1]
    assert [r for r in after[1][0] if r["portfolio_id"] == target["portfolio_id"]] == before[1][0]


async def test_unaffordable_negative_correction_never_uses_sibling_cash(dividend_books):
    engine, factory, targets = dividend_books
    await pay(engine, targets[0])
    target = await revise(factory, targets[0], rate=".1")
    async with factory.begin() as db:
        await db.execute(
            text("UPDATE accounts SET cash=.79 WHERE id=:p"), {"p": target["portfolio_id"]}
        )
    held = await pay(engine, target)
    assert held.outcome == "held_unaffordable" and await pay(engine, target) == held
    assert (await books(factory, targets))[0] == [Decimal(".79"), Decimal(100), Decimal(100)]
    async with factory.begin() as db:
        await db.execute(
            text("UPDATE accounts SET cash=.80 WHERE id=:p"), {"p": target["portfolio_id"]}
        )
    assert (await pay(engine, target)).outcome == "applied"
    cash, rows = await books(factory, targets)
    assert cash == [Decimal(0), Decimal(100), Decimal(100)]
    assert [Decimal(str(r["applied_delta"])) for r in rows[1]] == [Decimal(0), Decimal("-.8")]
    assert rows[1][1]["previous_decision_id"] == rows[1][0]["id"]


async def test_uncertain_anchor_worker_is_active_root_scoped(dividend_books, management_api):
    engine, factory, targets = dividend_books
    first, sibling = await pay(engine, targets[0]), await pay(engine, targets[1])
    await close(management_api, targets[0])
    await revise(factory, targets[1], classification="uncertain", eligible=False)
    for _ in range(2):
        result = await worker.run_dividend_cycle(
            sessionmaker=lambda: scheduler(engine),
            settings=SimpleNamespace(stock_actions_enabled=True),
        )
        assert result.status == "ok" and result.accepted == 1 and not result.rejected
    cash, rows = await books(factory, targets)
    assert cash == [Decimal(101), Decimal(102), Decimal(100)]
    assert len(rows[1]) == 1 and rows[1][0]["payment_id"] == sibling.payment_id
    assert rows[1][0]["payment_id"] != first.payment_id
    async with scheduler(engine) as db:
        with pytest.raises(dividends.DividendRefused) as exc:
            await dividends.record_dividend_hold(
                db,
                portfolio_id=targets[0]["portfolio_id"],
                payment_id=first.payment_id,
                expected_revision_fingerprint=targets[0]["revision_fingerprint"],
            )
        assert exc.value.code == "portfolio_unavailable"


async def test_trade_spending_races_dividend_on_one_root_without_sibling_effect(
    dividend_books, settings
):
    engine, factory, targets = dividend_books
    async with factory() as db:
        now = await db.scalar(text("SELECT clock_timestamp()"))
    await put_price(engine, "BTC", "100", now)
    target = targets[0]

    async def spend():
        async with factory() as db:
            try:
                return await trading.execute(
                    db,
                    portfolio=OwnedActivePortfolio(target["portfolio_id"], target["user_id"]),
                    order=trading.Order("BTC", "buy", "usd", Decimal(101)),
                    expected_mid=Decimal(100),
                    idempotency_key=uuid4(),
                    settings=settings,
                )
            except TradeRefused as exc:
                assert exc.code == "insufficient_cash"
                return None

    async with asyncio.timeout(20):
        result, _ = await asyncio.gather(spend(), pay(engine, target))
    cash, rows = await books(factory, targets)
    assert cash == [Decimal(101 if result is None else 0), Decimal(100), Decimal(100)]
    assert len(rows[0]) == 1 and not rows[1]
