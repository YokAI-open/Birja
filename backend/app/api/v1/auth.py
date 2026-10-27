from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response

from app.core.deps import EmailSenderDep, OtpStoreDep, verify_csrf
from app.core.security import CSRF_COOKIE, new_csrf_token, set_csrf_cookie
from app.schemas.auth import CodeSentOut, RequestCodeIn
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


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
)
async def request_code(
    body: RequestCodeIn,
    background_tasks: BackgroundTasks,
    otp: OtpStoreDep,
    sender: EmailSenderDep,
) -> CodeSentOut:
    code = await auth_service.request_code(otp, body.email)
    background_tasks.add_task(sender.send_code, body.email, code)
    return CodeSentOut(status="code_sent")
