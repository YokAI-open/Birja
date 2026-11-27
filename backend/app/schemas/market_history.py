"""History contracts independent of executable quote eligibility."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, PlainSerializer, model_validator

from app.schemas.stock_catalog import CatalogIdInput

HistoryRange = Literal["1D", "1W", "1M"]
HistorySource = Literal["kraken", "alpaca_iex", "coin_metrics"]
HistoryInterval = Literal[5, 30, 60, 240, 1440]
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
    interval_minutes: HistoryInterval
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


class CryptoHistoryBinding(HistoryContract):
    instrument: CryptoHistoryInstrument
    pair: Annotated[str, Field(pattern=r"^[A-Z0-9]{1,32}$")]


class EquityHistoryBinding(HistoryContract):
    instrument: Annotated[
        FeaturedHistoryInstrument | CatalogHistoryInstrument, Field(discriminator="kind")
    ]
    provider_symbol: HistorySymbol
    provider_asset_id: Annotated[str, Field(min_length=1, max_length=128)]
    exchange: Literal["NYSE", "NASDAQ"]
    # Earliest date verified for this exact security and provider symbol.
    identity_since: AwareDatetime


class HistoryScope(HistoryContract):
    generation: Annotated[int, Field(gt=0)]
    evidence_ref: Annotated[str, Field(min_length=1, max_length=256)]
    server: Annotated[str, Field(min_length=1, max_length=128)]
    reviewed_at: AwareDatetime
    valid_from: AwareDatetime
    valid_until: AwareDatetime
    collection_allowed: Literal[True]
    display_allowed: Literal[True]
    derived_allowed: Literal[True]
    retention_seconds: Annotated[int, Field(ge=1, le=600)]
    admitted_requests_per_minute: Annotated[int, Field(ge=1, le=10000)]
    observed_requests_per_minute: Annotated[int, Field(ge=1, le=10000)]
    max_response_bytes: Annotated[int, Field(ge=1, le=262144)]

    @model_validator(mode="after")
    def _valid_period(self) -> HistoryScope:
        if (
            not self.evidence_ref.strip()
            or not self.reviewed_at <= self.valid_from < self.valid_until
        ):
            raise ValueError("invalid historical source evidence period")
        return self

    def applies(self, now: AwareDatetime, server: str) -> bool:
        return server == self.server and self.valid_from <= now < self.valid_until


class KrakenHistoryScope(HistoryScope):
    targets: Annotated[tuple[CryptoHistoryBinding, ...], Field(min_length=1, max_length=100)]
    # Verified aggregate ceilings for Ticker and OHLC on this scheduler's IP.
    aggregate_ip_requests_per_minute: Annotated[int, Field(ge=1, le=10000)]
    aggregate_pair_requests_per_minute: Annotated[int, Field(ge=1, le=10000)]


class IexHistoryScope(HistoryScope):
    account: Annotated[str, Field(min_length=1, max_length=128)]
    targets: Annotated[tuple[EquityHistoryBinding, ...], Field(min_length=1, max_length=2048)]


class CoinMetricsHistoryScope(HistoryContract):
    """Fixed Community chart policy for the noncommercial deployment."""

    generation: Literal[1] = 1
    retention_seconds: Literal[600] = 600
    max_response_bytes: Literal[262144] = 262144


class MarketHistoryScopes(HistoryContract):
    kraken: KrakenHistoryScope | None = None
    alpaca_iex: IexHistoryScope | None = None
