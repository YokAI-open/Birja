"""Build a stock catalog using reusable OpenFIGI NYSE issue metadata."""

import argparse
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from pydantic import Field

from app.services.stock_catalog_classification import CatalogModel
from app.services.stock_catalog_pillar import (
    MAX_CAT_BYTES,
    MAX_PILLAR_BYTES,
    parse_cat_snapshot,
    parse_pillar_snapshot,
)
from app.services.stock_catalog_reference import (
    ReferenceMapping,
    reconcile_nasdaq_reference_rows,
    reconcile_nyse_reference,
)
from app.services.stock_catalog_sources import (
    MAX_DIRECTORY_BYTES,
    MAX_DIRECTORY_ROWS,
    SYMBOL_PATTERN,
    CatalogSourceError,
    ListingExchange,
    parse_directory,
)
from app.tasks.stock_catalog_inventory import (
    _RIGHTS,
    CatalogManifest,
    _build_manifest,
    _deduplicate_identities,
    _read_bounded,
    _screen_rows,
    _write_model,
)


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
    mappings = _read_mappings(args.mapping)
    rights = _RIGHTS.validate_json(_read_bounded(args.rights)) if args.rights else ()
    nyse, nyse_rows = reconcile_nyse_reference(cat, pillar, mappings["NYSE"], now)
    screened, pending = _screen_rows(nasdaq.rows)
    checked = reconcile_nasdaq_reference_rows(nasdaq, cat, pillar, pending, mappings["NASDAQ"], now)
    screened.update({row.row_key: row for row in checked})
    rows = tuple(screened[row.row_key] for row in nasdaq.rows) + nyse_rows
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
    parser.add_argument("--fixture", type=datetime.fromisoformat)
    args = parser.parse_args()
    if (args.rights is None) == (args.fixture is None):
        parser.error("Supply either current rights or an isolated fixture timestamp")
    inputs = (args.nasdaq, args.cat, args.pillar, args.mapping, args.rights)
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
