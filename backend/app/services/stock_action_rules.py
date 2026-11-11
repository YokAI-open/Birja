"""Independent action monitoring and persistent holds; no execution permission."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.services.corporate_action_rules import ActionReason


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
    return ActionDecision()
