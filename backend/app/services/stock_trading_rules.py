"""Pure deny-by-default execution and separately retained valuation evidence.

These rules do not fetch evidence or confer provider rights. SQL consumers must
revalidate the returned exact snapshot after all financial writes and waits.
"""

import re
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from decimal import Decimal, localcontext
from typing import Literal

from app.services.stock_quote_rules import utc

MAX_SAFE = 9007199254740991
STATUS_LEASE_SECONDS = 60
PRODUCTS = frozenset({"reference", "quotes", "actions", "status", "calendar"})
RefusalReason = Literal[
    "available",
    "permission_unavailable",
    "action_unavailable",
    "units_changed",
    "halted",
    "frozen",
    "status_unavailable",
    "session_unavailable",
    "market_closed",
    "quote_unavailable",
    "quote_stale",
]


@dataclass(frozen=True)
class AdmissionEvidence:
    product: str
    generation: int
    row_hash: str
    valid_from: datetime
    valid_until: datetime
    approved: bool = False


@dataclass(frozen=True)
class StatusEvidence:
    coin_id: int = 0
    provider_asset_id: str = ""
    state: Literal["normal", "halted", "frozen", "unknown"] = "unknown"
    event_at: datetime | None = None
    observed_at: datetime | None = None
    session_date: date | None = None
    admission_generation: int = 0
    continuity_generation: int = 0
    sequence: int = 0
    valid_until: datetime | None = None
    bootstrap_verified: bool = False
    continuity_current: bool = False
    source: str = "alpaca"
    source_ref: str = ""


@dataclass(frozen=True)
class QuoteEvidence:
    coin_id: int = 0
    provider_asset_id: str = ""
    bid: Decimal | None = None
    ask: Decimal | None = None
    event_at: datetime | None = None
    collected_at: datetime | None = None
    session_date: date | None = None
    admission_generation: int = 0
    unit_epoch: int = 0
    source: str = "alpaca"
    feed: str = "iex"


@dataclass(frozen=True)
class ExecutionEvidence:
    coin_id: int = 0
    provider_asset_id: str = ""
    admissions: tuple[AdmissionEvidence, ...] = ()
    action_current: bool = False
    action_valid_until: datetime | None = None
    next_blocking_at: datetime | None = None
    safety_epoch: int = 0
    unit_epoch: int = 0
    status: StatusEvidence = StatusEvidence()
    session_state: Literal["open", "closed", "unknown"] = "unknown"
    session_date: date | None = None
    opens_at: datetime | None = None
    closes_at: datetime | None = None
    session_valid_until: datetime | None = None
    calendar_generation: int = 0
    quote: QuoteEvidence = QuoteEvidence()


@dataclass(frozen=True)
class ExecutionDecision:
    allowed: bool
    reason: RefusalReason
    evaluated_at: datetime
    valid_until: datetime | None = None
    evidence: ExecutionEvidence | None = None


@dataclass(frozen=True)
class ValuationEvidence:
    execution: ExecutionEvidence = ExecutionEvidence()
    retained_until: datetime | None = None
    historical_admission_until: datetime | None = None


@dataclass(frozen=True)
class ValuationDecision:
    mode: Literal["fresh", "closed", "halted", "unavailable"]
    reason: RefusalReason
    mid: Decimal | None = None
    event_at: datetime | None = None
    valid_until: datetime | None = None


def _integer(value: object, minimum: int = 0) -> bool:
    return type(value) is int and minimum <= value <= MAX_SAFE


def _deadline(value: datetime | None, now: datetime) -> bool:
    return utc(value) and value is not None and now < value


def _admitted(evidence: ExecutionEvidence, now: datetime) -> bool:
    rows = evidence.admissions
    return (
        utc(now)
        and type(evidence.coin_id) is int
        and evidence.coin_id > 0
        and 0 < len(evidence.provider_asset_id.strip()) <= 128
        and len(rows) == len(PRODUCTS)
        and frozenset(row.product for row in rows) == PRODUCTS
        and all(
            row.approved is True
            and _integer(row.generation, 1)
            and re.fullmatch(r"[a-f0-9]{64}", row.row_hash) is not None
            and utc(row.valid_from)
            and row.valid_from <= now
            and _deadline(row.valid_until, now)
            for row in rows
        )
    )


def _generation(evidence: ExecutionEvidence, product: str) -> int:
    return next(row.generation for row in evidence.admissions if row.product == product)


def _action_reason(evidence: ExecutionEvidence, now: datetime) -> RefusalReason | None:
    if (
        evidence.action_current is not True
        or not _deadline(evidence.action_valid_until, now)
        or not _integer(evidence.safety_epoch)
        or not _integer(evidence.unit_epoch)
        or evidence.next_blocking_at is not None
        and not _deadline(evidence.next_blocking_at, now)
    ):
        return "action_unavailable"
    if not _integer(evidence.quote.unit_epoch) or evidence.quote.unit_epoch != evidence.unit_epoch:
        return "units_changed"
    return None


def status_current(status: StatusEvidence, now: datetime) -> bool:
    """Event may be old; only trusted explicit continuity renews a <=60s lease."""
    return (
        utc(now)
        and status.bootstrap_verified is True
        and status.continuity_current is True
        and status.source == "alpaca"
        and 0 < len(status.source_ref) <= 2048
        and type(status.coin_id) is int
        and status.coin_id > 0
        and 0 < len(status.provider_asset_id.strip()) <= 128
        and _integer(status.admission_generation, 1)
        and _integer(status.continuity_generation, 1)
        and _integer(status.sequence)
        and type(status.session_date) is date
        and utc(status.event_at)
        and utc(status.observed_at)
        and status.event_at is not None
        and status.observed_at is not None
        and status.event_at <= status.observed_at <= now
        and _deadline(status.valid_until, now)
        and status.valid_until is not None
        and timedelta(0)
        < status.valid_until - status.observed_at
        <= timedelta(seconds=STATUS_LEASE_SECONDS)
    )


def lose_status_continuity(status: StatusEvidence) -> StatusEvidence:
    """Loss/reconnect invalidates authority; cannot wrap a saturated generation."""
    generation = status.continuity_generation
    if not _integer(generation) or generation == MAX_SAFE:
        raise ValueError("Continuity generation cannot advance safely.")
    return replace(
        status,
        state="unknown",
        continuity_generation=generation + 1,
        bootstrap_verified=False,
        continuity_current=False,
        valid_until=None,
    )


def renew_status_continuity(
    status: StatusEvidence,
    observed_at: datetime,
    *,
    trusted_contiguous: bool = False,
    sequence: int,
) -> StatusEvidence:
    """Only a verified contiguous transport frame can extend existing authority.

    Quote updates, heartbeats and scheduler success must never call this with
    trusted_contiguous=True. A lost/expired stream requires a new verified baseline.
    """
    if (
        trusted_contiguous is not True
        or not status_current(status, observed_at)
        or not _integer(sequence)
        or sequence != status.sequence + 1
    ):
        return lose_status_continuity(status)
    return replace(
        status,
        observed_at=observed_at,
        sequence=sequence,
        valid_until=observed_at + timedelta(seconds=STATUS_LEASE_SECONDS),
    )


def _status_reason(evidence: ExecutionEvidence, now: datetime) -> RefusalReason | None:
    status = evidence.status
    if (
        not status_current(status, now)
        or status.coin_id != evidence.coin_id
        or status.provider_asset_id != evidence.provider_asset_id
        or status.admission_generation != _generation(evidence, "status")
        or status.session_date != evidence.session_date
    ):
        return "status_unavailable"
    if status.state == "halted":
        return "halted"
    if status.state == "frozen":
        return "frozen"
    return None if status.state == "normal" else "status_unavailable"


def _quote_valid(evidence: ExecutionEvidence, now: datetime) -> bool:
    quote = evidence.quote
    return (
        quote.coin_id == evidence.coin_id
        and quote.provider_asset_id == evidence.provider_asset_id
        and quote.source == "alpaca"
        and quote.feed == "iex"
        and quote.admission_generation == _generation(evidence, "quotes")
        and isinstance(quote.bid, Decimal)
        and isinstance(quote.ask, Decimal)
        and quote.bid.is_finite()
        and quote.ask.is_finite()
        and Decimal(0) < quote.bid <= quote.ask < Decimal("1e12")
        and _price_precision(quote.bid)
        and _price_precision(quote.ask)
        and utc(quote.event_at)
        and utc(quote.collected_at)
        and quote.event_at is not None
        and quote.collected_at is not None
        and quote.event_at <= quote.collected_at <= now
        and quote.session_date == quote.event_at.date()
    )


def _price_precision(value: Decimal) -> bool:
    with localcontext() as context:
        context.prec = 40
        return value == value.quantize(Decimal("0.00000001"))


def _deadlines(evidence: ExecutionEvidence) -> list[datetime]:
    return [row.valid_until for row in evidence.admissions] + [
        value
        for value in (
            evidence.action_valid_until,
            evidence.next_blocking_at,
            evidence.status.valid_until,
            evidence.session_valid_until,
        )
        if value is not None
    ]


def evaluate_execution(evidence: ExecutionEvidence, now: datetime) -> ExecutionDecision:
    """Strict reason priority: permission -> actions/units -> status -> session -> quote."""

    def refuse(reason: RefusalReason) -> ExecutionDecision:
        return ExecutionDecision(False, reason, now)

    if not _admitted(evidence, now):
        return refuse("permission_unavailable")
    reason = _action_reason(evidence, now) or _status_reason(evidence, now)
    if reason:
        return refuse(reason)
    if (
        evidence.session_state not in ("open", "closed")
        or not _deadline(evidence.session_valid_until, now)
        or not _integer(evidence.calendar_generation, 1)
        or evidence.calendar_generation != _generation(evidence, "calendar")
    ):
        return refuse("session_unavailable")
    opens, closes = evidence.opens_at, evidence.closes_at
    if evidence.session_state == "closed":
        return refuse("market_closed")
    if (
        not utc(opens)
        or not utc(closes)
        or opens is None
        or closes is None
        or opens >= closes
        or evidence.session_date != opens.date()
    ):
        return refuse("session_unavailable")
    if not opens <= now < closes:
        return refuse("market_closed")
    quote = evidence.quote
    if (
        not _quote_valid(evidence, now)
        or quote.event_at is None
        or quote.session_date != evidence.session_date
        or quote.event_at < opens
    ):
        return refuse("quote_unavailable")
    if now - quote.event_at >= timedelta(seconds=120):
        return refuse("quote_stale")
    valid_until = min(*_deadlines(evidence), closes, quote.event_at + timedelta(seconds=120))
    return ExecutionDecision(True, "available", now, valid_until, evidence)


def evaluate_valuation(evidence: ValuationEvidence, now: datetime) -> ValuationDecision:
    """Historical marks never confer execution permission or reset source age."""
    execution = evidence.execution
    if not _admitted(execution, now):
        return ValuationDecision("unavailable", "permission_unavailable")
    reason = _action_reason(execution, now) or _status_reason(execution, now)
    if reason not in (None, "halted"):
        return ValuationDecision("unavailable", reason)
    if not _deadline(evidence.retained_until, now) or not _deadline(
        evidence.historical_admission_until, now
    ):
        return ValuationDecision("unavailable", "permission_unavailable")
    if not _quote_valid(execution, now):
        return ValuationDecision("unavailable", "quote_unavailable")
    if (
        execution.session_state not in ("open", "closed")
        or not _deadline(execution.session_valid_until, now)
        or not _integer(execution.calendar_generation, 1)
        or execution.calendar_generation != _generation(execution, "calendar")
    ):
        return ValuationDecision("unavailable", "session_unavailable")
    decision = evaluate_execution(execution, now)
    mode: Literal["fresh", "closed", "halted"]
    if reason == "halted":
        mode = "halted"
    elif execution.session_state == "closed":
        mode = "closed"
    elif decision.allowed:
        mode = "fresh"
    else:
        return ValuationDecision("unavailable", decision.reason)
    quote = execution.quote
    if (
        quote.bid is None
        or quote.ask is None
        or evidence.retained_until is None
        or evidence.historical_admission_until is None
    ):
        return ValuationDecision("unavailable", "quote_unavailable")
    with localcontext() as context:
        context.prec = 40
        midpoint = (quote.bid + quote.ask) / 2
    deadlines = _deadlines(execution) + [
        evidence.retained_until,
        evidence.historical_admission_until,
    ]
    if mode == "fresh" and decision.valid_until is not None:
        deadlines.append(decision.valid_until)
    return ValuationDecision(mode, "available", midpoint, quote.event_at, min(deadlines))
