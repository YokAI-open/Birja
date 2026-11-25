"""PostgreSQL action accounting for a synthetic catalog issue."""

import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.models.stock_catalog import StockCatalogListing
from app.services.stock_catalog_promotion import CatalogFinancialBinding
from app.services.stock_sessions import build_sessions
from tests.portfolio_fixtures import PortfolioWorld, seed_portfolio_world
from tests.test_dividend_authority import apply, hold
from tests.test_stock_action_migrations import event
from tests.test_stock_catalog_finance_migration import finance_0025 as finance_0025
from tests.test_stock_catalog_promotion import (
    FIRST_ASSET,
    _listing,
    _promote,
    _reviewed_grant,
)
from tests.test_stock_catalog_promotion import (
    finance_0026 as finance_0026,
)
from tests.test_stock_catalog_publish import _manifest, _publish
from tests.test_stock_sessions import evidence

ACTION_FIELDS = {
    field: ["collection", "derivation", "storage", "backup"]
    for field in ("provider_event_id", "symbol", "event_type", "process_date", "terms")
}


@dataclass(frozen=True)
class ActionCase:
    binding: CatalogFinancialBinding
    listing: StockCatalogListing
    grant: int
    generation: int
    world: PortfolioWorld
    now: datetime
    cutoff: datetime
    next_open: datetime
    lease: datetime
    origin: datetime


async def action_grant(conn, binding, now, lease):
    scope = {
        "account": binding.account,
        "server": binding.server,
        "catalog_id": str(binding.catalog_id),
        "listing_id": str(binding.listing_id),
        "provider_asset_id": FIRST_ASSET,
        "feed": "alpaca-corporate-actions",
    }
    return await conn.scalar(
        text("""
        INSERT INTO stock_catalog_admissions
          (artifact,reference,reviewed_at,valid_until,fields,scope,is_fixture)
        VALUES ('catalog_actions','Synthetic SQL action evidence',:now,:lease,
          CAST(:fields AS jsonb),CAST(:scope AS jsonb),true) RETURNING id
        """),
        {
            "fields": json.dumps(ACTION_FIELDS),
            "scope": json.dumps(scope),
            "now": now,
            "lease": lease,
        },
    )


@pytest_asyncio.fixture
async def action_case(finance_0026, engine):
    async with finance_0026.begin() as db:
        now = await db.scalar(text("SELECT clock_timestamp()"))
        world = await seed_portfolio_world(await db.connection())
    published_at = now - timedelta(minutes=20)
    generation = await _publish(finance_0026, _manifest(published_at), None, now=published_at)
    listing = await _listing(finance_0026, generation.generation_id, "FQA")
    execution = await _reviewed_grant(finance_0026, listing, FIRST_ASSET, published_at)
    binding = await _promote(finance_0026, listing, execution, published_at)
    calendar = evidence(now)
    regular = [
        row
        for row in build_sessions(now, calendar)
        if row.exchange == "NASDAQ" and row.opens_at is not None
    ]
    last = max((row for row in regular if row.closes_at < now), key=lambda row: row.opens_at)
    upcoming = min((row for row in regular if row.opens_at > now), key=lambda row: row.opens_at)
    origin = last.opens_at - timedelta(days=1)
    lease = now + timedelta(minutes=10)
    async with engine.connect() as conn:
        tx = await conn.begin()
        await conn.execute(text("SELECT pg_advisory_xact_lock_shared(1026019025::bigint)"))
        await conn.execute(
            text(
                "SELECT pg_advisory_xact_lock(hashtextextended('birja.stock.instrument:' "
                "|| CAST(:coin AS text),0))"
            ),
            {"coin": str(binding.coin_id)},
        )
        grant = await action_grant(conn, binding, published_at, lease)
        case = ActionCase(
            binding,
            listing,
            grant,
            generation.generation_id,
            world,
            now,
            last.opens_at,
            upcoming.opens_at,
            lease,
            origin,
        )
        params = {
            "coin": binding.coin_id,
            "catalog": binding.catalog_id,
            "listing": listing.id,
            "grant": grant,
            "origin": origin,
            "now": now,
            "lease": lease,
        }
        # Seed an earlier empty journal origin for this already promoted synthetic issue.
        await conn.execute(
            text("UPDATE stock_catalog_instruments SET promoted_at=:origin WHERE coin_id=:coin"),
            params,
        )
        await conn.execute(
            text("""
            INSERT INTO stock_catalog_action_coverage
              (coin_id,catalog_id,listing_id,admission_id,journal_origin,coverage_start,
               covered_until,observed_at,valid_until)
            VALUES (:coin,:catalog,:listing,:grant,:origin,:origin,:now,:now,:lease)
            """),
            params,
        )
        await conn.execute(
            text("""
            UPDATE stock_action_state SET admission_generation=:grant,health='current',
              checked_at=:now,valid_until=:lease,journal_start_at=:origin,
              complete_from=:origin,coverage_start=:origin,covered_until=:now,sequence=1
            WHERE coin_id=:coin
            """),
            params,
        )
        calendar_row = asdict(calendar)
        calendar_row["scope"].update(
            durable_accounting=True,
            backup_restore=True,
            retention_mode="durable-accounting",
        )
        for key in ("scope", "quota", "allowed_fields", "calendar"):
            calendar_row[key] = json.dumps(calendar_row[key])
        await conn.execute(
            text("""
            INSERT INTO stock_data_admissions
              (product,state,generation,reviewed_at,valid_from,valid_until,evidence_ref,
               terms_version,attribution,collection_allowed,derived_allowed,display_allowed,
               retention_allowed,allowed_fields,scope,quota,calendar)
            VALUES (:product,:state,:generation,:reviewed_at,:valid_from,:valid_until,:evidence_ref,
              :terms_version,:attribution,:collection_allowed,:derived_allowed,:display_allowed,
              :retention_allowed,CAST(:allowed_fields AS jsonb),CAST(:scope AS jsonb),
              CAST(:quota AS jsonb),CAST(:calendar AS jsonb))
            """),
            calendar_row,
        )
        for session in (last, upcoming):
            await conn.execute(
                text("""
                INSERT INTO stock_sessions
                  (exchange,session_date,opens_at,closes_at,calendar_admission_generation,
                   coverage_start,coverage_end)
                VALUES ('NASDAQ',:date,:opens,:closes,:generation,:date,:date)
                """),
                {
                    "date": session.session_date,
                    "opens": session.opens_at,
                    "closes": session.closes_at,
                    "generation": calendar.generation,
                },
            )
        position = {**params, "portfolio": world.first, "owner": world.owner}
        await conn.execute(
            text("""
            INSERT INTO holdings (portfolio_id,coin_id,user_id,quantity,cost_basis)
            VALUES (:portfolio,:coin,:owner,2,87.65)
            """),
            position,
        )
        await conn.execute(
            text("""
            INSERT INTO stock_ownership_movements
              (portfolio_id,coin_id,user_id,sequence,economic_at,recorded_at,quantity,
               before_quantity,after_quantity,before_basis,after_basis,unit_epoch,
               cause_kind,causal_key)
            VALUES (:portfolio,:coin,:owner,1,:origin,:now,2,0,2,0,87.65,0,'opening','opening')
            """),
            position,
        )
        yield conn, case
        await tx.rollback()


async def record_revision(
    conn,
    case,
    event_id,
    source_id,
    *,
    ordinal,
    label,
    grant,
    terms,
    classification,
    cutoff=None,
    mutation="snapshot",
):
    fingerprint = format(ordinal, "064x")
    event_terms = {
        **terms,
        "coin_id": str(case.binding.coin_id),
        "catalog_id": str(case.binding.catalog_id),
        "listing_id": str(label.id),
        "symbol": label.ticker,
        "provider_asset_id": FIRST_ASSET,
    }
    params = {
        "event": event_id,
        "source": source_id,
        "ordinal": ordinal,
        "grant": grant,
        "fingerprint": fingerprint,
        "observed": case.now,
        "terms": json.dumps(event_terms),
        "classification": classification,
        "cutoff": cutoff,
        "mutation": mutation,
        "units": event_terms.get("units"),
    }
    if ordinal == 1:
        revision = await conn.scalar(
            text("""
            UPDATE stock_action_revisions SET fingerprint=:fingerprint,
              mutation_kind=:mutation,observed_at=:observed,admission_generation=:grant,
              normalized_terms=CAST(:terms AS jsonb),classification=:classification,
              verified_cutoff=:cutoff,units=:units
            WHERE event_id=:event AND ordinal=1 RETURNING id
            """),
            params,
        )
    else:
        revision = await conn.scalar(
            text("""
            INSERT INTO stock_action_revisions
              (event_id,source_id,ordinal,fingerprint,mutation_kind,observed_at,
               admission_generation,normalized_terms,classification,reason,verified_cutoff,units)
            VALUES (:event,:source,:ordinal,:fingerprint,:mutation,:observed,:grant,
              CAST(:terms AS jsonb),:classification,'synthetic',:cutoff,:units) RETURNING id
            """),
            params,
        )
    await conn.execute(
        text("UPDATE stock_action_events SET current_revision_id=:r WHERE id=:e"),
        {"r": revision, "e": event_id},
    )
    return revision, fingerprint


async def entitlement(conn, case, event_id, revision, fingerprint, *, version):
    params = {
        "event_id": event_id,
        "revision_id": revision,
        "revision_fingerprint": fingerprint,
        "portfolio": case.world.first,
        "owner": case.world.owner,
        "cutoff": case.cutoff,
        "version": version,
        "entitlement_fingerprint": format(100 + version, "064x"),
    }
    params["entitlement_id"] = await conn.scalar(
        text("""
        INSERT INTO stock_dividend_entitlements
          (event_id,portfolio_id,user_id,revision_id,cutoff,cutoff_rule,version,units_basis,
           unit_epoch,last_movement_sequence,eligible_quantity,state,fingerprint)
        VALUES (:event_id,:portfolio,:owner,:revision_id,:cutoff,'exclusive-regular-session-open',
          :version,'unit_epoch:0',0,1,2,'eligible',:entitlement_fingerprint) RETURNING id
        """),
        params,
    )
    return params


def verified_terms():
    return {
        "identity_verified": True,
        "dates_verified": True,
        "cancelled": False,
        "identity_changed": False,
        "due_bills": False,
    }


def dividend_terms(case, rate):
    day = str(case.cutoff.date())
    return {
        **verified_terms(),
        "event_type": "cash_dividend",
        "currency": "USD",
        "subtype": "ordinary",
        "foreign": False,
        "special": False,
        "rate": rate,
        "ex_date": day,
        "record_date": day,
        "payable_date": day,
    }


async def cash(conn, portfolio):
    return await conn.scalar(text("SELECT cash FROM accounts WHERE id=:p"), {"p": portfolio})


async def rename(conn, case):
    # Both generations are prepared in this synthetic transaction to keep the same journal.
    await conn.execute(text("UPDATE stock_catalog_generations SET is_active=false"))
    generation = await conn.scalar(
        text("""
        INSERT INTO stock_catalog_generations
          (manifest_sha256,mode,published_at,valid_until,is_active,sources,coverage)
        SELECT repeat('5',64),mode,published_at,valid_until,true,sources,coverage
        FROM stock_catalog_generations WHERE id=:old RETURNING id
        """),
        {"old": case.generation},
    )
    listing_id = await conn.scalar(
        text("""
        INSERT INTO stock_catalog_listings
          (generation_id,security_id,ticker,normalized_ticker,company_name,normalized_name,
           listing_exchange,classification,state,reason,source,row_key,row_digest,evidence_digest,
           evidence_at,valid_until,provider_asset_id,provider_symbol,provider_evidence_digest,
           provider_verified_at,provider_valid_until,provider_admission_id,unit_evidence_digest,
           unit_evidence_at,currency,units_per_share)
        SELECT :generation,security_id,'FQR','FQR','Renamed Synthetic','renamed synthetic',
          listing_exchange,classification,state,reason,source,row_key,row_digest,evidence_digest,
          evidence_at,valid_until,provider_asset_id,'FQR',provider_evidence_digest,
          provider_verified_at,provider_valid_until,provider_admission_id,unit_evidence_digest,
          unit_evidence_at,currency,units_per_share
        FROM stock_catalog_listings WHERE id=:old RETURNING id
        """),
        {"generation": generation, "old": case.listing.id},
    )
    mapping = await conn.scalar(
        text("""
        SELECT to_jsonb(a) FROM stock_catalog_admissions a
        JOIN stock_catalog_listings l ON l.provider_admission_id=a.id WHERE l.id=:old
        """),
        {"old": case.listing.id},
    )
    target = {
        **mapping["scope"]["units"][0]["target"],
        "listing_version": listing_id,
        "provider_symbol": "FQR",
    }
    mapping["scope"]["provider"]["targets"] = [target]
    mapping["scope"]["units"][0]["target"] = target
    provider_grant = await conn.scalar(
        text("""
        INSERT INTO stock_catalog_admissions
          (artifact,reference,reviewed_at,valid_until,fields,scope)
        SELECT artifact,reference,reviewed_at,valid_until,fields,CAST(:scope AS jsonb)
        FROM stock_catalog_admissions WHERE id=:old RETURNING id
        """),
        {"old": mapping["id"], "scope": json.dumps(mapping["scope"])},
    )
    await conn.execute(
        text("UPDATE stock_catalog_listings SET provider_admission_id=:p WHERE id=:id"),
        {"p": provider_grant, "id": listing_id},
    )
    binding = replace(case.binding, listing_id=listing_id)
    grant = await action_grant(
        conn,
        binding,
        case.now - timedelta(minutes=1),
        case.lease,
    )
    params = {
        "listing": listing_id,
        "catalog": binding.catalog_id,
        "coin": binding.coin_id,
        "grant": grant,
        "now": case.now,
        "lease": case.lease,
    }
    await conn.execute(
        text("""
        INSERT INTO stock_catalog_aliases
          (listing_id,security_id,namespace,symbol,normalized_symbol,verified_at,valid_until)
        VALUES (:listing,:catalog,'former','FQA','FQA',:now,:lease)
        """),
        params,
    )
    await conn.execute(
        text("UPDATE stock_catalog_instruments SET listing_id=:listing WHERE coin_id=:coin"),
        params,
    )
    await conn.execute(
        text("""
        UPDATE stock_catalog_action_coverage SET listing_id=:listing,admission_id=:grant
        WHERE coin_id=:coin
        """),
        params,
    )
    await conn.execute(
        text("UPDATE stock_action_state SET admission_generation=:grant WHERE coin_id=:coin"),
        params,
    )
    return StockCatalogListing(id=listing_id, ticker="FQR"), grant


async def test_catalog_action_dividend_correction_and_hold_keep_original_receipt(action_case):
    conn, case = action_case
    event_id, source_id, _ = await event(conn, case.binding.coin_id)
    original_revision, original_fingerprint = await record_revision(
        conn,
        case,
        event_id,
        source_id,
        ordinal=1,
        label=case.listing,
        grant=case.grant,
        terms=dividend_terms(case, "0.50"),
        classification="supported_dividend",
    )
    initial = await entitlement(
        conn,
        case,
        event_id,
        original_revision,
        original_fingerprint,
        version=1,
    )
    first = await apply(conn, initial)
    assert first["outcome"] == "original"
    assert await apply(conn, initial) == first
    assert await cash(conn, case.world.first) == Decimal("1235.56")

    renamed, grant = await rename(conn, case)
    corrected, corrected_fingerprint = await record_revision(
        conn,
        case,
        event_id,
        source_id,
        ordinal=2,
        label=renamed,
        grant=grant,
        terms=dividend_terms(case, "0.90"),
        classification="supported_dividend",
    )
    change = await entitlement(conn, case, event_id, corrected, corrected_fingerprint, version=2)
    correction = await apply(conn, change)
    assert correction["outcome"] == "applied"
    assert await apply(conn, change) == correction

    _, held_fingerprint = await record_revision(
        conn,
        case,
        event_id,
        source_id,
        ordinal=3,
        label=renamed,
        grant=grant,
        terms=dividend_terms(case, "1.00"),
        classification="uncertain",
    )
    held = await hold(conn, first["payment_id"], held_fingerprint)
    assert held["outcome"] == "held_uncertain"
    assert await hold(conn, first["payment_id"], held_fingerprint) == held
    assert await apply(conn, initial) == first
    assert await cash(conn, case.world.first) == Decimal("1236.36")
    assert await cash(conn, case.world.sibling) == Decimal("4321.09")
    assert await cash(conn, case.world.closed) == Decimal("55.55")
    assert (
        await conn.execute(
            text("""
        SELECT symbol,company_name FROM stock_dividend_payments
        UNION ALL SELECT symbol,company_name FROM stock_dividend_decisions
        """)
        )
    ).all() == [("FQA", case.listing.company_name)] * 3


@pytest.mark.parametrize(
    ("new_rate", "old_rate", "adjusted", "write_holding"),
    [("3", "1", 6, True), ("4", "3", None, False), ("3", "1", 6, False)],
)
async def test_catalog_action_split_persists_exact_basis_or_refuses_fraction(
    action_case,
    new_rate,
    old_rate,
    adjusted,
    write_holding,
):
    conn, case = action_case
    event_id, source_id, _ = await event(conn, case.binding.coin_id)
    revision, _ = await record_revision(
        conn,
        case,
        event_id,
        source_id,
        ordinal=1,
        label=case.listing,
        grant=case.grant,
        terms={
            **verified_terms(),
            "event_type": "forward_split",
            "units": "pre_split",
            "new_rate": new_rate,
            "old_rate": old_rate,
            "ex_date": str(case.cutoff.date()),
        },
        classification="supported_forward_split",
        cutoff=case.cutoff,
    )
    params = {
        "coin": case.binding.coin_id,
        "event": event_id,
        "revision": revision,
        "new": new_rate,
        "old": old_rate,
        "cutoff": case.cutoff,
    }

    async def post():
        async with conn.begin_nested():
            await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
            application = await conn.scalar(
                text("""
                INSERT INTO stock_split_applications
                  (coin_id,economic_event_id,revision_id,new_rate,old_rate,cutoff,prior_unit_epoch,
                   new_unit_epoch,sequence_boundary,before_digest,after_digest,
                   owner_digest_version,processed_at)
                VALUES (:coin,:event,:revision,:new,:old,:cutoff,0,1,1,repeat('a',64),
                  repeat('b',64),2,clock_timestamp()) RETURNING id
                """),
                params,
            )
            await conn.execute(
                text("""
                UPDATE stock_action_state SET unit_epoch=1,epoch=epoch+1,quote_not_before=:cutoff
                WHERE coin_id=:coin
                """),
                params,
            )
            if adjusted is not None:
                await conn.execute(
                    text("""
                    INSERT INTO stock_ownership_movements
                      (portfolio_id,coin_id,user_id,sequence,economic_at,recorded_at,quantity,
                       before_quantity,after_quantity,before_basis,after_basis,unit_epoch,
                       cause_kind,application_id,causal_key)
                    VALUES (:portfolio,:coin,:owner,2,:cutoff,clock_timestamp(),:delta,2,
                      :adjusted,87.65,87.65,1,'split',:application,:key)
                    """),
                    {
                        **params,
                        "application": application,
                        "owner": case.world.owner,
                        "portfolio": case.world.first,
                        "adjusted": adjusted,
                        "delta": adjusted - 2,
                        "key": f"split:{application}",
                    },
                )
            if write_holding:
                await conn.execute(
                    text("""
                    UPDATE holdings SET quantity=:quantity WHERE coin_id=:coin AND portfolio_id=:p
                    """),
                    {**params, "quantity": adjusted, "p": case.world.first},
                )
            await conn.execute(text("SET CONSTRAINTS stock_catalog_split_movements IMMEDIATE"))
            await conn.execute(text("RESET ROLE"))
            return application

    if not write_holding:
        with pytest.raises(DBAPIError, match="catalog split movements refused"):
            await post()
        assert await conn.scalar(text("SELECT count(*) FROM stock_split_applications")) == 0
    else:
        application = await post()
        assert (
            await conn.execute(
                text(
                    "SELECT after_quantity,after_basis FROM stock_ownership_movements "
                    "WHERE application_id=:a"
                ),
                {"a": application},
            )
        ).one() == (Decimal(adjusted), Decimal("87.65"))
        with pytest.raises(DBAPIError):
            await post()
        assert await conn.scalar(text("SELECT count(*) FROM stock_split_applications")) == 1


async def test_catalog_action_operator_requires_verified_rename_and_replays(action_case):
    conn, case = action_case
    # The migration installs the exact routine grant. The separate role
    # bootstrap supplies schema access after migration-only staging.
    await conn.execute(text("GRANT USAGE ON SCHEMA public TO birja_action_operator"))
    eid, source, _ = await event(conn, case.binding.coin_id)
    original, _ = await record_revision(
        conn,
        case,
        eid,
        source,
        ordinal=1,
        label=case.listing,
        grant=case.grant,
        terms=dividend_terms(case, "0.80"),
        classification="uncertain",
    )
    current, grant = await rename(conn, case)
    cancelled, fingerprint = await record_revision(
        conn,
        case,
        eid,
        source,
        ordinal=2,
        label=current,
        grant=grant,
        terms={**dividend_terms(case, "0.80"), "cancelled": True},
        classification="cancelled",
        mutation="delete",
    )
    await conn.execute(
        text("UPDATE stock_action_state SET health='reconciling' WHERE coin_id=:coin"),
        {"coin": case.binding.coin_id},
    )
    params = {
        "coin": case.binding.coin_id,
        "event": eid,
        "revision": cancelled,
        "generation": grant,
    }
    digests = (
        (
            await conn.execute(
                text("""
        SELECT
          (SELECT encode(sha256(convert_to(coalesce(jsonb_agg(to_jsonb(m) ORDER BY m.sequence),
              '[]'::jsonb)::text,'UTF8')),'hex')
             FROM stock_ownership_movements m WHERE coin_id=:coin) AS ledger,
          (SELECT encode(sha256(convert_to(to_jsonb(c)::text,'UTF8')),'hex')
             FROM stock_data_admissions c WHERE product='calendar') AS calendar,
          (SELECT encode(sha256(convert_to(to_jsonb(a)::text,'UTF8')),'hex')
             FROM (SELECT id,artifact,reviewed_at,valid_until,revoked_at,fields,scope,is_fixture
                   FROM stock_catalog_admissions WHERE id=:generation) a) AS admission,
          (SELECT generation::text FROM stock_data_admissions WHERE product='calendar')
            AS calendar_generation
        """),
                params,
            )
        )
        .mappings()
        .one()
    )
    evidence = {
        "format": 1,
        "unit_epoch": "0",
        "ledger_digest": digests["ledger"],
        "revision_fingerprint": fingerprint,
        "held_revision_ids": [original, cancelled],
        "observation_id": "0",
        "account": case.binding.account,
        "server": case.binding.server,
        "calendar_generation": digests["calendar_generation"],
        "review_valid_until": case.lease.isoformat(),
        "security_id": FIRST_ASSET,
        "cutoff": case.next_open.isoformat(),
        "alias_event_id": None,
        "calendar_digest": digests["calendar"],
        "admission_digest": digests["admission"],
    }

    async def resolve(*, key="synthetic-verified-cancellation", **changes):
        async with conn.begin_nested():
            await conn.execute(text("SET LOCAL ROLE birja_action_operator"))
            resolved = await conn.scalar(
                text("""
                WITH evidence(payload) AS (VALUES (CAST(:evidence AS jsonb)))
                SELECT public.apply_stock_action_resolution(:coin,:event,:revision,:generation,1,
                  :key,'confirm_no_effect',encode(sha256(convert_to(payload::text,'UTF8')),'hex'),
                  payload,'synthetic-test-operator') FROM evidence
                """),
                {**params, **changes, "key": key, "evidence": json.dumps(evidence)},
            )
            await conn.execute(text("RESET ROLE"))
            return resolved

    with pytest.raises(DBAPIError, match="resolution state stale"):
        await resolve(generation=case.grant)
    with pytest.raises(DBAPIError, match="catalog action identity unavailable"):
        async with conn.begin_nested():
            await conn.execute(text("DELETE FROM stock_catalog_aliases WHERE namespace='former'"))
            await resolve()

    resolved = await resolve()
    assert await resolve() == resolved
    assert await conn.scalar(text("SELECT count(*) FROM stock_action_resolutions")) == 1
    assert await cash(conn, case.world.first) == Decimal("1234.56")
    assert await conn.scalar(text("SELECT count(*) FROM stock_dividend_payments")) == 0
