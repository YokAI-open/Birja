from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # hide_input_in_errors keeps credentials in the URLs out of ValidationError text
    model_config = SettingsConfigDict(extra="ignore", hide_input_in_errors=True)

    env: Literal["dev", "test", "prod"] = "dev"
    database_url: str = Field(repr=False)
    redis_url: str = Field(repr=False)
    otp_hmac_secret: SecretStr = Field(repr=False)
    jwt_secret: SecretStr = Field(repr=False)

    # Rate limits (fixed windows, seconds). Per-IP defaults are loosened in dev only,
    # because all local browser traffic shares the Vite proxy's single IP.
    rl_request_email_limit: int = 5
    rl_request_email_window: int = 600
    rl_request_ip_limit: int = 20
    rl_request_ip_window: int = 3600
    rl_verify_email_limit: int = 10
    rl_verify_email_window: int = 600
    rl_verify_ip_limit: int = 30
    rl_verify_ip_window: int = 600
    rl_send_global_limit: int = 500
    rl_send_global_window: int = 86400

    @field_validator(
        "rl_request_email_limit",
        "rl_request_email_window",
        "rl_request_ip_limit",
        "rl_request_ip_window",
        "rl_verify_email_limit",
        "rl_verify_email_window",
        "rl_verify_ip_limit",
        "rl_verify_ip_window",
        "rl_send_global_limit",
        "rl_send_global_window",
    )
    @classmethod
    def _check_positive(cls, v: int, info: ValidationInfo) -> int:
        if v < 1:
            raise ValueError(f"{info.field_name} must be >= 1")
        return v

    @field_validator("database_url")
    @classmethod
    def _check_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("database_url must start with 'postgresql+asyncpg://'")
        return v

    @field_validator("otp_hmac_secret", "jwt_secret")
    @classmethod
    def _check_secret_length(cls, v: SecretStr, info: ValidationInfo) -> SecretStr:
        if len(v.get_secret_value()) < 32:
            raise ValueError(f"{info.field_name} must be at least 32 characters")
        return v

    @model_validator(mode="after")
    def _dev_ip_limits(self) -> Settings:
        # Playwright and manual runs all come from one IP in dev; keep the strict
        # defaults for test/prod and let an explicit env value win.
        if self.env == "dev":
            if "rl_request_ip_limit" not in self.model_fields_set:
                self.rl_request_ip_limit = 200
            if "rl_verify_ip_limit" not in self.model_fields_set:
                self.rl_verify_ip_limit = 300
        return self

    @model_validator(mode="after")
    def _check_secrets(self) -> Settings:
        if self.jwt_secret.get_secret_value() == self.otp_hmac_secret.get_secret_value():
            raise ValueError("jwt_secret must differ from otp_hmac_secret")
        if self.env == "prod":
            for name in ("otp_hmac_secret", "jwt_secret"):
                if getattr(self, name).get_secret_value().lower().startswith("change-me"):
                    raise ValueError(f"{name} is still a placeholder; set a real secret in prod")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
