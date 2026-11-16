"""Private metadata discovery and explicitly owned portfolio statements."""

from fastapi import APIRouter

from app.api.v1.stock_trades import PrivateRoute
from app.core.deps import CurrentUserDep, DbDep, OwnedActivePortfolioDep, SettingsDep
from app.schemas.portfolio import PortfolioOut
from app.schemas.portfolios import PortfolioSummary
from app.services.portfolio import get_portfolio
from app.services.portfolios import list_active_portfolios

router = APIRouter(prefix="/portfolios", tags=["portfolios"], route_class=PrivateRoute)


@router.get(
    "",
    response_model=list[PortfolioSummary],
    summary="Discover your active portfolio identities",
    description="Returns owned active IDs and names in stable order, without funding or totals.",
)
async def portfolios(user: CurrentUserDep, db: DbDep) -> list[PortfolioSummary]:
    return await list_active_portfolios(db, user)


@router.get(
    "/{portfolio_id}",
    response_model=PortfolioOut,
    summary="Read one owned portfolio statement",
    description="Values the selected active portfolio against its original stored starting cash.",
)
async def portfolio(
    portfolio: OwnedActivePortfolioDep, db: DbDep, settings: SettingsDep
) -> PortfolioOut:
    return PortfolioOut.from_value(await get_portfolio(db, portfolio=portfolio, settings=settings))
