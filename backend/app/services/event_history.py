"""Private mixed-event History and its bounded versioned cursor."""

import base64
import binascii
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

MAX_ID = 9223372036854775807
TIMESTAMP = re.compile(r"[1-9][0-9]{3}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z")


class InvalidCursor(ValueError):
    """Untrusted cursor violates the mixed-event contract."""


@dataclass(frozen=True)
class EventHistoryCursor:
    recorded_at: datetime
    kind_rank: int
    source_id: int


def encode_cursor(value: EventHistoryCursor) -> str:
    if value.recorded_at.tzinfo is None or value.recorded_at.utcoffset() is None:
        raise InvalidCursor()
    if type(value.source_id) is not int:
        raise InvalidCursor()
    obj = {
        "v": 2,
        "recorded_at": value.recorded_at.astimezone(UTC)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z"),
        "kind_rank": value.kind_rank,
        "source_id": str(value.source_id),
    }
    encoded = (
        base64.urlsafe_b64encode(json.dumps(obj, separators=(",", ":")).encode())
        .decode()
        .rstrip("=")
    )
    decode_cursor(encoded)
    return encoded


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise InvalidCursor()
        obj[key] = value
    return obj


def decode_cursor(value: str) -> EventHistoryCursor:
    try:
        if (
            not isinstance(value, str)
            or not 1 <= len(value) <= 512
            or re.fullmatch(r"[A-Za-z0-9_-]+", value) is None
        ):
            raise InvalidCursor()
        raw = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
        if base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != value:
            raise InvalidCursor()
        decoded = raw.decode("utf-8")
        obj = json.loads(decoded, object_pairs_hook=_object)
        if not isinstance(obj, dict) or set(obj) != {"v", "recorded_at", "kind_rank", "source_id"}:
            raise InvalidCursor()
        if json.dumps(obj, separators=(",", ":"), ensure_ascii=True) != decoded:
            raise InvalidCursor()
        if type(obj["v"]) is not int or obj["v"] != 2:
            raise InvalidCursor()
        stamp, rank, identifier = obj["recorded_at"], obj["kind_rank"], obj["source_id"]
        if not isinstance(stamp, str) or TIMESTAMP.fullmatch(stamp) is None:
            raise InvalidCursor()
        if type(rank) is not int or rank not in (1, 2, 3, 4):
            raise InvalidCursor()
        if not isinstance(identifier, str) or re.fullmatch(r"[1-9][0-9]{0,18}", identifier) is None:
            raise InvalidCursor()
        if int(identifier) > MAX_ID:
            raise InvalidCursor()
        return EventHistoryCursor(datetime.fromisoformat(stamp), rank, int(identifier))
    except (ValueError, TypeError, UnicodeError, binascii.Error) as exc:
        raise InvalidCursor() from exc
