"""Reviewed regular-session decisions; derived rows never establish authority."""

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache

import exchange_calendars as calendars  # type: ignore[import-untyped]
from sqlalchemy import column, exists, func, select, values
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import StockDataAdmission, StockSession
from app.services.stock_admission import ProductAdmission, evaluate_admission
from app.services.stock_quote_rules import ValidatedStockQuote, quote_eligibility, utc

EXCHANGES = {"NYSE": "XNYS", "NASDAQ": "XNAS"}


@dataclass(frozen=True)
class RegularSession:
    exchange: str
    session_date: date
    opens_at: datetime | None
    closes_at: datetime | None
    coverage_start: date
    coverage_end: date
    calendar_admission_generation: int


@dataclass(frozen=True)
class SessionDecision:
    state: str = "unknown"
    current: RegularSession | None = None
    next_session: RegularSession | None = None
    valid_until: datetime | None = None
    executable: bool = False


def build_sessions(
    now: datetime, current_calendar_admission: ProductAdmission | None
) -> list[RegularSession]:
    if (
        current_calendar_admission is None
        or not evaluate_admission(current_calendar_admission, "calendar", "derived", now).allowed
    ):
        return []
    evidence = current_calendar_admission
    start = date.fromisoformat(evidence.calendar["coverage_start"])
    end = date.fromisoformat(evidence.calendar["coverage_end"])
    overrides = {
        (o["exchange"], date.fromisoformat(o["date"])): o for o in evidence.calendar["overrides"]
    }
    rows = []
    for exchange, alias in EXCHANGES.items():
        for day, opens, closes in _calendar_bounds(alias, start, end):
            override = overrides.get((alias, day))
            if override:
                if override["state"] == "closed":
                    opens = closes = None
                else:
                    changed_open = datetime.fromisoformat(override["opens_at"])
                    changed_close = datetime.fromisoformat(override["closes_at"])
                    # A shortened override cannot invent a session or extend it.
                    if (
                        opens is None
                        or closes is None
                        or changed_open != opens
                        or changed_close > closes
                    ):
                        return []
                    opens, closes = changed_open, changed_close
            rows.append(
                RegularSession(exchange, day, opens, closes, start, end, evidence.generation)
            )
    return rows


@lru_cache(maxsize=8)
def _calendar_bounds(
    alias: str, start: date, end: date
) -> tuple[tuple[date, datetime | None, datetime | None], ...]:
    """Only immutable package bounds are cached; never authority or decisions."""
    calendar = calendars.get_calendar(alias, start=start.isoformat(), end=end.isoformat())
    open_days = {stamp.date() for stamp in calendar.sessions}
    result = []
    for offset in range((end - start).days + 1):
        day = start + timedelta(days=offset)
        if day in open_days:
            opens = calendar.session_open(day.isoformat()).to_pydatetime().astimezone(UTC)
            closes = calendar.session_close(day.isoformat()).to_pydatetime().astimezone(UTC)
        else:
            opens = closes = None
        result.append((day, opens, closes))
    return tuple(result)


def session_at(
    exchange: str,
    now: datetime,
    sessions: Sequence[RegularSession],
    current_calendar_admission: ProductAdmission | None,
) -> SessionDecision:
    if exchange not in EXCHANGES or not utc(now) or len(sessions) > 272:
        return SessionDecision()
    admission = evaluate_admission(current_calendar_admission, "calendar", "derived", now)
    if not admission.allowed:
        return SessionDecision()
    expected = {
        row.session_date: row
        for row in build_sessions(now, current_calendar_admission)
        if row.exchange == exchange
    }
    selected = [row for row in sessions if row.exchange == exchange]
    actual = {row.session_date: row for row in selected}
    if len(actual) != len(selected) or any(expected.get(day) != row for day, row in actual.items()):
        return SessionDecision()
    current = actual.get(now.date())
    if current is None:
        return SessionDecision()
    upcoming = sorted(
        (row for row in selected if row.opens_at is not None and row.opens_at > now),
        key=lambda row: row.session_date,
    )
    if not upcoming:
        return SessionDecision()
    # Missing an intervening derived day cannot silently skip a possible session.
    if any(day not in actual for day in expected if now.date() <= day <= upcoming[0].session_date):
        return SessionDecision()
    opened = (
        current.opens_at is not None
        and current.closes_at is not None
        and current.opens_at <= now < current.closes_at
    )
    return SessionDecision(
        "open" if opened else "closed", current, upcoming[0], admission.valid_until
    )


@dataclass(frozen=True)
class DiscoveryEligibility:
    calendar: str
    quote_valid: bool
    status: str
    actions: str
    executable: bool = False


def discovery_eligibility(
    session: SessionDecision,
    quote: ValidatedStockQuote | None,
    now: datetime,
    *,
    status: str = "unknown",
    actions: str = "unknown",
) -> DiscoveryEligibility:
    """Independent facts; no Phase7/8 fact combination can authorize a fill."""
    valid = (
        session.state == "open"
        and utc(now)
        and session.valid_until is not None
        and now < session.valid_until
        and quote is not None
        and quote_eligibility(quote, session.current, now)
    )
    return DiscoveryEligibility(session.state, valid, status, actions)


async def load_sessions(db: AsyncSession, now: datetime) -> list[RegularSession]:
    if not utc(now):
        return []
    columns = [column for column in StockSession.__table__.columns if column.name != "id"]
    rows = await db.execute(
        select(*columns)
        .where(
            StockSession.session_date >= now.date() - timedelta(days=45),
            StockSession.session_date <= now.date() + timedelta(days=90),
        )
        .order_by(StockSession.exchange, StockSession.session_date)
        .limit(273)
    )
    return [RegularSession(**row) for row in rows.mappings()]


async def persist_sessions(
    db: AsyncSession,
    sessions: Sequence[RegularSession],
    current_calendar_admission: ProductAdmission,
    now: datetime,
) -> int:
    """Caller owns a short commit; INSERT SELECT rechecks current authority.

    Runtime has no admission UPDATE/row-lock privilege. Compare the complete
    authoritative snapshot, generation and DB-clock review expiry in the write
    statement. A later revocation/generation change is refused by session_at.
    """
    expected = build_sessions(now, current_calendar_admission)
    if not sessions or len(sessions) > 272 or list(sessions) != expected:
        return 0
    if not all(
        evaluate_admission(current_calendar_admission, "calendar", purpose, now).allowed
        for purpose in ("derived", "retention", "collection")
    ):
        return 0
    admission = StockDataAdmission
    snapshot = asdict(current_calendar_admission)
    review_until = datetime.fromisoformat(current_calendar_admission.calendar["review_valid_until"])
    guard = exists(
        select(admission.id).where(
            *(getattr(admission, name) == value for name, value in snapshot.items()),
            admission.valid_from <= func.clock_timestamp(),
            admission.valid_until > func.clock_timestamp(),
            func.clock_timestamp() < review_until,
        )
    )
    names = list(asdict(sessions[0]))
    incoming = (
        values(*(column(name, StockSession.__table__.c[name].type) for name in names))
        .data([tuple(asdict(row)[name] for name in names) for row in sessions])
        .cte("incoming_stock_sessions")
    )
    # One bounded statement/snapshot; never delete old authority or evidence.
    stmt = insert(StockSession).from_select(
        names, select(*(incoming.c[name] for name in names)).where(guard)
    )
    query = stmt.on_conflict_do_update(
        index_elements=[StockSession.exchange, StockSession.session_date],
        set_={
            name: stmt.excluded[name] for name in names if name not in ("exchange", "session_date")
        },
    ).returning(StockSession.id)
    return len((await db.execute(query)).scalars().all())
