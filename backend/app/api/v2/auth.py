"""Identity-only sign-in; shared OTP and session services remain authoritative."""

from fastapi import APIRouter, Depends, HTTPException, Response

from app.api.v1.auth import _RATE_LIMITED_DOC, _rate_limited, _registration_closed
from app.core.deps import ClientIpDep, DbDep, OtpStoreDep, RedisDep, SettingsDep, verify_csrf
from app.core.security import set_session_cookies
from app.schemas.auth import IdentityOut, VerifyCodeIn
from app.services import auth as auth_service
from app.services.auth import InvalidCode, RegistrationClosed
from app.services.ratelimit import RateLimited

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/verify-code",
    response_model=IdentityOut,
    summary="Sign in and return session identity",
    description="Verifies a one-time code using the existing session machinery. "
    "Returns identity only; portfolio finances require an explicit portfolio target.",
    dependencies=[Depends(verify_csrf)],
    responses=_RATE_LIMITED_DOC,
)
async def verify_code(
    body: VerifyCodeIn,
    response: Response,
    db: DbDep,
    redis: RedisDep,
    otp: OtpStoreDep,
    settings: SettingsDep,
    ip: ClientIpDep,
) -> IdentityOut:
    try:
        identity, issued = await auth_service.verify_code(
            db, redis, otp, settings, body.email, body.code, ip
        )
    except RateLimited as exc:
        raise _rate_limited(exc) from None
    except RegistrationClosed:
        raise _registration_closed() from None
    except InvalidCode:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_code",
                "message": "That code is wrong or has expired. Check it or request a new code.",
            },
            headers={"Cache-Control": "no-store"},
        ) from None
    response.headers["Cache-Control"] = "no-store"
    set_session_cookies(response, issued.access, issued.refresh, issued.csrf)
    return identity
