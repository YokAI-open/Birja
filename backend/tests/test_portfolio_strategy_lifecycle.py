"""Publicly created strategies exercise the real restricted financial routes."""

import asyncio
import json
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.corporate_action import StockActionState
from app.services.stock_eligibility import load_execution_evidence
from app.services.stock_trading import _encoded
from tests import stock_trade_fixtures
from tests.helpers import put_price
from tests.test_portfolio_creation import authority, close, management_api, patch, post

__all__ = ["authority", "management_api"]


@asynccontextmanager
async def scheduler(engine):
    """Use installed scheduler ACLs; always reset a returned pooled connection."""
    async with engine.connect() as conn:
        await conn.execute(text("SET ROLE birja_scheduler"))
        await conn.commit()
        try:
            async with AsyncSession(bind=conn, expire_on_commit=False) as db:
                yield db
        finally:
            await conn.rollback()
            await conn.execute(text("RESET ROLE"))
            await conn.commit()


@pytest_asyncio.fixture
async def strategy_books(management_api, engine, monkeypatch, request):
    api = management_api
    roots = []
    for name in ("Patient", "Active"):
        response = await post(api, name)
        assert response.status_code == 201, response.text
        roots.append(response.json()["id"])
    # Reuse only the retained synthetic market evidence builder. It creates no
    # accounts: both financial roots above came from the production HTTP route.
    status = stock_trade_fixtures.status_case.__wrapped__(engine, None, None)
    market = await anext(status)
    factory, cid, now = market
    async with factory.begin() as db:
        db.add(
            StockActionState(
                coin_id=cid,
                admission_generation=1,
                health="current",
                checked_at=now,
                valid_until=now + timedelta(hours=1),
                journal_start_at=now - timedelta(days=20),
                complete_from=now - timedelta(days=20),
                coverage_start=now - timedelta(days=20),
                covered_until=now,
            )
        )
    evidence = stock_trade_fixtures.stock_trade_case.__wrapped__(
        market, (factory, cid, api.uid), monkeypatch, request
    )
    await anext(evidence)
    await put_price(engine, "BTC", "100", now)
    try:
        yield api, roots, cid, now
    finally:
        await evidence.aclose()
        await status.aclose()


async def trade(api, root, *, stock=False, side="buy", quantity="1", key=None, **changes):
    body = {
        "symbol": "AAPL" if stock else "BTC",
        "side": side,
        "quantity": quantity,
        "idempotency_key": str(key or uuid4()),
        **(
            {"expected_exec_price": "102" if side == "buy" else "100"}
            if stock
            else {"expected_mid": "100"}
        ),
        **changes,
    }
    return await api.client.post(
        f"/api/v2/portfolios/{root}/{'stock-trades' if stock else 'trades'}",
        json=body,
        headers={"X-CSRF-Token": "test-csrf"},
    )


async def ledger(api, root):
    async with api.migrator.connect() as conn:
        money = (
            await conn.execute(
                text("SELECT cash,starting_cash FROM accounts WHERE id=:p"), {"p": int(root)}
            )
        ).one()
        holdings = (
            await conn.execute(
                text(
                    "SELECT c.symbol,h.quantity,h.cost_basis FROM holdings h "
                    "JOIN coins c ON c.id=h.coin_id WHERE h.portfolio_id=:p ORDER BY c.symbol"
                ),
                {"p": int(root)},
            )
        ).all()
    return money, holdings


@pytest_asyncio.fixture
async def current_stock_authority_case(strategy_books, engine):
    """Retained accounting assertions on the current schema (0028)."""
    api, roots, cid, now = strategy_books
    closed = (await post(api, "Retained closed")).json()["id"]
    foreign = (await post(api, "Foreign", client=api.other)).json()["id"]
    await close(api, int(closed))
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        loaded = await load_execution_evidence(db, cid, api.app.state.settings)
        snapshot = json.loads(json.dumps(asdict(loaded.evidence), default=_encoded))
        snapshot["portfolio_id"] = int(roots[0])
    async with engine.connect() as conn:
        tx = await conn.begin()
        assert (
            await conn.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one() == "0028"
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
        case = {
            "coin": cid,
            "owner": api.uid,
            "foreign_owner": api.other_uid,
            "first": int(roots[0]),
            "sibling": int(roots[1]),
            "closed": int(closed),
            "foreign": int(foreign),
            "now": now,
            "snapshot": snapshot,
        }
        try:
            yield conn, case
        finally:
            await tx.rollback()


async def test_created_siblings_same_crypto_stock_buy_sell_exact_history_overview(strategy_books):
    api, (first, sibling), _, _ = strategy_books
    for root, amount in ((first, "2"), (sibling, "3")):
        for stock in (False, True):
            response = await trade(api, root, stock=stock, quantity=amount)
            assert response.status_code == 201, response.text
            assert response.json()["portfolio_id"] == root
    sibling_before = await ledger(api, sibling)
    for stock in (False, True):
        response = await trade(api, first, stock=stock, side="sell")
        assert response.status_code == 201, response.text
    # Independent arithmetic: BTC buy 201.00, sell 99.50; AAPL buy204/sell100.
    assert await ledger(api, first) == (
        (Decimal("9794.50"), Decimal(10000)),
        [("AAPL", Decimal(1), Decimal(102)), ("BTC", Decimal(1), Decimal("100.50"))],
    )
    assert (
        await ledger(api, sibling)
        == sibling_before
        == (
            (Decimal("9392.50"), Decimal(10000)),
            [("AAPL", Decimal(3), Decimal(306)), ("BTC", Decimal(3), Decimal("301.50"))],
        )
    )
    overview = await api.client.get("/api/v2/portfolios/overview")
    assert overview.status_code == 200, overview.text
    for row, root, cash, qty in zip(
        overview.json(), (first, sibling), ("9794.50", "9392.50"), (1, 3), strict=True
    ):
        assert row["id"] == root and Decimal(row["cash"]) == Decimal(cash)
        assert Decimal(row["total_value"]) == Decimal(cash) + Decimal(201 * qty)
        assert Decimal(row["total_pl"]) == Decimal(cash) + Decimal(201 * qty) - 10000
        detail = (await api.client.get(f"/api/v2/portfolios/{root}")).json()

        # Separate HTTP reads sample advancing time: compare all monetary and
        # source evidence, excluding only observation-relative age counters.
        def stable(value):
            if isinstance(value, list):
                return [stable(v) for v in value]
            if isinstance(value, dict):
                return {
                    k: stable(v)
                    for k, v in value.items()
                    if k not in {"id", "portfolio_id", "description", "valued_at", "age_seconds"}
                }
            return value

        assert stable(row) == stable(detail)
        history = (await api.client.get(f"/api/v2/portfolios/{root}/history")).json()
        assert len(history["items"]) == (4 if root == first else 2)
        async with api.migrator.connect() as conn:
            ids = set(
                (
                    await conn.execute(
                        text("SELECT id::text FROM trades WHERE portfolio_id=:p"), {"p": int(root)}
                    )
                ).scalars()
            )
        assert {r["id"] for r in history["items"]} == ids
        assert sum(Decimal(r["total"]) for r in history["items"]) == Decimal(cash) - 10000


@pytest.mark.parametrize("same_key", [False, True])
async def test_created_crossasset_race_spends_only_root_cash(strategy_books, same_key):
    api, (root, sibling), _, _ = strategy_books
    before = await ledger(api, sibling)
    key = uuid4()
    async with asyncio.timeout(15):
        results = await asyncio.gather(
            trade(api, root, stock=True, quantity="60", key=key),
            trade(api, root, quantity="60", key=key if same_key else None),
        )
    assert sorted(r.status_code for r in results) == [201, 409 if same_key else 422]
    refused = next(r for r in results if r.status_code != 201)
    assert refused.json()["detail"]["code"] == (
        "idempotency_conflict" if same_key else "insufficient_cash"
    )
    cash, rows = await ledger(api, root)
    # Crypto: 60 *100.25 + round(6015 *.0025)=6030.04; stock60*102=6120.
    assert cash[0] in {Decimal(3880), Decimal("3969.96")} and len(rows) == 1
    assert await ledger(api, sibling) == before


async def test_create_rename_trade_race_keeps_original_grants_and_financial_identity(
    strategy_books,
):
    api, (root, sibling), _, _ = strategy_books
    async with asyncio.timeout(15):
        renamed, created, filled = await asyncio.gather(
            patch(api, root, {"name": "Contested"}),
            post(api, "CONTESTED"),
            trade(api, root, stock=True),
        )
    assert sorted((renamed.status_code, created.status_code)) == (
        [200, 409] if renamed.status_code == 200 else [201, 409]
    )
    assert filled.status_code == 201, filled.text
    assert (await ledger(api, root))[0] == (Decimal(9898), Decimal(10000))
    assert (await ledger(api, sibling))[0] == (Decimal(10000), Decimal(10000))
    async with api.migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT count(*),sum(amount) FROM portfolio_creations"))
        ).one() == ((2, Decimal(20000)) if created.status_code == 409 else (3, Decimal(30000)))


async def test_stock_gate_stale_quote_and_foreign_target_never_spend_created_books(strategy_books):
    api, roots, cid, _ = strategy_books
    before = [await ledger(api, root) for root in roots]
    assert api.app.state.settings.stock_data_enabled is False
    async with api.migrator.begin() as conn:
        await conn.execute(
            text("UPDATE stock_quotes SET event_at=event_at-interval '3 days' WHERE coin_id=:c"),
            {"c": cid},
        )
    refused = await trade(api, roots[0], stock=True)
    assert refused.status_code == 409, refused.text
    foreign = await api.other.post(
        f"/api/v2/portfolios/{roots[0]}/stock-trades",
        json={
            "symbol": "AAPL",
            "side": "buy",
            "quantity": "1",
            "expected_exec_price": "102",
            "idempotency_key": str(uuid4()),
        },
        headers={"X-CSRF-Token": "test-csrf"},
    )
    assert foreign.status_code == 404
    assert [await ledger(api, root) for root in roots] == before
