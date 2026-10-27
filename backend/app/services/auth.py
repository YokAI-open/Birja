from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import (
    REFRESH_TOKEN_TTL_SECONDS,
    InvalidToken,
    create_access_token,
    decode_access_token,
    hash_refresh_token,
    new_csrf_token,
    new_refresh_token,
)
from app.models.auth import AuthSession, RefreshToken
from app.schemas.auth import MeOut
from app.services import accounts
from app.services.otp import OtpStore
from app.services.ratelimit import enforce


class InvalidCode(Exception):
    """Wrong, reused, expired, replaced or exhausted code: all look the same."""


async def request_code(redis: Redis, otp: OtpStore, settings: Settings, email: str, ip: str) -> str:
    """Issue a one-time code. Deliberately no user lookup: the response must be
    identical whether or not the email has an account (AUTH-01). Limits are checked
    first so a refused request issues and sends nothing (AUTH-03)."""
    await enforce(
        redis,
        f"sim:rl:req:email:{otp.email_key(email)}",
        settings.rl_request_email_limit,
        settings.rl_request_email_window,
    )
    await enforce(
        redis, f"sim:rl:req:ip:{ip}", settings.rl_request_ip_limit, settings.rl_request_ip_window
    )
    await enforce(
        redis, "sim:rl:req:global", settings.rl_send_global_limit, settings.rl_send_global_window
    )
    return await otp.issue(email)


@dataclass(frozen=True)
class IssuedSession:
    access: str
    refresh: str
    csrf: str


async def start_session(db: AsyncSession, user_id: int, settings: Settings) -> IssuedSession:
    """Open a server-side session and its first refresh token. Does not commit."""
    session = AuthSession(user_id=user_id)
    db.add(session)
    await db.flush()
    raw, digest = new_refresh_token()
    db.add(
        RefreshToken(
            session_id=session.id,
            token_hash=digest,
            expires_at=datetime.now(UTC) + timedelta(seconds=REFRESH_TOKEN_TTL_SECONDS),
        )
    )
    access = create_access_token(user_id, session.id, settings.jwt_secret)
    return IssuedSession(access=access, refresh=raw, csrf=new_csrf_token())


async def verify_code(
    db: AsyncSession,
    redis: Redis,
    otp: OtpStore,
    settings: Settings,
    email: str,
    code: str,
    ip: str,
) -> tuple[MeOut, IssuedSession]:
    await enforce(
        redis,
        f"sim:rl:ver:email:{otp.email_key(email)}",
        settings.rl_verify_email_limit,
        settings.rl_verify_email_window,
    )
    await enforce(
        redis, f"sim:rl:ver:ip:{ip}", settings.rl_verify_ip_limit, settings.rl_verify_ip_window
    )
    if not await otp.verify(email, code):
        raise InvalidCode
    user_id, _ = await accounts.get_or_create_user(db, email)
    me = await accounts.get_me(db, user_id)
    issued = await start_session(db, user_id, settings)
    await db.commit()
    return me, issued


# Two tabs share one cookie jar and can both send the same refresh cookie; the
# loser must not be treated as a thief.
REFRESH_REUSE_GRACE_SECONDS = 10


class InvalidSession(Exception):
    def __init__(self, clear_cookies: bool) -> None:
        super().__init__("invalid session")
        self.clear_cookies = clear_cookies


async def rotate_session(db: AsyncSession, settings: Settings, raw_refresh: str) -> IssuedSession:
    now = datetime.now(UTC)
    row = (
        await db.execute(
            select(RefreshToken, AuthSession)
            .join(AuthSession, RefreshToken.session_id == AuthSession.id)
            .where(RefreshToken.token_hash == hash_refresh_token(raw_refresh))
            .with_for_update()
        )
    ).first()
    if row is None:
        raise InvalidSession(clear_cookies=True)
    token, session = row
    if token.expires_at <= now or session.revoked_at is not None:
        await db.rollback()
        raise InvalidSession(clear_cookies=True)
    if token.used_at is not None:
        if (now - token.used_at).total_seconds() <= REFRESH_REUSE_GRACE_SECONDS:
            await db.rollback()
            raise InvalidSession(clear_cookies=False)
        session.revoked_at = now
        await db.commit()
        raise InvalidSession(clear_cookies=True)
    token.used_at = now
    raw, digest = new_refresh_token()
    db.add(
        RefreshToken(
            session_id=session.id,
            token_hash=digest,
            expires_at=now + timedelta(seconds=REFRESH_TOKEN_TTL_SECONDS),
        )
    )
    access = create_access_token(session.user_id, session.id, settings.jwt_secret)
    await db.commit()
    return IssuedSession(access=access, refresh=raw, csrf="")


async def end_session(db: AsyncSession, settings: Settings, access_token: str | None) -> None:
    if not access_token:
        return
    try:
        claims = decode_access_token(access_token, settings.jwt_secret, verify_exp=False)
    except InvalidToken:
        return
    await db.execute(
        update(AuthSession)
        .where(
            AuthSession.id == claims.session_id,
            AuthSession.user_id == claims.user_id,
            AuthSession.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )
    await db.commit()
