import base64
import binascii
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import literal, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price import Coin
from app.models.trade import Trade
from app.schemas.history import HistoryItem, HistoryPage

MAX_ID = 9223372036854775807
TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z")


class InvalidCursor(ValueError):
    """The untrusted cursor does not match the bounded versioned contract."""


@dataclass(frozen=True)
class HistoryCursor:
    created_at: datetime
    id: int


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise InvalidCursor()
        obj[key] = value
    return obj


def decode_cursor(value: str) -> HistoryCursor:
    try:
        if not 1 <= len(value) <= 512 or re.fullmatch(r"[A-Za-z0-9_-]+", value) is None:
            raise InvalidCursor()
        raw = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
        if base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != value:
            raise InvalidCursor()
        decoded = raw.decode("utf-8")
        obj = json.loads(decoded, object_pairs_hook=_object)
        if not isinstance(obj, dict) or set(obj) != {"v", "created_at", "id"}:
            raise InvalidCursor()
        if json.dumps(obj, separators=(",", ":"), ensure_ascii=True) != decoded:
            raise InvalidCursor()
        if type(obj["v"]) is not int or obj["v"] != 1:
            raise InvalidCursor()
        stamp, identifier = obj["created_at"], obj["id"]
        if not isinstance(stamp, str) or TIMESTAMP.fullmatch(stamp) is None:
            raise InvalidCursor()
        if not isinstance(identifier, str) or re.fullmatch(r"[1-9][0-9]{0,18}", identifier) is None:
            raise InvalidCursor()
        if int(identifier) > MAX_ID:
            raise InvalidCursor()
        return HistoryCursor(created_at=datetime.fromisoformat(stamp), id=int(identifier))
    except (ValueError, TypeError, UnicodeError, binascii.Error) as exc:
        raise InvalidCursor() from exc


def encode_cursor(value: HistoryCursor) -> str:
    if value.created_at.tzinfo is None or value.created_at.utcoffset() is None:
        raise InvalidCursor()
    obj = {
        "v": 1,
        "created_at": value.created_at.astimezone(UTC)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z"),
        "id": str(value.id),
    }
    encoded = (
        base64.urlsafe_b64encode(json.dumps(obj, separators=(",", ":")).encode())
        .decode()
        .rstrip("=")
    )
    decode_cursor(encoded)
    return encoded


async def list_history(
    db: AsyncSession, *, user_id: int, limit: int = 25, cursor: str | None = None
) -> HistoryPage:
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("History limit must be between 1 and 100")
    boundary = decode_cursor(cursor) if cursor is not None else None
    stmt = (
        select(
            Trade.id,
            Trade.created_at,
            Coin.symbol,
            Coin.name,
            Trade.side,
            Trade.quantity,
            Trade.exec_price,
            Trade.fee,
            Trade.cash_delta.label("total"),
        )
        .join(Coin, Coin.id == Trade.coin_id)
        .where(Trade.user_id == user_id)
        .order_by(Trade.created_at.desc(), Trade.id.desc())
        .limit(limit + 1)
    )
    if boundary is not None:
        stmt = stmt.where(
            tuple_(Trade.created_at, Trade.id)
            < tuple_(literal(boundary.created_at), literal(boundary.id))
        )
    rows = (await db.execute(stmt)).all()
    items = [HistoryItem(**{**row._mapping, "id": str(row.id)}) for row in rows[:limit]]
    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = encode_cursor(HistoryCursor(created_at=last.created_at, id=last.id))
    return HistoryPage(items=items, next_cursor=next_cursor)
