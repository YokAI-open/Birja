from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, PlainSerializer

Money = Annotated[
    Decimal, PlainSerializer(lambda value: format(value, "f"), return_type=str, when_used="json")
]


class HistoryItem(BaseModel):
    id: str
    created_at: datetime
    symbol: str
    name: str
    side: Literal["buy", "sell"]
    quantity: Money
    exec_price: Money
    fee: Money
    total: Money


class HistoryPage(BaseModel):
    items: list[HistoryItem]
    next_cursor: str | None
