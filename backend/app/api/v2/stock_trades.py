"""Private explicit-portfolio stock adapters using the existing authority."""

from fastapi import APIRouter, Depends, Response

from app.api.v1.stock_trades import PrivateRoute, Symbol, _refusal
from app.core.deps import DbDep, OwnedActivePortfolioDep, SettingsDep, verify_csrf
from app.schemas.stock_trades import ContextOut, FillOut, QuoteIn, QuoteOut, TradeIn
from app.services import stock_trading
from app.services.portfolios import fence_owned_active_portfolios
from app.services.trade_math import TradeRefused

router = APIRouter(
    prefix="/portfolios/{portfolio_id}",
    tags=["portfolio stock trades"],
    route_class=PrivateRoute,
)


@router.post(
    "/stock-trades/quote",
    response_model=QuoteOut,
    dependencies=[Depends(verify_csrf)],
    summary="Preview stock in an owned portfolio",
    description="Read-only whole-share IEX ask/bid preview in the selected active portfolio.",
)
async def post_quote(
    body: QuoteIn, portfolio: OwnedActivePortfolioDep, db: DbDep, settings: SettingsDep
) -> QuoteOut:
    try:
        result = await stock_trading.quote(db, portfolio=portfolio, order=body, settings=settings)
    except TradeRefused as exc:
        await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
        raise _refusal(exc) from None
    await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
    return result


@router.post(
    "/stock-trades",
    response_model=FillOut,
    status_code=201,
    dependencies=[Depends(verify_csrf)],
    summary="Confirm stock in an owned portfolio",
    description=(
        "Simulated whole-share execution with zero stock fees. Returns 201 for a new fill or "
        "200 for its immutable original active-portfolio receipt. No order is retargeted."
    ),
)
async def post_trade(
    body: TradeIn,
    portfolio: OwnedActivePortfolioDep,
    db: DbDep,
    settings: SettingsDep,
    response: Response,
) -> FillOut:
    try:
        fill, created = await stock_trading.execute(
            db, portfolio=portfolio, order=body, settings=settings
        )
    except TradeRefused as exc:
        await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
        raise _refusal(exc) from None
    await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
    if not created:
        response.status_code = 200
    return fill


@router.get(
    "/stock-trades/{symbol}/context",
    response_model=ContextOut,
    summary="Read a portfolio's stock draft context",
    description=(
        "Selected portfolio cash and holdings with current session and IEX venue evidence. "
        "Context alone never authorizes a fill."
    ),
)
async def get_context(
    symbol: Symbol, portfolio: OwnedActivePortfolioDep, db: DbDep, settings: SettingsDep
) -> ContextOut:
    try:
        result = await stock_trading.context(
            db, portfolio=portfolio, symbol=symbol, settings=settings
        )
    except TradeRefused as exc:
        await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
        raise _refusal(exc) from None
    await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
    return result
