from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.history import router as history_router
from app.api.v1.me import router as me_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.prices import router as prices_router
from app.api.v1.trades import router as trades_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(me_router)
api_router.include_router(prices_router)
api_router.include_router(trades_router)
api_router.include_router(portfolio_router)
api_router.include_router(history_router)
