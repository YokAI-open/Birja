from dataclasses import replace
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import pytest

from app.services.stock_halts import SOURCE, parse_halt_report
from app.services.stock_trading_rules import StatusEvidence, status_current

NOW = datetime(2026, 11, 24, 16, tzinfo=UTC)


def item(symbol: str, code: str, resumed_at: str = "", day: str = "11/24/2026") -> str:
    resume_date = "11/24/2026" if resumed_at else ""
    return (
        f"<item><n:IssueSymbol>{symbol}</n:IssueSymbol><n:ReasonCode>{code}</n:ReasonCode>"
        f"<n:HaltDate>{day}</n:HaltDate><n:HaltTime>10:01:00.500</n:HaltTime>"
        f"<n:ResumptionDate>{resume_date}</n:ResumptionDate>"
        f"<n:ResumptionTradeTime>{resumed_at}</n:ResumptionTradeTime></item>"
    )


def sample(*items: str) -> bytes:
    return (
        '<rss version="2.0" xmlns:n="http://www.nasdaqtrader.com/"><channel>'
        f"<n:numItems>{len(items)}</n:numItems>{''.join(items)}</channel></rss>"
    ).encode()


def test_carryover_scheduled_and_overlapping_halts():
    payload = sample(
        item("AAPL", "T1", day="11/23/2026"),
        item("AAPL", "LUDP", "10:05:00"),
        item("MSFT", "LUDP", "11:15:00"),
        item("NVDA", "T3", "10:05:00"),
        item("TSLA", "T3", "00:00:01"),
        item("", "MWC1"),
    )
    report = parse_halt_report(payload, last_modified=format_datetime(NOW), observed_at=NOW)
    assert report.halted_symbols == {"AAPL", "MSFT", "TSLA"}
    assert report.market_halted
    assert report.valid_until == NOW + timedelta(seconds=120)


@pytest.mark.parametrize("payload", [b"", b"<rss>", sample().replace(b">0<", b">1<")])
def test_unusable_reports_fail(payload):
    with pytest.raises(ValueError):
        parse_halt_report(payload, last_modified=format_datetime(NOW), observed_at=NOW)


def test_refresh_receipt_does_not_renew_source_time():
    with pytest.raises(ValueError):
        parse_halt_report(
            sample(), last_modified=format_datetime(NOW), observed_at=NOW + timedelta(seconds=120)
        )
    report = parse_halt_report(
        sample(), last_modified=format_datetime(NOW), observed_at=NOW + timedelta(seconds=119)
    )
    assert report.valid_until == NOW + timedelta(seconds=120)
    assert not report.halted_symbols and not report.market_halted


def test_reported_authority_has_distinct_source_and_never_renews_as_a_stream():
    value = StatusEvidence(
        coin_id=1,
        provider_asset_id="alpaca-asset",
        state="normal",
        event_at=NOW,
        observed_at=NOW + timedelta(seconds=10),
        valid_until=NOW + timedelta(seconds=120),
        session_date=NOW.date(),
        admission_generation=1,
        continuity_generation=1,
        source=SOURCE,
        source_ref="a" * 64,
    )
    assert status_current(value, NOW + timedelta(seconds=119))
    assert not status_current(value, NOW + timedelta(seconds=120))
    assert not status_current(replace(value, continuity_current=True), NOW + timedelta(seconds=11))
    assert not status_current(
        replace(value, valid_until=NOW + timedelta(seconds=121)), NOW + timedelta(seconds=11)
    )
