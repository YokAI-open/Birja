"""Read-only interpretation of retained effects, never financial authority.

One immutable closure policy explains omitted effects without an ever-growing
future-event by deleted-portfolio skip ledger. Normal APIs must not expose this
internal retained-record inspection; runtime financial SQL still rechecks active
state after its locks. An ``active`` result is NOT permission to apply anything.
"""

import re
from typing import Literal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

LifecycleDisposition = Literal["active", "recorded_before_closure", "not_applied_portfolio_closed"]


class LifecycleEvidenceUnavailable(ValueError):
    def __init__(self) -> None:
        super().__init__("Lifecycle evidence is unavailable.")


async def lifecycle_effect_disposition(
    db: AsyncSession,
    *,
    portfolio_id: int,
    event_id: int,
    revision_fingerprint: str,
    entitlement_id: int | None = None,
    payment_id: int | None = None,
) -> LifecycleDisposition:
    """Interpret one retained cause/revision without writes or provider calls.

    Known original/decision rows remain recorded, including held decisions. A later
    revision, earned-but-unpaid entitlement or unrecorded hold is excluded by the
    terminal policy. Nothing here cancels an entitlement or appends History.
    """
    ids = (portfolio_id, event_id, entitlement_id if entitlement_id is not None else payment_id)
    if (
        any(type(value) is not int or not 0 < value <= 9223372036854775807 for value in ids)
        or (entitlement_id is None) == (payment_id is None)
        or type(revision_fingerprint) is not str
        or re.fullmatch(r"[0-9a-f]{64}", revision_fingerprint) is None
    ):
        raise LifecycleEvidenceUnavailable()
    # A single statement snapshot ties immutable causes to the exact root and
    # revision. It does not lock or authorize a financial write.
    row = (
        (
            await db.execute(
                text("""WITH requested AS (SELECT CAST(:entitlement AS bigint) eid,
        CAST(:payment AS bigint) pid)
      SELECT a.closed_at,lc.closed_at AS lifecycle_at,
      lc.policy_version,lc.user_id=a.user_id AS same_owner,
      (lc.provenance='retained_boundary' AND lc.confirmation_name IS NULL AND lc.intent_id IS NULL)
       OR (lc.provenance='owner_confirmation' AND lc.confirmation_name=a.name AND EXISTS(
        SELECT FROM portfolio_closure_intents i WHERE i.id=lc.intent_id
        AND (i.portfolio_id,i.user_id)=(a.id,a.user_id) AND i.outcome='closed'
        AND i.policy_version=lc.policy_version AND i.confirmation_name=lc.confirmation_name
        AND i.recorded_at=lc.closed_at)) AS coherent_provenance,
      EXISTS(SELECT FROM stock_dividend_payments p WHERE p.portfolio_id=a.id
        AND p.user_id=a.user_id AND p.event_id=:event AND p.revision_fingerprint=:revision
        AND (q.eid IS NULL OR p.entitlement_id=q.eid)
        AND (q.pid IS NULL OR p.id=q.pid) AND p.recorded_at<=a.closed_at)
      OR EXISTS(SELECT FROM stock_dividend_decisions d WHERE d.portfolio_id=a.id
        AND d.user_id=a.user_id AND d.event_id=:event AND d.revision_fingerprint=:revision
        AND (q.eid IS NULL OR d.entitlement_id=q.eid)
        AND (q.pid IS NULL OR d.payment_id=q.pid) AND d.recorded_at<=a.closed_at)
      AS recorded
      FROM accounts a CROSS JOIN requested q
      LEFT JOIN portfolio_lifecycle_closures lc ON lc.portfolio_id=a.id
      JOIN stock_action_revisions r ON r.event_id=:event AND r.fingerprint=:revision
      WHERE a.id=:portfolio AND (
       (q.eid IS NOT NULL AND EXISTS(SELECT FROM stock_dividend_entitlements e
        WHERE e.id=q.eid AND (e.portfolio_id,e.user_id,e.event_id)=(a.id,a.user_id,:event)))
       OR (q.pid IS NOT NULL AND EXISTS(SELECT FROM stock_dividend_payments p
        WHERE p.id=q.pid AND (p.portfolio_id,p.user_id,p.event_id)=(a.id,a.user_id,:event))))"""),
                {
                    "portfolio": portfolio_id,
                    "event": event_id,
                    "revision": revision_fingerprint,
                    "entitlement": entitlement_id,
                    "payment": payment_id,
                },
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise LifecycleEvidenceUnavailable()
    if row["closed_at"] is None:
        if row["lifecycle_at"] is not None:
            raise LifecycleEvidenceUnavailable()
        return "active"
    if (
        row["closed_at"] != row["lifecycle_at"]
        or row["policy_version"] != "freeze_at_closure_v1"
        or row["same_owner"] is not True
        or row["coherent_provenance"] is not True
    ):
        raise LifecycleEvidenceUnavailable()
    return "recorded_before_closure" if row["recorded"] else "not_applied_portfolio_closed"
