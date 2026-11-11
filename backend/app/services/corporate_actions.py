"""Immutable corporate-action accounting in caller-owned transactions.

Use one READ COMMITTED transaction per instrument; any raised exception requires
rollback of the whole business operation. Provider I/O is forbidden here. Batch
completeness supplies observations, never monitoring authority or permission.
"""

import hashlib
import json
from dataclasses import asdict, dataclass, fields
from datetime import date, datetime
from decimal import Decimal
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.corporate_action import (
    StockActionEvent,
    StockActionObservation,
    StockActionResolution,
    StockActionRevision,
    StockActionSource,
    StockActionState,
    StockOwnershipMovement,
    StockSplitApplication,
)
from app.models.stock import StockDataAdmission
from app.models.trade import Holding
from app.services.alpaca_actions import ActionBatch
from app.services.corporate_action_rules import (
    NormalizedAction,
    SplitOwner,
    classify_action,
    plan_forward_split,
)
from app.services.stock_admission import ProductAdmission, evaluate_admission
from app.services.stock_ownership import (
    StockMovementInput,
    acquire_stock_gate,
    append_stock_movement,
    assert_ownership_consistent,
)
from app.services.stock_quote_rules import utc, verified_mapping
from app.services.stock_quotes import load_stock_catalog


class ActionHeld(ValueError):
    """Fixed safe refusal; never provider text."""


@dataclass(frozen=True)
class PersistedAction:
    event_id: int
    revision_id: int
    classification: str
    reason: str


async def _clock(db: AsyncSession) -> datetime:
    return cast(datetime, (await db.execute(select(func.clock_timestamp()))).scalar_one())


async def _load_admission(db: AsyncSession, product: str) -> ProductAdmission | None:
    columns = [c for c in StockDataAdmission.__table__.columns if c.name != "id"]
    row = (
        (await db.execute(select(*columns).where(StockDataAdmission.product == product)))
        .mappings()
        .one_or_none()
    )
    return ProductAdmission(**row) if row else None


async def _authority(
    db: AsyncSession, expected: ProductAdmission | None = None, *, capability: str = "rest"
) -> ProductAdmission:
    evidence = await _load_admission(db, "actions")
    now = await _clock(db)
    if (
        evidence is None
        or (expected is not None and evidence != expected)
        or not all(
            evaluate_admission(
                evidence,
                "actions",
                purpose,
                now,
                feed="alpaca-corporate-actions",
                capability=capability,
            ).allowed
            for purpose in ("collection", "derived", "retention")
        )
    ):
        raise ActionHeld("admission")
    return evidence


async def _guard(db: AsyncSession, cid: int, evidence: ProductAdmission) -> None:
    """Final SQL statement snapshots ALL permission fields and current DB time.

    Unlike SELECT FOR SHARE this requires no runtime UPDATE on admission. Failure
    aborts the caller's whole operation, including prior flushed journal effects.
    A later revocation prevents subsequent API disclosure/fills by generation.
    """
    permission = exists(
        select(StockDataAdmission.id).where(
            *(getattr(StockDataAdmission, k) == v for k, v in asdict(evidence).items()),
            StockDataAdmission.valid_from <= func.clock_timestamp(),
            StockDataAdmission.valid_until > func.clock_timestamp(),
        )
    )
    changed = (
        await db.execute(
            update(StockActionState)
            .where(
                StockActionState.coin_id == cid,
                permission,
            )
            .values(admission_generation=evidence.generation)
            .returning(StockActionState.coin_id)
        )
    ).scalar_one_or_none()
    if changed is None:
        raise ActionHeld("admission_changed")


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _terms(action: NormalizedAction) -> dict[str, Any]:
    return {
        key: value.isoformat()
        if isinstance(value, (datetime, date))
        else str(value)
        if isinstance(value, Decimal)
        else value
        for key, value in asdict(action).items()
        if key not in ("provider_event_id", "observed_at", "source_event_at")
    }


def _action(
    revision: StockActionRevision, identity: str = "retained-economic-event"
) -> NormalizedAction:
    data = {
        f.name: revision.normalized_terms[f.name]
        for f in fields(NormalizedAction)
        if f.name in revision.normalized_terms
    }
    for key in ("process_date", "declaration_date", "ex_date", "record_date", "payable_date"):
        if data.get(key) is not None:
            data[key] = date.fromisoformat(data[key])
    if data.get("economic_at") is not None:
        data["economic_at"] = datetime.fromisoformat(data["economic_at"])
    for key in ("rate", "new_rate", "old_rate"):
        if data.get(key) is not None:
            data[key] = Decimal(data[key])
    return NormalizedAction(
        provider_event_id=identity,
        observed_at=revision.observed_at,
        source_event_at=revision.source_event_at,
        **data,
    )


async def _state(db: AsyncSession, cid: int, generation: int) -> StockActionState:
    state = (
        await db.execute(
            select(StockActionState)
            .where(StockActionState.coin_id == cid)
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if state is None:
        state = StockActionState(coin_id=cid, admission_generation=generation)
        db.add(state)
        await db.flush()
    return state


async def _hold(db: AsyncSession, state: StockActionState, at: datetime) -> None:
    # No runtime path clears this persistent boundary. Privileged reconciliation
    # and the monitor explicitly prove which immutable reasons are resolved.
    state.epoch += 1
    state.health = "reconciling"
    state.next_blocking_at = min(state.next_blocking_at, at) if state.next_blocking_at else at
    await db.flush()


async def persist_action_batch(
    db: AsyncSession, batch: ActionBatch, authority: ProductAdmission
) -> tuple[PersistedAction, ...]:
    if (
        not isinstance(batch, ActionBatch)
        or len(batch.observations) > 1024
        or len(batch.coverage) > 1024
    ):
        raise ActionHeld("invalid_batch")
    cids = {row.action.coin_id for row in batch.observations}
    missing = []
    for coverage in batch.coverage:
        if (
            coverage.kind == "known_id"
            and coverage.reason == "missing_or_uncertain"
            and coverage.start == coverage.end
        ):
            source = (
                await db.execute(
                    select(StockActionSource).where(
                        StockActionSource.provider == "alpaca",
                        StockActionSource.product == "actions",
                        StockActionSource.provider_event_id == coverage.start,
                    )
                )
            ).scalar_one_or_none()
            if source is None:
                raise ActionHeld("unknown_missing_identity")
            event = cast(StockActionEvent, await db.get(StockActionEvent, source.event_id))
            cids.add(event.coin_id)
            missing.append(source)
    if not cids:
        return ()
    if len(cids) != 1:
        raise ActionHeld("one_instrument_per_transaction")
    cid = next(iter(cids))
    await acquire_stock_gate(db, cid)
    capability = (
        "replay" if any(row.mutation != "snapshot" for row in batch.observations) else "rest"
    )
    evidence = await _authority(db, authority, capability=capability)
    mapping = next((row for row in await load_stock_catalog(db) if row.coin_id == cid), None)
    now = await _clock(db)
    if mapping is None or not verified_mapping(mapping, now):
        raise ActionHeld("mapping")
    state = await _state(db, cid, evidence.generation)
    results = []
    for observation in batch.observations:
        action = observation.action
        if (
            not utc(action.observed_at)
            or action.observed_at > await _clock(db)
            or action.symbol != mapping.symbol
        ):
            raise ActionHeld("invalid_observation")
        source = (
            await db.execute(
                select(StockActionSource).where(
                    StockActionSource.provider == "alpaca",
                    StockActionSource.product == "actions",
                    StockActionSource.provider_event_id == action.provider_event_id,
                )
            )
        ).scalar_one_or_none()
        terms = _terms(action)
        classification = classify_action(action)
        kind, reason = classification.kind, classification.reason
        if source is None:
            candidates = (
                (
                    await db.execute(
                        select(StockActionRevision)
                        .join(StockActionEvent, StockActionEvent.id == StockActionRevision.event_id)
                        .where(
                            StockActionEvent.coin_id == cid,
                            StockActionRevision.id == StockActionEvent.current_revision_id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            # Another ID on the same type/date may be a replacement or alias.
            # Preserve as held separate candidate, never guess economic linkage.
            if any(
                r.normalized_terms.get("event_type") == action.event_type
                and r.normalized_terms.get("ex_date") == terms.get("ex_date")
                for r in candidates
            ):
                kind, reason = "uncertain", "conflicting"
                terms["ingest_hold"] = "suspected_alias"
            event = StockActionEvent(
                coin_id=cid, economic_key=str(uuid4()), first_observed_at=action.observed_at
            )
            db.add(event)
            await db.flush()
            source = StockActionSource(
                event_id=event.id,
                provider="alpaca",
                product="actions",
                provider_event_id=action.provider_event_id,
            )
            db.add(source)
            await db.flush()
        else:
            event = cast(
                StockActionEvent,
                await db.get(StockActionEvent, source.event_id, populate_existing=True),
            )
            if event.coin_id != cid:
                raise ActionHeld("identity_conflict")
        previous = (
            await db.get(StockActionRevision, event.current_revision_id)
            if event.current_revision_id
            else None
        )
        fingerprint = _digest(terms)
        identical = (
            previous is not None
            and {k: v for k, v in previous.normalized_terms.items() if k != "ingest_hold"} == terms
        )
        if not identical:
            applied = (
                await db.execute(
                    select(StockSplitApplication.id).where(
                        StockSplitApplication.economic_event_id == event.id
                    )
                )
            ).scalar_one_or_none()
            latest = (
                await db.execute(
                    select(func.max(StockOwnershipMovement.economic_at)).where(
                        StockOwnershipMovement.coin_id == cid
                    )
                )
            ).scalar_one()
            if applied is not None or (
                action.economic_at is not None
                and latest is not None
                and action.economic_at <= latest
            ):
                terms["ingest_hold"] = (
                    "applied_revision_changed" if applied is not None else "late_effective_event"
                )
                kind, reason = "uncertain", "conflicting"
            old = (
                await db.execute(
                    select(StockActionRevision).where(
                        StockActionRevision.event_id == event.id,
                        StockActionRevision.fingerprint == _digest(terms),
                    )
                )
            ).scalar_one_or_none()
            if old is not None:
                # Old source facts reappearing do not rewind the current pointer.
                terms["ingest_hold"] = "historical_revision_reappeared"
                kind, reason = "uncertain", "conflicting"
            fingerprint = _digest(terms)
            revision = (
                await db.execute(
                    select(StockActionRevision).where(
                        StockActionRevision.event_id == event.id,
                        StockActionRevision.fingerprint == fingerprint,
                    )
                )
            ).scalar_one_or_none()
            if revision is None:
                ordinal = (
                    await db.execute(
                        select(func.max(StockActionRevision.ordinal)).where(
                            StockActionRevision.event_id == event.id
                        )
                    )
                ).scalar_one() or 0
                revision = StockActionRevision(
                    event_id=event.id,
                    source_id=source.id,
                    ordinal=ordinal + 1,
                    fingerprint=fingerprint,
                    mutation_kind=observation.mutation,
                    source_mutation_id=observation.cursor,
                    source_event_at=observation.source_at or action.source_event_at,
                    observed_at=action.observed_at,
                    admission_generation=evidence.generation,
                    normalized_terms=terms,
                    classification=kind,
                    reason=reason,
                    verified_cutoff=action.economic_at
                    if kind == "supported_forward_split"
                    else None,
                    units=action.units,
                )
                db.add(revision)
                await db.flush()
            event.current_revision_id = revision.id
            state.epoch += 1
            if kind not in ("supported_dividend", "supported_forward_split"):
                await _hold(db, state, now)
            elif action.economic_at is not None:
                state.next_blocking_at = (
                    min(state.next_blocking_at, action.economic_at)
                    if state.next_blocking_at
                    else action.economic_at
                )
        else:
            revision = cast(StockActionRevision, previous)
        duplicate = (
            (
                await db.execute(
                    select(StockActionObservation).where(
                        StockActionObservation.source_id == source.id,
                        StockActionObservation.mutation_id == observation.cursor,
                    )
                )
            ).scalar_one_or_none()
            if observation.cursor is not None
            else None
        )
        if duplicate is not None:
            if duplicate.revision_id != revision.id:
                raise ActionHeld("mutation_conflict")
        else:
            db.add(
                StockActionObservation(
                    event_id=event.id,
                    source_id=source.id,
                    revision_id=revision.id,
                    mutation_id=observation.cursor,
                    observed_at=action.observed_at,
                    admission_generation=evidence.generation,
                    source_kind="replay" if observation.mutation != "snapshot" else "rest",
                    cycle_id=str(uuid4()),
                )
            )
        results.append(
            PersistedAction(event.id, revision.id, revision.classification, revision.reason)
        )
    for source in missing:
        missing_event = cast(
            StockActionEvent,
            await db.get(StockActionEvent, source.event_id, populate_existing=True),
        )
        db.add(
            StockActionObservation(
                event_id=missing_event.id,
                source_id=source.id,
                revision_id=missing_event.current_revision_id,
                mutation_id=None,
                observed_at=await _clock(db),
                admission_generation=evidence.generation,
                source_kind="missing_or_uncertain",
                cycle_id=str(uuid4()),
            )
        )
        await _hold(db, state, await _clock(db))
    await db.flush()
    await _guard(db, cid, evidence)
    return tuple(results)


async def apply_due_actions(
    db: AsyncSession, coin_id: int, now: datetime | None = None
) -> tuple[int, ...]:
    """Apply due splits once. Only post-lock database time is authoritative."""
    await acquire_stock_gate(db, coin_id)
    evidence = await _authority(db)
    state, rows = await assert_ownership_consistent(db, coin_id)
    holders = list(
        (
            await db.execute(
                select(Holding)
                .where(Holding.coin_id == coin_id)
                .order_by(Holding.user_id, Holding.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).scalars()
    )
    checked = await _clock(db)
    if (
        state.health != "current"
        or state.valid_until is None
        or checked >= state.valid_until
        or state.admission_generation != evidence.generation
    ):
        await _hold(db, state, checked)
        return ()
    if await persistent_action_holds(db, coin_id):
        await _hold(db, state, checked)
        return ()
    revisions = list(
        (
            await db.execute(
                select(StockActionRevision)
                .join(
                    StockActionEvent, StockActionEvent.current_revision_id == StockActionRevision.id
                )
                .where(
                    StockActionEvent.coin_id == coin_id,
                    StockActionRevision.classification == "supported_forward_split",
                )
                .order_by(StockActionRevision.verified_cutoff, StockActionRevision.id)
            )
        ).scalars()
    )
    result = []
    for revision in revisions:
        existing = (
            await db.execute(
                select(StockSplitApplication).where(
                    StockSplitApplication.economic_event_id == revision.event_id
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            result.append(existing.id)
            continue
        action = _action(revision)
        cutoff = revision.verified_cutoff
        checked = await _clock(db)
        if cutoff is None or cutoff > checked:
            continue
        if (
            state.complete_from is None
            or cutoff < state.complete_from
            or (rows and rows[-1].economic_at >= cutoff)
        ):
            await _hold(db, state, checked)
            continue
        owners = [SplitOwner(h.user_id, h.quantity, h.cost_basis) for h in holders]
        plan = plan_forward_split(action, owners)
        if not plan.allowed:
            await _hold(db, state, checked)
            continue
        await _authority(db, evidence)
        before = [(h.user_id, str(h.quantity), str(h.cost_basis)) for h in holders]
        after = [(h.user_id, str(h.quantity), str(h.total_basis)) for h in plan.owners]
        application = StockSplitApplication(
            coin_id=coin_id,
            economic_event_id=revision.event_id,
            revision_id=revision.id,
            new_rate=format(cast(Decimal, action.new_rate), "f"),
            old_rate=format(cast(Decimal, action.old_rate), "f"),
            cutoff=cutoff,
            prior_unit_epoch=state.unit_epoch,
            new_unit_epoch=state.unit_epoch + 1,
            sequence_boundary=rows[-1].sequence if rows else 0,
            before_digest=_digest(before),
            after_digest=_digest(after),
            processed_at=await _clock(db),
        )
        db.add(application)
        state.unit_epoch += 1
        state.epoch += 1
        state.quote_not_before = cutoff
        await db.flush()
        for original, adjusted in zip(holders, plan.owners, strict=True):
            if original.quantity > 0:
                await append_stock_movement(
                    db,
                    StockMovementInput(
                        original.user_id,
                        coin_id,
                        adjusted.quantity - original.quantity,
                        original.cost_basis,
                        "split:" + str(application.id),
                        application_id=application.id,
                    ),
                )
        state, rows = await assert_ownership_consistent(db, coin_id)
        state.sequence = rows[-1].sequence if rows else 0
        result.append(application.id)
    await db.flush()
    await _guard(db, coin_id, evidence)
    return tuple(result)


async def persistent_action_holds(db: AsyncSession, coin_id: int) -> tuple[str, ...]:
    """Reasons survive a healthy feed; only reviewed resolutions clear them."""
    resolved = select(StockActionResolution.expected_revision).where(
        StockActionResolution.coin_id == coin_id
    )
    held = list(
        (
            await db.execute(
                select(StockActionRevision.reason)
                .join(StockActionEvent, StockActionEvent.id == StockActionRevision.event_id)
                .where(
                    StockActionEvent.coin_id == coin_id,
                    StockActionRevision.classification.not_in(
                        ("supported_dividend", "supported_forward_split")
                    ),
                    StockActionRevision.id.not_in(resolved),
                )
            )
        ).scalars()
    )
    missing = (
        await db.execute(
            select(StockActionObservation.id)
            .join(StockActionEvent, StockActionEvent.id == StockActionObservation.event_id)
            .where(
                StockActionEvent.coin_id == coin_id,
                StockActionObservation.source_kind == "missing_or_uncertain",
                StockActionObservation.revision_id.not_in(resolved),
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if missing is not None:
        held.append("source_gap")
    return tuple(sorted(set(held)))


async def derive_dividend_entitlements(db: AsyncSession, event_id: int) -> tuple[object, ...]:
    return ()
