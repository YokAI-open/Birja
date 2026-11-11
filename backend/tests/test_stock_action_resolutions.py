"""Real isolated PostgreSQL authority; synthetic evidence is not provider approval."""

from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

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

CLI_PATH = Path(__file__).resolve().parents[2] / "scripts/stock-actions.py"

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
            "admission_digest": (
                await db.execute(
                    text("""SELECT encode(sha256(convert_to(
              to_jsonb(c)::text,'UTF8')),'hex') FROM stock_data_admissions c
              WHERE product='actions'""")
                )
            ).scalar_one(),
            "calendar_digest": (
                await db.execute(
                    text("""SELECT encode(sha256(convert_to(
              to_jsonb(c)::text,'UTF8')),'hex') FROM stock_data_admissions c
              WHERE product='calendar'""")
                )
            ).scalar_one(),
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


async def test_authority_identical_confirmation_preserves_reviewed_disposition(resolution_case):
    factory, request, _data, action = resolution_case
    async with factory.begin() as db:
        await db.execute(text(CALL), request)
        assert not await persistent_action_holds(db, request["coin"])
        await persist_action_batch(
            db,
            batch(action),
            await _load_admission(db, "actions"),
        )
        assert not await persistent_action_holds(db, request["coin"])


async def test_authority_upgrade_refuses_existing_runtime_operator_membership(
    engine, runtime_roles
):
    from tests.test_stock_migrations import migrate

    await migrate("0011", down=True)
    async with engine.begin() as conn:
        await conn.execute(text("GRANT birja_action_operator TO birja_app"))
    try:
        with pytest.raises(DBAPIError, match="unsafe action operator"):
            await migrate("head")
    finally:
        async with engine.begin() as conn:
            await conn.execute(text("REVOKE birja_action_operator FROM birja_app"))
        await migrate("head")


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
        Evidence.model_validate({**data, "cutoff": "2026-11-12T14:30:00"})


def request_model(request, data):
    from app.services.stock_action_reconciliation import ResolutionRequest

    return ResolutionRequest.model_validate(
        {
            "coin_id": request["coin"],
            "event_id": request["event"],
            "expected_revision": request["revision"],
            "admission_generation": request["generation"],
            "epoch": request["epoch"],
            "decision_key": request["key"],
            "decision": request["decision"],
            "actor_ref": request["actor"],
            "evidence": data,
        }
    )


async def test_private_service_current_and_stored_replay(resolution_case):
    from app.services.stock_action_reconciliation import inspect_actions, reconcile

    factory, request, data, _action = resolution_case
    async with factory.begin() as db:
        rows = await inspect_actions(db, coin_id=request["coin"])
        assert rows[0]["event_id"] == request["event"]
        assert set(rows[0]) == {
            "event_id",
            "coin_id",
            "revision_id",
            "epoch",
            "unit_epoch",
            "classification",
            "health",
        }
        await db.execute(text("SET LOCAL ROLE birja_action_operator"))
        first = await reconcile(db, request_model(request, data), account="birja", server="birja")
        assert (
            await reconcile(db, request_model(request, data), account="birja", server="birja")
            == first
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"coin_id": 0},
        {"coin_id": True},
        {"after": -1},
        {"after": False},
        {"limit": 0},
        {"limit": 101},
        {"event_id": 0},
        {"event_id": True},
    ],
)
async def test_private_inspect_rejects_invalid_pagination(engine, changes):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.services.stock_action_reconciliation import inspect_actions

    async with AsyncSession(engine) as db:
        with pytest.raises(ValueError):
            await inspect_actions(db, **{"coin_id": 1, **changes})


@pytest.mark.parametrize(
    "raw",
    [
        '{"a":1,"a":2}',
        '{"number":NaN}',
        '{"number":Infinity}',
        '"' + ("a" * 32768) + '"',
        "[" * 1500 + "]" * 1500,
    ],
)
def test_private_file_rejects_unbounded_or_ambiguous_json(tmp_path, raw):
    from app.services.stock_action_reconciliation import protected_json

    path = tmp_path / "evidence.json"
    path.write_text(raw)
    path.chmod(0o600)
    with pytest.raises(ValueError):
        protected_json(path)


def test_private_file_owned0600_regular_only(tmp_path):
    from app.services.stock_action_reconciliation import protected_json

    path = tmp_path / "evidence.json"
    path.write_text('{"format":1}')
    path.chmod(0o600)
    assert protected_json(path) == {"format": 1}
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(ValueError):
        protected_json(link)
    path.chmod(0o644)
    with pytest.raises(ValueError):
        protected_json(path)
    with pytest.raises(ValueError):
        protected_json(tmp_path)
    with pytest.raises(ValueError):
        protected_json(__import__("pathlib").Path("relative.json"))


async def test_authority_alias_rejects_different_economics(resolution_case):
    import json

    from app.models.corporate_action import StockActionSource

    factory, request, data, _action = resolution_case
    async with factory.begin() as db:
        current = await db.get(StockActionRevision, request["revision"])
        source = StockActionSource(
            event_id=request["event"],
            provider="alpaca",
            product="actions",
            provider_event_id="synthetic-conflicting-alias",
        )
        db.add(source)
        await db.flush()
        alias = StockActionRevision(
            event_id=request["event"],
            source_id=source.id,
            ordinal=3,
            fingerprint="1" * 64,
            mutation_kind="snapshot",
            observed_at=current.observed_at,
            admission_generation=current.admission_generation,
            normalized_terms={**current.normalized_terms, "rate": "999"},
            classification="supported_dividend",
            reason="none",
        )
        db.add(alias)
        await db.flush()
        data = {
            **data,
            "held_revision_ids": [*data["held_revision_ids"], alias.id],
            "alias_event_id": request["event"],
        }
        await db.execute(text("SET LOCAL ROLE birja_action_operator"))
        with pytest.raises(DBAPIError, match="alias"):
            await db.execute(
                text(CALL),
                {**request, "decision": "link_verified_alias", "evidence": json.dumps(data)},
            )


async def test_authority_uncertain_observation_reinstates_hold(resolution_case):
    from app.services.alpaca_actions import ActionBatch, ActionCoverage

    factory, request, _data, action = resolution_case
    async with factory.begin() as db:
        await db.execute(text(CALL), request)
        await persist_action_batch(
            db,
            ActionBatch(
                coverage=(
                    ActionCoverage(
                        "known_id",
                        action.provider_event_id,
                        action.provider_event_id,
                        False,
                        "missing_or_uncertain",
                    ),
                )
            ),
            await _load_admission(db, "actions"),
        )
        assert await persistent_action_holds(db, request["coin"])


@pytest.mark.parametrize(
    "case",
    [
        "scope",
        "calendar_missing",
        "calendar_expired",
        "generation",
        "revision_missing",
        "event_mismatch",
        "unsupported",
        "cutoff",
    ],
)
async def test_private_service_rejects_invalid_current_facts(resolution_case, case):
    from sqlalchemy import update

    from app.services.stock_action_reconciliation import reconcile

    factory, request, data, _action = resolution_case
    async with factory.begin() as db:
        if case == "scope":
            data = {**data, "account": "different"}
        elif case == "calendar_missing":
            await db.execute(
                delete(StockDataAdmission).where(StockDataAdmission.product == "calendar")
            )
        elif case == "calendar_expired":
            await db.execute(
                update(StockDataAdmission)
                .where(StockDataAdmission.product == "calendar")
                .values(state="revoked")
            )
        elif case == "generation":
            request = {**request, "generation": 99}
        elif case == "revision_missing":
            request = {**request, "revision": 9007199254740990}
        elif case == "event_mismatch":
            request = {**request, "event": 9007199254740990}
        elif case == "unsupported":
            request = {**request, "revision": data["held_revision_ids"][0]}
        else:
            data = {**data, "cutoff": datetime.fromisoformat(data["cutoff"]) + timedelta(minutes=1)}
        with pytest.raises(ValueError):
            await reconcile(db, request_model(request, data), account="birja", server="birja")


async def refreshed_request(db, request, data, action, **changes):
    from sqlalchemy import func, select

    from app.models.corporate_action import StockActionObservation

    current = (
        await persist_action_batch(
            db, batch(action, **changes), await _load_admission(db, "actions")
        )
    )[0]
    revision = await db.get(StockActionRevision, current.revision_id)
    state = await db.get(StockActionState, request["coin"])
    ids = list(
        (
            await db.execute(
                select(StockActionRevision.id)
                .where(StockActionRevision.event_id == request["event"])
                .order_by(StockActionRevision.id)
            )
        ).scalars()
    )
    obs = (await db.execute(select(func.max(StockActionObservation.id)))).scalar_one()
    return (
        {**request, "revision": revision.id, "epoch": state.epoch},
        {
            **data,
            "held_revision_ids": ids,
            "revision_fingerprint": revision.fingerprint,
            "observation_id": obs,
        },
    )


@pytest.mark.parametrize("offset", [0, 1])
async def test_private_service_forward_split_calendar_is_genuine(resolution_case, offset):
    from decimal import Decimal

    from app.services.stock_action_reconciliation import reconcile

    factory, request, data, action = resolution_case
    action = replace(
        action,
        event_type="forward_split",
        currency=None,
        rate=None,
        new_rate=Decimal(2),
        old_rate=Decimal(1),
        units="pre_split",
        economic_at=datetime.fromisoformat(data["cutoff"]) + timedelta(minutes=offset),
    )
    async with factory.begin() as db:
        request, data = await refreshed_request(db, request, data, action)
        if offset:
            with pytest.raises(ValueError, match="unsupported"):
                await reconcile(db, request_model(request, data), account="birja", server="birja")
        else:
            await db.execute(text("SET LOCAL ROLE birja_action_operator"))
            assert (
                await reconcile(db, request_model(request, data), account="birja", server="birja")
                > 0
            )


async def test_private_service_verified_prospective_cancellation(resolution_case):
    from app.services.stock_action_reconciliation import reconcile

    factory, request, data, action = resolution_case
    async with factory.begin() as db:
        request, data = await refreshed_request(
            db, request, data, replace(action, cancelled=True), mutation="delete"
        )
        request = {**request, "decision": "confirm_no_effect"}
        await db.execute(text("SET LOCAL ROLE birja_action_operator"))
        assert (
            await reconcile(db, request_model(request, data), account="birja", server="birja") > 0
        )


def test_private_file_unsafe_parent_invalid_utf8_and_growth(tmp_path, monkeypatch):
    import os

    import app.services.stock_action_reconciliation as service

    path = tmp_path / "evidence.json"
    path.write_bytes(b"\xff")
    path.chmod(0o600)
    with pytest.raises(ValueError, match="invalid evidence"):
        service.protected_json(path)
    tmp_path.chmod(0o777)
    try:
        with pytest.raises(ValueError, match="parent"):
            service.protected_json(path)
    finally:
        tmp_path.chmod(0o700)
    path.write_text("{}")
    monkeypatch.setattr(service.os, "read", lambda *_args: b"x" * 32769)
    with pytest.raises(ValueError, match="bounded"):
        service.protected_json(path)
    monkeypatch.undo()
    monkeypatch.setattr(service.os, "getuid", lambda: os.getgid() + 12345)
    with pytest.raises(ValueError, match="protected"):
        service.protected_json(path)


def test_private_file_refuses_parent_owned_by_other_user(tmp_path, monkeypatch):
    import os
    from pathlib import Path
    from types import SimpleNamespace

    from app.services.stock_action_reconciliation import protected_json

    path = tmp_path / "evidence.json"
    path.write_text("{}")
    path.chmod(0o600)
    original = Path.lstat

    def ownership(entry):
        result = original(entry)
        return (
            SimpleNamespace(st_uid=os.getuid() + 12345, st_mode=result.st_mode)
            if entry == tmp_path
            else result
        )

    monkeypatch.setattr(Path, "lstat", ownership)
    with pytest.raises(ValueError, match="parent"):
        protected_json(path)


async def test_authority_equal_alias_observes_shared_revision(resolution_case):
    import json

    from app.models.corporate_action import StockActionObservation, StockActionSource

    factory, request, data, _action = resolution_case
    async with factory.begin() as db:
        source = StockActionSource(
            event_id=request["event"],
            provider="alpaca",
            product="actions",
            provider_event_id="synthetic-equal-alias",
        )
        db.add(source)
        await db.flush()
        observation = StockActionObservation(
            event_id=request["event"],
            source_id=source.id,
            revision_id=request["revision"],
            observed_at=datetime.now(UTC),
            admission_generation=request["generation"],
            source_kind="rest",
            cycle_id="synthetic-alias",
        )
        db.add(observation)
        await db.flush()
        data = {**data, "observation_id": observation.id, "alias_event_id": request["event"]}
        await db.execute(text("SET LOCAL ROLE birja_action_operator"))
        identity = (
            await db.execute(
                text(CALL),
                {**request, "decision": "link_verified_alias", "evidence": json.dumps(data)},
            )
        ).scalar_one()
        assert identity > 0


@pytest.mark.parametrize("product", ["calendar", "actions"])
async def test_authority_calendar_override_change_during_gate_wait_is_stale(
    resolution_case, product
):
    import asyncio

    from sqlalchemy import update

    from app.services.stock_action_reconciliation import reconcile
    from app.services.stock_ownership import acquire_stock_gate
    from tests.test_corporate_actions import wait_blocked

    factory, request, data, _action = resolution_case
    announced = asyncio.Queue()

    async def operator():
        async with factory.begin() as db:
            await db.execute(text("SET LOCAL ROLE birja_action_operator"))
            await announced.put((await db.execute(text("SELECT pg_backend_pid()"))).scalar_one())
            return await reconcile(
                db, request_model(request, data), account="birja", server="birja"
            )

    async with factory.begin() as locker:
        await acquire_stock_gate(locker, request["coin"])
        job = asyncio.create_task(operator())
        pid = await announced.get()
        await wait_blocked(factory, pid)
        cal = await _load_admission(locker, "calendar")
        values = {
            "calendar": {
                **cal.calendar,
                "overrides": [
                    {
                        "exchange": "XNAS",
                        "date": data["cutoff"][:10],
                        "state": "closed",
                        "source": "https://www.nasdaq.com/market-activity/stock-market-holiday-schedule",
                    }
                ],
            }
        }
        if product == "actions":
            values = {"allowed_fields": []}
        await locker.execute(
            update(StockDataAdmission).where(StockDataAdmission.product == product).values(**values)
        )
    with pytest.raises(DBAPIError):
        await job


async def test_private_cli_rejects_unprotected_ca_before_ssl_load(tmp_path, monkeypatch):
    import argparse
    import importlib.util
    import json

    spec = importlib.util.spec_from_file_location("stock_actions_cli", CLI_PATH)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    ca = tmp_path / "ca.pem"
    ca.write_text("synthetic test CA data")
    ca.chmod(0o644)
    config = tmp_path / "connection.json"
    config.write_text(
        json.dumps(
            {
                "database_url": "postgresql+asyncpg://synthetic:synthetic@localhost/birja_test",
                "ca_file": str(ca),
                "account": "birja",
                "server": "birja",
            }
        )
    )
    config.chmod(0o600)

    def load(**_kwargs):
        raise AssertionError("unsafe CA reached SSL loader")

    monkeypatch.setattr(cli.ssl, "create_default_context", load)
    with pytest.raises(ValueError, match="protected"):
        await cli.run(argparse.Namespace(connection_file=str(config), command="inspect"))


async def test_private_cli_never_prints_success_before_transaction_commit(
    tmp_path, monkeypatch, capsys
):
    import argparse
    import importlib.util
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    spec = importlib.util.spec_from_file_location("stock_actions_commit_cli", CLI_PATH)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    config = {
        "database_url": "postgresql+asyncpg://synthetic:synthetic@localhost/birja_test",
        "ca_file": str(tmp_path / "ca"),
        "account": "birja",
        "server": "birja",
    }
    monkeypatch.setattr(cli, "protected_json", lambda _path: config)
    monkeypatch.setattr(cli, "protected_bytes", lambda _path: b"synthetic CA bytes")
    monkeypatch.setattr(cli.ssl, "create_default_context", lambda **_kwargs: object())
    db = AsyncMock()
    db.execute.return_value = SimpleNamespace(one=lambda: (True, True, ["birja_action_operator"]))
    transaction = AsyncMock()
    transaction.__aenter__.return_value = db
    transaction.__aexit__.side_effect = ValueError("synthetic commit failure")
    engine = SimpleNamespace(dispose=AsyncMock())
    monkeypatch.setattr(cli, "create_async_engine", lambda *_args, **_kwargs: engine)
    monkeypatch.setattr(
        cli,
        "async_sessionmaker",
        lambda *_args, **_kwargs: SimpleNamespace(begin=lambda: transaction),
    )
    monkeypatch.setattr(cli, "inspect_actions", AsyncMock(return_value=[]))
    with pytest.raises(ValueError, match="commit failure"):
        await cli.run(
            argparse.Namespace(
                connection_file=str(tmp_path / "config"),
                command="inspect",
                coin_id=1,
                event_id=None,
                after=0,
                limit=20,
            )
        )
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("product", ["actions", "calendar"])
async def test_private_service_binds_hash_to_the_precise_validated_snapshot(
    resolution_case, monkeypatch, product
):
    from sqlalchemy import update
    import app.services.stock_action_reconciliation as service

    factory, request, data, _action = resolution_case
    async with factory.begin() as db:
        values = {"allowed_fields": []}
        if product == "calendar":
            calendar = await _load_admission(db, "calendar")
            values = {
                "calendar": {
                    **calendar.calendar,
                    "overrides": [
                        {
                            "exchange": "XNAS",
                            "date": data["cutoff"][:10],
                            "state": "closed",
                            "source": "https://www.nasdaq.com/market-activity/stock-market-holiday-schedule",
                        }
                    ],
                }
            }
        savepoint = await db.begin_nested()
        await db.execute(
            update(StockDataAdmission).where(StockDataAdmission.product == product).values(**values)
        )
        later_hash = (
            await db.execute(
                text("""SELECT encode(sha256(convert_to(to_jsonb(c)::text,'UTF8')),'hex')
          FROM stock_data_admissions c WHERE c.product=:product"""),
                {"product": product},
            )
        ).scalar_one()
        await savepoint.rollback()
        original = service._mapping

        async def change_after_validation(session, coin):
            mapping = await original(session, coin)
            await session.execute(
                update(StockDataAdmission)
                .where(StockDataAdmission.product == product)
                .values(**values)
            )
            return mapping

        monkeypatch.setattr(service, "_mapping", change_after_validation)
        field = "admission_digest" if product == "actions" else "calendar_digest"
        data = {**data, field: later_hash}
        with pytest.raises(ValueError):
            await service.reconcile(
                db, request_model(request, data), account="birja", server="birja"
            )
