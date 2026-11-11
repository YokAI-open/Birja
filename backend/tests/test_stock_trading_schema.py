"""Exact stock inputs must not inherit crypto's permissive decimal coercion."""

from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.stock_trades import QuoteIn, TradeIn


@pytest.mark.parametrize("quantity", [True, 1, 1.0, "1.0", "1e2", "+1", "01", " 1", "1\n", "0", "-1", "1000000000000", "NaN", "Infinity", None])
def test_reject_ambiguous_quantity(quantity: object) -> None:
    with pytest.raises(ValidationError):
        QuoteIn.model_validate({"symbol": "AAPL", "side": "buy", "quantity": quantity})


@pytest.mark.parametrize("quantity", ["1", "999999999999"])
def test_exact_whole_quantity(quantity: str) -> None:
    request = QuoteIn(symbol="AAPL", side="buy", quantity=quantity)
    assert request.quantity == Decimal(quantity)
    assert request.model_dump(mode="json")["quantity"] == quantity


@pytest.mark.parametrize("price", [True, 1, 1.5, "0", "-1", "NaN", "Infinity", "1e2", "+1", "01", "1.000000001", "1000000000000", "1\n"])
def test_expected_price_is_exact_positive_numeric20_8(price: object) -> None:
    with pytest.raises(ValidationError):
        TradeIn.model_validate({"symbol": "AAPL", "side": "buy", "quantity": "1", "expected_exec_price": price, "idempotency_key": str(uuid4())})


def test_valid_confirmation_and_forbidden_caller_authority() -> None:
    payload = {"symbol": "AAPL", "side": "buy", "quantity": "1", "expected_exec_price": "999999999999.99999999", "idempotency_key": str(uuid4())}
    request = TradeIn.model_validate(payload)
    assert request.expected_exec_price == Decimal(payload["expected_exec_price"])
    for field in ("user_id", "amount_usd", "valid_until", "admission_generation"):
        with pytest.raises(ValidationError):
            TradeIn.model_validate({**payload, field: "1"})
