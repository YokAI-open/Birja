"""Real PostgreSQL discovery tests; permissions here are synthetic only."""

import asyncio
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import delete, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.corporate_action import StockActionState
from app.models.price import Coin
from app.models.stock import StockDataAdmission, StockQuote, StockSession
from app.services import stocks
from app.services.stock_sessions import build_sessions
from tests.helpers import sign_in, unique_email
from tests.test_stock_admission import action_admitted, admitted
from tests.test_stock_sessions import evidence

NOW = datetime(2026, 11, 10, 15, tzinfo=UTC)


@pytest_asyncio.fixture(autouse=True)
async def action_state_cleanup(engine, clean_stock_discovery):
    async with engine.begin() as conn:
        await conn.execute(delete(StockActionState))
    yield
    async with engine.begin() as conn:
        await conn.execute(delete(StockActionState))


async def seed(engine, *, event_at=NOW, now=NOW):
    authority = evidence(now)
    quote_permission = admitted()
    async with engine.begin() as conn:
        await conn.execute(
            insert(StockDataAdmission),
            [asdict(quote_permission), asdict(authority), asdict(action_admitted())],
        )
        await conn.execute(
            insert(StockSession), [asdict(r) for r in build_sessions(now, authority)]
        )
        ids = (
            (await conn.execute(select(Coin.id).where(Coin.asset_class == "stock"))).scalars().all()
        )
        await conn.execute(
            insert(StockActionState),
            [
                dict(
                    coin_id=cid,
                    admission_generation=4,
                    health="current",
                    epoch=1,
                    checked_at=now,
                    valid_until=now + timedelta(hours=1),
                    coverage_start=now - timedelta(days=1),
                    covered_until=now,
                )
                for cid in ids
            ],
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
                collected_at=now,
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


async def test_denied_persisted_row_with_null_times_keeps_metadata(
    engine, settings, clean_stock_discovery
):
    async with engine.begin() as conn:
        await conn.execute(insert(StockDataAdmission).values(product="quotes"))
    async with async_sessionmaker(engine)() as db:
        result = body(await stocks.list_stocks(db, settings, now=lambda: NOW))
    assert len(result["items"]) == 20
    assert all(item["quote"] is None for item in result["items"])
    assert result["admission"]["state"] == "unavailable"


async def test_repeatable_read_cannot_serve_old_authority(engine, settings, clean_stock_discovery):
    await seed(engine)
    async with engine.connect() as conn:
        conn = await conn.execution_options(isolation_level="REPEATABLE READ")
        async with AsyncSession(bind=conn) as db:
            result = body(await stocks.list_stocks(db, settings, now=lambda: NOW))
    assert len(result["items"]) == 20
    assert all(item["quote"] is None for item in result["items"])
    assert result["admission"]["state"] == "unavailable"


@pytest.mark.parametrize("condition", ["denied", "expired", "boundary", "valid"])
async def test_current_retention_controls_disclosure_and_client_deadline(
    engine, settings, clean_stock_discovery, condition
):
    await seed(engine)
    async with engine.begin() as conn:
        await conn.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "quotes")
            .values(
                retention_allowed=condition != "denied",
                quota={**admitted().quota, "retention_seconds": 2},
            )
        )
    elapsed = {"denied": 0, "expired": 3, "boundary": 2, "valid": 1}[condition]
    async with async_sessionmaker(engine)() as db:
        result = body(
            await stocks.list_stocks(db, settings, now=lambda: NOW + timedelta(seconds=elapsed))
        )
    if condition == "valid":
        assert result["items"][0]["quote"] is not None
        assert datetime.fromisoformat(result["admission"]["valid_until"]) == NOW + timedelta(
            seconds=2
        )
    else:
        assert result["items"][0]["quote"] is None


async def test_nondefault_verified_scope_projects_quotes(engine, settings, clean_stock_discovery):
    await seed(engine)
    scope = {"account": "reviewed-account", "server": "reviewed-server"}
    async with engine.begin() as conn:
        await conn.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product != "actions")
            .values(scope={**admitted().scope, **scope})
        )
        await conn.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "actions")
            .values(scope={**action_admitted().scope, **scope})
        )
    configured = settings.model_copy(
        update={"stock_data_account": scope["account"], "stock_data_server": scope["server"]}
    )
    async with async_sessionmaker(engine)() as db:
        result = body(await stocks.list_stocks(db, configured, now=lambda: NOW))
    assert result["items"][0]["session"]["state"] == "open"
    assert result["items"][0]["quote"] is not None


async def test_mixed_retention_windows_use_earliest_disclosed_deadline(
    engine, settings, clean_stock_discovery
):
    await seed(engine)
    async with engine.begin() as conn:
        coin_id = (await conn.execute(select(Coin.id).where(Coin.symbol == "MSFT"))).scalar_one()
        await conn.execute(
            insert(StockQuote).values(
                coin_id=coin_id,
                bid=100,
                ask=102,
                mid=101,
                source="alpaca",
                feed="iex",
                event_at=NOW - timedelta(seconds=1),
                collected_at=NOW - timedelta(seconds=1),
                session_date=NOW.date(),
                admission_generation=4,
            )
        )
        await conn.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "quotes")
            .values(quota={**admitted().quota, "retention_seconds": 2})
        )
    async with async_sessionmaker(engine)() as db:
        first = body(await stocks.list_stocks(db, settings, now=lambda: NOW))
        second = body(
            await stocks.list_stocks(db, settings, now=lambda: NOW + timedelta(seconds=1))
        )
    assert len([item for item in first["items"] if item["quote"]]) == 2
    assert datetime.fromisoformat(first["admission"]["valid_until"]) == NOW + timedelta(seconds=1)
    assert len([item for item in second["items"] if item["quote"]]) == 1
    assert datetime.fromisoformat(second["admission"]["valid_until"]) == NOW + timedelta(seconds=2)


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
    # Quote/calendar/action data alone does not establish reference or status rights.
    assert first["execution_reason"] == "permission_unavailable"
    assert first["quote_reason"] == "recent"
    assert result["attribution"]["label"] == "IEX prices"
    assert "simulat" in result["attribution"]["explanation"].lower()
    assert result["admission"]["generation"] == 4


@pytest.mark.parametrize("unit_epoch", [0, 1])
@pytest.mark.parametrize("source_age", [0, 121])
async def test_local_quote_units_never_enter_provider_projection(
    engine,
    settings,
    clean_stock_discovery,
    unit_epoch,
    source_age,
):
    await seed(engine, event_at=NOW - timedelta(seconds=source_age))
    async with engine.begin() as conn:
        await conn.execute(update(StockQuote).values(unit_epoch=unit_epoch))
    async with async_sessionmaker(engine)() as db:
        result = body(await stocks.list_stocks(db, settings, now=lambda: NOW))
    first = result["items"][0]
    assert first["symbol"] == "AAPL"
    assert first["execution_enabled"] is False
    if unit_epoch:
        assert first["quote"] is None
        assert first["quote_reason"] != "recent"
    else:
        assert first["quote"]["bid"] == "100.00000001"
        assert first["quote_reason"] == ("recent" if source_age == 0 else "stale")
    assert "secure-review" not in str(result)


@pytest.mark.parametrize("seconds,reason", [(119, "recent"), (120, "stale"), (121, "stale")])
async def test_source_age_refuses_at_120(engine, settings, clean_stock_discovery, seconds, reason):
    await seed(engine, event_at=NOW - timedelta(seconds=seconds))
    async with async_sessionmaker(engine)() as db:
        result = body(await stocks.list_stocks(db, settings, now=lambda: NOW))
    item = result["items"][0]
    assert item["quote_reason"] == reason
    assert item["quote"] is not None
    assert item["quote"]["age_seconds"] == seconds
    assert datetime.fromisoformat(item["quote"]["event_at"]) == NOW - timedelta(seconds=seconds)


async def login(auth_client, outbox):
    await sign_in(auth_client, outbox, unique_email("stocks"))


async def test_stock_endpoint_auth_and_no_store(client, auth_client, outbox, clean_stock_discovery):
    assert (await client.get("/api/v1/stocks")).status_code == 401
    await login(auth_client, outbox)
    response = await auth_client.get("/api/v1/stocks")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert set(response.headers["vary"].lower().split(", ")) >= {"cookie", "authorization"}
    data = response.json()
    assert len(data["items"]) == 20
    assert data["admission"]["state"] == "unavailable"
    assert all(row["quote"] is None for row in data["items"])
    assert all(row["status"]["state"] == "unknown" for row in data["items"])
    assert set(data) == {"server_now", "admission", "attribution", "items"}
    assert set(data["items"][0]) == {
        "id",
        "symbol",
        "company_name",
        "listing_exchange",
        "currency",
        "quote",
        "session",
        "status",
        "execution_enabled",
        "execution_reason",
        "quote_reason",
        "session_reason",
        "status_reason",
        "action",
        "valuation_reason",
    }
    for method in ("post", "put", "delete", "patch"):
        response = await getattr(auth_client, method)("/api/v1/stocks")
        assert response.status_code in (403, 405)


@pytest.mark.parametrize("change", ["revoked", "generation", "calendar_generation", "override"])
async def test_same_request_committed_change_redacts(
    engine, auth_client, outbox, clean_stock_discovery, monkeypatch, change
):
    await seed(engine)
    await login(auth_client, outbox)
    monkeypatch.setattr(stocks, "_now", lambda: NOW)
    paused, release = asyncio.Event(), asyncio.Event()
    original = AsyncSession.execute
    reads = []

    async def held(db, statement, *args, **kwargs):
        result = await original(db, statement, *args, **kwargs)
        if "stock_sessions" in str(statement) and not statement.get_execution_options().get(
            "stock_final_evidence"
        ):
            reads.append("actual staged read")
            paused.set()
            await asyncio.wait_for(release.wait(), 5)
        return result

    monkeypatch.setattr(AsyncSession, "execute", held)
    request = asyncio.create_task(auth_client.get("/api/v1/stocks"))
    try:
        await asyncio.wait_for(paused.wait(), 5)
        async with engine.begin() as admin:
            if change in ("revoked", "generation"):
                await admin.execute(
                    update(StockDataAdmission)
                    .where(StockDataAdmission.product == "quotes")
                    .values(generation=5, **({"state": "revoked"} if change == "revoked" else {}))
                )
            else:
                values = {"generation": 5}
                if change == "override":
                    calendar = evidence(NOW).calendar
                    values["calendar"] = {
                        **calendar,
                        "overrides": [
                            {
                                "exchange": "XNAS",
                                "date": "2026-11-10",
                                "state": "closed",
                                "source": "https://www.nasdaq.com/market-activity/stock-market-holiday-schedule",
                            }
                        ],
                    }
                await admin.execute(
                    update(StockDataAdmission)
                    .where(StockDataAdmission.product == "calendar")
                    .values(**values)
                )
        release.set()
        response = await asyncio.wait_for(request, 5)
    finally:
        release.set()
        if not request.done():
            request.cancel()
            await asyncio.gather(request, return_exceptions=True)
    assert reads == ["actual staged read"]
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 20
    assert data["items"][0]["quote"] is None
    assert "100.00000001" not in response.text
    assert "secure-review" not in response.text
    if change in ("calendar_generation", "override"):
        assert data["items"][0]["session"]["state"] == "unknown"
    else:
        assert data["items"][0]["quote_reason"] == "permission_unavailable"


@pytest.mark.parametrize("boundary", ["permission", "age", "close", "calendar_review"])
async def test_same_request_uses_final_clock(
    engine, auth_client, outbox, clean_stock_discovery, monkeypatch, boundary
):
    start = (
        NOW
        if boundary != "close"
        else NOW.replace(hour=20, minute=59, second=59, microsecond=999000)
    )
    event_at = start - timedelta(seconds=119, microseconds=999000) if boundary == "age" else start
    await seed(engine, now=start, event_at=event_at)
    async with engine.begin() as admin:
        if boundary == "permission":
            await admin.execute(
                update(StockDataAdmission)
                .where(StockDataAdmission.product == "quotes")
                .values(valid_until=start + timedelta(milliseconds=1))
            )
        elif boundary == "calendar_review":
            calendar = evidence(start).calendar
            await admin.execute(
                update(StockDataAdmission)
                .where(StockDataAdmission.product == "calendar")
                .values(
                    calendar={
                        **calendar,
                        "review_valid_until": (start + timedelta(milliseconds=1)).isoformat(),
                    }
                )
            )
    await login(auth_client, outbox)
    clock = [start]
    monkeypatch.setattr(stocks, "_now", lambda: clock[0])
    original = AsyncSession.execute

    async def cross(db, statement, *args, **kwargs):
        result = await original(db, statement, *args, **kwargs)
        if "stock_sessions" in str(statement) and not statement.get_execution_options().get(
            "stock_final_evidence"
        ):
            clock[0] = start + timedelta(milliseconds=1)
        return result

    monkeypatch.setattr(AsyncSession, "execute", cross)
    response = await auth_client.get("/api/v1/stocks")
    assert response.status_code == 200
    data = response.json()
    assert datetime.fromisoformat(data["server_now"]) == clock[0]
    item = data["items"][0]
    if boundary == "permission":
        assert item["quote"] is None
        assert item["quote_reason"] == "permission_unavailable"
    elif boundary == "age":
        assert item["quote"]["age_seconds"] == 120
        assert item["quote_reason"] == "stale"
    else:
        assert item["session"]["state"] == ("closed" if boundary == "close" else "unknown")
        if boundary == "close":
            assert item["quote"] is not None
            assert item["quote_reason"] == "session_unavailable"
        else:
            assert item["quote"] is None


@pytest.mark.parametrize("condition", ["closed", "previous_session", "unknown_calendar"])
async def test_historical_quotes_never_claim_recent_or_enable_execution(
    engine, settings, clean_stock_discovery, condition
):
    clock = NOW.replace(hour=21) if condition == "closed" else NOW
    event_at = NOW - timedelta(days=1) if condition == "previous_session" else NOW
    await seed(engine, now=clock, event_at=event_at)
    if condition == "unknown_calendar":
        async with engine.begin() as admin:
            await admin.execute(
                update(StockDataAdmission)
                .where(StockDataAdmission.product == "calendar")
                .values(state="revoked")
            )
    async with async_sessionmaker(engine)() as db:
        result = body(await stocks.list_stocks(db, settings, now=lambda: clock))
    item = result["items"][0]
    assert not item["execution_enabled"]
    assert item["quote_reason"] != "recent"
    if condition == "unknown_calendar":
        assert item["quote"] is None
    else:
        assert datetime.fromisoformat(item["quote"]["event_at"]) == event_at
        assert datetime.fromisoformat(item["quote"]["collected_at"]) == clock
        assert item["quote"]["age_seconds"] == int((clock - event_at).total_seconds())
        assert item["session"]["state"] == ("closed" if condition == "closed" else "open")


async def test_previous_request_revocation_and_failure_isolation(
    engine, auth_client, outbox, clean_stock_discovery, clean_prices, monkeypatch
):
    from app.models.price import Price

    await seed(engine)
    await login(auth_client, outbox)
    monkeypatch.setattr(stocks, "_now", lambda: NOW)
    first = await auth_client.get("/api/v1/stocks")
    assert first.json()["items"][0]["quote"] is not None
    async with engine.begin() as admin:
        await admin.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "quotes")
            .values(state="revoked", generation=5)
        )
        ids = (
            (
                await admin.execute(
                    select(Coin.id).where(Coin.asset_class == "crypto").order_by(Coin.id)
                )
            )
            .scalars()
            .all()
        )
        await admin.execute(
            insert(Price),
            [{"coin_id": i, "mid": Decimal("100"), "as_of": NOW, "source": "fake"} for i in ids],
        )
    assert (await auth_client.get("/api/v1/stocks")).json()["items"][0]["quote"] is None
    crypto = (await auth_client.get("/api/v1/prices")).json()
    assert len(crypto["items"]) == 15
    assert set(crypto) == {"server_time", "fresh_seconds", "stale_seconds", "items"}
    assert set(crypto["items"][0]) == {"symbol", "name", "price", "as_of", "age_seconds", "status"}


async def test_final_db_failure_keeps_metadata_and_no_raw_errors(
    engine, auth_client, outbox, clean_stock_discovery, monkeypatch
):
    await seed(engine)
    await login(auth_client, outbox)
    monkeypatch.setattr(stocks, "_now", lambda: NOW)
    original = AsyncSession.execute

    async def fail(db, statement, *args, **kwargs):
        if statement.get_execution_options().get("stock_final_evidence"):
            return await original(db, text("SELECT 1 / 0"))
        return await original(db, statement, *args, **kwargs)

    monkeypatch.setattr(AsyncSession, "execute", fail)
    response = await auth_client.get("/api/v1/stocks")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 20
    assert all(
        item["quote"] is None and item["session"]["state"] == "unknown" for item in data["items"]
    )
    assert data["admission"]["state"] == "unavailable"
    assert not any(
        marker in response.text for marker in ("division", "SELECT", "asyncpg", "secure-review")
    )


async def test_bounded_reads_and_no_io_after_projection(
    engine, settings, clean_stock_discovery, monkeypatch
):
    await seed(engine)
    original = AsyncSession.execute
    projected = []
    statements = []
    response_class = stocks.StocksResponse

    def projection(**kwargs):
        result = response_class(**kwargs)
        projected.append(True)
        return result

    async def monitor(db, statement, *args, **kwargs):
        assert not projected, "application DB work after immutable projection"
        statements.append(statement)
        return await original(db, statement, *args, **kwargs)

    monkeypatch.setattr(stocks, "StocksResponse", projection)
    monkeypatch.setattr(AsyncSession, "execute", monitor)
    async with async_sessionmaker(engine)() as db:
        response = await stocks.list_stocks(db, settings, now=lambda: NOW)
    assert len(response.items) == 20
    assert projected == [True]
    assert len(statements) == 3
    assert statements[-1].get_execution_options()["stock_final_evidence"]


async def test_action_unknown_suppresses_quote_without_hiding_identity(
    engine, settings, clean_stock_discovery
):
    await seed(engine)
    async with engine.begin() as conn:
        await conn.execute(delete(StockActionState))

    async with async_sessionmaker(engine)() as db:
        result = body(await stocks.list_stocks(db, settings, now=lambda: NOW))
    first = result["items"][0]
    assert first["quote"] is None
    assert first["action"] == {
        "state": "unknown",
        "reason": "monitor_unavailable",
        "epoch": 0,
        "checked_at": None,
        "valid_until": None,
    }
    assert first["valuation_reason"] == "action_unavailable"
    assert len(result["items"]) == 20


@pytest.mark.parametrize(
    "condition,expected",
    [
        ("current", "current"),
        ("expired", "unknown"),
        ("reconciling", "reconciling"),
        ("unknown", "unknown"),
        ("generation", "unknown"),
        ("coverage", "unknown"),
        ("future_check", "unknown"),
        ("boundary", "reconciling"),
        ("future_boundary", "current"),
    ],
)
async def test_action_current_monitor_and_deadlines(engine, settings, condition, expected):
    await seed(engine)
    values = {
        "expired": dict(valid_until=NOW),
        "reconciling": dict(health="reconciling"),
        "unknown": dict(health="unknown"),
        "generation": dict(admission_generation=5),
        "coverage": dict(covered_until=None),
        "future_check": dict(checked_at=NOW + timedelta(seconds=1)),
        "boundary": dict(next_blocking_at=NOW),
        "future_boundary": dict(next_blocking_at=NOW + timedelta(seconds=1)),
    }.get(condition, {})
    if condition == "expired":
        values["checked_at"] = NOW - timedelta(seconds=1)
    async with engine.begin() as conn:
        if values:
            await conn.execute(update(StockActionState).values(**values))
    async with async_sessionmaker(engine)() as db:
        result = body(await stocks.list_stocks(db, settings, now=lambda: NOW))
    first = result["items"][0]
    assert first["action"]["state"] == expected
    assert (first["quote"] is not None) == (expected == "current")
    if condition == "future_boundary":
        assert datetime.fromisoformat(first["action"]["valid_until"]) == NOW + timedelta(seconds=1)
    assert len(result["items"]) == 20
    assert all(not item["execution_enabled"] for item in result["items"])


@pytest.mark.parametrize("purpose", ["collection", "display", "derived", "retention"])
async def test_action_denied_rights_disclose_no_derived_timestamps(engine, settings, purpose):
    await seed(engine)
    async with engine.begin() as conn:
        await conn.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "actions")
            .values(**{purpose + "_allowed": False})
        )
    async with async_sessionmaker(engine)() as db:
        result = body(await stocks.list_stocks(db, settings, now=lambda: NOW))
    first = result["items"][0]
    assert first["quote"] is None
    assert first["action"] == dict(
        state="unknown", reason="monitor_unavailable", epoch=0, checked_at=None, valid_until=None
    )
    assert first["session"]["state"] == "open"


@pytest.mark.parametrize("change", ["hold", "generation", "rights", "resolution_health"])
async def test_action_final_committed_snapshot_after_staged_reads(
    engine, settings, monkeypatch, change
):
    await seed(engine)
    original = AsyncSession.execute
    changed = False

    async def intercept(db, statement, *args, **kwargs):
        nonlocal changed
        result = await original(db, statement, *args, **kwargs)
        if (
            "stock_sessions" in str(statement)
            and not statement.get_execution_options().get("stock_final_evidence")
            and not changed
        ):
            changed = True
            async with engine.begin() as conn:
                if change in ("hold", "resolution_health"):
                    await conn.execute(
                        update(StockActionState).values(health="reconciling", epoch=2)
                    )
                else:
                    await conn.execute(
                        update(StockDataAdmission)
                        .where(StockDataAdmission.product == "actions")
                        .values(
                            **(
                                dict(generation=5)
                                if change == "generation"
                                else dict(display_allowed=False)
                            )
                        )
                    )
        return result

    monkeypatch.setattr(AsyncSession, "execute", intercept)
    async with async_sessionmaker(engine)() as db:
        result = body(await stocks.list_stocks(db, settings, now=lambda: NOW))
    assert changed
    assert result["items"][0]["quote"] is None
    assert len(result["items"]) == 20
    if change in ("generation", "rights"):
        assert result["items"][0]["action"] == dict(
            state="unknown",
            reason="monitor_unavailable",
            epoch=0,
            checked_at=None,
            valid_until=None,
        )


async def test_action_calendar_revocation_hides_all_derived_authority(engine, settings):
    await seed(engine)
    async with engine.begin() as conn:
        await conn.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == "calendar")
            .values(state="revoked")
        )
    async with async_sessionmaker(engine)() as db:
        result = body(await stocks.list_stocks(db, settings, now=lambda: NOW))
    action = result["items"][0]["action"]
    assert action == dict(
        state="unknown", reason="monitor_unavailable", epoch=0, checked_at=None, valid_until=None
    )


@pytest.mark.parametrize("shape", ["overbound", "malformed_time"])
async def test_action_malformed_final_projection_is_failclosed(
    engine, settings, monkeypatch, shape
):
    from types import SimpleNamespace

    await seed(engine)
    original = AsyncSession.execute

    async def malformed(db, statement, *args, **kwargs):
        result = await original(db, statement, *args, **kwargs)
        if statement.get_execution_options().get("stock_final_evidence"):
            values = dict(result.one()._mapping)
            if shape == "overbound":
                values["actions"] = values["actions"] * 2
            else:
                values["actions"][0]["checked_at"] = "not-a-timestamp"
            return SimpleNamespace(one=lambda: SimpleNamespace(**values))
        return result

    monkeypatch.setattr(AsyncSession, "execute", malformed)
    async with async_sessionmaker(engine)() as db:
        result = body(await stocks.list_stocks(db, settings, now=lambda: NOW))
    assert result["items"][0]["quote"] is None
    assert result["items"][0]["action"] == dict(
        state="unknown", reason="monitor_unavailable", epoch=0, checked_at=None, valid_until=None
    )
    assert len(result["items"]) == 20
