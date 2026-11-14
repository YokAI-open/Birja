"""Narrow transaction owner for retained-row dividend accounting.

The SQL function owns authority, financial arithmetic and immutable replay.
Its final advancing guard is the final business statement: only commit follows.
"""

import re
from dataclasses import dataclass
from typing import Literal, cast

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

DividendOutcome = Literal[
    "original", "applied", "held_uncertain", "held_unaffordable", "verified_no_change"
]


@dataclass(frozen=True, slots=True)
class DividendResult:
    payment_id: int
    decision_id: int | None
    outcome: DividendOutcome


class DividendRefused(ValueError):
    """Fixed operational code, never retained owner data or raw database text."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__("Dividend work is unavailable.")


def _id(value: int) -> None:
    if type(value) is not int or not 0 < value <= 9223372036854775807:
        raise DividendRefused("invalid_identity")


def _fingerprint(value: str) -> None:
    if type(value) is not str or len(value) != 64 or re.fullmatch("[0-9a-f]{64}", value) is None:
        raise DividendRefused("invalid_identity")


async def _invoke(db: AsyncSession, statement: str, work: dict[str, int | str]) -> DividendResult:
    if db.in_transaction():
        raise DividendRefused("transaction_active")
    try:
        async with db.begin():
            row = (await db.execute(text(statement), work)).one()
            result = DividendResult(
                row.payment_id, row.decision_id, cast(DividendOutcome, row.outcome)
            )
        return result
    except DBAPIError as exc:
        state = getattr(exc.orig, "sqlstate", None)
        code = {
            "22003": "numeric_range",
            "22023": "authority_unavailable",
            "P0002": "authority_unavailable",
        }.get(str(state), "financial_unavailable")
        raise DividendRefused(code) from None


async def process_dividend(
    db: AsyncSession,
    *,
    event_id: int,
    entitlement_id: int,
    expected_revision_fingerprint: str,
    expected_entitlement_fingerprint: str,
) -> DividendResult:
    """Attempt one verified target; SQL alone decides new authority or replay."""
    _id(event_id)
    _id(entitlement_id)
    _fingerprint(expected_revision_fingerprint)
    _fingerprint(expected_entitlement_fingerprint)
    return await _invoke(
        db,
        "SELECT * FROM public.apply_stock_dividend(:event_id,:entitlement_id,"
        ":revision_fingerprint,:entitlement_fingerprint)",
        {
            "event_id": event_id,
            "entitlement_id": entitlement_id,
            "revision_fingerprint": expected_revision_fingerprint,
            "entitlement_fingerprint": expected_entitlement_fingerprint,
        },
    )


async def record_dividend_hold(
    db: AsyncSession, *, payment_id: int, expected_revision_fingerprint: str
) -> DividendResult:
    """Record one current uncertainty observation for an existing paid anchor."""
    _id(payment_id)
    _fingerprint(expected_revision_fingerprint)
    return await _invoke(
        db,
        "SELECT * FROM public.record_stock_dividend_hold(:payment_id,:revision_fingerprint)",
        {"payment_id": payment_id, "revision_fingerprint": expected_revision_fingerprint},
    )
