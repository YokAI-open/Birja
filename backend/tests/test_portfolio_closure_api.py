"""Actual authenticated DELETE requests against restricted current PostgreSQL."""

from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest_asyncio
from sqlalchemy import text

from app.core.security import create_access_token
from app.db.portfolio_bootstrap import GRANTS_0023_SQL
from app.main import create_app
from tests.test_portfolio_closure_authority import authority
from tests.test_portfolio_management_authority import owner

__all__ = ["authority"]
POLICY = "freeze_at_closure_v1"
CSRF = {"X-CSRF-Token": "test-csrf"}


@pytest_asyncio.fixture
async def closure_api(authority, settings):
    restricted, migrator, admin = authority
    async with admin.begin() as conn:
        raw = await conn.get_raw_connection()
        await raw.driver_connection.execute(GRANTS_0023_SQL)
    config = settings.model_copy(
        update={
            "database_url": restricted.url.render_as_string(hide_password=False),
            "price_source": "fake",
            "email_backend": "console",
        }
    )
    app = create_app(config)
    clients, owners = [], []
    async with app.router.lifespan_context(app):
        for _ in range(2):
            uid = await owner(migrator)
            async with migrator.begin() as conn:
                sid = (
                    await conn.execute(
                        text("INSERT INTO auth_sessions(user_id) VALUES (:u) RETURNING id"),
                        {"u": uid},
                    )
                ).scalar_one()
            client = httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://test"
            )
            client.cookies.set("bj_access", create_access_token(uid, sid, config.jwt_secret))
            client.cookies.set("bj_csrf", "test-csrf")
            clients.append(client)
            owners.append(uid)
        try:
            yield SimpleNamespace(
                client=clients[0], other=clients[1], uid=owners[0], other_uid=owners[1],
                app=app, migrator=migrator, restricted=restricted, admin=admin,
            )
        finally:
            for client in clients:
                await client.aclose()


async def create(api, name="Strategy", *, key=None, client=None):
    return await (client or api.client).post(
        "/api/v2/portfolios", json={"name": name},
        headers={**CSRF, "Idempotency-Key": str(key or uuid4())},
    )


def intent(name="Strategy", *, key=None):
    return {"intent_key": str(key or uuid4()), "confirmation_name": name, "policy_version": POLICY}


async def delete(api, root, payload=None, *, client=None):
    return await (client or api.client).request(
        "DELETE", f"/api/v2/portfolios/{root}", json=payload or intent(), headers=CSRF,
    )


async def test_confirmation_actual_delete_and_repeat_are_minimal_private(closure_api):
    api = closure_api
    made = await create(api)
    assert made.status_code == 201, made.text
    root = made.json()["id"]
    payload = intent()
    first = await delete(api, root, payload)
    assert first.status_code == 200, first.text
    assert first.json() == {"portfolio_id": root, "state": "closed"}
    assert first.headers["cache-control"] == "no-store"
    replay = await delete(api, root, payload)
    assert replay.status_code == 200 and replay.json() == first.json()
    assert (await api.client.get(f"/api/v2/portfolios/{root}/metadata")).status_code == 404
    async with api.migrator.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))).scalar_one() == 1
        assert (await conn.execute(text("SELECT cash,starting_cash FROM accounts WHERE id=:p"), {"p": int(root)})).one() == (10000, 10000)
