from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import SchedulerSettings, Settings
from tests.test_db_connection import create_test_ca


def action_settings(**changes):
    return SchedulerSettings(
        env="test",
        database_url="postgresql+asyncpg://u:pw@h/db",
        redis_url="redis://:pw@h:6379/0",
        **changes,
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"stock_actions_enabled": True},
        {"stock_actions_enabled": True, "stock_actions_coverage_start": "2026-11-01T00:00:00Z"},
        {"stock_actions_coverage_start": "2026-11-01T00:00:00"},
        {"stock_actions_coverage_start": "2026-11-01T00:00:00+03:00"},
        {"stock_actions_poll_interval_seconds": 59},
        {"stock_actions_health_max_age_seconds": 121},
        {"stock_actions_max_attempts": 9},
        {"stock_actions_cycle_budget_seconds": 31},
        {"stock_actions_max_response_bytes": 262145},
        {"stock_actions_segment_days": 0},
        {"stock_actions_future_days": 89},
        {"stock_account_requests_per_minute": 201},
    ],
)
def test_action_settings_reject_missing_scope_and_unbounded_policy(changes):
    with pytest.raises(ValidationError):
        action_settings(**changes)


def test_action_settings_default_off_scheduler_only_and_secret_free():
    settings = action_settings(stock_actions_coverage_start="")
    assert not settings.stock_actions_enabled
    assert settings.stock_actions_coverage_start is None
    assert "stock_actions_enabled" not in Settings.model_fields
    settings = action_settings(
        stock_actions_enabled=True,
        stock_actions_coverage_start="2026-11-01T00:00:00Z",
        alpaca_api_key="synthetic-key",
        alpaca_secret_key="synthetic-secret",
    )
    assert "synthetic-key" not in repr(settings)


VALID_SECRET = "x" * 40
JWT = "j" * 40
DB = "postgresql+asyncpg://u:pw@h/db"
REDIS = "redis://:pw@h:6379/0"
FAKE_KEY = "dummy-key-not-real"
FROM = "Birja <login@example.com>"


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
            env="prod",
            email_backend="resend",
            resend_api_key=FAKE_KEY,
            email_from=FROM,
            database_url=DB,
            redis_url=REDIS,
            otp_hmac_secret=secret,
            jwt_secret=JWT,
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
            email_backend="resend",
            resend_api_key=FAKE_KEY,
            email_from=FROM,
            database_url=DB,
            redis_url=REDIS,
            otp_hmac_secret=VALID_SECRET,
            jwt_secret=secret,
        )

    assert "jwt_secret is still a placeholder" in str(exc_info.value)
    assert secret not in str(exc_info.value)


def _base(**kw: object) -> Settings:
    args: dict[str, object] = {
        "database_url": DB,
        "redis_url": REDIS,
        "otp_hmac_secret": VALID_SECRET,
        "jwt_secret": JWT,
        **kw,
    }
    return Settings(**args)  # type: ignore[arg-type]


def test_email_defaults_to_console() -> None:
    s = _base()
    assert s.email_backend == "console"
    assert s.resend_api_key is None
    assert s.email_from is None


def test_empty_email_strings_become_none() -> None:
    s = _base(resend_api_key="", email_from="")
    assert s.resend_api_key is None
    assert s.email_from is None


@pytest.mark.parametrize(
    "kw",
    [
        {"email_from": FROM},
        {"resend_api_key": FAKE_KEY},
        {"resend_api_key": FAKE_KEY, "email_from": "no-at-sign"},
    ],
)
def test_resend_requires_key_and_from(kw: dict[str, str]) -> None:
    with pytest.raises(ValidationError) as exc_info:
        _base(email_backend="resend", **kw)
    assert FAKE_KEY not in str(exc_info.value)


def test_prod_rejects_console_backend() -> None:
    with pytest.raises(ValidationError, match="must be 'resend' in prod"):
        _base(env="prod")


def test_prod_with_resend_is_valid_and_hides_key(tmp_path: Path) -> None:
    s = _base(
        env="prod",
        email_backend="resend",
        resend_api_key=FAKE_KEY,
        email_from=FROM,
        database_ssl_ca_file=create_test_ca(tmp_path),
    )
    assert s.email_backend == "resend"
    assert FAKE_KEY not in repr(s)


def test_env_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENV", raising=False)
    with pytest.raises(ValidationError) as exc_info:
        Settings(database_url=DB, redis_url=REDIS, otp_hmac_secret=VALID_SECRET, jwt_secret=JWT)

    assert "env" in str(exc_info.value).lower()


def test_env_explicit_dev_still_works() -> None:
    s = Settings(
        env="dev",
        database_url=DB,
        redis_url=REDIS,
        otp_hmac_secret=VALID_SECRET,
        jwt_secret=JWT,
    )

    assert s.env == "dev"
    assert s.rl_request_ip_limit == 200
