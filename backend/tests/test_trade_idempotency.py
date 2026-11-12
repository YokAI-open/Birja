"""Global economic keys cannot be hidden by an asset-specific route."""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.trade import Trade
from app.services import trading
from app.services.trade_math import TradeRefused
from tests.stock_action_fixtures import ownership, synthetic_fill  # noqa: F401


async def test_crypto_route_detects_existing_stock_key(ownership, settings):
    factory, cid, uid = ownership
    async with factory() as db:
        saved = await synthetic_fill(db, cid, uid)
        key = (await db.execute(select(Trade.idempotency_key).where(Trade.id == saved.id))).scalar_one()
        with pytest.raises(TradeRefused) as exc:
            await trading.execute(
                db, user_id=uid,
                order=trading.Order("BTC", "buy", "quantity", Decimal(2)),
                expected_mid=Decimal(100), idempotency_key=key, settings=settings,
            )
        assert exc.value.code == "idempotency_conflict"
