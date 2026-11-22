"""Private stock preview, draft context and original financial receipts."""

import logging
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import HTTPException, Path, Request, Response
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

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
