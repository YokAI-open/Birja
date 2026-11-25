"""Stock HTTP against the actual production router composition."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, update

from app.models.stock import StockDataAdmission, StockQuote
from app.models.stock_execution import StockStatusEvidence
from app.models.trade import Trade
from app.models.user import User
from app.services import stock_trading
from tests.helpers import sign_in
from tests.test_portfolio_stock_trading import (
    ownership,
    snapshot,
    status_case,
    stock_books,
    stock_trade_case,
)

__all__ = ["ownership", "status_case", "stock_books", "stock_trade_case"]


@pytest_asyncio.fixture
async def stock_auth(stock_books, auth_client, outbox):
    factory, cid, roots, now = stock_books
    async with factory() as db:
        email = await db.scalar(select(User.email).where(User.id == roots[0].user_id))
    await sign_in(auth_client, outbox, email)
    return auth_client, factory, cid, roots, now


def path(root, endpoint="stock-trades"):
    return f"/api/v2/portfolios/{root.portfolio_id}/{endpoint}"


def headers(client):
    return {"X-CSRF-Token": client.cookies["bj_csrf"]}


def body(**changes):
    return {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": "2",
        "expected_exec_price": "102",
        "idempotency_key": str(uuid4()),
        **changes,
    }


def private(response):
    assert response.headers["cache-control"] == "no-store"
    assert {x.strip().lower() for x in response.headers["vary"].split(",")} >= {
        "cookie",
        "authorization",
    }


async def test_scoped_quote_receipt_context_and_original_replay(stock_auth):
    client, factory, cid, (root, sibling, *_), now = stock_auth
    sibling_before = await snapshot(factory, sibling)
    quote = await client.post(
        path(root, "stock-trades/quote"),
        json={"symbol": "AAPL", "side": "buy", "quantity": "2"},
        headers=headers(client),
    )
    assert quote.status_code == 200
    private(quote)
    assert quote.json()["portfolio_id"] == str(root.portfolio_id)
    assert (
        Decimal(quote.json()["cash_before"]) == 1000 and Decimal(quote.json()["exec_price"]) == 102
    )
    order = body()
    first = await client.post(path(root), json=order, headers=headers(client))
    assert first.status_code == 201
    private(first)
    original = first.json()
    assert original["portfolio_id"] == str(root.portfolio_id) and Decimal(original["fee"]) == 0
    for key in (
        "quantity",
        "exec_price",
        "cash_after",
        "cash_delta",
        "exact_mid",
        "bid",
        "ask",
        "notional",
    ):
        assert isinstance(original[key], str)
    async with factory.begin() as db:
        saved = (
            await db.execute(select(Trade.__table__).where(Trade.id == int(original["trade_id"])))
        ).one()
        await db.execute(update(StockDataAdmission).values(state="denied"))
    again = await client.post(
        path(root), json={**order, "expected_exec_price": "999"}, headers=headers(client)
    )
    assert again.status_code == 200 and again.json() == original
    private(again)
    async with factory() as db:
        assert (
            await db.execute(select(Trade.__table__).where(Trade.id == int(original["trade_id"])))
        ).one() == saved
    assert await snapshot(factory, sibling) == sibling_before


async def test_context_never_uses_sibling_cash_or_holdings(stock_auth):
    client, _, _, (root, sibling, *_), _ = stock_auth
    for target, expected in ((root, 1000), (sibling, 2000)):
        response = await client.get(path(target, "stock-trades/AAPL/context"))
        assert response.status_code == 200
        private(response)
        assert response.json()["portfolio_id"] == str(target.portfolio_id)
        assert Decimal(response.json()["cash"]) == expected
        assert Decimal(response.json()["held_quantity"]) == 0


@pytest.mark.parametrize("target", ["foreign", "closed", "unknown"])
@pytest.mark.parametrize(
    "endpoint", ["stock-trades", "stock-trades/quote", "stock-trades/AAPL/context"]
)
async def test_unavailable_target_private_and_identical(stock_auth, target, endpoint):
    client, _, _, roots, _ = stock_auth
    pid = (
        roots[3].portfolio_id
        if target == "foreign"
        else roots[2].portfolio_id
        if target == "closed"
        else 9223372036854775807
    )
    url = f"/api/v2/portfolios/{pid}/{endpoint}"
    response = (
        await client.get(url)
        if endpoint.endswith("context")
        else await client.post(
            url,
            json=body()
            if endpoint == "stock-trades"
            else {"symbol": "AAPL", "side": "buy", "quantity": "2"},
            headers=headers(client),
        )
    )
    assert response.status_code == 404 and response.json() == {
        "detail": {"code": "portfolio_unavailable"}
    }
    private(response)


@pytest.mark.parametrize("pid", ["abc", "0", "-1", "9223372036854775808"])
async def test_malformed_path_has_no_private_financial_fallback(stock_auth, pid):
    client, *_ = stock_auth
    response = await client.get(f"/api/v2/portfolios/{pid}/stock-trades/AAPL/context")
    assert response.status_code == 422
    private(response)


async def test_root_and_payload_key_conflicts_cannot_disclose_receipt(stock_auth):
    client, _, _, (root, sibling, closed, *_), _ = stock_auth
    order = body()
    assert (await client.post(path(root), json=order, headers=headers(client))).status_code == 201
    for target, changes in ((sibling, {}), (root, {"quantity": "3"})):
        response = await client.post(
            path(target), json={**order, **changes}, headers=headers(client)
        )
        assert (
            response.status_code == 409
            and response.json()["detail"]["code"] == "idempotency_conflict"
        )
        private(response)
    unavailable = await client.post(path(closed), json=order, headers=headers(client))
    assert unavailable.status_code == 404
    assert unavailable.json() == {"detail": {"code": "portfolio_unavailable"}}
    private(unavailable)


async def test_body_target_override_is_rejected(stock_auth):
    client, factory, _, (root, sibling, *_), _ = stock_auth
    before = await snapshot(factory, root)
    response = await client.post(
        path(root), json=body(portfolio_id=str(sibling.portfolio_id)), headers=headers(client)
    )
    assert response.status_code == 422
    private(response)
    assert await snapshot(factory, root) == before


async def test_csrf_and_session_required(stock_auth):
    client, _, _, (root, *_), _ = stock_auth
    denied = await client.post(path(root), json=body())
    assert denied.status_code == 403
    private(denied)
    client.cookies.clear()
    denied = await client.get(path(root, "stock-trades/AAPL/context"))
    assert denied.status_code == 401
    private(denied)


async def test_repricing_then_stale_quote_never_fills_automatically(stock_auth):
    client, factory, cid, (root, *_), now = stock_auth
    before = await snapshot(factory, root)
    response = await client.post(
        path(root), json=body(expected_exec_price="101"), headers=headers(client)
    )
    assert response.status_code == 409 and response.json()["detail"]["code"] == "price_changed"
    assert response.json()["detail"]["quote"]["portfolio_id"] == str(root.portfolio_id)
    private(response)
    assert await snapshot(factory, root) == before
    async with factory.begin() as db:
        await db.execute(
            update(StockQuote)
            .where(StockQuote.coin_id == cid)
            .values(event_at=now - timedelta(minutes=3), collected_at=now - timedelta(minutes=3))
        )
    response = await client.post(path(root), json=body(), headers=headers(client))
    assert response.status_code == 409 and response.json()["detail"]["code"] == "quote_stale"
    assert await snapshot(factory, root) == before


async def test_response_loss_after_commit_keeps_original_target_retry(stock_auth, monkeypatch):
    client, factory, _, (root, sibling, *_), _ = stock_auth
    original = stock_trading.execute

    async def lost(*args, **kwargs):
        await original(*args, **kwargs)
        raise RuntimeError("synthetic response loss")

    order = body()
    with monkeypatch.context() as patch:
        patch.setattr(stock_trading, "execute", lost)
        response = await client.post(path(root), json=order, headers=headers(client))
    assert (
        response.status_code == 500 and response.json()["detail"]["code"] == "service_unavailable"
    )
    private(response)
    response = await client.post(path(root), json=order, headers=headers(client))
    assert response.status_code == 200 and response.json()["portfolio_id"] == str(root.portfolio_id)
    assert len((await snapshot(factory, root))[2]) == 1
    response = await client.post(path(sibling), json=order, headers=headers(client))
    assert response.status_code == 409


async def test_stock_quote_refresh_ends_read_transaction_and_receipts_skip_refresh(
    stock_auth, settings, monkeypatch
):
    from sqlalchemy import text

    from app.api.v2 import stock_trades

    client, factory, cid, (root, *_), now = stock_auth
    monkeypatch.setattr(settings, "stock_data_enabled", True)
    async with factory.begin() as db:
        await db.execute(
            update(StockQuote)
            .where(StockQuote.coin_id == cid)
            .values(event_at=now - timedelta(minutes=3), collected_at=now - timedelta(minutes=3))
        )
    requests = []
    ask = Decimal("102")

    async def refresh(_redis, symbol, **scope):
        requests.append(symbol)
        assert scope == {"account": "birja", "server": "birja"}
        async with factory.begin() as db:
            idle = await db.scalar(
                text(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
                    "AND state = 'idle in transaction'"
                )
            )
            assert idle == 0
            checked = datetime.now(UTC)
            await db.execute(
                update(StockQuote)
                .where(StockQuote.coin_id == cid)
                .values(
                    event_at=checked, collected_at=checked, ask=ask, mid=(Decimal("100") + ask) / 2
                )
            )
        return True

    monkeypatch.setattr(stock_trades, "request_stock_quote", refresh)
    preview = await client.post(
        path(root, "stock-trades/quote"),
        json={"symbol": "AAPL", "side": "buy", "quantity": "2"},
        headers=headers(client),
    )
    assert preview.status_code == 200
    assert requests == ["AAPL"]
    async with factory.begin() as db:
        await db.execute(
            update(StockQuote)
            .where(StockQuote.coin_id == cid)
            .values(event_at=now - timedelta(minutes=3), collected_at=now - timedelta(minutes=3))
        )
    draft = await client.get(path(root, "stock-trades/AAPL/context"))
    assert draft.status_code == 200
    assert draft.json()["execution_enabled"] is True
    assert draft.json()["portfolio_id"] == str(root.portfolio_id)
    assert Decimal(draft.json()["quote"]["ask"]) == ask
    async with factory.begin() as db:
        await db.execute(
            update(StockQuote)
            .where(StockQuote.coin_id == cid)
            .values(event_at=now - timedelta(minutes=3), collected_at=now - timedelta(minutes=3))
        )
    ask = Decimal("103")
    before = await snapshot(factory, root)
    order = body()
    repriced = await client.post(path(root), json=order, headers=headers(client))
    assert repriced.status_code == 409
    assert repriced.json()["detail"]["code"] == "price_changed"
    assert Decimal(repriced.json()["detail"]["quote"]["exec_price"]) == ask
    assert await snapshot(factory, root) == before

    order["expected_exec_price"] = str(ask)
    fill = await client.post(path(root), json=order, headers=headers(client))
    assert fill.status_code == 201
    async with factory.begin() as db:
        await db.execute(update(StockDataAdmission).values(state="denied"))
    replay = await client.post(path(root), json=order, headers=headers(client))
    assert replay.status_code == 200 and replay.json() == fill.json()
    assert requests == ["AAPL", "AAPL", "AAPL"]


async def test_reported_mode_ignores_legacy_status_and_redacts_expired_rows(
    stock_auth, settings, monkeypatch
):
    from app.api.v2 import stock_trades

    client, factory, cid, (root, *_), now = stock_auth
    monkeypatch.setattr(settings, "stock_data_enabled", True)
    calls = []

    async def unfulfilled(_redis, symbol, **_scope):
        calls.append(symbol)
        return False

    monkeypatch.setattr(stock_trades, "request_stock_quote", unfulfilled)
    draft_path = path(root, "stock-trades/AAPL/context")
    async with factory.begin() as db:
        await db.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "status")
            .values(scope=StockDataAdmission.scope.op("||")({"feed": "nasdaq-rss"}))
        )
    legacy = (await client.get(draft_path)).json()
    assert legacy["execution_reason"] == "status_unavailable"
    assert legacy["status"]["source"] == "nasdaq-rss"
    assert legacy["status"]["observed_at"] is None
    assert calls == []

    observed = now - timedelta(seconds=10)
    async with factory.begin() as db:
        await db.execute(
            update(StockStatusEvidence)
            .where(StockStatusEvidence.coin_id == cid)
            .values(
                source="nasdaq-rss",
                source_ref="a" * 64,
                bootstrap_verified=False,
                continuity_current=False,
                sequence=0,
                event_at=observed,
                observed_at=observed,
                valid_until=observed + timedelta(seconds=110),
            )
        )
        await db.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "status")
            .values(quota=StockDataAdmission.quota.op("||")({"retention_seconds": 1}))
        )
    expired_report = (await client.get(draft_path)).json()
    assert expired_report["execution_reason"] == "status_unavailable"
    assert expired_report["status"]["observed_at"] is None
    assert expired_report["quote"] is None
    assert calls == []

    async with factory.begin() as db:
        checked = datetime.now(UTC)
        await db.execute(
            update(StockStatusEvidence)
            .where(StockStatusEvidence.coin_id == cid)
            .values(
                event_at=observed, observed_at=checked, valid_until=checked + timedelta(seconds=90)
            )
        )
        await db.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "status")
            .values(quota=StockDataAdmission.quota.op("||")({"retention_seconds": 120}))
        )
        await db.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "quotes")
            .values(quota=StockDataAdmission.quota.op("||")({"retention_seconds": 1}))
        )
        await db.execute(
            update(StockQuote)
            .where(StockQuote.coin_id == cid)
            .values(event_at=observed, collected_at=observed)
        )
    expired_quote = (await client.get(draft_path)).json()
    assert expired_quote["execution_reason"] == "quote_unavailable"
    assert expired_quote["status"]["state"] == "normal"
    assert expired_quote["quote"] is None
    before = await snapshot(factory, root)
    refused = await client.post(
        path(root, "stock-trades/quote"),
        json={"symbol": "AAPL", "side": "buy", "quantity": "2"},
        headers=headers(client),
    )
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "quote_unavailable"
    assert await snapshot(factory, root) == before
    assert calls == ["AAPL", "AAPL"]

    async with factory.begin() as db:
        await db.execute(delete(StockStatusEvidence).where(StockStatusEvidence.coin_id == cid))
    missing_report = (await client.get(draft_path)).json()
    assert missing_report["execution_reason"] == "status_unavailable"
    assert calls == ["AAPL", "AAPL"]


async def test_reported_halt_rule_allows_fills_and_preserves_receipts(stock_auth, monkeypatch):
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.services.stock_halts import REPORT_LOCK_KEYS

    client, factory, cid, (root, sibling, *_), _ = stock_auth
    guarded = 0
    execute = AsyncSession.execute

    async def verify_report_fence(self, statement, *args, **kwargs):
        nonlocal guarded
        if str(statement).startswith("SELECT public.assert_stock_execution_current"):
            async with factory.begin() as writer:
                available = await writer.scalar(
                    text(f"SELECT pg_try_advisory_xact_lock({REPORT_LOCK_KEYS})")
                )
                assert available is False
            guarded += 1
        return await execute(self, statement, *args, **kwargs)

    monkeypatch.setattr(AsyncSession, "execute", verify_report_fence)
    before = await snapshot(factory, sibling)
    stamp = datetime.now(UTC)
    async with factory.begin() as db:
        await db.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "status")
            .values(scope=StockDataAdmission.scope.op("||")({"feed": "nasdaq-rss"}))
        )
        await db.execute(
            update(StockStatusEvidence)
            .where(StockStatusEvidence.coin_id == cid)
            .values(
                source="nasdaq-rss",
                source_ref="a" * 64,
                state="halted",
                bootstrap_verified=False,
                continuity_current=False,
                sequence=0,
                event_at=stamp,
                observed_at=stamp,
                valid_until=stamp + timedelta(seconds=110),
            )
        )
    refused = await client.post(path(root), json=body(), headers=headers(client))
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "halted"
    async with factory.begin() as db:
        await db.execute(
            update(StockStatusEvidence)
            .where(StockStatusEvidence.coin_id == cid)
            .values(state="normal", source_ref="b" * 64)
        )
    draft = await client.get(path(root, "stock-trades/AAPL/context"))
    assert draft.status_code == 200 and draft.json()["status"]["source"] == "nasdaq-rss"
    buy = body()
    bought = await client.post(path(root), json=buy, headers=headers(client))
    assert bought.status_code == 201
    assert Decimal(bought.json()["cash_after"]) == 796
    sold = await client.post(
        path(root), json=body(side="sell", expected_exec_price="100"), headers=headers(client)
    )
    assert sold.status_code == 201
    assert Decimal(sold.json()["cash_after"]) == 996
    assert Decimal(sold.json()["held_after"]) == 0
    assert guarded == 2
    catalogue = await client.get("/api/v1/stocks")
    assert catalogue.status_code == 200
    stock = next(row for row in catalogue.json()["items"] if row["symbol"] == "AAPL")
    assert stock["status"]["reported_at"] is not None
    assert stock["execution_enabled"] is True
    history = await client.get(path(root, "event-history"))
    assert history.status_code == 200
    assert [row["side"] for row in history.json()["items"]] == ["sell", "buy"]
    assert await snapshot(factory, sibling) == before
    async with factory.begin() as db:
        await db.execute(
            update(StockStatusEvidence)
            .where(StockStatusEvidence.coin_id == cid)
            .values(state="halted", source_ref="c" * 64)
        )
    replay = await client.post(path(root), json=buy, headers=headers(client))
    assert replay.status_code == 200 and replay.json() == bought.json()
