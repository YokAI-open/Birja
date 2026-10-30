import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import event, func, select, update

from app.models.price import Coin
from app.models.trade import Holding, Trade
from app.models.user import Account, User
from tests.helpers import (
    cash_of,
    holding_of,
    put_holding,
    put_price,
    set_cash,
    sign_in,
    trade_count,
    unique_email,
)


async def test_portfolio_requires_session(auth_client):
    assert (await auth_client.get("/api/v1/portfolio")).status_code == 401


async def test_portfolio_is_private_plain_and_read_only(auth_client, outbox, engine, clean_prices):
    email = unique_email()
    await sign_in(auth_client, outbox, email)
    async with engine.connect() as conn:
        uid = (await conn.execute(select(User.id).where(User.email == email))).scalar_one()
    await set_cash(engine, uid, "9999")
    await put_holding(engine, uid, "BTC", "1", "2")
    before = (
        await cash_of(engine, uid),
        await holding_of(engine, uid, "BTC"),
        await trade_count(engine, uid),
    )
    response = await auth_client.get("/api/v1/portfolio")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert set(body) == {
        "cash",
        "starting_cash",
        "total_value",
        "total_pl",
        "total_pl_percent",
        "cash_allocation_percent",
        "valuation_complete",
        "valued_at",
        "prices_as_of",
        "fresh_seconds",
        "stale_seconds",
        "holdings",
    }
    assert body["cash"] == "9999.00"
    assert body["starting_cash"] == "10000.00"
    assert body["total_value"] is None
    h = body["holdings"][0]
    assert h["status"] == "unpriced"
    assert set(h) == {
        "symbol",
        "name",
        "is_active",
        "quantity",
        "cost_basis",
        "average_cost",
        "mid",
        "current_value",
        "unrealized_pl",
        "unrealized_pl_percent",
        "allocation_percent",
        "as_of",
        "age_seconds",
        "status",
    }
    for key in ("quantity", "cost_basis", "average_cost"):
        assert isinstance(h[key], str) and re.fullmatch(r"\d+(\.\d+)?", h[key])
    assert before == (
        await cash_of(engine, uid),
        await holding_of(engine, uid, "BTC"),
        await trade_count(engine, uid),
    )
    # A different real synthetic session must never inherit A's financial rows.
    auth_client.cookies.clear()
    await sign_in(auth_client, outbox, unique_email())
    other = (await auth_client.get("/api/v1/portfolio")).json()
    assert other["holdings"] == []
    assert other["cash"] == other["total_value"] == "10000.00"


async def test_portfolio_api_one_financial_read_inactive_and_missing_isolation(
    auth_client, outbox, engine, running_app, clean_prices
):
    email = unique_email()
    await sign_in(auth_client, outbox, email)
    async with engine.connect() as conn:
        uid = (await conn.execute(select(User.id).where(User.email == email))).scalar_one()
    await set_cash(engine, uid, "8000")
    await put_holding(engine, uid, "BTC", "1", "1000")
    await put_holding(engine, uid, "ETH", "2", "1000")
    as_of = datetime.now(UTC) - timedelta(seconds=301)
    await put_price(engine, "BTC", "1000", as_of)

    async def row_counts():
        async with engine.connect() as conn:
            return tuple(
                (
                    await conn.execute(
                        select(
                            *(
                                select(func.count())
                                .select_from(model)
                                .where(model.user_id == uid)
                                .scalar_subquery()
                                for model in (Account, Holding, Trade)
                            )
                        )
                    )
                ).one()
            )

    counts_before = await row_counts()
    async with engine.begin() as conn:
        await conn.execute(update(Coin).where(Coin.symbol == "BTC").values(is_active=False))
    before = (
        await cash_of(engine, uid),
        await holding_of(engine, uid, "BTC"),
        await holding_of(engine, uid, "ETH"),
        await trade_count(engine, uid),
    )
    statements = []

    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.upper())

    api_engine = running_app.state.engine.sync_engine
    event.listen(api_engine, "before_cursor_execute", capture)
    try:
        response = await auth_client.get("/api/v1/portfolio")
    finally:
        event.remove(api_engine, "before_cursor_execute", capture)
        async with engine.begin() as conn:
            await conn.execute(update(Coin).where(Coin.symbol == "BTC").values(is_active=True))
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    financial = [s for s in statements if "FROM ACCOUNTS" in s]
    assert len(financial) == 1
    assert all(table in financial[0] for table in ("HOLDINGS", "COINS", "PRICES"))
    assert all("FOR UPDATE" not in s for s in statements)
    assert any("FROM USERS" in s for s in statements)  # Existing authentication is separate.
    body = response.json()
    assert not body["valuation_complete"]
    assert body["total_value"] is body["total_pl"] is body["total_pl_percent"] is None
    assert body["cash_allocation_percent"] is None
    assert datetime.fromisoformat(body["prices_as_of"]) == as_of
    assert datetime.fromisoformat(body["valued_at"]) >= as_of + timedelta(seconds=301)
    rows = {h["symbol"]: h for h in body["holdings"]}
    assert set(rows) == {"BTC", "ETH"}
    assert rows["BTC"]["is_active"] is False
    assert rows["BTC"]["current_value"] == "1000.00"
    assert rows["BTC"]["status"] == "stale"
    assert rows["BTC"]["age_seconds"] >= 301
    assert rows["ETH"]["status"] == "unpriced"
    for key in (
        "mid",
        "current_value",
        "unrealized_pl",
        "unrealized_pl_percent",
        "as_of",
        "age_seconds",
    ):
        assert rows["ETH"][key] is None
    assert all(h["allocation_percent"] is None for h in rows.values())
    assert await row_counts() == counts_before == (1, 2, 0)
    assert before == (
        await cash_of(engine, uid),
        await holding_of(engine, uid, "BTC"),
        await holding_of(engine, uid, "ETH"),
        await trade_count(engine, uid),
    )
    auth_client.cookies.clear()
    other_email = unique_email()
    await sign_in(auth_client, outbox, other_email)
    async with engine.connect() as conn:
        other_uid = (
            await conn.execute(select(User.id).where(User.email == other_email))
        ).scalar_one()
    await set_cash(engine, other_uid, "9990")
    await put_holding(engine, other_uid, "SOL", "3", "10")
    other = (await auth_client.get("/api/v1/portfolio")).json()
    assert other["cash"] == "9990.00"
    assert [h["symbol"] for h in other["holdings"]] == ["SOL"]
    assert other["holdings"][0]["quantity"] == "3.00000000"
