"""Private portfolio metadata; metadata never grants financial authority."""

from typing import Annotated

from pydantic import BaseModel, Field, PlainSerializer

PortfolioId = Annotated[
    int,
    Field(gt=0, le=9223372036854775807),
    PlainSerializer(str, return_type=str, when_used="json"),
]


class PortfolioSummary(BaseModel):
    id: PortfolioId
    name: str
