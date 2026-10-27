import pytest
from pydantic import ValidationError

from app.core.config import Settings

VALID_SECRET = "x" * 40
DB = "postgresql+asyncpg://u:pw@h/db"
REDIS = "redis://:pw@h:6379/0"


def test_invalid_database_url_error_hides_password() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            database_url="postgresql://u:SuperSecret@h/db",
            redis_url="redis://:pw@h:6379/0",
            otp_hmac_secret=VALID_SECRET,
        )

    assert "database_url must start with" in str(exc_info.value)
    assert "SuperSecret" not in str(exc_info.value)


def test_short_otp_secret_rejected_without_leaking_it() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(database_url=DB, redis_url=REDIS, otp_hmac_secret="short-secret-value")

    assert "at least 32" in str(exc_info.value)
    assert "short-secret-value" not in str(exc_info.value)


def test_placeholder_otp_secret_rejected_in_prod() -> None:
    secret = "change-me-dev-only-otp-hmac-secret-0123456789"
    with pytest.raises(ValidationError) as exc_info:
        Settings(env="prod", database_url=DB, redis_url=REDIS, otp_hmac_secret=secret)

    assert "placeholder" in str(exc_info.value)
    assert secret not in str(exc_info.value)


def test_placeholder_otp_secret_allowed_in_dev() -> None:
    s = Settings(
        env="dev",
        database_url=DB,
        redis_url=REDIS,
        otp_hmac_secret="change-me-dev-only-otp-hmac-secret-0123456789",
    )
    assert s.env == "dev"
