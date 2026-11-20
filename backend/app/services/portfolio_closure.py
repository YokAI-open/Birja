"""Atomic terminal closure; no provider I/O or normal closed-book read surface."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.stock_ownership import (
    OwnershipHeld,
    _closure_instruments,
    _ClosureProofContext,
    assert_closure_ownership_consistent,
)


@dataclass(frozen=True)
class ClosureIntent:
    user_id: int
    portfolio_id: int
    intent_key: UUID
    confirmation_name: str
    policy_version: str = "freeze_at_closure_v1"


@dataclass(frozen=True)
class ClosureResult:
    portfolio_id: int
    outcome: Literal["closed", "confirmation_changed"]
    replayed: bool


async def close_owned_portfolio(db: AsyncSession, original: ClosureIntent) -> ClosureResult:
    """Map private transport dispositions without weakening the transaction proof."""
    try:
        result = await close_portfolio(db, original)
    except DBAPIError as exc:
        state = getattr(exc.orig, "sqlstate", None)
        message = getattr(getattr(exc.orig, "__cause__", None), "message", None)
        if state == "P0002" and message == "portfolio_unavailable":
            raise HTTPException(404, detail={"code": "portfolio_unavailable"}) from None
        if state == "23505" and message == "closure_intent_conflict":
            raise HTTPException(409, detail={"code": "closure_intent_conflict"}) from None
        if state == "P0001" and message == "closure_quota":
            now = datetime.now(UTC)
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            raise HTTPException(
                429,
                detail={"code": "closure_quota"},
                headers={"Retry-After": str(max(1, int((midnight - now).total_seconds()) + 1))},
            ) from None
        raise HTTPException(
            503, detail={"code": "service_unavailable"}, headers={"Retry-After": "5"}
        ) from None
    except OwnershipHeld:
        raise HTTPException(
            503, detail={"code": "service_unavailable"}, headers={"Retry-After": "5"}
        ) from None
    if result.outcome == "confirmation_changed":
        # The service already committed this durable terminal refusal. A delayed
        # original can only replay it, even if the current name changes back.
        raise HTTPException(409, detail={"code": "portfolio_confirmation_changed"})
    return result


async def close_portfolio(db: AsyncSession, original: ClosureIntent) -> ClosureResult:
    """Derive and prove the exact original under locks before committing.

    A40001 discards the entire attempt and rediscovers its instruments. Every
    other error rolls back. Commit/response loss is not a promise of rollback.
    The caller owns this business session; unrelated pending writes are refused.
    """
    if db.new or db.dirty or db.deleted or db.in_nested_transaction():
        raise OwnershipHeld("invalid_closure")
    if (
        not isinstance(original, ClosureIntent)
        or any(
            type(v) is not int or not 0 < v <= 9223372036854775807
            for v in (original.user_id, original.portfolio_id)
        )
        or not isinstance(original.intent_key, UUID)
        or original.intent_key.version != 4
        or type(original.confirmation_name) is not str
        or not 0 < len(original.confirmation_name) <= 60
        or original.policy_version != "freeze_at_closure_v1"
    ):
        raise OwnershipHeld("invalid_closure")
    attempt = 0
    while True:
        try:
            row = (
                await db.execute(
                    text("SELECT * FROM public.close_portfolio(:u,:p,:k,:n,:policy)"),
                    {
                        "u": original.user_id,
                        "p": original.portfolio_id,
                        "k": original.intent_key,
                        "n": original.confirmation_name,
                        "policy": original.policy_version,
                    },
                )
            ).one()
            if (
                row.portfolio_id != original.portfolio_id
                or row.outcome not in {"closed", "confirmation_changed"}
                or type(row.replayed) is not bool
            ):
                raise OwnershipHeld("invalid_closure")
            if row.outcome == "closed":
                db.info["portfolio_closure_proof"] = _ClosureProofContext(
                    db.get_transaction(),
                    original.user_id,
                    original.portfolio_id,
                    original.intent_key,
                    original.confirmation_name,
                    original.policy_version,
                    await _closure_instruments(db, original.portfolio_id),
                )
                await assert_closure_ownership_consistent(db)
            result = ClosureResult(row.portfolio_id, row.outcome, row.replayed)
            await db.commit()
            return result
        except DBAPIError as exc:
            await db.rollback()
            if getattr(exc.orig, "sqlstate", None) == "40001" and attempt < 2:
                attempt += 1
                continue
            raise
        except BaseException:
            await db.rollback()
            raise
        finally:
            db.info.pop("portfolio_closure_proof", None)
