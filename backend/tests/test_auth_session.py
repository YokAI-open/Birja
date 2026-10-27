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
        "iss": "birja",
        "aud": "birja-web",
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
    access, refresh, csrf = cookies[ACCESS_COOKIE], cookies["bj_refresh"], cookies["bj_csrf"]
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
    before = auth_client.cookies["bj_csrf"]
    resp = await sign_in(auth_client, outbox, email)

    cookies = _set_cookie_headers(resp)
    assert set(cookies) == {"bj_access", "bj_refresh", "bj_csrf"}
    assert "httponly" in cookies["bj_access"] and "path=/api;" in cookies["bj_access"] + ";"
    assert "httponly" in cookies["bj_refresh"]
    assert "path=/api/v1/auth/refresh" in cookies["bj_refresh"]
    assert "max-age=2592000" in cookies["bj_refresh"]
    assert "httponly" not in cookies["bj_csrf"]
    assert auth_client.cookies["bj_csrf"] != before
    assert resp.json() == {"email": email, "cash_usd": "10000.00000000"}


async def test_session_and_refresh_rows_store_only_hash(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, engine: AsyncEngine
) -> None:
    email = unique_email()
    resp = await sign_in(auth_client, outbox, email)
    raw = resp.headers.get_list("set-cookie")
    raw_refresh = next(h for h in raw if h.startswith("bj_refresh=")).split(";")[0].split("=", 1)[1]
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
    return await client.get("/api/v1/me", headers={"Cookie": f"bj_access={token}"})


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


# ---- refresh / logout section -----------------------------------------------

import asyncio  # noqa: E402


def _cookie(resp: httpx.Response, name: str) -> str:
    for h in resp.headers.get_list("set-cookie"):
        if h.startswith(f"{name}="):
            return h.split(";")[0].split("=", 1)[1]
    raise AssertionError(f"no {name} cookie")


async def _refresh(client: httpx.AsyncClient, refresh_token: str | None = None) -> httpx.Response:
    if "bj_csrf" not in client.cookies:
        await client.get("/api/v1/auth/csrf")
    csrf = client.cookies["bj_csrf"]
    headers = {"X-CSRF-Token": csrf}
    if refresh_token is not None:
        headers["Cookie"] = f"bj_csrf={csrf}; bj_refresh={refresh_token}"
        saved = list(client.cookies.jar)
        client.cookies.clear()
        try:
            return await client.post("/api/v1/auth/refresh", headers=headers)
        finally:
            for c in saved:
                client.cookies.jar.set_cookie(c)
    return await client.post("/api/v1/auth/refresh", headers=headers)


async def _signed_in(client: httpx.AsyncClient, outbox: OutboxSender) -> tuple[str, str, str]:
    email = unique_email()
    resp = await sign_in(client, outbox, email)
    return email, _cookie(resp, "bj_refresh"), _cookie(resp, "bj_access")


async def _db_update(engine: AsyncEngine, stmt) -> None:  # type: ignore[no-untyped-def]
    sessions = async_sessionmaker(engine)
    async with sessions() as db:
        await db.execute(stmt)
        await db.commit()


async def test_refresh_rotates_tokens(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, engine: AsyncEngine
) -> None:
    email, old_refresh, _ = await _signed_in(auth_client, outbox)
    _, sid = await _ids(engine, email)
    resp = await _refresh(auth_client)
    assert resp.status_code == 204
    cookies = _set_cookie_headers(resp)
    assert set(cookies) == {"bj_access", "bj_refresh", "bj_csrf"}
    assert "httponly" in cookies["bj_access"] and "httponly" in cookies["bj_refresh"]
    assert "path=/api/v1/auth/refresh" in cookies["bj_refresh"]
    assert _cookie(resp, "bj_refresh") != old_refresh
    assert (await auth_client.get("/api/v1/me")).status_code == 200

    sessions = async_sessionmaker(engine)
    async with sessions() as db:
        rows = (
            (
                await db.execute(
                    select(RefreshToken)
                    .where(RefreshToken.session_id == sid)
                    .order_by(RefreshToken.id)
                )
            )
            .scalars()
            .all()
        )
    assert len(rows) == 2
    assert rows[0].used_at is not None and rows[1].used_at is None
    assert rows[1].expires_at - datetime.now(UTC) > timedelta(days=29)


async def test_refresh_reuse_within_grace_keeps_newest_token_valid(
    auth_client: httpx.AsyncClient, outbox: OutboxSender
) -> None:
    _, old_refresh, _ = await _signed_in(auth_client, outbox)
    first = await _refresh(auth_client)
    newest = _cookie(first, "bj_refresh")
    _assert_401(await _refresh(auth_client, old_refresh))
    assert (await _refresh(auth_client, newest)).status_code == 204


async def test_refresh_reuse_after_grace_revokes_session(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, engine: AsyncEngine
) -> None:
    email, old_refresh, _ = await _signed_in(auth_client, outbox)
    _, sid = await _ids(engine, email)
    first = await _refresh(auth_client)
    newest = _cookie(first, "bj_refresh")
    access = _cookie(first, "bj_access")
    await _db_update(
        engine,
        update(RefreshToken)
        .where(RefreshToken.token_hash == hash_refresh_token(old_refresh))
        .values(used_at=datetime.now(UTC) - timedelta(minutes=1)),
    )
    resp = await _refresh(auth_client, old_refresh)
    _assert_401(resp)
    assert "max-age=0" in _set_cookie_headers(resp)["bj_refresh"]
    sessions = async_sessionmaker(engine)
    async with sessions() as db:
        revoked = (
            await db.execute(select(AuthSession.revoked_at).where(AuthSession.id == sid))
        ).scalar_one()
    assert revoked is not None
    _assert_401(await _refresh(auth_client, newest))
    _assert_401(await _me_with_token(auth_client, access))


async def test_concurrent_refresh_one_wins_without_revoke(
    running_app,
    outbox: OutboxSender,
    engine: AsyncEngine,  # type: ignore[no-untyped-def]
) -> None:
    async def make() -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=running_app), base_url="https://test"
        )

    async with await make() as a, await make() as b:
        email, refresh_token, _ = await _signed_in(a, outbox)
        csrf = a.cookies["bj_csrf"]
        headers = {
            "X-CSRF-Token": csrf,
            "Cookie": f"bj_csrf={csrf}; bj_refresh={refresh_token}",
        }
        r1, r2 = await asyncio.gather(
            a.post("/api/v1/auth/refresh", headers=headers),
            b.post("/api/v1/auth/refresh", headers=headers),
        )
    assert sorted([r1.status_code, r2.status_code]) == [204, 401]
    _, sid = await _ids(engine, email)
    sessions = async_sessionmaker(engine)
    async with sessions() as db:
        revoked = (
            await db.execute(select(AuthSession.revoked_at).where(AuthSession.id == sid))
        ).scalar_one()
    assert revoked is None


async def test_refresh_without_cookie_or_unknown_token_is_401(
    auth_client: httpx.AsyncClient,
) -> None:
    headers = await csrf_headers(auth_client)
    resp = await auth_client.post("/api/v1/auth/refresh", headers=headers)
    _assert_401(resp)
    assert "max-age=0" in _set_cookie_headers(resp)["bj_refresh"]
    _assert_401(await _refresh(auth_client, "not-a-real-token"))


async def test_refresh_expired_or_revoked_session_is_401(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, engine: AsyncEngine
) -> None:
    email, refresh_token, _ = await _signed_in(auth_client, outbox)
    _, sid = await _ids(engine, email)
    await _db_update(
        engine,
        update(RefreshToken)
        .where(RefreshToken.session_id == sid)
        .values(expires_at=datetime.now(UTC) - timedelta(seconds=1)),
    )
    resp = await _refresh(auth_client, refresh_token)
    _assert_401(resp)
    assert "max-age=0" in _set_cookie_headers(resp)["bj_refresh"]

    email2, refresh2, _ = await _signed_in(auth_client, outbox)
    _, sid2 = await _ids(engine, email2)
    await _db_update(
        engine,
        update(AuthSession).where(AuthSession.id == sid2).values(revoked_at=datetime.now(UTC)),
    )
    _assert_401(await _refresh(auth_client, refresh2))


async def test_refresh_and_logout_require_csrf(
    auth_client: httpx.AsyncClient, outbox: OutboxSender
) -> None:
    await _signed_in(auth_client, outbox)
    assert (await auth_client.post("/api/v1/auth/refresh")).status_code == 403
    assert (await auth_client.post("/api/v1/auth/logout")).status_code == 403


async def test_logout_revokes_session_and_clears_cookies(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, engine: AsyncEngine
) -> None:
    email, refresh_token, access = await _signed_in(auth_client, outbox)
    _, sid = await _ids(engine, email)
    headers = {"X-CSRF-Token": auth_client.cookies["bj_csrf"]}
    resp = await auth_client.post("/api/v1/auth/logout", headers=headers)
    assert resp.status_code == 204
    cookies = _set_cookie_headers(resp)
    assert set(cookies) == {"bj_access", "bj_refresh", "bj_csrf"}
    assert all("max-age=0" in v for v in cookies.values())
    assert "path=/api;" in cookies["bj_access"] + ";"
    assert "path=/api/v1/auth/refresh" in cookies["bj_refresh"]
    assert "path=/;" in cookies["bj_csrf"] + ";"
    sessions = async_sessionmaker(engine)
    async with sessions() as db:
        revoked = (
            await db.execute(select(AuthSession.revoked_at).where(AuthSession.id == sid))
        ).scalar_one()
    assert revoked is not None
    _assert_401(await _me_with_token(auth_client, access))
    _assert_401(await _refresh(auth_client, refresh_token))


async def test_logout_with_expired_access_token_still_revokes(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    engine: AsyncEngine,
    settings,  # type: ignore[no-untyped-def]
) -> None:
    email, _, _ = await _signed_in(auth_client, outbox)
    uid, sid = await _ids(engine, email)
    old = datetime.now(UTC) - timedelta(hours=2)
    expired = create_access_token(uid, sid, settings.jwt_secret, now=old)
    csrf = auth_client.cookies["bj_csrf"]
    resp = await auth_client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": csrf, "Cookie": f"bj_csrf={csrf}; bj_access={expired}"},
    )
    assert resp.status_code == 204
    sessions = async_sessionmaker(engine)
    async with sessions() as db:
        revoked = (
            await db.execute(select(AuthSession.revoked_at).where(AuthSession.id == sid))
        ).scalar_one()
    assert revoked is not None


async def test_logout_without_or_with_bad_token_revokes_nothing(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, engine: AsyncEngine
) -> None:
    email, _, access = await _signed_in(auth_client, outbox)
    _, sid = await _ids(engine, email)
    csrf = auth_client.cookies["bj_csrf"]
    for cookie in (f"bj_csrf={csrf}", f"bj_csrf={csrf}; bj_access={access[:-3]}abc"):
        resp = await auth_client.post(
            "/api/v1/auth/logout", headers={"X-CSRF-Token": csrf, "Cookie": cookie}
        )
        assert resp.status_code == 204
        assert "max-age=0" in _set_cookie_headers(resp)["bj_access"]
    sessions = async_sessionmaker(engine)
    async with sessions() as db:
        revoked = (
            await db.execute(select(AuthSession.revoked_at).where(AuthSession.id == sid))
        ).scalar_one()
    assert revoked is None


async def test_sign_in_after_logout_keeps_cash_at_10000(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, engine: AsyncEngine
) -> None:
    email, _, _ = await _signed_in(auth_client, outbox)
    headers = {"X-CSRF-Token": auth_client.cookies["bj_csrf"]}
    assert (await auth_client.post("/api/v1/auth/logout", headers=headers)).status_code == 204
    resp = await sign_in(auth_client, outbox, email)
    assert resp.json() == {"email": email, "cash_usd": "10000.00000000"}
    async with engine.connect() as conn:
        n = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM accounts a JOIN users u ON u.id=a.user_id "
                    "WHERE u.email=:e"
                ),
                {"e": email},
            )
        ).scalar_one()
    assert n == 1
