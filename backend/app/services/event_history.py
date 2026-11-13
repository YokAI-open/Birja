"""Private mixed-event History and its bounded versioned cursor."""

import base64
import binascii
import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from fractions import Fraction
from typing import Any, cast

from sqlalchemy import literal, select, tuple_, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.corporate_action import (
    StockActionRevision,
    StockOwnershipMovement,
    StockSplitApplication,
)
from app.models.dividend import StockDividendDecision, StockDividendPayment
from app.models.price import Coin
from app.models.stock_execution import StockFillFacts
from app.models.trade import Trade
from app.schemas.event_history import EventDividend, EventHistoryPage

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


def _stamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _number(value: Decimal) -> str:
    # Database NUMERIC can preserve a signed zero; the public wire has one zero.
    return format(abs(value) if value == 0 else value, "f")


def _terms(row: StockDividendPayment | StockDividendDecision) -> dict[str, Any]:
    return {
        "eligible_quantity": _number(cast(Decimal, row.eligible_quantity)),
        "rate": _number(cast(Decimal, row.rate)),
        "cutoff": _stamp(cast(datetime, row.cutoff)),
        "ex_date": row.ex_date.isoformat() if row.ex_date is not None else None,
        "record_date": row.record_date.isoformat() if row.record_date is not None else None,
        "payable_date": cast(date, row.payable_date).isoformat(),
    }


def _dividend(row: StockDividendPayment) -> dict[str, Any]:
    return {
        "kind": "dividend",
        "id": f"dividend:{row.id}",
        "recorded_at": _stamp(row.recorded_at),
        "asset_type": "stock",
        "symbol": row.symbol,
        "name": row.company_name,
        "cash_delta": _number(row.original_amount),
        "payment_reference": f"dividend:{row.id}",
        "credited_amount": _number(row.original_amount),
        "credited_at": _stamp(row.recorded_at),
        **_terms(row),
    }


async def list_event_history(
    db: AsyncSession, *, user_id: int, limit: int = 25, cursor: str | None = None
) -> EventHistoryPage:
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("History limit must be between 1 and 100")
    if type(user_id) is not int or not 1 <= user_id <= MAX_ID:
        raise ValueError("Invalid History owner")
    boundary = decode_cursor(cursor) if cursor is not None else None
    # Every source is owner-filtered before the seek and the bounded lookahead.
    sources = union_all(
        select(
            Trade.created_at.label("recorded_at"),
            literal(4).label("kind_rank"),
            Trade.id.label("source_id"),
        ).where(Trade.user_id == user_id),
        select(StockDividendPayment.recorded_at, literal(3), StockDividendPayment.id).where(
            StockDividendPayment.user_id == user_id
        ),
        select(StockOwnershipMovement.recorded_at, literal(2), StockOwnershipMovement.id).where(
            StockOwnershipMovement.user_id == user_id, StockOwnershipMovement.cause_kind == "split"
        ),
        select(StockDividendDecision.recorded_at, literal(1), StockDividendDecision.id).where(
            StockDividendDecision.user_id == user_id
        ),
    ).subquery("owned_events")
    stmt = select(sources)
    if boundary is not None:
        stmt = stmt.where(
            tuple_(sources.c.recorded_at, sources.c.kind_rank, sources.c.source_id)
            < tuple_(
                literal(boundary.recorded_at),
                literal(boundary.kind_rank),
                literal(boundary.source_id),
            )
        )
    stmt = stmt.order_by(
        sources.c.recorded_at.desc(), sources.c.kind_rank.desc(), sources.c.source_id.desc()
    ).limit(limit + 1)
    rows = (await db.execute(stmt)).all()
    selected = rows[:limit]
    ids = {rank: [r.source_id for r in selected if r.kind_rank == rank] for rank in (1, 2, 3, 4)}
    projected: dict[tuple[int, int], Any] = {}
    if ids[4]:
        trades = (
            await db.execute(
                select(Trade, Coin, StockFillFacts)
                .join(Coin, Coin.id == Trade.coin_id)
                .outerjoin(
                    StockFillFacts,
                    (StockFillFacts.trade_id == Trade.id) & (StockFillFacts.user_id == user_id),
                )
                .where(Trade.user_id == user_id, Trade.id.in_(ids[4]))
            )
        ).all()
        for trade, coin, facts in trades:
            stock = coin.asset_class == "stock"
            if stock and facts is None:
                raise ValueError("Missing immutable stock fill facts")
            projected[(4, trade.id)] = {
                "kind": "trade",
                "id": f"trade:{trade.id}",
                "recorded_at": _stamp(trade.created_at),
                "asset_type": coin.asset_class,
                "symbol": facts.symbol if stock else coin.symbol,
                "name": facts.company_name if stock else coin.name,
                "cash_delta": _number(trade.cash_delta),
                "side": trade.side,
                "quantity": _number(trade.quantity),
                "exec_price": _number(trade.exec_price),
                "fee": _number(trade.fee),
                "filled_at": _stamp(trade.created_at),
                "source": facts.source if stock else None,
                "feed": facts.feed if stock else None,
                "quote_at": _stamp(facts.event_at) if stock else None,
            }
    if ids[3]:
        payments = (
            await db.scalars(
                select(StockDividendPayment).where(
                    StockDividendPayment.user_id == user_id, StockDividendPayment.id.in_(ids[3])
                )
            )
        ).all()
        for payment in payments:
            projected[(3, payment.id)] = _dividend(payment)
    if ids[2]:
        splits = (
            await db.execute(
                select(StockOwnershipMovement, StockSplitApplication, StockActionRevision)
                .join(
                    StockSplitApplication,
                    StockSplitApplication.id == StockOwnershipMovement.application_id,
                )
                .join(
                    StockActionRevision, StockActionRevision.id == StockSplitApplication.revision_id
                )
                .where(
                    StockOwnershipMovement.user_id == user_id,
                    StockOwnershipMovement.id.in_(ids[2]),
                    StockOwnershipMovement.cause_kind == "split",
                )
            )
        ).all()
        for movement, application, revision in splits:
            ratio = Fraction(Decimal(application.new_rate)) / Fraction(
                Decimal(application.old_rate)
            )
            # Older split state has no saved company name. Its retained symbol is
            # a truthful stable label; never recreate historical labels from catalog.
            symbol = revision.normalized_terms["symbol"]
            projected[(2, movement.id)] = {
                "kind": "split",
                "id": f"split:{movement.id}",
                "recorded_at": _stamp(movement.recorded_at),
                "asset_type": "stock",
                "symbol": symbol,
                "name": symbol,
                "cash_delta": "0",
                "ratio_new": str(ratio.numerator),
                "ratio_old": str(ratio.denominator),
                "quantity_before": _number(movement.before_quantity),
                "quantity_after": _number(movement.after_quantity),
                "cost_basis_before": _number(movement.before_basis),
                "cost_basis_after": _number(movement.after_basis),
                "effective_at": _stamp(movement.economic_at),
            }
    if ids[1]:
        corrections = (
            await db.execute(
                select(StockDividendDecision, StockDividendPayment)
                .join(
                    StockDividendPayment,
                    (StockDividendPayment.id == StockDividendDecision.payment_id)
                    & (StockDividendPayment.user_id == user_id),
                )
                .where(
                    StockDividendDecision.user_id == user_id, StockDividendDecision.id.in_(ids[1])
                )
            )
        ).all()
        for decision, original in corrections:
            projected[(1, decision.id)] = {
                "kind": "dividend_correction",
                "id": f"dividend_correction:{decision.id}",
                "recorded_at": _stamp(decision.recorded_at),
                "asset_type": "stock",
                "symbol": decision.symbol,
                "name": decision.company_name,
                "cash_delta": _number(decision.applied_delta),
                "payment_reference": f"dividend:{original.id}",
                "decision_reference": f"dividend_correction:{decision.id}",
                "outcome": decision.outcome,
                "reason": decision.reason,
                "desired_total": _number(decision.desired_total)
                if decision.desired_total is not None
                else None,
                "cumulative_applied_before": _number(decision.cumulative_applied_before),
                "proposed_delta": _number(decision.proposed_delta)
                if decision.proposed_delta is not None
                else None,
                "applied_delta": _number(decision.applied_delta),
                "terms": None if decision.outcome == "held_uncertain" else _terms(decision),
                "original": EventDividend(**_dividend(original)),
            }
    items = [projected[(row.kind_rank, row.source_id)] for row in selected]
    next_cursor = None
    if len(rows) > limit:
        last = selected[-1]
        next_cursor = encode_cursor(
            EventHistoryCursor(last.recorded_at, last.kind_rank, last.source_id)
        )
    return EventHistoryPage(items=items, next_cursor=next_cursor)
