"""Bounded immutable Alpaca observations, never financial health or DB effects.

Caller owns a verified-TLS client with zero transport retries, private headers,
trust_env=False and no redirecting hooks. No credentials/environment are read.
Public protocol source identity and bounded fixtures are pinned in the tests.
"""

import asyncio
import copy
import hashlib
import inspect
import json
import math
import random
import re
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, cast
from uuid import UUID

import httpx

from app.services.corporate_action_rules import NormalizedAction
from app.services.stock_admission import ProductAdmission, evaluate_admission
from app.services.stock_quote_rules import StockMapping, utc, verified_mapping

REST_URL = "https://data.alpaca.markets/v1/corporate-actions"
REPLAY_URL = "https://stream.data.alpaca.markets/v1beta1/events/corporate-actions"
_JITTER = random.SystemRandom().random
_TYPES = {
    "capital_gains_distributions": "capital_gains_distribution",
    "cash_dividends": "cash_dividend",
    "cash_mergers": "cash_merger",
    "forward_splits": "forward_split",
    "name_changes": "name_change",
    "partial_calls": "partial_call",
    "redemptions": "redemption",
    "reorganizations": "reorganization",
    "reverse_splits": "reverse_split",
    "rights_distributions": "rights_distribution",
    "spin_offs": "spin_off",
    "stock_and_cash_mergers": "stock_and_cash_merger",
    "stock_dividends": "stock_dividend",
    "stock_mergers": "stock_merger",
    "unit_splits": "unit_split",
    "worthless_removals": "worthless_removal",
}
_SYMBOL_FIELDS = (
    "symbol",
    "old_symbol",
    "new_symbol",
    "source_symbol",
    "alternate_symbol",
    "acquiree_symbol",
    "acquirer_symbol",
)
_ULID = re.compile(r"[0-7][0-9A-HJKMNP-TV-Z]{25}\Z")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
_STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)\Z")
EvidenceLoader = Callable[[], ProductAdmission | None | Awaitable[ProductAdmission | None]]
LeaseCheck = Callable[[], bool | Awaitable[bool]]
Capability = Literal["rest", "replay"]


class ActionError(Exception):
    """Only fixed, non-provider text crosses this boundary."""


@dataclass(frozen=True)
class ActionObservation:
    action: NormalizedAction
    mutation: Literal["snapshot", "insert", "update", "delete"] = "snapshot"
    cursor: str | None = None
    source_at: datetime | None = None


@dataclass(frozen=True)
class ActionCoverage:
    kind: Literal["process_date", "known_id", "replay"]
    start: str
    end: str
    complete: bool
    reason: str


@dataclass(frozen=True)
class ActionBatch:
    records: tuple[NormalizedAction, ...] = ()
    observations: tuple[ActionObservation, ...] = ()
    coverage: tuple[ActionCoverage, ...] = ()
    continuation: str | None = None
    complete: bool = False
    attempt_count: int = 0
    reason: str = "source_gap"


@dataclass
class ActionBudget:
    """Serial caller-owned cycle budget shared across discovery, IDs and replay."""

    max_attempts: int = 8
    max_pages: int = 20
    max_response_bytes: int = 262144
    max_total_bytes: int = 1048576
    total_seconds: float = 30
    attempt_seconds: float = 5
    max_mutations: int = 1024
    max_frame_bytes: int = 65536
    monotonic: Callable[[], float] = field(default=time.monotonic, repr=False)
    attempts: int = field(default=0, init=False)
    pages: int = field(default=0, init=False)
    total_bytes: int = field(default=0, init=False)
    mutations: int = field(default=0, init=False)
    _started: float | None = field(default=None, init=False, repr=False)
    _last_attempt: float | None = field(default=None, init=False, repr=False)
    _busy: bool = field(default=False, init=False, repr=False)

    def remaining(self) -> float:
        if self._started is None:
            self._started = self.monotonic()
        value = self.total_seconds - (self.monotonic() - self._started)
        if value <= 0:
            raise ActionError("cycle_budget")
        return value

    def validate(self) -> None:
        bounds = (
            (self.max_attempts, 8),
            (self.max_pages, 20),
            (self.max_response_bytes, 262144),
            (self.max_total_bytes, 1048576),
            (self.max_mutations, 1024),
            (self.max_frame_bytes, 65536),
        )
        if any(type(value) is not int or not 1 <= value <= limit for value, limit in bounds):
            raise ActionError("invalid_budget")
        if any(
            type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= limit
            for value, limit in ((self.total_seconds, 30), (self.attempt_seconds, 5))
        ):
            raise ActionError("invalid_budget")


async def _resolve[T](value: T | Awaitable[T]) -> T:
    return await value if inspect.isawaitable(value) else value


@dataclass
class _Context:
    http: httpx.AsyncClient
    mappings: Sequence[StockMapping]
    evidence: EvidenceLoader
    now: Callable[[], datetime]
    budget: ActionBudget
    lease: LeaseCheck
    sleep: Callable[[float], Awaitable[None]]
    account: str
    server: str
    capability: Capability
    initial: ProductAdmission | None = None

    async def guard(self) -> ProductAdmission:
        self.budget.remaining()
        if await _resolve(self.lease()) is not True:
            raise ActionError("lease")
        value = await _resolve(self.evidence())
        self.budget.remaining()
        if await _resolve(self.lease()) is not True:
            raise ActionError("lease")
        if value is None or any(
            not evaluate_admission(
                value,
                "actions",
                purpose,
                self.now(),
                expected_generation=self.initial.generation if self.initial else None,
                account=self.account,
                server=self.server,
                feed="alpaca-corporate-actions",
                capability=self.capability,
            ).allowed
            for purpose in ("collection", "derived", "retention")
        ):
            raise ActionError("admission")
        if self.initial is None:
            self.initial = copy.deepcopy(value)
        elif value != self.initial:
            raise ActionError("admission_changed")
        return value


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate")
        result[key] = value
    return result


def _number(value: str) -> Decimal:
    if len(value) > 64:
        raise ValueError("number")
    number = Decimal(value)
    parts = number.as_tuple()
    if not number.is_finite() or len(parts.digits) > 28 or not -8 <= int(parts.exponent) <= 18:
        raise ValueError("number")
    return number


def _constant(value: str) -> None:
    raise ValueError("constant")


def _decode(raw: bytes) -> Any:
    depth, quoted, escaped = 0, False, False
    for char in raw:
        if quoted:
            if escaped:
                escaped = False
            elif char == 92:
                escaped = True
            elif char == 34:
                quoted = False
        elif char == 34:
            quoted = True
        elif char in (91, 123):
            depth += 1
            if depth > 8:
                raise ActionError("response_depth")
        elif char in (93, 125):
            depth -= 1
    try:
        return json.loads(
            raw,
            parse_int=_number,
            parse_float=_number,
            parse_constant=_constant,
            object_pairs_hook=_pairs,
        )
    except ValueError, ArithmeticError, RecursionError:
        raise ActionError("invalid_json") from None


def _day(value: Any) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str) or _DATE.fullmatch(value) is None:
        raise ActionError("invalid_date")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ActionError("invalid_date") from None


def _stamp(value: Any) -> datetime:
    if not isinstance(value, str) or _STAMP.fullmatch(value) is None:
        raise ActionError("invalid_timestamp")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise ActionError("invalid_timestamp") from None


def _uuid(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 36:
        raise ActionError("invalid_identity")
    try:
        if str(UUID(value)) != value:
            raise ValueError
    except ValueError:
        raise ActionError("invalid_identity") from None
    return value


def _rate(value: Any, *, replay: bool) -> Decimal | None:
    if value is None:
        return None
    try:
        if replay and not isinstance(value, str):
            raise ValueError
        result = _number(value) if replay and isinstance(value, str) else value
        if not isinstance(result, Decimal) or not 0 < result < Decimal("1e12"):
            raise ValueError
        return result
    except ValueError, ArithmeticError:
        raise ActionError("invalid_rate") from None


def _normalize(
    entry: Any,
    event_type: str,
    ctx: _Context,
    *,
    replay: bool = False,
    cancelled: bool = False,
    source_at: datetime | None = None,
) -> tuple[NormalizedAction, ...]:
    if not isinstance(entry, dict):
        raise ActionError("invalid_record")
    identity = _uuid(entry.get("id"))
    symbols: set[str] = set()
    for key in _SYMBOL_FIELDS:
        if key in entry:
            symbol = entry[key]
            if not isinstance(symbol, str) or not 0 < len(symbol) <= 32 or symbol != symbol.strip():
                raise ActionError("invalid_symbol")
            symbols.add(symbol)
    if not symbols:
        raise ActionError("invalid_symbol")
    currency = entry.get("currency")
    if currency is not None and (
        not isinstance(currency, str)
        or len(currency) > 3
        or (currency != "" and re.fullmatch(r"[A-Z]{3}", currency) is None)
    ):
        raise ActionError("invalid_currency")
    dates = {
        key: _day(entry.get(key))
        for key in (
            "process_date",
            "ex_date",
            "record_date",
            "payable_date",
            "effective_date",
            "due_bill_on_date",
            "due_bill_off_date",
            "due_bill_redemption_date",
        )
    }
    for flag in ("foreign", "special"):
        if flag in entry and type(entry[flag]) is not bool:
            raise ActionError("invalid_record")
    subtype = entry.get("sub_type")
    if subtype is not None and subtype not in ("interest", "return_of_capital"):
        raise ActionError("invalid_subtype")
    rate = _rate(entry.get("rate"), replay=replay)
    new_rate = _rate(entry.get("new_rate"), replay=replay)
    old_rate = _rate(entry.get("old_rate"), replay=replay)
    result = []
    changed = event_type not in ("cash_dividend", "forward_split")
    for mapping in ctx.mappings:
        if mapping.symbol not in symbols:
            continue
        result.append(
            NormalizedAction(
                identity,
                mapping.coin_id,
                mapping.symbol,
                event_type,
                dates["process_date"],
                ctx.now(),
                source_event_at=source_at,
                currency=currency or None,
                rate=rate,
                new_rate=new_rate,
                old_rate=old_rate,
                ex_date=dates["ex_date"],
                record_date=dates["record_date"],
                payable_date=dates["payable_date"],
                subtype=subtype,
                foreign=entry.get("foreign"),
                special=entry.get("special"),
                due_bills=True
                if any(
                    dates[key] is not None
                    for key in ("due_bill_on_date", "due_bill_off_date", "due_bill_redemption_date")
                )
                else None,
                identity_verified=not changed,
                identity_changed=changed,
                cancelled=cancelled,
            )
        )
    return tuple(result)


def _token(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not 0 < len(value) <= 2048 or any(ord(c) < 32 for c in value):
        raise ActionError("invalid_cursor")
    return value


async def _pause(ctx: _Context, seconds: float) -> None:
    if seconds >= ctx.budget.remaining():
        raise ActionError("cycle_budget")
    if seconds > 0:
        await ctx.sleep(seconds)
    await ctx.guard()


async def _attempt(ctx: _Context) -> int:
    evidence = await ctx.guard()
    budget = ctx.budget
    if budget.attempts >= min(budget.max_attempts, evidence.quota["requests_per_minute"]):
        raise ActionError("attempt_budget")
    cadence = 60 / evidence.quota["requests_per_minute"]
    if budget._last_attempt is not None:
        await _pause(ctx, max(0, cadence - (budget.monotonic() - budget._last_attempt)))
    evidence = await ctx.guard()
    budget.attempts += 1
    budget._last_attempt = budget.monotonic()
    return min(budget.max_response_bytes, cast(int, evidence.quota["max_response_bytes"]))


async def _request(ctx: _Context, params: dict[str, str]) -> bytes:
    retry = False
    while True:
        limit = await _attempt(ctx)
        delay = 0.0
        try:
            async with asyncio.timeout(min(ctx.budget.remaining(), ctx.budget.attempt_seconds)):
                async with ctx.http.stream(
                    "GET",
                    REST_URL,
                    params=params,
                    follow_redirects=False,
                    timeout=ctx.budget.attempt_seconds,
                    headers={"Accept-Encoding": "identity"},
                ) as response:
                    await ctx.guard()
                    if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                        raise ActionError("content_encoding")
                    if response.status_code in (429, 500, 502, 503, 504):
                        try:
                            delay = float(_number(response.headers.get("Retry-After", "1")))
                        except ValueError, ArithmeticError:
                            raise ActionError("retry_after") from None
                        if not 0 <= delay <= 5:
                            raise ActionError("retry_after")
                        if retry:
                            raise ActionError("http_retry_exhausted")
                    elif response.status_code != 200:
                        raise ActionError("http_status")
                    else:
                        body = bytearray()
                        async for chunk in response.aiter_bytes():
                            await ctx.guard()
                            ctx.budget.total_bytes += len(chunk)
                            if len(body) + len(chunk) > limit:
                                raise ActionError("response_limit")
                            if ctx.budget.total_bytes > ctx.budget.max_total_bytes:
                                raise ActionError("byte_budget")
                            body.extend(chunk)
                        await ctx.guard()
                        return bytes(body)
        except httpx.TransportError:
            if retry:
                raise ActionError("transport") from None
            delay = 1
        except TimeoutError:
            raise ActionError("attempt_timeout") from None
        await _pause(ctx, max(1 + _JITTER(), delay))
        retry = True


def _context(
    http: httpx.AsyncClient,
    mappings: Sequence[StockMapping],
    evidence: EvidenceLoader,
    now: Callable[[], datetime],
    budget: ActionBudget,
    lease: LeaseCheck,
    sleep: Callable[[float], Awaitable[None]],
    account: str,
    server: str,
    capability: Capability,
) -> _Context:
    budget.validate()
    if budget._busy:
        raise ActionError("concurrent_budget")
    if (
        http.trust_env
        or "last-event-id" in http.headers
        or not utc(now())
        or not 1 <= len(mappings) <= 20
        or not all(verified_mapping(mapping, now()) for mapping in mappings)
        or len({mapping.symbol for mapping in mappings}) != len(mappings)
        or len({mapping.coin_id for mapping in mappings}) != len(mappings)
        or len({mapping.provider_asset_id for mapping in mappings}) != len(mappings)
    ):
        raise ActionError("invalid_request")
    budget._busy = True
    return _Context(
        http, tuple(mappings), evidence, now, budget, lease, sleep, account, server, capability
    )


def _batch(
    rows: list[ActionObservation],
    coverage: tuple[ActionCoverage, ...],
    continuation: str | None,
    complete: bool,
    budget: ActionBudget,
    reason: str,
) -> ActionBatch:
    return ActionBatch(
        tuple(row.action for row in rows),
        tuple(rows),
        coverage,
        continuation,
        complete,
        budget.attempts,
        reason,
    )


async def _rest(
    ctx: _Context,
    params: dict[str, str],
    coverage: ActionCoverage,
    ids: Mapping[str, str] | None = None,
    initial_token: str | None = None,
) -> ActionBatch:
    rows: list[ActionObservation] = []
    token = initial_token
    seen_tokens: set[str] = {initial_token} if initial_token is not None else set()
    seen_ids: set[str] = set()
    try:
        async with asyncio.timeout(ctx.budget.remaining()):
            while True:
                if ctx.budget.pages >= ctx.budget.max_pages:
                    raise ActionError("page_budget")
                body = _decode(
                    await _request(ctx, params | ({"page_token": token} if token else {}))
                )
                if not isinstance(body, dict) or set(body) != {
                    "corporate_actions",
                    "next_page_token",
                }:
                    raise ActionError("invalid_body")
                groups = body["corporate_actions"]
                if not isinstance(groups, dict) or groups.keys() - _TYPES.keys():
                    raise ActionError("unknown_schema")
                page: list[ActionObservation] = []
                count = 0
                for group, entries in groups.items():
                    if not isinstance(entries, list):
                        raise ActionError("invalid_body")
                    count += len(entries)
                    if count > 1000:
                        raise ActionError("record_limit")
                    for entry in entries:
                        normalized = _normalize(entry, _TYPES[group], ctx)
                        event_id = _uuid(entry.get("id"))
                        if event_id in seen_ids:
                            raise ActionError("duplicate_identity")
                        seen_ids.add(event_id)
                        if not normalized or (
                            ids is not None
                            and (
                                event_id not in ids
                                or {row.symbol for row in normalized} != {ids[event_id]}
                            )
                        ):
                            raise ActionError("unexpected_identity")
                        if ids is None and any(
                            row.process_date is None
                            or not coverage.start <= row.process_date.isoformat() <= coverage.end
                            for row in normalized
                        ):
                            raise ActionError("outside_window")
                        page.extend(ActionObservation(row) for row in normalized)
                next_token = _token(body["next_page_token"])
                if next_token is not None and next_token in seen_tokens:
                    raise ActionError("cursor_loop")
                await ctx.guard()
                ctx.budget.pages += 1
                rows.extend(page)
                token = next_token
                if token is None:
                    missing = tuple(
                        ActionCoverage(
                            "known_id", identity, identity, False, "missing_or_uncertain"
                        )
                        for identity in sorted(set(ids or {}) - seen_ids)
                    )
                    completed = ActionCoverage(
                        coverage.kind, coverage.start, coverage.end, True, "pages_exhausted"
                    )
                    return _batch(
                        rows,
                        (completed, *missing),
                        None,
                        not missing,
                        ctx.budget,
                        "missing_or_uncertain" if missing else "pages_exhausted",
                    )
                seen_tokens.add(token)
    except ActionError as exc:
        reason = str(exc)
    except TimeoutError:
        reason = "cycle_budget"
    if reason in ("admission", "admission_changed", "lease"):
        rows.clear()
    return _batch(rows, (coverage,), token, False, ctx.budget, reason)


async def fetch_action_snapshot(
    http: httpx.AsyncClient,
    mappings: Sequence[StockMapping],
    evidence: EvidenceLoader,
    now: Callable[[], datetime],
    budget: ActionBudget,
    *,
    start: date,
    end: date,
    lease: LeaseCheck = lambda: True,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    account: str = "birja",
    server: str = "birja",
    page_token: str | None = None,
) -> ActionBatch:
    """Exhaust inclusive process-date pages; this does not prove financial health."""
    try:
        if type(start) is not date or type(end) is not date or not start <= end:
            raise ActionError("invalid_window")
        page_token = _token(page_token)
        ctx = _context(http, mappings, evidence, now, budget, lease, sleep, account, server, "rest")
    except ActionError as exc:
        return ActionBatch(attempt_count=budget.attempts, reason=str(exc))
    try:
        return await _rest(
            ctx,
            {
                "symbols": ",".join(sorted(mapping.symbol for mapping in mappings)),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "region": "us",
                "data_quality": "all",
                "limit": "1000",
                "sort": "asc",
            },
            ActionCoverage("process_date", start.isoformat(), end.isoformat(), False, "source_gap"),
            initial_token=page_token,
        )
    finally:
        budget._busy = False


async def recheck_action_ids(
    http: httpx.AsyncClient,
    mappings: Sequence[StockMapping],
    evidence: EvidenceLoader,
    now: Callable[[], datetime],
    budget: ActionBudget,
    *,
    ids: Mapping[str, str],
    lease: LeaseCheck = lambda: True,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    account: str = "birja",
    server: str = "birja",
) -> ActionBatch:
    """Known-ID absence is uncertain; never fabricate deletion/cancellation."""
    try:
        if not 1 <= len(ids) <= 1000:
            raise ActionError("invalid_ids")
        symbols = {mapping.symbol for mapping in mappings}
        for identity, symbol in ids.items():
            _uuid(identity)
            if symbol not in symbols:
                raise ActionError("invalid_ids")
        ctx = _context(http, mappings, evidence, now, budget, lease, sleep, account, server, "rest")
    except ActionError as exc:
        return ActionBatch(attempt_count=budget.attempts, reason=str(exc))
    try:
        return await _rest(
            ctx,
            {"ids": ",".join(sorted(ids)), "limit": "1000"},
            ActionCoverage("known_id", "", "", False, "source_gap"),
            dict(ids),
        )
    finally:
        budget._busy = False


def _cursor(value: Any) -> str:
    if not isinstance(value, str) or _ULID.fullmatch(value) is None:
        raise ActionError("invalid_cursor")
    return value


def _ulid_millis(value: str) -> int:
    result = 0
    for character in value[:10]:
        result = result * 32 + "0123456789ABCDEFGHJKMNPQRSTVWXYZ".index(character)
    return result


def _mutation_frame(
    data: bytes,
    ctx: _Context,
    seen: dict[str, bytes],
    last: str | None,
    since: datetime | None,
    until: datetime | None,
    since_id: str | None,
    until_id: str | None,
) -> tuple[list[ActionObservation], str | None, bool]:
    entries = _decode(data)
    if not isinstance(entries, list) or not entries:
        raise ActionError("invalid_frame")
    rows: list[ActionObservation] = []
    terminal = False
    for entry in entries:
        ctx.budget.mutations += 1
        if ctx.budget.mutations > ctx.budget.max_mutations:
            raise ActionError("mutation_budget")
        if not isinstance(entry, dict) or set(entry) != {
            "event_id",
            "at",
            "action",
            "region",
            "event_type",
            "ca",
        }:
            raise ActionError("invalid_envelope")
        cursor = _cursor(entry["event_id"])
        event_at = _stamp(entry["at"])
        mutation = entry["action"]
        name = entry["event_type"]
        if (
            mutation not in ("insert", "update", "delete")
            or entry["region"] != "us"
            or not isinstance(name, str)
            or not name.endswith("_corporateaction_event")
            or event_at > ctx.now()
        ):
            raise ActionError("invalid_envelope")
        kind = name.removesuffix("_corporateaction_event")
        if kind == "equity_partial_call":
            kind = "partial_call"
        if kind not in _TYPES.values():
            raise ActionError("unknown_schema")
        if (since is not None and (event_at < since or event_at > cast(datetime, until))) or (
            since_id is not None and (cursor < since_id or cursor > cast(str, until_id))
        ):
            raise ActionError("outside_window")
        # Digests are transient deduplication, never persisted provider payloads.
        digest = hashlib.sha256(json.dumps(entry, sort_keys=True, default=str).encode()).digest()
        if cursor in seen:
            if seen[cursor] != digest:
                raise ActionError("cursor_conflict")
            continue
        if last is not None and cursor <= last:
            raise ActionError("cursor_order")
        actions = _normalize(
            entry["ca"], kind, ctx, replay=True, cancelled=mutation == "delete", source_at=event_at
        )
        rows.extend(ActionObservation(action, mutation, cursor, event_at) for action in actions)
        seen[cursor] = digest
        last = cursor
        terminal = terminal or cursor == until_id
    return rows, last, terminal


async def _replay(
    ctx: _Context,
    params: dict[str, str],
    coverage: ActionCoverage,
    since: datetime | None,
    until: datetime | None,
    since_id: str | None,
    until_id: str | None,
) -> ActionBatch:
    rows: list[ActionObservation] = []
    last: str | None = None
    seen: dict[str, bytes] = {}
    terminal = False
    try:
        # Replay never reconnects automatically: validated partial frames/cursors
        # are returned as incomplete, for the durable consumer to reconcile.
        async with asyncio.timeout(ctx.budget.remaining()):
            limit = await _attempt(ctx)
            async with asyncio.timeout(min(ctx.budget.remaining(), ctx.budget.attempt_seconds)):
                async with ctx.http.stream(
                    "GET",
                    REPLAY_URL,
                    params=params,
                    follow_redirects=False,
                    timeout=ctx.budget.attempt_seconds,
                    headers={"Accept": "text/event-stream", "Accept-Encoding": "identity"},
                ) as response:
                    await ctx.guard()
                    if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                        raise ActionError("content_encoding")
                    if response.status_code != 200:
                        raise ActionError("replay_unavailable")
                    if (
                        response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                        != "text/event-stream"
                    ):
                        raise ActionError("content_type")
                    buffer = bytearray()
                    frame: list[bytes] = []
                    frame_size = 0
                    response_size = 0
                    async for chunk in response.aiter_bytes():
                        await ctx.guard()
                        response_size += len(chunk)
                        ctx.budget.total_bytes += len(chunk)
                        if response_size > limit:
                            raise ActionError("response_limit")
                        if ctx.budget.total_bytes > ctx.budget.max_total_bytes:
                            raise ActionError("byte_budget")
                        # Byte-by-byte framing bounds both lines and whole frames
                        # without buffering an arbitrary stream before decoding.
                        for byte in chunk:
                            frame_size += 1
                            if frame_size > ctx.budget.max_frame_bytes:
                                raise ActionError("frame_limit")
                            if byte != 10:
                                buffer.append(byte)
                                continue
                            line = bytes(buffer).removesuffix(b"\r")
                            buffer.clear()
                            if line:
                                frame.append(line)
                                continue
                            data: list[bytes] = []
                            for field in frame:
                                if field.startswith(b":"):
                                    continue
                                key, separator, value = field.partition(b":")
                                if not separator or key not in (b"data", b"id", b"event"):
                                    raise ActionError("invalid_framing")
                                if key == b"data":
                                    data.append(value.removeprefix(b" "))
                            if data:
                                page, next_cursor, reached = _mutation_frame(
                                    b"\n".join(data),
                                    ctx,
                                    seen,
                                    last,
                                    since,
                                    until,
                                    since_id,
                                    until_id,
                                )
                                await ctx.guard()
                                rows.extend(page)
                                last = next_cursor
                                terminal = terminal or reached
                            frame.clear()
                            frame_size = 0
                    await ctx.guard()
                    if buffer or frame:
                        raise ActionError("truncated_frame")
                    if until_id is not None and not terminal:
                        raise ActionError("source_gap")
                    # Timestamp mode's normal protocol EOF is the documented
                    # inclusive historical until close, NOT an idle timeout.
                    completed = ActionCoverage(
                        "replay",
                        coverage.start,
                        coverage.end,
                        True,
                        "terminal_id" if until_id else "historical_until_close",
                    )
                    return _batch(rows, (completed,), last, True, ctx.budget, completed.reason)
    except ActionError as exc:
        reason = str(exc)
    except httpx.TransportError:
        reason = "source_gap"
    except TimeoutError:
        reason = "replay_timeout"
    if reason in ("admission", "admission_changed", "lease"):
        rows.clear()
        last = None
    return _batch(rows, (coverage,), last, False, ctx.budget, reason)


async def replay_action_mutations(
    http: httpx.AsyncClient,
    mappings: Sequence[StockMapping],
    evidence: EvidenceLoader,
    now: Callable[[], datetime],
    budget: ActionBudget,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    since_id: str | None = None,
    until_id: str | None = None,
    lease: LeaseCheck = lambda: True,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    account: str = "birja",
    server: str = "birja",
) -> ActionBatch:
    """One finite, separately admitted all-US historical replay; no live worker.

    ID mode requires the exact inclusive terminal emission. Timestamp mode
    requires normal HTTP EOF on the documented historical-until request and
    fully terminated frames. HTTP errors, truncation, idle timeout or missing
    terminal ID never prove coverage. Local retained observations are curated.
    """
    try:
        if since_id is not None or until_id is not None:
            if since is not None or until is not None:
                raise ActionError("invalid_window")
            _cursor(since_id)
            _cursor(until_id)
            if cast(str, since_id) > cast(str, until_id) or _ulid_millis(cast(str, until_id)) > int(
                now().timestamp() * 1000
            ):
                raise ActionError("invalid_window")
            params = {
                "since_id": cast(str, since_id),
                "until_id": cast(str, until_id),
                "region": "us",
            }
            first, final = cast(str, since_id), cast(str, until_id)
        else:
            if (
                not utc(since)
                or not utc(until)
                or not cast(datetime, since) <= cast(datetime, until) <= now()
            ):
                raise ActionError("invalid_window")
            first, final = cast(datetime, since).isoformat(), cast(datetime, until).isoformat()
            params = {"since": first, "until": final, "region": "us"}
        ctx = _context(
            http, mappings, evidence, now, budget, lease, sleep, account, server, "replay"
        )
    except ActionError as exc:
        return ActionBatch(attempt_count=budget.attempts, reason=str(exc))
    try:
        return await _replay(
            ctx,
            params,
            ActionCoverage("replay", first, final, False, "source_gap"),
            since,
            until,
            since_id,
            until_id,
        )
    finally:
        budget._busy = False
