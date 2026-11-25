"""Build a stock catalog using reusable OpenFIGI NYSE issue metadata."""

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import Field

from app.services.stock_catalog_classification import (
    CatalogModel,
    InventoryRow,
    ReviewedIssue,
    classify_reviewed,
)
from app.services.stock_catalog_pillar import (
    MAX_CAT_BYTES,
    MAX_PILLAR_BYTES,
    CatSnapshot,
    PillarSnapshot,
    parse_cat_snapshot,
    parse_pillar_snapshot,
)
from app.services.stock_catalog_provider import _reject_constant, _reject_duplicates
from app.services.stock_catalog_publish import CatalogPublishError
from app.services.stock_catalog_reference import (
    ReferenceMapping,
    _digest,
    reconcile_nasdaq_reference_rows,
    reconcile_nyse_reference,
)
from app.services.stock_catalog_sources import (
    MAX_DIRECTORY_BYTES,
    MAX_DIRECTORY_ROWS,
    SYMBOL_PATTERN,
    CatalogSourceError,
    DirectoryRow,
    ListingExchange,
    parse_directory,
)
from app.tasks.stock_catalog_enroll import _private_file
from app.tasks.stock_catalog_inventory import (
    _REVIEWS,
    _RIGHTS,
    CatalogManifest,
    _build_manifest,
    _deduplicate_identities,
    _read_bounded,
    _rights_required,
    _screen_rows,
    _write_model,
)

_MAX_EXCEPTION_BYTES = 256 * 1024
_MAX_EXCEPTIONS = 256


class _Observation(CatalogModel):
    venue: ListingExchange
    symbol: str = Field(pattern=f"^{SYMBOL_PATTERN}$")
    observation: ReferenceMapping


def _read_mappings(path: Path) -> dict[ListingExchange, dict[str, ReferenceMapping]]:
    result: dict[ListingExchange, dict[str, ReferenceMapping]] = {"NYSE": {}, "NASDAQ": {}}
    for ordinal, line in enumerate(_read_bounded(path).splitlines(), 1):
        if ordinal > 2 * MAX_DIRECTORY_ROWS or len(line) > 512 * 1024:
            raise CatalogSourceError("Mapping observations exceed their size bound")
        item = _Observation.model_validate_json(line)
        venue_mappings = result[item.venue]
        if item.symbol in venue_mappings:
            raise CatalogSourceError("Mapping observation has a duplicate issue key")
        venue_mappings[item.symbol] = item.observation
    return result


def _read_reviews(path: Path) -> tuple[ReviewedIssue, ...]:
    try:
        body = _private_file(path, _MAX_EXCEPTION_BYTES)
    except CatalogPublishError as exc:
        raise CatalogSourceError(str(exc)) from None
    try:
        json.loads(body, object_pairs_hook=_reject_duplicates, parse_constant=_reject_constant)
    except ValueError, RecursionError:
        raise CatalogSourceError("Issuer review file has invalid JSON") from None
    reviews = _REVIEWS.validate_json(body)
    if not 1 <= len(reviews) <= _MAX_EXCEPTIONS:
        raise CatalogSourceError("Issuer review file exceeds its reviewed issue bound")
    if len({(review.source, review.row_digest) for review in reviews}) != len(reviews):
        raise CatalogSourceError("Issuer review repeats a directory row")
    for review in reviews:
        url = urlsplit(review.source_url)
        if (
            url.scheme != "https"
            or url.netloc != "www.sec.gov"
            or not url.path.strip("/")
            or url.query
            or url.fragment
            or review.reviewed_at.utcoffset() != timedelta(0)
        ):
            raise CatalogSourceError("Issuer review requires a dated official SEC evidence link")
    return reviews


def _reviewed_outcome(
    row: DirectoryRow,
    prior: InventoryRow,
    review: ReviewedIssue,
    cat: CatSnapshot,
    pillar: PillarSnapshot,
    pillar_keys: set[tuple[ListingExchange, str]],
    now: datetime,
) -> InventoryRow:
    proof_row = row
    if row.source == "openfigi_nyse":
        key: tuple[ListingExchange, str] = ("NYSE", review.ticker)
        if (
            row.ticker
            or row.company_name
            or row.aliases
            or review.classification != "out_of_scope"
            or key not in cat.keys
            or key not in pillar_keys
            or review.row_digest != _digest([cat.sha256, pillar.sha256, review.ticker])
        ):
            raise CatalogSourceError("NYSE issuer exclusion differs from exact comparator evidence")
        proof_row = replace(row, ticker=review.ticker)
    elif row.source != "nasdaqlisted" or not row.ticker or not row.company_name:
        raise CatalogSourceError("Issuer review must match an admitted reference directory")

    checked = classify_reviewed(proof_row, review, now)
    if checked.disposition == "unresolved":
        raise CatalogSourceError("Issuer review no longer matches the current source row or date")
    if prior.disposition in {"included", "excluded"} and (
        prior.classification != checked.classification
    ):
        raise CatalogSourceError("Issuer review conflicts with a resolved classification")
    if prior.disposition == "duplicate" or prior.reason == "conflicting_directory_rows":
        raise CatalogSourceError("Issuer review cannot resolve an ambiguous directory row")

    proof: dict[str, object] = {"issuer_review": review.model_dump(mode="json")}
    if prior.disposition == "included" and prior.evidence_at is not None:
        proof["retained_mapping_digest"] = prior.evidence_digest
        return prior.model_copy(
            update={
                "evidence_at": min(prior.evidence_at, review.reviewed_at),
                "evidence_digest": _digest(proof),
            }
        )
    return checked.model_copy(update={"ticker": row.ticker, "evidence_digest": _digest(proof)})


def _apply_reviews(
    rows: tuple[DirectoryRow, ...],
    outcomes: dict[str, InventoryRow],
    reviews: tuple[ReviewedIssue, ...],
    cat: CatSnapshot,
    pillar: PillarSnapshot,
    now: datetime,
) -> None:
    by_digest: dict[tuple[str, str], list[DirectoryRow]] = defaultdict(list)
    for row in rows:
        by_digest[row.source, row.row_digest].append(row)
    pillar_keys = set(pillar.index_by_venue_symbol())
    for review in reviews:
        matches = by_digest[review.source, review.row_digest]
        if len(matches) != 1:
            raise CatalogSourceError("Issuer review must match exactly one current source row")
        row = matches[0]
        outcomes[row.row_key] = _reviewed_outcome(
            row, outcomes[row.row_key], review, cat, pillar, pillar_keys, now
        )


def _inventory(args: argparse.Namespace, now: datetime) -> CatalogManifest:
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
    exception_file = getattr(args, "exceptions", None)
    reviews = _read_reviews(exception_file) if exception_file else ()
    mappings = _read_mappings(args.mapping)
    rights = _RIGHTS.validate_json(_read_bounded(args.rights)) if args.rights else ()
    if reviews and not args.fixture:
        _rights_required(now, rights, True, "openfigi_nyse")
    nyse, nyse_rows = reconcile_nyse_reference(cat, pillar, mappings["NYSE"], now)
    screened, pending = _screen_rows(nasdaq.rows)
    checked = reconcile_nasdaq_reference_rows(nasdaq, cat, pillar, pending, mappings["NASDAQ"], now)
    screened.update({row.row_key: row for row in (*checked, *nyse_rows)})
    source_rows = (*nasdaq.rows, *nyse.rows)
    if reviews:
        _apply_reviews(source_rows, screened, reviews, cat, pillar, now)
    rows = tuple(screened[row.row_key] for row in source_rows)
    return _build_manifest(
        "fixture" if args.fixture else "live",
        (nasdaq, nyse),
        rights,
        _deduplicate_identities(rows),
        now,
    )


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    for label in ("nasdaq", "cat", "pillar", "mapping", "output"):
        parser.add_argument(f"--{label}", type=Path, required=True)
    parser.add_argument("--cat-published-at", type=datetime.fromisoformat, required=True)
    parser.add_argument("--trade-date", type=date.fromisoformat, required=True)
    parser.add_argument("--rights", type=Path)
    parser.add_argument("--exceptions", type=Path, help="private reviewed SEC issue exceptions")
    parser.add_argument("--fixture", type=datetime.fromisoformat)
    args = parser.parse_args()
    if (args.rights is None) == (args.fixture is None):
        parser.error("Supply either current rights or an isolated fixture timestamp")
    inputs = (args.nasdaq, args.cat, args.pillar, args.mapping, args.rights, args.exceptions)
    if any(args.output.resolve() == item.resolve() for item in inputs if item is not None):
        parser.error("Choose an output path separate from the evidence inputs")
    return args


def main() -> int:
    try:
        args = _arguments()
        manifest = _inventory(args, args.fixture or datetime.now(UTC))
        _write_model(args.output, manifest)
        print(
            json.dumps(
                {venue: coverage.model_dump() for venue, coverage in manifest.coverage.items()},
                sort_keys=True,
            )
        )
        return 0 if manifest.complete else 2
    except (OSError, ValueError) as exc:
        # Validation bodies and filesystem paths can contain restricted data.
        detail = str(exc) if isinstance(exc, CatalogSourceError) else type(exc).__name__
        print(f"Reference inventory refused: {detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
