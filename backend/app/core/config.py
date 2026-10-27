from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # hide_input_in_errors keeps credentials in the URLs out of ValidationError text
    model_config = SettingsConfigDict(extra="ignore", hide_input_in_errors=True)

    env: Literal["dev", "test", "prod"] = "dev"
    database_url: str = Field(repr=False)
    redis_url: str = Field(repr=False)
    otp_hmac_secret: SecretStr = Field(repr=False)

    @field_validator("database_url")
    @classmethod
    def _check_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("database_url must start with 'postgresql+asyncpg://'")
        return v

    @field_validator("otp_hmac_secret")
    @classmethod
    def _check_otp_secret_length(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 32:
            raise ValueError("otp_hmac_secret must be at least 32 characters")
        return v

    @model_validator(mode="after")
    def _refuse_placeholder_secret_in_prod(self) -> Settings:
        if self.env == "prod" and self.otp_hmac_secret.get_secret_value().lower().startswith(
            "change-me"
        ):
            raise ValueError("otp_hmac_secret is still a placeholder; set a real secret in prod")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
