from typing import Any, Literal

from pydantic import BaseModel, EmailStr, field_validator


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
