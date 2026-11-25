"""Publication against the real, guarded disposable catalog migration."""

import asyncio
import hashlib
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import get_args

import httpx
import pytest
import pytest_asyncio
from pydantic import TypeAdapter
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models.stock_catalog import (
    StockCatalogAdmission,
    StockCatalogAlias,
    StockCatalogGeneration,
    StockCatalogListing,
    StockCatalogSecurity,
)
from app.services.stock_catalog_classification import InventoryRow
from app.services.stock_catalog_provider import (
    CatalogAssetAdmission,
    CatalogAssetTarget,
    CatalogUnitEvidence,
    stage_catalog_assets,
)
from app.services.stock_catalog_publish import (
    CatalogPublishError,
    PublicationReceipt,
    promote_catalog_mappings,
    publish_catalog,
)
from app.services.stock_catalog_sources import CatalogAlias, DirectorySource, ListingExchange
from app.tasks import stock_catalog_import
from app.tasks.stock_catalog_import import _database_settings
from app.tasks.stock_catalog_inventory import (
    ArtifactRights,
    CatalogManifest,
    Purpose,
    SourceEvidence,
    _coverage,
)
from tests.test_migrations import test_migration_url as migration_url

NOW = datetime(2026, 11, 24, 15, tzinfo=UTC)
SECOND = NOW + timedelta(hours=1)
Factory = async_sessionmaker[AsyncSession]


@pytest_asyncio.fixture
async def catalog_factory(engine: AsyncEngine, migrated: None) -> AsyncIterator[Factory]:
    async def clear_catalog() -> None:
        async with engine.begin() as connection:
            for model in (
                StockCatalogAlias,
                StockCatalogListing,
                StockCatalogGeneration,
                StockCatalogSecurity,
                StockCatalogAdmission,
            ):
                await connection.execute(delete(model))

    await clear_catalog()
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await clear_catalog()


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _manifest(
    now: datetime = NOW,
    *,
    nasdaq: tuple[tuple[str, str], ...] = (("FQA", "fixture-nasdaq"),),
    nyse: tuple[tuple[str, str], ...] = (("FQN", "fixture-nyse"),),
    rights: tuple[ArtifactRights, ...] = (),
) -> CatalogManifest:
    def row(
        source: DirectorySource, venue: ListingExchange, position: int, ticker: str, issue: str
    ) -> InventoryRow:
        return InventoryRow(
            source=source,
            row_key=f"{source}:{position}",
            row_digest=_sha(f"{ticker}:{issue}:{venue}"),
            ticker=ticker,
            listing_exchange=venue,
            company_name=f"{issue} Common Stock",
            name_source=source,
            classification="common_stock",
            share_class=None,
            identity_key=f"review:{_sha(issue)}",
            aliases=(CatalogAlias(namespace="nasdaq", symbol=ticker),),
            disposition="included",
            reason="reviewed_issue_evidence",
            evidence_at=now - timedelta(minutes=3),
            evidence_digest=_sha(f"review:{ticker}:{issue}:{venue}"),
        )

    records = tuple(
        row("nasdaqlisted", "NASDAQ", i, ticker, issue)
        for i, (ticker, issue) in enumerate(nasdaq, start=1)
    ) + tuple(
        row("otherlisted", "NYSE", i, ticker, issue)
        for i, (ticker, issue) in enumerate(nyse, start=1)
    )
    return CatalogManifest(
        mode="live" if rights else "fixture",
        sources=(
            SourceEvidence(
                artifact="nasdaqlisted",
                sha256=_sha(f"NASDAQ {now} {nasdaq}"),
                published_at=now - timedelta(minutes=15),
                row_count=len(nasdaq),
            ),
            SourceEvidence(
                artifact="otherlisted",
                sha256=_sha(f"NYSE {now} {nyse}"),
                published_at=now - timedelta(minutes=10),
                row_count=len(nyse),
            ),
        ),
        rights=rights,
        rows=records,
        coverage=_coverage(records),
        complete=True,
    )


async def _publish(
    factory: Factory,
    candidate: CatalogManifest,
    expected: int | None,
    *,
    now: datetime = NOW,
) -> PublicationReceipt:
    async with factory.begin() as db:
        return await publish_catalog(db, candidate, expected, now=now, allow_fixture=True)


async def _listings(db: AsyncSession, generation_id: int) -> list[StockCatalogListing]:
    return list(
        await db.scalars(
            select(StockCatalogListing).where(StockCatalogListing.generation_id == generation_id)
        )
    )


async def test_publication_is_atomic_and_identical_replay_keeps_deadline(
    catalog_factory: Factory,
) -> None:
    initial = _manifest()
    async with catalog_factory.begin() as writer:
        receipt = await publish_catalog(writer, initial, None, now=NOW, allow_fixture=True)
        async with catalog_factory() as reader:
            assert await reader.scalar(select(StockCatalogGeneration.id)) is None
    replay = await _publish(catalog_factory, initial, None, now=SECOND)
    assert replay.disposition == "already_published"
    assert replay.generation_id == receipt.generation_id
    assert replay.active == 2
    async with catalog_factory() as reader:
        generation = (await reader.scalars(select(StockCatalogGeneration))).one()
        assert generation.published_at == NOW
        assert generation.valid_until == initial.sources[0].published_at + timedelta(days=4)


async def test_concurrent_competing_publications_compare_expected_generation(
    catalog_factory: Factory,
) -> None:
    first = _manifest()
    different = _manifest(nyse=(("FQZ", "second-issue"),))
    results = await asyncio.gather(
        _publish(catalog_factory, first, None),
        _publish(catalog_factory, different, None),
        return_exceptions=True,
    )
    successes = [result for result in results if isinstance(result, PublicationReceipt)]
    refusals = [result for result in results if isinstance(result, CatalogPublishError)]
    assert len(successes) == len(refusals) == 1
    assert "expected catalog generation" in str(refusals[0])
    async with catalog_factory() as db:
        assert (
            await db.scalars(
                select(StockCatalogGeneration.id).where(StockCatalogGeneration.is_active)
            )
        ).one() == successes[0].generation_id
        assert len(await _listings(db, successes[0].generation_id)) == 2


async def test_rename_and_venue_move_preserve_issue_and_record_former_ticker(
    catalog_factory: Factory,
) -> None:
    first = await _publish(catalog_factory, _manifest(), None)
    changed = _manifest(
        SECOND,
        nasdaq=(("FQX", "another-nasdaq"),),
        nyse=(("FQN", "fixture-nyse"), ("FRN", "fixture-nasdaq")),
    )
    second = await _publish(catalog_factory, changed, first.generation_id, now=SECOND)
    async with catalog_factory() as db:
        old = next(row for row in await _listings(db, first.generation_id) if row.ticker == "FQA")
        new = next(row for row in await _listings(db, second.generation_id) if row.ticker == "FRN")
        assert (old.listing_exchange, new.listing_exchange) == ("NASDAQ", "NYSE")
        assert old.security_id == new.security_id and old.id != new.id
        alias = (
            await db.scalars(
                select(StockCatalogAlias).where(
                    StockCatalogAlias.listing_id == new.id, StockCatalogAlias.namespace == "former"
                )
            )
        ).one()
        assert (alias.symbol, alias.security_id, alias.valid_until) == (
            "FQA",
            old.security_id,
            old.valid_until,
        )


async def test_ticker_reuse_retires_old_issue_and_missing_corroboration_stays_review(
    catalog_factory: Factory,
) -> None:
    first = _manifest(nasdaq=(("FQA", "old-issue"), ("FQB", "missing-issue")))
    published = await _publish(catalog_factory, first, None)
    refreshed = _manifest(SECOND, nasdaq=(("FQA", "replacement-issue"),))
    updated = await _publish(catalog_factory, refreshed, published.generation_id, now=SECOND)
    async with catalog_factory() as db:
        before = {item.ticker: item for item in await _listings(db, published.generation_id)}
        rows = await _listings(db, updated.generation_id)
        replacement = next(row for row in rows if row.ticker == "FQA" and row.state == "active")
        assert replacement.security_id != before["FQA"].security_id
        originals = {row.security_id: row for row in rows if row.state != "active"}
        assert originals[before["FQA"].security_id].reason == "verified_ticker_reuse"
        assert originals[before["FQB"].security_id].state == "review"
        assert originals[before["FQA"].security_id].valid_until == before["FQA"].valid_until
        assert (updated.active, updated.review, updated.retired) == (2, 1, 1)


@pytest.mark.parametrize("figi_first", [True, False])
async def test_evidence_source_change_cannot_retire_the_same_ticker(
    catalog_factory: Factory, figi_first: bool
) -> None:
    def candidate(at: datetime, use_figi: bool) -> CatalogManifest:
        manifest = _manifest(at)
        if not use_figi:
            return manifest
        row = manifest.rows[0].model_copy(
            update={
                "identity_key": "figi:BBG001ABC234",
                "reason": "corroborated_share_class",
            }
        )
        return manifest.model_copy(update={"rows": (row, *manifest.rows[1:])})

    original = await _publish(catalog_factory, candidate(NOW, figi_first), None)
    with pytest.raises(CatalogPublishError, match="identity needs review"):
        await _publish(
            catalog_factory, candidate(SECOND, not figi_first), original.generation_id, now=SECOND
        )
    async with catalog_factory() as db:
        active = await db.scalar(
            select(StockCatalogGeneration).where(StockCatalogGeneration.is_active)
        )
        assert active is not None and active.id == original.generation_id
        listings = await _listings(db, active.id)
        assert len(listings) == 2 and {listing.state for listing in listings} == {"active"}
        assert await db.scalar(select(func.count()).select_from(StockCatalogSecurity)) == 2


async def test_bad_pair_incomplete_candidate_and_mass_removal_keep_active_version(
    catalog_factory: Factory,
) -> None:
    many = tuple((f"FX{i}", f"fixture-issue-{i}") for i in range(12))
    first = _manifest(nasdaq=many)
    receipt = await _publish(catalog_factory, first, None)
    changed = _manifest(SECOND, nasdaq=many[:3])
    with pytest.raises(CatalogPublishError, match="unexpectedly remove"):
        await _publish(catalog_factory, changed, receipt.generation_id, now=SECOND)
    stale = changed.model_copy(update={"sources": (changed.sources[0], first.sources[1])})
    with pytest.raises(CatalogPublishError):
        await _publish(catalog_factory, stale, receipt.generation_id, now=SECOND)
    incomplete = changed.model_copy(update={"complete": False})
    with pytest.raises(CatalogPublishError, match="coverage does not reconcile"):
        await _publish(catalog_factory, incomplete, receipt.generation_id, now=SECOND)

    async with catalog_factory() as db:
        active = (await db.scalars(select(StockCatalogGeneration))).one()
        assert active.id == receipt.generation_id and active.is_active
        assert active.valid_until == first.sources[0].published_at + timedelta(days=4)


def _rights() -> tuple[ArtifactRights, ...]:
    directory = (
        "ticker",
        "listing_exchange",
        "company_name",
        "aliases",
        "share_class",
        "eligibility",
        "source_evidence",
    )
    return TypeAdapter(tuple[ArtifactRights, ...]).validate_json(
        json.dumps(
            [
                {
                    "artifact": artifact,
                    "reference": "Fixture representing independent reviewed field rights",
                    "reviewed_at": (NOW - timedelta(hours=2)).isoformat(),
                    "valid_until": (NOW + timedelta(days=1)).isoformat(),
                    "fields": {field: get_args(Purpose) for field in fields},
                }
                for artifact, fields in (
                    ("nasdaqlisted", directory),
                    ("otherlisted", directory),
                    ("openfigi", ("identity_key", "classification", "source_evidence", "aliases")),
                    ("issuer_exception", ("identity_key", "classification", "source_evidence")),
                )
            ]
        )
    )


async def test_manifest_rights_require_a_current_independent_durable_decision(
    catalog_factory: Factory,
) -> None:
    rights = _rights()
    candidate = _manifest(rights=rights)
    with pytest.raises(CatalogPublishError, match="trusted operator admission"):
        await _publish(catalog_factory, candidate, None)
    async with catalog_factory.begin() as db:
        for right in rights:
            db.add(
                StockCatalogAdmission(
                    **right.model_dump(mode="json", exclude={"reviewed_at", "valid_until"}),
                    reviewed_at=right.reviewed_at,
                    valid_until=right.valid_until,
                    scope={},
                    is_fixture=False,
                )
            )
    receipt = await _publish(catalog_factory, candidate, None)
    async with catalog_factory.begin() as db:
        decision = (
            await db.scalars(
                select(StockCatalogAdmission).where(StockCatalogAdmission.artifact == "openfigi")
            )
        ).one()
        decision.revoked_at = NOW + timedelta(minutes=1)
    with pytest.raises(CatalogPublishError, match="trusted operator admission"):
        await _publish(catalog_factory, candidate, receipt.generation_id, now=SECOND)


async def test_operator_admission_requires_exact_apply_and_current_generation(
    catalog_factory: Factory, tmp_path: Path
) -> None:
    now = datetime.now(UTC)
    rows = [
        {
            **right.model_dump(mode="json"),
            "reviewed_at": (now - timedelta(minutes=5)).isoformat(),
            "valid_until": (now + timedelta(hours=1)).isoformat(),
            "scope": {},
        }
        for right in _rights()
    ]
    packet = tmp_path / "review.json"
    raw = json.dumps({"version": 1, "admissions": rows})
    packet.write_text(raw)
    digest = _sha(raw)
    migrator = create_async_engine(migration_url())
    command = ["admit", str(packet), "--expect-generation", "empty"]
    async with catalog_factory.begin() as admin:
        owner = await admin.scalar(
            text("SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname='public'")
        )
        assert owner in {"pg_database_owner", "birja_test"}
        # The migration suite's disposable reset uses birja_test as schema
        # owner. The operator rehearsal uses the production ownership shape.
        if owner == "birja_test":
            await admin.execute(text("ALTER SCHEMA public OWNER TO pg_database_owner"))
    try:
        review = await stock_catalog_import._admit(migrator, stock_catalog_import._args(command))
        assert review == {"disposition": "reviewed", "packet_sha256": digest, "count": 4}
        async with catalog_factory() as reader:
            assert await reader.scalar(select(func.count()).select_from(StockCatalogAdmission)) == 0

        with pytest.raises(CatalogPublishError):
            await stock_catalog_import._admit(
                migrator,
                stock_catalog_import._args(
                    [*command, "--apply", "--expected-packet-sha", "0" * 64]
                ),
            )
        applied = await stock_catalog_import._admit(
            migrator,
            stock_catalog_import._args([*command, "--apply", "--expected-packet-sha", digest]),
        )
        assert applied["disposition"] == "applied"
        with pytest.raises(CatalogPublishError, match="overlaps"):
            await stock_catalog_import._admit(migrator, stock_catalog_import._args(command))
        async with catalog_factory() as reader:
            assert await reader.scalar(select(func.count()).select_from(StockCatalogAdmission)) == 4

        rights = tuple(
            ArtifactRights.model_validate_json(
                json.dumps({k: v for k, v in row.items() if k != "scope"})
            )
            for row in rows
        )
        published = await _publish(catalog_factory, _manifest(now, rights=rights), None, now=now)
        with pytest.raises(CatalogPublishError, match="generation"):
            await stock_catalog_import._admit(migrator, stock_catalog_import._args(command))
        assert published.generation_id > 0
        current_command = [
            "admit",
            str(packet),
            "--expect-generation",
            str(published.generation_id),
        ]
        expired = {**rows[0], "valid_until": (now - timedelta(seconds=1)).isoformat()}
        packet.write_text(json.dumps({"version": 1, "admissions": [expired]}))
        with pytest.raises(CatalogPublishError, match="UTC validity"):
            await stock_catalog_import._admit(migrator, stock_catalog_import._args(current_command))
        replacement = {**rows[0], "reference": "Reviewed synthetic replacement"}
        admission_ids = applied["admission_ids"]
        assert isinstance(admission_ids, list)
        prior_id = int(admission_ids[0])
        raw = json.dumps({"version": 1, "admissions": [replacement], "revoke_ids": [prior_id]})
        packet.write_text(raw)
        reviewed = await stock_catalog_import._admit(
            migrator, stock_catalog_import._args(current_command)
        )
        assert reviewed["revoked_count"] == 1
        async with catalog_factory() as reader:
            prior = await reader.get(StockCatalogAdmission, prior_id)
            assert prior is not None and prior.revoked_at is None
        await stock_catalog_import._admit(
            migrator,
            stock_catalog_import._args(
                [*current_command, "--apply", "--expected-packet-sha", _sha(raw)]
            ),
        )
        async with catalog_factory() as reader:
            prior = await reader.get(StockCatalogAdmission, prior_id)
            assert prior is not None and prior.revoked_at is not None
            assert prior.reference == rows[0]["reference"]
            conn = await reader.connection()
            for role in ("birja_app", "birja_scheduler"):
                assert (
                    await conn.scalar(
                        text(
                            "SELECT has_table_privilege(:role,'stock_catalog_admissions','INSERT')"
                        ),
                        {"role": role},
                    )
                    is False
                )
            with pytest.raises(ValueError, match="restricted migrator"):
                await stock_catalog_import._check_connection(conn, False, for_finance=True)
    finally:
        await migrator.dispose()
        if owner == "birja_test":
            async with catalog_factory.begin() as admin:
                await admin.execute(text("ALTER SCHEMA public OWNER TO birja_test"))


async def test_fixture_manifest_requires_explicit_disposable_mode(
    catalog_factory: Factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with catalog_factory.begin() as db:
        with pytest.raises(CatalogPublishError, match="isolated test database"):
            await publish_catalog(db, _manifest(), None, now=NOW)
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv(
        "BIRJA_CATALOG_DATABASE_URL",
        "postgresql+asyncpg://birja_test@127.0.0.1:55432/birja_test",
    )
    with pytest.raises(CatalogPublishError, match="isolated local test database"):
        _database_settings(True)


async def test_both_exchange_asset_proofs_bind_only_their_current_listing_version(
    catalog_factory: Factory,
) -> None:
    initial = await _publish(catalog_factory, _manifest(), None)
    async with catalog_factory.begin() as db:
        rows = await _listings(db, initial.generation_id)
        by_exchange = {row.listing_exchange: row for row in rows}
        targets = (
            CatalogAssetTarget(
                catalog_id=by_exchange["NASDAQ"].security_id,
                listing_version=by_exchange["NASDAQ"].id,
                listing_exchange="NASDAQ",
                provider_symbol="FQA",
            ),
            CatalogAssetTarget(
                catalog_id=by_exchange["NYSE"].security_id,
                listing_version=by_exchange["NYSE"].id,
                listing_exchange="NYSE",
                provider_symbol="FQN",
            ),
        )
        units = tuple(
            CatalogUnitEvidence(
                target=target,
                currency="USD",
                units_per_share=1,
                classification="common_stock",
                reviewed_at=NOW - timedelta(hours=2),
                valid_until=NOW + timedelta(days=1),
                evidence_digest=_sha(target.provider_symbol),
            )
            for target in targets
        )
        admission = CatalogAssetAdmission(
            account="fixture",
            server="fixture",
            environment="paper",
            reviewed_at=NOW - timedelta(hours=1),
            valid_until=NOW + timedelta(days=1),
            evidence_digest=_sha("admission"),
            targets=targets,
            purposes=frozenset(get_args(Purpose)),
            request_limit=2,
        )
        record = StockCatalogAdmission(
            artifact="alpaca_assets",
            reference="Fixture reviewed Alpaca mapping and share units",
            reviewed_at=admission.reviewed_at,
            valid_until=admission.valid_until,
            fields={
                field: get_args(Purpose)
                for field in (
                    "provider_asset_id",
                    "provider_symbol",
                    "asset_evidence",
                    "currency",
                    "units_per_share",
                    "unit_evidence",
                )
            },
            scope={
                "provider": admission.model_dump(mode="json"),
                "units": [unit.model_dump(mode="json") for unit in units],
            },
            is_fixture=False,
        )
        db.add(record)
        await db.flush()
        admission_id = record.id

    provider_ids = {
        "FQA": "21000000-1234-4567-b89a-000000000001",
        "FQN": "21000000-1234-4567-b89a-000000000002",
    }

    def respond(request: httpx.Request) -> httpx.Response:
        target = next(
            value for value in targets if request.url.path.endswith(value.provider_symbol)
        )
        return httpx.Response(
            200,
            json={
                "id": provider_ids[target.provider_symbol],
                "symbol": target.provider_symbol,
                "class": "us_equity",
                "status": "active",
                "exchange": target.listing_exchange,
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        proofs = await stage_catalog_assets(
            client,
            units,
            admission,
            account="fixture",
            server="fixture",
            expected_listings={target.catalog_id: target for target in targets},
            clock=lambda: NOW,
        )
    altered = proofs[1].model_copy(update={"evidence_digest": _sha("altered")})
    with pytest.raises(CatalogPublishError, match="evidence was refused"):
        async with catalog_factory.begin() as db:
            await promote_catalog_mappings(
                db, admission_id, (proofs[0], altered), now=NOW, allow_fixture=True
            )
    async with catalog_factory.begin() as db:
        rows = await _listings(db, initial.generation_id)
        assert all(row.provider_asset_id is None for row in rows)
        assert (
            await promote_catalog_mappings(db, admission_id, proofs, now=NOW, allow_fixture=True)
            == 2
        )
        assert {row.ticker: row.provider_asset_id for row in rows} == provider_ids
        assert all((row.currency, row.units_per_share) == ("USD", 1) for row in rows)

    updated = await _publish(catalog_factory, _manifest(SECOND), initial.generation_id, now=SECOND)
    with pytest.raises(CatalogPublishError, match="listing version"):
        async with catalog_factory.begin() as db:
            await promote_catalog_mappings(db, admission_id, proofs, now=SECOND, allow_fixture=True)
    async with catalog_factory() as db:
        assert all(
            row.provider_asset_id is None for row in await _listings(db, updated.generation_id)
        )
