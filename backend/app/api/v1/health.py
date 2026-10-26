from fastapi import APIRouter, Response, status

from app.core.deps import DbDep, RedisDep
from app.schemas.health import HealthOut
from app.services.health import check_health

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthOut,
    summary="Backend, database and Redis health",
    description="Returns 200 when Postgres and Redis answer, 503 with the failing dependency "
    "marked as error otherwise.",
    responses={503: {"model": HealthOut, "description": "A dependency is unreachable"}},
)
async def health(db: DbDep, redis: RedisDep, response: Response) -> HealthOut:
    result = await check_health(db, redis)
    response.headers["Cache-Control"] = "no-store"
    if result.status == "degraded":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result
