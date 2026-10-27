import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

import jwt
from fastapi import Response
from pydantic import SecretStr


def hmac_hex(secret: SecretStr, message: str) -> str:
    """HMAC-SHA256 hexdigest of message, keyed with the server secret."""
    return hmac.new(
        secret.get_secret_value().encode(), message.encode(), hashlib.sha256
    ).hexdigest()


CSRF_COOKIE = "yk_csrf"
CSRF_HEADER = "X-CSRF-Token"
COOKIE_MAX_AGE_30D = 2592000


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response: Response, token: str) -> None:
    # Readable by JS on purpose (double-submit); Secure is accepted on localhost.
    response.set_cookie(
        CSRF_COOKIE,
        token,
        max_age=COOKIE_MAX_AGE_30D,
        path="/",
        secure=True,
        httponly=False,
        samesite="strict",
    )


ACCESS_COOKIE = "yk_access"
ACCESS_COOKIE_PATH = "/api"
REFRESH_COOKIE = "yk_refresh"
REFRESH_COOKIE_PATH = "/api/v1/auth/refresh"
ACCESS_TOKEN_TTL_SECONDS = 900
REFRESH_TOKEN_TTL_SECONDS = 2592000

_JWT_ISSUER = "yokai"
_JWT_AUDIENCE = "yokai-web"


class InvalidToken(Exception):
    """The access token is missing a claim, expired, forged or otherwise unusable."""


@dataclass(frozen=True)
class AccessClaims:
    user_id: int
    session_id: int


def create_access_token(
    user_id: int, session_id: int, secret: SecretStr, now: datetime | None = None
) -> str:
    issued = int((now or datetime.now(UTC)).timestamp())
    claims = {
        "sub": str(user_id),
        "sid": session_id,
        "iat": issued,
        "exp": issued + ACCESS_TOKEN_TTL_SECONDS,
        "iss": _JWT_ISSUER,
        "aud": _JWT_AUDIENCE,
        "typ": "access",
    }
    return jwt.encode(claims, secret.get_secret_value(), algorithm="HS256")


def decode_access_token(token: str, secret: SecretStr, *, verify_exp: bool = True) -> AccessClaims:
    try:
        payload = jwt.decode(
            token,
            secret.get_secret_value(),
            algorithms=["HS256"],
            audience=_JWT_AUDIENCE,
            issuer=_JWT_ISSUER,
            options={"require": ["exp", "iat", "sub", "sid"], "verify_exp": verify_exp},
        )
        if payload["typ"] != "access":
            raise InvalidToken
        return AccessClaims(user_id=int(payload["sub"]), session_id=int(payload["sid"]))
    except jwt.PyJWTError, KeyError, ValueError, TypeError:
        raise InvalidToken from None


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def new_refresh_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)
    return raw, hash_refresh_token(raw)


def set_session_cookies(response: Response, access: str, refresh: str, csrf: str) -> None:
    # The access cookie outlives the 15-minute JWT on purpose: sign-out (02-07)
    # must still receive it after expiry to find and revoke the session.
    response.set_cookie(
        ACCESS_COOKIE,
        access,
        max_age=REFRESH_TOKEN_TTL_SECONDS,
        path=ACCESS_COOKIE_PATH,
        secure=True,
        httponly=True,
        samesite="strict",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh,
        max_age=REFRESH_TOKEN_TTL_SECONDS,
        path=REFRESH_COOKIE_PATH,
        secure=True,
        httponly=True,
        samesite="strict",
    )
    set_csrf_cookie(response, csrf)


def clear_session_cookies(response: Response) -> None:
    for name, path, httponly in (
        (ACCESS_COOKIE, ACCESS_COOKIE_PATH, True),
        (REFRESH_COOKIE, REFRESH_COOKIE_PATH, True),
        (CSRF_COOKIE, "/", False),
    ):
        response.delete_cookie(name, path=path, secure=True, httponly=httponly, samesite="strict")
