"""Atomic whole-share execution using shared cash and immutable stock receipts.

Lock order is instrument gate, account, then all instrument holders through the
ownership helper. After deferred constraints, the invoker guard is the final
business SQL statement; commit alone follows it.
"""

import json
from dataclasses import asdict
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Any, cast
from uuid import UUID

from fastapi import HTTPException
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
from app.services.portfolios import OwnedActivePortfolio
from app.services.stock_eligibility import LoadedExecution, load_execution_evidence
from app.services.stock_halts import REPORT_LOCK_KEYS
from app.services.stock_halts import SOURCE as REPORTED_HALT_SOURCE
from app.services.stock_ownership import (
    OwnershipHeld,
    StockMovementInput,
    acquire_stock_gate,
    append_stock_movement,
)
from app.services.stock_trade_math import StockTradePlan, buy_max_quantity, plan_stock_trade
from app.services.stock_trading_rules import ValuationEvidence, evaluate_valuation
from app.services.trade_idempotency import find_user_trade, require_same_order
from app.services.trade_math import Q2, TradeRefused

ZERO = Decimal(0)


class PriceChanged(TradeRefused):
    def __init__(self, quote: QuoteOut, previous: Decimal) -> None:
        super().__init__("price_changed", "The price moved. Review and confirm again.")
        with localcontext() as ctx:
            ctx.prec = 64
            before = (previous * quote.quantity).quantize(Q2, rounding=ROUND_HALF_EVEN)
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


async def _account(
    db: AsyncSession, portfolio: OwnedActivePortfolio, *, lock: bool = False
) -> Account:
    query = (
        select(Account)
        .where(
            Account.id == portfolio.portfolio_id,
            Account.user_id == portfolio.user_id,
            Account.closed_at.is_(None),
        )
        .execution_options(populate_existing=True)
    )
    if lock:
        query = query.with_for_update()
    account = (await db.execute(query)).scalar_one_or_none()
    if account is None:
        raise HTTPException(404, detail={"code": "portfolio_unavailable"})
    return account


async def _financial(
    db: AsyncSession, portfolio: OwnedActivePortfolio, cid: int
) -> tuple[Decimal, Decimal, Decimal]:
    row = (
        await db.execute(
            select(Account.cash, Holding.quantity, Holding.cost_basis)
            .outerjoin(
                Holding,
                (Holding.portfolio_id == Account.id)
                & (Holding.user_id == Account.user_id)
                & (Holding.coin_id == cid),
            )
            .where(
                Account.id == portfolio.portfolio_id,
                Account.user_id == portfolio.user_id,
                Account.closed_at.is_(None),
            )
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(404, detail={"code": "portfolio_unavailable"})
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


def _preview(
    loaded: LoadedExecution, plan: StockTradePlan, portfolio: OwnedActivePortfolio
) -> QuoteOut:
    e, d, q = loaded.evidence, loaded.decision, loaded.evidence.quote
    return QuoteOut(
        portfolio_id=str(portfolio.portfolio_id),
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


async def _book_stock_trade(
    db: AsyncSession,
    portfolio: OwnedActivePortfolio,
    coin_id: int,
    plan: StockTradePlan,
    event_at: datetime,
    idempotency_key: UUID,
) -> tuple[Trade, StockOwnershipMovement]:
    trade = Trade(
        user_id=portfolio.user_id,
        portfolio_id=portfolio.portfolio_id,
        coin_id=coin_id,
        side=plan.side,
        input_kind="quantity",
        input_value=plan.quantity,
        quantity=plan.quantity,
        mid_price=plan.mid,
        price_as_of=event_at,
        exec_price=plan.exec_price,
        fee=ZERO,
        cash_delta=plan.cash_delta,
        cash_after=plan.cash_after,
        idempotency_key=idempotency_key,
    )
    db.add(trade)
    await db.flush()
    movement = await append_stock_movement(
        db,
        StockMovementInput(
            user_id=portfolio.user_id,
            portfolio_id=portfolio.portfolio_id,
            coin_id=coin_id,
            quantity=plan.quantity if plan.side == "buy" else -plan.quantity,
            after_basis=plan.cost_basis_after,
            causal_key=f"trade:{trade.id}",
            trade_id=trade.id,
        ),
    )
    return trade, movement


async def quote(
    db: AsyncSession, *, portfolio: OwnedActivePortfolio, order: QuoteIn, settings: Settings
) -> QuoteOut:
    await _account(db, portfolio)
    cid = await _instrument(db, order.symbol)
    cash, held, basis = await _financial(db, portfolio, cid)
    loaded = await load_execution_evidence(db, cid, settings)
    return _preview(loaded, _plan(loaded, order, cash, held, basis), portfolio)


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
        portfolio_id=str(trade.portfolio_id),
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


async def _replay(
    db: AsyncSession, portfolio: OwnedActivePortfolio, order: TradeIn
) -> FillOut | None:
    trade = await find_user_trade(db, portfolio.user_id, order.idempotency_key)
    if trade is None:
        return None
    require_same_order(
        trade,
        same_instrument=trade.portfolio_id == portfolio.portfolio_id,
        portfolio_id=portfolio.portfolio_id,
        side=order.side,
        kind="quantity",
        value=order.quantity,
    )
    # Historical stock replay joins no current catalogue, rights or holding.
    row = (
        await db.execute(
            select(StockFillFacts, StockOwnershipMovement.economic_at)
            .join(
                StockOwnershipMovement, StockOwnershipMovement.trade_id == StockFillFacts.trade_id
            )
            .where(
                StockFillFacts.trade_id == trade.id,
                StockFillFacts.user_id == portfolio.user_id,
                StockFillFacts.portfolio_id == portfolio.portfolio_id,
                StockOwnershipMovement.portfolio_id == portfolio.portfolio_id,
            )
        )
    ).one_or_none()
    if row is None:
        kind = (
            await db.execute(select(Coin.asset_class).where(Coin.id == trade.coin_id))
        ).scalar_one()
        if kind != "stock":
            require_same_order(
                trade,
                same_instrument=False,
                side=order.side,
                kind="quantity",
                value=order.quantity,
                portfolio_id=portfolio.portfolio_id,
            )
        raise _refuse("receipt_unavailable")
    facts, executed = row
    require_same_order(
        trade,
        same_instrument=facts.symbol == order.symbol and "catalog_id" not in facts.authority,
        portfolio_id=portfolio.portfolio_id,
        side=order.side,
        kind="quantity",
        value=order.quantity,
    )
    try:
        return _receipt(trade, facts, executed)
    except KeyError, TypeError, ValueError:
        raise _refuse("receipt_unavailable") from None


class _ExecutionRefreshed(Exception):
    """Tentative immutable metadata must be rebuilt after a full rollback."""


async def execute(
    db: AsyncSession, *, portfolio: OwnedActivePortfolio, order: TradeIn, settings: Settings
) -> tuple[FillOut, bool]:
    # Exactly one clean rebuild for quote metadata; never retry deadlock, timeout,
    # cancellation, ownership, constraint or permission failure. All authority and
    # cash locks are reacquired. A changed selected price still needs confirmation.
    try:
        return await _execute_once(db, portfolio=portfolio, order=order, settings=settings)
    except _ExecutionRefreshed:
        try:
            return await _execute_once(db, portfolio=portfolio, order=order, settings=settings)
        except _ExecutionRefreshed:
            raise _refuse("quote_unavailable") from None


async def _execute_once(
    db: AsyncSession, *, portfolio: OwnedActivePortfolio, order: TradeIn, settings: Settings
) -> tuple[FillOut, bool]:
    try:
        await _account(db, portfolio)
        historical = await find_user_trade(db, portfolio.user_id, order.idempotency_key)
        if historical is not None:
            stock_cause = await db.scalar(
                select(StockFillFacts.trade_id).where(
                    StockFillFacts.trade_id == historical.id,
                    ~StockFillFacts.authority.has_key("catalog_id"),  # noqa: W601
                )
            )
            if stock_cause is None:
                require_same_order(
                    historical,
                    same_instrument=False,
                    portfolio_id=portfolio.portfolio_id,
                    side=order.side,
                    kind="quantity",
                    value=order.quantity,
                )
            await acquire_stock_gate(db, historical.coin_id)
            await _account(db, portfolio, lock=True)
            prior = await _replay(db, portfolio, order)
            if prior is not None:
                await db.rollback()
                return prior, False
        cid = await _instrument(db, order.symbol)
        await acquire_stock_gate(db, cid)
        account = await _account(db, portfolio, lock=True)
        prior = await _replay(db, portfolio, order)
        if prior is not None:
            await db.rollback()
            return prior, False
        cash, held, basis = await _financial(db, portfolio, cid)
        loaded = await load_execution_evidence(db, cid, settings)
        plan = _plan(loaded, order, cash, held, basis)
        if plan.exec_price != order.expected_exec_price:
            raise PriceChanged(_preview(loaded, plan, portfolio), order.expected_exec_price)
        trade, movement = await _book_stock_trade(
            db,
            portfolio,
            cid,
            plan,
            cast(datetime, loaded.evidence.quote.event_at),
            order.idempotency_key,
        )
        current = await load_execution_evidence(db, cid, settings)
        _require(current)
        if current.evidence.quote != loaded.evidence.quote:
            replacement = _plan(current, order, cash, held, basis)
            if replacement.exec_price != order.expected_exec_price:
                raise PriceChanged(
                    _preview(current, replacement, portfolio), order.expected_exec_price
                )
            # Already inserted immutable Trade metadata must not be rewritten.
            raise _ExecutionRefreshed
        authority = json.loads(json.dumps(asdict(current.evidence), default=_encoded))
        authority["portfolio_id"] = portfolio.portfolio_id
        e, q = current.evidence, current.evidence.quote
        facts = StockFillFacts(
            trade_id=trade.id,
            coin_id=cid,
            user_id=portfolio.user_id,
            portfolio_id=portfolio.portfolio_id,
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
        await db.flush()
        # Build BOTH new and replay receipts from the exact persisted NUMERIC
        # scales. These refresh waits precede constraints and final authority.
        await db.refresh(trade)
        await db.refresh(facts)
        fill = _receipt(trade, facts, movement.economic_at)
        await db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        if e.status.source == REPORTED_HALT_SOURCE:
            await db.execute(text(f"SELECT pg_advisory_xact_lock_shared({REPORT_LOCK_KEYS})"))
        # LAST business SQL: no refresh, read, helper or provider await follows.
        await db.execute(
            text(
                "SELECT public.assert_stock_execution_current(:trade,:user,:authority)"
            ).bindparams(bindparam("authority", type_=JSONB)),
            {"trade": trade.id, "user": portfolio.user_id, "authority": authority},
        )
        await db.commit()
        return fill, True
    except IntegrityError as exc:
        await db.rollback()
        if "uq_trades_user_idempotency_key" in str(exc.orig):
            try:
                await _account(db, portfolio, lock=True)
                prior = await _replay(db, portfolio, order)
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
            message = str(exc.orig)
            if "stock quote unavailable" in message or "stock status unavailable" in message:
                raise _ExecutionRefreshed from None
            if "stock market closed" in message:
                raise _refuse("market_closed") from None
            raise _refuse("quote_unavailable") from None
        raise
    except BaseException:
        await db.rollback()
        raise


async def context(
    db: AsyncSession, *, portfolio: OwnedActivePortfolio, symbol: str, settings: Settings
) -> ContextOut:
    await _account(db, portfolio)
    cid = await _instrument(db, symbol)
    cash, held, basis = await _financial(db, portfolio, cid)
    loaded = await load_execution_evidence(db, cid, settings)
    if not loaded.symbol or loaded.decision.reason == "permission_unavailable":
        raise _refuse("permission_unavailable")
    e, d, q = loaded.evidence, loaded.decision, loaded.evidence.quote
    mark = evaluate_valuation(
        ValuationEvidence(
            e,
            loaded.quote_retained_until,
            next((a.valid_until for a in e.admissions if a.product == "quotes"), None),
        ),
        d.evaluated_at,
    )
    safe_quote = mark.mode != "unavailable"
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
        portfolio_id=str(portfolio.portfolio_id),
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
        valid_until=mark.valid_until if quote_facts is not None else d.valid_until,
    )
