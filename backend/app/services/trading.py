"""Trade execution (Phase 4): a read-only quote and a locked, idempotent execute.

Both go through ``plan_trade`` so the preview and the fill can never disagree. ``execute`` runs
in one transaction with a fixed lock order (account row, then holding row) and this check order:

1. lock the account row FOR UPDATE (serialises every trade of one user),
2. idempotency replay lookup, before any price check (a replay must not depend on today's price),
3. Live price only (D-03: the single ``freshness`` definition from Phase 3),
4. lock the holding row FOR UPDATE, plan the trade,
5. refuse with a fresh quote when the mid differs from the one the user previewed,
6. write cash, holding, cost basis and the trade row, then commit.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.price import Coin, Price
from app.models.trade import Holding, Trade
from app.models.user import Account
from app.services.prices import age_seconds, freshness
from app.services.trade_math import (
    InputKind,
    Plan,
    Side,
    TradeCosts,
    TradeRefused,
    cost_basis_after,
    plan_trade,
)

logger = logging.getLogger(__name__)

_ZERO = Decimal("0")


@dataclass(frozen=True)
class Order:
    symbol: str
    side: Side
    kind: InputKind
    value: Decimal


@dataclass(frozen=True)
class Quote:
    symbol: str
    as_of: datetime
    age_seconds: int
    plan: Plan


@dataclass(frozen=True)
class Fill:
    trade_id: int
    created_at: datetime
    symbol: str
    side: Side
    input_kind: InputKind
    input_value: Decimal
    mid: Decimal
    as_of: datetime
    exec_price: Decimal
    quantity: Decimal
    notional: Decimal
    fee: Decimal
    cash_delta: Decimal
    cash_after: Decimal


class PriceChanged(TradeRefused):
    """The mid moved since the preview; nothing was written. Carries the fresh quote."""

    def __init__(self, quote: Quote) -> None:
        super().__init__(
            "price_changed", "The price moved. Review the new total and confirm again."
        )
        self.quote = quote


def _costs(settings: Settings) -> TradeCosts:
    return TradeCosts(
        spread=settings.trade_spread,
        fee_rate=settings.trade_fee_rate,
        min_fee=settings.trade_min_fee_usd,
        min_order=settings.trade_min_order_usd,
    )


async def _load_coin(db: AsyncSession, symbol: str) -> Coin:
    coin = (
        await db.execute(select(Coin).where(Coin.symbol == symbol.upper(), Coin.is_active))
    ).scalar_one_or_none()
    if coin is None:
        raise TradeRefused("unknown_coin", "Unknown coin.")
    return coin


async def _load_coin_price(db: AsyncSession, symbol: str) -> tuple[Coin, Price]:
    row = (
        await db.execute(
            select(Coin, Price)
            .outerjoin(Price, Price.coin_id == Coin.id)
            .where(Coin.symbol == symbol.upper(), Coin.is_active)
            .execution_options(populate_existing=True)
        )
    ).one_or_none()
    if row is None:
        raise TradeRefused("unknown_coin", "Unknown coin.")
    coin, price = row
    if price is None:
        raise TradeRefused(
            "stale_price",
            f"There is no price for {coin.symbol} yet. Trading is paused until it arrives.",
        )
    return coin, price


def _require_fresh(symbol: str, as_of: datetime, now: datetime, settings: Settings) -> int:
    age = age_seconds(as_of, now)
    if freshness(age, settings.price_fresh_seconds, settings.price_stale_seconds) != "fresh":
        raise TradeRefused(
            "stale_price",
            f"The price for {symbol} is {age}s old. Trading is paused until it refreshes.",
        )
    return age


async def _find_trade(db: AsyncSession, user_id: int, key: uuid.UUID) -> tuple[Trade, str] | None:
    row = (
        await db.execute(
            select(Trade, Coin.symbol)
            .join(Coin, Coin.id == Trade.coin_id)
            .where(Trade.user_id == user_id, Trade.idempotency_key == key)
            .execution_options(populate_existing=True)
        )
    ).one_or_none()
    return None if row is None else (row[0], row[1])


def _fill(trade: Trade, symbol: str) -> Fill:
    if trade.side == "buy":
        notional = -trade.cash_delta - trade.fee
    else:
        notional = trade.cash_delta + trade.fee
    return Fill(
        trade_id=trade.id,
        created_at=trade.created_at,
        symbol=symbol,
        side=trade.side,  # type: ignore[arg-type]
        input_kind=trade.input_kind,  # type: ignore[arg-type]
        input_value=trade.input_value,
        mid=trade.mid_price,
        as_of=trade.price_as_of,
        exec_price=trade.exec_price,
        quantity=trade.quantity,
        notional=notional,
        fee=trade.fee,
        cash_delta=trade.cash_delta,
        cash_after=trade.cash_after,
    )


def _replay(found: tuple[Trade, str], order: Order) -> tuple[Fill, bool]:
    trade, symbol = found
    same = (
        symbol == order.symbol.upper()
        and trade.side == order.side
        and trade.input_kind == order.kind
        and trade.input_value == order.value
    )
    if not same:
        raise TradeRefused(
            "idempotency_conflict",
            "This order key was already used for a different order. Start a new order.",
        )
    return _fill(trade, symbol), False


async def _held(db: AsyncSession, user_id: int, coin_id: int) -> Decimal:
    qty = (
        await db.execute(
            select(Holding.quantity).where(Holding.user_id == user_id, Holding.coin_id == coin_id)
        )
    ).scalar_one_or_none()
    return _ZERO if qty is None else qty


async def quote(
    db: AsyncSession,
    *,
    user_id: int,
    order: Order,
    settings: Settings,
    now: datetime | None = None,
) -> Quote:
    """Price an order without locking or writing anything."""
    coin, price = await _load_coin_price(db, order.symbol)
    age = _require_fresh(coin.symbol, price.as_of, now or datetime.now(UTC), settings)
    cash = (await db.execute(select(Account.cash).where(Account.user_id == user_id))).scalar_one()
    plan = plan_trade(
        symbol=coin.symbol,
        side=order.side,
        kind=order.kind,
        value=order.value,
        mid=price.mid,
        cash=cash,
        held=await _held(db, user_id, coin.id),
        costs=_costs(settings),
    )
    return Quote(symbol=coin.symbol, as_of=price.as_of, age_seconds=age, plan=plan)


async def holding_quantity(db: AsyncSession, *, user_id: int, symbol: str) -> tuple[str, Decimal]:
    coin = await _load_coin(db, symbol)
    return coin.symbol, await _held(db, user_id, coin.id)


async def execute(
    db: AsyncSession,
    *,
    user_id: int,
    order: Order,
    expected_mid: Decimal,
    idempotency_key: uuid.UUID,
    settings: Settings,
    now: datetime | None = None,
) -> tuple[Fill, bool]:
    """Execute one market order. Returns (fill, True) when new, (original fill, False) on replay."""
    try:
        # (1) account lock first, always; holding lock second.
        account = (
            await db.execute(
                select(Account)
                .where(Account.user_id == user_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalar_one()

        # (2) replay precedes every price check.
        existing = await _find_trade(db, user_id, idempotency_key)
        if existing is not None:
            replayed = _replay(existing, order)  # build before the rollback expires the row
            await db.rollback()
            return replayed

        # (3) Live prices only.
        coin, price = await _load_coin_price(db, order.symbol)
        age = _require_fresh(coin.symbol, price.as_of, now or datetime.now(UTC), settings)

        # (4) holding lock, then plan.
        holding = (
            await db.execute(
                select(Holding)
                .where(Holding.user_id == user_id, Holding.coin_id == coin.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalar_one_or_none()
        plan = plan_trade(
            symbol=coin.symbol,
            side=order.side,
            kind=order.kind,
            value=order.value,
            mid=price.mid,
            cash=account.cash,
            held=_ZERO if holding is None else holding.quantity,
            costs=_costs(settings),
        )

        # (5) the user confirmed a different mid: show the new total instead of filling.
        if price.mid != expected_mid:
            raise PriceChanged(Quote(coin.symbol, price.as_of, age, plan))

        # (6) apply.
        basis = cost_basis_after(
            side=plan.side,
            cost_basis=_ZERO if holding is None else holding.cost_basis,
            held_before=plan.held_before,
            quantity=plan.quantity,
            cash_delta=plan.cash_delta,
        )
        account.cash = plan.cash_after
        if holding is None:  # only buys get here; plan_trade refuses a sell with nothing held
            db.add(
                Holding(
                    user_id=user_id, coin_id=coin.id, quantity=plan.held_after, cost_basis=basis
                )
            )
        else:
            holding.quantity = plan.held_after
            holding.cost_basis = basis
        trade = Trade(
            user_id=user_id,
            coin_id=coin.id,
            side=plan.side,
            input_kind=plan.kind,
            input_value=plan.input_value,
            quantity=plan.quantity,
            mid_price=price.mid,
            price_as_of=price.as_of,
            exec_price=plan.exec_price,
            fee=plan.fee,
            cash_delta=plan.cash_delta,
            cash_after=plan.cash_after,
            idempotency_key=idempotency_key,
        )
        db.add(trade)
        await db.flush()
        await db.refresh(trade)  # server-side created_at; the fill is built from stored values
        fill = _fill(trade, coin.symbol)
        side = plan.side
        await db.commit()
    except TradeRefused:
        await db.rollback()  # release the row locks now
        raise
    except IntegrityError as exc:
        await db.rollback()
        if "uq_trades_user_idempotency_key" in str(exc.orig):
            raced = await _find_trade(db, user_id, idempotency_key)
            if raced is not None:
                replayed = _replay(raced, order)
                await db.rollback()
                return replayed
        raise

    logger.info("trade executed trade_id=%s user_id=%s side=%s", fill.trade_id, user_id, side)
    return fill, True
