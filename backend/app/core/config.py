from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.db.connection import database_ssl_context, validate_database_url


class _StockSettings(BaseSettings):
    """Shared nonsecret stock bounds; these settings confer no product rights."""

    stock_data_enabled: bool = False
    stock_feed: Literal["iex"] = "iex"
    stock_poll_interval_seconds: int = Field(default=60, ge=60, le=120)
    stock_request_timeout_seconds: int = Field(default=5, ge=1, le=10)
    stock_max_retries: int = Field(default=1, ge=0, le=2)
    stock_cycle_budget_seconds: int = Field(default=15, ge=1, le=20)
    stock_max_response_bytes: int = Field(default=262144, ge=4096, le=1048576)
    stock_data_account: str = Field(default="birja", min_length=1, max_length=128)
    stock_data_server: str = Field(default="birja", min_length=1, max_length=128)

    @model_validator(mode="after")
    def _check_stock_budget(self) -> _StockSettings:
        if (
            self.stock_request_timeout_seconds * (self.stock_max_retries + 1)
            > self.stock_cycle_budget_seconds
        ):
            raise ValueError("stock request/retry budget exceeds stock cycle budget")
        if not self.stock_data_account.strip() or not self.stock_data_server.strip():
            raise ValueError("stock account/server scope must be nonblank")
        return self


class Settings(_StockSettings):
    # hide_input_in_errors keeps credentials in the URLs out of ValidationError text
    model_config = SettingsConfigDict(extra="ignore", hide_input_in_errors=True)

    env: Literal["dev", "test", "prod"]
    database_url: str = Field(repr=False)
    database_ssl_ca_file: str | None = Field(default=None, repr=False)
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
        return validate_database_url(v)

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

    @model_validator(mode="after")
    def _check_database_trust(self) -> Settings:
        database_ssl_context(self)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


class SchedulerSettings(_StockSettings):
    """Settings for the price scheduler container only (least privilege).

    The scheduler parses a third-party API, so it gets no token, OTP or email secrets:
    only the datastores and the price_* knobs. Validators mirror the matching ones in
    ``Settings``.
    """

    model_config = SettingsConfigDict(extra="ignore", hide_input_in_errors=True)

    env: Literal["dev", "test", "prod"]
    database_url: str = Field(repr=False)
    database_ssl_ca_file: str | None = Field(default=None, repr=False)
    redis_url: str = Field(repr=False)

    price_source: Literal["kraken", "fake"] = "kraken"
    price_poll_interval_seconds: int = 60
    price_max_move: Decimal = Decimal("0.25")
    price_confirm_tolerance: Decimal = Decimal("0.05")
    price_confirm_polls: int = 3

    # Provider credentials belong only in the dedicated scheduler environment.
    alpaca_api_key: SecretStr | None = Field(default=None, repr=False)
    alpaca_secret_key: SecretStr | None = Field(default=None, repr=False)

    # Internal safety caps, never a provider entitlement or service guarantee.
    stock_actions_enabled: bool = False
    stock_actions_poll_interval_seconds: int = Field(default=60, ge=60, le=120)
    stock_actions_health_max_age_seconds: int = Field(default=120, ge=1, le=120)
    stock_actions_max_attempts: int = Field(default=8, ge=1, le=8)
    stock_actions_cycle_budget_seconds: int = Field(default=30, ge=1, le=30)
    stock_actions_max_response_bytes: int = Field(default=262144, ge=1, le=262144)
    stock_actions_segment_days: int = Field(default=31, ge=1, le=366)
    stock_actions_future_days: int = Field(default=90, ge=90, le=90)
    stock_actions_coverage_start: datetime | None = None
    stock_account_requests_per_minute: int = Field(default=20, ge=1, le=200)

    @field_validator("stock_actions_coverage_start", mode="before")
    @classmethod
    def _empty_action_baseline(cls, value: object) -> object:
        return None if value == "" else value

    @model_validator(mode="after")
    def _check_action_policy(self) -> SchedulerSettings:
        baseline = self.stock_actions_coverage_start
        if baseline is not None and (
            baseline.tzinfo is None or baseline.utcoffset() != UTC.utcoffset(baseline)
        ):
            raise ValueError("action coverage start must be UTC")
        if self.stock_actions_enabled and baseline is None:
            raise ValueError("enabled action scheduler requires reviewed coverage start")
        return self

    @field_validator("alpaca_api_key", "alpaca_secret_key", mode="before")
    @classmethod
    def _empty_provider_secret(cls, value: object) -> object:
        return None if value == "" else value

    @model_validator(mode="after")
    def _check_stock_credentials(self) -> SchedulerSettings:
        if (self.stock_data_enabled or self.stock_actions_enabled) and any(
            value is None or not value.get_secret_value().strip()
            for value in (self.alpaca_api_key, self.alpaca_secret_key)
        ):
            raise ValueError("enabled stock scheduler requires both provider credentials")
        return self

    @field_validator("database_url")
    @classmethod
    def _check_database_url(cls, v: str) -> str:
        return validate_database_url(v)

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

    @model_validator(mode="after")
    def _check_database_trust(self) -> SchedulerSettings:
        database_ssl_context(self)
        return self


@lru_cache
def get_scheduler_settings() -> SchedulerSettings:
    return SchedulerSettings()
