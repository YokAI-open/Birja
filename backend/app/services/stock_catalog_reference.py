"""Reconcile reusable NYSE issue metadata against primary listing and class facts."""

import hashlib
import json
import re
from collections.abc import Mapping
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pydantic import AwareDatetime, Field

from app.services.stock_catalog_classification import (
    CORROBORATION_AGE,
    CatalogModel,
    Classification,
    InventoryRow,
    outcome,
)
from app.services.stock_catalog_pillar import CatSnapshot, PillarIssue, PillarSnapshot
from app.services.stock_catalog_sources import (
    SYMBOL_PATTERN,
    CatalogAlias,
    CatalogSourceError,
    DirectoryRow,
    DirectorySnapshot,
)

_FIGI = re.compile(r"[A-Z]{2}[A-Z0-9]{9}[0-9]")
# These are issue wrappers in the mapping, not a class decision. Primary
# listing evidence distinguishes common shares of such issuers from other issues.
_COMMON_ISSUER_WRAPPERS = {"REIT", "Foreign Sh."}
_NONCOMMON_TYPES = {
    ("Closed-End Fund", "Mutual Fund"),
    ("Ltd Part", "Partnership Shares"),
    ("MLP", "Partnership Shares"),
    ("Royalty Trst", "Common Stock"),
    ("Unit", "Unit"),
}
_NASDAQ_TIERS = {"UQ", "UR", "UW"}
_MappingIdentity = tuple[str, str, str, str, str]


class ReferenceMapping(CatalogModel):
    observed_at: AwareDatetime
    result: dict[str, object] = Field(max_length=1)


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _primary_aliases(issue: PillarIssue) -> tuple[str, ...]:
    return tuple(
        symbol
        for symbol in dict.fromkeys(
            (issue.cqs_symbol, issue.venue_symbol, preferred_openfigi_symbol(issue))
        )
        if re.fullmatch(SYMBOL_PATTERN, symbol) is not None
    )


def preferred_openfigi_symbol(issue: PillarIssue) -> str:
    """Translate only a verified primary NYSE share-class suffix to OpenFIGI."""
    share_class = re.fullmatch(r"([A-Z0-9]+)\.([A-Z])", issue.cqs_symbol)
    if (
        issue.listing_exchange == "NYSE"
        and issue.common_class is not None
        and share_class is not None
        and issue.venue_symbol == f"{share_class[1]} {share_class[2]}"
    ):
        return f"{share_class[1]}/{share_class[2]}"
    return issue.cqs_symbol


def _matching_result(
    result: dict[str, object], aliases: tuple[str, ...], exchange: str
) -> _MappingIdentity | None:
    rows = result.get("data")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        return None

    matches: set[_MappingIdentity] = set()
    for item in rows:
        if not isinstance(item, dict):
            return None
        ticker, name = item.get("ticker"), item.get("name")
        share_class, composite = item.get("shareClassFIGI"), item.get("compositeFIGI")
        kind, broad_type = item.get("securityType"), item.get("securityType2")
        venue_code = item.get("exchCode")
        if (
            venue_code != exchange
            or item.get("marketSector") != "Equity"
            or ticker not in aliases
            or not isinstance(ticker, str)
            or not isinstance(kind, str)
            or not isinstance(broad_type, str)
            or not isinstance(name, str)
            or not isinstance(share_class, str)
            or _FIGI.fullmatch(share_class) is None
            or not isinstance(composite, str)
            or _FIGI.fullmatch(composite) is None
            or composite == share_class
        ):
            # A conflicting same-query response must not silently disappear.
            return None
        name = name.strip()
        if not name or len(name) > 255 or not name.isprintable():
            return None
        if (kind, broad_type) in _NONCOMMON_TYPES:
            matches.add((ticker, name, share_class, composite, "out_of_scope"))
        elif kind in (
            {"Common Stock", "Ordinary Shares"} | _COMMON_ISSUER_WRAPPERS
        ) and broad_type in {"Common Stock", "Ordinary Shares", "REIT"}:
            matches.add((ticker, name, share_class, composite, "common"))
        else:
            return None
    return matches.pop() if len(matches) == 1 else None


def _matching_fallback(
    fallback: object, aliases: tuple[str, ...], primary_exchange: str
) -> _MappingIdentity | None:
    if (
        primary_exchange not in _NASDAQ_TIERS
        or not isinstance(fallback, dict)
        or set(fallback) != {"primary", "alternates"}
        or fallback["primary"] != {"warning": "No current mapping"}
    ):
        return None
    alternates = fallback["alternates"]
    expected = sorted(_NASDAQ_TIERS - {primary_exchange}) + ["US"]
    if not isinstance(alternates, list) or len(alternates) != len(expected):
        return None
    matches = {}
    for code, alternate in zip(expected, alternates, strict=True):
        if (
            not isinstance(alternate, dict)
            or set(alternate) != {"exchange", "result"}
            or alternate["exchange"] != code
            or not isinstance(alternate["result"], dict)
        ):
            return None
        if alternate["result"] == {"warning": "No current mapping"}:
            continue
        entry = _matching_result(alternate["result"], aliases, code)
        if entry is None:
            return None
        matches[code] = entry
    composite = matches.pop("US", None)
    if composite is None or not matches:
        return None
    # Alternate tier and composite records must refer to the same share class.
    selected = next(iter(matches.values()))
    identity = (selected[0], *selected[2:])
    if any((entry[0], *entry[2:]) != identity for entry in (*matches.values(), composite)):
        return None
    return selected


def _matching_mapping(
    mapping: ReferenceMapping, aliases: tuple[str, ...], exchange: str, now: datetime
) -> _MappingIdentity | None:
    if not timedelta(0) <= now - mapping.observed_at <= CORROBORATION_AGE:
        return None
    if "fallback" in mapping.result:
        return _matching_fallback(mapping.result["fallback"], aliases, exchange)
    return _matching_result(mapping.result, aliases, exchange)


def _classify(
    row: DirectoryRow,
    issue: PillarIssue | None,
    mappings: Mapping[str, ReferenceMapping],
    now: datetime,
) -> tuple[DirectoryRow, InventoryRow]:
    if issue is None:
        return row, outcome(row, "unresolved", "primary_listing_comparison_missing")
    classification: Classification | None = issue.common_class
    if classification is None:
        return row, outcome(
            row, "excluded", "primary_listing_noncommon_class", classification="out_of_scope"
        )
    aliases = _primary_aliases(issue)
    if row.figi_exchange is None:
        return row, outcome(row, "unresolved", "mapping_venue_missing")
    source_mappings = [mappings[symbol] for symbol in aliases if symbol in mappings]
    if not source_mappings:
        return row, outcome(row, "unresolved", "mapping_pending")
    matched = [
        (_matching_mapping(value, aliases, row.figi_exchange, now), value.observed_at)
        for value in source_mappings
        if set(value.result) != {"warning"}
    ]
    identified = {value for value, _ in matched}
    if len(identified) != 1 or (resolved := identified.pop()) is None:
        return row, outcome(row, "unresolved", "mapping_conflict_or_unknown")
    ticker, name, identity, composite, asset_type = resolved
    observed_at = min(at for _, at in matched)
    if asset_type == "out_of_scope":
        return row, outcome(
            row,
            "excluded",
            "corroborated_noncommon_class",
            classification="out_of_scope",
            evidence_digest=_digest([row.row_digest, resolved]),
            evidence_at=observed_at,
        )
    licensed = (
        DirectoryRow(
            source=row.source,
            row_key=row.row_key,
            row_digest=row.row_digest,
            ticker=issue.cqs_symbol,
            listing_exchange=row.listing_exchange,
            company_name=name,
            aliases=(CatalogAlias(namespace="openfigi", symbol=ticker),),
            figi_exchange="UN",
            exclusion=None,
        )
        if row.source == "openfigi_nyse"
        else row
    )
    return licensed, outcome(
        licensed,
        "included",
        "corroborated_share_class",
        classification=classification,
        identity=f"figi:{identity}",
        provider_ticker=ticker if licensed is row else None,
        evidence_digest=_digest(
            [row.row_digest, classification, ticker, name, identity, composite]
        ),
        evidence_at=observed_at,
    )


def reconcile_nyse_reference(
    cat: CatSnapshot,
    pillar: PillarSnapshot,
    mappings: Mapping[str, ReferenceMapping],
    now: datetime,
) -> tuple[DirectorySnapshot, tuple[InventoryRow, ...]]:
    """Cover every current non-test NYSE primary key with an explicit disposition."""
    if cat.trade_date != pillar.trade_date or not timedelta(0) <= (
        now - cat.published_at
    ) <= timedelta(days=4):
        raise CatalogSourceError("Reference evidence is stale or uses different trade dates")
    keys = sorted(symbol for venue, symbol in cat.keys if venue == "NYSE")
    if not keys:
        raise CatalogSourceError("Reference evidence has no NYSE primary keys")
    index = pillar.index_by_venue_symbol()
    expected = {
        symbol
        for (venue, symbol), issue in index.items()
        if venue == "NYSE" and issue.common_class is not None
    }
    if expected.difference(keys, cat.test_symbols):
        raise CatalogSourceError("NYSE references disagree on an active common issue")
    rows: list[DirectoryRow] = []
    results: list[InventoryRow] = []
    for ordinal, symbol in enumerate(keys, 1):
        issue = index.get(("NYSE", symbol))
        # Comparator keys can contain punctuation unsuitable for public ticker routes.
        # Only a corroborated OpenFIGI ticker and name can become published fields.
        row = DirectoryRow(
            source="openfigi_nyse",
            row_key=f"openfigi_nyse:{ordinal}",
            row_digest=_digest([cat.sha256, pillar.sha256, symbol]),
            ticker="",
            listing_exchange="NYSE",
            company_name="",
            aliases=(),
            figi_exchange="UN",
            exclusion=None,
        )
        normalized, audit = _classify(row, issue, mappings, now)
        rows.append(normalized)
        results.append(audit)
    source_sha = _digest([cat.sha256, pillar.sha256])
    return (
        DirectorySnapshot("openfigi_nyse", source_sha, cat.published_at, tuple(rows)),
        tuple(results),
    )


def reconcile_nasdaq_reference_rows(
    nasdaq: DirectorySnapshot,
    cat: CatSnapshot,
    pillar: PillarSnapshot,
    candidates: list[DirectoryRow],
    mappings: Mapping[str, ReferenceMapping],
    now: datetime,
) -> tuple[InventoryRow, ...]:
    """Check Nasdaq candidates against their primary security class."""
    if (
        nasdaq.artifact != "nasdaqlisted"
        or nasdaq.published_at.astimezone(ZoneInfo("America/New_York")).date() != pillar.trade_date
    ):
        raise CatalogSourceError("Reference evidence uses different trade dates")
    index = pillar.index_by_venue_symbol()
    directory_keys = {row.ticker for row in nasdaq.rows}
    expected = {
        symbol
        for (venue, symbol), issue in index.items()
        if venue == "NASDAQ" and issue.common_class is not None
    }
    if expected.difference(directory_keys, cat.test_symbols):
        raise CatalogSourceError("Nasdaq references disagree on an active common issue")
    return tuple(
        _classify(row, index.get(("NASDAQ", row.ticker)), mappings, now)[1] for row in candidates
    )
