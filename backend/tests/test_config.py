import pytest
from pydantic import ValidationError

from app.core.config import Settings

VALID_SECRET = "x" * 40
JWT = "j" * 40
DB = "postgresql+asyncpg://u:pw@h/db"
REDIS = "redis://:pw@h:6379/0"


def test_invalid_database_url_error_hides_password() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            database_url="postgresql://u:SuperSecret@h/db",
            redis_url="redis://:pw@h:6379/0",
            otp_hmac_secret=VALID_SECRET,
            jwt_secret=JWT,
        )

    assert "database_url must start with" in str(exc_info.value)
    assert "SuperSecret" not in str(exc_info.value)


def test_short_otp_secret_rejected_without_leaking_it() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            database_url=DB, redis_url=REDIS, otp_hmac_secret="short-secret-value", jwt_secret=JWT
        )

    assert "at least 32" in str(exc_info.value)
    assert "short-secret-value" not in str(exc_info.value)


def test_placeholder_otp_secret_rejected_in_prod() -> None:
    secret = "change-me-dev-only-otp-hmac-secret-0123456789"
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            env="prod", database_url=DB, redis_url=REDIS, otp_hmac_secret=secret, jwt_secret=JWT
        )

    assert "placeholder" in str(exc_info.value)
    assert secret not in str(exc_info.value)


def test_placeholder_otp_secret_allowed_in_dev() -> None:
    s = Settings(
        env="dev",
        database_url=DB,
        redis_url=REDIS,
        otp_hmac_secret="change-me-dev-only-otp-hmac-secret-0123456789",
        jwt_secret=JWT,
    )
    assert s.env == "dev"


def test_short_jwt_secret_rejected_without_leaking_it() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            database_url=DB, redis_url=REDIS, otp_hmac_secret=VALID_SECRET, jwt_secret="tiny-jwt"
        )

    assert "jwt_secret must be at least 32" in str(exc_info.value)
    assert "tiny-jwt" not in str(exc_info.value)


def test_jwt_secret_must_differ_from_otp_secret() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            database_url=DB, redis_url=REDIS, otp_hmac_secret=VALID_SECRET, jwt_secret=VALID_SECRET
        )

    assert "must differ" in str(exc_info.value)
    assert VALID_SECRET not in str(exc_info.value)


def test_placeholder_jwt_secret_rejected_in_prod() -> None:
    secret = "change-me-dev-only-jwt-secret-abcdefghijklmnop"
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            env="prod",
            database_url=DB,
            redis_url=REDIS,
            otp_hmac_secret=VALID_SECRET,
            jwt_secret=secret,
        )

    assert "jwt_secret is still a placeholder" in str(exc_info.value)
    assert secret not in str(exc_info.value)
