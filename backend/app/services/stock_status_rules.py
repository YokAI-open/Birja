"""Finite reviewed status boundary. No transport or entitlement is implied."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from app.services.stock_trading_rules import StatusEvidence, lose_status_continuity


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


def normalize_status_batch(
    batch: StatusBatch,
    previous: Mapping[int, StatusEvidence],
    identities: Mapping[int, str],
    *,
    admission_until: datetime,
    now: datetime,
) -> dict[int, StatusEvidence]:
    """Unknown-only baseline; verified finite authority is added by the RED gate."""
    return {
        cid: lose_status_continuity(
            previous.get(cid, StatusEvidence(coin_id=cid, provider_asset_id=asset))
        )
        for cid, asset in identities.items()
    }
