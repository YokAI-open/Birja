from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import Response
from pydantic import SecretStr

from app.core.security import (
    ACCESS_COOKIE,
    InvalidToken,
    clear_session_cookies,
    create_access_token,
    decode_access_token,
    hash_refresh_token,
    new_refresh_token,
    set_session_cookies,
)

SECRET = SecretStr("s" * 40)


def _claims(**over: object) -> dict[str, object]:
    now = int(datetime.now(UTC).timestamp())
    base: dict[str, object] = {
        "sub": "7",
        "sid": 9,
        "iat": now,
        "exp": now + 900,
        "iss": "yokai",
        "aud": "yokai-web",
        "typ": "access",
    }
    base.update(over)
    return {k: v for k, v in base.items() if v is not None}


def _enc(claims: dict[str, object], alg: str = "HS256", key: str = "s" * 40) -> str:
    return jwt.encode(claims, key, algorithm=alg)


def test_access_token_roundtrip() -> None:
    claims = decode_access_token(create_access_token(7, 9, SECRET), SECRET)
    assert (claims.user_id, claims.session_id) == (7, 9)


@pytest.mark.parametrize(
    "token",
    [
        _enc(_claims(), key="w" * 40),
        _enc(_claims(), alg="HS512"),
        jwt.encode(_claims(), None, algorithm="none"),
        _enc(
            _claims(
                iat=int(datetime.now(UTC).timestamp()) - 7200,
                exp=int(datetime.now(UTC).timestamp()) - 3600,
            )
        ),
        _enc(_claims(sid=None)),
        _enc(_claims(aud="other")),
        _enc(_claims(iss="other")),
        _enc(_claims(typ="refresh")),
        _enc(_claims(typ=None)),
        _enc(_claims(sub="abc")),
        "not-a-jwt",
    ],
)
def test_bad_access_tokens_rejected(token: str) -> None:
    with pytest.raises(InvalidToken):
        decode_access_token(token, SECRET)


def test_expired_token_accepted_when_expiry_not_verified() -> None:
    old = datetime.now(UTC) - timedelta(hours=1)
    token = create_access_token(7, 9, SECRET, now=old)
    with pytest.raises(InvalidToken):
        decode_access_token(token, SECRET)
    assert decode_access_token(token, SECRET, verify_exp=False).session_id == 9


def test_refresh_token_is_random_and_hashed() -> None:
    raw, digest = new_refresh_token()
    assert len(raw) >= 43
    assert len(digest) == 64 and digest != raw
    assert hash_refresh_token(raw) == digest
    assert new_refresh_token()[0] != raw


def test_set_and_clear_session_cookies() -> None:
    resp = Response()
    set_session_cookies(resp, "A", "R", "C")
    cookies = {h.split("=")[0]: h.lower() for h in resp.headers.getlist("set-cookie")}
    access, refresh, csrf = cookies[ACCESS_COOKIE], cookies["yk_refresh"], cookies["yk_csrf"]
    for c in (access, refresh, csrf):
        assert "secure" in c and "samesite=strict" in c and "max-age=2592000" in c
    assert "httponly" in access and "path=/api;" in access + ";"
    assert "httponly" in refresh and "path=/api/v1/auth/refresh" in refresh
    assert "httponly" not in csrf and "path=/;" in csrf + ";"

    cleared = Response()
    clear_session_cookies(cleared)
    heads = [h.lower() for h in cleared.headers.getlist("set-cookie")]
    assert len(heads) == 3 and all("max-age=0" in h for h in heads)
    assert any("path=/api/v1/auth/refresh" in h for h in heads)


# ---- API section -------------------------------------------------------------

import httpx  # noqa: E402
from sqlalchemy import select, text, update  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker  # noqa: E402

from app.models.auth import AuthSession, RefreshToken  # noqa: E402
from app.models.user import User  # noqa: E402
from tests.helpers import OutboxSender, csrf_headers, sign_in, unique_email  # noqa: E402


def _set_cookie_headers(resp: httpx.Response) -> dict[str, str]:
    return {h.split("=", 1)[0]: h.lower() for h in resp.headers.get_list("set-cookie")}


async def _ids(engine: AsyncEngine, email: str) -> tuple[int, int]:
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as db:
        uid = (await db.execute(select(User.id).where(User.email == email))).scalar_one()
        sid = (
            await db.execute(select(AuthSession.id).where(AuthSession.user_id == uid))
        ).scalar_one()
    return uid, sid


async def test_sign_in_sets_three_cookies_and_rotates_csrf(
    auth_client: httpx.AsyncClient, outbox: OutboxSender
) -> None:
    email = unique_email()
    await csrf_headers(auth_client)
    before = auth_client.cookies["yk_csrf"]
    resp = await sign_in(auth_client, outbox, email)

    cookies = _set_cookie_headers(resp)
    assert set(cookies) == {"yk_access", "yk_refresh", "yk_csrf"}
    assert "httponly" in cookies["yk_access"] and "path=/api;" in cookies["yk_access"] + ";"
    assert "httponly" in cookies["yk_refresh"]
    assert "path=/api/v1/auth/refresh" in cookies["yk_refresh"]
    assert "max-age=2592000" in cookies["yk_refresh"]
    assert "httponly" not in cookies["yk_csrf"]
    assert auth_client.cookies["yk_csrf"] != before
    assert resp.json() == {"email": email, "cash_usd": "10000.00000000"}


async def test_session_and_refresh_rows_store_only_hash(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, engine: AsyncEngine
) -> None:
    email = unique_email()
    resp = await sign_in(auth_client, outbox, email)
    raw = resp.headers.get_list("set-cookie")
    raw_refresh = next(h for h in raw if h.startswith("yk_refresh=")).split(";")[0].split("=", 1)[1]
    _, sid = await _ids(engine, email)

    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as db:
        session = (await db.execute(select(AuthSession).where(AuthSession.id == sid))).scalar_one()
        token = (
            await db.execute(select(RefreshToken).where(RefreshToken.session_id == sid))
        ).scalar_one()
        dump = (await db.execute(text("SELECT row_to_json(r)::text FROM refresh_tokens r"))).all()
    assert session.revoked_at is None
    assert len(token.token_hash) == 64 and token.token_hash != raw_refresh
    assert token.token_hash == hash_refresh_token(raw_refresh)
    assert all(raw_refresh not in row[0] for row in dump)


async def test_me_returns_user_and_cash(
    auth_client: httpx.AsyncClient, outbox: OutboxSender
) -> None:
    email = unique_email()
    await sign_in(auth_client, outbox, email)
    resp = await auth_client.get("/api/v1/me")
    assert resp.status_code == 200
    assert resp.json() == {"email": email, "cash_usd": "10000.00000000"}


def _assert_401(resp: httpx.Response) -> None:
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "not_authenticated"


async def test_me_without_cookie_is_401(auth_client: httpx.AsyncClient) -> None:
    _assert_401(await auth_client.get("/api/v1/me"))


async def _me_with_token(client: httpx.AsyncClient, token: str) -> httpx.Response:
    client.cookies.clear()
    return await client.get("/api/v1/me", headers={"Cookie": f"yk_access={token}"})


async def test_me_rejects_bad_tokens(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    settings,  # type: ignore[no-untyped-def]
) -> None:
    email = unique_email()
    await sign_in(auth_client, outbox, email)
    uid, sid = await _ids(engine, email)
    good = create_access_token(uid, sid, settings.jwt_secret)

    _assert_401(await _me_with_token(auth_client, good[:-3] + "abc"))
    old = datetime.now(UTC) - timedelta(hours=1)
    _assert_401(
        await _me_with_token(
            auth_client, create_access_token(uid, sid, settings.jwt_secret, now=old)
        )
    )
    _assert_401(await _me_with_token(auth_client, "garbage"))
    # sanity: the same helper accepts the good token
    assert (await _me_with_token(auth_client, good)).status_code == 200


async def test_me_rejects_revoked_session(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, engine: AsyncEngine
) -> None:
    email = unique_email()
    await sign_in(auth_client, outbox, email)
    _, sid = await _ids(engine, email)
    sessions = async_sessionmaker(engine)
    async with sessions() as db:
        await db.execute(
            update(AuthSession).where(AuthSession.id == sid).values(revoked_at=datetime.now(UTC))
        )
        await db.commit()
    _assert_401(await auth_client.get("/api/v1/me"))


async def test_me_rejects_mixed_user_and_session(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    settings,  # type: ignore[no-untyped-def]
) -> None:
    a, b = unique_email("a"), unique_email("b")
    await sign_in(auth_client, outbox, a)
    auth_client.cookies.clear()
    await sign_in(auth_client, outbox, b)
    uid_a, _ = await _ids(engine, a)
    _, sid_b = await _ids(engine, b)
    forged = create_access_token(uid_a, sid_b, settings.jwt_secret)
    _assert_401(await _me_with_token(auth_client, forged))
