from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import MeOut
from app.services import accounts
from app.services.otp import OtpStore


class InvalidCode(Exception):
    """Wrong, reused, expired, replaced or exhausted code: all look the same."""


async def request_code(otp: OtpStore, email: str) -> str:
    """Issue a one-time code. Deliberately no user lookup: the response must be
    identical whether or not the email has an account (AUTH-01)."""
    return await otp.issue(email)


async def verify_code(db: AsyncSession, otp: OtpStore, email: str, code: str) -> MeOut:
    if not await otp.verify(email, code):
        raise InvalidCode
    user_id, _ = await accounts.get_or_create_user(db, email)
    me = await accounts.get_me(db, user_id)
    await db.commit()
    return me
