import hmac
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import (
    ACCESS_COOKIE,
    CSRF_COOKIE,
    CSRF_HEADER,
    InvalidToken,
    decode_access_token,
)
from app.models.auth import AuthSession
from app.models.user import User
from app.services.email import EmailSender
from app.services.otp import OtpStore


def get_settings_dep(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.sessionmaker() as session:
        yield session


def get_redis(request: Request) -> Redis:
    redis: Redis = request.app.state.redis
    return redis


def get_client_ip(request: Request) -> str:
    # Only the socket peer. uvicorn's --proxy-headers (trusting --forwarded-allow-ips
    # only) rewrites it for trusted proxies; never parse the forwarding header here.
    return request.client.host if request.client else "unknown"


def verify_csrf(request: Request) -> None:
    cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get(CSRF_HEADER)
    if not cookie or not header or not hmac.compare_digest(cookie, header):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "csrf_failed",
                "message": "Your session token is missing or out of date. "
                "Reload the page and try again.",
            },
        )


def get_otp_store(request: Request) -> OtpStore:
    store: OtpStore = request.app.state.otp_store
    return store


def get_email_sender(request: Request) -> EmailSender:
    sender: EmailSender = request.app.state.email_sender
    return sender


def _not_authenticated() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"code": "not_authenticated", "message": "Sign in to continue."},
    )


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> User:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise _not_authenticated()
    try:
        claims = decode_access_token(token, settings.jwt_secret)
    except InvalidToken:
        raise _not_authenticated() from None
    user = (
        await db.execute(
            select(User)
            .join(AuthSession, AuthSession.user_id == User.id)
            .where(
                User.id == claims.user_id,
                AuthSession.id == claims.session_id,
                AuthSession.revoked_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if user is None:
        raise _not_authenticated()
    return user


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
DbDep = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[Redis, Depends(get_redis)]
ClientIpDep = Annotated[str, Depends(get_client_ip)]
CsrfDep = Annotated[None, Depends(verify_csrf)]
OtpStoreDep = Annotated[OtpStore, Depends(get_otp_store)]
EmailSenderDep = Annotated[EmailSender, Depends(get_email_sender)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
