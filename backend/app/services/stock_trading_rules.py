"""Pure stock authority contracts under assertion-first development."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ExecutionEvidence:
    pass


@dataclass(frozen=True)
class ExecutionDecision:
    allowed: bool
    reason: str


def evaluate_execution(evidence: ExecutionEvidence, now: datetime) -> ExecutionDecision:
    return ExecutionDecision(True, "available")
