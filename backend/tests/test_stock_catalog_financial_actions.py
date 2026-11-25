"""The catalog effect services use scoped 0026 fixtures and restricted roles."""

import json
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.db.portfolio_bootstrap import GRANTS_0026_SQL
from app.models.corporate_action import StockActionRevision, StockActionState
from app.models.stock import StockInstrument
from app.services import corporate_actions
from app.services.alpaca_actions import ActionBatch, ActionObservation
from app.services.corporate_action_rules import NormalizedAction
from app.services.corporate_actions import (
    ActionHeld,
    apply_due_actions,
    derive_dividend_entitlements,
    persist_action_batch,
)
from app.services.dividends import process_dividend
from app.services.stock_action_reconciliation import ResolutionRequest, reconcile
from app.services.stock_catalog_actions import load_catalog_action_authority
from app.services.stock_catalog_provider import (
    CatalogAssetTarget,
    CatalogUnitEvidence,
    _mapping_digest,
)
from app.services.stock_sessions import build_sessions
from tests.portfolio_fixtures import portfolio_session
from tests.test_stock_catalog_finance_migration import finance_0025 as finance_0025
from tests.test_stock_catalog_promotion import finance_0026 as finance_0026
from tests.test_stock_catalog_sql_actions import action_case as action_case
from tests.test_stock_catalog_sql_actions import cash, rename


@pytest_asyncio.fixture
async def scoped_actions(action_case):
    conn, case = action_case
    raw = await conn.get_raw_connection()
    await raw.driver_connection.execute(GRANTS_0026_SQL)
    return conn, case


@asynccontextmanager
async def _scheduler(conn):
    async with conn.begin_nested():
        await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
        async with portfolio_session(conn) as db:
            yield db
        await conn.execute(text("RESET ROLE"))


async def _authority(db, case):
    authority = await load_catalog_action_authority(
        db,
        case.binding.coin_id,
        case.now,
        account=case.binding.account,
        server=case.binding.server,
        allow_fixture=True,
    )
    assert authority is not None
    return authority


def _dividend(case, **changes):
    day = case.cutoff.date()
    return replace(
        NormalizedAction(
            str(uuid4()),
            case.binding.coin_id,
            case.listing.ticker,
            "cash_dividend",
            day,
            case.now,
            currency="USD",
            rate=Decimal("0.50"),
            ex_date=day,
            record_date=day,
            payable_date=day,
            subtype="ordinary",
            foreign=False,
            special=False,
            due_bills=False,
            identity_verified=True,
            dates_verified=True,
        ),
        **changes,
    )


async def _ingest(db, case, action, **observation):
    authority = await _authority(db, case)
    (result,) = await persist_action_batch(
        db,
        ActionBatch(
            records=(action,),
            observations=(ActionObservation(action, **observation),),
            complete=True,
        ),
        None,
        account=authority.binding.account,
        server=authority.binding.server,
        catalog=authority,
    )
    return authority, result


async def _derive(conn, case, action):
    async with _scheduler(conn) as db, db.begin():
        authority, revision = await _ingest(db, case, action)
        (entitlement,) = await derive_dividend_entitlements(
            db, revision.event_id, catalog=authority
        )
        assert entitlement.state == "eligible"
        assert entitlement.eligible_quantity == 2
        row = await db.get(StockActionRevision, revision.revision_id)
        assert row is not None
    return {
        "portfolio_id": entitlement.portfolio_id,
        "event_id": entitlement.event_id,
        "entitlement_id": entitlement.id,
        "expected_revision_fingerprint": row.fingerprint,
        "expected_entitlement_fingerprint": entitlement.fingerprint,
    }


async def _post(conn, work):
    async with _scheduler(conn) as db:
        return await process_dividend(db, **work)


async def _rename_with_current_mapping(conn, case):
    renamed, _grant = await rename(conn, case)
    proof = (
        await conn.execute(
            text("""
        SELECT l.provider_verified_at,l.provider_asset_id,a.scope,a.valid_until
        FROM stock_catalog_listings l JOIN stock_catalog_admissions a
          ON a.id=l.provider_admission_id WHERE l.id=:listing
    """),
            {"listing": renamed.id},
        )
    ).one()
    unit = CatalogUnitEvidence.model_validate_json(json.dumps(proof.scope["units"][0]))
    target = CatalogAssetTarget.model_validate(
        {**unit.target.model_dump(), "provider_asset_id": proof.provider_asset_id}
    )
    digest = _mapping_digest(
        target,
        unit,
        proof.scope["provider"]["evidence_digest"],
        proof.provider_verified_at,
        min(proof.valid_until, unit.valid_until),
    )
    await conn.execute(
        text(
            "UPDATE stock_catalog_listings SET provider_evidence_digest=:digest WHERE id=:listing"
        ),
        {"digest": digest, "listing": renamed.id},
    )
    return renamed


async def test_catalog_dividend_correction_replays_original_label_after_rename(scoped_actions):
    conn, case = scoped_actions
    action = _dividend(case)
    first_work = await _derive(conn, case, action)
    first = await _post(conn, first_work)
    assert first.outcome == "original"
    assert await _post(conn, first_work) == first
    assert await cash(conn, case.world.first) == Decimal("1235.56")

    renamed = await _rename_with_current_mapping(conn, case)
    updated = replace(action, symbol=renamed.ticker, rate=Decimal("0.90"))
    second_work = await _derive(conn, case, updated)
    correction = await _post(conn, second_work)
    assert correction.outcome == "applied"
    assert correction.payment_id == first.payment_id
    assert await _post(conn, second_work) == correction
    assert await _post(conn, first_work) == first
    assert await cash(conn, case.world.first) == Decimal("1236.36")
    assert await cash(conn, case.world.sibling) == Decimal("4321.09")
    assert await cash(conn, case.world.closed) == Decimal("55.55")
    labels = (
        await conn.execute(
            text("""
        SELECT symbol,company_name FROM stock_dividend_payments
        UNION ALL SELECT symbol,company_name FROM stock_dividend_decisions
    """)
        )
    ).all()
    assert labels == [(case.listing.ticker, case.listing.company_name)] * 2

    # Spending the virtual cash before a negative correction must hold the
    # original credit and the unaffordable decision.
    await conn.execute(text("UPDATE accounts SET cash=0.01 WHERE id=:id"), {"id": case.world.first})
    lower = await _derive(conn, case, replace(updated, rate=Decimal("0.10")))
    held = await _post(conn, lower)
    assert held.outcome == "held_unaffordable"
    assert await cash(conn, case.world.first) == Decimal("0.01")


@pytest.mark.parametrize(("new_rate", "old_rate", "quantity"), [("2", "1", 4), ("4", "3", 2)])
async def test_catalog_split_service_preserves_basis_and_holds_fractional_lots(
    scoped_actions, new_rate, old_rate, quantity
):
    conn, case = scoped_actions
    split = _dividend(
        case,
        event_type="forward_split",
        rate=None,
        units="pre_split",
        economic_at=case.cutoff,
        new_rate=Decimal(new_rate),
        old_rate=Decimal(old_rate),
    )
    async with _scheduler(conn) as db, db.begin():
        authority, revision = await _ingest(db, case, split)
        assert revision.classification == "supported_forward_split"
        applied = await apply_due_actions(db, case.binding.coin_id, catalog=authority)
        state = await db.get(StockActionState, case.binding.coin_id)
        assert state is not None
        if quantity == 4:
            assert len(applied) == 1
            assert await apply_due_actions(db, case.binding.coin_id, catalog=authority) == applied
            assert state.unit_epoch == 1 and state.quote_not_before == case.cutoff
            assert state.next_blocking_at is None
        else:
            assert not applied
            assert state.health == "reconciling" and state.unit_epoch == 0
    await conn.execute(text("SET CONSTRAINTS stock_catalog_split_movements IMMEDIATE"))
    result = (
        await conn.execute(
            text(
                "SELECT quantity,cost_basis FROM holdings WHERE coin_id=:coin AND portfolio_id=:p"
            ),
            {"coin": case.binding.coin_id, "p": case.world.first},
        )
    ).one()
    assert result == (Decimal(quantity), Decimal("87.65"))
    assert await cash(conn, case.world.first) == Decimal("1234.56")
    assert await cash(conn, case.world.closed) == Decimal("55.55")
    if quantity == 4:
        renamed = await _rename_with_current_mapping(conn, case)
        async with _scheduler(conn) as db, db.begin():
            new_authority, repeated = await _ingest(db, case, replace(split, symbol=renamed.ticker))
            assert repeated.revision_id == revision.revision_id
            assert (
                await apply_due_actions(db, case.binding.coin_id, catalog=new_authority) == applied
            )


async def test_action_services_refuse_unbound_scope_and_unverified_split_time(scoped_actions):
    conn, case = scoped_actions
    split = _dividend(
        case,
        event_type="forward_split",
        rate=None,
        units="pre_split",
        economic_at=case.cutoff + timedelta(minutes=1),
        new_rate=Decimal("2"),
        old_rate=Decimal("1"),
    )
    batch = ActionBatch(records=(split,), observations=(ActionObservation(split),), complete=True)
    async with _scheduler(conn) as db, db.begin():
        authority = await _authority(db, case)
        with pytest.raises(ActionHeld, match="identity_conflict"):
            await apply_due_actions(db, case.binding.coin_id + 1, catalog=authority)
        with pytest.raises(ActionHeld, match="admission_changed"):
            await apply_due_actions(
                db, case.binding.coin_id, catalog=replace(authority, fingerprint="review-changed")
            )
        with pytest.raises(ActionHeld, match="admission"):
            await apply_due_actions(db, case.binding.coin_id, catalog=authority, account="other")
        with pytest.raises(ActionHeld, match="admission"):
            await persist_action_batch(db, batch, None)
        with pytest.raises(ActionHeld, match="admission"):
            await persist_action_batch(db, batch, None, catalog=authority, account="other")
        state = await db.get(StockActionState, case.binding.coin_id)
        assert state is not None
        state.admission_generation = authority.admission_id + 1
        _, result = await _ingest(db, case, split)
        assert (result.classification, result.reason) == ("uncertain", "conflicting")
        assert state.admission_generation == authority.admission_id
        assert state.valid_until is None and state.health == "reconciling"
        with pytest.raises(ActionHeld, match="admission"):
            await derive_dividend_entitlements(
                db, result.event_id, catalog=authority, account="other"
            )
        assert await apply_due_actions(db, case.binding.coin_id, catalog=authority) == ()
    assert await cash(conn, case.world.first) == Decimal("1234.56")
    assert await conn.scalar(text("SELECT count(*) FROM stock_split_applications")) == 0


@pytest.mark.parametrize("effect,check", [("split", 2), ("split", 3), ("dividend", 2)])
async def test_catalog_effect_rolls_back_when_required_monitor_proof_disappears(
    scoped_actions, monkeypatch, effect, check
):
    conn, case = scoped_actions
    action = _dividend(case)
    if effect == "split":
        action = replace(
            action,
            event_type="forward_split",
            rate=None,
            units="pre_split",
            economic_at=case.cutoff,
            new_rate=Decimal("2"),
            old_rate=Decimal("1"),
        )
    async with _scheduler(conn) as db, db.begin():
        authority, revision = await _ingest(db, case, action)

    observed = 0
    genuine = corporate_actions._check_catalog_action

    async def unavailable(db, catalog, *, state=None):
        nonlocal observed
        current = await genuine(db, catalog, state=state)
        if state is not None:
            observed += 1
            if observed == check:
                assert current
                return False
        return current

    monkeypatch.setattr(corporate_actions, "_check_catalog_action", unavailable)
    with pytest.raises(ActionHeld, match="monitor_unavailable"):
        async with _scheduler(conn) as db, db.begin():
            if effect == "split":
                await apply_due_actions(db, case.binding.coin_id, catalog=authority)
            else:
                await derive_dividend_entitlements(db, revision.event_id, catalog=authority)
    assert observed == check
    assert await conn.scalar(text("SELECT count(*) FROM stock_split_applications")) == 0
    assert await conn.scalar(text("SELECT count(*) FROM stock_dividend_entitlements")) == 0
    assert await cash(conn, case.world.first) == Decimal("1234.56")


@pytest.mark.parametrize("split", [False, True])
async def test_verified_action_before_empty_catalog_journal_has_no_effect(scoped_actions, split):
    conn, case = scoped_actions
    async with _scheduler(conn) as db, db.begin():
        authority = await _authority(db, case)
        earlier = max(
            (
                row
                for row in build_sessions(case.now, authority.calendar)
                if row.exchange == case.binding.listing_exchange
                and row.opens_at is not None
                and row.opens_at < case.origin
            ),
            key=lambda row: row.session_date,
        )
        action = _dividend(case, ex_date=earlier.session_date, record_date=earlier.session_date)
        if split:
            action = replace(
                action,
                event_type="forward_split",
                economic_at=earlier.opens_at,
                units="pre_split",
                rate=None,
                new_rate=Decimal("2"),
                old_rate=Decimal("1"),
            )
        assert action.process_date > earlier.session_date
        assert (
            await persist_action_batch(
                db,
                ActionBatch(
                    records=(action,), observations=(ActionObservation(action),), complete=True
                ),
                None,
                account=case.binding.account,
                server=case.binding.server,
                catalog=authority,
            )
            == ()
        )
        assert await db.scalar(text("SELECT count(*) FROM stock_action_events")) == 0
        state = await db.get(StockActionState, case.binding.coin_id)
        assert state is not None and state.health == "current" and state.unit_epoch == 0
        _, uncertain = await _ingest(db, case, replace(action, dates_verified=False))
        assert uncertain.classification == "uncertain"
    assert await cash(conn, case.world.first) == Decimal("1234.56")
    assert await conn.scalar(text("SELECT count(*) FROM stock_split_applications")) == 0
    assert await conn.scalar(text("SELECT count(*) FROM stock_dividend_payments")) == 0


async def test_catalog_operator_reconciles_verified_cancellation_after_rename(
    scoped_actions, monkeypatch
):
    conn, case = scoped_actions
    action = _dividend(case, dates_verified=False)
    async with _scheduler(conn) as db, db.begin():
        _, original = await _ingest(db, case, action)
        assert original.classification == "uncertain"
    renamed = await _rename_with_current_mapping(conn, case)
    async with _scheduler(conn) as db, db.begin():
        authority, current = await _ingest(
            db,
            case,
            replace(action, symbol=renamed.ticker, dates_verified=True, cancelled=True),
            mutation="delete",
        )
        state = await db.get(StockActionState, case.binding.coin_id)
        revision = await db.get(StockActionRevision, current.revision_id)
        assert state is not None and revision is not None
        assert current.event_id == original.event_id and current.classification == "cancelled"
    digest = (
        await conn.execute(
            text("""
        SELECT
          (SELECT encode(sha256(convert_to(coalesce(jsonb_agg(to_jsonb(m) ORDER BY m.sequence),
              '[]'::jsonb)::text,'UTF8')),'hex') FROM stock_ownership_movements m
             WHERE coin_id=:coin) AS ledger,
          (SELECT encode(sha256(convert_to(to_jsonb(c)::text,'UTF8')),'hex')
             FROM stock_data_admissions c WHERE product='calendar') AS calendar,
          (SELECT encode(sha256(convert_to(to_jsonb(a)::text,'UTF8')),'hex')
             FROM (SELECT id,artifact,reviewed_at,valid_until,revoked_at,fields,scope,is_fixture
                   FROM stock_catalog_admissions WHERE id=:generation) a) AS admission,
          (SELECT max(id) FROM stock_action_observations WHERE event_id=:event) AS observation_id
    """),
            {
                "coin": case.binding.coin_id,
                "event": current.event_id,
                "generation": authority.admission_id,
            },
        )
    ).one()
    request = ResolutionRequest(
        coin_id=case.binding.coin_id,
        event_id=current.event_id,
        expected_revision=current.revision_id,
        admission_generation=authority.admission_id,
        epoch=state.epoch,
        decision_key="synthetic-catalog-cancelled",
        decision="confirm_no_effect",
        actor_ref="synthetic-operator",
        evidence={
            "format": 1,
            "unit_epoch": state.unit_epoch,
            "ledger_digest": digest.ledger,
            "revision_fingerprint": revision.fingerprint,
            "held_revision_ids": [original.revision_id, current.revision_id],
            "observation_id": digest.observation_id,
            "account": authority.binding.account,
            "server": authority.binding.server,
            "calendar_generation": authority.calendar.generation,
            "calendar_digest": digest.calendar,
            "admission_digest": digest.admission,
            "review_valid_until": authority.valid_until,
            "security_id": authority.binding.provider_asset_id,
            "cutoff": case.next_open,
            "alias_event_id": None,
        },
    )
    async with conn.begin_nested():
        await conn.execute(text("SET LOCAL ROLE birja_action_operator"))
        async with portfolio_session(conn) as db, db.begin():
            scope = {"account": authority.binding.account, "server": authority.binding.server}
            wrong_issue = request.model_copy(
                update={
                    "evidence": request.evidence.model_copy(update={"security_id": "other-fixture"})
                }
            )
            with pytest.raises(ValueError, match="actions authority unavailable"):
                await reconcile(db, wrong_issue, **scope)

            real_scalar = db.scalar

            async def missing_exchange(statement, *args, **kwargs):
                observed = await real_scalar(statement, *args, **kwargs)
                if statement.column_descriptions[0].get("entity") is StockInstrument:
                    assert observed == case.listing.listing_exchange
                    return None
                return observed

            with monkeypatch.context() as context:
                context.setattr(db, "scalar", missing_exchange)
                with pytest.raises(ValueError, match="revision unavailable"):
                    await reconcile(db, request, **scope)

            first = await reconcile(
                db, request, account=authority.binding.account, server=authority.binding.server
            )
            assert first > 0
            assert (
                await reconcile(
                    db, request, account=authority.binding.account, server=authority.binding.server
                )
                == first
            )
        await conn.execute(text("RESET ROLE"))
    assert await cash(conn, case.world.first) == Decimal("1234.56")
    assert await conn.scalar(text("SELECT count(*) FROM stock_dividend_payments")) == 0
