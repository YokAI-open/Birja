from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class PriceOut(BaseModel):
    symbol: str
    name: str
    price: Decimal = Field(description="Mid price in USD, serialized as a decimal string")
    as_of: datetime
    age_seconds: int
    status: Literal["fresh", "aging", "stale"]


class PricesOut(BaseModel):
    server_time: datetime
    fresh_seconds: int
    stale_seconds: int
    items: list[PriceOut]
