"""Private, selected-instrument chart reads. Upstream collection is scheduler-only."""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.stock_trades import PrivateRoute
from app.core.config import Settings
from app.core.deps import CatalogQuoteRedisDep, CsrfDep, CurrentUserDep, DbDep, SettingsDep
from app.schemas.market_history import MarketHistoryQuery, MarketHistoryResponse
from app.services.market_history_authority import (
    HistoryAuthority,
    HistoryInstrumentNotFound,
    HistoryListingChanged,
    resolve_history,
)
from app.services.market_history_demand import history_response, request_history

router = APIRouter(tags=["market history"], route_class=PrivateRoute)


async def _resolve(
    db: AsyncSession, settings: Settings, body: MarketHistoryQuery
) -> HistoryAuthority | None:
    try:
        return await resolve_history(db, settings, body, datetime.now(UTC))
    except HistoryInstrumentNotFound:
        raise HTTPException(404, detail={"code": "instrument_not_found"}) from None
    except HistoryListingChanged:
        raise HTTPException(409, detail={"code": "listing_changed"}) from None


@router.post("/market-history/query", response_model=MarketHistoryResponse)
async def post_market_history(
    body: MarketHistoryQuery,
    user: CurrentUserDep,
    csrf: CsrfDep,
    db: DbDep,
    redis: CatalogQuoteRedisDep,
    settings: SettingsDep,
) -> MarketHistoryResponse:
    authority = await _resolve(db, settings, body)
    if redis is None or authority is None:
        return history_response(body, "unavailable")
    owner_id = user.id
    await db.rollback()
    try:
        result = await request_history(
            redis,
            server=settings.stock_data_server,
            owner_id=owner_id,
            query=body,
            fingerprint=authority.fingerprint,
        )
    except RedisError, TimeoutError:
        return history_response(body, "unavailable")
    if result.series is None:
        return result
    # Re-read current authority after waiting on Redis. The cache record never
    # perpetuates permission or listing identity across a change.
    current = await _resolve(db, settings, body)
    if current is None or current.fingerprint != authority.fingerprint:
        return history_response(body, "unavailable")
    if datetime.now(UTC) >= current.valid_until:
        return history_response(body, "unavailable")
    return result
