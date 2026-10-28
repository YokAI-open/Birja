from datetime import UTC, datetime

from fastapi import APIRouter, Response

from app.core.deps import CurrentUserDep, DbDep, SettingsDep
from app.schemas.prices import PriceOut, PricesOut
from app.services import prices

router = APIRouter(tags=["prices"])


@router.get(
    "/prices",
    response_model=PricesOut,
    summary="Latest coin prices",
    description=(
        "Latest mid price in USD for each active coin, ordered by market cap, with the age "
        "of each price and a status: fresh (under 120 s), aging (120 to 300 s) or stale "
        "(over 300 s). The thresholds are returned in the response."
    ),
)
async def get_prices(
    user: CurrentUserDep, db: DbDep, settings: SettingsDep, response: Response
) -> PricesOut:
    response.headers["Cache-Control"] = "no-store"
    now = datetime.now(UTC)
    rows = await prices.list_prices(db, settings, now)
    return PricesOut(
        server_time=now,
        fresh_seconds=settings.price_fresh_seconds,
        stale_seconds=settings.price_stale_seconds,
        items=[
            PriceOut(
                symbol=r.symbol,
                name=r.name,
                price=r.price,
                as_of=r.as_of,
                age_seconds=r.age_seconds,
                status=r.status,
            )
            for r in rows
        ],
    )
