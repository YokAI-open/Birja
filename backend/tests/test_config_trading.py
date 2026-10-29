from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.config import SchedulerSettings, Settings

DB = "postgresql+asyncpg://u:pw@h/db"
REDIS = "redis://:pw@h:6379/0"


def _settings(**extra: object) -> Settings:
    return Settings(
        env="test",
        database_url=DB,
        redis_url=REDIS,
        otp_hmac_secret="x" * 40,  # type: ignore[arg-type]
        jwt_secret="j" * 40,  # type: ignore[arg-type]
        **extra,  # type: ignore[arg-type]
    )


def test_defaults_follow_decisions() -> None:
    s = _settings()
    assert s.trade_spread == Decimal("0.0025")
    assert s.trade_fee_rate == Decimal("0.0025")
    assert s.trade_min_fee_usd == Decimal("0.01")
    assert s.trade_min_order_usd == Decimal("1.00")


def test_env_overrides_parse_as_decimal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRADE_SPREAD", "0.005")
    monkeypatch.setenv("TRADE_FEE_RATE", "0")
    monkeypatch.setenv("TRADE_MIN_FEE_USD", "0.02")
    monkeypatch.setenv("TRADE_MIN_ORDER_USD", "5")
    s = _settings()
    assert s.trade_spread == Decimal("0.005")
    assert s.trade_fee_rate == Decimal("0")
    assert s.trade_min_fee_usd == Decimal("0.02")
    assert s.trade_min_order_usd == Decimal("5")


@pytest.mark.parametrize("name", ["trade_spread", "trade_fee_rate"])
@pytest.mark.parametrize("value", ["-0.001", "1", "1.5"])
def test_rates_out_of_range_refused(name: str, value: str) -> None:
    with pytest.raises(ValidationError, match=name):
        _settings(**{name: Decimal(value)})


@pytest.mark.parametrize("name", ["trade_spread", "trade_fee_rate"])
def test_zero_rate_is_allowed(name: str) -> None:
    assert getattr(_settings(**{name: Decimal("0")}), name) == Decimal("0")


@pytest.mark.parametrize("value", ["-0.01", "0.005"])
def test_min_fee_must_be_on_cent_grid(value: str) -> None:
    with pytest.raises(ValidationError, match="trade_min_fee_usd"):
        _settings(trade_min_fee_usd=Decimal(value))


def test_min_fee_zero_is_allowed() -> None:
    assert _settings(trade_min_fee_usd=Decimal("0")).trade_min_fee_usd == Decimal("0")


@pytest.mark.parametrize("value", ["0", "-1.00", "1.005"])
def test_min_order_must_be_positive_cents(value: str) -> None:
    with pytest.raises(ValidationError, match="trade_min_order_usd"):
        _settings(trade_min_order_usd=Decimal(value))


def test_scheduler_settings_have_no_trade_fields() -> None:
    assert not any(k.startswith("trade_") for k in SchedulerSettings.model_fields)
