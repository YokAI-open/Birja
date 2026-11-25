from dataclasses import replace
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import httpx
import pytest
from sqlalchemy import text

from app.core.config import SchedulerSettings
from app.services.stock_halts import SOURCE, catalog_report_state, parse_halt_report
from app.services.stock_sessions import RegularSession, SessionDecision
from app.services.stock_trading_rules import StatusEvidence, status_current
from app.tasks import stock_halts
from tests.test_stock_catalog_finance_migration import finance_0025 as finance_0025
from tests.test_stock_catalog_sql_authority import execution_market as execution_market
from tests.test_stock_catalog_sql_authority import finance_0026 as finance_0026

NOW = datetime(2026, 11, 24, 16, tzinfo=UTC)


def item(
    symbol: str, code: str, resumed_at: str = "", day: str = "11/24/2026", market: str = ""
) -> str:
    resume_date = "11/24/2026" if resumed_at else ""
    return (
        f"<item><n:IssueSymbol>{symbol}</n:IssueSymbol><n:ReasonCode>{code}</n:ReasonCode>"
        f"<n:Market>{market}</n:Market>"
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


def test_catalog_report_matches_venue_and_dated_alias():
    report = parse_halt_report(
        sample(item("FQA", "T1", market="NASDAQ"), item("NYSE1", "T1", market="NON-NASDAQ")),
        last_modified=format_datetime(NOW),
        observed_at=NOW,
    )
    before = NOW - timedelta(hours=2)
    assert catalog_report_state(report, "NASDAQ", {"FQA": before}) == "halted"
    assert catalog_report_state(report, "NYSE", {"FQA": before}) == "normal"
    assert catalog_report_state(report, "NASDAQ", {"FQR": before}) == "normal"
    assert catalog_report_state(report, "NASDAQ", {"FQR": before, "FQA": before}) == "halted"
    assert catalog_report_state(report, "NASDAQ", {"FQA": NOW}) is None
    assert catalog_report_state(report, "NYSE", {"NYSE1": before}) is None
    assert catalog_report_state(report, "NASDAQ", {"NYSE1": before}) == "normal"


def test_catalog_report_market_halt_applies_across_both_venues():
    report = parse_halt_report(
        sample(item("", "MWC1")), last_modified=format_datetime(NOW), observed_at=NOW
    )
    assert catalog_report_state(report, "NASDAQ", {"FQR": NOW}) == "halted"
    assert catalog_report_state(report, "NYSE", {"NY1": NOW}) == "halted"


def test_catalog_report_uncertain_notice_leaves_other_issues_eligible():
    report = parse_halt_report(
        sample(item("FQA", "T1", day="bad-date", market="NYSE")),
        last_modified=format_datetime(NOW),
        observed_at=NOW,
    )
    assert catalog_report_state(report, "NYSE", {"FQA": NOW}) is None
    assert catalog_report_state(report, "NYSE", {"FQB": NOW}) == "normal"


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


async def test_catalog_report_loop_reuses_one_report_and_refuses_ambiguous_notice(
    finance_0026, execution_market, redis_client, monkeypatch
):
    case = execution_market
    target = (case["catalog"], case["listing"])
    session = RegularSession(
        "NASDAQ", case["session"], case["opens"], case["end"], case["session"], case["session"], 1
    )
    # This test uses a short artificial session to exercise the projected DB
    # rows at any local time. The exchange calendar has its own contract tests.
    monkeypatch.setattr(stock_halts, "_open_exchanges", lambda *_a, **_k: {"NASDAQ"})
    monkeypatch.setattr(
        stock_halts,
        "session_at",
        lambda *_a, **_k: SessionDecision("open", session, None, case["end"]),
    )
    monkeypatch.setattr(stock_halts, "_catalog_targets", AsyncMock(return_value=(target,)))
    now = datetime.now(UTC)
    started = (now - timedelta(minutes=5)).astimezone(ZoneInfo("America/New_York"))
    item_xml = item("FQA", "T1", day=started.strftime("%m/%d/%Y"), market="NASDAQ").replace(
        "10:01:00.500", started.strftime("%H:%M:%S")
    )
    calls = []

    async def report_response(request):
        calls.append(request)
        return httpx.Response(
            200,
            headers={"Last-Modified": format_datetime(now - timedelta(seconds=1))},
            content=sample(item_xml),
        )

    async with finance_0026.begin() as db:
        await db.execute(text("DELETE FROM stock_catalog_status WHERE coin_id=:c"), case)
    settings = SchedulerSettings.model_construct(
        env="test",
        stock_data_enabled=True,
        stock_data_account=case["account"],
        stock_data_server=case["server"],
    )
    window = stock_halts.CatalogHaltWindow()
    await redis_client.delete(stock_halts._POLL_KEY)
    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(report_response)) as http:
            args = dict(
                sessionmaker=finance_0026,
                redis=redis_client,
                http=http,
                settings=settings,
                catalog_window=window,
                catalog_redis=redis_client,
            )
            assert (await stock_halts.run_stock_halt_cycle(**args)).accepted == 1
            assert (await stock_halts.run_stock_halt_cycle(**args)).accepted == 0
        assert len(calls) == 1
        async with finance_0026.begin() as db:
            status = await db.scalar(
                text("SELECT state FROM stock_catalog_status WHERE coin_id=:c"), case
            )
            assert status == "halted"
            assert window.report is not None
            unknown = replace(
                window.report, notices=(replace(window.report.notices[0], market=None),)
            )
            assert (
                await stock_halts._project_catalog_halt(
                    db,
                    target,
                    unknown,
                    account=case["account"],
                    server=case["server"],
                    allow_fixture=True,
                )
                == 0
            )
            assert await db.scalar(
                text(
                    "SELECT valid_until < clock_timestamp() "
                    "FROM stock_catalog_status WHERE coin_id=:c"
                ),
                case,
            )
            # A report refresh also expires old per-issue states that were
            # outside the small projection page for that tick.
            await db.execute(
                text(
                    "UPDATE stock_catalog_status SET valid_until=event_at + interval '100 seconds' "
                    "WHERE coin_id=:c"
                ),
                case,
            )
            newer = replace(
                window.report,
                published_at=now,
                observed_at=window.report.observed_at + timedelta(microseconds=1),
            )
            await stock_halts._expire_prior_catalog_reports(
                db, newer, account=case["account"], server=case["server"]
            )
            assert await db.scalar(
                text(
                    "SELECT valid_until = observed_at + interval '0.000001 seconds' "
                    "FROM stock_catalog_status WHERE coin_id=:c"
                ),
                case,
            )
    finally:
        await redis_client.delete(stock_halts._POLL_KEY)
