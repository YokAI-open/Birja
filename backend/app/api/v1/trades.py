from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.deps import CurrentUserDep, DbDep, SettingsDep, verify_csrf
from app.schemas.trades import FillOut, HoldingOut, QuoteIn, QuoteOut, TradeIn
from app.services import trading
from app.services.trade_math import TradeRefused

router = APIRouter(tags=["trades"])

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
        detail["quote"] = QuoteOut.from_quote(exc.quote).model_dump(mode="json")
    return HTTPException(status_code=STATUS[exc.code], detail=detail)


@router.post(
    "/trades/quote",
    response_model=QuoteOut,
    dependencies=[Depends(verify_csrf)],
    summary="Preview a market order",
    description=(
        "Prices a buy (by USD or quantity) or a sell (by quantity) at the current price with "
        "the simulated spread and fee. Writes nothing."
    ),
)
async def post_quote(
    body: QuoteIn, user: CurrentUserDep, db: DbDep, settings: SettingsDep, response: Response
) -> QuoteOut:
    response.headers["Cache-Control"] = "no-store"
    try:
        q = await trading.quote(db, user_id=user.id, order=body.to_order(), settings=settings)
    except TradeRefused as exc:
        raise _refusal(exc) from None
    return QuoteOut.from_quote(q)


@router.post(
    "/trades",
    response_model=FillOut,
    status_code=201,
    dependencies=[Depends(verify_csrf)],
    summary="Execute a market order",
    description=(
        "Fills the order at the current price. 201 for a new fill; 200 with the original fill "
        "when the same idempotency key is replayed. Refused with 409 price_changed (and a fresh "
        "quote) when the price differs from expected_mid."
    ),
)
async def post_trade(
    body: TradeIn, user: CurrentUserDep, db: DbDep, settings: SettingsDep, response: Response
) -> FillOut:
    response.headers["Cache-Control"] = "no-store"
    try:
        fill, created = await trading.execute(
            db,
            user_id=user.id,
            order=body.to_order(),
            expected_mid=body.expected_mid,
            idempotency_key=body.idempotency_key,
            settings=settings,
        )
    except TradeRefused as exc:
        raise _refusal(exc) from None
    if not created:
        response.status_code = 200
    return FillOut.from_fill(fill)


@router.get(
    "/holdings/{symbol}",
    response_model=HoldingOut,
    summary="Quantity held of one coin",
    description="The signed-in user's quantity of a coin (0 when none held).",
)
async def get_holding(
    symbol: str, user: CurrentUserDep, db: DbDep, response: Response
) -> HoldingOut:
    response.headers["Cache-Control"] = "no-store"
    try:
        sym, qty = await trading.holding_quantity(db, user_id=user.id, symbol=symbol)
    except TradeRefused as exc:
        raise _refusal(exc) from None
    return HoldingOut(symbol=sym, quantity=qty)
