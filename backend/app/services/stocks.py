"""Authenticated discovery projection; no provider requests or execution."""

from datetime import UTC, datetime


def _now() -> datetime:
    return datetime.now(UTC)


async def list_stocks(db, settings, *, now=_now):
    """Assemble catalogue-first discovery (implementation follows behavioral RED)."""
    return {"items": []}
