"""Independent evidence must default deny, even when a quote is recent."""

from datetime import UTC, datetime

from app.services.stock_trading_rules import ExecutionEvidence, evaluate_execution


def test_empty_evidence_defaults_deny() -> None:
    decision = evaluate_execution(ExecutionEvidence(), datetime(2026, 11, 11, 15, tzinfo=UTC))
    assert not decision.allowed
    assert decision.reason == "permission_unavailable"
