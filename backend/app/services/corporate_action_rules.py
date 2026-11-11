"""Immutable normalized source facts and exact economic decisions.

Local verification flags describe reviewed evidence; absent provider fields stay null.
No contract supplies permission, mutates accounting or enables execution.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from fractions import Fraction
from typing import Literal

from app.services.stock_admission import ProductAdmission

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
    return ActionClassification()


def dividend_cutoff(
    action: NormalizedAction,
    exchange: str,
    now: datetime,
    authority: ProductAdmission | None,
    *,
    account: str = "birja",
    server: str = "birja",
) -> CutoffEvidence | None:
    return None


def plan_forward_split(action: NormalizedAction, owners: Sequence[SplitOwner]) -> SplitPlan:
    return SplitPlan()
