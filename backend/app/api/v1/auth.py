from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response

from app.core.deps import (
    ClientIpDep,
    DbDep,
    EmailSenderDep,
    OtpStoreDep,
    RedisDep,
    SettingsDep,
    verify_csrf,
)
from app.core.security import CSRF_COOKIE, new_csrf_token, set_csrf_cookie, set_session_cookies
from app.schemas.auth import CodeSentOut, MeOut, RequestCodeIn, VerifyCodeIn
from app.services import auth as auth_service
from app.services.auth import InvalidCode
from app.services.ratelimit import RateLimited

router = APIRouter(prefix="/auth", tags=["auth"])

_RATE_LIMITED_DOC: dict[int | str, dict[str, str]] = {
    429: {"description": "Rate limited; see the Retry-After header (seconds)."}
}


def _rate_limited(exc: RateLimited) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail={"code": "rate_limited", "message": "Too many requests. Try again later."},
        headers={"Retry-After": str(exc.retry_after)},
    )


@router.get(
    "/csrf",
    status_code=204,
    response_class=Response,
    summary="Get a CSRF token cookie",
    description="Sets the yk_csrf cookie if the client does not have one yet.",
)
async def get_csrf(request: Request) -> Response:
    response = Response(status_code=204)
    if CSRF_COOKIE not in request.cookies:
        set_csrf_cookie(response, new_csrf_token())
    return response


@router.post(
    "/request-code",
    status_code=202,
    response_model=CodeSentOut,
    summary="Email a sign-in code",
    description="Sends a one-time code to the email. The response is identical "
    "for every email, whether or not it has an account.",
    dependencies=[Depends(verify_csrf)],
    responses=_RATE_LIMITED_DOC,
)
async def request_code(
    body: RequestCodeIn,
    background_tasks: BackgroundTasks,
    redis: RedisDep,
    otp: OtpStoreDep,
    settings: SettingsDep,
    sender: EmailSenderDep,
    ip: ClientIpDep,
) -> CodeSentOut:
    try:
        code = await auth_service.request_code(redis, otp, settings, body.email, ip)
    except RateLimited as exc:
        raise _rate_limited(exc) from None
    background_tasks.add_task(sender.send_code, body.email, code)
    return CodeSentOut(status="code_sent")


@router.post(
    "/verify-code",
    status_code=200,
    response_model=MeOut,
    summary="Sign in with a code",
    description="Verifies the emailed code. Every failure (wrong, reused, expired, "
    "replaced, too many attempts) returns the same 400. The first success creates "
    "the user and their $10,000.00 account.",
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
) -> MeOut:
    try:
        me, issued = await auth_service.verify_code(
            db, redis, otp, settings, body.email, body.code, ip
        )
    except RateLimited as exc:
        raise _rate_limited(exc) from None
    except InvalidCode:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_code",
                "message": "That code is wrong or has expired. Check it or request a new code.",
            },
        ) from None
    set_session_cookies(response, issued.access, issued.refresh, issued.csrf)
    return me
