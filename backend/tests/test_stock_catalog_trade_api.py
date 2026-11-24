"""Owned catalog orders through HTTP with real PostgreSQL authority."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import delete, func, select, update

from app.api.v2 import stock_catalog as routes
from app.models.corporate_action import StockActionState
from app.models.stock_catalog_finance import StockCatalogFinancialQuote, StockCatalogStatus
from app.models.trade import Trade
from app.models.user import Account, User
from app.schemas.stock_catalog_quotes import CatalogOrderIn
from app.services.portfolios import OwnedActivePortfolio
from app.services.stock_catalog_trading import PreviewLease
from tests.helpers import OutboxSender, csrf_headers, sign_in, unique_email
from tests.test_portfolio_stock_api import headers, private
from tests.test_stock_catalog_sql_authority import execution_market as execution_market
from tests.test_stock_catalog_sql_authority import finance_0025 as finance_0025
from tests.test_stock_catalog_sql_authority import finance_0026 as finance_0026
from tests.test_stock_catalog_trading import catalog_market as catalog_market


@dataclass(frozen=True)
class Ticket:
    client: httpx.AsyncClient
    app: FastAPI
    market: dict[str, Any]

    def url(self, action: str, *, portfolio: int | None = None, issue: int | None = None) -> str:
        return (
            f"/api/v2/portfolios/{portfolio or self.market['p']}"
            f"/stock-catalog/{issue or self.market['catalog']}/{action}"
        )

    def order(self, side: str = "buy") -> dict[str, str]:
        return {"listing_version": str(self.market["listing"]), "side": side, "quantity": "1"}

    def confirmation(
        self, order: dict[str, str], price: str, *, remaining: int = 30
    ) -> dict[str, str]:
        lease = PreviewLease(datetime.now(UTC) + timedelta(seconds=remaining), 0)
        token = lease.token(
            self.market["settings"],
            OwnedActivePortfolio(self.market["p"], self.market["u"]),
            self.market["catalog"],
            CatalogOrderIn.model_validate(order),
            Decimal(price),
        )
        return {
            **order,
            "expected_exec_price": price,
            "idempotency_key": str(uuid4()),
            "preview_token": token,
        }

    async def post(
        self, action: str, body: dict, *, portfolio: int | None = None, issue: int | None = None
    ) -> httpx.Response:
        result = await self.client.post(
            self.url(action, portfolio=portfolio, issue=issue),
            headers=headers(self.client),
            json=body,
        )
        private(result)
        return result


@pytest_asyncio.fixture
async def ticket(
    finance_0026,
    catalog_market,
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    running_app: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
) -> Ticket:
    email = unique_email("catalog-order-owner")
    async with finance_0026.begin() as db:
        updated = await db.scalar(
            update(User)
            .where(User.id == catalog_market["u"])
            .values(email=email)
            .returning(User.id)
        )
    assert updated == catalog_market["u"]
    await sign_in(auth_client, outbox, email)
    monkeypatch.setattr(running_app.state, "settings", catalog_market["settings"])
    return Ticket(auth_client, running_app, catalog_market)


async def test_catalog_buy_repricing_sell_and_original_receipt(ticket: Ticket, finance_0026):
    context = await ticket.client.get(ticket.url("trade-context"))
    assert context.status_code == 200, context.text
    private(context)
    cash = Decimal(context.json()["cash"])
    assert context.json()["execution_reason"] == "available"
    assert context.json()["read_only"] is False
    assert Decimal(context.json()["buy_max_quantity"]) > 0
    assert Decimal(context.json()["held_quantity"]) == 0

    buy = ticket.order()
    preview = await ticket.post("preview", buy)
    assert preview.status_code == 200, preview.text
    first = preview.json()
    assert first["catalog_id"] == str(ticket.market["catalog"])
    assert first["listing_version"] == buy["listing_version"]
    assert first["symbol"] == "FQA" and first["portfolio_id"] == str(ticket.market["p"])
    assert {"reference", "provider_asset_id", "authority", "coin_id"}.isdisjoint(first)
    assert Decimal(first["exec_price"]) == Decimal(first["ask"])
    assert Decimal(first["cash_before"]) == cash and Decimal(first["held_after"]) == 1

    confirm = {
        **buy,
        "expected_exec_price": first["exec_price"],
        "idempotency_key": str(uuid4()),
        "preview_token": first["preview_token"],
    }
    ask = Decimal(first["ask"]) + Decimal("0.25")
    async with finance_0026.begin() as db:
        await db.execute(
            update(StockCatalogFinancialQuote)
            .where(StockCatalogFinancialQuote.coin_id == ticket.market["c"])
            .values(ask=ask)
        )

    repriced = await ticket.post("confirm", confirm)
    assert repriced.status_code == 409, repriced.text
    replacement = repriced.json()["detail"]
    assert replacement["code"] == "price_changed"
    assert Decimal(replacement["previous_exec_price"]) == Decimal(first["exec_price"])
    assert Decimal(replacement["quote"]["exec_price"]) == ask
    assert Decimal(replacement["exec_price_change"]) == Decimal("0.25")
    assert Decimal(replacement["cash_delta_change"]) == Decimal("-0.26")
    unchanged = await ticket.client.get(ticket.url("trade-context"))
    assert unchanged.status_code == 200, unchanged.text
    assert Decimal(unchanged.json()["cash"]) == cash

    confirmed = {
        **confirm,
        "expected_exec_price": replacement["quote"]["exec_price"],
        "preview_token": replacement["quote"]["preview_token"],
    }
    created = await ticket.post("confirm", confirmed)
    assert created.status_code == 201, created.text
    receipt = created.json()
    assert Decimal(receipt["held_after"]) == 1
    assert Decimal(receipt["cash_after"]) == cash + Decimal(replacement["quote"]["cash_delta"])
    assert {"reference", "provider_asset_id", "authority", "coin_id"}.isdisjoint(receipt)

    sell = ticket.order("sell")
    preview = await ticket.post("preview", sell)
    assert preview.status_code == 200, preview.text
    second = preview.json()
    assert Decimal(second["exec_price"]) == Decimal(second["bid"])
    closed = await ticket.post(
        "confirm",
        {
            **sell,
            "expected_exec_price": second["exec_price"],
            "idempotency_key": str(uuid4()),
            "preview_token": second["preview_token"],
        },
    )
    assert closed.status_code == 201, closed.text
    assert Decimal(closed.json()["cash_after"]) == Decimal(second["cash_after"])
    assert Decimal(closed.json()["held_after"]) == 0

    ticket.app.state.settings = ticket.app.state.settings.model_copy(
        update={"stock_data_enabled": False}
    )
    replay = await ticket.post("confirm", confirmed)
    assert replay.status_code == 200 and replay.json() == receipt
    read = await ticket.post("receipt", confirmed)
    assert read.status_code == 200 and read.json() == receipt
    expired_replay = {
        **ticket.confirmation(buy, confirmed["expected_exec_price"], remaining=-30),
        "idempotency_key": confirmed["idempotency_key"],
    }
    for verb in ("confirm", "receipt"):
        replay = await ticket.post(verb, expired_replay)
        assert replay.status_code == 200 and replay.json() == receipt
    for changed, issue in (
        ({**confirmed, "listing_version": str(ticket.market["listing"] + 1)}, None),
        ({**confirmed, "quantity": "2"}, None),
        (confirmed, ticket.market["catalog"] + 1),
    ):
        refused = await ticket.post("confirm", changed, issue=issue)
        assert refused.status_code == 409, refused.text
        assert refused.json() == {"detail": {"code": "idempotency_conflict"}}


async def test_catalog_order_lookup_never_posts_an_unrecorded_confirmation(ticket, finance_0026):
    preview = await ticket.post("preview", ticket.order())
    assert preview.status_code == 200, preview.text
    body = {
        **ticket.order(),
        "expected_exec_price": preview.json()["exec_price"],
        "idempotency_key": str(uuid4()),
        "preview_token": preview.json()["preview_token"],
    }
    denied = await ticket.client.post(ticket.url("receipt"), json=body)
    assert denied.status_code == 403
    for _ in range(2):
        nobody_booked = await ticket.post("receipt", body)
        assert nobody_booked.status_code == 409, nobody_booked.text
        assert nobody_booked.json() == {"detail": {"code": "receipt_unavailable"}}
    expired = ticket.confirmation(ticket.order(), body["expected_exec_price"], remaining=-30)
    rolled = await ticket.post("receipt", expired)
    assert rolled.status_code == 409
    assert rolled.json() == {"detail": {"code": "receipt_missing"}}
    tampered = {**expired, "quantity": "2"}
    unknown = await ticket.post("receipt", tampered)
    assert unknown.status_code == 409
    assert unknown.json() == {"detail": {"code": "receipt_unavailable"}}
    for order in (expired, tampered):
        delayed = await ticket.post("confirm", order)
        assert delayed.status_code == 409
        assert delayed.json() == {"detail": {"code": "quote_stale"}}
    missing_token = {key: value for key, value in body.items() if key != "preview_token"}
    assert (await ticket.post("confirm", missing_token)).status_code == 422
    async with finance_0026() as db:
        count = await db.scalar(
            select(func.count(Trade.id)).where(Trade.portfolio_id == ticket.market["p"])
        )
        assert count == 0
        cash = await db.scalar(select(Account.cash).where(Account.id == ticket.market["p"]))
        assert cash == Decimal(preview.json()["cash_before"])
    replacement = await ticket.post("preview", ticket.order())
    assert replacement.status_code == 200, replacement.text
    fill = await ticket.post(
        "confirm",
        {
            **body,
            "preview_token": replacement.json()["preview_token"],
            "idempotency_key": str(uuid4()),
        },
    )
    assert fill.status_code == 201, fill.text


async def test_catalog_confirmation_rolls_back_when_preview_expires_during_execution(
    ticket: Ticket, finance_0026, monkeypatch: pytest.MonkeyPatch
):
    service = routes.stock_catalog_trading
    original = service._book_stock_trade
    preview = await ticket.post("preview", ticket.order())
    assert preview.status_code == 200, preview.text
    order = ticket.confirmation(ticket.order(), preview.json()["exec_price"], remaining=3)
    reached_write = False

    async def wait_past_deadline(*args, **kwargs):
        nonlocal reached_write
        booked = await original(*args, **kwargs)
        reached_write = True
        await asyncio.sleep(3)
        return booked

    monkeypatch.setattr(service, "_book_stock_trade", wait_past_deadline)
    late = await ticket.post("confirm", order)
    assert reached_write
    assert late.status_code == 409
    assert late.json() == {"detail": {"code": "quote_stale"}}
    absent = await ticket.post("receipt", order)
    assert absent.status_code == 409
    assert absent.json() == {"detail": {"code": "receipt_missing"}}
    async with finance_0026() as db:
        count = await db.scalar(
            select(func.count(Trade.id)).where(Trade.portfolio_id == ticket.market["p"])
        )
        cash = await db.scalar(select(Account.cash).where(Account.id == ticket.market["p"]))
    assert count == 0 and cash == Decimal(preview.json()["cash_before"])


async def test_catalog_orders_require_csrf_ownership_and_current_listing(
    ticket: Ticket, finance_0026
):
    buy = ticket.order()
    confirm = ticket.confirmation(buy, "1.00")
    denied = await ticket.client.post(ticket.url("preview"), json=buy)
    assert denied.status_code == 403
    private(denied)
    denied = await ticket.client.post(ticket.url("confirm"), json=confirm)
    assert denied.status_code == 403
    private(denied)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ticket.app), base_url="https://test"
    ) as other:
        csrf = await csrf_headers(other)
        for verb, body in (("preview", buy), ("confirm", confirm)):
            denied = await other.post(ticket.url(verb), json=body, headers=csrf)
            assert denied.status_code == 401
            private(denied)

    async with finance_0026() as db:
        foreign = await db.scalar(select(Account.id).where(Account.user_id != ticket.market["u"]))
        frozen = await db.scalar(
            select(Account.id).where(
                Account.user_id == ticket.market["u"], Account.closed_at.is_not(None)
            )
        )
    assert isinstance(foreign, int) and isinstance(frozen, int)
    for portfolio in (foreign, frozen):
        for verb, body in (("preview", buy), ("confirm", confirm)):
            denied = await ticket.post(verb, body, portfolio=portfolio)
            assert denied.status_code == 404
            assert denied.json() == {"detail": {"code": "portfolio_unavailable"}}

    for invalid in (
        {**buy, "quantity": 1},
        {**buy, "quantity": "1.5"},
        {**buy, "listing_version": ticket.market["listing"]},
        {**buy, "symbol": "FQA"},
    ):
        assert (await ticket.post("preview", invalid)).status_code == 422

    for verb, body in (("preview", buy), ("confirm", confirm)):
        stale = {**body, "listing_version": str(ticket.market["listing"] + 1)}
        if verb == "confirm":
            stale = ticket.confirmation(
                {**buy, "listing_version": stale["listing_version"]}, "1.00"
            )
        changed = await ticket.post(verb, stale)
        assert changed.status_code == 409, changed.text
        assert changed.json() == {"detail": {"code": "listing_changed"}}


async def test_catalog_reported_halt_refuses_both_order_routes_without_refresh(
    ticket: Ticket, finance_0026, monkeypatch: pytest.MonkeyPatch
):
    async def unexpected_demand(*args, **kwargs):
        raise AssertionError("A reported halt must prevent refresh and order entry.")

    monkeypatch.setattr(routes, "request_catalog_quote", unexpected_demand)
    async with finance_0026.begin() as db:
        await db.execute(
            update(StockCatalogStatus)
            .where(StockCatalogStatus.coin_id == ticket.market["c"])
            .values(state="halted")
        )
    context = await ticket.client.get(ticket.url("trade-context"))
    assert context.status_code == 200, context.text
    assert context.json()["execution_reason"] == "halted"
    assert context.json()["read_only"] is True
    buy = ticket.order()
    confirm = ticket.confirmation(buy, "1.00")
    for verb, body in (("preview", buy), ("confirm", confirm)):
        refused = await ticket.post(verb, body)
        assert refused.status_code == 409, refused.text
        assert refused.json() == {"detail": {"code": "halted"}}


async def test_open_selection_requests_status_coverage_without_admitting_orders(
    ticket: Ticket, finance_0026, monkeypatch: pytest.MonkeyPatch
):
    async with finance_0026.begin() as db:
        await db.execute(
            delete(StockCatalogStatus).where(StockCatalogStatus.coin_id == ticket.market["c"])
        )
        await db.execute(
            delete(StockCatalogFinancialQuote).where(
                StockCatalogFinancialQuote.coin_id == ticket.market["c"]
            )
        )
    calls = []

    async def wait(redis, **selection):
        calls.append(selection)
        return "quote_unavailable"

    monkeypatch.setattr(routes, "request_catalog_quote", wait)
    selected = await ticket.client.post(
        f"/api/v2/stock-catalog/{ticket.market['catalog']}/quote",
        headers=headers(ticket.client),
        json={"listing_version": str(ticket.market["listing"])},
    )
    assert selected.status_code == 200, selected.text
    private(selected)
    assert selected.json()["read_only"] is True
    assert selected.json()["execution_reason"] == "status_unavailable"
    [request] = calls
    assert request["purpose"] == "financial"
    assert (request["catalog_id"], request["listing_version"]) == (
        ticket.market["catalog"],
        ticket.market["listing"],
    )
    assert len(request["fingerprint"]) == 64

    refused = await ticket.post("preview", ticket.order())
    assert refused.status_code == 409
    assert refused.json() == {"detail": {"code": "status_unavailable"}}
    assert len(calls) == 1


async def test_catalog_selection_refreshes_post_split_units_before_order(
    ticket: Ticket, finance_0026, monkeypatch: pytest.MonkeyPatch
):
    async with finance_0026.begin() as db:
        await db.execute(
            update(StockActionState)
            .where(StockActionState.coin_id == ticket.market["c"])
            .values(unit_epoch=1, quote_not_before=ticket.market["now"])
        )
    calls = []

    async def wait(redis, **selection):
        calls.append(selection)
        return "quote_unavailable"

    monkeypatch.setattr(routes, "request_catalog_quote", wait)
    selected = await ticket.client.post(
        f"/api/v2/stock-catalog/{ticket.market['catalog']}/quote",
        headers=headers(ticket.client),
        json={"listing_version": str(ticket.market["listing"])},
    )
    assert selected.status_code == 200, selected.text
    assert selected.json()["execution_reason"] == "units_changed"
    assert selected.json()["read_only"] is True
    assert len(calls) == 1 and calls[0]["purpose"] == "financial"
    refused = await ticket.post("preview", ticket.order())
    assert refused.status_code == 409
    assert refused.json() == {"detail": {"code": "units_changed"}}
    assert len(calls) == 2
