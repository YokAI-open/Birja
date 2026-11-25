"""Classify a listing from exact, corroborated issue-level evidence."""

import hashlib
import json
import re
from datetime import datetime, timedelta
from typing import Literal
from urllib.parse import urlsplit

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.services.stock_catalog_sources import (
    CatalogAlias,
    DirectoryRow,
    DirectorySource,
    ListingExchange,
)

Disposition = Literal["included", "excluded", "duplicate", "unresolved"]
Classification = Literal["common_stock", "ordinary_shares", "out_of_scope"]
SHA256 = r"^[0-9a-f]{64}$"
IDENTITY = r"^(figi:[A-Z]{2}[A-Z0-9]{9}[0-9]|review:[0-9a-f]{64})$"
_FIGI = re.compile(r"[A-Z]{2}[A-Z0-9]{9}[0-9]")
_CLASS = re.compile(r"\bClass ([A-Z][A-Z0-9]{0,4})\b", re.IGNORECASE)
CORROBORATION_AGE = timedelta(days=7)

_COMMON_TYPES: dict[str, Classification] = {
    "Common Stock": "common_stock",
    "Ordinary Shares": "ordinary_shares",
}
_EXCLUDED_TYPES = {
    "ADR",
    "American Depositary Receipt",
    "Closed-End Fund",
    "Depositary Receipt",
    "Depositary Share",
    "ETP",
    "ETF",
    "Fund",
    "GDR",
    "Global Depositary Receipt",
    "Mutual Fund",
    "Preference",
    "Preferred",
    "Preferred Stock",
    "REIT",
    "Right",
    "Rights",
    "Unit",
    "Units",
    "Warrant",
    "Warrants",
}
_REVIEW_HOSTS = {"www.sec.gov", "www.nasdaqtrader.com", "www.nasdaq.com", "www.nyse.com"}


class CatalogModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class InventoryRow(CatalogModel):
    source: DirectorySource
    row_key: str
    row_digest: str = Field(pattern=SHA256)
    ticker: str
    listing_exchange: ListingExchange | None
    company_name: str
    name_source: DirectorySource
    classification: Classification | None
    share_class: str | None
    identity_key: str | None = Field(pattern=IDENTITY)
    aliases: tuple[CatalogAlias, ...]
    disposition: Disposition
    reason: str
    evidence_digest: str = Field(pattern=SHA256)
    evidence_at: AwareDatetime | None = None


class ReviewedIssue(CatalogModel):
    source: DirectorySource
    row_digest: str = Field(pattern=SHA256)
    ticker: str
    listing_exchange: ListingExchange
    issue_group: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$")
    reviewed_at: AwareDatetime
    source_url: str
    classification: Classification
    evidence_digest: str = Field(pattern=SHA256)

    def matches(self, row: DirectoryRow, now: datetime) -> bool:
        url = urlsplit(self.source_url)
        return (
            self.source == row.source
            and self.row_digest == row.row_digest
            and self.ticker == row.ticker
            and self.listing_exchange == row.listing_exchange
            and url.scheme == "https"
            and url.netloc in _REVIEW_HOSTS
            and bool(url.path.removeprefix("/"))
            and timedelta(0) <= now - self.reviewed_at <= CORROBORATION_AGE
        )


def outcome(
    row: DirectoryRow,
    disposition: Disposition,
    reason: str,
    *,
    classification: Classification | None = None,
    identity: str | None = None,
    provider_ticker: str | None = None,
    evidence_digest: str | None = None,
    evidence_at: datetime | None = None,
) -> InventoryRow:
    aliases = row.aliases
    if provider_ticker is not None:
        aliases += (CatalogAlias(namespace="openfigi", symbol=provider_ticker),)
    share_class = _CLASS.search(row.company_name) if disposition == "included" else None
    return InventoryRow(
        source=row.source,
        row_key=row.row_key,
        row_digest=row.row_digest,
        ticker=row.ticker,
        listing_exchange=row.listing_exchange,
        company_name=row.company_name,
        name_source=row.source,
        classification=classification,
        share_class=share_class[1].upper() if share_class else None,
        identity_key=identity,
        aliases=aliases,
        disposition=disposition,
        reason=reason,
        evidence_digest=evidence_digest or row.row_digest,
        evidence_at=evidence_at,
    )


def classify_reviewed(row: DirectoryRow, review: ReviewedIssue, now: datetime) -> InventoryRow:
    if not review.matches(row, now):
        return outcome(row, "unresolved", "exception_binding_or_date_mismatch")
    classification = review.classification
    identity = hashlib.sha256(review.issue_group.encode()).hexdigest()
    return outcome(
        row,
        "excluded" if classification == "out_of_scope" else "included",
        "reviewed_issue_evidence",
        classification=classification,
        identity=None if classification == "out_of_scope" else f"review:{identity}",
        evidence_digest=review.evidence_digest,
        evidence_at=review.reviewed_at,
    )


def _figi_fields(candidate: dict[str, object], row: DirectoryRow) -> tuple[str, ...] | None:
    exchange = candidate.get("exchCode")
    ticker = candidate.get("ticker")
    sector = candidate.get("marketSector")
    kind = candidate.get("securityType")
    broad_type = candidate.get("securityType2")
    share_class = candidate.get("shareClassFIGI")
    composite = candidate.get("compositeFIGI")
    if (
        exchange != row.figi_exchange
        or sector != "Equity"
        or not isinstance(ticker, str)
        or ticker not in {alias.symbol for alias in row.aliases}
        or not isinstance(kind, str)
        or not isinstance(broad_type, str)
    ):
        return None
    if kind in _EXCLUDED_TYPES and broad_type not in _COMMON_TYPES:
        return ("excluded", ticker, kind, broad_type)
    classification = _COMMON_TYPES.get(kind)
    if (
        classification is None
        or broad_type not in _COMMON_TYPES
        or not isinstance(share_class, str)
        or _FIGI.fullmatch(share_class) is None
        or not isinstance(composite, str)
        or _FIGI.fullmatch(composite) is None
        or share_class == composite
    ):
        return None
    return (classification, ticker, share_class, composite)


def classify_mapping(row: DirectoryRow, result: object, now: datetime) -> InventoryRow:
    if not isinstance(result, dict):
        raise ValueError("Invalid mapping outcome")
    if set(result) == {"warning"} and isinstance(result["warning"], str):
        return outcome(row, "unresolved", "mapping_missing", evidence_at=now)
    if set(result) != {"data"} or not isinstance(result["data"], list):
        raise ValueError("Invalid or failed mapping outcome")
    candidates = result["data"]
    if (
        not candidates
        or len(candidates) > 100
        or any(not isinstance(item, dict) for item in candidates)
    ):
        raise ValueError("Invalid mapping candidate set")
    evidence = {_figi_fields(item, row) for item in candidates}
    fields = next(iter(evidence))
    if fields is None or len(evidence) != 1:
        return outcome(row, "unresolved", "mapping_conflict_or_unknown", evidence_at=now)
    digest = hashlib.sha256(json.dumps(fields, separators=(",", ":")).encode()).hexdigest()
    kind, ticker, share_class, _ = fields
    if kind == "excluded":
        return outcome(
            row,
            "excluded",
            "recognized_security_type",
            classification="out_of_scope",
            evidence_digest=digest,
            evidence_at=now,
        )
    return outcome(
        row,
        "included",
        "corroborated_share_class",
        classification=_COMMON_TYPES_KIND[kind],
        identity=f"figi:{share_class}",
        provider_ticker=ticker,
        evidence_digest=digest,
        evidence_at=now,
    )


_COMMON_TYPES_KIND: dict[str, Classification] = {
    "common_stock": "common_stock",
    "ordinary_shares": "ordinary_shares",
}
