from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # hide_input_in_errors keeps credentials in the URLs out of ValidationError text
    model_config = SettingsConfigDict(extra="ignore", hide_input_in_errors=True)

    env: Literal["dev", "test", "prod"]
    database_url: str = Field(repr=False)
    redis_url: str = Field(repr=False)
    otp_hmac_secret: SecretStr = Field(repr=False)
    jwt_secret: SecretStr = Field(repr=False)

    # Email: console logs codes (dev/test only); resend sends real mail (D-01).
    # The key lives only in the local git-ignored .env (D-02).
    email_backend: Literal["console", "resend"] = "console"
    resend_api_key: SecretStr | None = Field(default=None, repr=False)
    email_from: str | None = None

    # Rate limits (fixed windows, seconds). Per-IP defaults are loosened in dev only,
    # because all local browser traffic shares the Vite proxy's single IP.
    rl_request_email_limit: int = 5
    rl_request_email_window: int = 600
    rl_request_ip_limit: int = 20
    rl_request_ip_window: int = 3600
    rl_verify_email_limit: int = 10
    rl_verify_email_window: int = 600
    # Long-horizon cap so slow, steady guessing against one email stays bounded.
    rl_verify_email_daily_limit: int = 30
    rl_verify_email_daily_window: int = 86400
    rl_verify_ip_limit: int = 30
    rl_verify_ip_window: int = 600
    # Global send cap: a cost guard. A short window keeps recovery quick if abuse trips it.
    rl_send_global_limit: int = 100
    rl_send_global_window: int = 3600

    # Price freshness (D-03): the single definition shared by the API response,
    # the UI (via the response) and Phase 4's stale-trade refusal.
    price_fresh_seconds: int = 120
    price_stale_seconds: int = 300

    # Price refresh scheduler (PRICE-03/04). "fake" is dev/CI only and refused in prod.
    price_source: Literal["kraken", "fake"] = "kraken"
    price_poll_interval_seconds: int = 60
    price_max_move: Decimal = Decimal("0.25")
    price_confirm_tolerance: Decimal = Decimal("0.05")
    price_confirm_polls: int = 3

    # Trading costs (D-01, D-04, D-06): a simulated spread around mid plus a fee, a
    # minimum fee and a minimum order size. Settings, not literals, so prod can retune.
    trade_spread: Decimal = Decimal("0.0025")
    trade_fee_rate: Decimal = Decimal("0.0025")
    trade_min_fee_usd: Decimal = Decimal("0.01")
    trade_min_order_usd: Decimal = Decimal("1.00")

    @field_validator(
        "rl_request_email_limit",
        "rl_request_email_window",
        "rl_request_ip_limit",
        "rl_request_ip_window",
        "rl_verify_email_limit",
        "rl_verify_email_window",
        "rl_verify_email_daily_limit",
        "rl_verify_email_daily_window",
        "rl_verify_ip_limit",
        "rl_verify_ip_window",
        "rl_send_global_limit",
        "rl_send_global_window",
        "price_fresh_seconds",
        "price_stale_seconds",
    )
    @classmethod
    def _check_positive(cls, v: int, info: ValidationInfo) -> int:
        if v < 1:
            raise ValueError(f"{info.field_name} must be >= 1")
        return v

    @field_validator("price_max_move", "price_confirm_tolerance")
    @classmethod
    def _check_fraction(cls, v: Decimal, info: ValidationInfo) -> Decimal:
        if not (Decimal(0) < v < Decimal(1)):
            raise ValueError(f"{info.field_name} must be > 0 and < 1")
        return v

    @field_validator("price_confirm_polls")
    @classmethod
    def _check_confirm_polls(cls, v: int) -> int:
        if v < 2:
            raise ValueError("price_confirm_polls must be >= 2")
        return v

    @field_validator("price_poll_interval_seconds")
    @classmethod
    def _check_poll_interval(cls, v: int) -> int:
        if v < 10:
            raise ValueError("price_poll_interval_seconds must be >= 10")
        return v

    @field_validator("trade_spread", "trade_fee_rate")
    @classmethod
    def _check_trade_rate(cls, v: Decimal, info: ValidationInfo) -> Decimal:
        # zero is a legitimate configuration (no spread / no fee), unlike _check_fraction
        if not (Decimal(0) <= v < Decimal(1)):
            raise ValueError(f"{info.field_name} must be >= 0 and < 1")
        return v

    @field_validator("trade_min_fee_usd", "trade_min_order_usd")
    @classmethod
    def _check_trade_cents(cls, v: Decimal, info: ValidationInfo) -> Decimal:
        # amounts must sit on the cent grid, or cash arithmetic would need hidden rounding
        low_ok = v >= 0 if info.field_name == "trade_min_fee_usd" else v > 0
        if not low_ok or v != v.quantize(Decimal("0.01")):
            bound = ">= 0" if info.field_name == "trade_min_fee_usd" else "> 0"
            raise ValueError(f"{info.field_name} must be {bound} and a whole number of cents")
        return v

    @model_validator(mode="after")
    def _check_price_source(self) -> Settings:
        if self.env == "prod" and self.price_source == "fake":
            raise ValueError("price_source 'fake' is not allowed in prod")
        return self

    @field_validator("resend_api_key", "email_from", mode="before")
    @classmethod
    def _empty_to_none(cls, v: object) -> object:
        # docker compose passes "" for unset optional variables
        return None if v == "" else v

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
    def _check_price_freshness(self) -> Settings:
        if self.price_stale_seconds <= self.price_fresh_seconds:
            raise ValueError("price_stale_seconds must be greater than price_fresh_seconds")
        return self

    @model_validator(mode="after")
    def _check_email(self) -> Settings:
        if self.email_backend == "resend":
            if self.resend_api_key is None:
                raise ValueError("resend_api_key is required when email_backend is 'resend'")
            if self.email_from is None or "@" not in self.email_from:
                raise ValueError(
                    "email_from must contain an address when email_backend is 'resend'"
                )
        if self.env == "prod" and self.email_backend != "resend":
            raise ValueError("email_backend must be 'resend' in prod (console would log codes)")
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


class SchedulerSettings(BaseSettings):
    """Settings for the price scheduler container only (least privilege).

    The scheduler parses a third-party API, so it gets no token, OTP or email secrets:
    only the datastores and the price_* knobs. Validators mirror the matching ones in
    ``Settings``.
    """

    model_config = SettingsConfigDict(extra="ignore", hide_input_in_errors=True)

    env: Literal["dev", "test", "prod"]
    database_url: str = Field(repr=False)
    redis_url: str = Field(repr=False)

    price_source: Literal["kraken", "fake"] = "kraken"
    price_poll_interval_seconds: int = 60
    price_max_move: Decimal = Decimal("0.25")
    price_confirm_tolerance: Decimal = Decimal("0.05")
    price_confirm_polls: int = 3

    @field_validator("database_url")
    @classmethod
    def _check_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("database_url must start with 'postgresql+asyncpg://'")
        return v

    @field_validator("price_max_move", "price_confirm_tolerance")
    @classmethod
    def _check_fraction(cls, v: Decimal, info: ValidationInfo) -> Decimal:
        if not (Decimal(0) < v < Decimal(1)):
            raise ValueError(f"{info.field_name} must be > 0 and < 1")
        return v

    @field_validator("price_confirm_polls")
    @classmethod
    def _check_confirm_polls(cls, v: int) -> int:
        if v < 2:
            raise ValueError("price_confirm_polls must be >= 2")
        return v

    @field_validator("price_poll_interval_seconds")
    @classmethod
    def _check_poll_interval(cls, v: int) -> int:
        if v < 10:
            raise ValueError("price_poll_interval_seconds must be >= 10")
        return v

    @model_validator(mode="after")
    def _check_price_source(self) -> SchedulerSettings:
        if self.env == "prod" and self.price_source == "fake":
            raise ValueError("price_source 'fake' is not allowed in prod")
        return self


@lru_cache
def get_scheduler_settings() -> SchedulerSettings:
    return SchedulerSettings()
