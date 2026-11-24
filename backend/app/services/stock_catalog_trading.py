"""Stable catalog orders using the shared stock ledger and exact SQL authority."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Any, cast

from sqlalchemy import bindparam, func, select, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.corporate_action import StockActionState, StockOwnershipMovement
from app.models.stock_catalog import StockCatalogListing
from app.models.stock_catalog_finance import (
    StockCatalogActionCoverage,
    StockCatalogFillEvidence,
    StockCatalogFinancialQuote,
    StockCatalogInstrument,
    StockCatalogStatus,
)
from app.models.stock_execution import StockFillFacts
from app.models.trade import Trade
from app.schemas.stock_catalog_quotes import (
    CatalogConfirmIn,
    CatalogExecutionReason,
    CatalogFillOut,
    CatalogOrderIn,
    CatalogPreviewOut,
    CatalogPriceChangedOut,
)
from app.services.corporate_actions import persistent_action_holds
from app.services.portfolios import OwnedActivePortfolio, fence_owned_active_portfolios
from app.services.stock_catalog_actions import (
    CatalogActionAuthority,
    load_catalog_action_authority,
    lock_catalog_action_scope,
)
from app.services.stock_catalog_financial_quotes import (
    CatalogFinancialQuoteContext,
    _sessions,
    load_catalog_financial_quote_context,
)
from app.services.stock_catalog_promotion import load_catalog_financial_binding
from app.services.stock_catalog_search import get_catalog_listing
from app.services.stock_eligibility import has_unprocessed_catalog_action, load_catalog_status
from app.services.stock_halts import REPORT_LOCK_KEYS
from app.services.stock_ownership import OwnershipHeld, acquire_stock_gate
from app.services.stock_trade_math import StockTradePlan, buy_max_quantity, plan_stock_trade
from app.services.stock_trading import _account, _book_stock_trade, _financial, _refuse
from app.services.trade_idempotency import find_user_trade, require_same_order
from app.services.trade_math import Q2, TradeRefused

ZERO = Decimal(0)
FRESH = timedelta(seconds=120)


@dataclass(frozen=True)
class CatalogExecution:
    """Private scoped evidence and public eligibility reason for one issue."""

    reason: CatalogExecutionReason
    coin_id: int | None = None
    listing: StockCatalogListing | None = None
    financial: CatalogFinancialQuoteContext | None = None
    quote: StockCatalogFinancialQuote | None = None
    status: StockCatalogStatus | None = None
    action_epoch: int | None = None
    action_admission_id: int | None = None
    evaluated_at: datetime | None = None
    valid_until: datetime | None = None
    version_changed: bool = False

    @property
    def available(self) -> bool:
        return self.reason == "available"


@dataclass(frozen=True)
class CatalogDraft:
    cash: Decimal
    held_quantity: Decimal
    buy_max_quantity: Decimal


class CatalogPriceChanged(TradeRefused):
    def __init__(self, quote: CatalogPreviewOut, previous: Decimal) -> None:
        super().__init__("price_changed", "The price moved. Review and confirm again.")
        with localcontext() as ctx:
            ctx.prec = 64
            before = (previous * quote.quantity).quantize(Q2, rounding=ROUND_HALF_EVEN)
        if quote.side == "buy":
            before = -before
        self.detail = CatalogPriceChangedOut(
            previous_exec_price=previous,
            previous_cash_delta=before,
            exec_price_change=quote.exec_price - previous,
            cash_delta_change=quote.cash_delta - before,
            quote=quote,
        )


async def _clock(db: AsyncSession) -> datetime:
    return cast(datetime, await db.scalar(select(func.clock_timestamp())))


def _has_action_lease(
    state: StockActionState | None,
    coverage: StockCatalogActionCoverage | None,
    authority: CatalogActionAuthority | None,
    now: datetime,
) -> bool:
    return (
        state is not None
        and coverage is not None
        and authority is not None
        and state.health == "current"
        and state.checked_at is not None
        and state.checked_at <= now
        and state.valid_until is not None
        and now < state.valid_until
        and state.epoch > 0
        and (state.next_blocking_at is None or now < state.next_blocking_at)
        and (coverage.catalog_id, coverage.listing_id, coverage.admission_id)
        == (authority.binding.catalog_id, authority.binding.listing_id, authority.admission_id)
        and state.admission_generation == authority.admission_id
        and coverage.coverage_start is not None
        and coverage.covered_until is not None
        and coverage.coverage_start <= coverage.journal_origin <= coverage.covered_until <= now
        and state.complete_from is not None
        and state.complete_from <= coverage.covered_until
        and coverage.journal_origin == state.journal_start_at == authority.journal_origin
        and (
            coverage.coverage_start,
            coverage.covered_until,
            coverage.cursor,
            coverage.observed_at,
            coverage.valid_until,
        )
        == (
            state.coverage_start,
            state.covered_until,
            state.cursor,
            state.checked_at,
            state.valid_until,
        )
    )


async def _coin_id(db: AsyncSession, catalog_id: int) -> int | None:
    column = StockCatalogInstrument.coin_id
    return cast(
        int | None,
        await db.scalar(select(column).where(StockCatalogInstrument.catalog_id == catalog_id)),
    )


async def load_catalog_execution(
    db: AsyncSession,
    settings: Settings,
    catalog_id: int,
    listing_version: int,
    now: datetime,
    *,
    portfolio: OwnedActivePortfolio | None = None,
) -> CatalogExecution:
    """Read the targeted listing only. Execution repeats these checks under lock."""
    listing = await get_catalog_listing(db, settings, catalog_id, now=now)
    coin_id = await _coin_id(db, catalog_id)
    result = CatalogExecution("read_only", coin_id=coin_id, listing=listing, evaluated_at=now)
    if listing is None or listing.id != listing_version:
        return replace(result, version_changed=listing is not None)
    if coin_id is None or listing.state != "active" or not settings.stock_data_enabled:
        return result
    financial = await load_catalog_financial_quote_context(
        db, settings, catalog_id, listing_version, now
    )
    if financial is None:
        binding = await load_catalog_financial_binding(
            db, catalog_id, listing_version, now, allow_fixture=settings.env == "test"
        )
        if binding is None or (binding.account, binding.server) != (
            settings.stock_data_account,
            settings.stock_data_server,
        ):
            return replace(result, reason="permission_unavailable")
        session, _ = await _sessions(db, binding, now)
        if session.state == "closed":
            return replace(result, reason="market_closed")
        reason: CatalogExecutionReason = (
            "session_unavailable" if session.state == "unknown" else "permission_unavailable"
        )
        return replace(result, reason=reason)
    result = replace(result, financial=financial)
    binding, current_session = financial.binding, financial.session
    report = await load_catalog_status(db, binding, now)
    if report is None or report[0].session_date != current_session.session_date:
        return replace(result, reason="status_unavailable")
    status, halt_grant_until = report
    if status.state == "halted":
        return replace(result, reason="halted")
    if status.state != "normal":
        return replace(result, reason="status_unavailable")
    scope = await load_catalog_action_authority(
        db,
        coin_id,
        now,
        account=binding.account,
        server=binding.server,
        allow_fixture=settings.env == "test",
    )
    state = await db.get(StockActionState, coin_id, populate_existing=True)
    coverage = await db.get(StockCatalogActionCoverage, coin_id, populate_existing=True)
    if (
        state is None
        or coverage is None
        or scope is None
        or state.complete_from is None
        or coverage.covered_until is None
        or state.valid_until is None
        or not _has_action_lease(state, coverage, scope, now)
    ):
        return replace(result, reason="action_unavailable")
    if await persistent_action_holds(db, coin_id) or await has_unprocessed_catalog_action(
        db,
        coin_id=coin_id,
        at=now,
        portfolio_id=portfolio.portfolio_id if portfolio else None,
        complete_from=max(state.complete_from, coverage.journal_origin),
        covered_until=coverage.covered_until,
    ):
        return replace(result, reason="action_unavailable")
    price = await db.get(StockCatalogFinancialQuote, coin_id, populate_existing=True)
    if price is None or (
        price.catalog_id,
        price.listing_id,
        price.provider_asset_id,
        price.provider_admission_id,
        price.execution_admission_id,
        price.session_date,
        price.opens_at,
        price.closes_at,
        price.calendar_generation,
    ) != (
        catalog_id,
        listing_version,
        binding.provider_asset_id,
        binding.provider_admission_id,
        financial.execution.id,
        current_session.session_date,
        current_session.opens_at,
        current_session.closes_at,
        current_session.calendar_admission_generation,
    ):
        return replace(result, reason="quote_unavailable")
    if price.unit_epoch != state.unit_epoch or (
        state.quote_not_before is not None and price.event_at <= state.quote_not_before
    ):
        return replace(result, reason="units_changed")
    if not financial.execution.reviewed_at <= price.collected_at <= price.observed_at <= now:
        return replace(result, reason="quote_unavailable")
    if current_session.closes_at is None:
        return replace(result, reason="session_unavailable")
    deadline = min(
        financial.valid_until,
        price.valid_until,
        price.event_at + FRESH,
        status.valid_until,
        halt_grant_until,
        scope.valid_until,
        state.valid_until,
        current_session.closes_at,
        state.next_blocking_at or state.valid_until,
    )
    if now >= deadline:
        return replace(result, reason="quote_stale")
    return replace(
        result,
        reason="available",
        quote=price,
        status=status,
        action_epoch=state.epoch,
        action_admission_id=coverage.admission_id,
        valid_until=deadline,
    )


async def draft(
    db: AsyncSession, *, portfolio: OwnedActivePortfolio, loaded: CatalogExecution
) -> CatalogDraft:
    if loaded.coin_id is None:
        return CatalogDraft((await _account(db, portfolio)).cash, ZERO, ZERO)
    cash, held, basis = await _financial(db, portfolio, loaded.coin_id)
    price = loaded.quote
    maximum = (
        buy_max_quantity(bid=price.bid, ask=price.ask, cash=cash, held=held, cost_basis=basis)
        if price is not None
        else ZERO
    )
    return CatalogDraft(cash, held, maximum)


def _require(loaded: CatalogExecution) -> StockCatalogFinancialQuote:
    if loaded.version_changed:
        raise _refuse("listing_changed")
    if not loaded.available or loaded.quote is None:
        raise _refuse(loaded.reason)
    return loaded.quote


def _plan(
    loaded: CatalogExecution, order: CatalogOrderIn, financial: tuple[Decimal, Decimal, Decimal]
) -> StockTradePlan:
    price = _require(loaded)
    cash, held, basis = financial
    return plan_stock_trade(
        side=order.side,
        quantity=order.quantity,
        bid=price.bid,
        ask=price.ask,
        cash=cash,
        held=held,
        cost_basis=basis,
    )


def _preview(
    loaded: CatalogExecution, plan: StockTradePlan, portfolio: OwnedActivePortfolio
) -> CatalogPreviewOut:
    price = _require(loaded)
    listing = loaded.listing
    if listing is None or loaded.valid_until is None or loaded.evaluated_at is None:
        raise _refuse("quote_unavailable")
    return CatalogPreviewOut(
        portfolio_id=portfolio.portfolio_id,
        catalog_id=listing.security_id,
        listing_version=listing.id,
        symbol=listing.ticker,
        company_name=listing.company_name,
        listing_exchange=cast(Any, listing.listing_exchange),
        side=plan.side,
        quantity=plan.quantity,
        bid=plan.bid,
        ask=plan.ask,
        exact_mid=plan.exact_mid,
        exec_price=plan.exec_price,
        event_at=price.event_at,
        collected_at=price.collected_at,
        observed_at=loaded.evaluated_at,
        age_seconds=int((loaded.evaluated_at - price.event_at).total_seconds()),
        notional=plan.notional,
        fee=plan.fee,
        cash_delta=plan.cash_delta,
        cash_before=plan.cash_before,
        cash_after=plan.cash_after,
        held_before=plan.held_before,
        held_after=plan.held_after,
        session_date=price.session_date,
        session_opens_at=price.opens_at,
        session_closes_at=price.closes_at,
        valid_until=loaded.valid_until,
    )


async def quote(
    db: AsyncSession,
    *,
    portfolio: OwnedActivePortfolio,
    catalog_id: int,
    order: CatalogOrderIn,
    settings: Settings,
) -> CatalogPreviewOut:
    # Read the clock and money after any wait for a competing root update.
    # Preview takes no instrument lock and has no provider or Redis wait.
    await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
    loaded = await load_catalog_execution(
        db, settings, catalog_id, order.listing_version, await _clock(db), portfolio=portfolio
    )
    price = _require(loaded)
    financial = await _financial(db, portfolio, price.coin_id)
    return _preview(loaded, _plan(loaded, order, financial), portfolio)


def _receipt(
    trade: Trade,
    facts: StockFillFacts,
    adjunct: StockCatalogFillEvidence,
    executed: datetime,
) -> CatalogFillOut:
    held_before = (
        facts.held_after - trade.quantity
        if trade.side == "buy"
        else facts.held_after + trade.quantity
    )
    return CatalogFillOut(
        portfolio_id=trade.portfolio_id,
        catalog_id=adjunct.catalog_id,
        listing_version=adjunct.listing_id,
        trade_id=trade.id,
        executed_at=executed,
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
        held_before=held_before,
        held_after=facts.held_after,
        session_date=facts.session_date,
        session_opens_at=facts.opens_at,
        session_closes_at=facts.closes_at,
    )


async def _replay(
    db: AsyncSession,
    portfolio: OwnedActivePortfolio,
    catalog_id: int,
    order: CatalogConfirmIn,
) -> CatalogFillOut | None:
    trade = await find_user_trade(db, portfolio.user_id, order.idempotency_key)
    if trade is None:
        return None
    row = (
        await db.execute(
            select(StockFillFacts, StockCatalogFillEvidence, StockOwnershipMovement.economic_at)
            .join(
                StockCatalogFillEvidence,
                StockCatalogFillEvidence.trade_id == StockFillFacts.trade_id,
            )
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
    require_same_order(
        trade,
        same_instrument=row is not None
        and (row[1].catalog_id, row[1].listing_id) == (catalog_id, order.listing_version),
        portfolio_id=portfolio.portfolio_id,
        side=order.side,
        kind="quantity",
        value=order.quantity,
        expected_exec_price=order.expected_exec_price,
    )
    if row is None:
        raise _refuse("receipt_unavailable")
    # A concurrent close is the only mutable fact needed for historical replay.
    await _account(db, portfolio, lock=True)
    try:
        return _receipt(trade, row[0], row[1], row[2])
    except TypeError, ValueError:
        raise _refuse("receipt_unavailable") from None


class _QuoteRolled(Exception):
    """Rebuild uncommitted trade metadata after the selected quote changes."""


def _quote_identity(price: StockCatalogFinancialQuote) -> tuple[Any, ...]:
    return (
        price.bid,
        price.ask,
        price.event_at,
        price.collected_at,
        price.observed_at,
        price.unit_epoch,
        price.calendar_generation,
        price.valid_until,
    )


async def execute(
    db: AsyncSession,
    *,
    portfolio: OwnedActivePortfolio,
    catalog_id: int,
    order: CatalogConfirmIn,
    settings: Settings,
) -> tuple[CatalogFillOut, bool]:
    # One clean retry for changed immutable quote metadata, as on the curated path.
    for _ in range(2):
        try:
            return await _execute_once(db, portfolio, catalog_id, order, settings)
        except _QuoteRolled:
            continue
    raise _refuse("quote_unavailable")


async def _execute_once(
    db: AsyncSession,
    portfolio: OwnedActivePortfolio,
    catalog_id: int,
    order: CatalogConfirmIn,
    settings: Settings,
) -> tuple[CatalogFillOut, bool]:
    try:
        await _account(db, portfolio)
        prior = await _replay(db, portfolio, catalog_id, order)
        if prior is not None:
            await db.rollback()
            return prior, False
        await lock_catalog_action_scope(db)
        prior = await _replay(db, portfolio, catalog_id, order)
        if prior is not None:
            await db.rollback()
            return prior, False
        coin_id = await _coin_id(db, catalog_id)
        if coin_id is None:
            raise _refuse("read_only")
        await acquire_stock_gate(db, coin_id)
        account = await _account(db, portfolio, lock=True)
        prior = await _replay(db, portfolio, catalog_id, order)
        if prior is not None:
            await db.rollback()
            return prior, False
        financial = await _financial(db, portfolio, coin_id)
        loaded = await load_catalog_execution(
            db, settings, catalog_id, order.listing_version, await _clock(db), portfolio=portfolio
        )
        plan = _plan(loaded, order, financial)
        if plan.exec_price != order.expected_exec_price:
            raise CatalogPriceChanged(_preview(loaded, plan, portfolio), order.expected_exec_price)
        price = _require(loaded)
        identity = _quote_identity(price)
        trade, movement = await _book_stock_trade(
            db, portfolio, coin_id, plan, price.event_at, order.idempotency_key
        )
        current = await load_catalog_execution(
            db, settings, catalog_id, order.listing_version, await _clock(db), portfolio=portfolio
        )
        price = _require(current)
        if _quote_identity(price) != identity:
            changed = _plan(current, order, financial)
            if changed.exec_price != order.expected_exec_price:
                raise CatalogPriceChanged(
                    _preview(current, changed, portfolio), order.expected_exec_price
                )
            raise _QuoteRolled
        listing, status = current.listing, current.status
        if (
            listing is None
            or status is None
            or current.action_epoch is None
            or current.action_admission_id is None
            or price.execution_admission_id is None
        ):
            raise _refuse("quote_unavailable")
        adjunct = StockCatalogFillEvidence(
            trade_id=trade.id,
            coin_id=coin_id,
            catalog_id=catalog_id,
            listing_id=listing.id,
            provider_admission_id=price.provider_admission_id,
            execution_admission_id=price.execution_admission_id,
            halt_admission_id=status.admission_id,
            action_admission_id=current.action_admission_id,
            unit_epoch=price.unit_epoch,
            action_epoch=current.action_epoch,
            report_digest=status.report_digest,
            report_event_at=status.event_at,
            report_valid_until=status.valid_until,
            quote_valid_until=price.valid_until,
        )
        authority = {
            "portfolio_id": str(portfolio.portfolio_id),
            "coin_id": str(coin_id),
            "catalog_id": str(catalog_id),
            "listing_id": str(listing.id),
            "provider_asset_id": price.provider_asset_id,
        }
        facts = StockFillFacts(
            trade_id=trade.id,
            coin_id=coin_id,
            user_id=portfolio.user_id,
            portfolio_id=portfolio.portfolio_id,
            provider_asset_id=price.provider_asset_id,
            symbol=listing.ticker,
            company_name=listing.company_name,
            listing_exchange=listing.listing_exchange,
            source=price.source,
            feed=price.feed,
            bid=price.bid,
            ask=price.ask,
            exact_mid=plan.exact_mid,
            held_after=movement.after_quantity,
            event_at=price.event_at,
            collected_at=price.collected_at,
            observed_at=price.observed_at,
            session_date=price.session_date,
            opens_at=price.opens_at,
            closes_at=price.closes_at,
            authority=authority,
        )
        db.add(facts)
        account.cash = plan.cash_after
        await db.flush()
        db.add(adjunct)
        await db.flush()
        await db.refresh(trade)
        await db.refresh(facts)
        fill = _receipt(trade, facts, adjunct, movement.economic_at)
        await db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        await db.execute(text(f"SELECT pg_advisory_xact_lock_shared({REPORT_LOCK_KEYS})"))
        # The final guard and transaction commit follow the last lock wait.
        await db.execute(
            text(
                "SELECT public.assert_catalog_stock_execution_current(:trade,:user,:authority)"
            ).bindparams(bindparam("authority", type_=JSONB)),
            {"trade": trade.id, "user": portfolio.user_id, "authority": authority},
        )
        await db.commit()
        return fill, True
    except IntegrityError as exc:
        await db.rollback()
        if "uq_trades_user_idempotency_key" in str(exc.orig):
            try:
                prior = await _replay(db, portfolio, catalog_id, order)
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
                raise _QuoteRolled from None
            if "stock market closed" in message:
                raise _refuse("market_closed") from None
            if "stock action" in message:
                raise _refuse("action_unavailable") from None
            if "stock execution permission" in message:
                raise _refuse("permission_unavailable") from None
            raise _refuse("quote_unavailable") from None
        raise
    except BaseException:
        await db.rollback()
        raise
