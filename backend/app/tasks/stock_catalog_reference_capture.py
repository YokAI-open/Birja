"""Capture reusable anonymous OpenFIGI mappings for verified common shares."""

import argparse
import asyncio
import hashlib
import json
import os
import sys
import tempfile
from collections import Counter
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Literal, cast

import httpx
from pydantic import AwareDatetime, Field

from app.services.stock_catalog_classification import CatalogModel
from app.services.stock_catalog_pillar import (
    MAX_CAT_BYTES,
    MAX_PILLAR_BYTES,
    CatSnapshot,
    PillarSnapshot,
    parse_cat_snapshot,
    parse_pillar_snapshot,
)
from app.services.stock_catalog_reference import (
    ReferenceMapping,
    _primary_aliases,
    reconcile_nasdaq_reference_rows,
    reconcile_nyse_reference,
)
from app.services.stock_catalog_sources import (
    MAX_DIRECTORY_BYTES,
    MAX_DIRECTORY_ROWS,
    SYMBOL_PATTERN,
    CatalogSourceError,
    DirectorySnapshot,
    ListingExchange,
    parse_directory,
)
from app.tasks.stock_catalog_inventory import (
    _DEADLINE,
    _RIGHTS,
    MAX_MAPPING_ATTEMPTS,
    MAX_MAPPING_BYTES,
    MAX_MAPPING_JOBS,
    MAX_MAPPING_PER_MINUTE,
    MAX_STAGE_BYTES,
    OPENFIGI_URL,
    Digest,
    RetryMapping,
    _bounded_request,
    _lock_cursor,
    _lock_path,
    _read_bounded,
    _retry_delay,
    _rights_required,
    _screen_rows,
)
from app.tasks.stock_catalog_reference_inventory import _Observation

_HOST_CURSOR_LOCK = Path.home() / ".birja-stock-catalog-reference-capture"
_MAX_TARGETS = 2 * MAX_DIRECTORY_ROWS
_MAPPING_WINDOW = timedelta(minutes=1)
_FIELD_NAMES = (
    "ticker",
    "name",
    "exchCode",
    "marketSector",
    "securityType",
    "securityType2",
    "shareClassFIGI",
    "compositeFIGI",
)


class CaptureTarget(CatalogModel):
    venue: ListingExchange
    symbol: str = Field(pattern=f"^{SYMBOL_PATTERN}$")
    exchange: Literal["UN", "UQ", "UR", "UW"]


@dataclass(frozen=True, slots=True)
class CapturePlan:
    digest: str
    targets: tuple[CaptureTarget, ...]


class CaptureCursor(CatalogModel):
    schema_version: Literal[1] = 1
    plan_digest: Digest
    recent_attempts: tuple[AwareDatetime, ...] = Field(
        default=(), max_length=MAX_MAPPING_PER_MINUTE
    )
    retry_after: AwareDatetime | None = None
    observations: tuple[_Observation, ...] = Field(default=(), max_length=_MAX_TARGETS)


def plan_capture(
    nasdaq: DirectorySnapshot, cat: CatSnapshot, pillar: PillarSnapshot, now: datetime
) -> CapturePlan:
    """Bind the exact common-share jobs to one set of current reference files."""
    if not timedelta(0) <= now - nasdaq.published_at <= timedelta(days=4):
        raise CatalogSourceError("Nasdaq reference evidence is stale or in the future")
    _, candidates = _screen_rows(nasdaq.rows)
    reconcile_nyse_reference(cat, pillar, {}, now)
    reconcile_nasdaq_reference_rows(nasdaq, cat, pillar, candidates, {}, now)
    index = pillar.index_by_venue_symbol()
    targets = []
    for venue, symbol in sorted(cat.keys):
        issue = index.get((venue, symbol))
        if venue != "NYSE" or issue is None or issue.common_class is None:
            continue
        aliases = _primary_aliases(issue)
        if not aliases:
            raise CatalogSourceError("A verified NYSE common issue has no exact mapping symbol")
        targets.append(CaptureTarget(venue=venue, symbol=aliases[0], exchange="UN"))
    for row in candidates:
        issue = index.get(("NASDAQ", row.ticker))
        if issue is None or issue.common_class is None:
            continue
        code = row.figi_exchange
        if code not in {"UQ", "UR", "UW"}:
            raise CatalogSourceError("A verified Nasdaq issue has no exact mapping venue")
        targets.append(
            CaptureTarget(
                venue="NASDAQ", symbol=row.ticker, exchange=cast(Literal["UQ", "UR", "UW"], code)
            )
        )
    keys = {(item.venue, item.symbol) for item in targets}
    if (
        not 2 <= len(targets) <= _MAX_TARGETS
        or len(keys) != len(targets)
        or {item.venue for item in targets} != {"NYSE", "NASDAQ"}
    ):
        raise CatalogSourceError("Reference mapping targets do not reconcile across both venues")
    ordered = tuple(sorted(targets, key=lambda item: (item.venue, item.symbol)))
    material = json.dumps(
        [nasdaq.sha256, cat.sha256, pillar.sha256, [item.model_dump() for item in ordered]],
        separators=(",", ":"),
        sort_keys=True,
    )
    return CapturePlan(hashlib.sha256(material.encode()).hexdigest(), ordered)


def _normalized_result(value: object) -> dict[str, object]:
    if isinstance(value, dict) and set(value) == {"warning"} and isinstance(value["warning"], str):
        return {"warning": "No current mapping"}
    if not isinstance(value, dict) or set(value) != {"data"}:
        raise CatalogSourceError("OpenFIGI returned an unrecognized mapping outcome")
    rows = value["data"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise CatalogSourceError("OpenFIGI mapping row count is invalid")
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            raise CatalogSourceError("OpenFIGI mapping row is not an object")
        record: dict[str, str | None] = {}
        for field in _FIELD_NAMES:
            item = row.get(field)
            if item is not None and (
                not isinstance(item, str) or not 0 < len(item) <= 255 or not item.isprintable()
            ):
                raise CatalogSourceError("OpenFIGI mapping metadata has an invalid field")
            record[field] = item
        normalized.append(record)
    return {"data": normalized}


def _validate_cursor(cursor: CaptureCursor, plan: CapturePlan, now: datetime) -> None:
    if cursor.plan_digest != plan.digest or len(cursor.observations) > len(plan.targets):
        raise CatalogSourceError("Capture cursor does not match the current input digests")
    if (
        tuple(sorted(cursor.recent_attempts)) != cursor.recent_attempts
        or any(instant > now for instant in cursor.recent_attempts)
        or any(item.observation.observed_at > now for item in cursor.observations)
    ):
        raise CatalogSourceError("Capture cursor contains inconsistent timestamps")
    prefix = plan.targets[: len(cursor.observations)]
    for item, target in zip(cursor.observations, prefix, strict=True):
        exact_key = (item.venue, item.symbol) == (target.venue, target.symbol)
        normalized = _normalized_result(item.observation.result)
        if not exact_key or normalized != item.observation.result:
            raise CatalogSourceError("Capture cursor has inconsistent mapping results")


async def capture(
    plan: CapturePlan,
    cursor: CaptureCursor,
    client: httpx.AsyncClient,
    save: Callable[[CaptureCursor], None],
    *,
    clock: Callable[[], datetime],
    sleeper: Callable[[float], Awaitable[None]],
    check_scope: Callable[[datetime], None],
) -> CaptureCursor:
    """Persist each reservation before the request, including failed requests."""
    _validate_cursor(cursor, plan, clock())
    for _ in range(MAX_MAPPING_ATTEMPTS):
        start = len(cursor.observations)
        if start == len(plan.targets):
            break
        now = clock()
        if cursor.retry_after is not None and now < cursor.retry_after:
            break
        window = tuple(item for item in cursor.recent_attempts if now - item < _MAPPING_WINDOW)
        if len(window) >= MAX_MAPPING_PER_MINUTE:
            await sleeper((_MAPPING_WINDOW - (now - window[0])).total_seconds())
            now = clock()
            window = tuple(item for item in window if now - item < _MAPPING_WINDOW)
            if len(window) >= MAX_MAPPING_PER_MINUTE:
                break
        check_scope(now)
        cursor = cursor.model_copy(update={"recent_attempts": (*window, now), "retry_after": None})
        save(cursor)
        targets = plan.targets[start : start + MAX_MAPPING_JOBS]
        jobs = [
            {"idType": "TICKER", "idValue": item.symbol, "exchCode": item.exchange}
            for item in targets
        ]
        try:
            raw = await _bounded_request(client, "POST", OPENFIGI_URL, MAX_MAPPING_BYTES, jobs=jobs)
        except RetryMapping as exc:
            now = clock()
            delay = _retry_delay(exc.retry_after, now, 60)
            cursor = cursor.model_copy(update={"retry_after": now + timedelta(seconds=delay)})
            save(cursor)
            break
        payload = json.loads(raw)
        if not isinstance(payload, list) or len(payload) != len(targets):
            raise CatalogSourceError("OpenFIGI mapping batch size does not match the jobs")
        observed_at = clock()
        check_scope(observed_at)
        new = tuple(
            _Observation(
                venue=target.venue,
                symbol=target.symbol,
                observation=ReferenceMapping(
                    observed_at=observed_at, result=_normalized_result(item)
                ),
            )
            for target, item in zip(targets, payload, strict=True)
        )
        cursor = cursor.model_copy(update={"observations": (*cursor.observations, *new)})
        save(cursor)
    return cursor


def _write_lines(path: Path, lines: Iterable[str]) -> None:
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
        staged = Path(output.name)
        try:
            byte_count = 0
            for line in lines:
                row = line.encode() + b"\n"
                byte_count += len(row)
                if byte_count > MAX_STAGE_BYTES:
                    raise CatalogSourceError("Reference capture exceeds the private file bound")
                output.write(row)
            output.flush()
            os.fsync(output.fileno())
            output.close()
            os.replace(staged, path)
        finally:
            staged.unlink(missing_ok=True)


def _private_output(path: Path) -> None:
    directory = path.parent.stat()
    if directory.st_uid != os.getuid() or directory.st_mode & 0o077:
        raise CatalogSourceError("Reference capture requires an owner-only output directory")
    if path.is_symlink():
        raise CatalogSourceError("Reference capture output cannot be a symlink")
    if path.exists():
        current = path.stat()
        if not path.is_file() or current.st_uid != os.getuid() or current.st_mode & 0o077:
            raise CatalogSourceError("Reference capture output must be an owner-only file")


def _load_plan(args: argparse.Namespace, now: datetime) -> CapturePlan:
    nasdaq = parse_directory("nasdaqlisted", _read_bounded(args.nasdaq, MAX_DIRECTORY_BYTES))
    cat = parse_cat_snapshot(
        _read_bounded(args.cat, MAX_CAT_BYTES),
        published_at=args.cat_published_at,
        expected_trade_date=args.trade_date,
    )
    pillar = parse_pillar_snapshot(
        _read_bounded(args.pillar, MAX_PILLAR_BYTES),
        filename=args.pillar.name,
        expected_trade_date=args.trade_date,
    )
    return plan_capture(nasdaq, cat, pillar, now)


async def _run(args: argparse.Namespace) -> int:
    for output in (args.cursor, args.output):
        _private_output(output)
    cursor_path = args.cursor.resolve()
    output_path = args.output.resolve()
    writes = {cursor_path, output_path, _lock_path(cursor_path), _lock_path(_HOST_CURSOR_LOCK)}
    inputs = {item.resolve() for item in (args.nasdaq, args.cat, args.pillar, args.rights)}
    if len(writes) != 4 or not writes.isdisjoint(inputs):
        raise CatalogSourceError("Reference capture requires separate paths for inputs and output")

    def clock() -> datetime:
        return datetime.now(UTC)

    def check_scope(at: datetime) -> None:
        _rights_required(at, rights, False, nyse_source="openfigi_nyse")

    with _lock_cursor(_HOST_CURSOR_LOCK), _lock_cursor(cursor_path):
        rights = _RIGHTS.validate_json(_read_bounded(args.rights))
        now = clock()
        check_scope(now)
        plan = _load_plan(args, now)
        cursor = (
            CaptureCursor.model_validate_json(_read_bounded(cursor_path))
            if cursor_path.exists()
            else CaptureCursor(plan_digest=plan.digest)
        )
        async with httpx.AsyncClient(
            follow_redirects=False, trust_env=False, timeout=_DEADLINE
        ) as client:
            cursor = await capture(
                plan,
                cursor,
                client,
                lambda state: _write_lines(cursor_path, (state.model_dump_json(),)),
                clock=clock,
                sleeper=asyncio.sleep,
                check_scope=check_scope,
            )
        _write_lines(output_path, (item.model_dump_json() for item in cursor.observations))
    result = {
        "plan_sha256": plan.digest,
        "targets": dict(Counter(item.venue for item in plan.targets)),
        "observations": dict(Counter(item.venue for item in cursor.observations)),
        "retry_after": cursor.retry_after.isoformat() if cursor.retry_after else None,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if len(cursor.observations) == len(plan.targets) else 2


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    for label in ("nasdaq", "cat", "pillar", "rights", "cursor", "output"):
        parser.add_argument(f"--{label}", type=Path, required=True)
    parser.add_argument("--cat-published-at", type=datetime.fromisoformat, required=True)
    parser.add_argument("--trade-date", type=date.fromisoformat, required=True)
    return parser.parse_args()


def main() -> int:
    try:
        return asyncio.run(_run(_arguments()))
    except (OSError, ValueError, httpx.HTTPError, TimeoutError) as exc:
        detail = str(exc) if isinstance(exc, CatalogSourceError) else type(exc).__name__
        print(f"Reference capture refused: {detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
