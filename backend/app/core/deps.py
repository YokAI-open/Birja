import hmac
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import CSRF_COOKIE, CSRF_HEADER
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


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
DbDep = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[Redis, Depends(get_redis)]
CsrfDep = Annotated[None, Depends(verify_csrf)]
OtpStoreDep = Annotated[OtpStore, Depends(get_otp_store)]
EmailSenderDep = Annotated[EmailSender, Depends(get_email_sender)]
