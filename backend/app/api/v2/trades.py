"""Explicit owned-portfolio crypto adapters; no implicit financial target."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response

from app.api.v1.stock_trades import PrivateRoute
from app.core.deps import DbDep, OwnedActivePortfolioDep, SettingsDep, verify_csrf
from app.schemas.trades import (
    PortfolioFillOut,
    PortfolioHoldingOut,
    PortfolioQuoteOut,
    QuoteIn,
    TradeIn,
)
from app.services import trading
from app.services.portfolios import fence_owned_active_portfolios
from app.services.trade_math import TradeRefused

router = APIRouter(
    prefix="/portfolios/{portfolio_id}", tags=["portfolio crypto trades"], route_class=PrivateRoute
)
STATUS = {
    "unknown_coin": 404,
    "stale_price": 409,
    "price_changed": 409,
    "idempotency_conflict": 409,
    "below_minimum": 422,
    "insufficient_cash": 422,
    "insufficient_quantity": 422,
    "order_too_large": 422,
    "invalid_order": 422,
}


def _refusal(exc: TradeRefused) -> HTTPException:
    detail: dict[str, Any] = {"code": exc.code, "message": exc.message}
    if isinstance(exc, trading.PriceChanged):
        detail["quote"] = PortfolioQuoteOut.from_quote(exc.quote).model_dump(mode="json")
    return HTTPException(status_code=STATUS[exc.code], detail=detail)


@router.post(
    "/trades/quote",
    response_model=PortfolioQuoteOut,
    dependencies=[Depends(verify_csrf)],
    summary="Preview crypto in an owned portfolio",
    description="Prices an order without mutation in the explicitly selected active portfolio.",
)
async def post_quote(
    body: QuoteIn, portfolio: OwnedActivePortfolioDep, db: DbDep, settings: SettingsDep
) -> PortfolioQuoteOut:
    try:
        quote = await trading.quote(
            db, portfolio=portfolio, order=body.to_order(), settings=settings
        )
    except TradeRefused as exc:
        await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
        raise _refusal(exc) from None
    await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
    return PortfolioQuoteOut.from_quote(quote)


@router.post(
    "/trades",
    response_model=PortfolioFillOut,
    status_code=201,
    dependencies=[Depends(verify_csrf)],
    summary="Execute crypto in an owned portfolio",
    description="Returns 201 for a fill or 200 for its original portfolio receipt on safe retry.",
)
async def post_trade(
    body: TradeIn,
    portfolio: OwnedActivePortfolioDep,
    db: DbDep,
    settings: SettingsDep,
    response: Response,
) -> PortfolioFillOut:
    try:
        fill, created = await trading.execute(
            db,
            portfolio=portfolio,
            order=body.to_order(),
            expected_mid=body.expected_mid,
            idempotency_key=body.idempotency_key,
            settings=settings,
        )
    except TradeRefused as exc:
        await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
        raise _refusal(exc) from None
    await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
    if not created:
        response.status_code = 200
    return PortfolioFillOut.from_fill(fill)


@router.get(
    "/holdings/{symbol}",
    response_model=PortfolioHoldingOut,
    summary="Read a portfolio's crypto quantity",
    description="Reads only the explicitly selected active portfolio, never another strategy.",
)
async def get_holding(
    symbol: str, portfolio: OwnedActivePortfolioDep, db: DbDep
) -> PortfolioHoldingOut:
    try:
        sym, quantity = await trading.holding_quantity(db, portfolio=portfolio, symbol=symbol)
    except TradeRefused as exc:
        await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
        raise _refusal(exc) from None
    await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
    return PortfolioHoldingOut(portfolio_id=portfolio.portfolio_id, symbol=sym, quantity=quantity)
