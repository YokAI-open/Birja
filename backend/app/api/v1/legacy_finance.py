"""Explicit retirement of every implicit-target financial entrypoint."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.stock_trades import PrivateRoute
from app.core.deps import CurrentUserDep, verify_csrf

router = APIRouter(tags=["legacy finance"], route_class=PrivateRoute)


async def portfolio_required(user: CurrentUserDep) -> None:
    raise HTTPException(409, detail={"code": "portfolio_required"})


# Preserve authentication and CSRF checks, but never parse a financial body or
# call a financial service to infer a target. Slash variants follow FastAPI's
# normal redirect to these same refusal endpoints.
for path, methods in (
    ("/trades/quote", ["POST"]),
    ("/trades", ["POST"]),
    ("/stock-trades/quote", ["POST"]),
    ("/stock-trades", ["POST"]),
):
    router.add_api_route(
        path,
        portfolio_required,
        methods=methods,
        dependencies=[Depends(verify_csrf)],
        response_model=None,
        summary="Select an explicit portfolio before trading",
        description="Legacy financial requests refuse without executing or looking up receipts.",
    )

for path in (
    "/trades",
    "/holdings/{symbol}",
    "/stock-trades/{symbol}/context",
    "/portfolio",
    "/history",
):
    router.add_api_route(
        path,
        portfolio_required,
        methods=["GET"],
        response_model=None,
        summary="Select an explicit portfolio before reading finances",
        description="Legacy financial reads refuse without choosing or disclosing a portfolio.",
    )
