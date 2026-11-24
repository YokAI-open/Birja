"""Bounded scheduler work for selected display quotes."""

import asyncio
import logging
import secrets
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime

import httpx
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import SchedulerSettings
from app.services.alpaca import AlpacaError, fetch_catalog_iex_quotes
from app.services.stock_catalog_quote_demand import (
    CatalogQuoteOutcome,
    CatalogQuoteRequest,
    complete_catalog_quote,
    current_catalog_quote_request,
    pending_catalog_quotes,
)
from app.services.stock_catalog_quotes import (
    CatalogQuoteBinding,
    CatalogQuoteContext,
    load_catalog_quote_context,
    publish_catalog_quote,
)
from app.tasks.scheduler import CycleResult
from app.tasks.stock_scheduler import _admissions, reserve_account_attempt

CATALOG_LOCK_KEY = "sim:lock:stock-catalog-quote"
_BATCH_SIZE = 8
_WORK_SECONDS = 6
_LOCK_MS = 10_000
_RELEASE_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""
logger = logging.getLogger(__name__)


def _binding_for(
    request: CatalogQuoteRequest, context: CatalogQuoteContext, now: datetime
) -> CatalogQuoteBinding | None:
    binding, decision = context.binding, context.session
    current = decision.current
    if (
        binding is None
        or binding.catalog_id != request.catalog_id
        or binding.listing_version != request.listing_version
        or binding.fingerprint != request.fingerprint
        or now >= binding.valid_until
        or decision.state != "open"
        or decision.valid_until is None
        or now >= decision.valid_until
        or current is None
        or current.opens_at is None
        or current.closes_at is None
        or not current.opens_at <= now < current.closes_at
    ):
        return None
    return binding


_BoundRequest = tuple[CatalogQuoteRequest, CatalogQuoteBinding]


async def _select_batch(
    sessionmaker: async_sessionmaker[AsyncSession],
    settings: SchedulerSettings,
    requests: tuple[CatalogQuoteRequest, ...],
    now: Callable[[], datetime],
) -> tuple[list[_BoundRequest], list[CatalogQuoteRequest]]:
    selected: list[_BoundRequest] = []
    refused: list[CatalogQuoteRequest] = []
    async with sessionmaker() as db:
        for request in requests:
            context = await load_catalog_quote_context(db, settings, request.catalog_id, now=now())
            binding = _binding_for(request, context, now())
            if binding is None:
                refused.append(request)
            else:
                selected.append((request, binding))

    # The provider response is symbol-keyed. Ambiguous aliases cannot share
    # a price or displace another selected catalog identity.
    symbol_counts = Counter(binding.provider_symbol for _, binding in selected)
    refused.extend(
        request for request, binding in selected if symbol_counts[binding.provider_symbol] > 1
    )
    selected = [
        (request, binding)
        for request, binding in selected
        if symbol_counts[binding.provider_symbol] == 1
    ]
    if selected:
        limit = min(binding.symbols_per_request for _, binding in selected)
        selected = selected[:limit]
    return selected, refused


async def _refresh(
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    http: httpx.AsyncClient,
    settings: SchedulerSettings,
    selected: list[_BoundRequest],
    now: Callable[[], datetime],
    lock_token: str,
) -> int:
    account, server = settings.stock_data_account, settings.stock_data_server
    quota = min(binding.requests_per_minute for _, binding in selected)
    attempt_bytes = min(binding.max_response_bytes for _, binding in selected)

    async def before_attempt() -> None:
        # Every attempt reads fresh committed evidence and closes the transaction.
        async with sessionmaker() as db:
            evidence = await _admissions(db)
            contexts = [
                await load_catalog_quote_context(db, settings, request.catalog_id, now=now())
                for request, _ in selected
            ]
        if await redis.get(CATALOG_LOCK_KEY) != lock_token:
            raise AlpacaError("failed_check")
        for request, _ in selected:
            if not await current_catalog_quote_request(
                redis, request, account=account, server=server
            ):
                raise AlpacaError("failed_check")
        checked_at = now()
        if any(
            _binding_for(request, context, checked_at) != binding
            for (request, binding), context in zip(selected, contexts, strict=True)
        ):
            raise AlpacaError("failed_check")
        if not await reserve_account_attempt(redis, settings, evidence, at=checked_at, cap=quota):
            raise AlpacaError("account_budget")
        ready_at = now()
        if any(
            _binding_for(request, context, ready_at) != binding
            for (request, binding), context in zip(selected, contexts, strict=True)
        ):
            raise AlpacaError("failed_check")

    try:
        prices = await fetch_catalog_iex_quotes(
            http,
            {binding.provider_symbol: binding.listing_exchange for _, binding in selected},
            now,
            before_attempt=before_attempt,
            attempts=min(settings.stock_max_retries + 1, quota),
            max_bytes=min(attempt_bytes, settings.stock_max_response_bytes),
            budget_seconds=min(_WORK_SECONDS, settings.stock_cycle_budget_seconds),
        )
    except AlpacaError as exc:
        reason: CatalogQuoteOutcome
        if exc.status == 429 or str(exc) == "account_budget":
            reason = "throttled"
        elif str(exc) == "failed_check":
            reason = "failed_check"
        else:
            reason = "source_error"
        for request, _ in selected:
            await complete_catalog_quote(
                redis, request, account=account, server=server, reason=reason
            )
        return 0

    accepted = 0
    for request, binding in selected:
        async with sessionmaker() as db:
            context = await load_catalog_quote_context(db, settings, request.catalog_id, now=now())
        price = prices.get(binding.provider_symbol)
        owned = await redis.get(CATALOG_LOCK_KEY) == lock_token
        checked_at = now()
        if not owned or _binding_for(request, context, checked_at) != binding:
            reason = "failed_check"
        elif price is not None and await publish_catalog_quote(
            redis,
            request,
            binding,
            context.session,
            price,
            account=account,
            server=server,
            now=checked_at,
        ):
            accepted += 1
            continue
        else:
            reason = "quote_unavailable"
        await complete_catalog_quote(redis, request, account=account, server=server, reason=reason)
    return accepted


async def run_catalog_quote_cycle(
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    http: httpx.AsyncClient,
    settings: SchedulerSettings,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> CycleResult:
    if not settings.stock_data_enabled:
        return CycleResult("ok")
    account, server = settings.stock_data_account, settings.stock_data_server
    token = secrets.token_hex(16)
    try:
        acquired = await redis.set(CATALOG_LOCK_KEY, token, nx=True, px=_LOCK_MS)
    except RedisError:
        return CycleResult("lock_error")
    if not acquired:
        return CycleResult("locked")

    requests: tuple[CatalogQuoteRequest, ...] = ()
    try:
        async with asyncio.timeout(min(_WORK_SECONDS, settings.stock_cycle_budget_seconds)):
            requests = await pending_catalog_quotes(
                redis, account=account, server=server, limit=_BATCH_SIZE
            )
            if not requests:
                return CycleResult("ok")
            selected, refused = await _select_batch(sessionmaker, settings, requests, now)
            requests = (*refused, *(request for request, _ in selected))
            for request in refused:
                await complete_catalog_quote(
                    redis, request, account=account, server=server, reason="failed_check"
                )
            accepted = 0
            if selected:
                accepted = await _refresh(sessionmaker, redis, http, settings, selected, now, token)
            return CycleResult("ok", accepted=accepted, rejected=len(requests) - accepted)
    except Exception as exc:
        logger.warning("catalog quote cycle failed: %s", type(exc).__name__)
        try:
            async with asyncio.timeout(1):
                for request in requests:
                    await complete_catalog_quote(
                        redis, request, account=account, server=server, reason="source_error"
                    )
        except RedisError, TimeoutError:
            logger.warning("catalog request completion unavailable")
        return CycleResult("source_error")
    finally:
        try:
            await redis.eval(_RELEASE_LUA, 1, CATALOG_LOCK_KEY, token)
        except RedisError:
            logger.warning("catalog quote lock release failed")
