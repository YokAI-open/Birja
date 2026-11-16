"""Actual identity routers in an isolated composition; production mounting is Plan15."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.api.v2.router import api_router
from app.core.config import Settings
from app.main import create_app
from app.models.auth import AuthSession
from app.models.user import Account, User
from tests.helpers import csrf_headers, request_and_get_code, unique_email


@pytest.fixture(scope="session")
def app(settings: Settings) -> FastAPI:
    composition = create_app(settings)
    composition.include_router(api_router, prefix="/api/v2")
    return composition


async def _verify(client, outbox, email):
    code = await request_and_get_code(client, outbox, email)
    return await client.post(
        "/api/v2/auth/verify-code",
        json={"email": email, "code": code},
        headers={"X-CSRF-Token": client.cookies["bj_csrf"]},
    )


@pytest.mark.parametrize("count,closed", [(0, False), (1, False), (2, False), (1, True)])
async def test_versioned_identity_has_no_finances_and_preserves_roots(
    auth_client, outbox, engine, count, closed
):
    email = unique_email("versioned")
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as db:
        user = User(email=email)
        db.add(user)
        await db.flush()
        uid = user.id
        for i in range(count):
            db.add(
                Account(
                    user_id=uid,
                    name=f"Retained {i}",
                    cash=Decimal("4521.09") + i,
                    starting_cash=Decimal("9321.01") + i,
                    closed_at=datetime.now(UTC) if closed else None,
                )
            )
        await db.commit()

    async def snapshot():
        async with sessions() as db:
            return (
                await db.execute(
                    select(Account.__table__).where(Account.user_id == uid).order_by(Account.id)
                )
            ).all()

    before = await snapshot()
    verified = await _verify(auth_client, outbox, email)
    assert verified.status_code == 200
    assert verified.json() == {"email": email}
    assert verified.headers["cache-control"] == "no-store"
    for _ in range(2):
        me = await auth_client.get("/api/v2/me")
        assert me.status_code == 200 and me.json() == {"email": email}
        assert me.headers["cache-control"] == "no-store"
    assert await snapshot() == before


async def test_versioned_cookie_contract_and_refresh_logout(auth_client, outbox):
    email = unique_email("cookie")
    await csrf_headers(auth_client)
    before = auth_client.cookies["bj_csrf"]
    response = await _verify(auth_client, outbox, email)
    assert response.status_code == 200
    cookies = {h.split("=", 1)[0]: h.lower() for h in response.headers.get_list("set-cookie")}
    assert set(cookies) == {"bj_access", "bj_refresh", "bj_csrf"}
    assert auth_client.cookies["bj_csrf"] != before
    for cookie in cookies.values():
        assert "secure" in cookie and "samesite=strict" in cookie
    assert "httponly" in cookies["bj_access"] and "path=/api;" in cookies["bj_access"] + ";"
    assert "httponly" in cookies["bj_refresh"]
    assert "path=/api/v1/auth/refresh" in cookies["bj_refresh"]
    assert "httponly" not in cookies["bj_csrf"]
    headers = {"X-CSRF-Token": auth_client.cookies["bj_csrf"]}
    refreshed = await auth_client.post("/api/v1/auth/refresh", headers=headers)
    assert refreshed.status_code == 204
    assert (await auth_client.get("/api/v2/me")).json() == {"email": email}
    assert (await auth_client.post("/api/v1/auth/logout", headers=headers)).status_code == 204
    assert (await auth_client.get("/api/v2/me")).status_code == 401


async def test_versioned_account_switch_returns_only_current_identity(auth_client, outbox):
    for _ in range(2):
        email = unique_email("switch")
        response = await _verify(auth_client, outbox, email)
        assert response.status_code == 200 and response.json() == {"email": email}
        assert (await auth_client.get("/api/v2/me")).json() == {"email": email}


async def test_versioned_csrf_refusal_does_not_consume_code(auth_client, outbox):
    email = unique_email("csrf")
    code = await request_and_get_code(auth_client, outbox, email)
    payload = {"email": email, "code": code}
    assert (await auth_client.post("/api/v2/auth/verify-code", json=payload)).status_code == 403
    valid = await auth_client.post(
        "/api/v2/auth/verify-code",
        json=payload,
        headers={"X-CSRF-Token": auth_client.cookies["bj_csrf"]},
    )
    assert valid.status_code == 200
    reused = await auth_client.post(
        "/api/v2/auth/verify-code",
        json=payload,
        headers={"X-CSRF-Token": auth_client.cookies["bj_csrf"]},
    )
    assert reused.status_code == 400 and reused.json()["detail"]["code"] == "invalid_code"


async def test_versioned_no_unauthenticated_identity(auth_client):
    response = await auth_client.get("/api/v2/me")
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "not_authenticated"


async def test_legacy_refusal_leaves_valid_otp_and_database_untouched(
    auth_client, outbox, running_app, engine, redis_client
):
    email = unique_email("legacy")
    code = await request_and_get_code(auth_client, outbox, email)
    otp_key = "sim:otp:" + running_app.state.otp_store.email_key(email)
    before_otp = await redis_client.hgetall(otp_key)
    payload = {"email": email, "code": code}
    headers = {"X-CSRF-Token": auth_client.cookies["bj_csrf"]}
    for _ in range(2):
        refused = await auth_client.post("/api/v1/auth/verify-code", json=payload, headers=headers)
        assert refused.status_code == 409
        assert refused.json() == {"detail": {"code": "api_version_required"}}
        assert refused.headers["cache-control"] == "no-store"
        assert not refused.headers.get_list("set-cookie")
        assert "bj_access" not in auth_client.cookies
        assert "bj_refresh" not in auth_client.cookies
        assert await redis_client.hgetall(otp_key) == before_otp
    async with engine.connect() as conn:
        assert (await conn.execute(select(User.id).where(User.email == email))).first() is None
    accepted = await auth_client.post("/api/v2/auth/verify-code", json=payload, headers=headers)
    assert accepted.status_code == 200 and accepted.json() == {"email": email}
    reused = await auth_client.post(
        "/api/v2/auth/verify-code",
        json=payload,
        headers={"X-CSRF-Token": auth_client.cookies["bj_csrf"]},
    )
    assert reused.status_code == 400 and reused.json()["detail"]["code"] == "invalid_code"
    async with engine.connect() as conn:
        rows = (
            await conn.execute(select(AuthSession.id).join(User).where(User.email == email))
        ).all()
    assert len(rows) == 1


async def test_legacy_me_never_returns_or_selects_portfolio(auth_client, outbox, engine):
    email = unique_email("legacy-me")
    assert (await _verify(auth_client, outbox, email)).status_code == 200
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as db:
        uid = (await db.execute(select(User.id).where(User.email == email))).scalar_one()
        db.add(Account(user_id=uid, name="Other", cash=Decimal("37"), starting_cash=Decimal("42")))
        await db.commit()
    refused = await auth_client.get("/api/v1/me")
    assert refused.status_code == 409
    assert refused.json() == {"detail": {"code": "api_version_required"}}
    assert refused.headers["cache-control"] == "no-store"
    assert not refused.headers.get_list("set-cookie")
    assert (await auth_client.get("/api/v2/me")).json() == {"email": email}


async def test_legacy_refusal_keeps_csrf_and_authentication_checks(auth_client):
    missing = await auth_client.post(
        "/api/v1/auth/verify-code", json={"email": unique_email(), "code": "123456"}
    )
    assert missing.status_code == 403 and missing.json()["detail"]["code"] == "csrf_failed"
    unauthenticated = await auth_client.get("/api/v1/me")
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["detail"]["code"] == "not_authenticated"
