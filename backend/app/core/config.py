from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    env: Literal["dev", "test", "prod"] = "dev"
    database_url: str = Field(repr=False)
    redis_url: str = Field(repr=False)

    @field_validator("database_url")
    @classmethod
    def _check_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("database_url must start with 'postgresql+asyncpg://'")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
