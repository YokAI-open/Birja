from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.market_history import MarketHistoryQuery, MarketHistorySeries
from app.services.market_history import (
    HistoryBar,
    HistoryBatch,
    HistoryDataError,
    HistoryWindow,
    crypto_history_window,
    equity_history_window,
    normalize_history,
)
from app.services.stock_sessions import RegularSession


def _at(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp).replace(tzinfo=UTC)


def _session(
    day: str, open_hour: str | None = None, close_hour: str = "21:00", *, generation: int = 7
) -> RegularSession:
    return RegularSession(
        "NYSE",
        date.fromisoformat(day),
        _at(f"{day}T{open_hour}") if open_hour else None,
        _at(f"{day}T{close_hour}") if open_hour else None,
        date(2026, 1, 1),
        date(2026, 12, 31),
        generation,
    )


def _bars(window: HistoryWindow, price: str = "100.00") -> list[HistoryBar]:
    return [HistoryBar(slot.start, Decimal(price)) for slot in window.slots]


def test_strict_discriminated_round_trip() -> None:
    query = {
        "instrument": {
            "kind": "catalog",
            "catalog_id": "9223372036854775807",
            "listing_version": "5",
        },
        "range": "1M",
    }
    assert MarketHistoryQuery.model_validate(query).model_dump(mode="json") == query
    for selector in (
        {"kind": "catalog", "catalog_id": 4, "listing_version": "5"},
        {"kind": "catalog", "catalog_id": "04", "listing_version": "5"},
        {"kind": "catalog", "catalog_id": "4", "listing_version": "9223372036854775808"},
        {"kind": "featured", "symbol": "aapl"},
        {"kind": "crypto", "symbol": "BTC", "listing_version": "1"},
        {"kind": "stock", "symbol": "AAPL"},
    ):
        with pytest.raises(ValidationError):
            MarketHistoryQuery.model_validate({"instrument": selector, "range": "1D"})
    with pytest.raises(ValidationError):
        MarketHistoryQuery.model_validate(
            {"instrument": {"kind": "crypto", "symbol": "BTC"}, "range": "1Y"}
        )


@pytest.mark.parametrize(
    ("range_name", "interval", "count"), [("1D", 5, 288), ("1W", 60, 168), ("1M", 240, 180)]
)
def test_crypto_windows_and_exact_change(range_name, interval: int, count: int) -> None:
    window = crypto_history_window(range_name, _at("2026-11-27T20:02"))
    assert window.interval_minutes == interval
    assert len(window.slots) == count
    start, end = window.start_at, window.end_at
    for baseline, last, expected in [("100", "101.005", "1.00"), ("100", "101.015", "1.02")]:
        bars = _bars(window, baseline)
        bars.extend(
            [
                HistoryBar(start - window.step, Decimal(baseline)),
                HistoryBar(end, Decimal("700")),  # interval still building
            ]
        )
        bars[count - 1] = HistoryBar(end - window.step, Decimal(last))
        series = normalize_history(window, HistoryBatch(tuple(bars)))
        assert series.period_change_pct == Decimal(expected)
        assert series.day_change_pct == Decimal(expected)
        assert (series.coverage, series.timeliness, series.as_of) == ("complete", "on_time", end)
        assert MarketHistorySeries.model_validate_json(series.model_dump_json()) == series


def test_crypto_change_uses_a_fixed_24_hour_grid_and_never_bridges_missing_baseline() -> None:
    window = crypto_history_window("1W", _at("2026-11-27T20:02"))
    bars = _bars(window, "25")
    bars[-1] = HistoryBar(bars[-1].starts_at, Decimal("50"))
    baseline_start = bars[-1].starts_at - timedelta(days=1)
    bars = [bar for bar in bars if bar.starts_at != baseline_start]
    series = normalize_history(window, HistoryBatch(tuple(bars)))
    assert series.coverage == "partial" and series.timeliness == "on_time"
    assert sum(point.gap_before == "missing" for point in series.points) == 1
    assert series.day_change_pct is None and series.period_change_pct is None


def test_grace_and_delayed_contiguous_and_sparse_series() -> None:
    now = _at("2026-11-27T20:00:59")
    window = crypto_history_window("1D", now)
    bars = _bars(window)
    assert window.expected_through_at == _at("2026-11-27T19:55")
    within_grace = normalize_history(window, HistoryBatch(tuple(bars[:-1])))
    assert within_grace.timeliness == "on_time" and within_grace.coverage == "complete"
    assert within_grace.period_change_pct is None
    delayed = normalize_history(window, HistoryBatch(tuple(bars[:-2])))
    assert delayed.as_of == _at("2026-11-27T19:50")
    assert delayed.timeliness == "delayed" and delayed.coverage == "partial"
    assert all(point.gap_before is None for point in delayed.points)
    sparse = normalize_history(window, HistoryBatch(tuple(bars[0:3] + bars[4:-2])))
    assert sparse.timeliness == "delayed" and sparse.coverage == "partial"
    assert sparse.points[3].gap_before == "missing"


def test_equity_holiday_early_close_and_weekend_have_no_false_delay() -> None:
    friday = "2026-11-27"
    rows = [
        _session("2026-11-25", "14:30"),
        _session("2026-11-26"),  # Thanksgiving
        _session(friday, "14:30", "18:00"),
        _session("2026-11-28"),
        _session("2026-11-29"),
    ]
    window = equity_history_window(
        "1D", _at("2026-11-29T15:00"), "NYSE", rows, calendar_generation=7, identity_since=None
    )
    assert window is not None
    assert window.expected_through_at == _at("2026-11-27T18:00")
    assert window.prior_close_start == _at("2026-11-25T20:55")
    baseline = HistoryBar(window.prior_close_start, Decimal("100"))
    late = HistoryBar(_at("2026-11-27T18:00"), Decimal("800"))
    bars = [baseline, *_bars(window, "101"), late]
    series = normalize_history(window, HistoryBatch(tuple(bars)))
    assert len(series.points) == 42
    assert series.as_of == _at("2026-11-27T18:00")
    assert (series.coverage, series.timeliness) == ("complete", "on_time")
    assert series.day_change_pct == Decimal("1.00")
    assert series.adjustment == "split" and series.time_basis == "regular_session"
    old = normalize_history(window, HistoryBatch(tuple(bars[:-2])))
    assert old.timeliness == "delayed" and old.day_change_pct is None


def test_dst_and_missing_calendar_rows_preserve_gap_kind() -> None:
    # The clocks advance one hour between these sessions.
    rows = [
        _session("2026-03-03", "14:30"),
        _session("2026-03-04", "14:30"),
        _session("2026-03-05", "14:30"),
        _session("2026-03-06", "14:30"),
        _session("2026-03-07"),
        _session("2026-03-08"),
        _session("2026-03-09", "13:30", "20:00"),
    ]
    now = _at("2026-03-09T14:07")
    full = equity_history_window(
        "1W", now, "NYSE", rows, calendar_generation=7, identity_since=None
    )
    short = equity_history_window(
        "1W", now, "NYSE", rows[:4] + rows[5:], calendar_generation=7, identity_since=None
    )
    assert full is not None and short is not None
    assert full.expected_through_at == _at("2026-03-09T14:00")
    assert full.prior_close_start == _at("2026-03-06T20:30")
    assert short.prior_close_start is None
    good = normalize_history(full, HistoryBatch(tuple(_bars(full))))
    interrupted = normalize_history(short, HistoryBatch(tuple(_bars(short))))
    assert good.points[-1].starts_at == interrupted.points[-1].starts_at == _at("2026-03-09T13:30")
    assert good.points[-1].gap_before == "closed"
    assert interrupted.points[-1].gap_before == "missing"
    assert interrupted.timeliness == "on_time" and interrupted.coverage == "partial"
    assert interrupted.period_change_pct is None


def test_reused_ticker_excludes_wrong_version_and_unclosed_intervals() -> None:
    rows = [_session("2026-11-23", "14:30"), _session("2026-11-24", "14:30")]
    window = equity_history_window(
        "1D",
        _at("2026-11-24T15:02"),
        "NYSE",
        rows,
        calendar_generation=7,
        identity_since=_at("2026-11-24T14:47"),
    )
    assert window is not None and window.request_start_at == _at("2026-11-24T14:47")
    bars = [
        HistoryBar(_at("2026-11-23T20:55"), Decimal("10")),
        *_bars(window),
        HistoryBar(_at("2026-11-24T15:00"), Decimal("900")),
    ]
    series = normalize_history(window, HistoryBatch(tuple(bars)))
    assert [point.starts_at for point in series.points] == [
        _at("2026-11-24T14:50"),
        _at("2026-11-24T14:55"),
    ]
    assert series.points[0].gap_before == "missing"
    assert series.coverage == "partial" and series.timeliness == "on_time"
    assert series.day_change_pct is None and series.period_change_pct is None
    assert (
        equity_history_window(
            "1D", _at("2026-11-24T15:02"), "NYSE", rows, calendar_generation=8, identity_since=None
        )
        is None
    )


def test_missing_reference_coverage_makes_timeliness_unknown() -> None:
    window = equity_history_window(
        "1D",
        _at("2026-11-24T16:00"),
        "NYSE",
        [_session("2026-11-23", "14:30")],
        calendar_generation=7,
        identity_since=None,
    )
    assert window is not None
    series = normalize_history(window, HistoryBatch(tuple(_bars(window))))
    assert series.expected_through_at is None
    assert series.coverage == "partial" and series.timeliness == "unknown"


def test_identical_duplicates_collapse_and_conflicting_rows_fail() -> None:
    window = crypto_history_window("1D", _at("2026-11-27T20:02"))
    bar = HistoryBar(window.slots[-1].start, Decimal("0.00000001"))
    series = normalize_history(window, HistoryBatch((bar, bar)))
    assert len(series.points) == 1
    assert series.model_dump(mode="json")["points"][0]["close"] == "0.00000001"
    with pytest.raises(HistoryDataError, match="contradictory"):
        normalize_history(window, HistoryBatch((bar, HistoryBar(bar.starts_at, Decimal("50")))))


@pytest.mark.parametrize("close", ["0", "-2", "NaN", "Infinity", "1E-99", "1E90"])
def test_invalid_decimal_close_is_rejected(close: str) -> None:
    window = crypto_history_window("1M", _at("2026-11-27T20:02"))
    bar = HistoryBar(window.slots[0].start, Decimal(close))
    with pytest.raises(HistoryDataError, match="historical close"):
        normalize_history(window, HistoryBatch((bar,)))


def test_two_pages_with_continuation_are_partial_even_when_on_time() -> None:
    window = crypto_history_window("1M", _at("2026-11-27T20:02"))
    partial = normalize_history(window, HistoryBatch(tuple(_bars(window)), complete=False))
    assert (partial.coverage, partial.timeliness) == ("partial", "on_time")
    assert partial.period_change_pct is None
