"""Public stock discovery contracts, independent of execution."""

import re
from typing import Annotated, Literal

from pydantic import (
    AliasChoices,
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
)

CatalogId = Annotated[
    int,
    Field(gt=0, le=9223372036854775807),
    PlainSerializer(str, return_type=str, when_used="json"),
]


def _decimal_identity(value: object) -> int:
    if not isinstance(value, str) or re.fullmatch(r"[1-9][0-9]{0,18}", value) is None:
        raise ValueError("catalog identity must be a decimal string")
    return int(value)


CatalogIdInput = Annotated[CatalogId, BeforeValidator(_decimal_identity)]


def _search_text(value: object) -> str:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isprintable():
            return stripped
    raise ValueError("enter a ticker or company name")


CatalogSearchText = Annotated[
    str,
    Field(min_length=1, max_length=80),
    BeforeValidator(_search_text),
]


class StockCatalogItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    catalog_id: CatalogId = Field(validation_alias=AliasChoices("catalog_id", "security_id"))
    listing_version: CatalogId = Field(validation_alias=AliasChoices("listing_version", "id"))
    ticker: str
    company_name: str
    listing_exchange: Literal["NASDAQ", "NYSE"]
    share_class: str | None
    state: Literal["active", "review", "retired"]
    reason: Literal[
        "reviewed_issue_evidence",
        "corroborated_share_class",
        "missing_without_retirement_evidence",
        "confirmed_retirement",
        "verified_ticker_reuse",
    ]


class StockCatalogSearch(BaseModel):
    model_config = ConfigDict(frozen=True)

    state: Literal["ready", "unavailable"]
    generation_id: CatalogId | None = None
    published_at: AwareDatetime | None = None
    has_more: bool = False
    items: list[StockCatalogItem] = Field(default_factory=list)
