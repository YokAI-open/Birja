"""Read and validate the two Nasdaq Trader listing directories."""

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict

DirectorySource = Literal["nasdaqlisted", "otherlisted"]
ListingExchange = Literal["NYSE", "NASDAQ"]
AliasNamespace = Literal["act", "cqs", "nasdaq", "openfigi"]

DIRECTORY_URLS: dict[DirectorySource, str] = {
    "nasdaqlisted": "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
    "otherlisted": "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt",
}
HEADERS = {
    "nasdaqlisted": (
        "Symbol|Security Name|Market Category|Test Issue|Financial Status|"
        "Round Lot Size|ETF|NextShares"
    ),
    "otherlisted": (
        "ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol"
    ),
}
MAX_DIRECTORY_BYTES = 4 * 1024 * 1024
MAX_DIRECTORY_ROWS = 20_000
_MAX_AGE = timedelta(days=4)
_MAX_PAIR_SKEW = timedelta(hours=1)
_EASTERN = ZoneInfo("America/New_York")
SYMBOL_PATTERN = r"[A-Z0-9][A-Z0-9.$^+/=\-]{0,13}"
_TIMESTAMP = re.compile(r"File Creation Time: ?([0-9]{10}):?([0-9]{2})")
_NASDAQ_FIGI_VENUES = {"Q": "UW", "G": "UQ", "S": "UR"}
_OTHER_VENUES = {"A", "N", "P", "V", "Z"}


class CatalogSourceError(ValueError):
    """The source cannot contribute to a complete inventory."""


class CatalogAlias(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    namespace: AliasNamespace
    symbol: str


@dataclass(frozen=True, slots=True)
class DirectoryRow:
    source: DirectorySource
    row_key: str
    row_digest: str
    ticker: str
    listing_exchange: ListingExchange | None
    company_name: str
    aliases: tuple[CatalogAlias, ...]
    figi_exchange: str | None
    exclusion: str | None


@dataclass(frozen=True, slots=True)
class DirectorySnapshot:
    artifact: DirectorySource
    sha256: str
    published_at: datetime
    rows: tuple[DirectoryRow, ...]


def _source_timestamp(value: str) -> datetime:
    match = _TIMESTAMP.fullmatch(value)
    if match is None:
        raise CatalogSourceError("Missing or malformed terminal directory timestamp")
    try:
        local_time = datetime.strptime("".join(match.groups()), "%m%d%Y%H%M")
    except ValueError as exc:
        raise CatalogSourceError("Invalid terminal directory timestamp") from exc
    early = local_time.replace(tzinfo=_EASTERN, fold=0)
    late = local_time.replace(tzinfo=_EASTERN, fold=1)
    if early.utcoffset() != late.utcoffset():
        raise CatalogSourceError("Directory timestamp is ambiguous or nonexistent")
    return early.astimezone(UTC)


def _symbol(value: str) -> str:
    if re.fullmatch(SYMBOL_PATTERN, value) is None:
        raise CatalogSourceError("Invalid directory ticker")
    return value


def _parse_row(source: DirectorySource, line: str, ordinal: int) -> DirectoryRow:
    fields = line.split("|")
    if len(fields) != 8:
        raise CatalogSourceError("Invalid directory column count")
    ticker, name, category, first, second, third, fourth, fifth = fields
    ticker = _symbol(ticker)
    listing_exchange: ListingExchange | None
    figi_exchange: str | None
    aliases: tuple[CatalogAlias, ...]
    if source == "nasdaqlisted":
        listing_exchange = "NASDAQ"
        figi_exchange = _NASDAQ_FIGI_VENUES.get(category)
        test_issue, financial_status, round_lot, etf, next_shares = (
            first,
            second,
            third,
            fourth,
            fifth,
        )
        if figi_exchange is None or financial_status not in [
            "D",
            "E",
            "Q",
            "N",
            "G",
            "H",
            "J",
            "K",
        ]:
            raise CatalogSourceError("Unknown Nasdaq category or financial status")
        if next_shares not in {"Y", "N"}:
            raise CatalogSourceError("Unknown Nasdaq NextShares flag")
        aliases = (CatalogAlias(namespace="nasdaq", symbol=ticker),)
    else:
        if category not in _OTHER_VENUES:
            raise CatalogSourceError("Unknown other-listed exchange code")
        listing_exchange = "NYSE" if category == "N" else None
        figi_exchange = "UN" if listing_exchange else None
        cqs, etf, round_lot, test_issue, nasdaq = first, second, third, fourth, fifth
        next_shares = "N"
        aliases = (
            CatalogAlias(namespace="act", symbol=ticker),
            CatalogAlias(namespace="cqs", symbol=_symbol(cqs)),
            CatalogAlias(namespace="nasdaq", symbol=_symbol(nasdaq)),
        )
    if etf not in {"Y", "N"} or test_issue not in {"Y", "N"}:
        raise CatalogSourceError("Unknown ETF or test issue flag")
    if re.fullmatch(r"[0-9]{1,6}", round_lot) is None or int(round_lot) == 0:
        raise CatalogSourceError("Invalid directory round lot")
    if not name.strip() or len(name) > 255 or not name.isprintable():
        raise CatalogSourceError("Invalid directory security name")
    exclusion = None
    if listing_exchange is None:
        exclusion = "other_primary_exchange"
    elif test_issue == "Y":
        exclusion = "test_issue"
    elif etf == "Y":
        exclusion = "exchange_traded_fund"
    elif next_shares == "Y":
        exclusion = "nextshares"
    return DirectoryRow(
        source=source,
        row_key=f"{source}:{ordinal}",
        row_digest=hashlib.sha256(line.encode("utf-8")).hexdigest(),
        ticker=ticker,
        listing_exchange=listing_exchange,
        company_name=name.strip(),
        aliases=aliases,
        figi_exchange=figi_exchange,
        exclusion=exclusion,
    )


def parse_directory(source: DirectorySource, payload: bytes) -> DirectorySnapshot:
    if not payload or len(payload) > MAX_DIRECTORY_BYTES or not payload.endswith(b"\n"):
        raise CatalogSourceError("Directory is empty, oversized or truncated")
    try:
        decoded = payload.decode("utf-8").replace("\r\n", "\n")
    except UnicodeError as exc:
        raise CatalogSourceError("Directory has invalid UTF-8") from exc
    lines = decoded.removesuffix("\n").split("\n")
    if not 3 <= len(lines) <= MAX_DIRECTORY_ROWS + 2 or lines[0] != HEADERS[source]:
        raise CatalogSourceError("Directory has an unexpected header or row count")
    footer = lines[-1].split("|")
    if len(footer) != 8 or any(footer[1:]):
        raise CatalogSourceError("Directory is missing a complete terminal timestamp row")
    return DirectorySnapshot(
        artifact=source,
        sha256=hashlib.sha256(payload).hexdigest(),
        published_at=_source_timestamp(footer[0]),
        rows=tuple(
            _parse_row(source, line, ordinal) for ordinal, line in enumerate(lines[1:-1], 1)
        ),
    )


def validate_directory_pair(
    nasdaq: DirectorySnapshot, other: DirectorySnapshot, now: datetime
) -> tuple[DirectorySnapshot, DirectorySnapshot]:
    if now.utcoffset() is None:
        raise CatalogSourceError("Directory verification requires an aware clock")
    if nasdaq.artifact != "nasdaqlisted" or other.artifact != "otherlisted":
        raise CatalogSourceError("Both distinct listing directories are required")
    if abs(nasdaq.published_at - other.published_at) > _MAX_PAIR_SKEW:
        raise CatalogSourceError("Directory timestamps are incoherent")
    if any(
        not timedelta(0) <= now - snapshot.published_at <= _MAX_AGE for snapshot in (nasdaq, other)
    ):
        raise CatalogSourceError("Directory timestamp is stale or in the future")
    if not any(row.listing_exchange == "NYSE" for row in other.rows):
        raise CatalogSourceError("The other-listed directory has no NYSE observations")
    return nasdaq, other
