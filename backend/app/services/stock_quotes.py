"""Latest stock quote persistence; caller owns the short transaction/commit."""

import logging
from collections.abc import Callable, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Text, and_, column, exists, false, func, or_, select, values
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.corporate_action import (
    StockActionEvent,
    StockActionRevision,
    StockActionState,
    StockSplitApplication,
)
from app.models.price import Coin
from app.models.stock import StockDataAdmission, StockInstrument, StockQuote
from app.services.stock_admission import ProductAdmission, evaluate_admission
from app.services.stock_ownership import OwnershipHeld, acquire_stock_gate
from app.services.stock_quote_rules import (
    CURATED_SYMBOLS,
    RawStockQuote,
    StockMapping,
    ValidatedStockQuote,
    utc,
    validate_quote,
)

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


async def load_stock_catalog(db: AsyncSession) -> list[StockMapping]:
    """Bounded stable identities; NULL verification is deliberately not authority."""
    result = await db.execute(
        select(
            Coin.id,
            Coin.symbol,
            StockInstrument.provider_asset_id,
            StockInstrument.provider_verified_at,
            StockInstrument.listing_exchange,
        )
        .join(StockInstrument, StockInstrument.coin_id == Coin.id)
        .where(Coin.asset_class == "stock", Coin.is_active, Coin.symbol.in_(CURATED_SYMBOLS))
        .order_by(Coin.sort_order, Coin.id)
        .limit(20)
    )
    return [StockMapping(*row) for row in result]


def _unit_authority(incoming: Any, units: int, action_evidence: ProductAdmission | None) -> Any:
    """Final-statement proof under the instrument gate; no caller commits."""
    from app.services.corporate_actions import action_hold_queries

    state, applied = StockActionState, StockSplitApplication
    if units == 0:
        return and_(
            ~exists(
                select(state.coin_id).where(
                    state.coin_id == incoming.c.coin_id, state.unit_epoch != 0
                )
            ),
            ~exists(select(applied.id).where(applied.coin_id == incoming.c.coin_id)),
        )
    if action_evidence is None:
        return false()
    held, missing = action_hold_queries(incoming.c.coin_id)
    current_action_permission = exists(
        select(StockDataAdmission.id).where(
            *(
                getattr(StockDataAdmission, name) == value
                for name, value in asdict(action_evidence).items()
            ),
            StockDataAdmission.valid_from <= func.clock_timestamp(),
            StockDataAdmission.valid_until > func.clock_timestamp(),
        )
    )
    current_boundary = exists(
        select(applied.id)
        .join(StockActionEvent, StockActionEvent.id == applied.economic_event_id)
        .where(
            applied.coin_id == state.coin_id,
            applied.new_unit_epoch == state.unit_epoch,
            applied.revision_id == StockActionEvent.current_revision_id,
            applied.cutoff == state.quote_not_before,
            incoming.c.event_at > applied.cutoff,
            or_(
                state.next_blocking_at.is_(None),
                state.next_blocking_at <= applied.cutoff,
                state.next_blocking_at > func.clock_timestamp(),
            ),
        )
        .correlate(state, incoming)
    )
    pending = exists(
        select(StockActionRevision.id)
        .join(StockActionEvent, StockActionEvent.current_revision_id == StockActionRevision.id)
        .where(
            StockActionEvent.coin_id == incoming.c.coin_id,
            StockActionRevision.classification == "supported_forward_split",
            or_(
                StockActionRevision.verified_cutoff.is_(None),
                StockActionRevision.verified_cutoff <= func.clock_timestamp(),
            ),
            ~exists(
                select(applied.id)
                .where(applied.economic_event_id == StockActionEvent.id)
                .correlate(StockActionEvent)
            ),
        )
        .correlate(incoming)
    )
    changed = exists(
        select(applied.id)
        .join(StockActionEvent, StockActionEvent.id == applied.economic_event_id)
        .where(
            applied.coin_id == incoming.c.coin_id,
            applied.revision_id != StockActionEvent.current_revision_id,
        )
        .correlate(incoming)
    )
    return and_(
        current_action_permission,
        ~exists(held),
        ~exists(missing),
        ~pending,
        ~changed,
        exists(
            select(state.coin_id)
            .where(
                state.coin_id == incoming.c.coin_id,
                state.unit_epoch == units,
                state.health == "current",
                state.admission_generation == action_evidence.generation,
                state.checked_at <= func.clock_timestamp(),
                state.valid_until > func.clock_timestamp(),
                state.coverage_start <= state.covered_until,
                state.covered_until <= func.clock_timestamp(),
                current_boundary,
            )
            .correlate(incoming)
        ),
    )


async def upsert_stock_quotes(
    db: AsyncSession,
    quotes: Sequence[ValidatedStockQuote],
    admission_generation: int,
    *,
    now: Callable[[], datetime] = _now,
    account: str = "birja",
    server: str = "birja",
) -> int:
    """Compare source times atomically; equal/older events do not renew receipt.

    The caller uses a short READ COMMITTED transaction and commits. Runtime has
    SELECT-only admission privileges: do not use FOR SHARE (requires UPDATE).
    Instead INSERT SELECT rechecks current committed evidence, its full snapshot,
    generation, catalogue mapping and database wall clock in the write statement.
    A change committed before that statement's snapshot prevents persistence.
    A later administrative change makes retained rows undisplayable through the
    generation checks at the read boundary; no lock grants extra authority.
    """
    if not quotes or len(quotes) > 20 or type(admission_generation) is not int:
        return 0
    admission_columns = [c for c in StockDataAdmission.__table__.columns if c.name != "id"]
    row = (
        (await db.execute(select(*admission_columns).where(StockDataAdmission.product == "quotes")))
        .mappings()
        .one_or_none()
    )
    evidence = ProductAdmission(**row) if row else None
    catalog = {mapping.coin_id: mapping for mapping in await load_stock_catalog(db)}
    checked_at = now()  # AFTER awaited reads; no cached receipt clock.
    if evidence is None or not all(
        evaluate_admission(
            evidence,
            "quotes",
            purpose,
            checked_at,
            expected_generation=admission_generation,
            account=account,
            server=server,
        ).allowed
        for purpose in ("collection", "retention", "derived")
    ):
        return 0
    accepted: dict[int, ValidatedStockQuote] = {}
    for quote in quotes:
        mapping = catalog.get(quote.coin_id)
        if (
            mapping is None
            or quote.symbol != mapping.symbol
            or quote.admission_generation != admission_generation
            or not utc(quote.event_at)
            or not utc(quote.collected_at)
            or quote.collected_at > checked_at
            or quote.session_date != quote.event_at.date()
        ):
            continue
        valid = validate_quote(
            RawStockQuote(
                mapping,
                quote.bid,
                quote.ask,
                quote.event_at,
                ["R"],
                tape="C" if mapping.listing_exchange == "NASDAQ" else "A",
                source=quote.source,
                feed=quote.feed,
            ),
            checked_at,
            admission_generation,
        )
        if valid is None or valid.mid != quote.mid or quote.event_at > quote.collected_at:
            continue
        previous = accepted.get(quote.coin_id)
        if previous is None or previous.event_at < quote.event_at:
            accepted[quote.coin_id] = quote
    if not accepted:
        return 0
    if len(accepted) != 1:
        # Each caller transaction owns exactly one financial instrument gate.
        # The scheduler partitions batches before entering this service.
        raise OwnershipHeld("one_instrument_per_transaction")
    coin_id = next(iter(accepted))
    await acquire_stock_gate(db, coin_id)
    current_row = (
        (await db.execute(select(*admission_columns).where(StockDataAdmission.product == "quotes")))
        .mappings()
        .one_or_none()
    )
    checked_at = now()
    if (
        current_row is None
        or ProductAdmission(**current_row) != evidence
        or not all(
            evaluate_admission(
                evidence,
                "quotes",
                purpose,
                checked_at,
                expected_generation=admission_generation,
                account=account,
                server=server,
            ).allowed
            for purpose in ("collection", "retention", "derived")
        )
    ):
        return 0
    units = (
        await db.execute(
            select(StockActionState.unit_epoch).where(StockActionState.coin_id == coin_id)
        )
    ).scalar_one_or_none() or 0
    action_evidence = None
    if units:
        action_row = (
            (
                await db.execute(
                    select(*admission_columns).where(StockDataAdmission.product == "actions")
                )
            )
            .mappings()
            .one_or_none()
        )
        action_evidence = ProductAdmission(**action_row) if action_row else None
        checked_at = now()
        if action_evidence is None or not all(
            evaluate_admission(
                action_evidence,
                "actions",
                purpose,
                checked_at,
                feed="alpaca-corporate-actions",
                account=account,
                server=server,
            ).allowed
            for purpose in ("collection", "retention", "derived")
        ):
            return 0
    checked_at = now()  # No authority/catalogue/gate wait can reuse the staged age.
    quote = accepted[coin_id]
    mapping = catalog[coin_id]
    if (
        validate_quote(
            RawStockQuote(
                mapping,
                quote.bid,
                quote.ask,
                quote.event_at,
                ["R"],
                tape="C" if mapping.listing_exchange == "NASDAQ" else "A",
                source=quote.source,
                feed=quote.feed,
            ),
            checked_at,
            admission_generation,
        )
        is None
        or quote.collected_at > checked_at
    ):
        return 0
    # Provider validation has no authority to assign an accounting unit epoch.
    # Keep this explicit when local storage gains columns.
    names = [
        "coin_id",
        "bid",
        "ask",
        "mid",
        "source",
        "feed",
        "event_at",
        "collected_at",
        "session_date",
        "admission_generation",
        "unit_epoch",
    ]
    incoming = (
        values(
            *(column(name, StockQuote.__table__.c[name].type) for name in names),
            column("symbol", Text),
            column("provider_asset_id", Text),
            column("provider_verified_at", DateTime(timezone=True)),
            column("listing_exchange", Text),
        )
        .data(
            [
                (
                    quote.coin_id,
                    quote.bid,
                    quote.ask,
                    quote.mid,
                    quote.source,
                    quote.feed,
                    quote.event_at,
                    quote.collected_at,
                    quote.session_date,
                    quote.admission_generation,
                    units,
                )
                + (
                    quote.symbol,
                    catalog[quote.coin_id].provider_asset_id,
                    catalog[quote.coin_id].provider_verified_at,
                    catalog[quote.coin_id].listing_exchange,
                )
                for quote in accepted.values()
            ]
        )
        .cte("incoming_stock_quotes")
    )
    admission = StockDataAdmission
    current_permission = exists(
        select(admission.id).where(
            *(getattr(admission, name) == value for name, value in asdict(evidence).items()),
            admission.valid_from <= func.clock_timestamp(),
            admission.valid_until > func.clock_timestamp(),
        )
    )
    current_mapping = exists(
        select(StockInstrument.coin_id)
        .join(
            Coin,
            Coin.id == StockInstrument.coin_id,
        )
        .where(
            Coin.id == incoming.c.coin_id,
            Coin.symbol == incoming.c.symbol,
            Coin.asset_class == "stock",
            Coin.is_active,
            StockInstrument.provider_asset_id == incoming.c.provider_asset_id,
            StockInstrument.provider_verified_at == incoming.c.provider_verified_at,
            StockInstrument.listing_exchange == incoming.c.listing_exchange,
        )
    )
    unit_authority = _unit_authority(incoming, units, action_evidence)
    stmt = insert(StockQuote).from_select(
        names,
        select(
            *(incoming.c[name] for name in names),
        ).where(current_permission, current_mapping, unit_authority),
    )
    returning = stmt.on_conflict_do_update(
        index_elements=[StockQuote.coin_id],
        set_={name: stmt.excluded[name] for name in names if name != "coin_id"},
        where=(StockQuote.event_at < stmt.excluded.event_at)
        & (StockQuote.unit_epoch <= stmt.excluded.unit_epoch),
    ).returning(StockQuote.coin_id)
    count = len((await db.execute(returning)).scalars().all())
    if count < len(accepted):
        logger.info(
            "stock quote write refused: nonnewer_or_authority_changed count=%s",
            len(accepted) - count,
        )
    return count
