"""Private portfolio metadata; metadata never grants financial authority."""

import unicodedata
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, PlainSerializer, model_validator

PortfolioId = Annotated[
    int,
    Field(gt=0, le=9223372036854775807),
    PlainSerializer(str, return_type=str, when_used="json"),
]


class PortfolioSummary(BaseModel):
    id: PortfolioId
    name: str


# Unicode White_Space, deliberately excluding Python's extra C0 separators.
_WHITE_SPACE = (
    "\u0009\u000a\u000b\u000c\u000d\u0020\u0085\u00a0\u1680"
    + "".join(chr(cp) for cp in range(0x2000, 0x200B))
    + "\u2028\u2029\u202f\u205f\u3000"
)


def _name(value: str) -> str:
    if any(ord(c) < 32 or 127 <= ord(c) <= 159 or 0xD800 <= ord(c) <= 0xDFFF for c in value):
        raise ValueError("name contains forbidden controls")
    display = unicodedata.normalize("NFC", value.strip(_WHITE_SPACE))
    if not 1 <= len(display) <= 60:
        raise ValueError("name must contain 1 to 60 normalized Unicode scalars")
    # Uniqueness and persisted replay equivalence belong exclusively to SQL.
    return display


def _description(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    if any(
        (ord(c) < 32 and c not in "\t\n") or 127 <= ord(c) <= 159 or 0xD800 <= ord(c) <= 0xDFFF
        for c in value
    ):
        raise ValueError("description contains forbidden controls")
    if len(value) > 1000:
        raise ValueError("description must contain at most 1000 normalized Unicode scalars")
    return value


Name = Annotated[str, Field(strict=True), AfterValidator(_name)]
Description = Annotated[str, Field(strict=True), AfterValidator(_description)]


class PortfolioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Name
    description: Description = ""


class PortfolioPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Defaults represent omission only. Explicit null fails strict string parsing.
    name: Name = Field(default="", validate_default=False)
    description: Description = ""

    @model_validator(mode="after")
    def _nonempty(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("include name or description")
        return self


class PortfolioMetadata(PortfolioSummary):
    description: str
