"""Private daily-series responses on the real authenticated PostgreSQL API."""

import asyncio
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

import httpx
from sqlalchemy import text

from app.core.security import create_access_token
from app.main import create_app
from app.services import portfolio_daily_values as history
from tests.test_migrations import install_runtime_grants_for_revision
from tests.test_portfolio_creation import authority, close, management_api, post
from tests.test_portfolio_daily_schema import (
    OBSERVATION,
    observation,
    run_migration,
    scratch_database,
)
from tests.test_portfolio_management_authority import owner

__all__ = ["authority", "management_api", "scratch_database"]

URL = "/api/v2/portfolios/value-history"
TODAY = date(2026, 11, 26)


async def create(api, name, *, foreign=False):
    response = await post(api, name, client=api.other if foreign else api.client)
    assert response.status_code == 201, response.text
    return int(response.json()["id"])


async def seed(conn, uid, root, day, total):
    await conn.execute(
        OBSERVATION,
        observation(
            uid,
            root,
            day=day,
            capture=datetime.combine(day, time(22, 15), UTC),
            total=Decimal(total) if total is not None else None,
            complete=total is not None,
        ),
    )


def assert_private(response):
    assert response.headers["cache-control"] == "no-store"
    assert "cookie" in response.headers["vary"].lower()


async def test_exact_private_daily_series_bounds_and_independent_owners(
    management_api, monkeypatch
):
    api = management_api

    class FixedClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.combine(TODAY, time(0, 30), UTC)

    monkeypatch.setattr(history, "datetime", FixedClock)
    empty = await api.client.get(URL)
    assert_private(empty)
    assert empty.json() == {"start_day": "2026-10-28", "end_day": "2026-11-26", "portfolios": []}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api.app), base_url="https://test"
    ) as client:
        anon = await client.get(URL)
    assert_private(anon)
    assert anon.status_code == 401

    first = await create(api, "First")
    closed = await create(api, "Closed")
    foreign = await create(api, "Foreign", foreign=True)
    large = 9007199254740993
    async with api.migrator.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO accounts(id,user_id,name,name_key,cash,starting_cash)
                OVERRIDING SYSTEM VALUE
                VALUES (:id,:owner,'Large ID','large id',100.00,220.00)
            """),
            {"id": large, "owner": api.uid},
        )
        for offset, total in [
            (-30, "90"),
            (-29, "9007199254740993.01"),
            (-5, None),
            (0, "99.99"),
            (1, "100.00"),
        ]:
            await seed(conn, api.uid, first, TODAY + timedelta(days=offset), total)
        await seed(conn, api.uid, closed, TODAY, "12.00")
        await seed(conn, api.other_uid, foreign, TODAY, "77.10")
    await close(api, str(closed))

    response = await api.client.get(URL)
    assert_private(response)
    assert response.status_code == 200, response.text
    assert response.json() == {
        "start_day": "2026-10-28",
        "end_day": "2026-11-26",
        "portfolios": [
            {
                "portfolio_id": str(first),
                "points": [
                    {
                        "utc_day": "2026-10-28",
                        "captured_at": "2026-10-28T22:15:00Z",
                        "total_value": "9007199254740993.01",
                        "valuation_complete": True,
                    },
                    {
                        "utc_day": "2026-11-21",
                        "captured_at": "2026-11-21T22:15:00Z",
                        "total_value": None,
                        "valuation_complete": False,
                    },
                    {
                        "utc_day": "2026-11-26",
                        "captured_at": "2026-11-26T22:15:00Z",
                        "total_value": "99.99",
                        "valuation_complete": True,
                    },
                ],
            },
            {"portfolio_id": str(large), "points": []},
        ],
    }
    filtered = await api.client.get(URL, params={"owner_id": api.other_uid, "limit": 1})
    assert filtered.json() == response.json()
    other = await api.other.get(URL)
    assert [item["portfolio_id"] for item in other.json()["portfolios"]] == [str(foreign)]
    assert other.json()["portfolios"][0]["points"][0]["total_value"] == "77.10"


async def test_close_commits_between_hydration_and_final_history_authority(
    management_api, monkeypatch
):
    api = management_api
    root = await create(api, "Last book")
    async with api.migrator.begin() as conn:
        await seed(conn, api.uid, root, datetime.now(UTC).date(), "10000.00")
    hydrated = asyncio.Event()
    finish = asyncio.Event()
    fence = history.fence_owned_active_portfolios

    async def wait_before_final_fence(db, owner_id, portfolios):
        assert portfolios == [root]
        hydrated.set()
        await finish.wait()
        await fence(db, owner_id, portfolios)

    monkeypatch.setattr(history, "fence_owned_active_portfolios", wait_before_final_fence)
    task = asyncio.create_task(api.client.get(URL))
    try:
        await asyncio.wait_for(hydrated.wait(), 5)
        await close(api, str(root))
        finish.set()
        response = await asyncio.wait_for(task, 5)
    finally:
        finish.set()
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    assert_private(response)
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "portfolio_unavailable"}}


async def test_admitted_0027_current_statements_survive_daily_refusal(
    authority, scratch_database, settings
):
    restricted, _, _ = authority
    admin, migrator = scratch_database
    await run_migration(migrator, "0027")
    async with admin.begin() as conn:
        await install_runtime_grants_for_revision(conn, "0027")
    uid = await owner(migrator)
    async with migrator.begin() as conn:
        sid = await conn.scalar(
            text("INSERT INTO auth_sessions(user_id) VALUES (:uid) RETURNING id"), {"uid": uid}
        )
    config = settings.model_copy(
        update={
            "database_url": restricted.url.set(database=admin.url.database).render_as_string(
                hide_password=False
            )
        }
    )
    app = create_app(config)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://test"
        ) as client,
    ):
        client.cookies.set("bj_access", create_access_token(uid, sid, config.jwt_secret))
        client.cookies.set("bj_csrf", "test-csrf")
        response = await post(None, "Predecessor", client=client)
        assert response.status_code == 201, response.text
        root = response.json()["id"]
        failed = await client.get(URL)
        assert_private(failed)
        assert failed.status_code == 503 and failed.json() == {
            "detail": {"code": "service_unavailable"}
        }
        overview = await client.get("/api/v2/portfolios/overview")
        current = await client.get(f"/api/v2/portfolios/{root}")
        orders = await client.get(f"/api/v2/portfolios/{root}/holdings/BTC")
        assert overview.status_code == current.status_code == orders.status_code == 200
        assert overview.json()[0]["total_value"] == current.json()["total_value"] == "10000.00"
