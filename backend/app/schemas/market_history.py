"""History contracts independent of executable quote eligibility."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, PlainSerializer

from app.schemas.stock_catalog import CatalogIdInput

HistoryRange = Literal["1D", "1W", "1M"]
HistorySource = Literal["kraken", "alpaca_iex"]
HistoryCoverage = Literal["complete", "partial", "empty"]
HistoryTimeliness = Literal["on_time", "delayed", "unknown"]
HistoryState = Literal["ready", "partial", "empty", "pending", "unavailable"]
HistorySymbol = Annotated[str, Field(pattern=r"^[A-Z0-9][A-Z0-9.\-/]{0,13}$")]
HistoryDecimal = Annotated[
    Decimal,
    PlainSerializer(lambda number: format(number, "f"), return_type=str, when_used="json"),
]


class HistoryContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class CryptoHistoryInstrument(HistoryContract):
    kind: Literal["crypto"]
    symbol: HistorySymbol


class FeaturedHistoryInstrument(HistoryContract):
    kind: Literal["featured"]
    symbol: HistorySymbol


class CatalogHistoryInstrument(HistoryContract):
    kind: Literal["catalog"]
    catalog_id: CatalogIdInput
    listing_version: CatalogIdInput


HistoryInstrument = Annotated[
    CryptoHistoryInstrument | FeaturedHistoryInstrument | CatalogHistoryInstrument,
    Field(discriminator="kind"),
]


class MarketHistoryQuery(HistoryContract):
    instrument: HistoryInstrument
    range: HistoryRange


class MarketHistoryPoint(HistoryContract):
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    close: Annotated[HistoryDecimal, Field(gt=0, max_digits=30, decimal_places=12)]
    gap_before: Literal["missing", "closed"] | None = None


class MarketHistorySeries(HistoryContract):
    source: HistorySource
    currency: Literal["USD"] = "USD"
    time_basis: Literal["utc", "regular_session"]
    adjustment: Literal["raw", "split"]
    interval_minutes: Literal[5, 30, 60, 240]
    start_at: AwareDatetime
    end_at: AwareDatetime
    as_of: AwareDatetime | None
    expected_through_at: AwareDatetime | None
    timeliness: HistoryTimeliness
    coverage: HistoryCoverage
    points: tuple[MarketHistoryPoint, ...] = Field(max_length=512)
    day_change_pct: HistoryDecimal | None = None
    period_change_pct: HistoryDecimal | None = None


class MarketHistoryResponse(MarketHistoryQuery):
    state: HistoryState
    series: MarketHistorySeries | None = None
