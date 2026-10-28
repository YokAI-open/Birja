import pytest
from pydantic import ValidationError

from app.core.config import Settings

DB = "postgresql+asyncpg://u:pw@h/db"
REDIS = "redis://:pw@h:6379/0"


def _settings(**extra: int) -> Settings:
    return Settings(
        env="test",
        database_url=DB,
        redis_url=REDIS,
        otp_hmac_secret="x" * 40,
        jwt_secret="j" * 40,
        **extra,
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
