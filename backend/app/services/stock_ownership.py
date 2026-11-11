"""Instrument-first ownership transactions; no order endpoint or opening mutation.

Phase 9 callers own a READ COMMITTED transaction: instrument gate, account,
holdings ordered by (user_id,id), immutable cause, then journal/holding and cash
in the SAME transaction. Never commit a fill before its movement. Callers must
also enforce admission, quote/session and action eligibility immediately before
execution. Trade.created_at is ingestion time, never economic ownership time.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import cast

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.corporate_action import (
    StockActionState,
    StockOwnershipMovement,
    StockSplitApplication,
)
from app.models.stock import StockInstrument
from app.models.trade import Holding, Trade
from app.models.user import Account
from app.services.corporate_action_rules import CutoffEvidence, _decimal


class OwnershipHeld(ValueError):
    """History or current authority cannot establish a safe automatic effect."""


@dataclass(frozen=True)
class StockMovementInput:
    user_id: int
    coin_id: int
    quantity: Decimal
    after_basis: Decimal
    causal_key: str
    trade_id: int | None = None
    application_id: int | None = None


async def acquire_stock_gate(db: AsyncSession, coin_id: int) -> datetime:
    """One instrument per transaction. Hash collisions only over-serialize.

    SQL/operator consumers MUST use exactly this stable namespace expression.
    Local timeouts bound waits and abandoned transactions; cancellation propagates
    to the caller's transaction context, which must roll back before reuse.
    """
    if type(coin_id) is not int or not 0 < coin_id <= 9007199254740991:
        raise OwnershipHeld("invalid_instrument")
    tx = db.get_transaction()
    previous = db.info.get("stock_gate")
    if previous is not None and previous[0] is tx and previous[1] != coin_id:
        raise OwnershipHeld("one_instrument_per_transaction")
    await db.execute(text("SET LOCAL lock_timeout = '5s'"))
    await db.execute(text("SET LOCAL statement_timeout = '10s'"))
    await db.execute(text("SET LOCAL idle_in_transaction_session_timeout = '30s'"))
    if (await db.execute(text("SHOW transaction_isolation"))).scalar_one() != "read committed":
        raise OwnershipHeld("read_committed_required")
    await db.execute(
        text(
            "SELECT pg_advisory_xact_lock(hashtextextended("
            "'birja.stock.instrument:' || CAST(:coin AS text),0))"
        ),
        {"coin": str(coin_id)},
    )
    await _clock(db)
    instrument = (
        await db.execute(select(StockInstrument.coin_id).where(StockInstrument.coin_id == coin_id))
    ).scalar_one_or_none()
    now = await _clock(db)
    if instrument is None:
        raise OwnershipHeld("invalid_instrument")
    db.info["stock_gate"] = (db.get_transaction(), coin_id)
    return now


async def _clock(db: AsyncSession) -> datetime:
    return cast(datetime, (await db.execute(select(func.clock_timestamp()))).scalar_one())


def _validate(movement: StockMovementInput) -> None:
    if (
        type(movement.user_id) is not int
        or not 0 < movement.user_id <= 9007199254740991
        or not isinstance(movement.quantity, Decimal)
        or not movement.quantity.is_finite()
        or not _decimal(abs(movement.quantity))
        or movement.quantity == 0
        or movement.quantity != movement.quantity.to_integral_value()
        or abs(movement.quantity) >= Decimal("1e12")
        or not _decimal(movement.after_basis, cents=True)
        or movement.after_basis >= Decimal("1e12")
        or not isinstance(movement.causal_key, str)
        or not 0 < len(movement.causal_key) <= 256
        or ((movement.trade_id is None) == (movement.application_id is None))
        or any(
            type(value) is not int or not 0 < value <= 9007199254740991
            for value in (movement.trade_id, movement.application_id)
            if value is not None
        )
    ):
        raise OwnershipHeld("invalid_movement")


async def append_stock_movement(
    db: AsyncSession, movement: StockMovementInput
) -> StockOwnershipMovement:
    """Append an exact matched immutable fill/split and holding change atomically.

    No caller economic timestamp exists. A replay returns the ORIGINAL row even
    when monitoring has since expired. No opening operation is exported.
    Scheduler splits use their verified application cutoff as economic time;
    new fills always use fresh DB wall time after every lock/authority read.
    """
    _validate(movement)
    await acquire_stock_gate(db, movement.coin_id)
    found = (
        await db.execute(
            select(StockOwnershipMovement).where(
                StockOwnershipMovement.coin_id == movement.coin_id,
                StockOwnershipMovement.user_id == movement.user_id,
                StockOwnershipMovement.causal_key == movement.causal_key,
            )
        )
    ).scalar_one_or_none()
    await _clock(db)
    if found is not None:
        if (found.quantity, found.after_basis, found.trade_id, found.application_id) != (
            movement.quantity,
            movement.after_basis,
            movement.trade_id,
            movement.application_id,
        ):
            raise OwnershipHeld("causal_conflict")
        return found
    duplicate_cause = (
        await db.execute(
            select(StockOwnershipMovement.id).where(
                StockOwnershipMovement.trade_id == movement.trade_id
                if movement.trade_id is not None
                else (StockOwnershipMovement.application_id == movement.application_id)
                & (StockOwnershipMovement.user_id == movement.user_id)
            )
        )
    ).scalar_one_or_none()
    await _clock(db)
    if duplicate_cause is not None:
        raise OwnershipHeld("causal_conflict")
    if movement.trade_id is not None:
        account = (
            await db.execute(
                select(Account.user_id).where(Account.user_id == movement.user_id).with_for_update()
            )
        ).scalar_one_or_none()
        await _clock(db)
        if account is None:
            raise OwnershipHeld("missing_account")
    holdings = (
        (
            await db.execute(
                select(Holding)
                .where(Holding.coin_id == movement.coin_id)
                .order_by(Holding.user_id, Holding.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        )
        .scalars()
        .all()
    )
    await _clock(db)
    state, rows = await assert_ownership_consistent(db, movement.coin_id)
    now = await _clock(db)
    holding = next((row for row in holdings if row.user_id == movement.user_id), None)
    before = Decimal(0) if holding is None else holding.quantity
    basis = Decimal(0) if holding is None else holding.cost_basis
    after = before + movement.quantity
    if after < 0 or after >= Decimal("1e12") or (after == 0 and movement.after_basis != 0):
        raise OwnershipHeld("invalid_result")
    economic_at = now
    if movement.trade_id is not None:
        trade = (
            await db.execute(
                select(Trade).where(
                    Trade.id == movement.trade_id,
                    Trade.coin_id == movement.coin_id,
                    Trade.user_id == movement.user_id,
                )
            )
        ).scalar_one_or_none()
        now = await _clock(db)
        economic_at = now
        if (
            trade is None
            or trade.quantity != abs(movement.quantity)
            or (trade.side == "buy") != (movement.quantity > 0)
        ):
            raise OwnershipHeld("fill_mismatch")
        if (
            state.health != "current"
            or state.valid_until is None
            or now >= state.valid_until
            or state.next_blocking_at is not None
            and now >= state.next_blocking_at
        ):
            raise OwnershipHeld("monitor_unavailable")
    else:
        application = (
            await db.execute(
                select(StockSplitApplication).where(
                    StockSplitApplication.id == movement.application_id,
                    StockSplitApplication.coin_id == movement.coin_id,
                )
            )
        ).scalar_one_or_none()
        now = await _clock(db)
        if (
            application is None
            or application.new_unit_epoch != state.unit_epoch
            or application.cutoff
            < (rows[-1].economic_at if rows else cast(datetime, state.journal_start_at))
            or movement.after_basis != basis
        ):
            raise OwnershipHeld("split_mismatch")
        from fractions import Fraction

        if Fraction(after) != Fraction(before) * Fraction(Decimal(application.new_rate)) / Fraction(
            Decimal(application.old_rate)
        ):
            raise OwnershipHeld("split_mismatch")
        economic_at = application.cutoff
    sequence = rows[-1].sequence + 1 if rows else 1
    row = StockOwnershipMovement(
        coin_id=movement.coin_id,
        user_id=movement.user_id,
        sequence=sequence,
        economic_at=economic_at,
        recorded_at=now,
        quantity=movement.quantity,
        before_quantity=before,
        after_quantity=after,
        before_basis=basis,
        after_basis=movement.after_basis,
        unit_epoch=state.unit_epoch,
        cause_kind="fill" if movement.trade_id is not None else "split",
        trade_id=movement.trade_id,
        application_id=movement.application_id,
        causal_key=movement.causal_key,
    )
    if holding is None:
        db.add(
            Holding(
                user_id=movement.user_id,
                coin_id=movement.coin_id,
                quantity=after,
                cost_basis=movement.after_basis,
            )
        )
    else:
        holding.quantity = after
        if movement.after_basis != basis:
            holding.cost_basis = movement.after_basis
    db.add(row)
    await db.flush()
    return row


async def assert_ownership_consistent(
    db: AsyncSession, coin_id: int
) -> tuple[StockActionState, list[StockOwnershipMovement]]:
    """Validate COMPLETE instrument history, including departed/zero owners.

    The app never updates state.sequence/health. Sequence allocation derives from
    the journal tail under the gate; state.sequence is a scheduler checkpoint and
    cannot exceed that tail. This works with the existing append-only app grants.
    """
    await acquire_stock_gate(db, coin_id)
    state = (
        await db.execute(
            select(StockActionState)
            .where(StockActionState.coin_id == coin_id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    await _clock(db)
    if state is None or state.journal_start_at is None or state.complete_from is None:
        raise OwnershipHeld("missing_baseline")
    rows = list(
        (
            await db.execute(
                select(StockOwnershipMovement)
                .where(StockOwnershipMovement.coin_id == coin_id)
                .order_by(StockOwnershipMovement.sequence)
            )
        )
        .scalars()
        .all()
    )
    await _clock(db)
    totals: dict[int, tuple[Decimal, Decimal]] = {}
    previous = state.journal_start_at
    for index, row in enumerate(rows, 1):
        if (
            row.sequence != index
            or row.economic_at < previous
            or row.recorded_at < row.economic_at
            or (row.before_quantity, row.before_basis)
            != totals.get(row.user_id, (Decimal(0), Decimal(0)))
        ):
            raise OwnershipHeld("history_gap")
        previous = row.economic_at
        totals[row.user_id] = (row.after_quantity, row.after_basis)
    if state.sequence > len(rows):
        raise OwnershipHeld("history_gap")
    holdings = (await db.execute(select(Holding).where(Holding.coin_id == coin_id))).scalars().all()
    await _clock(db)
    actual = {row.user_id: (row.quantity, row.cost_basis) for row in holdings}
    if any(
        actual.get(uid, (Decimal(0), Decimal(0))) != total for uid, total in totals.items()
    ) or any(total != totals.get(uid, (Decimal(0), Decimal(0))) for uid, total in actual.items()):
        raise OwnershipHeld("holding_mismatch")
    return state, rows


@dataclass(frozen=True)
class StockQuantitySnapshot:
    quantity: Decimal
    unit_epoch: int
    last_movement_sequence: int
    cutoff: CutoffEvidence


async def reconstruct_stock_quantity(
    db: AsyncSession, user_id: int, coin_id: int, cutoff: CutoffEvidence, units: int
) -> StockQuantitySnapshot:
    raise OwnershipHeld("unverified")
