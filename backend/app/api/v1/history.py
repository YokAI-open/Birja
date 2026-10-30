import re
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response

from app.core.deps import CurrentUserDep, DbDep
from app.schemas.history import HistoryPage
from app.services.history import InvalidCursor, list_history

router = APIRouter(tags=["trades"])


@router.get(
    "/trades",
    response_model=HistoryPage,
    summary="Read your executed trades",
    description=(
        "Read stored fills newest first using an opaque cursor. "
        "Every seek remains scoped to your session."
    ),
)
async def history(
    user: CurrentUserDep,
    db: DbDep,
    response: Response,
    limit: Annotated[str, Query(description="Page size from 1 to 100")] = "25",
    cursor: Annotated[
        str | None, Query(description="Opaque continuation from the previous page")
    ] = None,
) -> HistoryPage:
    response.headers["Cache-Control"] = "no-store"
    if re.fullmatch(r"[1-9][0-9]{0,2}", limit) is None or int(limit) > 100:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_limit", "message": "History limit must be between 1 and 100."},
        )
    try:
        return await list_history(db, user_id=user.id, limit=int(limit), cursor=cursor)
    except InvalidCursor:
        raise HTTPException(
            status_code=422, detail={"code": "invalid_cursor", "message": "Invalid history cursor."}
        ) from None
