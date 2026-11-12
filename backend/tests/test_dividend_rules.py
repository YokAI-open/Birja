"""Exact public financial vectors; later SQL authority must match these values."""

from decimal import ROUND_HALF_UP, Decimal

import pytest

# Explicit temporary behavior seam for the initial RED. It reproduces the
# unsafe numeric-round tie convention, so failure is financial, not an import.
def evaluate_dividend_target(
    quantity: Decimal, rate: Decimal, cumulative_applied: Decimal, cash: Decimal
) -> Decimal:
    return (quantity * rate).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)


# Literal independent expected amounts, also consumed by actual SQL parity tests.
TARGET_VECTORS = (
    ("1", ".005", "0.00"),
    ("1", ".015", "0.02"),
    ("1", ".025", "0.02"),
    ("3", ".005", "0.02"),
    ("1", "1.005", "1.00"),
    ("1", "1.015", "1.02"),
    ("999999999999", ".00000001", "10000.00"),
    ("1", "999999999999.99499999", "999999999999.99"),
    ("0", "999999999999.99999999", "0.00"),
    ("100", "0", "0.00"),
)


@pytest.mark.parametrize("quantity,rate,expected", TARGET_VECTORS)
def test_target_vectors(quantity: str, rate: str, expected: str) -> None:
    result = evaluate_dividend_target(Decimal(quantity), Decimal(rate), Decimal(0), Decimal(0))
    assert result == Decimal(expected)
