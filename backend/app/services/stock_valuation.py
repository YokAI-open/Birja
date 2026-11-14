"""Dated stock marks keep their original financial snapshot and source rights.

The quote table stores a permission generation, not historical terms. An
immutable fill's original full-row admission hash provides conservative proof
for that generation. Missing proof suppresses a mark; a current renewal never
manufactures original retention rights. No schema or financial writes occur.
"""

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from app.schemas.stock_trades import AuthorityIdentity
from app.services.stock_eligibility import LoadedExecution, session_rows
from app.services.stock_trading import _authority
from app.services.stock_trading_rules import (
    ExecutionEvidence,
    RefusalReason,
    ValuationEvidence,
    evaluate_valuation,
)


@dataclass(frozen=True)
class StockMark:
    mark_mode: Literal["fresh", "closed", "halted", "unavailable"] = "unavailable"
    valuation_reason: RefusalReason = "permission_unavailable"
    source: Literal["alpaca"] | None = None
    feed: Literal["iex"] | None = None
    event_at: datetime | None = None
    collected_at: datetime | None = None
    historical_admission_until: datetime | None = None
    retained_until: datetime | None = None
    valid_until: datetime | None = None
    authority: AuthorityIdentity | None = None
    units_safe: bool = False


@dataclass(frozen=True)
class StockValuation:
    mid: Decimal | None
    mark: StockMark


def _action(loaded: LoadedExecution, raw: Any) -> ExecutionEvidence:
    """Consumed exact applied split markers cannot invalidate compatible display."""
    e = loaded.evidence
    row: dict[str, Any] = next((a for a in raw.actions or [] if a["coin_id"] == e.coin_id), {})
    cached, split, applied = (
        row.get(k) for k in ("next_blocking_at", "split_boundary", "quote_not_before")
    )
    if cached is not None and split is not None and split == applied and cached <= split:
        pending = row.get("pending_boundary")
        return replace(e, next_blocking_at=datetime.fromisoformat(pending) if pending else None)
    return e


def _units_safe(e: ExecutionEvidence, now: datetime) -> bool:
    admissions = [a for a in e.admissions if a.product in ("actions", "reference", "calendar")]
    return bool(
        len(admissions) == 3
        and e.action_current
        and e.action_valid_until is not None
        and now < e.action_valid_until
        and (e.next_blocking_at is None or now < e.next_blocking_at)
        and all(a.approved and now < a.valid_until for a in admissions)
    )


def value_stock(
    snapshot: LoadedExecution | None,
    current: LoadedExecution | None,
    *,
    raw: Any,
    current_raw: Any,
    proof: dict[str, Any] | None,
    now: datetime,
) -> StockValuation:
    def denied(reason: RefusalReason, *, units: bool = False) -> StockValuation:
        return StockValuation(None, StockMark(valuation_reason=reason, units_safe=units))

    if snapshot is None or current is None:
        return denied("permission_unavailable")
    e, latest = _action(snapshot, raw), _action(current, current_raw)
    if e.provider_asset_id != latest.provider_asset_id:
        return denied("permission_unavailable")
    if e.unit_epoch != latest.unit_epoch:
        return denied("units_changed")
    if e.safety_epoch != latest.safety_epoch:
        return denied("action_unavailable")
    if e.admissions != latest.admissions:
        return denied("permission_unavailable")
    # Renewed observations may suppress old prices or turn them into dated halt
    # marks, never renew the old snapshot's authority deadline or source price.
    units = _units_safe(e, now) and _units_safe(latest, now)
    if e.status.continuity_generation != latest.status.continuity_generation:
        return denied("status_unavailable", units=units)
    if e.action_valid_until is None or latest.action_valid_until is None:
        return denied("action_unavailable")
    if e.session_valid_until is None or latest.session_valid_until is None:
        return denied("session_unavailable")
    if e.status.valid_until is None or latest.status.valid_until is None:
        return denied("status_unavailable", units=units)
    e = replace(
        e,
        status=replace(
            latest.status,
            valid_until=min(e.status.valid_until, latest.status.valid_until),
        ),
        action_current=e.action_current and latest.action_current,
        action_valid_until=min(e.action_valid_until, latest.action_valid_until),
        session_state=latest.session_state,
        session_date=latest.session_date,
        opens_at=latest.opens_at,
        closes_at=latest.closes_at,
        session_valid_until=min(e.session_valid_until, latest.session_valid_until),
        next_blocking_at=min(
            (v for v in (e.next_blocking_at, latest.next_blocking_at) if v is not None),
            default=None,
        ),
    )
    units = _units_safe(e, now)
    if proof is None:
        return denied("permission_unavailable", units=units)
    try:
        quote_admission = next(a for a in e.admissions if a.product == "quotes")
        original = next(a for a in proof["admissions"] if a["product"] == "quotes")
        original_until = datetime.fromisoformat(original["valid_until"])
        original_from = datetime.fromisoformat(original["valid_from"])
        if (
            proof["provider_asset_id"] != e.provider_asset_id
            or original["generation"] != e.quote.admission_generation
            or original["row_hash"] != quote_admission.row_hash
            or e.quote.collected_at is None
            or not original_from <= e.quote.collected_at < original_until
        ):
            return denied("permission_unavailable", units=units)
        source_session = next(
            s
            for s in session_rows(raw.sessions or [])
            if s.exchange == snapshot.listing_exchange and s.session_date == e.quote.session_date
        )
        if (
            source_session.opens_at is None
            or source_session.closes_at is None
            or e.quote.event_at is None
            or not source_session.opens_at <= e.quote.event_at < source_session.closes_at
        ):
            return denied("quote_unavailable", units=units)
    except KeyError, TypeError, ValueError, StopIteration:
        return denied("permission_unavailable", units=units)
    decision = evaluate_valuation(
        ValuationEvidence(e, snapshot.quote_retained_until, original_until), now
    )
    if decision.mode == "unavailable":
        return denied(decision.reason, units=units)
    return StockValuation(
        decision.mid,
        StockMark(
            mark_mode=decision.mode,
            valuation_reason=decision.reason,
            source="alpaca",
            feed="iex",
            event_at=e.quote.event_at,
            collected_at=e.quote.collected_at,
            historical_admission_until=original_until,
            retained_until=snapshot.quote_retained_until,
            valid_until=decision.valid_until,
            authority=_authority(replace(snapshot, evidence=e)),
            units_safe=units,
        ),
    )
