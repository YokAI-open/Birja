from fastapi import APIRouter

from app.core.deps import CurrentUserDep, DbDep
from app.schemas.auth import MeOut
from app.services import accounts

router = APIRouter(tags=["me"])


@router.get(
    "/me",
    response_model=MeOut,
    summary="Current user and cash",
    description="Returns the signed-in user's email and cash balance.",
)
async def get_me(user: CurrentUserDep, db: DbDep) -> MeOut:
    return await accounts.get_me(db, user.id)
