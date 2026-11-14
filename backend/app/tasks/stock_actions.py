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
from dataclasses import asdict, replace
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
)
from app.services.alpaca_actions import (
    ActionBatch,
    ActionBudget,
    ActionError,
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
from app.services.stock_ownership import acquire_stock_gate, assert_ownership_consistent
from app.services.stock_quote_rules import CURATED_SYMBOLS, verified_mapping
from app.services.stock_quotes import load_stock_catalog
from app.tasks.scheduler import CycleResult
from app.tasks.stock_scheduler import _RELEASE_LUA, _admissions, reserve_account_attempt

LOCK_KEY = "sim:stock:actions:lock"
WINDOW_KEY = "sim:stock:actions:window"
logger = logging.getLogger(__name__)


class _Scope(TypedDict):
    account: str
    server: str


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
    budget = ActionBudget(
        max_attempts=getattr(settings, "stock_actions_max_attempts", 8),
        total_seconds=getattr(settings, "stock_actions_cycle_budget_seconds", 30),
        max_response_bytes=getattr(settings, "stock_actions_max_response_bytes", 262144),
    )

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

    # Starting work invalidates the preceding lease. Partial committed segments
    # remain resumable, but no cycle can revive its previous healthy deadline.
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
    if start > horizon:
        start = horizon + timedelta(days=1) if pending_targets else until.date()
    end = min(
        horizon, start + timedelta(days=getattr(settings, "stock_actions_segment_days", 31) - 1)
    )
    async with sessionmaker() as db:
        known = (
            await db.execute(
                select(StockActionSource.provider_event_id, StockActionEvent.coin_id)
                .join(StockActionEvent, StockActionEvent.id == StockActionSource.event_id)
                .where(
                    StockActionSource.provider == "alpaca", StockActionSource.product == "actions"
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
    next_replay_end = until
    density_limit = False
    if not replay.complete:
        if replay.reason in ("response_limit", "byte_budget", "mutation_budget", "cycle_budget"):
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
            if complete:
                state.coverage_start = baseline
                state.covered_until = until
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
            or any(r.epoch != checkpoints[r.coin_id][0] or r.covered_until != until for r in rows)
        ):
            raise ActionError("publication_changed")
        deadline = min(
            checked
            + timedelta(seconds=getattr(settings, "stock_actions_health_max_age_seconds", 120)),
            *(
                cast(datetime, a.valid_until)
                for a in latest.values()
                if a.product in ("actions", "calendar", "reference")
            ),
            datetime.fromisoformat(original["calendar"].calendar["review_valid_until"]),
        )
        for state in rows:
            state.health = "current"
            state.checked_at = checked
            state.valid_until = deadline
            state.staged_continuation = {
                **cast(dict[str, Any], state.staged_continuation),
                "target_until": None,
                "replay_end": None,
            }
        await db.flush()
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


async def run_stock_action_cycle(
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    http: httpx.AsyncClient,
    settings: SchedulerSettings,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
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
            return await _refresh(sessionmaker, redis, http, settings, token, now)
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
