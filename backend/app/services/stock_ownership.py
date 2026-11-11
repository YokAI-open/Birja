"""Instrument-first ownership transactions; no order endpoint or opening mutation.

Phase 9 callers own a READ COMMITTED transaction: instrument gate, account,
holdings ordered by (user_id,id), immutable cause, then journal/holding and cash
in the SAME transaction. Never commit a fill before its movement. Callers must
also enforce admission, quote/session and action eligibility immediately before
execution. Trade.created_at is ingestion time, never economic ownership time.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession


class OwnershipHeld(ValueError):
    """History or current authority cannot establish a safe automatic effect."""


@dataclass(frozen=True)
class StockMovementInput:
    user_id: int
    coin_id: int
    quantity: Decimal
    after_basis: Decimal
    causal_key: str
    trade_id: int | None = None
    application_id: int | None = None


async def acquire_stock_gate(db: AsyncSession, coin_id: int) -> datetime:
    raise OwnershipHeld("unverified")


async def append_stock_movement(db: AsyncSession, movement: StockMovementInput):
    raise OwnershipHeld("unverified")


async def assert_ownership_consistent(db: AsyncSession, coin_id: int):
    raise OwnershipHeld("unverified")


async def reconstruct_stock_quantity(db: AsyncSession, user_id: int, coin_id: int, cutoff, units):
    raise OwnershipHeld("unverified")
