"""Atomic whole-share execution using shared cash and immutable stock receipts.

Lock order is instrument gate, account, then all instrument holders through the
ownership helper. After deferred constraints, the invoker guard is the final
business SQL statement; commit alone follows it.
"""

import json
from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import bindparam, select, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.corporate_action import StockOwnershipMovement
from app.models.price import Coin
from app.models.stock_execution import StockFillFacts
from app.models.trade import Holding, Trade
from app.models.user import Account
from app.schemas.stock_trades import (
    ActionFacts,
    AdmissionIdentity,
    AuthorityIdentity,
    ContextOut,
    FillOut,
    PriceChangedOut,
    QuoteFacts,
    QuoteIn,
    QuoteOut,
    SessionFacts,
    StatusFacts,
    TradeIn,
)
from app.services.stock_eligibility import LoadedExecution, load_execution_evidence
from app.services.stock_ownership import (
    OwnershipHeld,
    StockMovementInput,
    acquire_stock_gate,
    append_stock_movement,
)
from app.services.stock_trade_math import StockTradePlan, buy_max_quantity, plan_stock_trade
from app.services.trade_idempotency import find_user_trade, require_same_order
from app.services.trade_math import Q2, TradeRefused

ZERO = Decimal(0)


class PriceChanged(TradeRefused):
    def __init__(self, quote: QuoteOut, previous: Decimal) -> None:
        super().__init__("price_changed", "The price moved. Review and confirm again.")
        before = (previous * quote.quantity).quantize(Q2)
        if quote.side == "buy":
            before = -before
        self.detail = PriceChangedOut(
            previous_exec_price=previous,
            previous_cash_delta=before,
            exec_price_change=quote.exec_price - previous,
            cash_delta_change=quote.cash_delta - before,
            quote=quote,
        )
        self.quote = quote


def _refuse(code: str) -> TradeRefused:
    return TradeRefused(code, "This stock order is unavailable. Refresh and review again.")


def _encoded(value: object) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    raise TypeError("Unsupported stock fact")


def _authority(loaded: LoadedExecution) -> AuthorityIdentity:
    e = loaded.evidence
    return AuthorityIdentity(
        admissions=tuple(
            AdmissionIdentity(
                product=cast(Any, a.product),
                generation=a.generation,
                row_hash=a.row_hash,
                valid_until=a.valid_until,
            )
            for a in e.admissions
        ),
        calendar_generation=e.calendar_generation,
        safety_epoch=e.safety_epoch,
        unit_epoch=e.unit_epoch,
        status_admission_generation=e.status.admission_generation,
        continuity_generation=e.status.continuity_generation,
        status_sequence=e.status.sequence,
    )


def _require(loaded: LoadedExecution) -> None:
    if not loaded.decision.allowed:
        raise _refuse(loaded.decision.reason)


async def _instrument(db: AsyncSession, symbol: str) -> int:
    cid = (
        await db.execute(
            select(Coin.id).where(
                Coin.symbol == symbol,
                Coin.asset_class == "stock",
                Coin.is_active,
            )
        )
    ).scalar_one_or_none()
    if cid is None:
        raise _refuse("quote_unavailable")
    return cid


async def _financial(db: AsyncSession, uid: int, cid: int) -> tuple[Decimal, Decimal, Decimal]:
    row = (
        await db.execute(
            select(Account.cash, Holding.quantity, Holding.cost_basis)
            .outerjoin(Holding, (Holding.user_id == Account.user_id) & (Holding.coin_id == cid))
            .where(Account.user_id == uid)
        )
    ).one()
    return row.cash, row.quantity or ZERO, row.cost_basis or ZERO


def _plan(
    loaded: LoadedExecution, order: QuoteIn, cash: Decimal, held: Decimal, basis: Decimal
) -> StockTradePlan:
    _require(loaded)
    q = loaded.evidence.quote
    return plan_stock_trade(
        side=order.side,
        quantity=order.quantity,
        bid=cast(Decimal, q.bid),
        ask=cast(Decimal, q.ask),
        cash=cash,
        held=held,
        cost_basis=basis,
    )


def _preview(loaded: LoadedExecution, plan: StockTradePlan) -> QuoteOut:
    e, d, q = loaded.evidence, loaded.decision, loaded.evidence.quote
    return QuoteOut(
        coin_id=str(e.coin_id),
        provider_asset_id=e.provider_asset_id,
        symbol=loaded.symbol,
        company_name=loaded.company_name,
        listing_exchange=cast(Any, loaded.listing_exchange),
        side=plan.side,
        quantity=plan.quantity,
        bid=plan.bid,
        ask=plan.ask,
        exact_mid=plan.exact_mid,
        exec_price=plan.exec_price,
        event_at=q.event_at,
        collected_at=q.collected_at,
        observed_at=d.evaluated_at,
        age_seconds=int((d.evaluated_at - cast(datetime, q.event_at)).total_seconds()),
        notional=plan.notional,
        fee=ZERO,
        cash_delta=plan.cash_delta,
        cash_before=plan.cash_before,
        cash_after=plan.cash_after,
        held_before=plan.held_before,
        held_after=plan.held_after,
        session_date=e.session_date,
        session_opens_at=e.opens_at,
        session_closes_at=e.closes_at,
        authority=_authority(loaded),
        valid_until=d.valid_until,
    )


async def quote(db: AsyncSession, *, user_id: int, order: QuoteIn, settings: Settings) -> QuoteOut:
    cid = await _instrument(db, order.symbol)
    cash, held, basis = await _financial(db, user_id, cid)
    loaded = await load_execution_evidence(db, cid, settings)
    return _preview(loaded, _plan(loaded, order, cash, held, basis))


def _receipt(trade: Trade, facts: StockFillFacts, executed: datetime) -> FillOut:
    raw = facts.authority
    authority = AuthorityIdentity(
        admissions=tuple(
            AdmissionIdentity.model_validate(
                {k: a[k] for k in ("product", "generation", "row_hash", "valid_until")}
            )
            for a in raw["admissions"]
        ),
        calendar_generation=raw["calendar_generation"],
        safety_epoch=raw["safety_epoch"],
        unit_epoch=raw["unit_epoch"],
        status_admission_generation=raw["status"]["admission_generation"],
        continuity_generation=raw["status"]["continuity_generation"],
        status_sequence=raw["status"]["sequence"],
    )
    return FillOut(
        trade_id=str(trade.id),
        executed_at=executed,
        coin_id=str(facts.coin_id),
        provider_asset_id=facts.provider_asset_id,
        symbol=facts.symbol,
        company_name=facts.company_name,
        listing_exchange=cast(Any, facts.listing_exchange),
        side=cast(Any, trade.side),
        quantity=trade.quantity,
        bid=facts.bid,
        ask=facts.ask,
        exact_mid=facts.exact_mid,
        exec_price=trade.exec_price,
        event_at=facts.event_at,
        collected_at=facts.collected_at,
        observed_at=facts.observed_at,
        age_seconds=int((facts.observed_at - facts.event_at).total_seconds()),
        notional=abs(trade.cash_delta),
        fee=trade.fee,
        cash_delta=trade.cash_delta,
        cash_before=trade.cash_after - trade.cash_delta,
        cash_after=trade.cash_after,
        held_before=facts.held_after - trade.quantity
        if trade.side == "buy"
        else facts.held_after + trade.quantity,
        held_after=facts.held_after,
        session_date=facts.session_date,
        session_opens_at=facts.opens_at,
        session_closes_at=facts.closes_at,
        authority=authority,
    )


async def _replay(db: AsyncSession, user_id: int, order: TradeIn) -> FillOut | None:
    trade = await find_user_trade(db, user_id, order.idempotency_key)
    if trade is None:
        return None
    # Historical stock replay joins no current catalogue, rights or holding.
    row = (
        await db.execute(
            select(StockFillFacts, StockOwnershipMovement.economic_at)
            .join(
                StockOwnershipMovement, StockOwnershipMovement.trade_id == StockFillFacts.trade_id
            )
            .where(StockFillFacts.trade_id == trade.id, StockFillFacts.user_id == user_id)
        )
    ).one_or_none()
    if row is None:
        kind = (
            await db.execute(select(Coin.asset_class).where(Coin.id == trade.coin_id))
        ).scalar_one()
        if kind != "stock":
            require_same_order(
                trade, same_instrument=False, side=order.side, kind="quantity", value=order.quantity
            )
        raise _refuse("receipt_unavailable")
    facts, executed = row
    require_same_order(
        trade,
        same_instrument=facts.symbol == order.symbol,
        side=order.side,
        kind="quantity",
        value=order.quantity,
    )
    try:
        return _receipt(trade, facts, executed)
    except KeyError, TypeError, ValueError:
        raise _refuse("receipt_unavailable") from None


async def execute(
    db: AsyncSession, *, user_id: int, order: TradeIn, settings: Settings
) -> tuple[FillOut, bool]:
    try:
        prior = await _replay(db, user_id, order)
        if prior is not None:
            await db.rollback()
            return prior, False
        cid = await _instrument(db, order.symbol)
        await acquire_stock_gate(db, cid)
        account = (
            await db.execute(
                select(Account)
                .where(Account.user_id == user_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalar_one()
        prior = await _replay(db, user_id, order)
        if prior is not None:
            await db.rollback()
            return prior, False
        cash, held, basis = await _financial(db, user_id, cid)
        loaded = await load_execution_evidence(db, cid, settings)
        plan = _plan(loaded, order, cash, held, basis)
        if plan.exec_price != order.expected_exec_price:
            raise PriceChanged(_preview(loaded, plan), order.expected_exec_price)
        trade = Trade(
            user_id=user_id,
            coin_id=cid,
            side=order.side,
            input_kind="quantity",
            input_value=plan.quantity,
            quantity=plan.quantity,
            mid_price=plan.mid,
            price_as_of=loaded.evidence.quote.event_at,
            exec_price=plan.exec_price,
            fee=ZERO,
            cash_delta=plan.cash_delta,
            cash_after=plan.cash_after,
            idempotency_key=order.idempotency_key,
        )
        db.add(trade)
        await db.flush()
        movement = await append_stock_movement(
            db,
            StockMovementInput(
                user_id=user_id,
                coin_id=cid,
                quantity=plan.quantity if order.side == "buy" else -plan.quantity,
                after_basis=plan.cost_basis_after,
                causal_key=f"trade:{trade.id}",
                trade_id=trade.id,
            ),
        )
        current = await load_execution_evidence(db, cid, settings)
        _require(current)
        if current.evidence.quote != loaded.evidence.quote:
            replacement = _plan(current, order, cash, held, basis)
            if replacement.exec_price != order.expected_exec_price:
                raise PriceChanged(_preview(current, replacement), order.expected_exec_price)
            # Already inserted immutable Trade metadata must not be rewritten.
            raise _refuse("quote_unavailable")
        authority = json.loads(json.dumps(asdict(current.evidence), default=_encoded))
        e, q = current.evidence, current.evidence.quote
        facts = StockFillFacts(
            trade_id=trade.id,
            coin_id=cid,
            user_id=user_id,
            provider_asset_id=e.provider_asset_id,
            symbol=current.symbol,
            company_name=current.company_name,
            listing_exchange=current.listing_exchange,
            source="alpaca",
            feed="iex",
            bid=q.bid,
            ask=q.ask,
            exact_mid=plan.exact_mid,
            held_after=movement.after_quantity,
            event_at=q.event_at,
            collected_at=q.collected_at,
            observed_at=current.decision.evaluated_at,
            session_date=e.session_date,
            opens_at=e.opens_at,
            closes_at=e.closes_at,
            authority=authority,
        )
        db.add(facts)
        account.cash = plan.cash_after
        fill = _receipt(trade, facts, movement.economic_at)
        await db.flush()
        await db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        # LAST business SQL: no refresh, read, helper or provider await follows.
        await db.execute(
            text(
                "SELECT public.assert_stock_execution_current(:trade,:user,:authority)"
            ).bindparams(bindparam("authority", type_=JSONB)),
            {"trade": trade.id, "user": user_id, "authority": authority},
        )
        await db.commit()
        return fill, True
    except IntegrityError as exc:
        await db.rollback()
        if "uq_trades_user_idempotency_key" in str(exc.orig):
            try:
                prior = await _replay(db, user_id, order)
                if prior is not None:
                    return prior, False
            finally:
                await db.rollback()
        raise
    except OwnershipHeld:
        await db.rollback()
        raise _refuse("action_unavailable") from None
    except DBAPIError as exc:
        await db.rollback()
        if getattr(exc.orig, "sqlstate", None) == "22023":
            raise _refuse("quote_unavailable") from None
        raise
    except BaseException:
        await db.rollback()
        raise


async def context(db: AsyncSession, *, user_id: int, symbol: str, settings: Settings) -> ContextOut:
    cid = await _instrument(db, symbol)
    cash, held, basis = await _financial(db, user_id, cid)
    loaded = await load_execution_evidence(db, cid, settings)
    if not loaded.symbol or loaded.decision.reason == "permission_unavailable":
        raise _refuse("permission_unavailable")
    e, d, q = loaded.evidence, loaded.decision, loaded.evidence.quote
    safe_quote = d.allowed or d.reason in ("market_closed", "halted")
    quote_facts = None
    if safe_quote and all(
        value is not None for value in (q.bid, q.ask, q.event_at, q.collected_at, q.session_date)
    ):
        quote_facts = QuoteFacts(
            bid=q.bid,
            ask=q.ask,
            exact_mid=(cast(Decimal, q.bid) + cast(Decimal, q.ask)) / 2,
            event_at=q.event_at,
            collected_at=q.collected_at,
            session_date=q.session_date,
            admission_generation=q.admission_generation,
            unit_epoch=q.unit_epoch,
        )
    maximum = ZERO
    if d.allowed:
        maximum = buy_max_quantity(
            bid=cast(Decimal, q.bid),
            ask=cast(Decimal, q.ask),
            cash=cash,
            held=held,
            cost_basis=basis,
        )
    return ContextOut(
        coin_id=str(cid),
        provider_asset_id=e.provider_asset_id,
        symbol=loaded.symbol,
        company_name=loaded.company_name,
        listing_exchange=cast(Any, loaded.listing_exchange),
        observed_at=d.evaluated_at,
        cash=cash,
        held_quantity=held,
        buy_max_quantity=maximum,
        quote=quote_facts,
        session=SessionFacts(
            state=e.session_state,
            session_date=e.session_date,
            opens_at=e.opens_at,
            closes_at=e.closes_at,
            valid_until=e.session_valid_until,
        ),
        status=StatusFacts(
            **{k: v for k, v in asdict(e.status).items() if k in StatusFacts.model_fields}
        ),
        action=ActionFacts(
            state="current" if e.action_current else "unknown",
            reason="available" if e.action_current else "monitor_unavailable",
            valid_until=e.action_valid_until,
            next_blocking_at=e.next_blocking_at,
        ),
        authority=_authority(loaded),
        execution_enabled=d.allowed,
        execution_reason=d.reason,
        valid_until=d.valid_until,
    )
