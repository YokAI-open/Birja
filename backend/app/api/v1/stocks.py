"""Authenticated read-only stock discovery."""

from fastapi import APIRouter, Response

from app.core.deps import CurrentUserDep, DbDep, SettingsDep
from app.schemas.stocks import StocksResponse
from app.services import stocks

router = APIRouter(tags=["stocks"])


@router.get(
    "/stocks",
    response_model=StocksResponse,
    summary="Curated US stocks and permitted IEX quotes",
    description=(
        "Twenty independently verified catalogue identities with current permitted "
        "IEX quotes and independently evaluated regular sessions. Trading is disabled."
    ),
)
async def get_stocks(
    user: CurrentUserDep, db: DbDep, settings: SettingsDep, response: Response
) -> StocksResponse:
    result = await stocks.list_stocks(db, settings)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie, Authorization"
    return result
