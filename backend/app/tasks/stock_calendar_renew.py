"""Install a freshly reviewed stock calendar and its derived sessions atomically.

Inspect the prior digest and review a mode-0600 packet with the exact bytes
of both independently checked official source records before applying it.
The operator attests the retrieval, schedule comparison and review timestamps
in the packet. This command makes no exchange requests or review attestations.
"""

import argparse
import asyncio
import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass, fields, replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from pydantic import AwareDatetime, Field, TypeAdapter
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db.connection import database_connect_args
from app.db.portfolio_migrate import require_source
from app.models.stock import StockDataAdmission
from app.services.stock_admission import ProductAdmission, evaluate_admission
from app.services.stock_catalog_classification import SHA256, CatalogModel
from app.services.stock_catalog_provider import _reject_constant, _reject_duplicates
from app.services.stock_catalog_publish import CatalogPublishError, _lock_catalog
from app.services.stock_quote_rules import utc
from app.services.stock_sessions import EXCHANGES, build_sessions, persist_sessions, session_at
from app.tasks.stock_catalog_enroll import _private_file
from app.tasks.stock_catalog_import import _check_account, _check_connection, _database_settings

_MAX_PACKET_BYTES = 64 * 1024
_MAX_EVIDENCE_BYTES = 4 * 1024 * 1024
_OFFICIAL_URLS = {
    "XNYS": "https://www.nyse.com/trade/hours-calendars",
    "XNAS": "https://www.nasdaq.com/market-activity/stock-market-holiday-schedule",
}
_CALENDAR_FIELDS = {
    "exchanges",
    "version",
    "sources",
    "review_valid_until",
    "coverage_start",
    "coverage_end",
    "overrides",
}
_ADMISSION_FIELDS = {field.name for field in fields(ProductAdmission)}
_ADMISSION = TypeAdapter(ProductAdmission)


class _OfficialCheck(CatalogModel):
    exchange: Literal["XNYS", "XNAS"]
    url: str
    checked_at: AwareDatetime
    sha256: str = Field(pattern=SHA256)
    reference: str = Field(min_length=8, max_length=256)


class _Packet(CatalogModel):
    version: Literal[1]
    expected_generation: int = Field(ge=0, lt=2**63 - 1)
    expected_previous_sha256: str | None = Field(pattern=SHA256)
    review_kind: Literal["unchanged_schedule", "updated_schedule"]
    official_checks: tuple[_OfficialCheck, _OfficialCheck]
    admission: dict[str, Any]


@dataclass(frozen=True, slots=True, repr=False)
class _Review:
    packet: _Packet
    digest: str
    candidate: ProductAdmission


def _json_time(value: object) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError("Unexpected calendar value")


def _previous_digest(previous: ProductAdmission | None) -> str | None:
    if previous is None:
        return None
    data = json.dumps(asdict(previous), sort_keys=True, separators=(",", ":"), default=_json_time)
    return hashlib.sha256(data.encode()).hexdigest()


def _read_review(packet: Path, nyse: Path, nasdaq: Path) -> _Review:
    raw = _private_file(packet, _MAX_PACKET_BYTES)
    decoded = json.loads(raw, object_pairs_hook=_reject_duplicates, parse_constant=_reject_constant)
    if not isinstance(decoded, dict):
        raise CatalogPublishError("Expected a calendar review object")
    review = _Packet.model_validate_json(raw)
    if {check.exchange for check in review.official_checks} != set(_OFFICIAL_URLS):
        raise CatalogPublishError("Both official exchange source checks are required")
    paths = {"XNYS": nyse, "XNAS": nasdaq}
    for check in review.official_checks:
        body = _private_file(paths[check.exchange], _MAX_EVIDENCE_BYTES)
        if (
            not body
            or check.url != _OFFICIAL_URLS[check.exchange]
            or check.sha256 != hashlib.sha256(body).hexdigest()
            or check.reference != check.reference.strip()
            or not check.reference.isprintable()
        ):
            raise CatalogPublishError("Official check does not match the reviewed source evidence")
    if set(review.admission) != _ADMISSION_FIELDS:
        raise CatalogPublishError("Calendar admission fields do not match operator contract")
    candidate = _ADMISSION.validate_json(json.dumps(review.admission), strict=True)
    return _Review(review, hashlib.sha256(raw).hexdigest(), candidate)


def _overrides(candidate: ProductAdmission, start: str, end: str) -> list[dict[str, Any]]:
    return sorted(
        [row for row in candidate.calendar["overrides"] if start <= row["date"] <= end],
        key=lambda row: (row["exchange"], row["date"]),
    )


def _prepare(
    review: _Review, previous: ProductAdmission | None, now: datetime
) -> tuple[ProductAdmission, str, str]:
    candidate, packet = review.candidate, review.packet
    generation = previous.generation if previous is not None else 0
    if (
        generation != packet.expected_generation
        or _previous_digest(previous) != packet.expected_previous_sha256
        or candidate.generation != generation + 1
    ):
        raise CatalogPublishError("The prior calendar authority changed after packet preparation")
    if candidate.product != "calendar" or candidate.state != "approved":
        raise CatalogPublishError("Expected a reviewed calendar authority")
    account, server = candidate.scope.get("account"), candidate.scope.get("server")
    if not isinstance(account, str) or not isinstance(server, str):
        raise CatalogPublishError("Explicit calendar account and server are required")
    _check_account(account, server)
    if (
        previous is not None
        and previous.state == "approved"
        and (previous.scope.get("account"), previous.scope.get("server")) != (account, server)
    ):
        raise CatalogPublishError("Calendar renewal cannot change an approved account or server")

    reviewed_at = candidate.reviewed_at
    calendar = candidate.calendar
    if reviewed_at is None or not utc(reviewed_at) or set(calendar) != _CALENDAR_FIELDS:
        raise CatalogPublishError("Expected dated calendar review and schedule fields")
    previous_review = previous.reviewed_at if previous is not None else None
    if previous_review is not None and (
        reviewed_at <= previous_review
        or any(check.checked_at <= previous_review for check in packet.official_checks)
    ):
        raise CatalogPublishError("A renewal requires fresh official checks after the prior review")

    if not all(
        evaluate_admission(
            candidate, "calendar", purpose, now, account=account, server=server
        ).allowed
        for purpose in ("collection", "retention", "derived")
    ):
        raise CatalogPublishError("Calendar schedule or authority is not currently valid")
    expiry = datetime.fromisoformat(calendar["review_valid_until"])
    if (
        set(calendar["sources"]) != set(_OFFICIAL_URLS.values())
        or len(calendar["sources"]) != len(_OFFICIAL_URLS)
        or len({check.sha256 for check in packet.official_checks}) != len(_OFFICIAL_URLS)
        or any(
            not utc(check.checked_at)
            or not check.checked_at <= reviewed_at <= now < expiry
            or expiry > check.checked_at + timedelta(hours=24)
            for check in packet.official_checks
        )
    ):
        raise CatalogPublishError("Official calendar checks must be fresh and match both sources")

    # Use the runtime load window so in-range rows from older calendar
    # generations cannot survive a renewal with mismatched schedule metadata.
    start = (now.date() - timedelta(days=45)).isoformat()
    end = (now.date() + timedelta(days=90)).isoformat()
    if (calendar["coverage_start"], calendar["coverage_end"]) != (start, end):
        raise CatalogPublishError("Calendar packet must cover the complete current session window")
    if packet.review_kind == "unchanged_schedule":
        if previous is None or previous.state != "approved" or not previous.calendar:
            raise CatalogPublishError(
                "An unchanged schedule requires prior approved calendar evidence"
            )
        if calendar["version"] != previous.calendar.get("version") or _overrides(
            candidate, start, end
        ) != _overrides(previous, start, end):
            raise CatalogPublishError("Schedule changes require an updated-schedule review")

    # Keep check receipts and the packet identity with the derived authority.
    candidate = replace(
        candidate,
        calendar={
            **calendar,
            "official_checks": [check.model_dump(mode="json") for check in packet.official_checks],
            "operator_packet_sha256": review.digest,
            "operator_prior_sha256": packet.expected_previous_sha256,
        },
    )
    return candidate, account, server


async def _load(
    db: AsyncSession, *, lock: bool = False
) -> tuple[StockDataAdmission | None, ProductAdmission | None]:
    query = select(StockDataAdmission).where(StockDataAdmission.product == "calendar")
    row = (await db.scalars(query.with_for_update() if lock else query)).one_or_none()
    prior = (
        ProductAdmission(**{name: getattr(row, name) for name in _ADMISSION_FIELDS})
        if row
        else None
    )
    return row, prior


async def _renew(
    db: AsyncSession,
    review: _Review,
    now: datetime,
    *,
    expected_sha: str | None = None,
) -> dict[str, object]:
    if expected_sha is not None and expected_sha != review.digest:
        raise CatalogPublishError("Apply requires the exact reviewed calendar packet SHA-256")
    await _lock_catalog(db)
    row, prior = await _load(db, lock=True)
    candidate, account, server = _prepare(review, prior, now)
    sessions = build_sessions(now, candidate, account=account, server=server)
    if len(sessions) != 272 or any(
        session_at(exchange, now, sessions, candidate, account=account, server=server).state
        == "unknown"
        for exchange in EXCHANGES
    ):
        raise CatalogPublishError("Calendar review does not yield a complete usable session window")

    if expected_sha is not None:
        data = asdict(candidate)
        if row is None:
            db.add(StockDataAdmission(**data))
        else:
            for name, value in data.items():
                setattr(row, name, value)
        await db.flush()
        if await persist_sessions(
            db, sessions, candidate, now, account=account, server=server
        ) != len(sessions):
            raise CatalogPublishError("The reviewed sessions could not be persisted atomically")
    return {
        "disposition": "applied" if expected_sha is not None else "reviewed",
        "packet_sha256": review.digest,
        "generation": candidate.generation,
        "review_valid_until": candidate.calendar["review_valid_until"],
        "sessions": len(sessions),
    }


def _args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True, dest="command")
    commands.add_parser("inspect")
    for command in ("review", "apply"):
        operation = commands.add_parser(command)
        operation.add_argument("--packet", type=Path, required=True)
        operation.add_argument("--nyse-evidence", type=Path, required=True)
        operation.add_argument("--nasdaq-evidence", type=Path, required=True)
        if command == "apply":
            operation.add_argument("--expected-packet-sha", required=True)
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> dict[str, object]:
    review = (
        None
        if args.command == "inspect"
        else _read_review(args.packet, args.nyse_evidence, args.nasdaq_evidence)
    )
    require_source()
    settings = _database_settings(False)
    engine = create_async_engine(
        settings.database_url,
        connect_args=database_connect_args(settings, migration=True),
        hide_parameters=True,
    )
    try:
        async with AsyncSession(engine) as db, db.begin():
            await _check_connection(await db.connection(), False)
            if review is None:
                _, prior = await _load(db)
                return {
                    "generation": prior.generation if prior is not None else 0,
                    "state": prior.state if prior is not None else "missing",
                    "previous_sha256": _previous_digest(prior),
                }
            return await _renew(
                db,
                review,
                datetime.now(UTC),
                expected_sha=getattr(args, "expected_packet_sha", None),
            )
    finally:
        await engine.dispose()


def main(argv: Sequence[str] | None = None) -> int:
    args = _args(argv)
    try:
        result = asyncio.run(_run(args))
    except CatalogPublishError as exc:
        print(json.dumps({"disposition": "refused", "reason": str(exc)}), file=sys.stderr)
        return 2
    except ValueError, OSError, SQLAlchemyError:
        print(
            json.dumps(
                {"disposition": "refused", "reason": "invalid calendar input or connection"}
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
