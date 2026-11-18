"""A read-only statement for one explicitly owned active portfolio."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal

from fastapi import HTTPException
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

if TYPE_CHECKING:
    from app.services.portfolios import OwnedActivePortfolio

PortfolioPriceStatus = Literal["fresh", "aging", "stale", "unpriced"]


@dataclass(frozen=True)
class HoldingValue(PositionValue):
    age_seconds: int | None
    status: PortfolioPriceStatus
    stock_mark: StockMark | None


@dataclass(frozen=True)
class PortfolioSnapshot(PortfolioValue):
    portfolio_id: str
    name: str
    description: str
    holdings: tuple[HoldingValue, ...]
    valued_at: datetime
    prices_as_of: datetime | None
    fresh_seconds: int
    stale_seconds: int


async def get_portfolio(
    db: AsyncSession,
    *,
    portfolio: OwnedActivePortfolio,
    settings: Settings,
    now: datetime | None = None,
) -> PortfolioSnapshot:
    return (
        await load_portfolio_snapshots(
            db,
            owner_id=portfolio.user_id,
            portfolio_ids=[portfolio.portfolio_id],
            settings=settings,
            now=now,
        )
    )[0]


async def load_portfolio_snapshots(
    db: AsyncSession,
    *,
    owner_id: int,
    portfolio_ids: list[int] | None = None,
    settings: Settings,
    now: datetime | None = None,
) -> tuple[PortfolioSnapshot, ...]:
    """One financial snapshot and one shared final authority/ownership check.

    None selects every active root; explicit IDs must all remain available.
    Bounded root selection precedes the holding joins, including in corrupt
    over-cap states. Never truncate a strategy or poll markets per strategy.
    """
    if (
        type(owner_id) is not int
        or not 0 < owner_id <= 9223372036854775807
        or portfolio_ids is not None
        and (
            not isinstance(portfolio_ids, list)
            or len(portfolio_ids) > 10
            or any(type(p) is not int or not 0 < p <= 9223372036854775807 for p in portfolio_ids)
            or len(set(portfolio_ids)) != len(portfolio_ids)
        )
    ):
        raise HTTPException(422, detail={"code": "invalid_input"})
    if portfolio_ids == []:
        return ()
    root_query = select(Account.id).where(
        Account.user_id == owner_id,
        Account.closed_at.is_(None),
    )
    if portfolio_ids is not None:
        root_query = root_query.where(Account.id.in_(portfolio_ids))
    roots = root_query.order_by(Account.id).limit(11).cte("selected_portfolios")
    # Scalar columns prevent identity-map reuse or lazy reads. The positive-quantity
    # predicate stays in ON so a cash-only account still produces one row.
    authority = execution_snapshot_query(now or datetime.now(UTC)).cte("portfolio_market")
    # Original quote-generation rights are authenticated by immutable accounting
    # evidence. They never supply a new cash/quantity/price financial snapshot.
    proof = (
        select(StockFillFacts.authority)
        .where(
            StockFillFacts.portfolio_id == Account.id,
            StockFillFacts.user_id == Account.user_id,
            StockFillFacts.coin_id == Coin.id,
            StockFillFacts.authority["quote"]["admission_generation"]
            == func.to_jsonb(StockQuote.admission_generation),
        )
        .order_by(StockFillFacts.trade_id)
        .limit(1)
        .correlate(Account, Coin, StockQuote)
        .scalar_subquery()
    )
    result = await db.execute(
        select(
            Account.id.label("portfolio_id"),
            Account.name.label("portfolio_name"),
            Account.description,
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
        .join(roots, roots.c.id == Account.id)
        .outerjoin(
            Holding,
            and_(
                Holding.portfolio_id == Account.id,
                Holding.user_id == Account.user_id,
                Holding.quantity > 0,
            ),
        )
        .outerjoin(Coin, Coin.id == Holding.coin_id)
        .outerjoin(Price, and_(Price.coin_id == Coin.id, Coin.asset_class == "crypto"))
        .outerjoin(StockInstrument, StockInstrument.coin_id == Coin.id)
        .outerjoin(StockQuote, StockQuote.coin_id == Coin.id)
        .join(authority, true())
        .where(
            Account.user_id == owner_id,
            Account.closed_at.is_(None),
        )
        .order_by(Account.id, Coin.symbol, Coin.id)
    )
    rows = result.all()
    grouped: dict[int, list[Any]] = {}
    for row in rows:
        grouped.setdefault(row.portfolio_id, []).append(row)
    if len(grouped) > 10:
        raise HTTPException(409, detail={"code": "portfolio_limit"})
    if portfolio_ids is not None and set(grouped) != set(portfolio_ids):
        raise HTTPException(status_code=404, detail={"code": "portfolio_unavailable"})
    if not rows:
        return ()
    # Check membership again in the same statement as current market authority.
    # READ COMMITTED gives this a fresh view after the financial await. Include
    # every owner root for overview so a newly created/closed root cannot silently
    # disappear from a supposedly complete comparison.
    # Retain shared root locks until the caller's read transaction ends. A
    # closer/owner writer cannot commit between the final await and response
    # serialization. No financial values are reread or changed by this check.
    current_ids = (
        root_query.order_by(Account.id).limit(11).with_for_update(read=True, of=Account).subquery()
    )
    current_raw = (
        await db.execute(
            execution_snapshot_query(now or datetime.now(UTC)).add_columns(
                select(func.array_agg(current_ids.c.id)).scalar_subquery().label("active_ids")
            )
        )
    ).one()
    valued_at = now or datetime.now(UTC)  # One advancing time after BOTH awaits.
    if set(current_raw.active_ids or []) != set(grouped):
        raise HTTPException(404, detail={"code": "portfolio_unavailable"})
    original = executions_from_snapshot(rows[0], settings, now=valued_at)
    current = executions_from_snapshot(current_raw, settings, now=valued_at)
    return tuple(
        _assemble_snapshot(book, original, current, current_raw, settings, valued_at)
        for book in grouped.values()
    )


def _assemble_snapshot(
    rows: list[Any],
    original: dict[int, Any],
    current: dict[int, Any],
    current_raw: Any,
    settings: Settings,
    valued_at: datetime,
) -> PortfolioSnapshot:
    positions = []
    marks = {}
    stock_rows = [r for r in rows if r.asset_class == "stock"]
    if stock_rows:
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
        portfolio_id=str(rows[0].portfolio_id),
        name=rows[0].portfolio_name,
        description=rows[0].description,
        **{f.name: getattr(value, f.name) for f in fields(value) if f.name != "holdings"},
        holdings=tuple(holdings),
        valued_at=valued_at,
        prices_as_of=min((p.as_of for p in positions if p.as_of is not None), default=None),
        fresh_seconds=settings.price_fresh_seconds,
        stale_seconds=settings.price_stale_seconds,
    )
