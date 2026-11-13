"""Private mixed-event History and its bounded versioned cursor."""

from dataclasses import dataclass
from datetime import datetime


class InvalidCursor(ValueError):
    """Untrusted cursor violates the mixed-event contract."""


@dataclass(frozen=True)
class EventHistoryCursor:
    recorded_at: datetime
    kind_rank: int
    source_id: int


def encode_cursor(value: EventHistoryCursor) -> str:
    raise InvalidCursor()


def decode_cursor(value: str) -> EventHistoryCursor:
    raise InvalidCursor()
