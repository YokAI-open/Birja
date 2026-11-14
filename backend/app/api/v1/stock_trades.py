"""Private stock preview, draft context and original financial receipts."""

import logging
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.core.deps import CurrentUserDep, DbDep, SettingsDep, verify_csrf
from app.schemas.stock_trades import ContextOut, FillOut, QuoteIn, QuoteOut, TradeIn
from app.services import stock_trading
from app.services.trade_math import TradeRefused

logger = logging.getLogger(__name__)
PRIVATE = {"Cache-Control": "no-store", "Vary": "Cookie, Authorization"}


class PrivateRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()

        async def private(request: Request) -> Response:
            try:
                response = await original(request)
            except StarletteHTTPException as exc:
                exc.headers = {**(exc.headers or {}), **PRIVATE}
                raise
            except RequestValidationError as exc:
                response = await request_validation_exception_handler(request, exc)
            except Exception as exc:
                # A response failure can follow commit. Never imply no fill or
                # expose SQL/provider/credential details; retry the ORIGINAL key.
                logger.error("stock request failed type=%s", type(exc).__name__)
                response = JSONResponse(
                    status_code=500,
                    content={
                        "detail": {
                            "code": "service_unavailable",
                            "message": "Order result unavailable. Check the original order again.",
                        }
                    },
                )
            response.headers.update(PRIVATE)
            return response

        return private


router = APIRouter(tags=["stock trades"], route_class=PrivateRoute)
Symbol = Annotated[str, Path(pattern=r"^[A-Z][A-Z0-9.\-]{0,9}$", max_length=10)]
RANGE_CODES = frozenset(
    {"invalid_quantity", "insufficient_cash", "insufficient_holding", "numeric_range"}
)
UNAVAILABLE_CODES = frozenset(
    {
        "permission_unavailable",
        "action_unavailable",
        "units_changed",
        "halted",
        "frozen",
        "status_unavailable",
        "session_unavailable",
        "market_closed",
        "quote_unavailable",
        "quote_stale",
        "receipt_unavailable",
        "idempotency_conflict",
    }
)


def _refusal(exc: TradeRefused) -> HTTPException:
    if isinstance(exc, stock_trading.PriceChanged):
        return HTTPException(409, detail=exc.detail.model_dump(mode="json"), headers=PRIVATE)
    if exc.code in RANGE_CODES:
        status = 422
    elif exc.code in UNAVAILABLE_CODES:
        status = 409
    else:
        # Unknown domain outcomes must not be presented as known no-fill codes.
        return HTTPException(500, detail={"code": "service_unavailable"}, headers=PRIVATE)
    return HTTPException(status, detail={"code": exc.code}, headers=PRIVATE)


@router.post(
    "/stock-trades/quote",
    response_model=QuoteOut,
    dependencies=[Depends(verify_csrf)],
    summary="Preview a whole-share stock order",
    description=(
        "Read-only IEX ask/bid preview for simulated execution, with zero stock commission or "
        "regulatory fees. No order is queued. "
    ),
)
async def post_quote(
    body: QuoteIn, user: CurrentUserDep, db: DbDep, settings: SettingsDep
) -> QuoteOut:
    try:
        return await stock_trading.quote(db, user_id=user.id, order=body, settings=settings)
    except TradeRefused as exc:
        raise _refusal(exc) from None


@router.post(
    "/stock-trades",
    response_model=FillOut,
    status_code=201,
    dependencies=[Depends(verify_csrf)],
    summary="Confirm a whole-share stock order",
    description=(
        "Simulated IEX execution with shared virtual cash and immediately reusable sale "
        "proceeds. Returns 201 for a new fill or 200 for its immutable original receipt. A "
        "changed selected price requires a replacement preview and explicit confirmation. "
    ),
)
async def post_trade(
    body: TradeIn, user: CurrentUserDep, db: DbDep, settings: SettingsDep, response: Response
) -> FillOut:
    try:
        fill, created = await stock_trading.execute(
            db, user_id=user.id, order=body, settings=settings
        )
    except TradeRefused as exc:
        raise _refusal(exc) from None
    if not created:
        response.status_code = 200
    return fill


@router.get(
    "/stock-trades/{symbol}/context",
    response_model=ContextOut,
    summary="Read the stock draft context",
    description=(
        "Own cash and whole-share holding, server-calculated draft quantity and independently "
        "verified market status. IEX is one venue, not consolidated US prices; values do not "
        "authorize a fill. "
    ),
)
async def get_context(
    symbol: Symbol, user: CurrentUserDep, db: DbDep, settings: SettingsDep
) -> ContextOut:
    try:
        return await stock_trading.context(db, user_id=user.id, symbol=symbol, settings=settings)
    except TradeRefused as exc:
        raise _refusal(exc) from None
