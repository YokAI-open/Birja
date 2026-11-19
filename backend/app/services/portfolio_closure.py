"""Atomic terminal closure; no provider I/O or normal closed-book read surface."""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

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
            type(v) is not int or not 0 < v <= 9007199254740991
            for v in (original.user_id, original.portfolio_id)
        )
        or not isinstance(original.intent_key, UUID)
        or original.intent_key.version != 4
        or type(original.confirmation_name) is not str
        or not 0 < len(original.confirmation_name) <= 60
        or original.policy_version != "freeze_at_closure_v1"
    ):
        raise OwnershipHeld("invalid_closure")
    for attempt in range(3):
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
                continue
            raise
        except BaseException:
            await db.rollback()
            raise
        finally:
            db.info.pop("portfolio_closure_proof", None)
    raise OwnershipHeld("invalid_closure")
