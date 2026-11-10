"""Official dated schedules and synthetic operator authority, never real permission.

2026 dates: https://www.nyse.com/trade/hours-calendars and
https://www.nasdaq.com/market-activity/stock-market-holiday-schedule.
"""

from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.models.stock import StockDataAdmission
from app.services.stock_quote_rules import ValidatedStockQuote
from app.services.stock_sessions import (
    build_sessions,
    discovery_eligibility,
    load_sessions,
    persist_sessions,
    session_at,
)
from tests.test_stock_admission import admitted


def evidence(now: datetime):
    return replace(
        admitted("calendar"),
        reviewed_at=now - timedelta(hours=1),
        valid_from=now - timedelta(hours=2),
        valid_until=now + timedelta(hours=8),
        calendar={
            "exchanges": ["XNYS", "XNAS"],
            "version": "exchange-calendars-4.13.2/official-2026",
            "sources": [
                "https://www.nyse.com/trade/hours-calendars",
                "https://www.nasdaq.com/market-activity/stock-market-holiday-schedule",
            ],
            "review_valid_until": (now + timedelta(hours=8)).isoformat(),
            "coverage_start": (now.date() - timedelta(days=45)).isoformat(),
            "coverage_end": (now.date() + timedelta(days=90)).isoformat(),
            "overrides": [],
        },
    )


NOW = datetime(2026, 11, 10, 15, tzinfo=UTC)


@pytest.mark.parametrize("exchange", ["NYSE", "NASDAQ"])
@pytest.mark.parametrize(
    "stamp,state",
    [
        ("2026-11-10T14:29:59+00:00", "closed"),
        ("2026-11-10T14:30:00+00:00", "open"),
        ("2026-11-10T20:59:59+00:00", "open"),
        ("2026-11-10T21:00:00+00:00", "closed"),
        ("2026-11-26T16:00:00+00:00", "closed"),
        ("2026-11-27T17:59:59+00:00", "open"),
        ("2026-11-27T18:00:00+00:00", "closed"),
        ("2026-11-28T16:00:00+00:00", "closed"),
    ],
)
def test_current_and_next_verified_session(exchange: str, stamp: str, state: str) -> None:
    now = datetime.fromisoformat(stamp)
    authority = evidence(now)
    rows = build_sessions(now, authority)
    assert len(rows) == 272
    result = session_at(exchange, now, rows, authority)
    assert result.state == state
    assert result.current is not None
    assert result.next_session is not None
    assert result.next_session.opens_at > now
    assert result.valid_until == now + timedelta(hours=8)
    assert result.executable is False


@pytest.mark.parametrize(
    "day,hour", [("2026-03-06", 14), ("2026-03-09", 13), ("2026-10-30", 13), ("2026-11-02", 14)]
)
def test_dst_is_exchange_local(day: str, hour: int) -> None:
    now = datetime.fromisoformat(day + "T15:00:00+00:00")
    authority = evidence(now)
    result = session_at("NYSE", now, build_sessions(now, authority), authority)
    assert result.state == "open"
    assert result.current.opens_at.hour == hour


def test_generation_replacement_never_reuses_old_rows() -> None:
    authority = evidence(NOW)
    rows = build_sessions(NOW, authority)
    assert session_at("NYSE", NOW, rows, authority).state == "open"
    newer = replace(authority, generation=authority.generation + 1)
    assert session_at("NYSE", NOW, rows, newer).state == "unknown"
    assert session_at("NYSE", NOW, build_sessions(NOW, newer), newer).state == "open"
    forged = [replace(row, calendar_admission_generation=99) for row in rows]
    assert session_at("NYSE", NOW, forged, authority).state == "unknown"
    assert session_at("NYSE", NOW, build_sessions(NOW, authority), authority).state == "open"


@pytest.mark.parametrize(
    "problem",
    [
        "missing",
        "expired_review",
        "old_review",
        "expired_coverage",
        "revoked",
        "no_next",
        "duplicate",
        "missing_today",
        "forged_bounds",
    ],
)
def test_uncertain_authority_or_rows_are_unknown(problem: str) -> None:
    authority = evidence(NOW)
    rows = build_sessions(NOW, authority)
    if problem == "missing":
        authority = None
    elif problem == "expired_review":
        authority = replace(
            authority, calendar={**authority.calendar, "review_valid_until": NOW.isoformat()}
        )
    elif problem == "old_review":
        authority = replace(authority, reviewed_at=NOW - timedelta(hours=25))
    elif problem == "expired_coverage":
        authority = replace(
            authority, calendar={**authority.calendar, "coverage_end": "2026-11-09"}
        )
    elif problem == "revoked":
        authority = replace(authority, state="revoked")
    elif problem == "no_next":
        rows = [row for row in rows if row.session_date <= NOW.date()]
    elif problem == "duplicate":
        rows = rows + rows
    elif problem == "missing_today":
        rows = [row for row in rows if row.session_date != NOW.date()]
    else:
        rows = [
            replace(row, closes_at=row.closes_at + timedelta(minutes=1)) if row.closes_at else row
            for row in rows
        ]
    assert session_at("NYSE", NOW, rows, authority).state == "unknown"


@pytest.mark.parametrize("state", ["closed", "shortened"])
def test_migrator_override_requires_new_matching_derived_rows(state: str) -> None:
    now = NOW.replace(hour=19)
    authority = evidence(now)
    old = build_sessions(now, authority)
    override = {
        "exchange": "XNYS",
        "date": "2026-11-10",
        "state": state,
        "source": "https://www.nyse.com/trade/hours-calendars",
    }
    if state == "shortened":
        override.update(opens_at="2026-11-10T14:30:00+00:00", closes_at="2026-11-10T18:00:00+00:00")
    changed = replace(
        authority, generation=5, calendar={**authority.calendar, "overrides": [override]}
    )
    assert session_at("NYSE", now, old, changed).state == "unknown"
    forged = [replace(row, calendar_admission_generation=5) for row in old]
    assert session_at("NYSE", now, forged, changed).state == "unknown"
    refreshed = build_sessions(now, changed)
    result = session_at("NYSE", now, refreshed, changed)
    assert result.state == "closed"
    assert result.executable is False
    assert session_at("NASDAQ", now, refreshed, changed).state == "open"


def test_scheduler_rows_cannot_supply_missing_authority() -> None:
    rows = build_sessions(NOW, evidence(NOW))
    assert rows
    assert all(not hasattr(row, "review_valid_until") for row in rows)
    assert session_at("NYSE", NOW, rows, None).state == "unknown"
    assert build_sessions(NOW, None) == []
    assert session_at("OTC", NOW, rows, evidence(NOW)).state == "unknown"
    assert session_at("NYSE", NOW.replace(tzinfo=None), rows, evidence(NOW)).state == "unknown"


def test_independent_quote_status_actions_never_enable_stock_execution() -> None:
    authority = evidence(NOW)
    session = session_at("NYSE", NOW, build_sessions(NOW, authority), authority)
    quote = ValidatedStockQuote(
        1, "JPM", Decimal("100"), Decimal("102"), Decimal("101"), NOW, NOW, NOW.date(), 4
    )
    result = discovery_eligibility(session, quote, NOW)
    assert result.calendar == "open"
    assert result.quote_valid
    assert result.status == result.actions == "unknown"
    assert not result.executable
    yesterday = replace(
        quote, event_at=NOW - timedelta(days=1), session_date=NOW.date() - timedelta(days=1)
    )
    assert not discovery_eligibility(session, yesterday, NOW).quote_valid
    assert not discovery_eligibility(
        session, replace(quote, event_at=NOW - timedelta(seconds=120)), NOW
    ).quote_valid
    assert not discovery_eligibility(session, None, NOW).quote_valid
    assert not discovery_eligibility(
        session, quote, NOW, status="normal", actions="clear"
    ).executable


@pytest.mark.parametrize("day,close", [("2026-11-15", "18:00"), ("2026-11-27", "19:00")])
def test_shortened_override_cannot_invent_or_extend_official_session(day: str, close: str) -> None:
    authority = evidence(NOW)
    override = {
        "exchange": "XNYS",
        "date": day,
        "state": "shortened",
        "opens_at": day + "T14:30:00+00:00",
        "closes_at": day + "T" + close + ":00+00:00",
        "source": "https://www.nyse.com/trade/hours-calendars",
    }
    changed = replace(authority, calendar={**authority.calendar, "overrides": [override]})
    assert build_sessions(NOW, changed) == []


def test_missing_intervening_derived_date_cannot_skip_next_session() -> None:
    now = NOW.replace(hour=22)
    authority = evidence(now)
    rows = [
        row
        for row in build_sessions(now, authority)
        if row.session_date.isoformat() != "2026-11-11"
    ]
    assert session_at("NYSE", now, rows, authority).state == "unknown"


async def test_exact_persist_load_refresh_and_committed_authority_replacement(
    engine: AsyncEngine, clean_stock_discovery: None
) -> None:
    now = datetime.now(UTC)
    authority = evidence(now)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        db.add(StockDataAdmission(**asdict(authority)))
        await db.commit()
        rows = build_sessions(now, authority)
        assert await persist_sessions(db, rows, authority, now) == 272
        await db.commit()
        loaded = await load_sessions(db, now)
        assert sorted(loaded, key=lambda r: (r.exchange, r.session_date)) == sorted(
            rows, key=lambda r: (r.exchange, r.session_date)
        )
        assert await persist_sessions(db, rows, authority, now) == 272
        await db.commit()
        changed = replace(authority, generation=5)
        async with factory() as admin:
            await admin.execute(
                update(StockDataAdmission)
                .where(StockDataAdmission.product == "calendar")
                .values(generation=5)
            )
            await admin.commit()
        assert await persist_sessions(db, rows, authority, now) == 0
        assert session_at("NYSE", now, loaded, changed).state == "unknown"
        new_rows = build_sessions(now, changed)
        assert await persist_sessions(db, new_rows, changed, now) == 272
        await db.commit()
        refreshed = await load_sessions(db, now)
        assert session_at("NYSE", now, refreshed, changed).state != "unknown"
        stored = (
            await db.execute(
                select(StockDataAdmission).where(StockDataAdmission.product == "calendar")
            )
        ).scalar_one()
        assert stored.reviewed_at == authority.reviewed_at
        assert stored.calendar == authority.calendar


async def test_persist_rejects_forged_rows_and_expired_database_review(
    engine: AsyncEngine, clean_stock_discovery: None
) -> None:
    now = datetime.now(UTC)
    earlier = now - timedelta(hours=9)
    authority = evidence(earlier)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        db.add(StockDataAdmission(**asdict(authority)))
        await db.commit()
        rows = build_sessions(earlier, authority)
        assert rows
        assert await persist_sessions(db, rows, authority, earlier) == 0
        fresh = evidence(now)
        assert await persist_sessions(db, rows[:-1], fresh, now) == 0
        fresh_rows = build_sessions(now, fresh)
        assert (
            await persist_sessions(db, fresh_rows, replace(fresh, retention_allowed=False), now)
            == 0
        )
        assert await load_sessions(db, now) == []
        assert await load_sessions(db, now.replace(tzinfo=None)) == []
