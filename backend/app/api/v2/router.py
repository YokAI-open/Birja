from fastapi import APIRouter

from app.api.v2.auth import router as auth_router
from app.api.v2.history import router as history_router
from app.api.v2.me import router as me_router
from app.api.v2.portfolios import router as portfolios_router
from app.api.v2.stock_trades import router as stock_trades_router
from app.api.v2.trades import router as trades_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(me_router)
api_router.include_router(portfolios_router)
api_router.include_router(history_router)
api_router.include_router(trades_router)
api_router.include_router(stock_trades_router)
