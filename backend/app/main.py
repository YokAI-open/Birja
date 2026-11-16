from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.connection import database_connect_args
from app.db.schema_contract import SchemaAdmissionError, require_schema
from app.services.email import build_email_sender
from app.services.otp import OtpStore


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args=database_connect_args(settings),
    )
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    app.state.engine = engine
    app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    app.state.redis = redis
    app.state.otp_store = OtpStore(redis, settings.otp_hmac_secret)
    http = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
    app.state.http = http
    app.state.email_sender = build_email_sender(settings, http)
    try:
        async with engine.connect() as connection:
            await require_schema(connection)
        yield
    finally:
        await http.aclose()
        await redis.aclose()
        await engine.dispose()


async def redis_unavailable(request: Request, exc: RedisError) -> JSONResponse:
    # Sign-in cannot work without Redis: tell the client to retry, leak nothing.
    return JSONResponse(
        status_code=503,
        content={
            "detail": {
                "code": "service_unavailable",
                "message": "Sign-in is temporarily unavailable. Try again in a moment.",
            }
        },
        headers={"Retry-After": "5"},
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    configure_logging()
    settings = settings or get_settings()
    is_prod = settings.env == "prod"
    app = FastAPI(
        title="Birja API",
        lifespan=lifespan,
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
    )
    app.state.settings = settings

    @app.middleware("http")
    async def admit_write(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            try:
                async with request.app.state.engine.connect() as connection:
                    await require_schema(connection)
            except SchemaAdmissionError:
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": {
                            "code": "schema_unavailable",
                            "message": "Service is temporarily unavailable.",
                        }
                    },
                )
        return await call_next(request)

    app.add_exception_handler(RedisError, redis_unavailable)  # type: ignore[arg-type]
    app.include_router(api_router, prefix="/api/v1")
    return app
