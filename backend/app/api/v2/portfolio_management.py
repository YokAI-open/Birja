"""Bounded private management transport; an unavailable response may follow commit."""

import json
import logging
import re
from collections.abc import Callable, Coroutine
from typing import Any
from uuid import UUID

from fastapi import HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.api.v1.stock_trades import PRIVATE
from app.core.config import Settings
from app.schemas.portfolios import PortfolioCreate, PortfolioPatch
from app.services.ratelimit import RateLimited, enforce, ip_bucket

logger = logging.getLogger(__name__)
MAX_BODY_BYTES = 8192
_KEY = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")


class ManagementRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()

        async def private(request: Request) -> Response:
            try:
                response = await original(request)
            except StarletteHTTPException as exc:
                exc.headers = {**(exc.headers or {}), **PRIVATE}
                raise
            except RequestValidationError:
                response = JSONResponse(
                    status_code=422, content={"detail": {"code": "invalid_input"}}
                )
            except RedisError:
                response = JSONResponse(
                    status_code=503,
                    content={"detail": {"code": "service_unavailable"}},
                    headers={"Retry-After": "5"},
                )
            except Exception as exc:
                logger.error("portfolio management failed type=%s", type(exc).__name__)
                response = JSONResponse(
                    status_code=500,
                    content={
                        "detail": {
                            "code": "service_unavailable",
                            "message": "Portfolio result unavailable. Retry the original request.",
                        }
                    },
                )
            response.headers.update(PRIVATE)
            return response

        return private


def creation_key(value: str | None) -> UUID:
    if value is None or len(value) != 36 or _KEY.fullmatch(value) is None:
        raise HTTPException(422, detail={"code": "invalid_creation_key"})
    return UUID(value)


async def enforce_creation_attempt(redis: Redis, owner: int, ip: str, settings: Settings) -> None:
    try:
        # Count the network bucket first so rotating owners cannot evade it.
        await enforce(
            redis,
            f"sim:rl:portfolio_create:ip:{ip_bucket(ip)}",
            settings.portfolio_create_ip_limit,
            60,
        )
        await enforce(
            redis,
            f"sim:rl:portfolio_create:owner:{owner}",
            settings.portfolio_create_owner_limit,
            60,
        )
    except RateLimited as exc:
        raise HTTPException(
            429, detail={"code": "rate_limited"}, headers={"Retry-After": str(exc.retry_after)}
        ) from None


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate field")
        result[key] = value
    return result


async def read_management_body(
    request: Request, *, patch: bool
) -> PortfolioCreate | PortfolioPatch:
    """Called only after owner/CSRF checks; never trust Content-Length for memory bounds."""
    media = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media != "application/json":
        raise HTTPException(415, detail={"code": "unsupported_media_type"})
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_BODY_BYTES:
            raise HTTPException(413, detail={"code": "body_too_large"})
        body.extend(chunk)
    try:
        value = json.loads(body.decode("utf-8"), object_pairs_hook=_object)
        schema = PortfolioPatch if patch else PortfolioCreate
        return schema.model_validate(value)
    except ValueError, ValidationError, RecursionError:
        raise HTTPException(422, detail={"code": "invalid_input"}) from None
