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
