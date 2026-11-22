"""Private root-bound trade and mixed-event History adapters."""

import re
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.v1.stock_trades import PrivateRoute
from app.core.deps import DbDep, OwnedActivePortfolioDep
from app.schemas.event_history import EventHistoryPage
from app.schemas.history import HistoryPage
from app.services import event_history, history

router = APIRouter(
    prefix="/portfolios/{portfolio_id}", tags=["portfolio history"], route_class=PrivateRoute
)
Limit = Annotated[str, Query(description="Page size from 1 to 100")]
Cursor = Annotated[str | None, Query(description="Opaque continuation for this portfolio")]


def _limit(value: str) -> int:
    if re.fullmatch(r"[1-9][0-9]{0,2}", value) is None or int(value) > 100:
        raise HTTPException(
            422,
            detail={"code": "invalid_limit", "message": "History limit must be between 1 and 100."},
        )
    return int(value)


def _cursor_error() -> HTTPException:
    return HTTPException(
        422, detail={"code": "invalid_cursor", "message": "Invalid history cursor."}
    )


@router.get(
    "/history",
    response_model=HistoryPage,
    summary="Read one portfolio's executed trades",
    description="Reads immutable fills with a root-bound cursor and deterministic seek order.",
)
async def trades(
    portfolio: OwnedActivePortfolioDep, db: DbDep, limit: Limit = "25", cursor: Cursor = None
) -> HistoryPage:
    size = _limit(limit)
    try:
        return await history.list_history(db, portfolio=portfolio, limit=size, cursor=cursor)
    except history.InvalidCursor:
        raise _cursor_error() from None


@router.get(
    "/event-history",
    response_model=EventHistoryPage,
    summary="Read one portfolio's financial event history",
    description="Reads owned trades, dividends, splits, corrections and their private originals.",
)
async def events(
    portfolio: OwnedActivePortfolioDep, db: DbDep, limit: Limit = "25", cursor: Cursor = None
) -> EventHistoryPage:
    size = _limit(limit)
    try:
        return await event_history.list_event_history(
            db, portfolio=portfolio, limit=size, cursor=cursor
        )
    except event_history.InvalidCursor:
        raise _cursor_error() from None
