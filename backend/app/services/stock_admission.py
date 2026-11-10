"""Product-specific evidence values; runtime callers have no administration rights."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ProductAdmission:
    product: str
    state: str = "denied"
    generation: int = 1
    reviewed_at: datetime | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    evidence_ref: str | None = field(default=None, repr=False)
    terms_version: str | None = field(default=None, repr=False)
    collection_allowed: bool = False
    display_allowed: bool = False
    derived_allowed: bool = False
    retention_allowed: bool = False
    scope: dict[str, Any] = field(default_factory=dict, repr=False)
    quota: dict[str, Any] = field(default_factory=dict, repr=False)
    allowed_fields: list[str] = field(default_factory=list)
    attribution: str = ""
    calendar: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class AdmissionDecision:
    allowed: bool
    reason: str
    generation: int | None = None
    valid_until: datetime | None = None
    attribution: str = ""


def evaluate_admission(
    evidence: ProductAdmission | None,
    product: str,
    purpose: str,
    now: datetime,
    *,
    expected_generation: int | None = None,
    account: str = "birja",
    server: str = "birja",
    feed: str = "iex",
) -> AdmissionDecision:
    """Deny until a complete product/purpose evidence review can be established."""
    return AdmissionDecision(False, "unknown")
