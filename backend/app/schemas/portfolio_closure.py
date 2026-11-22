"""Strict immutable review context; names never confer portfolio authority."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.schemas.portfolios import PortfolioId, _name


def _key(value: str) -> str:
    parsed = UUID(value)
    if parsed.version != 4 or str(parsed) != value:
        raise ValueError("canonical UUIDv4 required")
    return value


def _reviewed_name(value: str) -> str:
    if _name(value) != value:
        raise ValueError("canonical reviewed name required")
    return value


class PortfolioClosure(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent_key: Annotated[
        str, Field(strict=True, min_length=36, max_length=36), AfterValidator(_key)
    ]
    confirmation_name: Annotated[
        str, Field(strict=True, min_length=1, max_length=60), AfterValidator(_reviewed_name)
    ]
    policy_version: Literal["freeze_at_closure_v1"]


class PortfolioClosureReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    portfolio_id: PortfolioId
    state: Literal["closed"] = "closed"
