from fastapi import APIRouter, Response

from app.core.deps import CurrentUserDep, DbDep, SettingsDep
from app.schemas.portfolio import PortfolioOut
from app.services.portfolio import get_portfolio

router = APIRouter(tags=["portfolio"])


@router.get(
    "/portfolio",
    response_model=PortfolioOut,
    summary="Read your portfolio",
    description=(
        "Read cash, positive holdings and mid-price performance from one financial snapshot."
    ),
)
async def portfolio(
    user: CurrentUserDep, db: DbDep, settings: SettingsDep, response: Response
) -> PortfolioOut:
    response.headers["Cache-Control"] = "no-store"
    return PortfolioOut.from_value(await get_portfolio(db, user_id=user.id, settings=settings))
