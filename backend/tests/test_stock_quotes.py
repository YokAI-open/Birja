"Actual isolated PostgreSQL proves source-time monotonicity and permission races."

import asyncio
from collections.abc import AsyncIterator
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.models.price import Coin
from app.models.stock import StockDataAdmission, StockInstrument, StockQuote
from app.services.stock_quote_rules import RawStockQuote, StockMapping, validate_quote
from app.services.stock_quotes import load_stock_catalog, upsert_stock_quotes
from tests.test_stock_admission import action_admitted, admitted

NOW = datetime.now(UTC)


@pytest_asyncio.fixture
async def db(engine: AsyncEngine, stock_state: list[StockMapping]) -> AsyncIterator[AsyncSession]:
    # Close/roll back each writer before restoring catalogue fixture values.
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session


@pytest_asyncio.fixture
async def stock_state(
    engine: AsyncEngine,
    clean_stock_discovery: None,
) -> AsyncIterator[list[StockMapping]]:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        originals = (await db.execute(select(StockInstrument))).scalars().all()
        saved = [(r.coin_id, r.provider_asset_id, r.provider_verified_at) for r in originals]
        for instrument in originals:
            instrument.provider_asset_id = f"synthetic-{instrument.coin_id}"
            instrument.provider_verified_at = NOW - timedelta(days=1)
        db.add(
            StockDataAdmission(
                **asdict(
                    replace(
                        admitted(),
                        reviewed_at=NOW - timedelta(hours=1),
                        valid_from=NOW - timedelta(hours=2),
                        valid_until=NOW + timedelta(hours=8),
                    )
                )
            )
        )
        await db.commit()
        rows = await db.execute(
            select(
                Coin.id,
                Coin.symbol,
                StockInstrument.provider_asset_id,
                StockInstrument.provider_verified_at,
                StockInstrument.listing_exchange,
            )
            .join(StockInstrument, StockInstrument.coin_id == Coin.id)
            .where(Coin.asset_class == "stock", Coin.is_active)
            .order_by(Coin.sort_order, Coin.id)
        )
        mappings = [StockMapping(*row) for row in rows]
    yield mappings
    async with factory() as db:
        await db.execute(delete(StockQuote))
        for coin_id, provider_id, verified_at in saved:
            await db.execute(
                update(StockInstrument)
                .where(StockInstrument.coin_id == coin_id)
                .values(provider_asset_id=provider_id, provider_verified_at=verified_at)
            )
        await db.commit()


def accepted(mapping: StockMapping, seconds: int = 0, bid: str = "100.00000001"):
    event = NOW + timedelta(seconds=seconds)
    result = validate_quote(
        RawStockQuote(
            mapping,
            Decimal(bid),
            Decimal("100.00000002"),
            event,
            ["R"],
            tape="C" if mapping.listing_exchange == "NASDAQ" else "A",
        ),
        event,
        4,
    )
    assert result is not None
    return result


async def test_catalogue_and_exact_durable_source_values(
    db: AsyncSession,
    stock_state: list[StockMapping],
) -> None:
    assert len(stock_state) == 20
    assert len({m.coin_id for m in stock_state}) == 20
    assert all(m.provider_asset_id and m.provider_verified_at for m in stock_state)
    assert await load_stock_catalog(db) == stock_state
    quote = replace(accepted(stock_state[0]), collected_at=NOW + timedelta(seconds=1))
    assert await upsert_stock_quotes(db, [quote], 4, now=lambda: NOW + timedelta(seconds=1)) == 1
    stored = await db.get(StockQuote, quote.coin_id)
    assert stored is not None
    assert (stored.bid, stored.ask, stored.mid) == (
        Decimal("100.00000001"),
        Decimal("100.00000002"),
        Decimal("100.00000002"),
    )
    assert stored.event_at == NOW and stored.collected_at == NOW + timedelta(seconds=1)
    assert stored.session_date == NOW.date()
    assert (stored.source, stored.feed, stored.admission_generation) == ("alpaca", "iex", 4)
    assert stored.unit_epoch == 0


async def test_older_equal_changed_and_partial_never_refresh_retained_observation(
    db: AsyncSession,
    stock_state: list[StockMapping],
) -> None:
    first, second = [accepted(m) for m in stock_state[:2]]
    assert await upsert_stock_quotes(db, [first, second], 4, now=lambda: NOW) == 2
    newer = accepted(stock_state[0], 2)
    assert await upsert_stock_quotes(db, [newer], 4, now=lambda: NOW + timedelta(seconds=2)) == 1
    equal_changed = replace(
        newer,
        bid=Decimal("100"),
        mid=Decimal("100.00000001"),
        collected_at=NOW + timedelta(seconds=3),
    )
    assert (
        await upsert_stock_quotes(
            db, [equal_changed, first], 4, now=lambda: NOW + timedelta(seconds=3)
        )
        == 0
    )
    db.expire_all()
    stored = await db.get(StockQuote, first.coin_id)
    other = await db.get(StockQuote, second.coin_id)
    assert stored is not None and other is not None
    assert stored.bid == newer.bid and stored.collected_at == newer.collected_at
    assert other.event_at == second.event_at and other.collected_at == second.collected_at


@pytest.mark.parametrize(
    "changes",
    [
        {"state": "revoked"},
        {"generation": 5},
        {"collection_allowed": False},
        {"retention_allowed": False},
        {"derived_allowed": False},
        {"valid_until": NOW},
        {"scope": {}},
        {"quota": {}},
    ],
)
async def test_current_permissions_are_required_before_any_write(
    db: AsyncSession,
    stock_state: list[StockMapping],
    changes: dict[str, object],
) -> None:
    await db.execute(update(StockDataAdmission).values(**changes))
    assert await upsert_stock_quotes(db, [accepted(stock_state[0])], 4, now=lambda: NOW) == 0
    assert await db.get(StockQuote, stock_state[0].coin_id) is None


@pytest.mark.parametrize(
    "changes",
    [
        {"event_at": NOW + timedelta(seconds=1)},
        {"collected_at": NOW + timedelta(seconds=1)},
        {"event_at": NOW - timedelta(seconds=120)},
        {"mid": Decimal("1")},
        {"feed": "sip"},
        {"coin_id": 1},
        {"symbol": "MSFT"},
        {"admission_generation": 5},
        {"bid": Decimal("NaN")},
        {"bid": Decimal("0.000000001")},
        {"session_date": NOW.date() - timedelta(days=1)},
    ],
)
async def test_forged_future_and_invalid_rows_are_refused_without_poisoning_batch(
    db: AsyncSession,
    stock_state: list[StockMapping],
    changes: dict[str, object],
) -> None:
    first, second = [accepted(m) for m in stock_state[:2]]
    assert (
        await upsert_stock_quotes(db, [replace(first, **changes), second], 4, now=lambda: NOW) == 1
    )
    assert await db.get(StockQuote, first.coin_id) is None
    assert await db.get(StockQuote, second.coin_id) is not None


async def test_current_catalogue_verification_and_empty_batch(
    db: AsyncSession,
    stock_state: list[StockMapping],
) -> None:
    quote = accepted(stock_state[0])
    await db.execute(
        update(StockInstrument)
        .where(StockInstrument.coin_id == quote.coin_id)
        .values(provider_verified_at=None)
    )
    assert await upsert_stock_quotes(db, [quote], 4, now=lambda: NOW) == 0
    assert await upsert_stock_quotes(db, [], 4, now=lambda: NOW) == 0
    assert await upsert_stock_quotes(db, [quote], 0, now=lambda: NOW) == 0


async def test_default_utc_clock_persists_a_current_observation(
    db: AsyncSession,
    stock_state: list[StockMapping],
) -> None:
    observed = datetime.now(UTC)
    quote = replace(accepted(stock_state[0]), event_at=observed, collected_at=observed)
    assert await upsert_stock_quotes(db, [quote], 4) == 1


async def test_concurrent_reordered_writes_only_keep_newest_source_event(
    engine: AsyncEngine,
    stock_state: list[StockMapping],
) -> None:
    factory = async_sessionmaker(engine)

    async def write(seconds: int) -> None:
        async with factory() as db:
            await upsert_stock_quotes(
                db, [accepted(stock_state[0], seconds)], 4, now=lambda: NOW + timedelta(seconds=10)
            )
            await db.commit()

    await asyncio.gather(*(write(seconds) for seconds in (3, 1, 9, 2, 8)))
    async with factory() as db:
        stored = await db.get(StockQuote, stock_state[0].coin_id)
        assert stored is not None and stored.event_at == NOW + timedelta(seconds=9)


async def test_revoke_committed_after_read_before_upsert_statement_is_enforced(
    engine: AsyncEngine,
    stock_state: list[StockMapping],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    factory = async_sessionmaker(engine)
    original = AsyncSession.execute
    revoked = False

    async def execute(self, statement, *args, **kwargs):
        nonlocal revoked
        if self.info.get("writer") and statement.is_insert and not revoked:
            async with factory() as admin:
                await admin.execute(
                    update(StockDataAdmission).values(state="revoked", generation=5)
                )
                await admin.commit()
            revoked = True
        return await original(self, statement, *args, **kwargs)

    monkeypatch.setattr(AsyncSession, "execute", execute)
    async with factory(info={"writer": True}) as db:
        assert await upsert_stock_quotes(db, [accepted(stock_state[0])], 4, now=lambda: NOW) == 0
        assert revoked
        assert await db.get(StockQuote, stock_state[0].coin_id) is None


async def test_real_clock_expiry_at_statement_not_only_snapshot(
    engine: AsyncEngine,
    stock_state: list[StockMapping],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    factory = async_sessionmaker(engine)
    real_now = datetime.now(UTC)
    evidence = replace(
        admitted(),
        reviewed_at=real_now - timedelta(hours=1),
        valid_from=real_now - timedelta(hours=2),
        valid_until=real_now + timedelta(seconds=1),
    )
    async with factory() as admin:
        await admin.execute(delete(StockDataAdmission))
        admin.add(StockDataAdmission(**asdict(evidence)))
        await admin.commit()
    original = AsyncSession.execute

    async def execute(self, statement, *args, **kwargs):
        if self.info.get("writer") and statement.is_insert:
            await asyncio.sleep(1.05)
        return await original(self, statement, *args, **kwargs)

    monkeypatch.setattr(AsyncSession, "execute", execute)
    quote = replace(accepted(stock_state[0]), event_at=real_now, collected_at=real_now)
    async with factory(info={"writer": True}) as db:
        assert await upsert_stock_quotes(db, [quote], 4, now=lambda: real_now) == 0
        assert await db.get(StockQuote, quote.coin_id) is None


@pytest.mark.parametrize("stored_quote", [False, True])
async def test_nonzero_units_refuse_old_writer(
    db: AsyncSession,
    stock_state: list[StockMapping],
    stored_quote: bool,
) -> None:
    quote = accepted(stock_state[0])
    if stored_quote:
        assert await upsert_stock_quotes(db, [quote], 4, now=lambda: NOW) == 1
        await db.execute(update(StockQuote).values(unit_epoch=1))
    else:
        await db.execute(
            text(
                "INSERT INTO "
                "stock_action_state(coin_id,admission_generation,unit_epoch) VALUES "
                "(:c,4,1)"
            ),
            {"c": quote.coin_id},
        )
    assert (
        await upsert_stock_quotes(
            db, [accepted(stock_state[0], 1)], 4, now=lambda: NOW + timedelta(seconds=1)
        )
        == 0
    )
    db.expire_all()
    stored = await db.get(StockQuote, quote.coin_id)
    if stored_quote:
        assert stored is not None and stored.unit_epoch == 1 and stored.event_at == NOW
    else:
        assert stored is None


@pytest.mark.parametrize("existing", [False, True])
async def test_committed_unit_change_before_final_statement(
    engine: AsyncEngine,
    stock_state: list[StockMapping],
    monkeypatch: pytest.MonkeyPatch,
    existing: bool,
) -> None:
    factory = async_sessionmaker(engine)
    cid = stock_state[0].coin_id
    if existing:
        async with factory() as db:
            assert (
                await upsert_stock_quotes(db, [accepted(stock_state[0])], 4, now=lambda: NOW) == 1
            )
            await db.commit()
    original = AsyncSession.execute
    changed = False

    async def execute(self, statement, *args, **kwargs):
        nonlocal changed
        if self.info.get("unit_writer") and statement.is_insert and not changed:
            async with factory() as admin:
                await original(
                    admin,
                    text(
                        "INSERT INTO "
                        "stock_action_state(coin_id,admission_generation,unit_epoch) VALUES "
                        "(:c,4,1)"
                    ),
                    {"c": cid},
                )
                await admin.commit()
            changed = True
        return await original(self, statement, *args, **kwargs)

    monkeypatch.setattr(AsyncSession, "execute", execute)
    try:
        async with factory(info={"unit_writer": True}) as db:
            assert (
                await upsert_stock_quotes(
                    db, [accepted(stock_state[0], 1)], 4, now=lambda: NOW + timedelta(seconds=1)
                )
                == 0
            )
            assert changed
    finally:
        async with factory() as db:
            await db.execute(text("DELETE FROM stock_action_state WHERE coin_id=:c"), {"c": cid})
            await db.commit()


async def test_genuine_post_split_event_acquires_local_current_units(db, stock_state):
    from app.models.corporate_action import StockActionState
    from tests.stock_action_fixtures import synthetic_split

    cid = stock_state[0].coin_id
    db.add(
        StockDataAdmission(
            **asdict(
                replace(
                    action_admitted(),
                    reviewed_at=NOW - timedelta(hours=1),
                    valid_from=NOW - timedelta(hours=2),
                    valid_until=NOW + timedelta(hours=8),
                )
            )
        )
    )
    db.add(
        StockActionState(
            coin_id=cid,
            admission_generation=4,
            health="current",
            checked_at=NOW,
            valid_until=NOW + timedelta(hours=1),
            coverage_start=NOW - timedelta(days=1),
            covered_until=NOW,
        )
    )
    await db.flush()
    await synthetic_split(db, cid, NOW - timedelta(seconds=1), boundary=0)
    state = await db.get(StockActionState, cid)
    state.quote_not_before = NOW - timedelta(seconds=1)
    await db.flush()
    assert await upsert_stock_quotes(db, [accepted(stock_state[0])], 4, now=lambda: NOW) == 1
    stored = await db.get(StockQuote, cid)
    assert stored.unit_epoch == 1
    assert stored.event_at == NOW
