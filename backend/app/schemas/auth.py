from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class RequestCodeIn(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def _normalize(cls, v: Any) -> Any:
        return v.strip().lower() if isinstance(v, str) else v

    @field_validator("email", mode="after")
    @classmethod
    def _max_length(cls, v: str) -> str:
        if len(v) > 254:
            raise ValueError("email is too long")
        return v


class CodeSentOut(BaseModel):
    status: Literal["code_sent"]


class VerifyCodeIn(RequestCodeIn):
    code: str = Field(pattern=r"^\d{6}$")


class MeOut(BaseModel):
    email: str
    cash_usd: Decimal = Field(description="USD cash balance, serialized as a decimal string")
