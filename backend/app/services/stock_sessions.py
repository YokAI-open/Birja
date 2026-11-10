"""Reviewed regular-session decisions; derived rows never establish authority."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime

from app.services.stock_admission import ProductAdmission


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
    return []


def session_at(
    exchange: str,
    now: datetime,
    sessions: Sequence[RegularSession],
    current_calendar_admission: ProductAdmission | None,
) -> SessionDecision:
    return SessionDecision()
