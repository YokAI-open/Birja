from fastapi import APIRouter, Response

from app.core.deps import CurrentUserDep, DbDep
from app.schemas.auth import IdentityOut
from app.services import accounts

router = APIRouter(tags=["me"])


@router.get(
    "/me",
    response_model=IdentityOut,
    summary="Current session identity",
    description="Returns the signed-in user's email independently of portfolio ownership.",
)
async def get_me(user: CurrentUserDep, db: DbDep, response: Response) -> IdentityOut:
    response.headers["Cache-Control"] = "no-store"
    return await accounts.get_me(db, user.id)
