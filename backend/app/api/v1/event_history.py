"""Private, immutable mixed-event History endpoint."""

import re
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response

from app.core.deps import CurrentUserDep, DbDep
from app.schemas.event_history import EventHistoryPage
from app.services.event_history import InvalidCursor, list_event_history

router = APIRouter(tags=["history"])


@router.get(
    "/history",
    response_model=EventHistoryPage,
    summary="Read your trading and corporate-action history",
    description=(
        "Read stored trades, dividends, splits and corrections newest first. "
        "Every page and linked original remains scoped to your session."
    ),
)
async def event_history(
    user: CurrentUserDep,
    db: DbDep,
    response: Response,
    limit: Annotated[str, Query(description="Page size from 1 to 100")] = "25",
    cursor: Annotated[
        str | None, Query(description="Opaque continuation from the previous page")
    ] = None,
) -> EventHistoryPage:
    response.headers["Cache-Control"] = "no-store"
    if re.fullmatch(r"[1-9][0-9]{0,2}", limit) is None or int(limit) > 100:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_limit", "message": "History limit must be between 1 and 100."},
            headers={"Cache-Control": "no-store"},
        )
    try:
        return await list_event_history(db, user_id=user.id, limit=int(limit), cursor=cursor)
    except InvalidCursor:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_cursor", "message": "Invalid history cursor."},
            headers={"Cache-Control": "no-store"},
        ) from None
