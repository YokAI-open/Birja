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
