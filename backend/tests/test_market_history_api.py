"""Exercise real authentication, identities and bounded history demand."""

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest_asyncio
from redis.exceptions import RedisError

from app.core.config import Settings
from app.schemas.market_history import MarketHistoryQuery, MarketHistoryScopes
from app.services.market_history_demand import claim_history, request_history
from tests.helpers import sign_in, unique_email
from tests.test_stock_catalog_publish import catalog_factory as catalog_factory
from tests.test_stock_catalog_quotes import seed_catalog_quote_fixture

URL = "/api/v2/market-history/query"
BTC = {"instrument": {"kind": "crypto", "symbol": "BTC"}, "range": "1W"}


def scope_fields(now: datetime, server: str) -> dict:
    return {
        "generation": 1,
        "evidence_ref": "synthetic-reviewed-history-fixture",
        "server": server,
        "reviewed_at": (now - timedelta(minutes=2)).isoformat(),
        "valid_from": (now - timedelta(minutes=1)).isoformat(),
        "valid_until": (now + timedelta(minutes=9)).isoformat(),
        "collection_allowed": True,
        "display_allowed": True,
        "derived_allowed": True,
        "retention_seconds": 45,
        "admitted_requests_per_minute": 6,
        "observed_requests_per_minute": 6,
        "max_response_bytes": 32768,
    }


def crypto_scope(now: datetime, server: str, **changes: object) -> MarketHistoryScopes:
    return MarketHistoryScopes.model_validate_json(
        json.dumps(
            {
                "kraken": {
                    **scope_fields(now, server),
                    "aggregate_ip_requests_per_minute": 60,
                    "aggregate_pair_requests_per_minute": 12,
                    "targets": [{"instrument": BTC["instrument"], "pair": "XXBTZUSD"}],
                    **changes,
                },
            }
        )
    )


@pytest_asyncio.fixture
async def history_server(monkeypatch, settings, redis_client) -> AsyncIterator[str]:
    from app.services.market_history_demand import _queue

    server = f"test-history-{uuid4().hex}"
    monkeypatch.setattr(settings, "stock_data_server", server)
    yield server
    prefix = _queue(server)
    async for key in redis_client.scan_iter(f"{prefix}*"):
        await redis_client.delete(key)


async def test_auth_csrf_and_disabled_history(auth_client, outbox, settings) -> None:
    response = await auth_client.post(URL, json=BTC)
    assert response.status_code == 401
    assert "no-store" in response.headers["cache-control"]
    await sign_in(auth_client, outbox, unique_email())
    response = await auth_client.post(URL, json=BTC)
    assert response.status_code == 403
    headers = {"X-CSRF-Token": auth_client.cookies["bj_csrf"]}
    assert settings.market_history_scope_json is None
    response = await auth_client.post(URL, json=BTC, headers=headers)
    assert response.status_code == 200
    assert response.json() == {**BTC, "state": "unavailable", "series": None}
    assert "no-store" in response.headers["cache-control"]
    surplus = {**BTC, "provider": "unrecognized"}
    assert (await auth_client.post(URL, json=surplus, headers=headers)).status_code == 422


async def test_stale_catalog_version_refused_even_when_scope_disabled(
    auth_client,
    outbox,
    catalog_factory,
) -> None:
    now = datetime.now(UTC)
    async with catalog_factory.begin() as db:
        catalog_id, version = await seed_catalog_quote_fixture(db, now)
    await sign_in(auth_client, outbox, unique_email())
    headers = {"X-CSRF-Token": auth_client.cookies["bj_csrf"]}
    body = {
        "instrument": {
            "kind": "catalog",
            "catalog_id": str(catalog_id),
            "listing_version": str(version + 1),
        },
        "range": "1W",
    }
    response = await auth_client.post(URL, json=body, headers=headers)
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "listing_changed"}}
    assert "no-store" in response.headers["cache-control"]
    body["instrument"]["listing_version"] = str(version)
    response = await auth_client.post(URL, json=body, headers=headers)
    assert response.status_code == 200
    assert response.json() == {**body, "state": "unavailable", "series": None}


async def test_repeated_history_reads_share_work_and_rate_limits(
    auth_client,
    outbox,
    settings,
    monkeypatch,
    redis_client,
    history_server,
) -> None:
    scope = crypto_scope(datetime.now(UTC), history_server)
    monkeypatch.setattr(settings, "market_history_scope_json", scope)
    await sign_in(auth_client, outbox, unique_email())
    headers = {"X-CSRF-Token": auth_client.cookies["bj_csrf"]}
    replies = await asyncio.gather(
        *[auth_client.post(URL, json=BTC, headers=headers) for _ in range(12)]
    )
    assert all(r.status_code == 200 and r.json()["state"] == "pending" for r in replies)
    over = await auth_client.post(URL, json=BTC, headers=headers)
    assert over.json()["state"] == "unavailable"
    from app.services.market_history_demand import _queue, complete_history

    assert await redis_client.zcard(_queue(history_server)) == 1
    job = await claim_history(redis_client, history_server)
    assert job is not None and job.query == MarketHistoryQuery.model_validate(BTC)
    assert await claim_history(redis_client, history_server) is None
    assert await complete_history(redis_client, history_server, job)


async def test_pending_capacity_is_shared_across_users(redis_client, history_server) -> None:
    query = MarketHistoryQuery.model_validate(BTC)
    results = await asyncio.gather(
        *[
            request_history(
                redis_client,
                server=history_server,
                owner_id=index,
                query=query,
                fingerprint=f"{index:064x}",
            )
            for index in range(65)
        ]
    )
    assert sum(item.state == "pending" for item in results) == 64
    assert sum(item.state == "unavailable" for item in results) == 1


async def test_expired_scope_and_redis_outage_are_history_only(
    auth_client,
    outbox,
    settings,
    monkeypatch,
    running_app,
    redis_client,
    history_server,
) -> None:
    await sign_in(auth_client, outbox, unique_email())
    headers = {"X-CSRF-Token": auth_client.cookies["bj_csrf"]}
    now = datetime.now(UTC)
    monkeypatch.setattr(
        settings,
        "market_history_scope_json",
        crypto_scope(now - timedelta(minutes=10), history_server),
    )
    response = await auth_client.post(URL, json=BTC, headers=headers)
    assert response.json()["state"] == "unavailable"
    assert await claim_history(redis_client, history_server) is None
    monkeypatch.setattr(settings, "market_history_scope_json", crypto_scope(now, history_server))

    class BrokenCache:
        async def get(self, _key):
            raise RedisError("synthetic cache outage")

    monkeypatch.setattr(running_app.state, "catalog_quote_redis", BrokenCache())
    response = await auth_client.post(URL, json=BTC, headers=headers)
    assert response.json() == {**BTC, "state": "unavailable", "series": None}
    assert (await auth_client.get("/api/v1/prices")).status_code == 200


def test_invalid_optional_scope_leaves_other_services_configured(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_HISTORY_SCOPE_JSON", '{"kraken":{"display_allowed":false}}')
    assert Settings().market_history_scope_json is None
    valid = crypto_scope(datetime.now(UTC), "birja")
    monkeypatch.setenv("MARKET_HISTORY_SCOPE_JSON", valid.model_dump_json())
    assert Settings().market_history_scope_json == valid
