"""Finite source catch-up; observation completeness never repairs economic holds.

HTTP is outside financial gates. Each instrument commits observations and its
segment marker together; a separate all-or-nothing SQL publication checks every
instrument's epoch before extending the monitoring deadline.
"""

import asyncio
import json
import logging
import secrets
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
from typing import Any, Literal, TypedDict, cast

import httpx
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import SchedulerSettings
from app.models.corporate_action import (
    StockActionEvent,
    StockActionRevision,
    StockActionSource,
    StockActionState,
    StockOwnershipMovement,
)
from app.models.stock_catalog_finance import StockCatalogActionCoverage
from app.models.trade import Holding
from app.services.alpaca_actions import (
    ActionBatch,
    ActionBudget,
    ActionError,
    ActionEvidence,
    fetch_action_snapshot,
    recheck_action_ids,
    replay_action_mutations,
)
from app.services.corporate_actions import (
    _guard,
    apply_due_actions,
    derive_dividend_entitlements,
    persist_action_batch,
)
from app.services.stock_admission import ProductAdmission, evaluate_admission
from app.services.stock_catalog_action_demand import selected_catalog_actions
from app.services.stock_catalog_actions import (
    CatalogActionAuthority,
    catalog_action_candidates,
    load_catalog_action_authority,
    lock_catalog_action_scope,
)
from app.services.stock_ownership import acquire_stock_gate, assert_ownership_consistent
from app.services.stock_quote_rules import CURATED_SYMBOLS, StockMapping, verified_mapping
from app.services.stock_quotes import load_stock_catalog
from app.tasks.scheduler import CycleResult
from app.tasks.stock_scheduler import _RELEASE_LUA, _admissions, reserve_account_attempt

LOCK_KEY = "sim:stock:actions:lock"
WINDOW_KEY = "sim:stock:actions:window"
REPLAY_RESIZE_REASONS = frozenset(
    {"response_limit", "byte_budget", "mutation_budget", "cycle_budget", "replay_timeout"}
)
logger = logging.getLogger(__name__)


class _Scope(TypedDict):
    account: str
    server: str


def _cycle_budget(settings: SchedulerSettings) -> ActionBudget:
    return ActionBudget(
        max_attempts=settings.stock_actions_max_attempts,
        total_seconds=settings.stock_actions_cycle_budget_seconds,
        max_response_bytes=settings.stock_actions_max_response_bytes,
    )


def _allowed(
    evidence: dict[str, ProductAdmission], settings: SchedulerSettings, now: datetime
) -> bool:
    return all(
        evaluate_admission(
            evidence.get(product),
            product,
            purpose,
            now,
            account=settings.stock_data_account,
            server=settings.stock_data_server,
            feed="alpaca-corporate-actions" if product == "actions" else "iex",
            capability=cast(Literal["rest", "replay"] | None, capability),
        ).allowed
        for product, capability in (
            ("actions", "rest"),
            ("actions", "replay"),
            ("calendar", None),
            ("reference", None),
        )
        for purpose in ("collection", "derived", "retention")
    )


async def _clock(db: AsyncSession) -> datetime:
    return cast(datetime, (await db.execute(select(func.clock_timestamp()))).scalar_one())


async def _refresh(
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    http: httpx.AsyncClient,
    settings: SchedulerSettings,
    token: str,
    now: Callable[[], datetime],
    budget: ActionBudget | None = None,
) -> CycleResult:
    baseline = getattr(settings, "stock_actions_coverage_start", None)
    if not isinstance(baseline, datetime) or baseline.tzinfo != UTC:
        raise ActionError("coverage_policy")
    async with sessionmaker() as db:
        original = await _admissions(db)
        mappings = await load_stock_catalog(db)
        until = await _clock(db)
    if baseline > until or not _allowed(original, settings, until):
        raise ActionError("admission")
    if (
        {m.symbol for m in mappings} != CURATED_SYMBOLS
        or len(mappings) != 20
        or not all(verified_mapping(m, until) for m in mappings)
        or len({m.provider_asset_id for m in mappings}) != 20
    ):
        raise ActionError("mapping")
    scope: _Scope = {"account": settings.stock_data_account, "server": settings.stock_data_server}
    policy_key = sha256(
        json.dumps(
            {
                "authority": {
                    k: asdict(v)
                    for k, v in original.items()
                    if k in ("actions", "calendar", "reference")
                },
                "scope": scope,
                "mappings": [asdict(m) for m in mappings],
                "baseline": baseline,
                "segment_days": settings.stock_actions_segment_days,
            },
            default=str,
            sort_keys=True,
        ).encode()
    ).hexdigest()
    budget = budget or _cycle_budget(settings)

    async def lease() -> bool:
        return await redis.get(LOCK_KEY) == token

    async def evidence() -> ProductAdmission | None:
        async with sessionmaker() as db:
            latest = await _admissions(db)
            current = await load_stock_catalog(db)
            checked = await _clock(db)
        if (
            latest != original
            or current != mappings
            or not _allowed(latest, settings, checked)
            or not _allowed(latest, settings, now())
        ):
            raise ActionError("admission_changed")
        return latest["actions"]

    async def guard() -> None:
        budget.remaining()
        await evidence()
        if not await lease():
            raise ActionError("lease")

    # A matching healthy lease can run to its original deadline while evidence
    # is refreshed. Partial or failed reads never extend it.
    checkpoints: dict[int, tuple[int, dict[str, Any], datetime | None]] = {}
    for mapping in mappings:
        await guard()
        async with sessionmaker.begin() as db:
            await acquire_stock_gate(db, mapping.coin_id)
            state = await db.get(StockActionState, mapping.coin_id)
            if state is None:
                state = StockActionState(
                    coin_id=mapping.coin_id,
                    admission_generation=original["actions"].generation,
                    journal_start_at=baseline,
                    complete_from=baseline,
                )
                db.add(state)
                await db.flush()
            if (
                state.journal_start_at is None
                or state.complete_from is None
                or baseline > state.journal_start_at
            ):
                raise ActionError("journal_baseline")
            await assert_ownership_consistent(db, mapping.coin_id)
            stage = state.staged_continuation or {}
            if (
                state.admission_generation != original["actions"].generation
                or stage.get("policy_key") != policy_key
            ):
                stage = {}
            checked = await _clock(db)
            keep_lease = (
                bool(stage)
                and state.health == "current"
                and state.covered_until is not None
                and state.valid_until is not None
                and checked < state.valid_until
                and (state.next_blocking_at is None or checked < state.next_blocking_at)
            )
            if not keep_lease:
                state.health = "reconciling"
                state.valid_until = None
                state.epoch += 1
            state.admission_generation = original["actions"].generation
            checkpoints[mapping.coin_id] = (state.epoch, stage, state.covered_until)
    stages = [stage for _, stage, _ in checkpoints.values()]
    pending_targets = [
        datetime.fromisoformat(stage["target_until"])
        for stage in stages
        if stage.get("target_until")
    ]
    if pending_targets:
        until = min(pending_targets)
    horizon = until.date() + timedelta(days=getattr(settings, "stock_actions_future_days", 90))
    # Choose the least advanced durable segment across all twenty, including
    # interrupted previous commits. Never skip an instrument after a crash.
    starts = [
        date.fromisoformat(stage["next_date"]) if "next_date" in stage else baseline.date()
        for _, stage, _ in checkpoints.values()
    ]
    start = min(starts)
    end = min(
        horizon, start + timedelta(days=getattr(settings, "stock_actions_segment_days", 31) - 1)
    )
    async with sessionmaker() as db:
        known = (
            await db.execute(
                select(StockActionSource.provider_event_id, StockActionEvent.coin_id)
                .join(StockActionEvent, StockActionEvent.id == StockActionSource.event_id)
                .where(
                    StockActionSource.provider == "alpaca",
                    StockActionSource.product == "actions",
                    StockActionEvent.coin_id.in_([mapping.coin_id for mapping in mappings]),
                )
                .order_by(StockActionSource.id)
                .limit(1001)
            )
        ).all()
    if len(known) > 1000:
        raise ActionError("known_id_budget")
    symbol_by_id = {m.coin_id: m.symbol for m in mappings}
    ids = {identity: symbol_by_id[cid] for identity, cid in known}
    tokens = [stage.get("continuation") for stage in stages]
    page_token = tokens[0] if len(set(tokens)) == 1 else None
    rest_complete = start > horizon
    frontiers = [
        datetime.fromisoformat(stage["replay_frontier"])
        if stage.get("replay_frontier")
        else baseline
        for stage in stages
    ]
    since = min(frontiers)
    replay_ends = [
        datetime.fromisoformat(stage["replay_end"]) if stage.get("replay_end") else until
        for stage in stages
    ]
    replay_end = min(until, *replay_ends)

    async def before_request(request: httpx.Request) -> None:
        await guard()
        if not await reserve_account_attempt(redis, settings, original):
            raise ActionError("account_budget")
        await guard()

    http.event_hooks["request"].append(before_request)
    try:
        batches: list[ActionBatch] = []
        snapshot = None
        if not rest_complete:
            snapshot = await fetch_action_snapshot(
                http,
                mappings,
                evidence,
                now,
                budget,
                start=start,
                end=end,
                lease=lease,
                page_token=page_token,
                **scope,
            )
            batches.append(snapshot)
            rest_complete = snapshot.complete and end == horizon
        if ids:
            batches.append(
                await recheck_action_ids(
                    http, mappings, evidence, now, budget, ids=ids, lease=lease, **scope
                )
            )
        replay = await replay_action_mutations(
            http,
            mappings,
            evidence,
            now,
            budget,
            since=since,
            until=replay_end,
            lease=lease,
            **scope,
        )
        batches.append(replay)
    finally:
        http.event_hooks["request"].remove(before_request)
    replay_frontier = replay_end if replay.complete else since
    next_replay_end = min(until, replay_end + (replay_end - since))
    density_limit = False
    if not replay.complete:
        if replay.reason in REPLAY_RESIZE_REASONS:
            next_replay_end = since + (replay_end - since) / 2
            density_limit = next_replay_end <= since
        else:
            next_replay_end = replay_end
    complete = (
        all(batch.complete for batch in batches) and rest_complete and replay_frontier == until
    )
    # Missing-ID evidence has no action row; route it using retained identity.
    id_coin = {identity: cid for identity, cid in known}
    for mapping in mappings:
        await guard()
        async with sessionmaker.begin() as db:
            await acquire_stock_gate(db, mapping.coin_id)
            for batch in batches:
                observations = tuple(
                    o for o in batch.observations if o.action.coin_id == mapping.coin_id
                )
                coverage = tuple(
                    c
                    for c in batch.coverage
                    if c.kind != "known_id"
                    or c.start not in id_coin
                    or id_coin[c.start] == mapping.coin_id
                )
                await persist_action_batch(
                    db,
                    replace(
                        batch,
                        observations=observations,
                        records=tuple(o.action for o in observations),
                        coverage=coverage,
                    ),
                    original["actions"],
                    **scope,
                )
            state = cast(StockActionState, await db.get(StockActionState, mapping.coin_id))
            state.staged_continuation = {
                "policy_key": policy_key,
                "target_until": until.isoformat(),
                "next_date": (
                    (end + timedelta(days=1))
                    if snapshot is not None and snapshot.complete
                    else start
                ).isoformat(),
                "segment_start": start.isoformat(),
                "segment_end": end.isoformat(),
                "until": until.isoformat(),
                "complete": rest_complete,
                "continuation": snapshot.continuation if snapshot is not None else None,
                "replay_frontier": replay_frontier.isoformat(),
                "replay_end": next_replay_end.isoformat(),
                "reason": "replay_density_limit" if density_limit else replay.reason,
            }
            state.cursor = next(
                (o.cursor for b in reversed(batches) for o in reversed(b.observations) if o.cursor),
                replay.continuation or state.cursor,
            )
            await db.flush()
            checkpoints[mapping.coin_id] = (
                state.epoch,
                state.staged_continuation,
                state.covered_until,
            )
            # Permission and lease checked after all awaited ingestion too.
            await guard()
    if not complete:
        return CycleResult("source_error")
    await guard()
    # Lock in deterministic order before the final global health publication.
    async with sessionmaker.begin() as db:
        rows = list(
            (
                await db.execute(
                    select(StockActionState)
                    .where(StockActionState.coin_id.in_(checkpoints))
                    .order_by(StockActionState.coin_id)
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
            ).scalars()
        )
        latest = await _admissions(db)
        checked = await _clock(db)
        if (
            len(rows) != 20
            or latest != original
            or not _allowed(latest, settings, checked)
            or any(
                r.epoch != checkpoints[r.coin_id][0]
                or r.staged_continuation != checkpoints[r.coin_id][1]
                or r.covered_until != checkpoints[r.coin_id][2]
                for r in rows
            )
        ):
            raise ActionError("publication_changed")
        deadline = min(
            until
            + timedelta(seconds=getattr(settings, "stock_actions_health_max_age_seconds", 120)),
            *(
                cast(datetime, a.valid_until)
                for a in latest.values()
                if a.product in ("actions", "calendar", "reference")
            ),
            datetime.fromisoformat(original["calendar"].calendar["review_valid_until"]),
        )
        current = checked < deadline
        for state in rows:
            state.coverage_start = baseline
            state.covered_until = until
            state.health = "current" if current else "reconciling"
            state.checked_at = checked if current else None
            state.valid_until = deadline if current else None
            state.staged_continuation = {
                **cast(dict[str, Any], state.staged_continuation),
                "target_until": None,
                "replay_end": None,
            }
        await db.flush()
        if not current:
            # Persist the completed historical frontier so the next cycle can
            # catch up without granting an order lease for stale evidence.
            await guard()
            return CycleResult("source_error")
        for mapping in mappings:
            state = next(row for row in rows if row.coin_id == mapping.coin_id)
            await _guard(
                db,
                mapping.coin_id,
                original["actions"],
                mapping,
                original["calendar"],
                require_monitor=True,
                expected_epoch=checkpoints[mapping.coin_id][0],
                expected_units=state.unit_epoch,
            )
        await guard()
    for mapping in mappings:
        await guard()
        async with sessionmaker.begin() as db:
            await apply_due_actions(db, mapping.coin_id, **scope)
            event_ids = list(
                (
                    await db.execute(
                        select(StockActionEvent.id)
                        .join(
                            StockActionRevision,
                            StockActionRevision.id == StockActionEvent.current_revision_id,
                        )
                        .where(
                            StockActionEvent.coin_id == mapping.coin_id,
                            StockActionRevision.normalized_terms["event_type"].as_string()
                            == "cash_dividend",
                        )
                        .order_by(StockActionEvent.id)
                        .limit(1001)
                    )
                ).scalars()
            )
            if len(event_ids) > 1000:
                raise ActionError("entitlement_budget")
            for event_id in event_ids:
                await derive_dividend_entitlements(db, event_id, **scope)
            await guard()
    return CycleResult("ok")


@dataclass(frozen=True)
class _CatalogCheckpoint:
    epoch: int
    stage: dict[str, Any]
    covered_until: datetime | None
    snapshot_through: date | None
    proof_key: str


def _catalog_proof_key(authority: CatalogActionAuthority, settings: SchedulerSettings) -> str:
    return sha256(
        json.dumps(
            [
                authority.binding.listing_id,
                authority.fingerprint,
                authority.calendar.generation,
                authority.ticker,
                authority.journal_origin.isoformat(),
                [
                    (alias.symbol, alias.through.isoformat(), alias.valid_until.isoformat())
                    for alias in authority.aliases
                ],
                sorted(authority.ambiguous_symbols),
                settings.stock_actions_future_days,
                settings.stock_actions_segment_days,
            ],
        ).encode()
    ).hexdigest()


async def _prepare_catalog_action(
    db: AsyncSession, authority: CatalogActionAuthority, scope: _Scope, proof_key: str
) -> _CatalogCheckpoint:
    binding = authority.binding
    await lock_catalog_action_scope(db)
    await acquire_stock_gate(db, binding.coin_id)
    checked = await _clock(db)
    if authority != await load_catalog_action_authority(
        db,
        binding.coin_id,
        checked,
        allow_fixture=authority.is_fixture,
        **scope,
    ):
        raise ActionError("admission_changed")
    state = await db.get(StockActionState, binding.coin_id, populate_existing=True)
    if state is None:
        raise ActionError("journal_baseline")
    origin = authority.journal_origin
    if state.journal_start_at is None:
        has_book = await db.scalar(
            select(
                select(Holding.id)
                .where(Holding.coin_id == binding.coin_id, Holding.quantity > 0)
                .exists()
                | select(StockOwnershipMovement.id)
                .where(StockOwnershipMovement.coin_id == binding.coin_id)
                .exists()
            )
        )
        if has_book:
            raise ActionError("journal_baseline")
        state.journal_start_at = state.complete_from = origin
    if (
        state.journal_start_at != origin
        or state.complete_from is None
        or state.complete_from > origin
    ):
        raise ActionError("journal_baseline")
    await assert_ownership_consistent(db, binding.coin_id)
    coverage = await db.get(StockCatalogActionCoverage, binding.coin_id, populate_existing=True)
    same_version = coverage is not None and (
        coverage.catalog_id,
        coverage.admission_id,
        coverage.listing_id,
        coverage.journal_origin,
    ) == (binding.catalog_id, authority.admission_id, binding.listing_id, origin)
    stage = dict(state.staged_continuation or {}) if same_version else {}
    covered_until = None
    snapshot_through = None
    if (
        stage.get("completed_policy") == proof_key
        and coverage is not None
        and coverage.coverage_start == state.coverage_start == origin
        and coverage.covered_until == state.covered_until
        and state.covered_until is not None
        and origin <= state.covered_until <= checked
    ):
        covered_until = state.covered_until
        snapshot_through = date.fromisoformat(stage["snapshot_through"])
    keep_lease = (
        covered_until is not None
        and coverage is not None
        and state.health == "current"
        and state.admission_generation == authority.admission_id
        and state.valid_until is not None
        and checked < state.valid_until <= authority.valid_until
        and (state.next_blocking_at is None or checked < state.next_blocking_at)
        and (state.checked_at, state.valid_until, state.cursor)
        == (coverage.observed_at, coverage.valid_until, coverage.cursor)
    )
    if coverage is None:
        coverage = StockCatalogActionCoverage(
            coin_id=binding.coin_id,
            catalog_id=binding.catalog_id,
            listing_id=binding.listing_id,
            admission_id=authority.admission_id,
            journal_origin=origin,
            observed_at=checked,
        )
        db.add(coverage)
    else:
        coverage.listing_id = binding.listing_id
        coverage.admission_id = authority.admission_id
        if not same_version:
            coverage.coverage_start = coverage.covered_until = None
            coverage.cursor = None
    if not keep_lease:
        if state.health != "reconciling" or not same_version:
            state.epoch += 1
        coverage.observed_at, coverage.valid_until = checked, None
        state.health, state.valid_until = "reconciling", None
    state.admission_generation = authority.admission_id
    state.staged_continuation = stage
    if not same_version:
        state.coverage_start = state.covered_until = None
        state.cursor = None
    return _CatalogCheckpoint(state.epoch, stage, covered_until, snapshot_through, proof_key)


@dataclass(frozen=True)
class _CatalogWindow:
    target: datetime
    start: date
    horizon: date
    replay_at: datetime
    replay_end: datetime
    token: str | None


def _catalog_window(
    stages: tuple[_CatalogCheckpoint, ...],
    baseline: datetime,
    at: datetime,
    key: str,
    settings: SchedulerSettings,
) -> _CatalogWindow:
    progress = stages[0].stage
    same_stage = all(
        stage.stage.get("policy_key") == key
        and all(
            stage.stage.get(field) == progress.get(field)
            for field in (
                "target_until",
                "next_date",
                "replay_at",
                "replay_end",
                "continuation",
            )
        )
        for stage in stages
    )
    if same_stage and progress.get("target_until"):
        target = datetime.fromisoformat(progress["target_until"])
        start = date.fromisoformat(progress["next_date"])
        replay_at = datetime.fromisoformat(progress["replay_at"])
        replay_end = datetime.fromisoformat(progress["replay_end"])
        token = progress.get("continuation")
    else:
        replay_at = min(p.covered_until or baseline for p in stages)
        start = min(
            p.snapshot_through + timedelta(days=1) if p.snapshot_through else baseline.date()
            for p in stages
        )
        target, replay_end, token = at, at, None
    horizon = target.date() + timedelta(days=settings.stock_actions_future_days)
    return _CatalogWindow(target, start, horizon, replay_at, replay_end, token)


async def _catalog_effects(
    db: AsyncSession,
    authority: CatalogActionAuthority,
    scope: _Scope,
) -> None:
    coin_id = authority.binding.coin_id
    await apply_due_actions(db, coin_id, catalog=authority, **scope)
    event_ids = list(
        (
            await db.scalars(
                select(StockActionEvent.id)
                .join(
                    StockActionRevision,
                    StockActionRevision.id == StockActionEvent.current_revision_id,
                )
                .where(
                    StockActionEvent.coin_id == coin_id,
                    StockActionRevision.normalized_terms["event_type"].as_string()
                    == "cash_dividend",
                )
                .order_by(StockActionEvent.id)
                .limit(1001)
            )
        ).all()
    )
    if len(event_ids) > 1000:
        raise ActionError("entitlement_budget")
    for event_id in event_ids:
        await derive_dividend_entitlements(db, event_id, catalog=authority, **scope)


async def _publish_catalog_action_window(
    db: AsyncSession,
    authority: CatalogActionAuthority,
    stage: _CatalogCheckpoint,
    scope: _Scope,
    batches: list[ActionBatch],
    window: _CatalogWindow,
    progress: dict[str, Any],
    complete: bool,
    id_coins: dict[str, int],
    blocked: set[int],
    settings: SchedulerSettings,
) -> None:
    coin_id = authority.binding.coin_id
    await lock_catalog_action_scope(db)
    await acquire_stock_gate(db, coin_id)
    checked = await _clock(db)
    current = await load_catalog_action_authority(
        db,
        coin_id,
        checked,
        allow_fixture=authority.is_fixture,
        **scope,
    )
    state = await db.get(StockActionState, coin_id, populate_existing=True)
    coverage = await db.get(StockCatalogActionCoverage, coin_id, populate_existing=True)
    if current != authority or state is None or coverage is None or state.epoch != stage.epoch:
        raise ActionError("publication_changed")

    for batch in batches:
        observations = tuple(o for o in batch.observations if o.action.coin_id == coin_id)
        fragments = tuple(
            c for c in batch.coverage if c.start not in id_coins or id_coins[c.start] == coin_id
        )
        await persist_action_batch(
            db,
            replace(
                batch,
                observations=observations,
                records=tuple(o.action for o in observations),
                coverage=fragments,
            ),
            None,
            catalog=authority,
            **scope,
        )
    checked = await _clock(db)
    if (
        checked >= authority.valid_until
        or (
            await load_catalog_action_authority(
                db,
                coin_id,
                checked,
                allow_fixture=authority.is_fixture,
                **scope,
            )
        )
        != authority
    ):
        raise ActionError("publication_changed")
    if coin_id in blocked:
        # Re-read the disputed interval rather than advancing beyond it.
        if state.health == "current":
            state.epoch += 1
        state.health = "reconciling"
        state.valid_until = coverage.valid_until = None
        state.cursor = coverage.cursor = None
        state.checked_at = coverage.observed_at = checked
        state.staged_continuation = {"reason": "identity_or_known_id_gap"}
        state.coverage_start = coverage.coverage_start = None
        state.covered_until = coverage.covered_until = None
    elif complete:
        origin = authority.journal_origin
        state.cursor = coverage.cursor = None
        state.checked_at = coverage.observed_at = checked
        state.coverage_start = coverage.coverage_start = origin
        state.covered_until = coverage.covered_until = window.target
        deadline = min(
            authority.valid_until,
            window.target + timedelta(seconds=settings.stock_actions_health_max_age_seconds),
        )
        state.staged_continuation = {
            "completed_policy": stage.proof_key,
            "snapshot_through": window.horizon.isoformat(),
        }
        state.health = "current" if checked < deadline else "reconciling"
        state.valid_until = coverage.valid_until = deadline if checked < deadline else None
        if state.valid_until is not None:
            await db.flush()
            await _catalog_effects(db, authority, scope)
    else:
        state.staged_continuation = {
            **progress,
            **(
                {
                    "completed_policy": stage.proof_key,
                    "snapshot_through": stage.snapshot_through.isoformat(),
                }
                if stage.snapshot_through is not None
                else {}
            ),
        }
        if state.health != "current" or state.valid_until is None or checked >= state.valid_until:
            state.health = "reconciling"
            state.valid_until = coverage.valid_until = None
            state.cursor = coverage.cursor = progress["continuation"]
            state.checked_at = coverage.observed_at = checked


async def _refresh_catalog(
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    http: httpx.AsyncClient,
    settings: SchedulerSettings,
    token: str,
    now: Callable[[], datetime],
    budget: ActionBudget,
    authorities: tuple[CatalogActionAuthority, ...],
) -> CycleResult:
    scope: _Scope = {"account": settings.stock_data_account, "server": settings.stock_data_server}
    policies = [a.policy for a in authorities if a.policy is not None]
    if not policies:
        raise ActionError("admission")
    cap = min(p.requests_per_minute for p in policies)

    async def lease() -> bool:
        return await redis.get(LOCK_KEY) == token

    async def evidence() -> ActionEvidence:
        budget.remaining()
        async with sessionmaker() as db:
            checked = await _clock(db)
            refreshed = tuple(
                [
                    await load_catalog_action_authority(
                        db,
                        a.binding.coin_id,
                        checked,
                        allow_fixture=a.is_fixture,
                        **scope,
                    )
                    for a in authorities
                ]
            )
        return authorities if refreshed == authorities else None

    async def guard() -> None:
        if not await lease():
            raise ActionError("lease")
        if await evidence() is None:
            raise ActionError("admission_changed")

    stages = []
    proof_keys = [_catalog_proof_key(authority, settings) for authority in authorities]
    for authority, proof_key in zip(authorities, proof_keys, strict=True):
        await guard()
        async with sessionmaker.begin() as db:
            stages.append(await _prepare_catalog_action(db, authority, scope, proof_key))
    baseline = min(a.journal_origin for a in authorities)
    policy_key = sha256(
        json.dumps(
            sorted((a.binding.coin_id, key) for a, key in zip(authorities, proof_keys, strict=True))
        ).encode()
    ).hexdigest()
    async with sessionmaker() as db:
        at = await _clock(db)
        known_rows = (
            await db.execute(
                select(StockActionSource.provider_event_id, StockActionEvent.coin_id)
                .join(StockActionEvent, StockActionEvent.id == StockActionSource.event_id)
                .where(
                    StockActionSource.provider == "alpaca",
                    StockActionSource.product == "actions",
                    StockActionEvent.coin_id.in_([a.binding.coin_id for a in authorities]),
                )
                .order_by(StockActionSource.id)
                .limit(1001)
            )
        ).all()
    if len(known_rows) > 1000:
        raise ActionError("known_id_budget")
    window = _catalog_window(tuple(stages), baseline, at, policy_key, settings)
    if any(window.horizon > p.future_through for p in policies):
        raise ActionError("unreviewed_window")
    names = {a.binding.coin_id: a.ticker for a in authorities}
    id_coins = {event_id: coin_id for event_id, coin_id in known_rows}
    ids = {event_id: names[coin_id] for event_id, coin_id in known_rows}
    mappings = tuple(
        StockMapping(
            a.binding.coin_id,
            a.ticker,
            a.binding.provider_asset_id,
            a.journal_origin,
            a.binding.listing_exchange,
        )
        for a in authorities
    )

    async def before_request(request: httpx.Request) -> None:
        await guard()
        async with sessionmaker() as db:
            grants = await _admissions(db)
        if not await reserve_account_attempt(redis, settings, grants, at=now(), cap=cap):
            raise ActionError("account_budget")
        await guard()

    batches: list[ActionBatch] = []
    snapshot = known = None
    next_date, page_token = window.start, window.token
    http.event_hooks["request"].append(before_request)
    try:
        while next_date <= window.horizon and budget.attempts < budget.max_attempts:
            end = min(
                window.horizon, next_date + timedelta(days=settings.stock_actions_segment_days - 1)
            )
            snapshot = await fetch_action_snapshot(
                http,
                mappings,
                evidence,
                now,
                budget,
                start=next_date,
                end=end,
                lease=lease,
                page_token=page_token,
                catalog=authorities,
                **scope,
            )
            batches.append(snapshot)
            page_token = snapshot.continuation
            if not snapshot.complete or snapshot.uncertain_coin_ids:
                break
            next_date = end + timedelta(days=1)
        rest_complete = next_date > window.horizon
        if ids and rest_complete:
            known = await recheck_action_ids(
                http,
                mappings,
                evidence,
                now,
                budget,
                ids=ids,
                lease=lease,
                catalog=authorities,
                **scope,
            )
            batches.append(known)
        replay = None
        if rest_complete and window.replay_at < window.target:
            replay = await replay_action_mutations(
                http,
                mappings,
                evidence,
                now,
                budget,
                since=window.replay_at,
                until=window.replay_end,
                lease=lease,
                catalog=authorities,
                **scope,
            )
            batches.append(replay)
    finally:
        http.event_hooks["request"].remove(before_request)

    frontier, next_replay_end = window.replay_at, window.replay_end
    if replay is not None and replay.complete:
        frontier = window.replay_end
        next_replay_end = min(window.target, frontier + (frontier - window.replay_at))
    elif replay is not None and replay.reason in REPLAY_RESIZE_REASONS:
        next_replay_end = window.replay_at + (window.replay_end - window.replay_at) / 2
    replay_complete = frontier == window.target
    missing = {
        id_coins[c.start]
        for c in (known.coverage if known is not None else ())
        if c.kind == "known_id" and not c.complete and c.start in id_coins
    }
    known_complete = not ids or bool(
        known
        and (
            known.complete
            or missing
            and any(c.kind == "known_id" and c.complete for c in known.coverage)
        )
    )
    blocked = missing | {coin for batch in batches for coin in batch.uncertain_coin_ids}
    expected_partial = {
        "attempt_budget",
        "page_budget",
        "response_limit",
        "byte_budget",
        "mutation_budget",
        "cycle_budget",
        "replay_timeout",
        "missing_or_uncertain",
    }
    if any(not batch.complete and batch.reason not in expected_partial for batch in batches):
        blocked.update(names)
    complete = rest_complete and replay_complete and known_complete
    progress = {
        "policy_key": policy_key,
        "target_until": window.target.isoformat(),
        "next_date": next_date.isoformat(),
        "continuation": page_token,
        "replay_at": frontier.isoformat(),
        "replay_end": next_replay_end.isoformat(),
    }
    for authority, stage in zip(authorities, stages, strict=True):
        await guard()
        async with sessionmaker.begin() as db:
            await _publish_catalog_action_window(
                db,
                authority,
                stage,
                scope,
                batches,
                window,
                progress,
                complete,
                id_coins,
                blocked,
                settings,
            )
    if not complete or blocked:
        return CycleResult("source_error")
    return CycleResult("ok", accepted=len(authorities))


async def run_stock_action_cycle(
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    http: httpx.AsyncClient,
    settings: SchedulerSettings,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    catalog_redis: Redis | None = None,
) -> CycleResult:
    if not getattr(settings, "stock_actions_enabled", False):
        return CycleResult("ok")
    token = secrets.token_hex(16)
    try:
        if not await redis.set(LOCK_KEY, token, nx=True, px=45000):
            return CycleResult("locked")
    except RedisError:
        return CycleResult("lock_error")
    try:
        if not await redis.set(
            WINDOW_KEY,
            token,
            nx=True,
            px=getattr(settings, "stock_actions_poll_interval_seconds", 60) * 1000,
        ):
            return CycleResult("locked")
        async with asyncio.timeout(getattr(settings, "stock_actions_cycle_budget_seconds", 30)):
            scope: _Scope = {
                "account": settings.stock_data_account,
                "server": settings.stock_data_server,
            }
            selected = (
                await selected_catalog_actions(catalog_redis, **scope)
                if catalog_redis is not None
                else None
            )
            async with sessionmaker() as db:
                at = await _clock(db)
                authorities = await catalog_action_candidates(
                    db,
                    at,
                    allow_fixture=settings.env == "test",
                    selected=selected,
                    max_age_seconds=settings.stock_actions_health_max_age_seconds,
                    **scope,
                )
                legacy_approved = _allowed(await _admissions(db), settings, at)
            if not authorities:
                return await _refresh(sessionmaker, redis, http, settings, token, now)
            budget = _cycle_budget(settings)
            original_attempts = budget.max_attempts
            if legacy_approved and original_attempts > 1:
                budget.max_attempts = max(1, original_attempts // 2)
            try:
                catalog_result = await _refresh_catalog(
                    sessionmaker,
                    redis,
                    http,
                    settings,
                    token,
                    now,
                    budget,
                    authorities,
                )
            except ActionError as exc:
                logger.warning("catalog action cycle incomplete: %s", str(exc))
                catalog_result = CycleResult("source_error")
            finally:
                budget.max_attempts = original_attempts
            if legacy_approved:
                legacy_result = await _refresh(
                    sessionmaker, redis, http, settings, token, now, budget
                )
                if legacy_result.status != "ok":
                    return legacy_result
            return catalog_result
    except Exception as exc:
        logger.warning(
            "action cycle failed: %s",
            str(exc) if isinstance(exc, ActionError) else type(exc).__name__,
        )
        return CycleResult("source_error")
    finally:
        try:
            await redis.eval(_RELEASE_LUA, 1, LOCK_KEY, token)
        except RedisError:
            logger.warning("action lock release failed")
