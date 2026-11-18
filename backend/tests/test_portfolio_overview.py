"""Bounded shared statements on the actual restricted current-schema database."""

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.services import portfolio as service
from app.services.portfolios import OwnedActivePortfolio
from tests.test_portfolio_creation import management_api
from tests.test_portfolio_management_authority import authority, close, create
from tests.test_portfolio_valuation import (
    migrated,
    ownership,
    status_case,
    stock_books,
    stock_trade_case,
)

__all__ = [
    "management_api",
    "authority",
    "migrated",
    "ownership",
    "status_case",
    "stock_books",
    "stock_trade_case",
]


async def test_actual_mixed_overview_detail_parity_and_safety(
    stock_books, management_api, monkeypatch
):
    from app.core.security import create_access_token
    from tests.test_portfolio_stock_trading import execute, order

    factory, _, (root, sibling, *_), _ = stock_books
    api = management_api
    settings = api.app.state.settings
    await execute(factory, root, settings)
    await execute(factory, sibling, settings, order(quantity="3"))
    now = datetime.now(UTC)
    async with api.migrator.begin() as conn:
        session = (
            await conn.execute(
                text("INSERT INTO auth_sessions(user_id) VALUES (:u) RETURNING id"),
                {"u": root.user_id},
            )
        ).scalar_one()
        btc = (await conn.execute(text("SELECT id FROM coins WHERE symbol='BTC'"))).scalar_one()
        eth = (await conn.execute(text("SELECT id FROM coins WHERE symbol='ETH'"))).scalar_one()
        await conn.execute(text("DELETE FROM prices"))
        await conn.execute(
            text("INSERT INTO prices(coin_id,mid,as_of,source) VALUES (:c,100,:t,'fake')"),
            {"c": btc, "t": now},
        )
        for book, coin in ((root, btc), (sibling, eth)):
            await conn.execute(
                text(
                    "INSERT INTO holdings(portfolio_id,user_id,coin_id,quantity,cost_basis) "
                    "VALUES (:p,:u,:c,0.1,5)"
                ),
                {"p": book.portfolio_id, "u": root.user_id, "c": coin},
            )
    api.client.cookies.set(
        "bj_access", create_access_token(root.user_id, session, settings.jwt_secret)
    )

    class FixedClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now

    monkeypatch.setattr(service, "datetime", FixedClock)
    response = await api.client.get("/api/v2/portfolios/overview")
    assert response.status_code == 200, response.text
    a, b = response.json()
    assert a["total_value"] == a["known_value"] == "1008.00"
    assert a["total_pl"] == "-8992.00" and a["total_pl_percent"] == "-89.92"
    assert b["known_value"] == "1997.00" and b["starting_cash"] == "7654.00"
    assert b["total_value"] is b["total_pl"] is b["total_pl_percent"] is None
    assert b["unvalued_holding_count"] == 1
    for row in (a, b):
        detail = (await api.client.get(f"/api/v2/portfolios/{row['id']}")).json()
        assert {k: v for k, v in row.items() if k not in {"id", "description"}} == {
            k: v for k, v in detail.items() if k != "portfolio_id"
        }
    # A current safety loss cannot renew/retain yesterday's complete valuation.
    async with api.migrator.begin() as conn:
        await conn.execute(text("UPDATE stock_action_state SET health='unknown'"))
    a, b = (await api.client.get("/api/v2/portfolios/overview")).json()
    assert a["known_value"] == "806.00" and a["total_value"] is None
    assert b["known_value"] == "1694.00" and b["unvalued_holding_count"] == 2


@pytest.mark.parametrize("count", [0, 1, 10])
async def test_actual_overview_contract_and_constant_financial_queries(management_api, count):
    api = management_api
    roots = [
        await create(api.restricted, api.uid, f"Book {n}", f"Description {n}") for n in range(count)
    ]
    foreign = await create(api.restricted, api.other_uid, "Private foreign")
    closed = await create(api.restricted, api.other_uid, "Private closed")
    await close(api.migrator, closed.portfolio_id)
    queries = []

    def capture(conn, cursor, statement, params, context, many):
        queries.append(statement)

    engine = api.app.state.engine.sync_engine
    event.listen(engine, "before_cursor_execute", capture)
    try:
        response = await api.client.get("/api/v2/portfolios/overview")
    finally:
        event.remove(engine, "before_cursor_execute", capture)
    assert response.status_code == 200, response.text
    assert len(queries) <= 3  # One session/auth check plus <=2 financial SQL.
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Cookie, Authorization"
    payload = response.json()
    assert [p["id"] for p in payload] == [str(r.portfolio_id) for r in roots]
    assert len({p["valued_at"] for p in payload}) <= 1
    if count == 1:
        from pydantic import TypeAdapter, ValidationError

        from app.schemas.portfolios import PortfolioOverview, PortfolioOverviewList

        with pytest.raises(ValidationError):
            PortfolioOverview.model_validate({**payload[0], "pooled_total": "10000"})
        with pytest.raises(ValidationError):
            TypeAdapter(PortfolioOverviewList).validate_python(payload * 11)
        schema = api.app.openapi()["paths"]["/api/v2/portfolios/overview"]["get"]
        assert schema["responses"]["200"]["content"]["application/json"]["schema"]["maxItems"] == 10
    for index, row in enumerate(payload):
        detail = (await api.client.get(f"/api/v2/portfolios/{row['id']}")).json()
        expected_keys = (detail.keys() - {"portfolio_id"}) | {"id", "description"}
        assert row.keys() == expected_keys
        assert row["description"] == f"Description {index}"
        assert row["cash"] == row["starting_cash"] == row["total_value"] == "10000.00"
        assert row["total_pl"] == row["total_pl_percent"] == "0.00"
        assert {k: v for k, v in row.items() if k not in {"id", "description", "valued_at"}} == {
            k: v for k, v in detail.items() if k not in {"portfolio_id", "valued_at"}
        }
    discovery = await api.client.get("/api/v2/portfolios")
    assert discovery.json() == [{"id": str(r.portfolio_id), "name": r.name} for r in roots]
    other = await api.other.get("/api/v2/portfolios/overview")
    assert [p["id"] for p in other.json()] == [str(foreign.portfolio_id)]


async def test_actual_overview_private_auth_and_corrupt_overcap_refusal(management_api):
    import httpx

    api = management_api
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api.app), base_url="https://test"
    ) as guest:
        response = await guest.get("/api/v2/portfolios/overview")
    assert response.status_code == 401 and response.headers["cache-control"] == "no-store"
    async with api.migrator.begin() as conn:
        for n in range(11):
            await conn.execute(
                text(
                    "INSERT INTO accounts(user_id,name,name_key,cash,starting_cash) "
                    "VALUES (:u,:n,:n,1,1)"
                ),
                {"u": api.uid, "n": f"corrupt-{n}"},
            )
    response = await api.client.get("/api/v2/portfolios/overview")
    assert response.status_code == 409 and response.json()["detail"] == {"code": "portfolio_limit"}
    assert response.headers["cache-control"] == "no-store"


async def load(api, settings, ids=None, **kwargs):
    async with async_sessionmaker(api.restricted)() as db:
        return await service.load_portfolio_snapshots(
            db, owner_id=api.uid, portfolio_ids=ids, settings=settings, **kwargs
        )


@pytest.mark.parametrize("count", [0, 1, 10])
async def test_bounded_batch_matches_detail_exactly(management_api, settings, count):
    api = management_api
    roots = [await create(api.restricted, api.uid, f"Book {n}") for n in range(count)]
    now = datetime.now(UTC)
    queries = []

    def capture(conn, cursor, statement, parameters, context, many):
        queries.append(statement)

    event.listen(api.restricted.sync_engine, "before_cursor_execute", capture)
    try:
        if count == 0:
            assert await load(api, settings, [], now=now) == ()
            assert queries == []
        batch = await load(api, settings, now=now)
    finally:
        event.remove(api.restricted.sync_engine, "before_cursor_execute", capture)
    assert len(queries) <= 2
    assert [p.portfolio_id for p in batch] == [str(r.portfolio_id) for r in roots]
    for result in batch:
        assert result.cash == result.starting_cash == result.total_value == Decimal("10000")
        assert result.total_pl == result.total_pl_percent == 0
        async with async_sessionmaker(api.restricted)() as db:
            detail = await service.get_portfolio(
                db,
                portfolio=OwnedActivePortfolio(int(result.portfolio_id), api.uid),
                settings=settings,
                now=now,
            )
        assert asdict(detail) == asdict(result)


async def test_shared_symbols_custom_baseline_and_incomplete_are_per_book(management_api, settings):
    api = management_api
    roots = []
    now = datetime.now(UTC)
    async with api.migrator.begin() as conn:
        coin = (await conn.execute(text("SELECT id FROM coins WHERE symbol='BTC'"))).scalar_one()
        missing = (await conn.execute(text("SELECT id FROM coins WHERE symbol='ETH'"))).scalar_one()
        await conn.execute(text("DELETE FROM prices"))
        await conn.execute(
            text("INSERT INTO prices(coin_id,mid,as_of,source) VALUES (:c,100,:t,'fake')"),
            {"c": coin, "t": now},
        )
        for i in range(3):
            root = (
                await conn.execute(
                    text(
                        "INSERT INTO accounts(user_id,name,name_key,cash,starting_cash) "
                        "VALUES (:u,:n,:n,1000,7654) RETURNING id"
                    ),
                    {"u": api.uid, "n": f"legacy-{i}"},
                )
            ).scalar_one()
            roots.append(root)
            await conn.execute(
                text(
                    "INSERT INTO holdings(portfolio_id,user_id,coin_id,quantity,cost_basis) "
                    "VALUES (:p,:u,:c,:q,5)"
                ),
                {"p": root, "u": api.uid, "c": missing if i == 2 else coin, "q": Decimal(i + 1)},
            )
    a, b, c = await load(api, settings, now=now)
    assert (a.total_value, b.total_value) == (1100, 1200)
    assert a.total_pl == -6554 and a.total_pl_percent == Decimal("-85.63")
    assert c.known_value == 1000 and c.total_value is c.total_pl is c.total_pl_percent is None
    assert c.unvalued_holding_count == 1 and not c.valuation_complete
    assert {p.valued_at for p in (a, b, c)} == {now}
    assert a.prices_as_of == b.prices_as_of == now


@pytest.mark.parametrize("target", ["foreign", "closed", "unknown"])
async def test_explicit_batch_refuses_unavailable_without_partial_result(
    management_api, settings, target
):
    api = management_api
    own = await create(api.restricted, api.uid)
    other = await create(api.restricted, api.other_uid)
    if target == "closed":
        await close(api.migrator, own.portfolio_id)
    ids = {
        "foreign": [own.portfolio_id, other.portfolio_id],
        "closed": [own.portfolio_id],
        "unknown": [9223372036854775807],
    }[target]
    with pytest.raises(HTTPException) as exc:
        await load(api, settings, ids)
    assert exc.value.status_code == 404


async def test_zero_baseline_and_corrupt_eleventh_root_refuse_total_only(management_api, settings):
    api = management_api
    async with api.migrator.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO accounts(user_id,name,name_key,cash,starting_cash) "
                "VALUES (:u,'Legacy','legacy',10000,0)"
            ),
            {"u": api.uid},
        )
    (result,) = await load(api, settings)
    assert result.total_value == result.total_pl == 10000
    assert result.total_pl_percent is None
    # Privileged fixture corruption, never a public funding path.
    async with api.migrator.begin() as conn:
        for n in range(10):
            await conn.execute(
                text(
                    "INSERT INTO accounts(user_id,name,name_key,cash,starting_cash) "
                    "VALUES (:u,:n,:n,1,1)"
                ),
                {"u": api.uid, "n": f"corrupt-{n}"},
            )
    with pytest.raises(HTTPException) as exc:
        await load(api, settings)
    assert exc.value.status_code == 409


@pytest.mark.parametrize("ids", [[0], [-1], [True], ["1"], [1, 1], list(range(1, 12))])
async def test_malformed_or_overlong_batch_refuses_before_sql(management_api, settings, ids):
    with pytest.raises(HTTPException) as exc:
        await load(management_api, settings, ids)
    assert exc.value.status_code == 422


async def test_closure_between_financial_and_final_read_refuses(
    management_api, settings, monkeypatch
):
    from sqlalchemy.ext.asyncio import AsyncSession

    api = management_api
    root = await create(api.restricted, api.uid)
    execute = AsyncSession.execute
    reads = 0

    async def intercepted(db, stmt, *args, **kwargs):
        nonlocal reads
        result = await execute(db, stmt, *args, **kwargs)
        reads += 1
        if reads == 1:
            await close(api.migrator, root.portfolio_id)
        return result

    monkeypatch.setattr(AsyncSession, "execute", intercepted)
    with pytest.raises(HTTPException) as exc:
        await load(api, settings)
    assert exc.value.status_code == 404


async def test_final_membership_protects_response_until_reader_releases(
    management_api, settings, monkeypatch
):
    from sqlalchemy.exc import DBAPIError
    from sqlalchemy.ext.asyncio import AsyncSession

    api = management_api
    root = await create(api.restricted, api.uid)
    execute = AsyncSession.execute
    reads = 0
    protected = False

    async def intercepted(db, stmt, *args, **kwargs):
        nonlocal reads, protected
        result = await execute(db, stmt, *args, **kwargs)
        reads += 1
        if reads == 2:
            # Independent real writer races AFTER the final awaited statement.
            # It may only close once the read transaction releases its roots.
            try:
                async with api.migrator.begin() as writer:
                    await writer.execute(text("SET LOCAL lock_timeout='50ms'"))
                    await writer.execute(
                        text("UPDATE accounts SET closed_at=clock_timestamp() WHERE id=:p"),
                        {"p": root.portfolio_id},
                    )
            except DBAPIError as exc:
                assert exc.orig.sqlstate == "55P03"
                protected = True
        return result

    monkeypatch.setattr(AsyncSession, "execute", intercepted)
    (result,) = await load(api, settings)
    assert result.portfolio_id == str(root.portfolio_id) and protected
    await close(api.migrator, root.portfolio_id)
    assert await load(api, settings) == ()
