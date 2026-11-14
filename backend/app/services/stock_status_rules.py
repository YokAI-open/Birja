"""Finite reviewed status boundary. No transport or entitlement is implied."""

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timedelta
from typing import Literal

from app.services.stock_quote_rules import utc
from app.services.stock_trading_rules import (
    MAX_SAFE,
    STATUS_LEASE_SECONDS,
    StatusEvidence,
    lose_status_continuity,
    status_current,
)


@dataclass(frozen=True)
class StatusEvent:
    coin_id: int
    provider_asset_id: str
    state: Literal["normal", "halted", "frozen", "unknown"]
    event_at: datetime
    session_date: date
    sequence: int
    source_ref: str


@dataclass(frozen=True)
class StatusBatch:
    events: tuple[StatusEvent, ...]
    observed_at: datetime
    admission_generation: int
    continuity_generation: int
    baseline_verified: bool = False
    contiguous: bool = False
    complete: bool = False
    end_marker: bool = False
    lost: bool = False
    reconnected: bool = False


def status_batch_within_bounds(batch: StatusBatch) -> bool:
    """Whole-envelope size guard only; this does not establish authority."""
    if (
        not isinstance(batch, StatusBatch)
        or type(batch.events) is not tuple
        or not 0 < len(batch.events) <= 1000
        or not utc(batch.observed_at)
        or any(
            type(value) is not int or not 0 < value <= MAX_SAFE
            for value in (batch.admission_generation, batch.continuity_generation)
        )
        or any(
            type(value) is not bool
            for value in (
                batch.baseline_verified,
                batch.contiguous,
                batch.complete,
                batch.end_marker,
                batch.lost,
                batch.reconnected,
            )
        )
    ):
        return False
    if any(
        not isinstance(event, StatusEvent)
        or not isinstance(event.provider_asset_id, str)
        or len(event.provider_asset_id) > 128
        or not isinstance(event.source_ref, str)
        or len(event.source_ref) > 2048
        or not isinstance(event.state, str)
        or len(event.state) > 32
        or not utc(event.event_at)
        or type(event.session_date) is not date
        or type(event.coin_id) is not int
        or not 0 < event.coin_id < 2**63
        or type(event.sequence) is not int
        or not 0 <= event.sequence <= MAX_SAFE
        for event in batch.events
    ):
        return False
    return len(json.dumps(asdict(batch), default=str, ensure_ascii=False).encode()) <= 1048576


def normalize_status_batch(
    batch: StatusBatch,
    previous: Mapping[int, StatusEvidence],
    identities: Mapping[int, str],
    *,
    admission_until: datetime,
    now: datetime,
) -> dict[int, StatusEvidence]:
    """Only explicit verified baseline/contiguous segments can mint a lease.

    Events are normalized finite transport evidence, not raw Alpaca JSON. No
    provider adapter is implemented. Missing messages/heartbeats are not proof.
    A failed segment invalidates every instrument in its declared bounded scope.
    """
    if (
        not 0 < len(identities) <= 20
        or len(previous) > 20
        or any(
            type(cid) is not int
            or not 0 < cid < 2**63
            or not isinstance(asset, str)
            or not 0 < len(asset) <= 128
            or asset != asset.strip()
            for cid, asset in identities.items()
        )
    ):
        raise ValueError("Invalid bounded status scope")
    initial = {
        cid: previous.get(
            cid,
            StatusEvidence(
                coin_id=cid, provider_asset_id=asset, source_ref="continuity-unavailable"
            ),
        )
        for cid, asset in identities.items()
    }

    def invalidate() -> dict[int, StatusEvidence]:
        return {cid: lose_status_continuity(old) for cid, old in initial.items()}

    if (
        not isinstance(batch, StatusBatch)
        or type(batch.events) is not tuple
        or not 0 < len(batch.events) <= 1000
        or not utc(now)
        or not utc(batch.observed_at)
        or not utc(admission_until)
        or not batch.observed_at
        <= now
        < min(admission_until, batch.observed_at + timedelta(seconds=STATUS_LEASE_SECONDS))
        or any(
            type(value) is not int or not 0 < value <= MAX_SAFE
            for value in (batch.admission_generation, batch.continuity_generation)
        )
        or any(value is not True for value in (batch.contiguous, batch.complete, batch.end_marker))
        or batch.lost is not False
        or batch.reconnected is not False
        or type(batch.baseline_verified) is not bool
    ):
        return invalidate()
    for event in batch.events:
        if (
            not isinstance(event, StatusEvent)
            or type(event.coin_id) is not int
            or event.coin_id not in identities
            or event.provider_asset_id != identities[event.coin_id]
            or event.state not in ("normal", "halted", "frozen", "unknown")
            or not utc(event.event_at)
            or event.event_at > batch.observed_at
            or type(event.session_date) is not date
            or type(event.sequence) is not int
            or not 0 <= event.sequence <= MAX_SAFE
            or not isinstance(event.source_ref, str)
            or not event.source_ref.strip()
            or not 0 < len(event.source_ref) <= 2048
        ):
            return invalidate()
    if not status_batch_within_bounds(batch):
        return invalidate()
    grouped: dict[int, list[StatusEvent]] = {}
    for event in batch.events:
        grouped.setdefault(event.coin_id, []).append(event)
    output: dict[int, StatusEvidence] = {}
    for cid, events in grouped.items():
        old = initial[cid]
        last = events[-1]
        # Retrying exactly the same finite frame preserves, never renews, proof.
        if (
            len(events) == 1
            and status_current(old, now)
            and old.valid_until is not None
            and old.valid_until <= admission_until
            and old.provider_asset_id == last.provider_asset_id
            and old.state == last.state
            and old.event_at == last.event_at
            and old.session_date == last.session_date
            and old.sequence == last.sequence
            and old.observed_at == batch.observed_at
            and old.admission_generation == batch.admission_generation
            and old.continuity_generation == batch.continuity_generation
            and old.source_ref == last.source_ref
        ):
            output[cid] = old
            continue
        baseline = batch.baseline_verified
        valid_start = (
            batch.continuity_generation > old.continuity_generation
            if baseline
            else status_current(old, batch.observed_at)
            and old.provider_asset_id == identities[cid]
            and batch.continuity_generation == old.continuity_generation
            and batch.admission_generation == old.admission_generation
        )
        current = old
        for index, event in enumerate(events):
            if (
                not valid_start
                or (not baseline or index > 0)
                and event.sequence != current.sequence + 1
                or current.event_at is not None
                and (
                    event.event_at < current.event_at
                    or current.state in ("halted", "frozen")
                    and event.state == "normal"
                    and event.event_at == current.event_at
                )
                or event.state == "unknown"
            ):
                current = lose_status_continuity(
                    replace(
                        current,
                        continuity_generation=max(
                            current.continuity_generation, batch.continuity_generation
                        ),
                        event_at=max(current.event_at, event.event_at)
                        if current.event_at is not None
                        else event.event_at,
                        observed_at=batch.observed_at,
                        source_ref=event.source_ref,
                    )
                )
                break
            current = StatusEvidence(
                cid,
                identities[cid],
                event.state,
                event.event_at,
                batch.observed_at,
                event.session_date,
                batch.admission_generation,
                batch.continuity_generation,
                event.sequence,
                min(admission_until, batch.observed_at + timedelta(seconds=60)),
                True,
                True,
                "alpaca",
                event.source_ref,
            )
        output[cid] = current
    return output
