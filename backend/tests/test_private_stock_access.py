import asyncio
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select

from app.models.user import User
from tests.helpers import csrf_headers, selected_portfolio_path, sign_in, unique_email
from tests.stock_trade_fixtures import ownership, status_case, stock_trade_case

__all__ = ["ownership", "status_case", "stock_trade_case"]


@pytest.mark.asyncio
async def test_owner_stock_prices_and_orders_pause_when_the_list_widens(
    running_app, settings, auth_client, outbox, stock_trade_case, tmp_path, monkeypatch
) -> None:
    factory, _, owner_id, _ = stock_trade_case
    async with factory() as db:
        owner = (await db.execute(select(User.email).where(User.id == owner_id))).scalar_one()
    guest = unique_email("guest")
    email_file = tmp_path / "allowed-emails.txt"
    monkeypatch.setattr(
        running_app.state,
        "settings",
        settings.model_copy(
            update={"auth_allowed_emails_file": str(email_file), "stock_data_owner_id": owner_id}
        ),
    )

    await asyncio.to_thread(email_file.write_text, owner, encoding="utf-8")
    await sign_in(auth_client, outbox, owner)
    portfolio = await selected_portfolio_path(auth_client)
    stocks = "/api/v1/stocks"
    trade = portfolio + "/stock-trades"
    order = {"symbol": "AAPL", "side": "buy", "quantity": "1"}
    headers = await csrf_headers(auth_client)

    def apple_quotes(response: httpx.Response):
        assert response.status_code == 200
        return next(item["quote"] for item in response.json()["items"] if item["symbol"] == "AAPL")

    assert Decimal(apple_quotes(await auth_client.get(stocks))["ask"]) == 102
    assert (
        await auth_client.post(trade + "/quote", json=order, headers=headers)
    ).status_code == 200
    fill = {
        **order,
        "expected_exec_price": "102",
        "idempotency_key": str(uuid4()),
    }
    assert (await auth_client.post(trade, json=fill, headers=headers)).status_code == 201
    assert Decimal((await auth_client.get(portfolio)).json()["holdings"][0]["mid"]) == 101

    await asyncio.to_thread(email_file.write_text, f"{owner}\n{guest}", encoding="utf-8")
    assert apple_quotes(await auth_client.get(stocks)) is None
    preview = await auth_client.post(trade + "/quote", json=order, headers=headers)
    assert preview.status_code == 409
    assert preview.json()["detail"]["code"] == "permission_unavailable"
    assert (await auth_client.get(trade + "/AAPL/context")).status_code == 409
    assert (
        await auth_client.post(
            trade, json={**fill, "idempotency_key": str(uuid4())}, headers=headers
        )
    ).status_code == 409
    owner_book = (await auth_client.get(portfolio)).json()
    assert owner_book["holdings"][0]["mid"] is None
    assert Decimal(owner_book["holdings"][0]["quantity"]) == 1
    catalog = await auth_client.post(
        "/api/v2/stock-catalog/1/quote", json={"listing_version": "1"}, headers=headers
    )
    assert catalog.status_code == 409
    assert catalog.json()["detail"]["code"] == "permission_unavailable"

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=running_app), base_url="https://test"
    ) as guest_client:
        await sign_in(guest_client, outbox, guest)
        assert (await guest_client.get("/api/v1/prices")).status_code == 200
        await asyncio.to_thread(email_file.write_text, guest, encoding="utf-8")
        assert apple_quotes(await guest_client.get(stocks)) is None
        guest_portfolio = await selected_portfolio_path(guest_client)
        assert (
            await guest_client.get(guest_portfolio + "/stock-trades/AAPL/context")
        ).status_code == 409

    await asyncio.to_thread(email_file.write_text, owner, encoding="utf-8")
    assert Decimal(apple_quotes(await auth_client.get(stocks))["bid"]) == 100
