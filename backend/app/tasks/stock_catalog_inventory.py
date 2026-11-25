"""Build a reconciled stock catalog candidate from reviewed inventory inputs."""

import argparse
import asyncio
import fcntl
import json
import os
import sys
import tempfile
from collections import Counter, deque
from collections.abc import Awaitable, Callable, Iterable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Annotated, Literal

import httpx
from pydantic import AwareDatetime, Field, TypeAdapter

from app.services.stock_catalog_classification import (
    CORROBORATION_AGE,
    SHA256,
    CatalogModel,
    InventoryRow,
    ReviewedIssue,
    classify_mapping,
    classify_reviewed,
    outcome,
)
from app.services.stock_catalog_sources import (
    DIRECTORY_URLS,
    MAX_DIRECTORY_BYTES,
    MAX_DIRECTORY_ROWS,
    CatalogSourceError,
    DirectoryRow,
    DirectorySnapshot,
    DirectorySource,
    parse_directory,
    validate_directory_pair,
)

Mode = Literal["fixture", "live"]
Venue = Literal["NASDAQ", "NYSE", "out_of_scope"]
Artifact = Literal["nasdaqlisted", "otherlisted", "openfigi", "issuer_exception"]
Purpose = Literal["collection", "internal_use", "derived_use", "display", "storage", "backup"]
Digest = Annotated[str, Field(pattern=SHA256)]

MAX_MAPPING_ATTEMPTS = 100
MAX_MAPPING_PER_MINUTE = 20
MAX_MAPPING_JOBS = 10
MAX_MAPPING_BYTES = 512 * 1024
MAX_STAGE_BYTES = 32 * 1024 * 1024
OPENFIGI_URL = "https://api.openfigi.com/v3/mapping"
_DEADLINE = 15
_MAX_RETRY_WAIT = 60
_RETRY_STATUSES = {429, 500, 502, 503, 504}
_DIRECTORY_FIELDS = {
    "ticker",
    "listing_exchange",
    "company_name",
    "aliases",
    "share_class",
    "eligibility",
    "source_evidence",
}
_CLASSIFICATION_FIELDS = {"classification", "identity_key", "source_evidence"}
_DURABLE_PURPOSES = {"collection", "internal_use", "derived_use", "storage", "backup"}
_MAPPING_REASONS = {
    "corroborated_share_class",
    "recognized_security_type",
    "mapping_missing",
    "mapping_conflict_or_unknown",
}


class ArtifactRights(CatalogModel):
    artifact: Artifact
    reference: str = Field(min_length=8, max_length=512)
    reviewed_at: AwareDatetime
    valid_until: AwareDatetime
    fields: dict[str, tuple[Purpose, ...]]


class SourceEvidence(CatalogModel):
    artifact: DirectorySource
    sha256: Digest
    published_at: AwareDatetime
    row_count: int = Field(gt=0, le=MAX_DIRECTORY_ROWS)


class Coverage(CatalogModel):
    included: int = Field(ge=0)
    excluded: int = Field(ge=0)
    duplicate: int = Field(ge=0)
    unresolved: int = Field(ge=0)
    total: int = Field(ge=0)


class CatalogManifest(CatalogModel):
    schema_version: Literal[1] = 1
    mode: Mode
    sources: tuple[SourceEvidence, SourceEvidence]
    rights: tuple[ArtifactRights, ...]
    rows: tuple[InventoryRow, ...]
    coverage: dict[Venue, Coverage]
    complete: bool


class Cursor(CatalogModel):
    schema_version: Literal[1] = 1
    source_digests: tuple[Digest, Digest]
    recent_attempts: tuple[AwareDatetime, ...] = Field(
        default=(), max_length=MAX_MAPPING_PER_MINUTE
    )
    retry_after: AwareDatetime | None = None
    outcomes: tuple[InventoryRow, ...] = ()


def _rights_required(now: datetime, rights: tuple[ArtifactRights, ...], exceptions: bool) -> None:
    required = {
        "nasdaqlisted": _DIRECTORY_FIELDS,
        "otherlisted": _DIRECTORY_FIELDS,
        "openfigi": _CLASSIFICATION_FIELDS | {"aliases"},
    }
    if exceptions:
        required["issuer_exception"] = _CLASSIFICATION_FIELDS
    indexed = {item.artifact: item for item in rights}
    if len(indexed) != len(rights):
        raise CatalogSourceError("Ambiguous artifact rights")
    for artifact, fields in required.items():
        matching = next((item for item in rights if item.artifact == artifact), None)
        if matching is None or not matching.reviewed_at <= now < matching.valid_until:
            raise CatalogSourceError(f"Current explicit rights required for {artifact}")
        for field in fields:
            purposes = _DURABLE_PURPOSES
            if field in {"ticker", "company_name", "listing_exchange", "share_class"}:
                purposes = purposes | {"display"}
            if not purposes.issubset(matching.fields.get(field, ())):
                raise CatalogSourceError(f"Incomplete rights scope for {artifact}.{field}")


def _coverage(rows: Iterable[InventoryRow]) -> dict[Venue, Coverage]:
    counts = Counter((row.listing_exchange or "out_of_scope", row.disposition) for row in rows)
    venues: tuple[Venue, ...] = ("NASDAQ", "NYSE", "out_of_scope")
    coverage = {}
    for venue in venues:
        included = counts[venue, "included"]
        excluded = counts[venue, "excluded"]
        duplicate = counts[venue, "duplicate"]
        unresolved = counts[venue, "unresolved"]
        coverage[venue] = Coverage(
            included=included,
            excluded=excluded,
            duplicate=duplicate,
            unresolved=unresolved,
            total=included + excluded + duplicate + unresolved,
        )
    return coverage


def _complete(coverage: dict[Venue, Coverage]) -> bool:
    return (
        coverage["NYSE"].included > 0
        and coverage["NASDAQ"].included > 0
        and not any(count.unresolved for count in coverage.values())
    )


def validate_manifest(manifest: CatalogManifest, now: datetime) -> None:
    """Verify the manifest's compact evidence and completeness claims on read."""
    first, second = manifest.sources
    if (
        (first.artifact, second.artifact) != ("nasdaqlisted", "otherlisted")
        or first.sha256 == second.sha256
        or abs(first.published_at - second.published_at) > timedelta(hours=1)
        or any(
            not timedelta(0) <= now - src.published_at <= timedelta(days=4)
            for src in manifest.sources
        )
    ):
        raise CatalogSourceError("Manifest directory pair is invalid or stale")
    coverage = _coverage(manifest.rows)
    if manifest.coverage != coverage or manifest.complete != _complete(coverage):
        raise CatalogSourceError("Manifest coverage does not reconcile")
    if manifest.mode == "live":
        _rights_required(
            now,
            manifest.rights,
            any(row.reason == "reviewed_issue_evidence" for row in manifest.rows),
        )
    counts = Counter(row.source for row in manifest.rows)
    if any(counts[src.artifact] != src.row_count for src in manifest.sources):
        raise CatalogSourceError("Manifest row count does not match source count")
    expected = {
        f"{src.artifact}:{i}" for src in manifest.sources for i in range(1, src.row_count + 1)
    }
    if len(manifest.rows) != len(expected) or {row.row_key for row in manifest.rows} != expected:
        raise CatalogSourceError("Manifest row references do not reconcile")
    admitted = [row for row in manifest.rows if row.disposition == "included"]
    if (
        any(
            row.identity_key is None
            or row.classification not in {"common_stock", "ordinary_shares"}
            or row.listing_exchange is None
            or row.evidence_at is None
            or not timedelta(0) <= now - row.evidence_at <= CORROBORATION_AGE
            for row in admitted
        )
        or len({row.identity_key for row in admitted}) != len(admitted)
        or len({(row.listing_exchange, row.ticker) for row in admitted}) != len(admitted)
        or any(
            row.name_source != row.source or not row.row_key.startswith(f"{row.source}:")
            for row in manifest.rows
        )
    ):
        raise CatalogSourceError("Manifest issue identities or evidence do not reconcile")


def _build_manifest(
    mode: Mode,
    snapshots: tuple[DirectorySnapshot, DirectorySnapshot],
    rights: tuple[ArtifactRights, ...],
    rows: tuple[InventoryRow, ...],
    now: datetime,
) -> CatalogManifest:
    first, second = snapshots
    coverage = _coverage(rows)
    manifest = CatalogManifest(
        mode=mode,
        sources=(
            SourceEvidence(
                artifact=first.artifact,
                sha256=first.sha256,
                published_at=first.published_at,
                row_count=len(first.rows),
            ),
            SourceEvidence(
                artifact=second.artifact,
                sha256=second.sha256,
                published_at=second.published_at,
                row_count=len(second.rows),
            ),
        ),
        rights=rights,
        rows=rows,
        coverage=coverage,
        complete=_complete(coverage),
    )
    validate_manifest(manifest, now)
    return manifest


def _screen_rows(
    rows: tuple[DirectoryRow, ...],
) -> tuple[dict[str, InventoryRow], list[DirectoryRow]]:
    results: dict[str, InventoryRow] = {}
    to_map = []
    by_listing: dict[tuple[str, str], list[DirectoryRow]] = {}
    for row in rows:
        if row.listing_exchange is not None:
            by_listing.setdefault((row.listing_exchange, row.ticker), []).append(row)
        elif row.exclusion:
            results[row.row_key] = outcome(
                row, "excluded", row.exclusion, classification="out_of_scope"
            )
        else:
            raise CatalogSourceError("Candidate directory row has no listing exchange")
    for group in by_listing.values():
        if len({row.row_digest for row in group}) > 1:
            for row in group:
                results[row.row_key] = outcome(row, "unresolved", "conflicting_directory_rows")
        else:
            first = group[0]
            if first.exclusion:
                results[first.row_key] = outcome(
                    first, "excluded", first.exclusion, classification="out_of_scope"
                )
            else:
                to_map.append(first)
            for row in group[1:]:
                results[row.row_key] = outcome(row, "duplicate", "identical_directory_row")
    return results, to_map


def _deduplicate_identities(rows: tuple[InventoryRow, ...]) -> tuple[InventoryRow, ...]:
    counts = Counter(row.identity_key for row in rows if row.disposition == "included")
    return tuple(
        row.model_copy(
            update={
                "disposition": "unresolved",
                "reason": "conflicting_issue_identity",
                "identity_key": None,
                "share_class": None,
            }
        )
        if row.disposition == "included" and counts[row.identity_key] > 1
        else row
        for row in rows
    )


def _read_bounded(path: Path, limit: int = MAX_STAGE_BYTES) -> bytes:
    with path.open("rb") as stream:
        payload = stream.read(limit + 1)
    if len(payload) > limit:
        raise CatalogSourceError("Inventory file exceeds its byte limit")
    return payload


def _write_model(path: Path, value: CatalogModel) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as stream:
        staged = Path(stream.name)
        try:
            stream.write(value.model_dump_json())
            stream.write("\n")
            stream.close()
            os.replace(staged, path)
        finally:
            staged.unlink(missing_ok=True)


class RetryMapping(Exception):
    def __init__(self, retry_after: str | None) -> None:
        self.retry_after = retry_after


async def _bounded_request(
    client: httpx.AsyncClient,
    method: Literal["GET", "POST"],
    url: str,
    limit: int,
    *,
    jobs: list[dict[str, str]] | None = None,
) -> bytes:
    async with asyncio.timeout(_DEADLINE), client.stream(method, url, json=jobs) as response:
        if method == "POST" and response.status_code in _RETRY_STATUSES:
            raise RetryMapping(response.headers.get("retry-after"))
        if response.status_code != 200:
            raise CatalogSourceError(f"Official source returned HTTP {response.status_code}")
        raw = bytearray()
        async for chunk in response.aiter_bytes(chunk_size=16 * 1024):
            if len(raw) + len(chunk) > limit:
                raise CatalogSourceError("Official source exceeds its response size limit")
            raw.extend(chunk)
        return bytes(raw)


def _retry_delay(value: str | None, now: datetime, fallback: int) -> float:
    if value is None:
        return fallback
    if value.isascii() and value.isdecimal():
        return float(value) if len(value) <= 3 else _MAX_RETRY_WAIT + 1
    try:
        date = parsedate_to_datetime(value)
        return max(fallback, (date - now).total_seconds())
    except ValueError, OverflowError, TypeError:
        return fallback


def _decode_batch(
    payload: object, rows: list[DirectoryRow], now: datetime
) -> tuple[InventoryRow, ...]:
    if not isinstance(payload, list) or len(payload) != len(rows):
        raise CatalogSourceError("Mapping batch size does not match its jobs")
    return tuple(
        classify_mapping(row, result, now) for row, result in zip(rows, payload, strict=True)
    )


async def _mapping_batch(
    client: httpx.AsyncClient, batch: list[DirectoryRow], now: datetime
) -> tuple[InventoryRow, ...]:
    jobs = []
    for row in batch:
        if row.figi_exchange is None:
            raise CatalogSourceError("Candidate directory row has no mapping exchange")
        jobs.append({"idType": "TICKER", "idValue": row.ticker, "exchCode": row.figi_exchange})
    payload = await _bounded_request(client, "POST", OPENFIGI_URL, MAX_MAPPING_BYTES, jobs=jobs)
    return _decode_batch(json.loads(payload), batch, now)


async def _resume_mapping(
    client: httpx.AsyncClient,
    pending: list[DirectoryRow],
    cursor: Cursor,
    save: Callable[[Cursor], None],
    *,
    clock: Callable[[], datetime],
    sleeper: Callable[[float], Awaitable[None]],
    check_scope: Callable[[datetime], None],
) -> Cursor:
    attempts = deque(cursor.recent_attempts)
    completed = list(cursor.outcomes)
    retry_after = cursor.retry_after
    run_attempts = 0

    def checkpoint() -> Cursor:
        updated = Cursor(
            source_digests=cursor.source_digests,
            recent_attempts=tuple(attempts),
            retry_after=retry_after,
            outcomes=tuple(completed),
        )
        save(updated)
        return updated

    for start in range(0, len(pending), MAX_MAPPING_JOBS):
        batch = pending[start : start + MAX_MAPPING_JOBS]
        for retry in range(3):
            if run_attempts == MAX_MAPPING_ATTEMPTS:
                return checkpoint()
            now = clock()
            if retry_after is not None and retry_after > now:
                wait = (retry_after - now).total_seconds()
                if wait > _MAX_RETRY_WAIT:
                    return checkpoint()
                await sleeper(wait)
            now = clock()
            while attempts and now - attempts[0] >= timedelta(minutes=1):
                attempts.popleft()
            if len(attempts) >= MAX_MAPPING_PER_MINUTE:
                await sleeper(max(0, 60 - (now - attempts[0]).total_seconds()))
                now = clock()
                while attempts and now - attempts[0] >= timedelta(minutes=1):
                    attempts.popleft()
                if len(attempts) >= MAX_MAPPING_PER_MINUTE:
                    return checkpoint()
            check_scope(now)
            retry_after = None
            attempts.append(now)
            run_attempts += 1
            checkpoint()
            try:
                completed.extend(await _mapping_batch(client, batch, now))
            except RetryMapping as exc:
                wait = _retry_delay(exc.retry_after, clock(), 2**retry)
                retry_after = clock() + timedelta(seconds=wait)
                checkpoint()
            except httpx.TransportError, TimeoutError:
                retry_after = clock() + timedelta(seconds=2**retry)
                checkpoint()
            else:
                checkpoint()
                break
        else:
            return checkpoint()
    return checkpoint()


_RIGHTS = TypeAdapter(tuple[ArtifactRights, ...])
_REVIEWS = TypeAdapter(tuple[ReviewedIssue, ...])


def _reusable(
    previous: Iterable[InventoryRow], now: datetime
) -> dict[tuple[str, str], InventoryRow]:
    return {
        (row.source, row.row_digest): row
        for row in previous
        if row.evidence_at is not None
        and row.reason in _MAPPING_REASONS
        and timedelta(0)
        <= now - row.evidence_at
        <= (timedelta(days=1) if row.disposition == "unresolved" else CORROBORATION_AGE)
    }


def _inventory_inputs(
    snapshots: tuple[DirectorySnapshot, DirectorySnapshot],
    reviews: tuple[ReviewedIssue, ...],
    now: datetime,
    previous: Iterable[InventoryRow],
) -> tuple[tuple[DirectoryRow, ...], dict[str, InventoryRow], list[DirectoryRow]]:
    rows = (*snapshots[0].rows, *snapshots[1].rows)
    results, candidates = _screen_rows(rows)
    by_issue = {(review.source, review.row_digest): review for review in reviews}
    if len(by_issue) != len(reviews):
        raise CatalogSourceError("Duplicate reviewed issue evidence")
    reusable = _reusable(previous, now)
    pending = []
    for row in candidates:
        key = (row.source, row.row_digest)
        if key in by_issue:
            results[row.row_key] = classify_reviewed(row, by_issue[key], now)
        elif (saved := reusable.get(key)) is not None:
            if saved.ticker != row.ticker or saved.listing_exchange != row.listing_exchange:
                raise CatalogSourceError("Cached mapping row does not match its directory issue")
            results[row.row_key] = saved.model_copy(update={"row_key": row.row_key})
        else:
            pending.append(row)
    return rows, results, pending


async def inventory(
    args: argparse.Namespace, client: httpx.AsyncClient, now: datetime
) -> CatalogManifest:
    rights = _RIGHTS.validate_json(_read_bounded(args.rights)) if args.rights else ()
    reviews = _REVIEWS.validate_json(_read_bounded(args.exceptions)) if args.exceptions else ()
    cursor = None
    if args.mode == "live":
        _rights_required(now, rights, bool(reviews))
        directory_bytes = await asyncio.gather(
            *(
                _bounded_request(client, "GET", url, MAX_DIRECTORY_BYTES)
                for url in DIRECTORY_URLS.values()
            )
        )
        if args.cursor.exists():
            cursor = Cursor.model_validate_json(_read_bounded(args.cursor))
    else:
        directory_bytes = [
            _read_bounded(path, MAX_DIRECTORY_BYTES) for path in (args.nasdaq, args.other)
        ]
    snapshots = validate_directory_pair(
        parse_directory("nasdaqlisted", directory_bytes[0]),
        parse_directory("otherlisted", directory_bytes[1]),
        now,
    )
    source_digests = (snapshots[0].sha256, snapshots[1].sha256)
    previous = cursor.outcomes if cursor else ()
    if cursor is not None and cursor.source_digests != source_digests:
        # Keep recent request accounting across directory refreshes, then rebind unchanged evidence.
        cursor = cursor.model_copy(update={"source_digests": source_digests, "outcomes": ()})
    rows, results, pending = _inventory_inputs(snapshots, reviews, now, previous)
    if args.mode == "live":
        cursor = cursor or Cursor(source_digests=source_digests)
        cached = tuple(row for row in results.values() if row.reason in _MAPPING_REASONS)
        cursor = cursor.model_copy(update={"outcomes": cached})
        cursor = await _resume_mapping(
            client,
            pending,
            cursor,
            lambda state: _write_model(args.cursor, state),
            clock=lambda: datetime.now(UTC),
            sleeper=asyncio.sleep,
            check_scope=lambda at: _rights_required(at, rights, bool(reviews)),
        )
        results.update({row.row_key: row for row in cursor.outcomes})
        now = datetime.now(UTC)
    else:
        mappings = json.loads(_read_bounded(args.mapping))
        if not isinstance(mappings, dict) or not set(mappings).issubset(
            {row.row_key for row in pending}
        ):
            raise CatalogSourceError("Unexpected fixture mapping row key")
        mapped = (
            classify_mapping(row, mappings[row.row_key], now)
            for row in pending
            if row.row_key in mappings
        )
        results.update({row.row_key: row for row in mapped})
    audited = tuple(
        results.get(row.row_key) or outcome(row, "unresolved", "mapping_pending") for row in rows
    )
    return _build_manifest(args.mode, snapshots, rights, _deduplicate_identities(audited), now)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--exceptions", type=Path)
    modes = parser.add_subparsers(dest="mode", required=True)
    fixture = modes.add_parser("fixture")
    fixture.add_argument("--as-of", type=datetime.fromisoformat, required=True)
    fixture.add_argument("--nasdaq", type=Path, required=True)
    fixture.add_argument("--other", type=Path, required=True)
    fixture.add_argument("--mapping", type=Path, required=True)
    live = modes.add_parser("live")
    live.add_argument("--rights", type=Path, required=True)
    live.add_argument("--cursor", type=Path, required=True)
    parser.set_defaults(rights=None)
    return parser.parse_args()


@contextmanager
def _lock_cursor(path: Path) -> Iterator[None]:
    lock_path = _lock_path(path)
    descriptor = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise CatalogSourceError("An inventory already owns this live cursor") from exc
        yield
    finally:
        os.close(descriptor)


def _lock_path(path: Path) -> Path:
    return path.with_suffix(f"{path.suffix}.lock")


async def _run(args: argparse.Namespace) -> bool:
    now = args.as_of if args.mode == "fixture" else datetime.now(UTC)
    async with httpx.AsyncClient(
        follow_redirects=False, trust_env=False, timeout=_DEADLINE
    ) as client:
        if args.mode == "live":
            cursor = args.cursor.resolve()
            if args.output.resolve() in {cursor, _lock_path(cursor)}:
                raise CatalogSourceError("Live output and cursor require separate paths")
            with _lock_cursor(cursor):
                manifest = await inventory(args, client, now)
                _write_model(args.output, manifest)
        else:
            manifest = await inventory(args, client, now)
            _write_model(args.output, manifest)
    print(
        json.dumps(
            {venue: item.model_dump() for venue, item in manifest.coverage.items()}, sort_keys=True
        )
    )
    return manifest.complete


def main() -> int:
    try:
        return 0 if asyncio.run(_run(_args())) else 2
    except (OSError, ValueError, httpx.HTTPError, TimeoutError) as exc:
        # Validation bodies and filesystem paths may contain restricted data.
        detail = str(exc) if isinstance(exc, CatalogSourceError) else type(exc).__name__
        print(f"Inventory refused: {detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
