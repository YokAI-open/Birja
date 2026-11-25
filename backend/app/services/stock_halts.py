"""Reported Nasdaq Trader halts for the simulator eligibility policy."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from hashlib import sha256
from typing import Literal
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
_REPORT_SYMBOL = re.compile(r"[A-Z0-9][A-Z0-9.$^+/=-]{0,13}\Z")


@dataclass(frozen=True, slots=True)
class HaltNotice:
    symbol: str
    market: str | None
    started_at: datetime | None


@dataclass(frozen=True)
class HaltReport:
    published_at: datetime
    observed_at: datetime
    halted_symbols: frozenset[str]
    market_halted: bool
    digest: str
    notices: tuple[HaltNotice, ...] = ()

    @property
    def valid_until(self) -> datetime:
        return self.published_at + REPORT_MAX_AGE


def catalog_report_state(
    report: HaltReport, exchange: str, verified_names: dict[str, datetime]
) -> Literal["normal", "halted"] | None:
    """Match a report notice to a dated listing or alias of this issue."""
    if report.market_halted:
        return "halted"
    uncertain = False
    for notice in report.notices:
        if notice.symbol not in verified_names:
            continue
        if notice.market is not None and (
            (notice.market == "NON-NASDAQ" and exchange == "NASDAQ")
            or (notice.market in {"NYSE", "NASDAQ"} and notice.market != exchange)
        ):
            continue
        if (
            notice.market == exchange
            and notice.started_at is not None
            and verified_names[notice.symbol] <= notice.started_at
        ):
            return "halted"
        uncertain = True
    return None if uncertain else "normal"


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


def _active_start(
    row: ElementTree.Element, published: datetime, observed: datetime
) -> datetime | None:
    start = _instant(_field(row, "HaltDate"), _field(row, "HaltTime"))
    if start > observed:
        raise ValueError("Reported halt is dated after receipt")
    day = _field(row, "ResumptionDate")
    time = _field(row, "ResumptionTradeTime")
    if time and not day:
        raise ValueError("Halt has a resumption time without a date")
    # Midnight placeholders in the exchange feed do not establish resumption.
    if day and time and time not in ("00:00:00", "00:00:01"):
        resume = _instant(day, time)
        if resume < start:
            raise ValueError("Halt resumption predates halt")
        if resume <= published:
            return None
    return start


def _notice_market(row: ElementTree.Element) -> str | None:
    fields = row.findall(f"{_NAMESPACE}Market")
    if len(fields) != 1 or len(fields[0]):
        return None
    market = (fields[0].text or "").strip().upper()
    if market in {"NASDAQ", "NYSE", "NON-NASDAQ"}:
        return market
    return None


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
    notices = []
    market_halted = False
    for row in rows:
        symbol = _field(row, "IssueSymbol")
        code = _field(row, "ReasonCode")
        if not _REPORT_SYMBOL.fullmatch(symbol) and code not in _MARKET_WIDE:
            continue
        market = _notice_market(row)
        try:
            start = _active_start(row, published, observed_at)
        except ValueError:
            if symbol in CURATED_SYMBOLS or code in _MARKET_WIDE:
                raise
            notices.append(HaltNotice(symbol, market, None))
            continue
        if start is None:
            continue
        if code in _MARKET_WIDE:
            market_halted = True
        if symbol in CURATED_SYMBOLS:
            halted.add(symbol)
        if _REPORT_SYMBOL.fullmatch(symbol):
            notices.append(HaltNotice(symbol, market, start))
    return HaltReport(
        published,
        observed_at,
        frozenset(halted),
        market_halted,
        sha256(payload).hexdigest(),
        tuple(notices),
    )
