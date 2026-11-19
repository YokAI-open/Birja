"""Actual authenticated DELETE requests against restricted current PostgreSQL."""

import asyncio
import json
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
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
                # Real email input validation rejects reserved .test domains;
                # use a unique non-deliverable fixture address accepted by OTP.
                await conn.execute(
                    text("UPDATE users SET email=:e WHERE id=:u"),
                    {"u": uid, "e": f"closure-{uuid4().hex}@example.com"},
                )
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
                client=clients[0],
                other=clients[1],
                uid=owners[0],
                other_uid=owners[1],
                app=app,
                migrator=migrator,
                restricted=restricted,
                admin=admin,
            )
        finally:
            for client in clients:
                await client.aclose()


async def create(api, name="Strategy", *, key=None, client=None):
    browser = client or api.client
    return await browser.post(
        "/api/v2/portfolios",
        json={"name": name},
        headers={
            "X-CSRF-Token": browser.cookies["bj_csrf"],
            "Idempotency-Key": str(key or uuid4()),
        },
    )


def intent(name="Strategy", *, key=None):
    return {"intent_key": str(key or uuid4()), "confirmation_name": name, "policy_version": POLICY}


async def delete(api, root, payload=None, *, client=None):
    return await (client or api.client).request(
        "DELETE",
        f"/api/v2/portfolios/{root}",
        json=payload or intent(),
        headers=CSRF,
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
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))
        ).scalar_one() == 1
        assert (
            await conn.execute(
                text("SELECT cash,starting_cash FROM accounts WHERE id=:p"), {"p": int(root)}
            )
        ).one() == (10000, 10000)


@pytest.mark.parametrize(
    "first,large_owner",
    [(9007199254740993, False), (9007199254740993, True), (9223372036854775807, False)],
)
async def test_postgres_bigint_string_identity_can_close_without_rounding(
    closure_api, first, large_owner
):
    api = closure_api
    async with api.migrator.begin() as conn:
        await conn.execute(text("SELECT setval('accounts_id_seq',:n,false)"), {"n": first})
        if large_owner:
            uid = (
                await conn.execute(
                    text(
                        "INSERT INTO users(id,email) OVERRIDING SYSTEM VALUE "
                        "VALUES (:u,:e) RETURNING id"
                    ),
                    {"u": first + 2, "e": f"bigint-{uuid4().hex}@example.com"},
                )
            ).scalar_one()
            sid = (
                await conn.execute(
                    text("INSERT INTO auth_sessions(user_id) VALUES (:u) RETURNING id"),
                    {"u": uid},
                )
            ).scalar_one()
            api.client.cookies.set(
                "bj_access", create_access_token(uid, sid, api.app.state.settings.jwt_secret)
            )
    made = await create(api)
    assert made.status_code == 201, made.text
    assert made.json()["id"] == str(first)
    original = intent()
    response = await delete(api, str(first), original)
    assert response.status_code == 200, response.text
    assert response.json() == {"portfolio_id": str(first), "state": "closed"}
    assert (await delete(api, str(first), original)).json() == response.json()
    async with api.migrator.connect() as conn:
        assert (
            await conn.execute(
                text("SELECT cash,starting_cash,closed_at IS NOT NULL FROM accounts WHERE id=:p"),
                {"p": first},
            )
        ).one() == (10000, 10000, True)


async def state(api):
    async with api.migrator.connect() as conn:
        return (
            await conn.execute(
                text("SELECT id,name,cash,starting_cash,closed_at FROM accounts ORDER BY id")
            )
        ).all(), (
            await conn.execute(text("SELECT count(*) FROM portfolio_closure_intents"))
        ).scalar_one()


async def test_csrf_and_identity_precede_untrusted_body(closure_api):
    api = closure_api
    root = (await create(api)).json()["id"]
    before = await state(api)
    consumed = False

    async def dangerous():
        nonlocal consumed
        consumed = True
        yield b"{" + b" " * 9000

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api.app), base_url="https://test"
    ) as guest:
        r = await guest.request("DELETE", f"/api/v2/portfolios/{root}", content=dangerous())
    assert r.status_code == 401 and not consumed
    r = await api.client.request("DELETE", f"/api/v2/portfolios/{root}", content=dangerous())
    assert r.status_code == 403 and not consumed
    assert r.headers["cache-control"] == "no-store"
    assert await state(api) == before
    async with api.migrator.begin() as conn:
        await conn.execute(
            text("UPDATE auth_sessions SET revoked_at=clock_timestamp() WHERE user_id=:u"),
            {"u": api.uid},
        )
    r = await api.client.request(
        "DELETE", f"/api/v2/portfolios/{root}", content=dangerous(), headers=CSRF
    )
    assert r.status_code == 401 and not consumed
    assert r.headers["cache-control"] == "no-store"
    assert await state(api) == before


async def test_malformed_exact_body_and_canonical_review_refuse_without_writes(closure_api):
    api = closure_api
    root = (await create(api)).json()["id"]
    before = await state(api)
    original = intent()
    bodies = [
        {},
        [],
        None,
        {**original, "owner": api.uid},
        {**original, "cash": "10000"},
        {**original, "intent_key": str(uuid4()).upper()},
        {**original, "intent_key": str(uuid4()).replace("-", "")},
        {**original, "intent_key": "00000000-0000-0000-0000-000000000000"},
        {**original, "intent_key": 123},
        {**original, "confirmation_name": None},
        {**original, "confirmation_name": " Strategy "},
        {**original, "confirmation_name": "e\u0301"},
        {**original, "confirmation_name": "x" * 61},
        {**original, "confirmation_name": "bad\x00"},
        {**original, "policy_version": "other"},
    ]
    for payload in bodies:
        r = await api.client.request(
            "DELETE",
            f"/api/v2/portfolios/{root}",
            content=json.dumps(payload),
            headers={**CSRF, "content-type": "application/json"},
        )
        assert r.status_code == 422, r.text
        assert r.json() == {"detail": {"code": "invalid_input"}}
        assert r.headers["cache-control"] == "no-store"
    for raw, media, code in [
        (b"{", "application/json", 422),
        (b'{"intent_key":"x","intent_key":"y"}', "application/json", 422),
        (b"{}", "text/plain", 415),
        (b"[" * 1500, "application/json", 422),
    ]:
        r = await api.client.request(
            "DELETE",
            f"/api/v2/portfolios/{root}",
            content=raw,
            headers={**CSRF, "content-type": media},
        )
        assert r.status_code == code
    assert await state(api) == before
    # The exact bounded body remains valid; one extra byte is rejected even
    # when the Content-Length header claims the request is small.
    raw = json.dumps(original).encode().ljust(8192)
    for declared in (None, "1", "8193"):

        async def oversized():
            yield raw[:4000]
            yield raw[4000:] + b" "

        headers = {**CSRF, "content-type": "application/json"}
        if declared is not None:
            headers["content-length"] = declared
        r = await api.client.request(
            "DELETE", f"/api/v2/portfolios/{root}", content=oversized(), headers=headers
        )
        assert r.status_code == 413
    assert await state(api) == before
    r = await api.client.request(
        "DELETE",
        f"/api/v2/portfolios/{root}",
        content=raw,
        headers={**CSRF, "content-type": "application/json; charset=utf-8"},
    )
    assert r.status_code == 200


async def test_foreign_missing_and_path_boundaries_are_private(closure_api):
    api = closure_api
    root = (await create(api)).json()["id"]
    before = await state(api)
    for target, client in [(root, api.other), ("999999999", api.client)]:
        r = await delete(api, target, client=client)
        assert r.status_code == 404 and r.json() == {"detail": {"code": "portfolio_unavailable"}}
        assert r.headers["vary"] == "Cookie, Authorization"
    for target in ("0", "-1", "01", "1.0", "9223372036854775808", "x" * 20):
        r = await delete(api, target)
        assert r.status_code == 422 and r.json() == {"detail": {"code": "invalid_input"}}
        assert r.headers["cache-control"] == "no-store"
    assert await state(api) == before


async def test_confirmation_rename_refusal_and_key_conflict_are_durable(closure_api):
    api = closure_api
    root = (await create(api)).json()["id"]
    payload = intent("Wrong reviewed name")
    r = await delete(api, root, payload)
    assert r.status_code == 409 and r.json() == {
        "detail": {"code": "portfolio_confirmation_changed"}
    }
    async with api.migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT outcome FROM portfolio_closure_intents"))
        ).scalar_one() == "confirmation_changed"
    changed = await delete(api, root, {**payload, "confirmation_name": "Strategy"})
    assert (
        changed.status_code == 409 and changed.json()["detail"]["code"] == "closure_intent_conflict"
    )
    assert (await delete(api, root, intent())).status_code == 200


async def test_attempt_limits_have_ttl_and_replays_cannot_rotate_keys(closure_api):
    api = closure_api
    root = (await create(api)).json()["id"]
    api.app.state.settings = api.app.state.settings.model_copy(
        update={"portfolio_create_owner_limit": 2}
    )
    payload = intent()
    assert (await delete(api, root, payload)).status_code == 200
    assert (await delete(api, root, payload)).status_code == 200
    r = await delete(api, root, intent())
    assert r.status_code == 429 and 0 < int(r.headers["Retry-After"]) <= 60
    redis = api.app.state.redis
    keys = [k async for k in redis.scan_iter(match="sim:rl:portfolio_close:*")]
    assert len(keys) == 2
    assert all([0 < await redis.ttl(k) <= 60 for k in keys])
    assert (await state(api))[1] == 1


async def test_attempt_ip_limit_cannot_be_evaded_by_owner_rotation(redis_client, settings):
    from fastapi import HTTPException

    from app.api.v2.portfolio_management import enforce_closure_attempt

    limits = settings.model_copy(
        update={"portfolio_create_owner_limit": 2, "portfolio_create_ip_limit": 4}
    )
    for uid in (11, 11, 12, 13):
        await enforce_closure_attempt(redis_client, uid, "192.0.2.7", limits)
    with pytest.raises(HTTPException) as error:
        await enforce_closure_attempt(redis_client, 14, "192.0.2.7", limits)
    assert error.value.status_code == 429 and int(error.value.headers["Retry-After"]) > 0
    keys = [k async for k in redis_client.scan_iter(match="sim:rl:portfolio_close:*")]
    assert len(keys) == 4 and all([0 < await redis_client.ttl(k) <= 60 for k in keys])


async def test_real_owner_lock_timeout_refuses_then_retry_can_finish(closure_api):
    api = closure_api
    root = (await create(api)).json()["id"]
    payload = intent()
    before = await state(api)
    async with api.migrator.begin() as conn:
        await conn.execute(text("SELECT id FROM users WHERE id=:u FOR UPDATE"), {"u": api.uid})
        r = await asyncio.wait_for(delete(api, root, payload), timeout=6)
        assert r.status_code == 503 and r.headers["Retry-After"] == "5"
        assert r.json() == {"detail": {"code": "service_unavailable"}}
        assert await state(api) == before
    assert (await delete(api, root, payload)).status_code == 200


async def test_corrupt_retained_evidence_and_redis_errors_refuse_privately(
    closure_api, monkeypatch
):
    from redis.exceptions import ConnectionError as RedisConnectionError

    from app.api.v2 import portfolio_management

    api = closure_api
    root = (await create(api)).json()["id"]

    async def unavailable(*args, **kwargs):
        raise RedisConnectionError("secret redis details")

    with monkeypatch.context() as scoped:
        scoped.setattr(portfolio_management, "enforce", unavailable)
        r = await delete(api, root)
    assert r.status_code == 503 and "secret" not in r.text and r.headers["Retry-After"] == "5"
    assert (await state(api))[1] == 0
    assert (await delete(api, root)).status_code == 200
    async with api.migrator.begin() as conn:
        for table in ("portfolio_lifecycle_closures", "portfolio_closure_intents"):
            await conn.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER USER"))  # noqa: S608
            await conn.execute(
                text(f"UPDATE {table} SET confirmation_name='Corrupt' WHERE portfolio_id=:p"),  # noqa: S608
                {"p": int(root)},
            )
            await conn.execute(text(f"ALTER TABLE {table} ENABLE TRIGGER USER"))  # noqa: S608
    before = await state(api)
    r = await delete(api, root)
    assert r.status_code == 503 and r.headers["Retry-After"] == "5"
    # The global write-admission guard may refuse corrupt retained names even
    # before the route's complete proof. That earlier refusal is private too.
    assert r.json()["detail"]["code"] == "schema_unavailable"
    assert r.headers["cache-control"] == "no-store"
    assert await state(api) == before


async def test_confirmation_with_real_holdings_freezes_without_liquidation(closure_api):
    from tests.helpers import put_price

    api = closure_api
    root = (await create(api)).json()["id"]
    await put_price(api.admin, "BTC", "100", datetime.now(UTC))
    order = {
        "symbol": "BTC",
        "side": "buy",
        "quantity": "1",
        "expected_mid": "100",
        "idempotency_key": str(uuid4()),
    }
    fill = await api.client.post(f"/api/v2/portfolios/{root}/trades", json=order, headers=CSRF)
    assert fill.status_code == 201, fill.text
    async with api.migrator.connect() as conn:
        before = (
            await conn.execute(text("SELECT cash FROM accounts WHERE id=:p"), {"p": int(root)})
        ).scalar_one()
        holding = (
            await conn.execute(
                text("SELECT quantity,cost_basis FROM holdings WHERE portfolio_id=:p"),
                {"p": int(root)},
            )
        ).one()
    assert (await delete(api, root)).status_code == 200
    async with api.migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT cash FROM accounts WHERE id=:p"), {"p": int(root)})
        ).scalar_one() == before
        assert (
            await conn.execute(
                text("SELECT quantity,cost_basis FROM holdings WHERE portfolio_id=:p"),
                {"p": int(root)},
            )
        ).one() == holding
        assert (await conn.execute(text("SELECT count(*) FROM trades"))).scalar_one() == 1
    assert (
        await api.client.post(f"/api/v2/portfolios/{root}/trades", json=order, headers=CSRF)
    ).status_code == 404
