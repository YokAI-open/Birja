"""A read-only, user-scoped financial statement snapshot."""

from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import and_, func, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.price import Coin, Price
from app.models.stock import StockInstrument, StockQuote
from app.models.stock_execution import StockFillFacts
from app.models.trade import Holding
from app.models.user import Account
from app.services.portfolio_math import (
    PortfolioValue,
    PositionInput,
    PositionValue,
    calculate_portfolio,
)
from app.services.prices import age_seconds, freshness
from app.services.stock_eligibility import execution_snapshot_query, executions_from_snapshot
from app.services.stock_valuation import StockMark, value_stock

PortfolioPriceStatus = Literal["fresh", "aging", "stale", "unpriced"]


@dataclass(frozen=True)
class HoldingValue(PositionValue):
    age_seconds: int | None
    status: PortfolioPriceStatus
    stock_mark: StockMark | None


@dataclass(frozen=True)
class PortfolioSnapshot(PortfolioValue):
    holdings: tuple[HoldingValue, ...]
    valued_at: datetime
    prices_as_of: datetime | None
    fresh_seconds: int
    stale_seconds: int


async def get_portfolio(
    db: AsyncSession, *, user_id: int, settings: Settings, now: datetime | None = None
) -> PortfolioSnapshot:
    # Scalar columns prevent identity-map reuse or lazy reads. The positive-quantity
    # predicate stays in ON so a cash-only account still produces one row.
    authority = execution_snapshot_query(datetime.now(UTC)).cte("portfolio_market")
    # Original quote-generation rights are authenticated by immutable accounting
    # evidence. They never supply a new cash/quantity/price financial snapshot.
    proof = (
        select(StockFillFacts.authority)
        .where(
            StockFillFacts.coin_id == Coin.id,
            StockFillFacts.authority["quote"]["admission_generation"]
            == func.to_jsonb(StockQuote.admission_generation),
        )
        .order_by(StockFillFacts.trade_id)
        .limit(1)
        .correlate(Coin, StockQuote)
        .scalar_subquery()
    )
    result = await db.execute(
        select(
            Account.cash,
            Account.starting_cash,
            Coin.symbol,
            Coin.name,
            Coin.is_active,
            Holding.quantity,
            Holding.cost_basis,
            Price.mid,
            Price.as_of,
            Coin.id.label("coin_id"),
            Coin.asset_class,
            StockInstrument.provider_asset_id,
            proof.label("original_authority"),
            *authority.c,
        )
        .select_from(Account)
        .outerjoin(Holding, and_(Holding.user_id == Account.user_id, Holding.quantity > 0))
        .outerjoin(Coin, Coin.id == Holding.coin_id)
        .outerjoin(Price, and_(Price.coin_id == Coin.id, Coin.asset_class == "crypto"))
        .outerjoin(StockInstrument, StockInstrument.coin_id == Coin.id)
        .outerjoin(StockQuote, StockQuote.coin_id == Coin.id)
        .join(authority, true())
        .where(Account.user_id == user_id)
        .order_by(Coin.symbol, Coin.id)
    )
    valued_at = now or datetime.now(UTC)  # Sample after the awaited statement.
    rows = result.all()
    if not rows:
        raise RuntimeError("Authenticated user has no account")
    positions = []
    marks = {}
    stock_rows = [r for r in rows if r.asset_class == "stock"]
    if stock_rows:
        current_raw = (await db.execute(execution_snapshot_query(valued_at))).one()
        valued_at = now or datetime.now(UTC)
        original = executions_from_snapshot(rows[0], settings, now=valued_at)
        current = executions_from_snapshot(current_raw, settings, now=valued_at)
        for row in stock_rows:
            result_mark = value_stock(
                original.get(row.coin_id),
                current.get(row.coin_id),
                raw=rows[0],
                current_raw=current_raw,
                proof=row.original_authority,
                now=valued_at,
            )
            marks[row.coin_id] = result_mark
    for row in rows:
        if row.symbol is None:
            continue
        stock = marks.get(row.coin_id)
        positions.append(
            PositionInput(
                row.symbol,
                row.name,
                row.is_active,
                row.quantity,
                row.cost_basis,
                stock.mid if stock is not None else row.mid,
                stock.mark.event_at if stock is not None else row.as_of,
                asset_class=row.asset_class,
                coin_id=str(row.coin_id),
                provider_asset_id=row.provider_asset_id,
                units_safe=stock.mark.units_safe if stock is not None else True,
            )
        )
    value = calculate_portfolio(rows[0].cash, rows[0].starting_cash, positions)
    holdings = []
    for p in value.holdings:
        age = age_seconds(p.as_of, valued_at) if p.as_of is not None else None
        status: PortfolioPriceStatus = (
            freshness(age, settings.price_fresh_seconds, settings.price_stale_seconds)
            if age is not None
            else "unpriced"
        )
        mark = marks.get(int(p.coin_id))
        holdings.append(
            HoldingValue(
                **asdict(p),
                age_seconds=age,
                status=status,
                stock_mark=mark.mark if mark is not None else None,
            )
        )
    return PortfolioSnapshot(
        **{f.name: getattr(value, f.name) for f in fields(value) if f.name != "holdings"},
        holdings=tuple(holdings),
        valued_at=valued_at,
        prices_as_of=min((p.as_of for p in positions if p.as_of is not None), default=None),
        fresh_seconds=settings.price_fresh_seconds,
        stale_seconds=settings.price_stale_seconds,
    )
