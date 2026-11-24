"""Reported Nasdaq Trader halts for the simulator eligibility policy."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from hashlib import sha256
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

from app.services.stock_quote_rules import CURATED_SYMBOLS

SOURCE = "nasdaq-rss"
# Two-key PostgreSQL advisory lock namespace, separate from instrument locks.
REPORT_LOCK_KEYS = "1326459824, 1"
URL = "https://www.nasdaqtrader.com/rss.aspx?feed=tradehalts"
REPORT_MAX_AGE = timedelta(seconds=120)
MAX_REPORT_BYTES = 2 * 1024 * 1024
_NAMESPACE = "{http://www.nasdaqtrader.com/}"
_EASTERN = ZoneInfo("America/New_York")
_MARKET_WIDE = frozenset({"MWC0", "MWC1", "MWC2", "MWC3", "MWCQ"})


@dataclass(frozen=True)
class HaltReport:
    published_at: datetime
    observed_at: datetime
    halted_symbols: frozenset[str]
    market_halted: bool
    digest: str

    @property
    def valid_until(self) -> datetime:
        return self.published_at + REPORT_MAX_AGE


def _field(row: ElementTree.Element, key: str) -> str:
    fields = row.findall(f"{_NAMESPACE}{key}")
    if len(fields) != 1 or len(fields[0]):
        raise ValueError("Halt report field is missing or ambiguous")
    return (fields[0].text or "").strip()


def _instant(day: str, time: str) -> datetime:
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", day) or not re.fullmatch(
        r"\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?", time
    ):
        raise ValueError("Invalid halt report timestamp")
    fmt = "%m/%d/%Y %H:%M:%S.%f" if "." in time else "%m/%d/%Y %H:%M:%S"
    return datetime.strptime(f"{day} {time}", fmt).replace(tzinfo=_EASTERN).astimezone(UTC)


def parse_halt_report(payload: bytes, *, last_modified: str, observed_at: datetime) -> HaltReport:
    """Validate the received report. Missing notices do not prove venue status."""
    published = parsedate_to_datetime(last_modified)
    if (
        published.tzinfo is None
        or observed_at.utcoffset() != timedelta(0)
        or not timedelta(0) <= observed_at - published < REPORT_MAX_AGE
        or not 0 < len(payload) <= MAX_REPORT_BYTES
        or b"\x00" in payload
        or b"<!" in payload.replace(b"<![CDATA[", b"")
    ):
        raise ValueError("Unavailable or expired halt report")
    published = published.astimezone(UTC)
    try:
        root = ElementTree.fromstring(payload)  # noqa: S314 - bounded, declarations excluded above
    except ElementTree.ParseError as exc:
        raise ValueError("Invalid halt report XML") from exc
    channels = root.findall("channel")
    if root.tag != "rss" or len(channels) != 1:
        raise ValueError("Invalid halt report envelope")
    rows = channels[0].findall("item")
    count = _field(channels[0], "numItems")
    if not re.fullmatch(r"\d{1,4}", count) or int(count) != len(rows):
        raise ValueError("Halt report count mismatch")
    halted = set()
    market_halted = False
    for row in rows:
        symbol = _field(row, "IssueSymbol")
        code = _field(row, "ReasonCode")
        if symbol not in CURATED_SYMBOLS and code not in _MARKET_WIDE:
            continue
        start = _instant(_field(row, "HaltDate"), _field(row, "HaltTime"))
        if start > observed_at:
            raise ValueError("Reported halt is dated after receipt")
        day = _field(row, "ResumptionDate")
        time = _field(row, "ResumptionTradeTime")
        if time and not day:
            raise ValueError("Halt has a resumption time without a date")
        # Midnight placeholders in the exchange feed do not establish a trade resumption.
        if day and time and time not in ("00:00:00", "00:00:01"):
            resume = _instant(day, time)
            if resume < start:
                raise ValueError("Halt resumption predates halt")
            if resume <= published:
                continue
        if code in _MARKET_WIDE:
            market_halted = True
        if symbol in CURATED_SYMBOLS:
            halted.add(symbol)
    return HaltReport(
        published, observed_at, frozenset(halted), market_halted, sha256(payload).hexdigest()
    )
