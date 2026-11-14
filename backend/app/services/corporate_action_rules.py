"""Immutable normalized source facts and exact economic decisions.

Local verification flags describe reviewed evidence; absent provider fields stay null.
No contract supplies permission, mutates accounting or enables execution.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from fractions import Fraction
from typing import Literal, cast

from app.services.stock_admission import ProductAdmission
from app.services.stock_quote_rules import CURATED_SYMBOLS, utc
from app.services.stock_sessions import build_sessions

ActionReason = Literal[
    "none",
    "monitor_unavailable",
    "source_gap",
    "unsupported",
    "fractional",
    "conflicting",
    "identity_change",
    "post_split_quote_missing",
]
ClassificationKind = Literal[
    "supported_dividend", "supported_forward_split", "unsupported", "uncertain", "cancelled"
]


@dataclass(frozen=True)
class NormalizedAction:
    provider_event_id: str
    coin_id: int
    symbol: str
    event_type: str
    process_date: date | None
    observed_at: datetime
    source_event_at: datetime | None = None
    economic_at: datetime | None = None
    currency: str | None = None
    rate: Decimal | None = None
    new_rate: Decimal | None = None
    old_rate: Decimal | None = None
    declaration_date: date | None = None
    ex_date: date | None = None
    record_date: date | None = None
    payable_date: date | None = None
    subtype: str | None = None
    foreign: bool | None = None
    special: bool | None = None
    due_bills: bool | None = None
    identity_verified: bool = False
    dates_verified: bool = False
    identity_changed: bool = False
    cancelled: bool = False
    units: str | None = None
    same_boundary_split: bool = False
    economic_order: int | None = None
    due_bill_mapping_verified: bool = False


@dataclass(frozen=True)
class ActionClassification:
    kind: ClassificationKind = "uncertain"
    reason: ActionReason = "conflicting"
    action: NormalizedAction | None = None
    ratio: Fraction | None = None


@dataclass(frozen=True)
class CutoffEvidence:
    cutoff: datetime
    exchange: str
    ex_date: date
    calendar_generation: int
    calendar_version: str
    rule: str = "exclusive-regular-session-open"
    exclusive: bool = True


@dataclass(frozen=True)
class SplitOwner:
    user_id: int
    quantity: Decimal
    total_basis: Decimal


@dataclass(frozen=True)
class SplitPlan:
    allowed: bool = False
    reason: ActionReason = "conflicting"
    ratio: Fraction | None = None
    owners: tuple[SplitOwner, ...] = ()


def classify_action(action: NormalizedAction) -> ActionClassification:
    """Only explicit verified terms support automatic effects; no invented dates."""
    uncertain = ActionClassification()
    if (
        not isinstance(action, NormalizedAction)
        or not isinstance(action.provider_event_id, str)
        or not 0 < len(action.provider_event_id.strip()) <= 256
        or type(action.coin_id) is not int
        or not 0 < action.coin_id <= 9007199254740991
        or not isinstance(action.symbol, str)
        or action.symbol not in CURATED_SYMBOLS
        or type(action.process_date) is not date
        or not utc(action.observed_at)
        or (action.source_event_at is not None and not utc(action.source_event_at))
        or (action.economic_at is not None and not utc(action.economic_at))
        or action.identity_verified is not True
        or action.dates_verified is not True
        or type(action.cancelled) is not bool
        or type(action.identity_changed) is not bool
    ):
        return uncertain
    if action.identity_changed:
        return ActionClassification("unsupported", "identity_change")
    if action.cancelled:
        return ActionClassification("cancelled", "conflicting")
    if action.event_type not in ("cash_dividend", "forward_split"):
        return ActionClassification("unsupported", "unsupported")
    if (
        type(action.ex_date) is not date
        or type(action.record_date) is not date
        or type(action.payable_date) is not date
    ):
        return uncertain
    ex_date = action.ex_date
    record_date = action.record_date
    payable_date = action.payable_date
    if action.event_type == "cash_dividend":
        if (
            action.currency != "USD"
            or action.foreign is not False
            or action.special is not False
            or action.subtype != "ordinary"
            or action.due_bills is not False
            or not _decimal(action.rate, positive=True)
            or not ex_date <= record_date <= payable_date
            or (
                action.declaration_date is not None
                and (type(action.declaration_date) is not date or action.declaration_date > ex_date)
            )
            or type(action.same_boundary_split) is not bool
            or (
                action.same_boundary_split
                and (
                    type(action.economic_order) is not int
                    or (action.units, action.economic_order)
                    not in (("pre_split", 1), ("post_split", 2))
                )
            )
        ):
            return uncertain
        return ActionClassification("supported_dividend", "none", action)
    if (
        action.economic_at is None
        or action.units != "pre_split"
        or type(action.due_bills) is not bool
        or (action.due_bills is not False and action.due_bill_mapping_verified is not True)
        or action.economic_at.date() != ex_date
        or record_date > payable_date
        or (action.due_bills is False and ex_date > record_date)
        or not _decimal(action.new_rate, positive=True)
        or not _decimal(action.old_rate, positive=True)
    ):
        return uncertain
    ratio = Fraction(cast(Decimal, action.new_rate)) / Fraction(cast(Decimal, action.old_rate))
    if ratio <= 1:
        return ActionClassification("unsupported", "unsupported")
    if max(ratio.numerator, ratio.denominator) > 1000000000:
        return uncertain
    return ActionClassification("supported_forward_split", "none", action, ratio)


def _decimal(value: object, *, positive: bool = False, cents: bool = False) -> bool:
    """Bound coefficient/exponent before Fraction can allocate a giant integer."""
    if not isinstance(value, Decimal) or not value.is_finite():
        return False
    parts = value.as_tuple()
    if len(parts.digits) > 28 or not -8 <= int(parts.exponent) <= 18:
        return False
    if not (
        Decimal(0) < value < Decimal("1e12") if positive else Decimal(0) <= value < Decimal("1e18")
    ):
        return False
    fraction = Fraction(value)
    return not cents or (fraction * 100).denominator == 1


def dividend_cutoff(
    action: NormalizedAction,
    exchange: str,
    now: datetime,
    authority: ProductAdmission | None,
    *,
    account: str = "birja",
    server: str = "birja",
) -> CutoffEvidence | None:
    if classify_action(action).kind != "supported_dividend" or not utc(now):
        return None
    sessions = build_sessions(now, authority, account=account, server=server)
    selected = [
        row for row in sessions if row.exchange == exchange and row.session_date == action.ex_date
    ]
    if len(selected) != 1 or selected[0].opens_at is None or authority is None:
        return None
    return CutoffEvidence(
        selected[0].opens_at,
        exchange,
        cast(date, action.ex_date),
        authority.generation,
        authority.calendar["version"],
    )


def plan_forward_split(action: NormalizedAction, owners: Sequence[SplitOwner]) -> SplitPlan:
    classification = classify_action(action)
    if classification.kind != "supported_forward_split" or classification.ratio is None:
        return SplitPlan(reason=classification.reason)
    result = []
    seen = set()
    for owner in owners:
        if (
            not isinstance(owner, SplitOwner)
            or type(owner.user_id) is not int
            or not 0 < owner.user_id <= 9007199254740991
            or owner.user_id in seen
            or not _decimal(owner.quantity)
            or not _decimal(owner.total_basis, cents=True)
            or owner.total_basis >= Decimal("1e12")
            or (owner.quantity == 0 and owner.total_basis != 0)
            or owner.quantity >= Decimal("1e12")
        ):
            return SplitPlan()
        seen.add(owner.user_id)
        quantity = Fraction(owner.quantity)
        if quantity.denominator != 1:
            return SplitPlan(reason="fractional")
        adjusted = quantity * classification.ratio
        if adjusted.denominator != 1:
            return SplitPlan(reason="fractional")
        if adjusted.numerator >= 1000000000000:
            return SplitPlan()
        result.append(SplitOwner(owner.user_id, Decimal(adjusted.numerator), owner.total_basis))
    return SplitPlan(True, "none", classification.ratio, tuple(result))
