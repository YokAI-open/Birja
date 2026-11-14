"""Exact stock inputs must not inherit crypto's permissive decimal coercion."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.stock_trades import QuoteIn, TradeIn


@pytest.mark.parametrize(
    "quantity",
    [
        True,
        1,
        1.0,
        "1.0",
        "1e2",
        "+1",
        "01",
        " 1",
        "1\n",
        "0",
        "-1",
        "1000000000000",
        "NaN",
        "Infinity",
        None,
    ],
)
def test_reject_ambiguous_quantity(quantity: object) -> None:
    with pytest.raises(ValidationError):
        QuoteIn.model_validate({"symbol": "AAPL", "side": "buy", "quantity": quantity})


@pytest.mark.parametrize("quantity", ["1", "999999999999"])
def test_exact_whole_quantity(quantity: str) -> None:
    request = QuoteIn(symbol="AAPL", side="buy", quantity=quantity)
    assert request.quantity == Decimal(quantity)
    assert request.model_dump(mode="json")["quantity"] == quantity


@pytest.mark.parametrize(
    "price",
    [
        True,
        1,
        1.5,
        "0",
        "-1",
        "NaN",
        "Infinity",
        "1e2",
        "+1",
        "01",
        "1.000000001",
        "1000000000000",
        "1\n",
    ],
)
def test_expected_price_is_exact_positive_numeric20_8(price: object) -> None:
    with pytest.raises(ValidationError):
        TradeIn.model_validate(
            {
                "symbol": "AAPL",
                "side": "buy",
                "quantity": "1",
                "expected_exec_price": price,
                "idempotency_key": str(uuid4()),
            }
        )


def test_valid_confirmation_and_forbidden_caller_authority() -> None:
    payload = {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": "1",
        "expected_exec_price": "999999999999.99999999",
        "idempotency_key": str(uuid4()),
    }
    request = TradeIn.model_validate(payload)
    assert request.expected_exec_price == Decimal(payload["expected_exec_price"])
    for field in ("user_id", "amount_usd", "valid_until", "admission_generation"):
        with pytest.raises(ValidationError):
            TradeIn.model_validate({**payload, field: "1"})


def test_receipt_is_saved_projection_without_renewed_deadline() -> None:
    from app.schemas.stock_trades import FillOut, QuoteOut

    now = datetime(2026, 11, 11, 15, tzinfo=UTC)
    facts = {
        "coin_id": "9007199254740993",
        "provider_asset_id": "fixture-AAPL",
        "symbol": "AAPL",
        "company_name": "Apple",
        "listing_exchange": "NASDAQ",
        "side": "buy",
        "quantity": Decimal("2"),
        "bid": Decimal("1.00000000"),
        "ask": Decimal("1.00000001"),
        "exact_mid": Decimal("1.000000005"),
        "exec_price": Decimal("1.00000001"),
        "event_at": now,
        "collected_at": now,
        "observed_at": now,
        "age_seconds": 0,
        "notional": Decimal("2.00"),
        "cash_delta": Decimal("-2.00"),
        "cash_before": Decimal("10.00"),
        "cash_after": Decimal("8.00"),
        "held_before": Decimal("0"),
        "held_after": Decimal("2"),
        "session_date": now.date(),
        "session_opens_at": now,
        "session_closes_at": now,
        "authority": {
            "admissions": (),
            "calendar_generation": 1,
            "safety_epoch": 0,
            "unit_epoch": 0,
            "status_admission_generation": 1,
            "continuity_generation": 1,
            "status_sequence": 1,
        },
    }
    quote = QuoteOut.model_validate({**facts, "valid_until": now})
    receipt = FillOut.model_validate({**facts, "trade_id": "9007199254740994", "executed_at": now})
    output = receipt.model_dump(mode="json")
    assert output["exact_mid"] == "1.000000005"
    assert output["fee"] == "0"
    assert output["cash_after"] == "8.00"
    assert output["held_after"] == "2"
    assert output["coin_id"] == "9007199254740993"
    assert output["schema_version"] == 1
    assert "valid_until" not in output
    assert quote.model_dump(mode="json")["valid_until"]
    with pytest.raises(ValidationError):
        receipt.cash_after = Decimal("99")
    with pytest.raises(ValidationError):
        FillOut.model_validate({**facts, "trade_id": 1, "executed_at": now})
    with pytest.raises(ValidationError):
        FillOut.model_validate({**facts, "trade_id": "1", "executed_at": now, "fee": Decimal("1")})


def test_domain_error_has_no_unknown_success_default() -> None:
    from app.schemas.stock_trades import RefusalOut

    assert RefusalOut(code="market_closed").code == "market_closed"
    with pytest.raises(ValidationError):
        RefusalOut.model_validate({"code": "unexpected"})


def test_crypto_quantity_coercion_is_unchanged() -> None:
    from app.schemas.trades import QuoteIn as CryptoQuoteIn

    assert CryptoQuoteIn(symbol="BTC", side="buy", quantity=Decimal("0.1")).quantity == Decimal(
        "0.1"
    )
