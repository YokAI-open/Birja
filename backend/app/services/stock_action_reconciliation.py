"""Private typed reconciliation. The database function owns final authority."""

import json
import os
import stat
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.corporate_action_rules import classify_action, dividend_cutoff
from app.services.corporate_actions import _action, _authority, _load_admission, _mapping
from app.services.stock_admission import evaluate_admission
from app.services.stock_sessions import build_sessions

SafeId = Annotated[StrictInt, Field(gt=0, le=9007199254740991)]
ZeroId = Annotated[StrictInt, Field(ge=0, le=9007199254740991)]
Digest = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]

LEDGER_SQL = """SELECT encode(sha256(convert_to(coalesce(
 jsonb_agg(to_jsonb(m) ORDER BY m.sequence),'[]'::jsonb)::text,'UTF8')),'hex')
 FROM public.stock_ownership_movements m WHERE m.coin_id=:coin"""


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    format: Literal[1]
    unit_epoch: ZeroId
    ledger_digest: Digest
    revision_fingerprint: Digest
    held_revision_ids: Annotated[list[SafeId], Field(min_length=1, max_length=128)]
    observation_id: ZeroId
    account: Annotated[StrictStr, Field(min_length=1, max_length=256)]
    server: Annotated[StrictStr, Field(min_length=1, max_length=256)]
    calendar_generation: SafeId
    review_valid_until: datetime
    security_id: Annotated[StrictStr, Field(min_length=1, max_length=128)]
    cutoff: datetime
    alias_event_id: SafeId | None

    @field_validator("cutoff", "review_valid_until")
    @classmethod
    def aware_utc(cls, value: datetime) -> datetime:
        if value.utcoffset() != timedelta(0):
            raise ValueError("UTC timestamp required")
        return value


class ResolutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    coin_id: SafeId
    event_id: SafeId
    expected_revision: SafeId
    admission_generation: SafeId
    epoch: SafeId
    decision_key: Annotated[StrictStr, Field(min_length=1, max_length=256)]
    decision: Literal[
        "confirm_no_effect", "accept_corrected_supported_revision", "link_verified_alias"
    ]
    actor_ref: Annotated[StrictStr, Field(min_length=1, max_length=256)]
    evidence: Evidence


def protected_json(path: Path) -> object:
    """Read one bounded owned regular0600 file without following symlinks."""
    if not path.is_absolute() or path != path.resolve():
        raise ValueError("protected file required")
    for parent in path.parents:
        entry = parent.lstat()
        if not stat.S_ISDIR(entry.st_mode) or entry.st_uid not in (0, os.getuid()):
            raise ValueError("protected parent required")
        if entry.st_mode & 0o022 and not (
            parent == Path("/tmp") and entry.st_mode & stat.S_ISVTX  # noqa: S108
        ):
            raise ValueError("protected parent required")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        entry = os.fstat(descriptor)
        if (
            not stat.S_ISREG(entry.st_mode)
            or entry.st_uid != os.getuid()
            or stat.S_IMODE(entry.st_mode) != 0o600
            or entry.st_size > 32768
        ):
            raise ValueError("protected file required")
        raw = os.read(descriptor, 32769)
        if len(raw) > 32768:
            raise ValueError("bounded file required")
    finally:
        os.close(descriptor)

    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate field")
            result[key] = value
        return result

    def invalid(_value: str) -> None:
        raise ValueError("nonfinite value")

    try:
        value = json.loads(
            raw, object_pairs_hook=unique, parse_constant=invalid, parse_float=invalid
        )
        pending = [(value, 0)]
        while pending:
            item, depth = pending.pop()
            if depth > 16:
                raise ValueError("evidence depth exceeded")
            if isinstance(item, dict):
                pending.extend((child, depth + 1) for child in item.values())
            elif isinstance(item, list):
                pending.extend((child, depth + 1) for child in item)
        return value
    except (RecursionError, UnicodeError) as exc:
        raise ValueError("invalid evidence") from exc


async def inspect_actions(
    db: AsyncSession, *, coin_id: int, event_id: int | None = None, after: int = 0, limit: int = 20
) -> list[dict[str, object]]:
    if type(coin_id) is not int or not 0 < coin_id <= 9007199254740991:
        raise ValueError("invalid coin")
    if type(after) is not int or after < 0 or type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("invalid pagination")
    if event_id is not None and (type(event_id) is not int or event_id <= 0):
        raise ValueError("invalid event")
    rows = (
        await db.execute(
            text("""SELECT e.id AS event_id,e.coin_id,e.current_revision_id AS revision_id,
              r.classification,r.reason,s.epoch,s.unit_epoch,s.health
              FROM public.stock_action_events e
              JOIN public.stock_action_revisions r ON r.id=e.current_revision_id
              JOIN public.stock_action_state s ON s.coin_id=e.coin_id
              WHERE e.coin_id=:coin AND e.id>:after
              AND (CAST(:event AS bigint) IS NULL OR e.id=:event)
              ORDER BY e.id LIMIT :limit"""),
            {"coin": coin_id, "event": event_id, "after": after, "limit": limit},
        )
    ).mappings()
    # Reasons/classifications are bounded constants in the service, but the DB
    # text is never trusted for terminal rendering. Emit only an allowlist.
    kinds = {
        "supported_dividend",
        "supported_forward_split",
        "cancelled",
        "uncertain",
        "unsupported",
    }
    return [
        {
            **{
                key: row[key]
                for key in ("event_id", "coin_id", "revision_id", "epoch", "unit_epoch")
            },
            "classification": row["classification"]
            if row["classification"] in kinds
            else "uncertain",
            "health": row["health"]
            if row["health"] in ("unknown", "reconciling", "current")
            else "unknown",
        }
        for row in rows
    ]


async def reconcile(
    db: AsyncSession, request: ResolutionRequest, *, account: str, server: str
) -> int:
    """Validate configured scope and genuine rules; SQL rechecks after waits.

    Caller owns the transaction. No financial writes or commits occur here.
    """
    from app.models.corporate_action import StockActionRevision

    evidence = request.evidence
    if (evidence.account, evidence.server) != (account, server):
        raise ValueError("configured scope mismatch")
    # Stored replay is handled first by SQL, including exact-payload conflict.
    # New decisions always require fresh independent product/calendar rights.
    stored = (
        await db.execute(
            text("""SELECT id FROM public.stock_action_resolutions
      WHERE coin_id=:coin AND decision_key=:key"""),
            {"coin": request.coin_id, "key": request.decision_key},
        )
    ).scalar_one_or_none()
    if stored is None:
        auth = await _authority(db, account=account, server=server)
        calendar = await _load_admission(db, "calendar")
        now = (await db.execute(text("SELECT clock_timestamp()"))).scalar_one()
        if calendar is None or not all(
            evaluate_admission(
                calendar, "calendar", purpose, now, account=account, server=server
            ).allowed
            for purpose in ("collection", "derived")
        ):
            raise ValueError("calendar authority unavailable")
        if auth.generation != request.admission_generation:
            raise ValueError("admission changed")
        revision = await db.get(StockActionRevision, request.expected_revision)
        if revision is None or revision.event_id != request.event_id:
            raise ValueError("revision unavailable")
        mapping = await _mapping(db, request.coin_id)
        action = _action(revision)
        if request.decision != "confirm_no_effect":
            classified = classify_action(action)
            cutoff = dividend_cutoff(
                action, mapping.listing_exchange, now, calendar, account=account, server=server
            )
            effective_cutoff = (
                action.economic_at
                if classified.kind == "supported_forward_split"
                and any(
                    row.exchange == mapping.listing_exchange
                    and row.session_date == action.ex_date
                    and row.opens_at == action.economic_at
                    for row in build_sessions(now, calendar, account=account, server=server)
                )
                else cutoff.cutoff
                if cutoff
                else None
            )
            if (
                classified.kind not in ("supported_dividend", "supported_forward_split")
                or effective_cutoff is None
            ):
                raise ValueError("unsupported reconciliation")
            if effective_cutoff != evidence.cutoff:
                raise ValueError("calendar cutoff mismatch")
    payload = evidence.model_dump_json()
    result = await db.execute(
        text("""SELECT public.apply_stock_action_resolution(:coin,:event,:revision,
        :generation,:epoch,:key,:decision,
        encode(sha256(convert_to(CAST(:evidence AS jsonb)::text,'UTF8')),'hex'),
        CAST(:evidence AS jsonb),:actor)"""),
        {
            "coin": request.coin_id,
            "event": request.event_id,
            "revision": request.expected_revision,
            "generation": request.admission_generation,
            "epoch": request.epoch,
            "key": request.decision_key,
            "decision": request.decision,
            "evidence": payload,
            "actor": request.actor_ref,
        },
    )
    return int(result.scalar_one())
