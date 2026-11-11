"""Product-specific evidence values; runtime callers have no administration rights."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any, cast
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

FIELDS = {
    "reference": {"symbol", "name", "exchange", "provider_asset_id"},
    "quotes": {"bid", "ask", "event_at", "symbol"},
    "actions": {"provider_event_id", "symbol", "event_type", "process_date"},
    "status": {"symbol", "status", "event_at"},
    "calendar": {"exchange", "session_date", "opens_at", "closes_at"},
}
PURPOSES = {"collection", "display", "derived", "retention"}


def _utc(value: datetime | None) -> bool:
    return isinstance(value, datetime) and value.utcoffset() == timedelta(0)


def _text(value: object, limit: int) -> bool:
    return isinstance(value, str) and 0 < len(value.strip()) <= limit


def _official_url(value: object, exchange: str | None = None) -> bool:
    if not _text(value, 2048):
        return False
    parsed = urlsplit(str(value))
    hosts = {"XNYS": {"www.nyse.com", "nyse.com"}, "XNAS": {"www.nasdaq.com", "nasdaq.com"}}
    allowed = hosts[exchange] if exchange else set.union(*hosts.values())
    return (
        parsed.scheme == "https"
        and parsed.hostname in allowed
        and parsed.username is None
        and parsed.password is None
        and parsed.port in (None, 443)
    )


def _calendar_expiry(evidence: ProductAdmission, now: datetime) -> datetime:
    """Validate migrator-owned authority; sessions cannot supply these values."""
    data = evidence.calendar
    if sorted(data["exchanges"]) != ["XNAS", "XNYS"] or not _text(data["version"], 256):
        raise ValueError("calendar scope")
    sources = data["sources"]
    if not isinstance(sources, list) or not 2 <= len(sources) <= 8:
        raise ValueError("calendar provenance")
    if not all(_official_url(source) for source in sources) or not all(
        any(_official_url(source, exchange) for source in sources) for exchange in ("XNYS", "XNAS")
    ):
        raise ValueError("calendar provenance")
    review_until = datetime.fromisoformat(data["review_valid_until"])
    if (
        not _utc(review_until)
        or evidence.reviewed_at is None
        or not now < review_until <= evidence.reviewed_at + timedelta(hours=24)
    ):
        raise ValueError("calendar review")
    start = date.fromisoformat(data["coverage_start"])
    end = date.fromisoformat(data["coverage_end"])
    # The review fixes a bounded horizon; it is never renewed by a runtime write.
    reviewed_date = evidence.reviewed_at.astimezone(UTC).date()
    if not (
        reviewed_date - timedelta(days=45)
        <= start
        <= now.date()
        <= end
        <= reviewed_date + timedelta(days=90)
    ):
        raise ValueError("calendar coverage")
    overrides = data["overrides"]
    if not isinstance(overrides, list) or len(overrides) > 272:
        raise ValueError("calendar overrides")
    seen: set[tuple[str, date]] = set()
    for override in overrides:
        exchange = override["exchange"]
        day = date.fromisoformat(override["date"])
        identity = (exchange, day)
        if (
            exchange not in ("XNYS", "XNAS")
            or not start <= day <= end
            or identity in seen
            or not _official_url(override["source"], exchange)
        ):
            raise ValueError("calendar override provenance")
        seen.add(identity)
        if override["state"] == "closed":
            if override.get("opens_at") is not None or override.get("closes_at") is not None:
                raise ValueError("closed boundaries")
        elif override["state"] == "shortened":
            opens = datetime.fromisoformat(override["opens_at"])
            closes = datetime.fromisoformat(override["closes_at"])
            local_open = opens.astimezone(ZoneInfo("America/New_York"))
            local_close = closes.astimezone(ZoneInfo("America/New_York"))
            if (
                not _utc(opens)
                or not _utc(closes)
                or opens.date() != day
                or closes.date() != day
                or not timedelta(0) < closes - opens < timedelta(hours=6, minutes=30)
                or (local_open.hour, local_open.minute, local_open.second, local_open.microsecond)
                != (9, 30, 0, 0)
                or local_open.date() != day
                or local_close.date() != day
                or local_close.hour >= 16
            ):
                raise ValueError("shortened boundaries")
        else:
            raise ValueError("unsupported override")
    return review_until


@dataclass(frozen=True)
class ProductAdmission:
    product: str
    state: str = "denied"
    generation: int = 1
    reviewed_at: datetime | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    evidence_ref: str | None = field(default=None, repr=False)
    terms_version: str | None = field(default=None, repr=False)
    collection_allowed: bool = False
    display_allowed: bool = False
    derived_allowed: bool = False
    retention_allowed: bool = False
    scope: dict[str, Any] = field(default_factory=dict, repr=False)
    quota: dict[str, Any] = field(default_factory=dict, repr=False)
    allowed_fields: list[str] = field(default_factory=list)
    attribution: str = ""
    calendar: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class AdmissionDecision:
    allowed: bool
    reason: str
    generation: int | None = None
    valid_until: datetime | None = None
    attribution: str = ""


def evaluate_admission(
    evidence: ProductAdmission | None,
    product: str,
    purpose: str,
    now: datetime,
    *,
    expected_generation: int | None = None,
    account: str = "birja",
    server: str = "birja",
    feed: str = "iex",
    capability: str | None = None,
) -> AdmissionDecision:
    """Evaluate current committed evidence separately at every asynchronous boundary.

    Callers must reload after I/O, pass the generation used by their derived data,
    and obtain fresh UTC. This pure decision cannot revoke a previously returned
    object or replace transaction isolation. Account/server identify the reviewed
    deployment; credentials and an enable flag never participate in approval.
    """
    denied = AdmissionDecision(False, "unknown")
    if evidence is None or product not in FIELDS or purpose not in PURPOSES or not _utc(now):
        return denied
    try:
        if (
            evidence.product != product
            or evidence.state != "approved"
            or type(evidence.generation) is not int
            or evidence.generation <= 0
            or (expected_generation is not None and evidence.generation != expected_generation)
            or not all(
                _utc(value)
                for value in (evidence.reviewed_at, evidence.valid_from, evidence.valid_until)
            )
        ):
            return denied
        if not (
            cast(datetime, evidence.reviewed_at) <= now
            and cast(datetime, evidence.valid_from) <= now < cast(datetime, evidence.valid_until)
        ):
            return denied
        if (
            not _text(evidence.evidence_ref, 2048)
            or not _text(evidence.terms_version, 256)
            or getattr(evidence, f"{purpose}_allowed") is not True
            or not _text(evidence.attribution, 2048)
        ):
            return denied
        expected_scope = {
            "application": "birja",
            "audience": "authenticated-users",
            "account": account,
            "server": server,
            "feed": feed,
        }
        if (
            feed != ("alpaca-corporate-actions" if product == "actions" else "iex")
            or not account
            or not server
            or any(evidence.scope.get(key) != value for key, value in expected_scope.items())
        ):
            return denied
        if (
            not isinstance(evidence.allowed_fields, list)
            or not all(_text(value, 64) for value in evidence.allowed_fields)
            or len(evidence.allowed_fields) > 64
            or len(set(evidence.allowed_fields)) != len(evidence.allowed_fields)
            or not FIELDS[product].issubset(evidence.allowed_fields)
        ):
            return denied
        bounds = {
            "requests_per_minute": (1, 200),
            "symbols_per_request": (20, 1000),
            "max_response_bytes": (1, 1048576),
            "retention_seconds": (1, 315360000) if product == "actions" else (1, 86400),
        }
        if any(
            type(evidence.quota.get(key)) is not int or not low <= evidence.quota[key] <= high
            for key, (low, high) in bounds.items()
        ):
            return denied
        if product == "actions":
            from app.services.stock_quote_rules import CURATED_SYMBOLS

            scope = evidence.scope
            capabilities = scope.get("capabilities")
            symbols = scope.get("rest_symbols")
            if (
                not isinstance(capabilities, list)
                or not capabilities
                or any(value not in ("rest", "replay") for value in capabilities)
                or len(set(capabilities)) != len(capabilities)
                or "rest" not in capabilities
                or (capability is not None and capability not in capabilities)
                or not isinstance(symbols, list)
                or not all(isinstance(value, str) for value in symbols)
                or len(symbols) != 20
                or set(symbols) != CURATED_SYMBOLS
                or scope.get("durable_accounting") is not True
                or scope.get("backup_restore") is not True
                or scope.get("retention_mode") != "durable-accounting"
                or (
                    "replay" in capabilities
                    and (
                        scope.get("all_us_replay_ingress") is not True
                        or scope.get("replay_region") != "us"
                    )
                )
            ):
                return denied
        elif capability is not None:
            return denied
        expiry = cast(datetime, evidence.valid_until)
        if product == "calendar":
            expiry = min(expiry, _calendar_expiry(evidence, now))
        elif evidence.calendar:
            return denied
        return AdmissionDecision(
            True, "approved", evidence.generation, expiry, evidence.attribution
        )
    except KeyError, TypeError, ValueError, OverflowError, AttributeError:
        # Malformed operator JSON must never establish authority or leak its text.
        return denied
