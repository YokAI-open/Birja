"""Bounded corporate action observations; no financial or database side effects."""

from dataclasses import dataclass

REST_URL = "https://data.alpaca.markets/v1/corporate-actions"
REPLAY_URL = "https://stream.data.alpaca.markets/v1beta1/events/corporate-actions"


@dataclass(frozen=True)
class ActionBatch:
    records: tuple = ()
    observations: tuple = ()
    coverage: tuple = ()
    continuation: str | None = None
    complete: bool = False
    attempt_count: int = 0


class ActionBudget:
    pass


async def fetch_action_snapshot(*args, **kwargs) -> ActionBatch:
    return ActionBatch()


async def recheck_action_ids(*args, **kwargs) -> ActionBatch:
    return ActionBatch()
