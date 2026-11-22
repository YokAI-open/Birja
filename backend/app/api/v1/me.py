from fastapi import APIRouter, HTTPException

from app.core.deps import CurrentUserDep

router = APIRouter(tags=["me"])


@router.get(
    "/me",
    status_code=409,
    summary="Refuse obsolete cash-bearing identity",
    description="Use /api/v2/me for identity and an explicit portfolio for finances.",
)
async def get_me(user: CurrentUserDep) -> None:
    raise HTTPException(
        status_code=409,
        detail={"code": "api_version_required"},
        headers={"Cache-Control": "no-store"},
    )
