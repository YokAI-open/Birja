import pytest
from pydantic import ValidationError

from app.core.config import Settings

DB = "postgresql+asyncpg://u:pw@h/db"
REDIS = "redis://:pw@h:6379/0"


def _settings(**kw: object) -> Settings:
    return Settings.model_validate(
        {
            "database_url": DB,
            "redis_url": REDIS,
            "otp_hmac_secret": "x" * 40,
            "jwt_secret": "j" * 40,
            **kw,
        }
    )


def test_rate_limit_defaults_strict_outside_dev() -> None:
    s = _settings(env="test")
    assert (s.rl_request_email_limit, s.rl_request_email_window) == (5, 600)
    assert (s.rl_request_ip_limit, s.rl_request_ip_window) == (20, 3600)
    assert (s.rl_verify_email_limit, s.rl_verify_ip_limit) == (10, 30)
    assert (s.rl_verify_email_daily_limit, s.rl_verify_email_daily_window) == (30, 86400)
    assert (s.rl_send_global_limit, s.rl_send_global_window) == (100, 3600)


def test_dev_loosens_ip_limits_unless_set_explicitly() -> None:
    dev = _settings(env="dev")
    assert (dev.rl_request_ip_limit, dev.rl_verify_ip_limit) == (200, 300)
    explicit = _settings(env="dev", rl_request_ip_limit=7, rl_verify_ip_limit=9)
    assert (explicit.rl_request_ip_limit, explicit.rl_verify_ip_limit) == (7, 9)


@pytest.mark.parametrize("bad", [0, -1])
def test_rate_limit_values_must_be_positive(bad: int) -> None:
    with pytest.raises(ValidationError):
        _settings(rl_request_email_limit=bad)
