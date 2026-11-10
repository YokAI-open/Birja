"""Synthetic quotes do not establish feed access or calendar authority."""

from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.services.stock_quote_rules import (
    RawStockQuote,
    StockMapping,
    quote_eligibility,
    validate_quote,
)

NOW = datetime(2026, 11, 10, 15, tzinfo=UTC)
MAPPING = StockMapping(16, "AAPL", "synthetic-asset", NOW - timedelta(days=1), "NASDAQ")


def raw(**changes: object) -> RawStockQuote:
    return replace(
        RawStockQuote(MAPPING, Decimal("100.00000001"), Decimal("100.00000002"), NOW, ["R"]),
        **changes,
    )


@dataclass(frozen=True)
class Session:
    session_date: date = NOW.date()
    opens_at: datetime | None = NOW.replace(hour=14, minute=30)
    closes_at: datetime | None = NOW.replace(hour=21)


def test_exact_half_even_mid_and_distinct_receipt() -> None:
    result = validate_quote(raw(), NOW + timedelta(seconds=1), 4)
    assert result is not None
    assert result.bid == Decimal("100.00000001")
    assert result.ask == Decimal("100.00000002")
    assert result.mid == Decimal("100.00000002")
    assert result.event_at == NOW
    assert result.collected_at == NOW + timedelta(seconds=1)
    assert result.session_date == NOW.date()
    assert result.admission_generation == 4
    even = validate_quote(raw(bid=Decimal("100"), ask=Decimal("100.00000001")), NOW, 4)
    assert even is not None and even.mid == Decimal("100")


@pytest.mark.parametrize(
    "changes",
    [
        {"bid": Decimal("0")}, {"ask": Decimal("-1")},
        {"bid": Decimal("NaN")}, {"ask": Decimal("Infinity")},
        {"bid": 100.0}, {"ask": "100"}, {"bid": True},
        {"ask": Decimal("1e12")}, {"bid": Decimal("101")},
        {"bid": Decimal("0.000000001")}, {"ask": Decimal("100.000000021")},
        {"conditions": []}, {"conditions": None}, {"conditions": "R"},
        {"conditions": ["R", "H"]}, {"conditions": ["?"]},
        {"conditions": ["R", "R", "R"]},
        {"bid_exchange": "Q"}, {"ask_exchange": "N"},
        {"tape": "A"}, {"source": "other"}, {"feed": "sip"},
        {"bid_size": 0}, {"ask_size": True}, {"ask_size": -1},
        {"event_at": NOW.replace(tzinfo=None)},
        {"event_at": NOW.astimezone(timezone(timedelta(hours=1)))},
        {"event_at": NOW + timedelta(microseconds=1)},
        {"event_at": NOW - timedelta(seconds=120)},
        {"mapping": replace(MAPPING, provider_asset_id=None)},
        {"mapping": replace(MAPPING, provider_verified_at=None)},
        {"mapping": replace(MAPPING, provider_verified_at=NOW + timedelta(seconds=1))},
        {"mapping": replace(MAPPING, symbol="FAKE")},
        {"mapping": replace(MAPPING, coin_id=True)},
    ],
)
def test_refuse_invalid_source_values(changes: dict[str, object]) -> None:
    assert validate_quote(raw(**changes), NOW, 4) is None


def test_regular_condition_can_apply_to_both_sides() -> None:
    assert validate_quote(raw(conditions=["R", "R"]), NOW, 4) is not None


@pytest.mark.parametrize("generation", [0, -1, True])
def test_invalid_generation(generation: int) -> None:
    assert validate_quote(raw(), NOW, generation) is None


@pytest.mark.parametrize(
    "age,eligible", [(timedelta(0), True), (timedelta(seconds=119, microseconds=999999), True),
                     (timedelta(seconds=120), False), (timedelta(microseconds=-1), False)],
)
def test_exact_age_boundary(age: timedelta, eligible: bool) -> None:
    quote = validate_quote(raw(), NOW, 4)
    assert quote is not None
    assert quote_eligibility(quote, Session(), NOW + age) is eligible


def test_previous_session_closed_unknown_and_exact_boundaries() -> None:
    quote = validate_quote(raw(), NOW, 4)
    assert quote is not None
    assert quote_eligibility(quote, Session(opens_at=NOW), NOW)
    assert not quote_eligibility(quote, Session(closes_at=NOW), NOW)
    assert not quote_eligibility(quote, Session(opens_at=NOW + timedelta(microseconds=1)), NOW)
    assert not quote_eligibility(quote, Session(session_date=NOW.date()-timedelta(days=1)), NOW)
    assert not quote_eligibility(quote, Session(opens_at=None, closes_at=None), NOW)
    assert not quote_eligibility(quote, None, NOW)
    assert not quote_eligibility(quote, Session(), NOW.replace(tzinfo=None))
    assert not quote_eligibility(replace(quote, event_at=NOW-timedelta(days=1)), Session(), NOW)
