"""Private explicit-portfolio stock adapters using the existing authority."""

from fastapi import APIRouter, Depends, Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.stock_trades import PrivateRoute, Symbol, _refusal
from app.core.config import Settings
from app.core.deps import DbDep, OwnedActivePortfolioDep, RedisDep, SettingsDep, verify_csrf
from app.schemas.stock_trades import ContextOut, FillOut, QuoteIn, QuoteOut, TradeIn
from app.services import stock_trading
from app.services.portfolios import fence_owned_active_portfolios
from app.services.stock_quote_demand import request_stock_quote
from app.services.trade_math import TradeRefused

router = APIRouter(
    prefix="/portfolios/{portfolio_id}",
    tags=["portfolio stock trades"],
    route_class=PrivateRoute,
)


async def _refresh_quote(
    db: AsyncSession, redis: Redis, settings: Settings, symbol: str, reason: str
) -> bool:
    if not settings.stock_data_enabled or reason not in ("quote_unavailable", "quote_stale"):
        return False
    # The initial read and (for confirmation) any failed transaction are over
    # before the scheduler wait. The retry reauthorizes the fixed portfolio.
    await db.rollback()
    return await request_stock_quote(
        redis, symbol, account=settings.stock_data_account, server=settings.stock_data_server
    )


@router.post(
    "/stock-trades/quote",
    response_model=QuoteOut,
    dependencies=[Depends(verify_csrf)],
    summary="Preview stock in an owned portfolio",
    description="Read-only whole-share IEX ask/bid preview in the selected active portfolio.",
)
async def post_quote(
    body: QuoteIn,
    portfolio: OwnedActivePortfolioDep,
    db: DbDep,
    settings: SettingsDep,
    redis: RedisDep,
) -> QuoteOut:
    try:
        try:
            result = await stock_trading.quote(
                db, portfolio=portfolio, order=body, settings=settings
            )
        except TradeRefused as exc:
            if not await _refresh_quote(db, redis, settings, body.symbol, exc.code):
                raise
            result = await stock_trading.quote(
                db, portfolio=portfolio, order=body, settings=settings
            )
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
    redis: RedisDep,
    response: Response,
) -> FillOut:
    try:
        try:
            fill, created = await stock_trading.execute(
                db, portfolio=portfolio, order=body, settings=settings
            )
        except TradeRefused as exc:
            if not await _refresh_quote(db, redis, settings, body.symbol, exc.code):
                raise
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
    symbol: Symbol,
    portfolio: OwnedActivePortfolioDep,
    db: DbDep,
    settings: SettingsDep,
    redis: RedisDep,
) -> ContextOut:
    try:
        result = await stock_trading.context(
            db, portfolio=portfolio, symbol=symbol, settings=settings
        )
        if await _refresh_quote(db, redis, settings, symbol, result.execution_reason):
            result = await stock_trading.context(
                db, portfolio=portfolio, symbol=symbol, settings=settings
            )
    except TradeRefused as exc:
        await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
        raise _refusal(exc) from None
    await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
    return result
