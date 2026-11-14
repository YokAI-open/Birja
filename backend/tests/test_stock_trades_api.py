# ruff: noqa: F811
"""Authenticated HTTP uses real stock execution and isolated persisted authority."""

from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.models.user import User
from tests.helpers import csrf_headers, sign_in, unique_email
from tests.stock_trade_fixtures import ownership, status_case, stock_trade_case  # noqa: F401
from tests.test_stock_status import financial_snapshot

BASE = "/api/v1/stock-trades"


@pytest_asyncio.fixture
async def stock_http(stock_trade_case, auth_client, outbox):
    factory, cid, unused, now = stock_trade_case
    email = unique_email("stock-http")
    await sign_in(auth_client, outbox, email)
    async with factory() as db:
        uid = await db.scalar(select(User.id).where(User.email == email))
    yield auth_client, await csrf_headers(auth_client), factory, cid, uid, now


def body(**changes):
    return {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": "2",
        "expected_exec_price": "102",
        "idempotency_key": str(uuid4()),
        **changes,
    }


async def test_preview_context_and_fill_are_reachable_exact_and_private(stock_http):
    client, headers, factory, cid, uid, now = stock_http
    before = await financial_snapshot(factory)
    preview = await client.post(
        BASE + "/quote", json={"symbol": "AAPL", "side": "buy", "quantity": "2"}, headers=headers
    )
    assert preview.status_code == 200, preview.text
    assert Decimal(preview.json()["exec_price"]) == 102
    assert preview.headers["cache-control"] == "no-store"
    context = await client.get(BASE + "/AAPL/context")
    assert context.status_code == 200 and Decimal(context.json()["buy_max_quantity"]) == 98
    assert await financial_snapshot(factory) == before
    order = body()
    fill = await client.post(BASE, json=order, headers=headers)
    assert fill.status_code == 201, fill.text
    saved = fill.json()
    assert saved["coin_id"] == str(cid) and isinstance(saved["trade_id"], str)
    assert Decimal(saved["cash_after"]) == 9796 and Decimal(saved["held_after"]) == 2
    assert Decimal(saved["fee"]) == 0 and saved["feed"] == "iex"
    again = await client.post(BASE, json=order, headers=headers)
    assert again.status_code == 200 and again.json() == saved


@pytest.mark.parametrize(
    "method,path", [("GET", "/AAPL/context"), ("POST", "/quote"), ("POST", "")]
)
async def test_authentication_and_csrf_are_private_and_precede_finances(auth_client, method, path):
    headers = await csrf_headers(auth_client)
    response = await auth_client.request(
        method,
        BASE + path,
        json=body() if not path else {"symbol": "AAPL", "side": "buy", "quantity": "2"},
        headers=headers,
    )
    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"
    if method == "POST":
        response = await auth_client.post(BASE + path, json=body())
        assert response.status_code == 403 and response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "change",
    [
        {"quantity": 2},
        {"quantity": "1.5"},
        {"quantity": "0"},
        {"quantity": "1e2"},
        {"quantity": "1000000000000"},
        {"user_id": 1},
        {"amount_usd": "100"},
        {"expected_exec_price": 102},
        {"expected_exec_price": "NaN"},
        {"idempotency_key": "bad"},
    ],
)
async def test_invalid_economic_input_is_private_and_never_writes(stock_http, change):
    client, headers, factory, cid, uid, now = stock_http
    before = await financial_snapshot(factory)
    result = await client.post(BASE, json=body(**change), headers=headers)
    assert result.status_code == 422 and result.headers["cache-control"] == "no-store"
    assert await financial_snapshot(factory) == before


async def test_context_symbol_is_bounded_private_and_owner_scoped(stock_http):
    client, headers, factory, cid, uid, now = stock_http
    for symbol in ("aapl", "A" * 11):
        result = await client.get(BASE + f"/{symbol}/context")
        assert result.status_code == 422 and result.headers["cache-control"] == "no-store"
    result = await client.get(BASE + "/BTC/context")
    assert result.status_code == 409 and result.json()["detail"]["code"] == "quote_unavailable"


async def test_http_selected_price_reconfirmation_and_opposite_side_only(stock_http):
    from sqlalchemy import update

    from app.models.stock import StockQuote

    client, headers, factory, cid, uid, now = stock_http
    order = body()
    before = await financial_snapshot(factory)
    async with factory.begin() as db:
        await db.execute(
            update(StockQuote)
            .where(StockQuote.coin_id == cid)
            .values(ask=Decimal(103), mid=Decimal("101.5"))
        )
    changed = await client.post(BASE, json=order, headers=headers)
    assert changed.status_code == 409 and changed.headers["cache-control"] == "no-store"
    detail = changed.json()["detail"]
    assert detail["code"] == "price_changed"
    assert (
        Decimal(detail["previous_exec_price"]) == 102 and Decimal(detail["exec_price_change"]) == 1
    )
    assert (
        Decimal(detail["previous_cash_delta"]) == -204
        and Decimal(detail["cash_delta_change"]) == -2
    )
    assert await financial_snapshot(factory) == before
    # User explicitly confirms the replacement ask; opposite bid alone does not
    # alter that confirmed price. The actual saved source facts remain current.
    async with factory.begin() as db:
        await db.execute(
            update(StockQuote)
            .where(StockQuote.coin_id == cid)
            .values(bid=Decimal(101), mid=Decimal(102))
        )
    confirmed = await client.post(
        BASE, json={**order, "expected_exec_price": "103"}, headers=headers
    )
    assert confirmed.status_code == 201 and Decimal(confirmed.json()["exec_price"]) == 103
    assert (
        Decimal(confirmed.json()["bid"]) == 101 and Decimal(confirmed.json()["cash_after"]) == 9794
    )


async def test_http_original_receipt_after_sell_rename_and_revoke(stock_http):
    from sqlalchemy import update

    from app.models.price import Coin
    from app.models.stock import StockDataAdmission

    client, headers, factory, cid, uid, now = stock_http
    order = body()
    first = await client.post(BASE, json=order, headers=headers)
    assert first.status_code == 201
    sale = await client.post(
        BASE, json=body(side="sell", expected_exec_price="100"), headers=headers
    )
    assert sale.status_code == 201 and Decimal(sale.json()["held_after"]) == 0
    async with factory.begin() as db:
        old = (await db.execute(select(Coin.symbol, Coin.name).where(Coin.id == cid))).one()
        await db.execute(
            update(Coin)
            .where(Coin.id == cid)
            .values(symbol="RENAMED", name="Renamed", is_active=False)
        )
        await db.execute(update(StockDataAdmission).values(state="denied"))
    before = await financial_snapshot(factory)
    try:
        retry = await client.post(
            BASE, json={**order, "expected_exec_price": "999"}, headers=headers
        )
        assert retry.status_code == 200 and retry.json() == first.json()
        conflict = await client.post(BASE, json={**order, "quantity": "3"}, headers=headers)
        assert (
            conflict.status_code == 409
            and conflict.json()["detail"]["code"] == "idempotency_conflict"
        )
        assert await financial_snapshot(factory) == before
        new = await client.post(BASE, json=body(), headers=headers)
        assert new.status_code == 409 and new.headers["cache-control"] == "no-store"
    finally:
        async with factory.begin() as db:
            await db.execute(
                update(Coin)
                .where(Coin.id == cid)
                .values(symbol=old.symbol, name=old.name, is_active=True)
            )


@pytest.mark.parametrize("endpoint", ["/quote", "/AAPL/context", ""])
async def test_unapproved_authority_is_private_for_every_endpoint(stock_http, endpoint):
    from sqlalchemy import update

    from app.models.stock import StockDataAdmission

    client, headers, factory, cid, uid, now = stock_http
    async with factory.begin() as db:
        await db.execute(update(StockDataAdmission).values(state="denied"))
    before = await financial_snapshot(factory)
    if endpoint.endswith("context"):
        result = await client.get(BASE + endpoint)
    else:
        value = body() if endpoint == "" else {"symbol": "AAPL", "side": "buy", "quantity": "2"}
        result = await client.post(BASE + endpoint, json=value, headers=headers)
    assert result.status_code == 409 and result.json()["detail"]["code"] == "permission_unavailable"
    assert result.headers["cache-control"] == "no-store"
    assert await financial_snapshot(factory) == before


async def test_insufficient_quantity_or_cash_is_422(stock_http):
    client, headers, factory, cid, uid, now = stock_http
    for value, code in [
        (body(quantity="100"), "insufficient_cash"),
        (body(side="sell", expected_exec_price="100"), "insufficient_holding"),
    ]:
        result = await client.post(BASE, json=value, headers=headers)
        assert result.status_code == 422 and result.json()["detail"]["code"] == code
        assert result.headers["cache-control"] == "no-store"


async def test_response_failure_after_actual_commit_is_private_and_retry_recovers(
    stock_http, monkeypatch
):
    from app.services import stock_trading

    client, headers, factory, cid, uid, now = stock_http
    original = stock_trading.execute

    async def fail_after_actual_commit(*args, **kwargs):
        await original(*args, **kwargs)
        raise RuntimeError("private-test-detail-must-not-leak")

    monkeypatch.setattr(stock_trading, "execute", fail_after_actual_commit)
    order = body()
    result = await client.post(BASE, json=order, headers=headers)
    assert result.status_code == 500 and result.headers["cache-control"] == "no-store"
    assert result.json()["detail"]["code"] == "service_unavailable"
    assert "private-test-detail" not in result.text
    monkeypatch.setattr(stock_trading, "execute", original)
    before = await financial_snapshot(factory)
    retry = await client.post(BASE, json=order, headers=headers)
    assert retry.status_code == 200 and Decimal(retry.json()["cash_after"]) == 9796
    assert await financial_snapshot(factory) == before


async def test_openapi_contains_exact_models_and_auth_routes(app):
    schema = app.openapi()
    for path, method, model in [
        (BASE + "/quote", "post", "QuoteOut"),
        (BASE, "post", "FillOut"),
        (BASE + "/{symbol}/context", "get", "ContextOut"),
    ]:
        operation = schema["paths"][path][method]
        assert (
            operation["summary"]
            and operation["description"]
            and operation["tags"] == ["stock trades"]
        )
        response = operation["responses"]["201" if path == BASE else "200"]["content"][
            "application/json"
        ]["schema"]
        assert schema["components"]["schemas"][response["$ref"].rsplit("/", 1)[1]]["title"] == model
    ref = schema["paths"][BASE]["post"]["requestBody"]["content"]["application/json"]["schema"][
        "$ref"
    ]
    assert schema["components"]["schemas"][ref.rsplit("/", 1)[1]]["additionalProperties"] is False


def test_unknown_domain_code_is_an_uncertain_500():
    from app.api.v1.stock_trades import _refusal
    from app.services.trade_math import TradeRefused

    result = _refusal(TradeRefused("unknown-provider-code", "private-detail"))
    assert result.status_code == 500 and result.detail == {"code": "service_unavailable"}


async def test_http_shared_sale_cash_and_cross_asset_keys(stock_http, engine, clean_prices):
    from sqlalchemy import update

    from app.models.user import Account
    from tests.helpers import put_price

    client, headers, factory, cid, uid, now = stock_http
    await put_price(engine, "BTC", "100", now)
    async with factory.begin() as db:
        await db.execute(update(Account).where(Account.user_id == uid).values(cash=Decimal(204)))
    order = body()
    assert (await client.post(BASE, json=order, headers=headers)).status_code == 201
    sale = await client.post(
        BASE, json=body(side="sell", expected_exec_price="100"), headers=headers
    )
    assert sale.status_code == 201 and Decimal(sale.json()["cash_after"]) == 200
    crypto_key = str(uuid4())
    crypto = {
        "symbol": "BTC",
        "side": "buy",
        "amount_usd": "98",
        "expected_mid": "100",
        "idempotency_key": crypto_key,
    }
    result = await client.post("/api/v1/trades", json=crypto, headers=headers)
    assert result.status_code == 201 and Decimal(result.json()["cash_after"]) == 102
    assert Decimal(result.json()["fee"]) == Decimal("0.24")
    stock = await client.post(BASE, json=body(quantity="1"), headers=headers)
    assert stock.status_code == 201 and Decimal(stock.json()["cash_after"]) == 0
    before = await financial_snapshot(factory)
    stock_conflict = await client.post(BASE, json=body(idempotency_key=crypto_key), headers=headers)
    crypto_conflict = await client.post(
        "/api/v1/trades",
        json={**crypto, "idempotency_key": order["idempotency_key"]},
        headers=headers,
    )
    assert stock_conflict.status_code == crypto_conflict.status_code == 409
    assert (
        stock_conflict.json()["detail"]["code"]
        == crypto_conflict.json()["detail"]["code"]
        == "idempotency_conflict"
    )
    assert await financial_snapshot(factory) == before
    async with factory() as db:
        assert await db.scalar(select(Account.starting_cash).where(Account.user_id == uid)) == 10000


async def test_http_same_key_other_user_does_not_reveal_original_receipt(stock_http, outbox):
    client, headers, factory, cid, uid, now = stock_http
    order = body()
    first = await client.post(BASE, json=order, headers=headers)
    assert first.status_code == 201
    await sign_in(client, outbox, unique_email("other-stock-user"))
    other_headers = await csrf_headers(client)
    context = await client.get(BASE + "/AAPL/context")
    assert context.status_code == 200 and Decimal(context.json()["held_quantity"]) == 0
    assert Decimal(context.json()["cash"]) == 10000
    second = await client.post(BASE, json=order, headers=other_headers)
    assert second.status_code == 201 and second.json()["trade_id"] != first.json()["trade_id"]
    assert Decimal(second.json()["cash_after"]) == 9796


async def test_http_original_receipt_survives_matched_split(stock_http):
    from sqlalchemy import func

    from app.services.stock_ownership import StockMovementInput, append_stock_movement
    from tests.stock_action_fixtures import synthetic_split

    client, headers, factory, cid, uid, now = stock_http
    order = body()
    first = await client.post(BASE, json=order, headers=headers)
    assert first.status_code == 201
    async with factory.begin() as db:
        cutoff = await db.scalar(select(func.clock_timestamp()))
        split = await synthetic_split(db, cid, cutoff, boundary=1)
        await append_stock_movement(
            db,
            StockMovementInput(
                uid,
                cid,
                Decimal(2),
                Decimal(204),
                "split:" + str(split.id),
                application_id=split.id,
            ),
        )
    before = await financial_snapshot(factory)
    replay = await client.post(BASE, json=order, headers=headers)
    assert replay.status_code == 200 and replay.json() == first.json()
    assert Decimal(replay.json()["held_after"]) == 2
    new = await client.post(BASE, json=body(), headers=headers)
    assert new.status_code == 409 and new.json()["detail"]["code"] == "action_unavailable"
    assert await financial_snapshot(factory) == before
