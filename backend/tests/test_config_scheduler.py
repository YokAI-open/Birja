from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.config import SchedulerSettings, get_scheduler_settings

DB = "postgresql+asyncpg://u:pw@h/db"
REDIS = "redis://:pw@h:6379/0"
APP_SECRETS = ("OTP_HMAC_SECRET", "JWT_SECRET", "RESEND_API_KEY", "EMAIL_FROM", "EMAIL_BACKEND")


def _settings(env: str = "test", **extra: object) -> SchedulerSettings:
    return SchedulerSettings(
        env=env,  # type: ignore[arg-type]
        database_url=DB,
        redis_url=REDIS,
        **extra,  # type: ignore[arg-type]
    )


def test_needs_no_app_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in APP_SECRETS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("DATABASE_URL", DB)
    monkeypatch.setenv("REDIS_URL", REDIS)
    monkeypatch.setenv("PRICE_SOURCE", "kraken")
    get_scheduler_settings.cache_clear()
    try:
        s = get_scheduler_settings()
    finally:
        get_scheduler_settings.cache_clear()
    assert s.env == "prod"
    assert not hasattr(s, "jwt_secret")
    assert not hasattr(s, "otp_hmac_secret")
    assert not hasattr(s, "resend_api_key")


def test_secrets_in_env_are_ignored_not_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "j" * 40)
    s = _settings()
    assert "jwt_secret" not in s.model_dump()


def test_defaults_match_backend_settings() -> None:
    s = _settings()
    assert s.price_source == "kraken"
    assert s.price_poll_interval_seconds == 60
    assert s.price_max_move == Decimal("0.25")
    assert s.price_confirm_tolerance == Decimal("0.05")
    assert s.price_confirm_polls == 3


def test_fake_source_refused_in_prod() -> None:
    with pytest.raises(ValidationError, match="price_source 'fake' is not allowed in prod"):
        _settings(env="prod", price_source="fake")


@pytest.mark.parametrize("env", ["dev", "test"])
def test_fake_source_allowed_outside_prod(env: str) -> None:
    assert _settings(env=env, price_source="fake").price_source == "fake"


def test_database_url_must_be_asyncpg() -> None:
    with pytest.raises(ValidationError, match="must start with 'postgresql\\+asyncpg://'"):
        SchedulerSettings(env="test", database_url="postgresql://u@h/db", redis_url=REDIS)


def test_urls_are_not_in_repr() -> None:
    text = repr(_settings())
    assert "pw" not in text


@pytest.mark.parametrize("name", ["price_max_move", "price_confirm_tolerance"])
@pytest.mark.parametrize("value", ["0", "1", "-0.1", "1.5"])
def test_fractions_must_be_between_0_and_1(name: str, value: str) -> None:
    with pytest.raises(ValidationError, match=f"{name} must be > 0 and < 1"):
        _settings(**{name: Decimal(value)})


def test_confirm_polls_at_least_2() -> None:
    with pytest.raises(ValidationError, match="price_confirm_polls must be >= 2"):
        _settings(price_confirm_polls=1)
    assert _settings(price_confirm_polls=2).price_confirm_polls == 2


def test_poll_interval_at_least_10() -> None:
    with pytest.raises(ValidationError, match="price_poll_interval_seconds must be >= 10"):
        _settings(price_poll_interval_seconds=9)
    assert _settings(price_poll_interval_seconds=10).price_poll_interval_seconds == 10


def test_unknown_env_refused() -> None:
    with pytest.raises(ValidationError):
        _settings(env="staging")
