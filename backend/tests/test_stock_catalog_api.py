"""Search and stable detail against the migrated, disposable PostgreSQL catalog."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx
from fastapi import FastAPI
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.stock_catalog import StockCatalogAdmission, StockCatalogAlias
from app.models.trade import Holding, Trade
from app.models.user import Account
from app.services.stock_catalog_publish import CatalogPublishError
from app.services.stock_catalog_search import catalog_item, get_catalog_listing, search_catalog
from app.services.stock_catalog_sources import CatalogAlias
from app.tasks.stock_catalog_inventory import CatalogManifest
from tests.helpers import OutboxSender, sign_in, unique_email
from tests.test_stock_catalog_publish import (
    NOW,
    SECOND,
    Factory,
    _listings,
    _manifest,
    _publish,
    _rights,
)
from tests.test_stock_catalog_publish import (
    catalog_factory as catalog_factory,
)

CATALOG = "/api/v1/stock-catalog"


def headings(
    manifest: CatalogManifest, names_and_classes: dict[str, tuple[str, str | None]]
) -> CatalogManifest:
    return manifest.model_copy(
        update={
            "rows": tuple(
                row.model_copy(
                    update={
                        "company_name": names_and_classes[row.ticker][0],
                        "share_class": names_and_classes[row.ticker][1],
                    }
                )
                if row.ticker in names_and_classes
                else row
                for row in manifest.rows
            )
        }
    )


async def test_search_ranking_ties_aliases_and_distinct_classes(
    catalog_factory: Factory, settings: Settings
) -> None:
    candidate = headings(
        _manifest(
            nasdaq=(
                ("Q", "exact"),
                ("AA", "alias"),
                ("QB.A", "ticker-prefix"),
                ("QB.B", "ticker-prefix-b"),
                ("ZA", "alias-prefix"),
                ("ZX", "name-prefix"),
                ("ZZ", "name-substring"),
            ),
            nyse=(("Q", "exact-nyse"),),
        ),
        {
            "QB.A": ("Fixture Holdings Class A", "A"),
            "QB.B": ("Fixture Holdings Class B", "B"),
            "ZX": ("Quartz Industry", None),
            "ZZ": ("Advanced Quartz", None),
        },
    )
    candidate = candidate.model_copy(
        update={
            "rows": tuple(
                row.model_copy(
                    update={
                        "aliases": (
                            *row.aliases,
                            CatalogAlias(
                                namespace="act", symbol="Q" if row.ticker == "AA" else "QZ"
                            ),
                            CatalogAlias(
                                namespace="cqs", symbol="Q" if row.ticker == "AA" else "QZ"
                            ),
                        )
                    }
                )
                if row.ticker in {"AA", "ZA"}
                else row
                for row in candidate.rows
            )
        }
    )
    receipt = await _publish(catalog_factory, candidate, None)
    async with catalog_factory() as db:
        result = await search_catalog(db, settings, "  q  ", now=NOW)
        assert result.state == "ready"
        assert result.generation_id == receipt.generation_id
        assert result.published_at == NOW
        assert not result.has_more
        assert [(i.ticker, i.listing_exchange) for i in result.items] == [
            ("Q", "NASDAQ"),
            ("Q", "NYSE"),
            ("AA", "NASDAQ"),
            ("QB.A", "NASDAQ"),
            ("QB.B", "NASDAQ"),
            ("ZA", "NASDAQ"),
            ("ZX", "NASDAQ"),
            ("ZZ", "NASDAQ"),
        ]
        classes = await search_catalog(db, settings, "fixture holdings", now=NOW)
        assert [row.share_class for row in classes.items] == ["A", "B"]
        assert len({row.catalog_id for row in classes.items}) == 2
        dotted = await search_catalog(db, settings, "qb.a", now=NOW)
        assert [row.ticker for row in dotted.items] == ["QB.A"]

    async with catalog_factory.begin() as db:
        aliases = await db.scalars(
            select(StockCatalogAlias).where(StockCatalogAlias.symbol == "QZ")
        )
        expired, pending = aliases.all()
        expired.verified_at = NOW - timedelta(hours=1)
        expired.valid_until = NOW
        pending.verified_at = NOW + timedelta(seconds=1)
    async with catalog_factory() as db:
        no_alias = await search_catalog(db, settings, "QZ", now=NOW)
        assert no_alias.state == "ready" and no_alias.items == []


async def test_search_bounds_literals_empty_and_fixture_readiness(
    catalog_factory: Factory, settings: Settings
) -> None:
    candidate = headings(
        _manifest(
            nasdaq=tuple((f"Z{i:02}", f"Group {i}") for i in range(21)),
            nyse=(("FQN", "Fixture Other"),),
        ),
        {"FQN": ("Percent % Capital / Under_score", None)},
    )
    await _publish(catalog_factory, candidate, None)
    async with catalog_factory() as db:
        result = await search_catalog(db, settings, "GROUP", now=NOW)
        assert result.has_more
        assert [item.ticker for item in result.items] == [f"Z{i:02}" for i in range(20)]
        for query in ("%", "_", "/", "under_score"):
            literal = await search_catalog(db, settings, query, now=NOW)
            assert [item.ticker for item in literal.items] == ["FQN"]
            assert not literal.has_more
        assert (await search_catalog(db, settings, "Z20", now=NOW)).items[0].ticker == "Z20"
        no_match = await search_catalog(db, settings, "MISSING", now=NOW)
        assert no_match.state == "ready" and no_match.items == [] and not no_match.has_more
        prod = settings.model_copy(update={"env": "prod"})
        for environment, current in ((prod, NOW), (settings, NOW + timedelta(days=4))):
            unavailable = await search_catalog(db, environment, "GROUP", now=current)
            assert unavailable.state == "unavailable" and unavailable.generation_id is None
            assert (
                await get_catalog_listing(db, environment, result.items[0].catalog_id, now=current)
                is None
            )


async def test_details_follow_identity_through_rename_failed_refresh_and_ticker_reuse(
    catalog_factory: Factory, settings: Settings
) -> None:
    first = await _publish(catalog_factory, _manifest(), None)
    async with catalog_factory() as db:
        before = (await search_catalog(db, settings, "FQA", now=NOW)).items[0]
    renamed = _manifest(SECOND, nasdaq=(("FQR", "fixture-nasdaq"),))
    with pytest.raises(CatalogPublishError, match="expected catalog generation"):
        await _publish(catalog_factory, renamed, None, now=SECOND)
    async with catalog_factory() as db:
        still_active = (await search_catalog(db, settings, "FQA", now=SECOND)).items[0]
        assert still_active == before
    second = await _publish(catalog_factory, renamed, first.generation_id, now=SECOND)
    async with catalog_factory() as db:
        former = (await search_catalog(db, settings, "FQA", now=SECOND)).items[0]
        assert former.catalog_id == before.catalog_id
        assert former.ticker == "FQR" and former.listing_version != before.listing_version
    # The old directory observation has expired while the new directory is current.
    third = SECOND + timedelta(days=5)
    await _publish(
        catalog_factory,
        _manifest(third, nasdaq=(("FQR", "new-share-class"),)),
        second.generation_id,
        now=third,
    )
    async with catalog_factory() as db:
        newcomer = (await search_catalog(db, settings, "FQR", now=third)).items[0]
        assert newcomer.catalog_id != before.catalog_id
        old = await get_catalog_listing(db, settings, before.catalog_id, now=third)
        assert old is not None
        assert catalog_item(old).state == "retired"
        assert catalog_item(old).reason == "verified_ticker_reuse"
        assert newcomer.company_name != old.company_name


async def test_search_and_details_use_current_field_rights_under_app_role(
    catalog_factory: Factory, settings: Settings
) -> None:
    rights = _rights()
    candidate = _manifest(rights=rights)
    candidate = candidate.model_copy(
        update={
            "rows": (
                candidate.rows[0].model_copy(
                    update={
                        "reason": "corroborated_share_class",
                        "aliases": (
                            CatalogAlias(namespace="openfigi", symbol="FIGI"),
                            CatalogAlias(namespace="act", symbol="ACT"),
                        ),
                    }
                ),
                candidate.rows[1],
            )
        }
    )
    async with catalog_factory.begin() as db:
        db.add_all(
            [
                StockCatalogAdmission(
                    artifact=right.artifact,
                    reference=right.reference,
                    reviewed_at=right.reviewed_at,
                    valid_until=right.valid_until,
                    fields=right.fields,
                    scope={},
                    is_fixture=False,
                )
                for right in rights
            ]
        )
    receipt = await _publish(catalog_factory, candidate, None)
    async with catalog_factory.begin() as db:
        listings = await _listings(db, receipt.generation_id)
        first = next(row for row in listings if row.ticker == "FQA").security_id
        assert (
            await db.scalar(
                text(
                    "SELECT has_column_privilege("
                    "'birja_app', 'stock_catalog_admissions', 'reference', 'SELECT')"
                )
            )
            is False
        )
        await db.execute(text("SET LOCAL ROLE birja_app"))
        for query in ("FQA", "FIGI", "ACT"):
            allowed = await search_catalog(db, settings, query, now=NOW)
            assert [item.catalog_id for item in allowed.items] == [first]
        assert await get_catalog_listing(db, settings, first, now=NOW) is not None

    async with catalog_factory.begin() as db:
        grants = {
            grant.artifact: grant for grant in await db.scalars(select(StockCatalogAdmission))
        }
        figi_fields = grants["openfigi"].fields
        grants["openfigi"].fields = {**figi_fields, "aliases": ["storage"]}
        directory = grants["nasdaqlisted"]
        directory.fields = {**directory.fields, "aliases": ["storage"]}
    async with catalog_factory() as db:
        for query in ("FIGI", "ACT"):
            result = await search_catalog(db, settings, query, now=NOW)
            assert not result.items and result.state == "ready"
        assert (await search_catalog(db, settings, "FQA", now=NOW)).items[0].catalog_id == first
    async with catalog_factory.begin() as db:
        grant = await db.scalar(
            select(StockCatalogAdmission).where(StockCatalogAdmission.artifact == "nasdaqlisted")
        )
        assert grant is not None
        grant.valid_until = SECOND
    async with catalog_factory() as db:
        assert await get_catalog_listing(db, settings, first, now=SECOND) is None
        expired = await search_catalog(db, settings, "FQA", now=SECOND)
        assert expired.state == "ready" and expired.items == []
        assert (await search_catalog(db, settings, "FQN", now=SECOND)).items[0].ticker == "FQN"


async def _financial_counts(db: AsyncSession) -> tuple[int, int, object]:
    holding_count = await db.scalar(select(func.count()).select_from(Holding))
    trade_count = await db.scalar(select(func.count()).select_from(Trade))
    assert holding_count is not None and trade_count is not None
    return holding_count, trade_count, await db.scalar(select(func.sum(Account.cash)))


async def test_search_and_details_http_auth_validation_and_no_external_work(
    catalog_factory: Factory,
    running_app: FastAPI,
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert (await auth_client.get(f"{CATALOG}/search", params={"q": "FQA"})).status_code == 401
    assert (await auth_client.get(f"{CATALOG}/1")).status_code == 401
    await sign_in(auth_client, outbox, unique_email("catalog"))

    class NoRedis:
        def __getattr__(self, name: str) -> object:
            raise AssertionError(f"catalog read attempted Redis operation {name}")

    monkeypatch.setattr(running_app.state, "redis", NoRedis())
    with respx.mock(assert_all_called=False) as outbound:
        empty = await auth_client.get(f"{CATALOG}/search", params={"q": "FQA"})
        assert empty.json() == {
            "state": "unavailable",
            "generation_id": None,
            "published_at": None,
            "has_more": False,
            "items": [],
        }
        now = datetime.now(UTC) - timedelta(seconds=1)
        receipt = await _publish(catalog_factory, _manifest(now), None, now=now)
        async with catalog_factory() as db:
            before = await _financial_counts(db)
        result = await auth_client.get(f"{CATALOG}/search", params={"q": f" {'FQA': >80} "})
        assert result.status_code == 200, result.text
        assert result.json()["generation_id"] == str(receipt.generation_id)
        [item] = result.json()["items"]
        assert set(item) == {
            "catalog_id",
            "listing_version",
            "ticker",
            "company_name",
            "listing_exchange",
            "share_class",
            "state",
            "reason",
        }
        assert item["listing_version"].isdecimal() and item["ticker"] == "FQA"
        details = await auth_client.get(f"{CATALOG}/{item['catalog_id']}")
        assert details.status_code == 200 and details.json() == item
        for response in (empty, result, details):
            assert response.headers["cache-control"] == "private, no-store"
            assert response.headers["vary"] == "Cookie, Authorization"
        unknown = await auth_client.get(f"{CATALOG}/9223372036854775807")
        assert unknown.status_code == 404
        for value in ("a" * 81, " ", "\x00"):
            invalid = await auth_client.get(f"{CATALOG}/search", params={"q": value})
            assert invalid.status_code == 422
        for path_id in ("0", "01", "1.0", "9223372036854775808"):
            assert (await auth_client.get(f"{CATALOG}/{path_id}")).status_code == 422
        async with catalog_factory() as db:
            assert await _financial_counts(db) == before
        assert not outbound.calls
