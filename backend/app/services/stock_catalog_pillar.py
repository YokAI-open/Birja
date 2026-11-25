"""Verify listing facts using the public NYSE Pillar and FINRA CAT references.

Use these records for comparison. Obtain published fields from sources with
documented reuse rights and retain comparator dates, digests and counts.
"""

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Literal
from zoneinfo import ZoneInfo

from app.services.stock_catalog_sources import CatalogSourceError, ListingExchange

MAX_PILLAR_BYTES = 4 * 1024 * 1024
MAX_PILLAR_ROWS = 20_000
MAX_CAT_BYTES = 8 * 1024 * 1024
MAX_CAT_ROWS = 100_000
_EASTERN = ZoneInfo("America/New_York")
_PRIMARY_EXCHANGES: dict[str, ListingExchange] = {"N": "NYSE", "Q": "NASDAQ"}
_VENUE_SYMBOL = re.compile(r"[A-Z0-9]+(?: [A-Z0-9]+)?")
_CQS_SYMBOL = re.compile(r"[A-Z0-9][A-Z0-9.prw]{0,13}")
_NUMBER = re.compile(r"[0-9]{1,10}")
_CAT_HEADER = "symbol|issueName|listingExchange|testIssueFlag"
_CAT_FOOTER = re.compile(r"([0-9]{14})\|([0-9]{1,6})")
_PILLAR_LISTED_VENUES = frozenset("AFLMNPQVZ")
_CAT_LISTED_VENUES = frozenset("AFMNPQUVZ") | {""}
_PILLAR_SECURITY_TYPES = frozenset("ACHDEFMIOPRSTUW")
_COMMON_CLASSES: dict[str, Literal["common_stock", "ordinary_shares"]] = {
    "C": "common_stock",
    "O": "ordinary_shares",
}


@dataclass(frozen=True, slots=True)
class PillarIssue:
    listing_exchange: ListingExchange
    venue_symbol: str
    cqs_symbol: str
    security_type: str

    @property
    def common_class(self) -> Literal["common_stock", "ordinary_shares"] | None:
        return _COMMON_CLASSES.get(self.security_type)


@dataclass(frozen=True, slots=True)
class PillarSnapshot:
    trade_date: date
    sha256: str
    row_count: int
    issues: tuple[PillarIssue, ...]

    def index_by_venue_symbol(self) -> dict[tuple[ListingExchange, str], PillarIssue]:
        return {(issue.listing_exchange, issue.venue_symbol): issue for issue in self.issues}

    def index_by_cqs_symbol(self) -> dict[tuple[ListingExchange, str], PillarIssue]:
        return {(issue.listing_exchange, issue.cqs_symbol): issue for issue in self.issues}


@dataclass(frozen=True, slots=True)
class CatSnapshot:
    trade_date: date
    created_at: datetime
    published_at: datetime
    sha256: str
    row_count: int
    keys: frozenset[tuple[ListingExchange, str]]
    test_symbols: frozenset[str]


def _source_lines(payload: bytes, limit: int, source: str) -> list[str]:
    if not payload or len(payload) > limit or not payload.endswith(b"\n"):
        raise CatalogSourceError(f"{source} file is empty, oversized or truncated")
    try:
        text = payload.decode("utf-8").replace("\r\n", "\n")
    except UnicodeError as exc:
        raise CatalogSourceError(f"{source} file has invalid UTF-8") from exc
    if "\r" in text or "\x00" in text:
        raise CatalogSourceError(f"{source} file contains invalid characters")
    return text.removesuffix("\n").split("\n")


def _valid_venue_symbol(value: str) -> bool:
    return len(value) <= 14 and _VENUE_SYMBOL.fullmatch(value) is not None


def parse_pillar_snapshot(
    payload: bytes, *, filename: str, expected_trade_date: date
) -> PillarSnapshot:
    """Read the dated NYSE production TXT layout from Pillar v2.4o §9."""
    if filename != f"NYSESymbolMapping_{expected_trade_date:%Y%m%d}.txt":
        raise CatalogSourceError("Pillar name does not match the expected trading date")
    lines = _source_lines(payload, MAX_PILLAR_BYTES, "Pillar")
    if len(lines) > MAX_PILLAR_ROWS:
        raise CatalogSourceError("Pillar file exceeds its row bound")
    issues = []
    for line in lines:
        fields = line.split("|")
        if len(fields) != 12:
            raise CatalogSourceError("Pillar row has an unexpected field count")
        symbol, cqs, index, market, listed, tape, lot, scale, system, kind, reserved, end = fields
        if (
            not _valid_venue_symbol(symbol)
            or _CQS_SYMBOL.fullmatch(cqs) is None
            or market != "N"
            or listed not in _PILLAR_LISTED_VENUES
            or tape not in {"A", "B", "C"}
            or kind not in _PILLAR_SECURITY_TYPES
            or reserved
            or end
            or any(_NUMBER.fullmatch(value) is None for value in (index, lot, scale, system))
        ):
            raise CatalogSourceError("Pillar row has invalid fields")
        exchange = _PRIMARY_EXCHANGES.get(listed)
        if exchange is None or kind == "T":
            continue
        if tape != ("A" if exchange == "NYSE" else "C"):
            raise CatalogSourceError("Pillar row conflicts with the primary listing tape")
        issues.append(PillarIssue(exchange, symbol, cqs, kind))
    snapshot = PillarSnapshot(
        expected_trade_date, hashlib.sha256(payload).hexdigest(), len(lines), tuple(issues)
    )
    if len(snapshot.index_by_venue_symbol()) != len(issues) or len(
        snapshot.index_by_cqs_symbol()
    ) != len(issues):
        raise CatalogSourceError("Pillar file has ambiguous primary or CQS symbols")
    if {issue.listing_exchange for issue in issues} != {"NYSE", "NASDAQ"}:
        raise CatalogSourceError("Pillar file does not cover both primary venues")
    return snapshot


def _cat_created_at(footer: str, row_count: int) -> datetime:
    match = _CAT_FOOTER.fullmatch(footer)
    if match is None or int(match[2]) != row_count:
        raise CatalogSourceError("CAT footer does not match the data row count")
    try:
        local = datetime.strptime(match[1], "%Y%m%d%H%M%S")
    except ValueError as exc:
        raise CatalogSourceError("CAT footer timestamp is invalid") from exc
    created_at = local.replace(tzinfo=_EASTERN, fold=0)
    if created_at.utcoffset() != local.replace(tzinfo=_EASTERN, fold=1).utcoffset():
        raise CatalogSourceError("CAT footer timestamp is ambiguous or nonexistent")
    return created_at


def parse_cat_snapshot(
    payload: bytes, *, published_at: datetime, expected_trade_date: date
) -> CatSnapshot:
    """Keep exact primary NYSE and Nasdaq symbols from a dated CAT report."""
    lines = _source_lines(payload, MAX_CAT_BYTES, "CAT")
    if not 3 <= len(lines) <= MAX_CAT_ROWS + 2 or lines[0] != _CAT_HEADER:
        raise CatalogSourceError("CAT file has an unexpected header or row count")
    row_count = len(lines) - 2
    created_at = _cat_created_at(lines[-1], row_count)
    if (
        published_at.utcoffset() is None
        or created_at.date() != expected_trade_date
        or created_at > published_at
        or published_at.astimezone(_EASTERN).date() != expected_trade_date
    ):
        raise CatalogSourceError("CAT dates do not match the expected trading date")
    keys: set[tuple[ListingExchange, str]] = set()
    test_symbols: set[str] = set()
    for line in lines[1:-1]:
        fields = line.split("|")
        if len(fields) != 4:
            raise CatalogSourceError("CAT row has an unexpected field count")
        symbol, name, listed, test = fields
        if (
            not 0 < len(symbol) <= 14
            or len(name) > 255
            or listed not in _CAT_LISTED_VENUES
            or test not in {"N", "Y"}
        ):
            raise CatalogSourceError("CAT row has invalid fields")
        if test == "Y":
            test_symbols.add(symbol)
            continue
        exchange = _PRIMARY_EXCHANGES.get(listed)
        if exchange is None:
            continue
        key = (exchange, symbol)
        if not _valid_venue_symbol(symbol) or key in keys:
            raise CatalogSourceError("CAT file has invalid or ambiguous primary symbols")
        keys.add(key)
    if {venue for venue, _ in keys} != {"NYSE", "NASDAQ"}:
        raise CatalogSourceError("CAT file does not cover both primary venues")
    return CatSnapshot(
        expected_trade_date,
        created_at.astimezone(UTC),
        published_at.astimezone(UTC),
        hashlib.sha256(payload).hexdigest(),
        row_count,
        frozenset(keys),
        frozenset(test_symbols),
    )
