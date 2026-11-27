"""Build bounded windows and normalize completed historical prices."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Literal
from zoneinfo import ZoneInfo

from app.schemas.market_history import (
    HistoryCoverage,
    HistoryInterval,
    HistoryRange,
    HistorySource,
    HistoryTimeliness,
    MarketHistoryPoint,
    MarketHistorySeries,
)
from app.services.stock_sessions import EXCHANGES, RegularSession

_UTC_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_NEW_YORK = ZoneInfo("America/New_York")
_GRACE = timedelta(seconds=60)
_DAY = timedelta(days=1)
_CRYPTO_MINUTES: dict[HistoryRange, Literal[5, 60, 240]] = {"1D": 5, "1W": 60, "1M": 240}
_REFERENCE_MINUTES: dict[HistoryRange, Literal[5, 60, 1440]] = {"1D": 5, "1W": 60, "1M": 1440}
_DAYS: dict[HistoryRange, int] = {"1D": 1, "1W": 7, "1M": 30}


@dataclass(frozen=True, slots=True)
class HistoryBar:
    starts_at: datetime
    close: Decimal


@dataclass(frozen=True, slots=True)
class HistoryBatch:
    bars: tuple[HistoryBar, ...]
    complete: bool = True


@dataclass(frozen=True, slots=True)
class _Slot:
    start: datetime
    session: date | None = None


@dataclass(frozen=True, slots=True)
class HistoryWindow:
    range: HistoryRange
    source: HistorySource
    interval_minutes: HistoryInterval
    start_at: datetime
    end_at: datetime
    request_start_at: datetime
    expected_through_at: datetime | None
    slots: tuple[_Slot, ...]
    coverage_known: bool
    reference_session: date | None = None
    reference_close_at: datetime | None = None
    calendar_dates: frozenset[date] = frozenset()
    prior_close_start: datetime | None = None
    expected_reference_start: datetime | None = None
    identity_since: datetime | None = None

    @property
    def step(self) -> timedelta:
        return timedelta(minutes=self.interval_minutes)


class HistoryDataError(ValueError):
    """Rejected history series."""


def _utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        raise HistoryDataError("history timestamps must include an offset")
    return value.astimezone(UTC)


def _grid(start: datetime, end: datetime, step: timedelta) -> Iterator[datetime]:
    for index in range((end - start) // step):
        yield start + index * step


def crypto_history_window(
    range: HistoryRange, now: datetime, source: Literal["kraken", "coin_metrics"] = "kraken"
) -> HistoryWindow:
    now = _utc(now)
    interval = _REFERENCE_MINUTES[range] if source == "coin_metrics" else _CRYPTO_MINUTES[range]
    step = timedelta(minutes=interval)
    end = _UTC_EPOCH + ((now - _UTC_EPOCH) // step) * step
    start = end - timedelta(days=_DAYS[range])
    expected_end = _UTC_EPOCH + ((now - _GRACE - _UTC_EPOCH) // step) * step
    return HistoryWindow(
        range=range,
        source=source,
        interval_minutes=interval,
        start_at=start,
        end_at=end,
        request_start_at=min(start, end - _DAY) - 2 * step,
        expected_through_at=expected_end,
        slots=tuple(_Slot(start) for start in _grid(start, end, step)),
        coverage_known=True,
    )


def _calendar_days(first: date, last: date) -> Iterator[date]:
    for offset in range((last - first).days + 1):
        yield first + timedelta(days=offset)


def _admitted_sessions(
    sessions: Iterable[RegularSession], exchange: str, generation: int, first: date, last: date
) -> dict[date, RegularSession]:
    days: dict[date, RegularSession] = {}
    conflicting: set[date] = set()
    for row in sessions:
        day = row.session_date
        if (
            row.exchange != exchange
            or row.calendar_admission_generation != generation
            or not first <= day <= last
            or not row.coverage_start <= day <= row.coverage_end
        ):
            continue
        if row.opens_at is not None and row.closes_at is not None:
            opens, closes = _utc(row.opens_at), _utc(row.closes_at)
            valid = opens.astimezone(_NEW_YORK).date() == closes.astimezone(
                _NEW_YORK
            ).date() == day and timedelta(0) < closes - opens <= timedelta(hours=7)
        else:
            valid = row.opens_at is None and row.closes_at is None
        if not valid or (day in days and days[day] != row):
            conflicting.add(day)
        days[day] = row
    return {day: row for day, row in days.items() if day not in conflicting}


def equity_history_window(
    range: HistoryRange,
    now: datetime,
    exchange: str,
    sessions: Iterable[RegularSession],
    *,
    calendar_generation: int,
    identity_since: datetime | None,
) -> HistoryWindow | None:
    now = _utc(now)
    identity_since = _utc(identity_since) if identity_since is not None else None
    if exchange not in EXCHANGES or calendar_generation < 1:
        return None
    today = now.astimezone(_NEW_YORK).date()
    # Coverage beyond 45 days cannot satisfy the requested window or its preceding baseline.
    admitted = _admitted_sessions(
        sessions, exchange, calendar_generation, today - timedelta(days=45), today
    )
    previous_sessions = sorted(
        (row for row in admitted.values() if row.opens_at is not None and row.opens_at <= now),
        key=lambda row: row.session_date,
        reverse=True,
    )
    if not previous_sessions:
        return None
    reference = previous_sessions[0]
    if reference.opens_at is None or reference.closes_at is None:
        return None
    ref_day = reference.session_date
    end = min(now, _utc(reference.closes_at))
    if identity_since is not None and end <= identity_since:
        return None
    start_day = ref_day - timedelta(days=_DAYS[range] - 1)
    start = (
        _utc(reference.opens_at)
        if range == "1D"
        else datetime.combine(start_day, time.min, _NEW_YORK).astimezone(UTC)
    )
    interval: Literal[5, 30] = 5 if range == "1D" else 30
    step = timedelta(minutes=interval)
    slots: list[_Slot] = []
    for day in _calendar_days(start_day, ref_day):
        row = admitted.get(day)
        if row is not None and row.opens_at is not None and row.closes_at is not None:
            slots.extend(
                _Slot(slot, day)
                for slot in _grid(_utc(row.opens_at), min(end, _utc(row.closes_at)), step)
            )
    reference_known = all(day in admitted for day in _calendar_days(ref_day, today))
    expected = [slot.start + step for slot in slots if slot.start + step <= now - _GRACE]
    prior_start = None
    if len(previous_sessions) > 1:
        prior = previous_sessions[1]
        if prior.opens_at is not None and prior.closes_at is not None:
            candidate = _utc(prior.closes_at) - step
            if (
                candidate >= prior.opens_at
                and (candidate - prior.opens_at) % step == timedelta(0)
                and all(day in admitted for day in _calendar_days(prior.session_date, ref_day))
            ):
                prior_start = candidate
    request_start = min(start, prior_start) if prior_start is not None else start
    return HistoryWindow(
        range=range,
        source="alpaca_iex",
        interval_minutes=interval,
        start_at=start,
        end_at=end,
        request_start_at=max(request_start, identity_since) if identity_since else request_start,
        expected_through_at=expected[-1] if reference_known and expected else None,
        slots=tuple(slots),
        coverage_known=reference_known
        and all(day in admitted for day in _calendar_days(start_day, ref_day)),
        reference_session=ref_day,
        reference_close_at=_utc(reference.closes_at),
        calendar_dates=frozenset(admitted),
        prior_close_start=prior_start,
        expected_reference_start=next(
            (slot.start for slot in reversed(slots) if slot.session == ref_day), None
        ),
        identity_since=identity_since,
    )


def validate_close(value: object) -> Decimal:
    if type(value) is int:
        value = Decimal(value)
    if not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
        raise HistoryDataError("invalid historical close")
    exponent = value.as_tuple().exponent
    if not isinstance(exponent, int) or exponent < -12 or value.adjusted() >= 18:
        raise HistoryDataError("historical close exceeds supported precision")
    return value


def _observations(window: HistoryWindow, batch: HistoryBatch) -> dict[datetime, Decimal]:
    observations: dict[datetime, Decimal] = {}
    for bar in batch.bars:
        start = _utc(bar.starts_at)
        close = validate_close(bar.close)
        if (
            start < window.request_start_at
            or start + window.step > window.end_at
            or (window.identity_since is not None and start < window.identity_since)
        ):
            continue
        if start in observations and observations[start] != close:
            raise HistoryDataError("contradictory historical closes")
        observations[start] = close
    return observations


def _percentage(close: Decimal, baseline: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 64
        change = ((close / baseline - 1) * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return abs(change) if change.is_zero() else change


def _changes(
    window: HistoryWindow,
    observations: dict[datetime, Decimal],
    points: list[MarketHistoryPoint],
    timeliness: HistoryTimeliness,
    coverage: HistoryCoverage,
) -> tuple[Decimal | None, Decimal | None]:
    if not points or timeliness != "on_time":
        return None, None
    final = points[-1]
    daily_start: datetime | None
    period_start: datetime | None
    if window.source != "alpaca_iex":
        daily_start = final.starts_at - _DAY
        period_start = window.start_at - window.step
    else:
        if (
            window.expected_reference_start is None
            or final.starts_at.astimezone(_NEW_YORK).date() != window.reference_session
            or (
                window.end_at == window.reference_close_at
                and final.ends_at != window.reference_close_at
            )
        ):
            return None, None
        daily_start = window.prior_close_start
        period_start = window.slots[0].start if window.slots else None
    daily_base = observations.get(daily_start) if daily_start is not None else None
    period_base = observations.get(period_start) if period_start is not None else None
    day = _percentage(final.close, daily_base) if daily_base is not None else None
    period = (
        _percentage(final.close, period_base)
        if coverage == "complete"
        and period_base is not None
        and period_start is not None
        and period_start < final.starts_at
        and (window.source == "alpaca_iex" or final.ends_at == window.end_at)
        else None
    )
    return day, period


def normalize_history(window: HistoryWindow, batch: HistoryBatch) -> MarketHistorySeries:
    observations = _observations(window, batch)
    points: list[MarketHistoryPoint] = []
    previous: _Slot | None = None
    previous_index: int | None = None
    coverage_short = not (window.coverage_known and batch.complete)
    for index, slot in enumerate(window.slots):
        close = observations.get(slot.start)
        end = slot.start + window.step
        if close is None:
            coverage_short |= (
                window.expected_through_at is not None and end <= window.expected_through_at
            )
            continue
        gap: Literal["missing", "closed"] | None = None
        if previous is not None and previous_index is not None:
            if index != previous_index + 1:
                gap = "missing"
            elif (
                previous.session is not None
                and slot.session is not None
                and previous.session != slot.session
            ):
                continuity = all(
                    day in window.calendar_dates
                    for day in _calendar_days(previous.session, slot.session)
                )
                gap = "closed" if continuity else "missing"
        elif index:
            gap = "missing"
        points.append(
            MarketHistoryPoint(starts_at=slot.start, ends_at=end, close=close, gap_before=gap)
        )
        previous, previous_index = slot, index

    if len(points) > 512:
        raise HistoryDataError("too many normalized historical points")
    as_of = points[-1].ends_at if points else None
    timeliness: HistoryTimeliness = "unknown"
    if as_of is not None and window.expected_through_at is not None:
        timeliness = "on_time" if as_of >= window.expected_through_at else "delayed"
    coverage: HistoryCoverage = (
        "empty" if not points else "partial" if coverage_short else "complete"
    )
    day, period = _changes(window, observations, points, timeliness, coverage)
    equity = window.source == "alpaca_iex"
    return MarketHistorySeries(
        source=window.source,
        time_basis="regular_session" if equity else "utc",
        adjustment="split" if equity else "raw",
        interval_minutes=window.interval_minutes,
        start_at=window.start_at,
        end_at=window.end_at,
        as_of=as_of,
        expected_through_at=window.expected_through_at,
        timeliness=timeliness,
        coverage=coverage,
        points=tuple(points),
        day_change_pct=day,
        period_change_pct=period,
    )
