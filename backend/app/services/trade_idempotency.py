"""User-scoped global trade keys, independent of market availability."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trade import Trade
from app.services.trade_math import TradeRefused


async def find_user_trade(db: AsyncSession, user_id: int, key: UUID) -> Trade | None:
    return (
        await db.execute(
            select(Trade)
            .where(Trade.user_id == user_id, Trade.idempotency_key == key)
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()


def require_same_order(
    trade: Trade, *, same_instrument: bool, side: str, kind: str, value: Decimal
) -> None:
    """Confirmation prices are deliberately excluded from economic identity."""
    if not (
        same_instrument
        and trade.side == side
        and trade.input_kind == kind
        and trade.input_value == value
    ):
        raise TradeRefused(
            "idempotency_conflict",
            "This order key was already used for a different order. Start a new order.",
        )
