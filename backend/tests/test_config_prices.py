from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.config import Settings

DB = "postgresql+asyncpg://u:pw@h/db"
REDIS = "redis://:pw@h:6379/0"


def _settings(env: str = "test", **extra: object) -> Settings:
    return Settings(
        env=env,  # type: ignore[arg-type]
        database_url=DB,
        redis_url=REDIS,
        otp_hmac_secret="x" * 40,  # type: ignore[arg-type]
        jwt_secret="j" * 40,  # type: ignore[arg-type]
        **extra,  # type: ignore[arg-type]
    )


def test_defaults_follow_d03() -> None:
    s = _settings()
    assert s.price_fresh_seconds == 120
    assert s.price_stale_seconds == 300


@pytest.mark.parametrize("name", ["price_fresh_seconds", "price_stale_seconds"])
@pytest.mark.parametrize("value", [0, -5])
def test_non_positive_refused(name: str, value: int) -> None:
    with pytest.raises(ValidationError, match="must be >= 1"):
        _settings(**{name: value})


@pytest.mark.parametrize("stale", [120, 60])
def test_stale_must_exceed_fresh(stale: int) -> None:
    with pytest.raises(ValidationError, match="price_stale_seconds must be greater"):
        _settings(price_fresh_seconds=120, price_stale_seconds=stale)


def test_scheduler_defaults() -> None:
    s = _settings()
    assert s.price_source == "kraken"
    assert s.price_poll_interval_seconds == 60
    assert s.price_max_move == Decimal("0.25")
    assert s.price_confirm_tolerance == Decimal("0.05")
    assert s.price_confirm_polls == 3


def test_fake_source_refused_in_prod() -> None:
    with pytest.raises(ValidationError, match="price_source 'fake' is not allowed in prod"):
        _settings(
            env="prod",
            price_source="fake",
            email_backend="resend",
            resend_api_key="k",
            email_from="a@b.co",
        )


@pytest.mark.parametrize("env", ["dev", "test"])
def test_fake_source_allowed_outside_prod(env: str) -> None:
    assert _settings(env=env, price_source="fake").price_source == "fake"


@pytest.mark.parametrize("name", ["price_max_move", "price_confirm_tolerance"])
@pytest.mark.parametrize("value", ["0", "1", "-0.1", "1.5"])
def test_fractions_must_be_between_0_and_1(name: str, value: str) -> None:
    with pytest.raises(ValidationError, match="must be > 0 and < 1"):
        _settings(**{name: Decimal(value)})


def test_confirm_polls_at_least_two() -> None:
    with pytest.raises(ValidationError, match="price_confirm_polls must be >= 2"):
        _settings(price_confirm_polls=1)


def test_poll_interval_at_least_ten() -> None:
    with pytest.raises(ValidationError, match="price_poll_interval_seconds must be >= 10"):
        _settings(price_poll_interval_seconds=9)
