"""Scheduler-owned finite status persistence; caller owns one short transaction."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Any
from typing import cast as typecast

from sqlalchemy import Table, Text, cast, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price import Coin
from app.models.stock import StockDataAdmission, StockInstrument
from app.models.stock_execution import StockStatusEvidence
from app.services.stock_admission import ProductAdmission, evaluate_admission
from app.services.stock_ownership import acquire_stock_gate
from app.services.stock_quote_rules import CURATED_SYMBOLS, utc
from app.services.stock_status_rules import StatusBatch, StatusEvent, normalize_status_batch
from app.services.stock_trading_rules import (
    MAX_SAFE,
    StatusEvidence,
    lose_status_continuity,
    status_current,
)


class StatusUnavailable(ValueError):
    """No current independently admitted finite status proof can be committed."""


@dataclass(frozen=True)
class _Authority:
    identity: tuple[Any, ...]
    admissions: tuple[ProductAdmission, ...]
    hashes: tuple[str, ...]
    checked_at: datetime

    @property
    def valid_until(self) -> datetime:
        return min(a.valid_until for a in self.admissions if a.valid_until is not None)


async def _authority(db: AsyncSession, coin_id: int, account: str, server: str) -> _Authority:
    table = typecast(Table, StockDataAdmission.__table__)
    columns = [c for c in table.columns if c.name != "id"]
    rows = (
        (
            await db.execute(
                select(
                    *columns,
                    func.encode(
                        func.sha256(
                            func.convert_to(cast(func.to_jsonb(table.table_valued()), Text), "UTF8")
                        ),
                        "hex",
                    ).label("row_hash"),
                    StockInstrument.provider_asset_id,
                    StockInstrument.provider_verified_at,
                    StockInstrument.listing_exchange,
                    Coin.symbol,
                    func.clock_timestamp().label("checked_at"),
                )
                .select_from(table)
                .join(StockInstrument, StockInstrument.coin_id == coin_id)
                .join(Coin, Coin.id == StockInstrument.coin_id)
                .where(
                    StockDataAdmission.product.in_(("reference", "status")),
                    Coin.asset_class == "stock",
                    Coin.is_active,
                    Coin.symbol.in_(CURATED_SYMBOLS),
                )
                .order_by(StockDataAdmission.product)
            )
        )
        .mappings()
        .all()
    )
    if len(rows) != 2 or {r.product for r in rows} != {"reference", "status"}:
        raise StatusUnavailable("status_admission_unavailable")
    checked = rows[-1].checked_at
    identity = tuple(
        rows[-1][key]
        for key in ("provider_asset_id", "provider_verified_at", "listing_exchange", "symbol")
    )
    if not identity[0] or identity[1] is None or identity[1] > checked:
        raise StatusUnavailable("status_mapping_unavailable")
    permissions = tuple(ProductAdmission(**{c.name: row[c.name] for c in columns}) for row in rows)
    if not all(
        evaluate_admission(a, a.product, purpose, checked, account=account, server=server).allowed
        for a in permissions
        for purpose in ("collection", "derived", "retention")
    ):
        raise StatusUnavailable("status_admission_unavailable")
    return _Authority(identity, permissions, tuple(row.row_hash for row in rows), checked)


async def load_status(db: AsyncSession, coin_id: int) -> StatusEvidence | None:
    """Fresh scalar columns, never a retained ORM authority instance."""
    row = (
        (
            await db.execute(
                select(*StockStatusEvidence.__table__.columns).where(
                    StockStatusEvidence.coin_id == coin_id
                )
            )
        )
        .mappings()
        .one_or_none()
    )
    return StatusEvidence(**row) if row else None


async def invalidate_status(db: AsyncSession, coin_id: int) -> bool:
    """Loss/startup may remove authority without obtaining new collection rights."""
    await acquire_stock_gate(db, coin_id)
    old = await load_status(db, coin_id)
    if old is None or (
        old.state == "unknown"
        and not old.continuity_current
        and not old.bootstrap_verified
        and old.valid_until is None
    ):
        return False
    if old.continuity_generation == MAX_SAFE:
        # Terminal exhaustion cannot advance or wrap, but must remove authority.
        # No later supported baseline generation can exceed this value.
        lost = replace(
            old,
            state="unknown",
            bootstrap_verified=False,
            continuity_current=False,
            valid_until=None,
        )
    else:
        lost = lose_status_continuity(old)
    await _write(db, lost)
    return True


async def _write(db: AsyncSession, value: StatusEvidence) -> None:
    from dataclasses import asdict

    data = asdict(value)
    statement = insert(StockStatusEvidence).values(**data)
    await db.execute(
        statement.on_conflict_do_update(
            index_elements=[StockStatusEvidence.coin_id],
            set_={key: getattr(statement.excluded, key) for key in data if key != "coin_id"},
        )
    )
    await db.flush()


async def persist_status_batch(
    db: AsyncSession,
    batch: StatusBatch,
    *,
    coin_id: int,
    account: str = "birja",
    server: str = "birja",
) -> StatusEvidence:
    """One instrument per transaction; final authority follows every write wait.

    No provider request is made. A caller partitions a validated finite source
    into sorted instrument transactions and rolls back on StatusUnavailable.
    """
    if (
        not isinstance(batch, StatusBatch)
        or type(batch.events) is not tuple
        or len(batch.events) > 1000
        or any(
            not isinstance(event, StatusEvent) or event.coin_id != coin_id for event in batch.events
        )
    ):
        raise ValueError("One instrument per status transaction")
    await acquire_stock_gate(db, coin_id)
    authority = await _authority(db, coin_id, account, server)
    status_permission = next(a for a in authority.admissions if a.product == "status")
    if batch.admission_generation != status_permission.generation:
        raise StatusUnavailable("status_generation_changed")
    old = await load_status(db, coin_id)
    value = normalize_status_batch(
        batch,
        {coin_id: old} if old is not None else {},
        {coin_id: authority.identity[0]},
        admission_until=min(
            authority.valid_until,
            batch.observed_at + timedelta(seconds=status_permission.quota["retention_seconds"]),
        )
        if utc(batch.observed_at)
        else authority.valid_until,
        now=authority.checked_at,
    )[coin_id]
    if value != old:
        await _write(db, value)
    final = await _authority(db, coin_id, account, server)
    if final.hashes != authority.hashes or final.identity != authority.identity:
        raise StatusUnavailable("status_authority_changed")
    if value.continuity_current and not status_current(value, final.checked_at):
        raise StatusUnavailable("status_expired")
    return value
