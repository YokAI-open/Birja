from app.services.otp import OtpStore


async def request_code(otp: OtpStore, email: str) -> str:
    """Issue a one-time code. Deliberately no user lookup: the response must be
    identical whether or not the email has an account (AUTH-01)."""
    return await otp.issue(email)
