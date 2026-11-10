"""Latest stock quote persistence; caller owns the short transaction/commit."""

from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.stock_quote_rules import StockMapping, ValidatedStockQuote


async def load_stock_catalog(db: AsyncSession) -> list[StockMapping]:
    return []


async def upsert_stock_quotes(
    db: AsyncSession,
    quotes: Sequence[ValidatedStockQuote],
    admission_generation: int,
    *,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    account: str = "birja",
    server: str = "birja",
) -> int:
    return 0
