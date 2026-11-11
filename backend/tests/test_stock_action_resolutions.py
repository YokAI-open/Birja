"""Real isolated PostgreSQL authority; synthetic evidence is not provider approval."""

from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import delete, text
from sqlalchemy.exc import DBAPIError

from app.models.corporate_action import StockActionResolution, StockActionRevision, StockActionState
from app.models.stock import StockDataAdmission, StockSession
from app.services.corporate_actions import (
    _load_admission,
    persist_action_batch,
    persistent_action_holds,
)
from app.services.stock_sessions import build_sessions
from tests.stock_action_fixtures import ownership as _ownership
from tests.test_corporate_actions import actions as _actions
from tests.test_corporate_actions import batch
from tests.test_stock_action_migrations import runtime_roles as _runtime_roles
from tests.test_stock_sessions import evidence as calendar_evidence

ownership = _ownership
actions = _actions
runtime_roles = _runtime_roles

CALL = """SELECT public.apply_stock_action_resolution(:coin,:event,:revision,:generation,
 :epoch,:key,:decision,encode(sha256(convert_to(CAST(:evidence AS jsonb)::text,'UTF8')),'hex'),
 CAST(:evidence AS jsonb),:actor)"""


@pytest_asyncio.fixture
async def resolution_case(runtime_roles, actions):
    import json

    factory, coin, _user, action, auth = actions
    now = datetime.now(UTC)
    calendar = calendar_evidence(now)
    rows = build_sessions(now, calendar)
    opening = next(r for r in rows if r.exchange == "NASDAQ" and r.opens_at and r.opens_at > now)
    action = replace(
        action,
        ex_date=opening.session_date,
        record_date=opening.session_date,
        payable_date=opening.session_date + timedelta(days=5),
    )
    async with factory.begin() as db:
        db.add(StockDataAdmission(**asdict(calendar)))
        for row in rows:
            db.add(StockSession(**asdict(row)))
        held = await persist_action_batch(db, batch(replace(action, rate=None)), auth)
        current = await persist_action_batch(db, batch(action), auth)
        revision = await db.get(StockActionRevision, current[0].revision_id)
        state = await db.get(StockActionState, coin)
        ledger = (
            await db.execute(
                text("""SELECT encode(sha256(convert_to(
          '[]','UTF8')),'hex')""")
            )
        ).scalar_one()
        obs = (await db.execute(text("SELECT max(id) FROM stock_action_observations"))).scalar_one()
        data = {
            "format": 1,
            "unit_epoch": state.unit_epoch,
            "ledger_digest": ledger,
            "revision_fingerprint": revision.fingerprint,
            "held_revision_ids": [held[0].revision_id, current[0].revision_id],
            "observation_id": obs,
            "account": "birja",
            "server": "birja",
            "calendar_generation": calendar.generation,
            "review_valid_until": (now + timedelta(minutes=15)).isoformat(),
            "security_id": f"synthetic-{coin}",
            "cutoff": opening.opens_at.isoformat(),
            "alias_event_id": None,
        }
        request = dict(
            coin=coin,
            event=current[0].event_id,
            revision=current[0].revision_id,
            generation=auth.generation,
            epoch=state.epoch,
            key="synthetic-reviewed",
            decision="accept_corrected_supported_revision",
            actor="synthetic:operator",
            evidence=json.dumps(data),
        )
    try:
        yield factory, request, data, action
    finally:
        async with factory.begin() as db:
            await db.execute(delete(StockActionResolution))
            await db.execute(delete(StockSession))


async def test_authority_resolves_exact_held_history_without_financial_change(resolution_case):
    factory, request, _data, _action = resolution_case
    async with factory.begin() as db:
        assert await persistent_action_holds(db, request["coin"])
        await db.execute(text("SET LOCAL ROLE birja_action_operator"))
        first = (await db.execute(text(CALL), request)).scalar_one()
        assert (await db.execute(text(CALL), request)).scalar_one() == first
        assert not await persistent_action_holds(db, request["coin"])
        state = await db.get(StockActionState, request["coin"])
        assert state.health == "reconciling" and state.valid_until is None


@pytest.mark.parametrize("role", ["birja_app", "birja_scheduler"])
async def test_authority_runtime_cannot_execute(resolution_case, role):
    factory, request, _data, _action = resolution_case
    async with factory.begin() as db:
        await db.execute(text(f"SET LOCAL ROLE {role}"))
        with pytest.raises(DBAPIError, match="permission denied"):
            await db.execute(text(CALL), request)


@pytest.mark.parametrize(
    "field,value",
    [
        ("unit_epoch", 99),
        ("ledger_digest", "0" * 64),
        ("held_revision_ids", []),
        ("revision_fingerprint", "0" * 64),
        ("observation_id", 0),
        ("account", "other"),
        ("calendar_generation", 99),
        ("review_valid_until", "2000-01-01T00:00:00+00:00"),
        ("security_id", "other"),
        ("cutoff", "2000-01-01T00:00:00+00:00"),
        ("healthy", True),
    ],
)
async def test_authority_rejects_stale_or_arbitrary_evidence(resolution_case, field, value):
    import json

    factory, request, data, _action = resolution_case
    request = {**request, "evidence": json.dumps({**data, field: value})}
    async with factory.begin() as db:
        await db.execute(text("SET LOCAL ROLE birja_action_operator"))
        with pytest.raises(DBAPIError):
            await db.execute(text(CALL), request)


async def test_authority_new_observation_invalidates_old_disposition(resolution_case):
    factory, request, _data, action = resolution_case
    async with factory.begin() as db:
        await db.execute(text(CALL), request)
        assert not await persistent_action_holds(db, request["coin"])
        await persist_action_batch(
            db,
            batch(action),
            await _load_admission(db, "actions"),
        )
        assert await persistent_action_holds(db, request["coin"])


async def test_authority_has_narrow_operator_entrypoint(engine, migrated, runtime_roles):
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                text("""SELECT prosecdef,proconfig,
          NOT has_function_privilege('birja_app',p.oid,'EXECUTE'),
          NOT has_function_privilege('birja_scheduler',p.oid,'EXECUTE'),
          has_function_privilege('birja_action_operator',p.oid,'EXECUTE')
          FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
          WHERE n.nspname='public' AND p.proname='apply_stock_action_resolution'""")
            )
        ).one_or_none()
        assert row is not None, "Reconciliation must have an actual restricted database authority"
        assert row[0] and row[1] == ["search_path=pg_catalog, public"]
        assert all(row[2:])


async def test_private_evidence_rejects_naive_cutoff(resolution_case):
    from app.services.stock_action_reconciliation import Evidence

    _factory, _request, data, _action = resolution_case
    with pytest.raises(ValueError):
        Evidence.model_validate({**data, 'cutoff':'2026-11-12T14:30:00'})
