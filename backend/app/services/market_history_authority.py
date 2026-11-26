"""Bind display history to the exact reviewed source, market identity and window."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import SchedulerSettings, Settings
from app.models.price import Coin
from app.models.stock import StockDataAdmission, StockInstrument
from app.models.stock_catalog import StockCatalogAdmission, StockCatalogGeneration
from app.schemas.market_history import (
    CatalogHistoryInstrument,
    CryptoHistoryInstrument,
    FeaturedHistoryInstrument,
    IexHistoryScope,
    KrakenHistoryScope,
    MarketHistoryQuery,
)
from app.services.market_history import HistoryWindow, crypto_history_window, equity_history_window
from app.services.stock_admission import ProductAdmission, evaluate_admission
from app.services.stock_catalog_quotes import load_catalog_asset_mapping
from app.services.stock_catalog_search import get_catalog_listing
from app.services.stock_sessions import build_sessions

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_MINUTE = timedelta(minutes=1)


class HistoryInstrumentNotFound(Exception):
    pass


class HistoryListingChanged(Exception):
    pass


@dataclass(frozen=True, slots=True)
class HistoryAuthority:
    scope: KrakenHistoryScope | IexHistoryScope
    provider_symbol: str
    window: HistoryWindow
    valid_until: datetime
    fingerprint: str


def _authority(
    scope: KrakenHistoryScope | IexHistoryScope,
    symbol: str,
    window: HistoryWindow,
    valid_until: datetime,
    identity: tuple[object, ...],
) -> HistoryAuthority:
    binding = (
        scope.model_dump_json(),
        symbol,
        identity,
        valid_until,
        window.range,
        window.source,
        window.start_at,
        window.end_at,
        window.request_start_at,
        window.expected_through_at,
        window.interval_minutes,
        window.coverage_known,
        window.slots,
        tuple(sorted(window.calendar_dates)),
        window.prior_close_start,
        window.expected_reference_start,
        window.identity_since,
    )
    fingerprint = sha256(repr(binding).encode()).hexdigest()
    return HistoryAuthority(scope, symbol, window, valid_until, fingerprint)


async def _crypto(
    db: AsyncSession,
    settings: Settings | SchedulerSettings,
    query: MarketHistoryQuery,
    now: datetime,
) -> HistoryAuthority | None:
    instrument = query.instrument
    assert isinstance(instrument, CryptoHistoryInstrument)  # noqa: S101 - dispatched by type
    coin = (
        await db.execute(
            select(Coin.id, Coin.kraken_pair).where(
                Coin.symbol == instrument.symbol, Coin.asset_class == "crypto", Coin.is_active
            )
        )
    ).one_or_none()
    if coin is None:
        raise HistoryInstrumentNotFound
    scopes = settings.market_history_scope_json
    scope = scopes.kraken if scopes is not None else None
    if scope is None or not scope.applies(now, settings.stock_data_server):
        return None
    matches = [target for target in scope.targets if target.instrument == instrument]
    if len(matches) != 1 or matches[0].pair != coin.kraken_pair:
        return None
    pair = matches[0].pair
    window = crypto_history_window(query.range, now)
    return _authority(scope, pair, window, scope.valid_until, (coin.id, instrument.symbol))


async def _calendar(db: AsyncSession) -> ProductAdmission | None:
    columns = [col for col in StockDataAdmission.__table__.columns if col.name != "id"]
    row = (
        (await db.execute(select(*columns).where(StockDataAdmission.product == "calendar")))
        .mappings()
        .one_or_none()
    )
    return ProductAdmission(**row) if row else None


async def _equity(
    db: AsyncSession,
    settings: Settings | SchedulerSettings,
    query: MarketHistoryQuery,
    now: datetime,
) -> HistoryAuthority | None:
    instrument = query.instrument
    listing = None
    if isinstance(instrument, CatalogHistoryInstrument):
        listing = await get_catalog_listing(db, settings, instrument.catalog_id, now=now)
        if listing is None:
            raise HistoryInstrumentNotFound
        if listing.id != instrument.listing_version:
            raise HistoryListingChanged
        if listing.state != "active":
            raise HistoryInstrumentNotFound
        exchange, provider_symbol, asset_id = (
            listing.listing_exchange,
            listing.provider_symbol,
            listing.provider_asset_id,
        )
        identity: tuple[object, ...] = (listing.security_id, listing.id, listing.generation_id)
    else:
        assert isinstance(instrument, FeaturedHistoryInstrument)  # noqa: S101 - dispatched by type
        row = (
            await db.execute(
                select(
                    Coin.id,
                    StockInstrument.listing_exchange,
                    StockInstrument.provider_asset_id,
                    StockInstrument.provider_verified_at,
                )
                .join(StockInstrument, StockInstrument.coin_id == Coin.id)
                .where(
                    Coin.symbol == instrument.symbol, Coin.asset_class == "stock", Coin.is_active
                )
            )
        ).one_or_none()
        if row is None:
            raise HistoryInstrumentNotFound
        exchange, provider_symbol, asset_id = (
            row.listing_exchange,
            instrument.symbol,
            row.provider_asset_id,
        )
        if row.provider_verified_at is None or row.provider_verified_at > now:
            return None
        identity = (row.id, instrument.symbol, row.provider_verified_at)

    scopes = settings.market_history_scope_json
    scope = scopes.alpaca_iex if scopes is not None else None
    if (
        scope is None
        or not settings.stock_data_enabled
        or scope.account != settings.stock_data_account
        or not scope.applies(now, settings.stock_data_server)
    ):
        return None
    matches = [target for target in scope.targets if target.instrument == instrument]
    if len(matches) != 1:
        return None
    target = matches[0]
    if (target.provider_symbol, target.provider_asset_id, target.exchange) != (
        provider_symbol,
        asset_id,
        exchange,
    ) or target.identity_since > now:
        return None
    deadline = scope.valid_until
    if listing is not None:
        mapping = await load_catalog_asset_mapping(
            db, listing, now, account=settings.stock_data_account, server=settings.stock_data_server
        )
        generation = await db.get(
            StockCatalogGeneration, listing.generation_id, populate_existing=True
        )
        if mapping is None or generation is None or not generation.is_active:
            return None
        mapping_evidence, mapping_until = mapping
        deadline = min(deadline, mapping_until, generation.valid_until)
        if generation.mode == "live":
            rights_until = await db.scalar(
                select(StockCatalogAdmission.valid_until)
                .where(
                    StockCatalogAdmission.id.in_(
                        (
                            listing.directory_admission_id,
                            listing.name_admission_id,
                            listing.classification_admission_id,
                        )
                    )
                )
                .order_by(StockCatalogAdmission.valid_until)
                .limit(1)
            )
            if rights_until is None:
                return None
            deadline = min(deadline, rights_until)
        identity += (mapping_evidence.evidence_digest,)

    calendar = await _calendar(db)
    account = settings.stock_data_account
    server = settings.stock_data_server
    decision = evaluate_admission(
        calendar, "calendar", "derived", now, account=account, server=server
    )
    if calendar is None or not decision.allowed or decision.valid_until is None:
        return None
    # Advance one minute after a complete bucket. A stable window lets the API
    # and worker share reads without serving an old window across a bar boundary.
    step = timedelta(minutes=5 if query.range == "1D" else 30)
    anchor = _EPOCH + ((now - _MINUTE - _EPOCH) // step) * step + _MINUTE
    window = equity_history_window(
        query.range,
        anchor,
        target.exchange,
        build_sessions(now, calendar, account=account, server=server),
        calendar_generation=calendar.generation,
        identity_since=target.identity_since,
    )
    if window is None:
        return None
    return _authority(
        scope,
        target.provider_symbol,
        window,
        min(deadline, decision.valid_until),
        (*identity, target.provider_asset_id, target.exchange, calendar.generation),
    )


async def resolve_history(
    db: AsyncSession,
    settings: Settings | SchedulerSettings,
    query: MarketHistoryQuery,
    now: datetime,
) -> HistoryAuthority | None:
    if isinstance(query.instrument, CryptoHistoryInstrument):
        return await _crypto(db, settings, query, now)
    return await _equity(db, settings, query, now)
