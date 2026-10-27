import hashlib
import hmac
import secrets

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
