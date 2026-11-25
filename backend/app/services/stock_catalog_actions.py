"""Issuer-bound action rights, historical aliases and monitoring readiness."""

import json
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.stock import StockDataAdmission
from app.models.stock_catalog import (
    StockCatalogAlias,
    StockCatalogListing,
)
from app.services.stock_admission import (
    CatalogActionPolicy,
    ProductAdmission,
    catalog_action_policy,
    evaluate_admission,
)
from app.services.stock_catalog_promotion import (
    CATALOG_ACTION_FIELDS,
    CatalogFinancialBinding,
    load_catalog_action_binding,
)


@dataclass(frozen=True)
class CatalogActionAlias:
    symbol: str
    through: date
    valid_until: datetime


@dataclass(frozen=True)
class CatalogActionAuthority:
    binding: CatalogFinancialBinding
    admission_id: int
    ticker: str
    valid_until: datetime
    calendar: ProductAdmission
    journal_origin: datetime
    policy: CatalogActionPolicy | None
    fingerprint: str
    is_fixture: bool = False
    aliases: tuple[CatalogActionAlias, ...] = ()
    ambiguous_symbols: frozenset[str] = frozenset()

    @property
    def known_symbols(self) -> frozenset[str]:
        return frozenset(
            (self.ticker, self.binding.provider_symbol, *(alias.symbol for alias in self.aliases))
        )


def matches_catalog_action_symbol(
    authority: CatalogActionAuthority, symbol: str, process_date: date | None, at: datetime
) -> bool:
    if symbol in authority.ambiguous_symbols:
        return False
    if symbol in (authority.ticker, authority.binding.provider_symbol):
        return True
    return process_date is not None and any(
        alias.symbol == symbol and process_date <= alias.through and at < alias.valid_until
        for alias in authority.aliases
    )


async def load_catalog_action_authority(
    db: AsyncSession,
    coin_id: int,
    at: datetime,
    *,
    account: str,
    server: str,
    allow_fixture: bool = False,
) -> CatalogActionAuthority | None:
    """Recheck the exact issue under accounting rights, independently of trading."""
    rows = (
        await db.execute(
            text("""
        SELECT b.catalog_id,b.listing_id,b.promoted_at,l.ticker,g.published_at,
               a.id,a.reviewed_at,a.fields,a.scope,a.is_fixture,c.journal_origin,st.journal_start_at
          FROM public.stock_catalog_instruments b
          JOIN public.stock_catalog_listings l ON (l.id,l.security_id)=(b.listing_id,b.catalog_id)
          JOIN public.stock_catalog_generations g ON g.id=l.generation_id
          JOIN public.stock_catalog_admissions a ON a.artifact='catalog_actions'
          LEFT JOIN public.stock_catalog_action_coverage c ON c.coin_id=b.coin_id
          LEFT JOIN public.stock_action_state st ON st.coin_id=b.coin_id
         WHERE b.coin_id=:coin AND (g.mode='live' OR :allow_fixture)
           AND a.scope->>'catalog_id'=b.catalog_id::text
           AND a.scope->>'listing_id'=b.listing_id::text
           AND a.scope->>'provider_asset_id'=l.provider_asset_id
           AND a.is_fixture=(g.mode='fixture') AND a.revoked_at IS NULL
           AND a.reviewed_at<=:at AND :at<a.valid_until
           AND a.scope @> CAST(:scope AS jsonb)
           AND public.stock_catalog_scope_current(
             a.id,'catalog_actions',b,l,:at,CAST(:fields AS jsonb))
         ORDER BY a.id LIMIT 2
    """),
            {
                "coin": coin_id,
                "at": at,
                "allow_fixture": allow_fixture,
                "fields": json.dumps(CATALOG_ACTION_FIELDS),
                "scope": json.dumps({"account": account, "server": server}),
            },
        )
    ).all()
    if len(rows) != 1:
        return None
    row = rows[0]
    origin = row.journal_origin or row.journal_start_at or row.promoted_at
    if not row.promoted_at <= origin <= at or (
        row.journal_start_at is not None and row.journal_start_at != origin
    ):
        return None
    binding = await load_catalog_action_binding(
        db,
        row.catalog_id,
        row.listing_id,
        row.id,
        at,
        allow_fixture=allow_fixture,
    )
    if binding is None or (binding.coin_id, binding.account, binding.server) != (
        coin_id,
        account,
        server,
    ):
        return None
    model = StockDataAdmission
    columns = [column for column in model.__table__.columns if column.name != "id"]
    verified = (
        (await db.execute(select(*columns).where(model.product == "calendar")))
        .mappings()
        .one_or_none()
    )
    if verified is None:
        return None
    calendar = ProductAdmission(**verified)
    decisions = [
        evaluate_admission(calendar, "calendar", purpose, at, account=account, server=server)
        for purpose in ("collection", "derived", "retention")
    ]
    calendar_deadlines = [
        decision.valid_until
        for decision in decisions
        if decision.allowed and decision.valid_until is not None
    ]
    if len(calendar_deadlines) != len(decisions):
        return None

    alias, listing = StockCatalogAlias, aliased(StockCatalogListing)
    former = (
        await db.execute(
            select(alias.symbol, alias.valid_until)
            .where(
                alias.security_id == row.catalog_id,
                alias.listing_id == row.listing_id,
                alias.namespace == "former",
                alias.verified_at <= at,
                alias.valid_until > at,
                select(listing.id)
                .where(
                    listing.security_id == row.catalog_id,
                    listing.id != row.listing_id,
                    listing.ticker == alias.symbol,
                    listing.provider_asset_id == binding.provider_asset_id,
                )
                .exists(),
            )
            .order_by(alias.symbol)
            .limit(9)
        )
    ).all()
    if len(former) > 8:
        return None
    aliases = tuple(
        CatalogActionAlias(symbol, row.published_at.date(), expiry) for symbol, expiry in former
    )
    known = [row.ticker, binding.provider_symbol, *(alias.symbol for alias in aliases)]
    # Any other issue with the same provider-facing label makes symbol-only
    # matching uncertain. A replayed ticker cannot transfer an entitlement.
    collisions = frozenset(
        (
            await db.scalars(
                select(StockCatalogListing.ticker)
                .where(
                    StockCatalogListing.security_id != row.catalog_id,
                    StockCatalogListing.ticker.in_(known),
                )
                .distinct()
            )
        ).all()
    )
    policy = catalog_action_policy(row.scope)
    if policy is not None and (
        binding.provider_symbol not in policy.rest_symbols
        or not set(policy.rest_symbols) <= set(known)
        or len(policy.rest_symbols) > policy.symbols_per_request
        or origin.date() < policy.history_start
        or origin < policy.mutation_start
    ):
        policy = None
    expiry = min(
        binding.valid_until, *calendar_deadlines, *(alias.valid_until for alias in aliases)
    )
    digest = sha256(
        json.dumps(
            [row.id, row.reviewed_at.isoformat(), row.fields, row.scope], sort_keys=True
        ).encode()
    ).hexdigest()
    return CatalogActionAuthority(
        binding,
        row.id,
        row.ticker,
        expiry,
        calendar,
        origin,
        policy,
        digest,
        row.is_fixture,
        aliases,
        collisions,
    )


async def catalog_action_candidates(
    db: AsyncSession,
    at: datetime,
    *,
    account: str,
    server: str,
    allow_fixture: bool,
    selected: tuple[tuple[int, int], ...] | None = None,
    max_age_seconds: int = 120,
) -> tuple[CatalogActionAuthority, ...]:
    """Take one cohort, sharing provider capacity between open exposure and selection."""
    rows = (
        await db.execute(
            text("""
        WITH selected_listings AS (
            SELECT DISTINCT catalog_id, listing_id
            FROM jsonb_to_recordset(CAST(:selected AS jsonb))
            AS item(catalog_id bigint, listing_id bigint)
        ), open_exposures AS (
            SELECT h.coin_id
            FROM public.holdings h JOIN public.accounts p ON p.id=h.portfolio_id
            WHERE NOT :scan_all AND h.quantity>0 AND p.closed_at IS NULL
            UNION
            -- A sold position may still have a later dividend or correction.
            SELECT m.coin_id
            FROM public.stock_ownership_movements m
            JOIN public.accounts p ON (p.id,p.user_id)=(m.portfolio_id,m.user_id)
            WHERE NOT :scan_all AND p.closed_at IS NULL
        ), candidates AS MATERIALIZED (
            SELECT b.coin_id, b AS binding, l AS listing, g.mode, c.observed_at,
                   st.staged_continuation->>'target_until' IS NOT NULL AS in_progress,
                   CASE WHEN st.staged_continuation->>'target_until' IS NOT NULL
                     THEN st.staged_continuation->>'policy_key' END AS active_window,
                   CASE WHEN pg_input_is_valid(
                       st.staged_continuation->>'target_until','timestamp with time zone')
                     THEN (st.staged_continuation->>'target_until')::timestamptz END AS target_at,
                   requested.catalog_id IS NOT NULL AS is_selected
            FROM public.stock_catalog_instruments b
            JOIN public.stock_catalog_listings l ON (l.id,l.security_id)=(b.listing_id,b.catalog_id)
            JOIN public.stock_catalog_generations g ON g.id=l.generation_id
            JOIN public.stock_action_state st ON st.coin_id=b.coin_id
            LEFT JOIN public.stock_catalog_action_coverage c ON c.coin_id=b.coin_id
            LEFT JOIN open_exposures exposure ON exposure.coin_id=b.coin_id
            LEFT JOIN selected_listings requested
              ON (requested.catalog_id,requested.listing_id)=(b.catalog_id,b.listing_id)
            WHERE (g.mode='live' OR :allow_fixture) AND g.is_active
              AND g.published_at<=:at AND :at<g.valid_until
              AND (
                :scan_all OR st.staged_continuation->>'target_until' IS NOT NULL
                OR exposure.coin_id IS NOT NULL OR requested.catalog_id IS NOT NULL
            )
        ), admitted AS (
            SELECT coin_id, active_window, in_progress, target_at, is_selected, observed_at,
                   row_number() OVER (PARTITION BY in_progress, is_selected
                                      ORDER BY observed_at NULLS FIRST, coin_id) AS lane_rank
            FROM candidates
            WHERE EXISTS (
                SELECT 1 FROM public.stock_catalog_admissions a
                WHERE a.artifact='catalog_actions' AND a.scope @> CAST(:scope AS jsonb)
                  AND a.is_fixture=(candidates.mode='fixture') AND a.revoked_at IS NULL
                  AND a.reviewed_at<=:at AND :at<a.valid_until
                  AND a.scope->>'catalog_id'=(candidates.binding).catalog_id::text
                  AND a.scope->>'listing_id'=(candidates.binding).listing_id::text
                  AND a.scope->>'provider_asset_id'=(candidates.listing).provider_asset_id
                  AND public.stock_catalog_scope_current(
                    a.id,'catalog_actions',candidates.binding,candidates.listing,
                    :at,CAST(:fields AS jsonb))
            )
        )
        SELECT coin_id, active_window
        FROM admitted
        ORDER BY CASE
                   WHEN NOT in_progress THEN 1
                   WHEN :scan_all OR (
                     target_at<=:at
                     AND target_at>:at-CAST(:max_age_seconds AS integer)*interval '1 second'
                   ) THEN 0
                   ELSE 2
                 END, active_window,
                 -- At most three obligation slots for each waiting selection slot.
                 CASE WHEN NOT :scan_all AND NOT in_progress
                   THEN (lane_rank-1)*CASE WHEN is_selected THEN 3 ELSE 1 END ELSE 0 END,
                 (NOT :scan_all AND NOT in_progress AND NOT is_selected),
                 observed_at NULLS FIRST, coin_id
        LIMIT 8
    """),
            {
                "at": at,
                "allow_fixture": allow_fixture,
                "scan_all": selected is None,
                "max_age_seconds": max_age_seconds,
                "selected": json.dumps(
                    [
                        {"catalog_id": catalog_id, "listing_id": listing_id}
                        for catalog_id, listing_id in selected or ()
                    ]
                ),
                "fields": json.dumps(CATALOG_ACTION_FIELDS),
                "scope": json.dumps(
                    {
                        "account": account,
                        "server": server,
                        "known_id_recheck": True,
                        "all_us_replay_ingress": True,
                        "replay_region": "us",
                    }
                ),
            },
        )
    ).all()
    ready: list[CatalogActionAuthority] = []
    symbols: set[str] = set()
    cap = 8
    active_window = rows[0].active_window if rows else None
    for coin, previous_window in rows:
        if previous_window != active_window:
            break
        authority = await load_catalog_action_authority(
            db,
            coin,
            at,
            account=account,
            server=server,
            allow_fixture=allow_fixture,
        )
        if authority is None or authority.policy is None:
            continue
        proposed = symbols | set(authority.policy.rest_symbols)
        if len(proposed) > min(cap, authority.policy.symbols_per_request):
            break
        baseline = min(item.journal_origin for item in (*ready, authority))
        if any(
            item.policy is None
            or item.policy.history_start > baseline.date()
            or item.policy.mutation_start > baseline
            for item in (*ready, authority)
        ):
            break
        ready.append(authority)
        symbols = proposed
        cap = min(cap, authority.policy.symbols_per_request)
    return tuple(ready)


async def lock_catalog_action_scope(db: AsyncSession) -> None:
    await db.execute(text("SELECT pg_advisory_xact_lock_shared(1026019025::bigint)"))
