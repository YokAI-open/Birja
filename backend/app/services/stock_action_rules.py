"""Independent action monitoring and persistent holds; no execution permission."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.services.corporate_action_rules import ActionReason
from app.services.stock_quote_rules import utc


@dataclass(frozen=True)
class ActionDecision:
    state: Literal["current", "unknown", "reconciling", "suspended"] = "unknown"
    reason: ActionReason = "monitor_unavailable"
    valid_until: datetime | None = None
    valuation_allowed: bool = False
    execution_enabled: bool = False


def evaluate_action_state(
    *,
    now: datetime,
    health: str = "unknown",
    rights_current: bool = False,
    coverage_complete: bool = False,
    valid_until: datetime | None = None,
    persistent_holds: tuple[ActionReason, ...] = (),
    known_boundary: datetime | None = None,
    unresolved_revision: bool = False,
    unit_epoch: int = 0,
    quote_unit_epoch: int | None = None,
    split_boundary: datetime | None = None,
    quote_event_at: datetime | None = None,
) -> ActionDecision:
    # A healthy poll cannot clear an independently persistent economic hold.
    held_reasons = ("unsupported", "fractional", "conflicting", "identity_change")
    if persistent_holds:
        selected: ActionReason = next(
            (value for value in persistent_holds if value in held_reasons), "conflicting"
        )
        return ActionDecision("suspended", selected)
    if unresolved_revision is not False:
        return ActionDecision("suspended", "conflicting")
    if (
        not utc(now)
        or rights_current is not True
        or not utc(valid_until)
        or valid_until is None
        or now >= valid_until
        or type(unit_epoch) is not int
        or not 0 <= unit_epoch <= 9007199254740991
    ):
        return ActionDecision()
    if health == "reconciling":
        return ActionDecision("reconciling", "source_gap")
    if health != "current":
        return ActionDecision()
    if coverage_complete is not True:
        return ActionDecision("unknown", "source_gap")
    if known_boundary is not None:
        if not utc(known_boundary):
            return ActionDecision()
        if now >= known_boundary:
            return ActionDecision("reconciling", "conflicting")
        valid_until = min(valid_until, known_boundary)
    if type(quote_unit_epoch) is not int or quote_unit_epoch != unit_epoch:
        return ActionDecision("suspended", "post_split_quote_missing")
    if unit_epoch > 0 and (
        not utc(split_boundary)
        or not utc(quote_event_at)
        or split_boundary is None
        or quote_event_at is None
        or not split_boundary < quote_event_at <= now
    ):
        return ActionDecision("suspended", "post_split_quote_missing")
    return ActionDecision("current", "none", valid_until, True)
