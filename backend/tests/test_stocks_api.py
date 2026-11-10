"""Real PostgreSQL discovery tests; permissions here are synthetic only."""

from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.price import Coin
from app.models.stock import StockDataAdmission, StockQuote, StockSession
from app.services import stocks
from app.services.stock_sessions import build_sessions
from tests.test_stock_admission import admitted
from tests.test_stock_sessions import evidence

NOW = datetime(2026, 11, 10, 15, tzinfo=UTC)


async def seed(engine, *, event_at=NOW, now=NOW):
    authority = evidence(now)
    quote_permission = admitted()
    async with engine.begin() as conn:
        await conn.execute(
            insert(StockDataAdmission), [asdict(quote_permission), asdict(authority)]
        )
        await conn.execute(
            insert(StockSession), [asdict(r) for r in build_sessions(now, authority)]
        )
        coin_id = (await conn.execute(select(Coin.id).where(Coin.symbol == "AAPL"))).scalar_one()
        await conn.execute(
            insert(StockQuote).values(
                coin_id=coin_id,
                bid=Decimal("100.00000001"),
                ask=Decimal("100.00000003"),
                mid=Decimal("100.00000002"),
                source="alpaca",
                feed="iex",
                event_at=event_at,
                collected_at=NOW,
                session_date=NOW.date(),
                admission_generation=4,
            )
        )


def body(response):
    return response.model_dump(mode="json") if hasattr(response, "model_dump") else response


async def test_catalogue_survives_absent_authority(engine, settings, clean_stock_discovery):
    async with async_sessionmaker(engine)() as db:
        result = body(await stocks.list_stocks(db, settings, now=lambda: NOW))
    assert len(result["items"]) == 20
    assert result["items"][0]["symbol"] == "AAPL"
    assert all(row["quote"] is None for row in result["items"])
    assert all(row["session"]["state"] == "unknown" for row in result["items"])
    assert all(row["execution_enabled"] is False for row in result["items"])


async def test_exact_quote_and_independent_facts(engine, settings, clean_stock_discovery):
    await seed(engine)
    async with async_sessionmaker(engine)() as db:
        result = body(await stocks.list_stocks(db, settings, now=lambda: NOW))
    assert len(result["items"]) == 20
    first = result["items"][0]
    assert first["quote"]["bid"] == "100.00000001"
    assert first["quote"]["ask"] == "100.00000003"
    assert first["quote"]["mid"] == "100.00000002"
    assert first["session"]["state"] == "open"
    assert first["status"] == {"state": "unknown", "observed_at": None, "valid_until": None}
    assert first["execution_reason"] == "phase_disabled"
    assert first["quote_reason"] == "recent"
    assert result["attribution"]["label"] == "IEX prices"
    assert "simulat" in result["attribution"]["explanation"].lower()
    assert result["admission"]["generation"] == 4
    assert "secure-review" not in str(result)


@pytest.mark.parametrize("seconds,reason", [(119, "recent"), (120, "stale"), (121, "stale")])
async def test_source_age_refuses_at_120(engine, settings, clean_stock_discovery, seconds, reason):
    await seed(engine, event_at=NOW - timedelta(seconds=seconds))
    async with async_sessionmaker(engine)() as db:
        result = body(await stocks.list_stocks(db, settings, now=lambda: NOW))
    item = result["items"][0]
    assert item["quote_reason"] == reason
    assert (item["quote"] is not None) is (seconds < 120)
