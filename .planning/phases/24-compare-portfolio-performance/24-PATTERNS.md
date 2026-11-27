# Phase 24 — Portfolio performance pattern map

Mapped against `2dc83f8` on 2026-11-26. The file names for new modules are
planning candidates. The source locations identify existing behavior to reuse.

## File classification

| Planned seam | Role and flow | Closest existing analog |
|---|---|---|
| Daily aggregate and capture service | Model and service, transactional append | `Account`, `load_portfolio_snapshots`, `calculate_portfolio` |
| Scheduled capture and role fence | Task and migration, bounded batch | `amain` background callbacks, `lock_stock_portfolio_roots`, `fence_owned_active_portfolios` |
| Schema admission and encrypted restore | Migration and operations, revision-bound file I/O | `require_schema`, `portfolio_migrate`, the 0027 producer and verifier, `successor_recovery_operations` |
| Owner-batched private trend read | Route and service, request-response | `/portfolios/overview`, `list_active_portfolios` and `fence_owned_active_portfolios` |
| Trend decoder and query hook | Utility and hook, request-response | `fetchPortfolioOverview`, `usePortfolioOverview`, `usePortfolioDeletion` |
| Overview card and sparkline | Page and component, navigation and display | `PortfoliosPage` card link and `MarketHistoryChart` Canvas lifecycle |
| Selected portfolio and holding cards | Page and component, display and navigation | `PortfolioPage`, `PortfolioHoldings`, `PortfolioAllocation` |

## Exact statement and capture

`load_portfolio_snapshots` accepts an `owner_id`, optional exact `portfolio_ids`,
valuation settings and a deterministic `now` seam. It filters active roots before
joining holdings, bounds ownership selection to the existing ten-book cap,
rehydrates market authority and rechecks the same active IDs. Its current return
assembles the authoritative values once. [Portfolio service](../../../backend/app/services/portfolio.py#L82)

```python
return tuple(
    _assemble_snapshot(book, original, current, current_raw, catalog, settings, valued_at)
    for book in grouped.values()
)
```

Reuse the statement's emitted Decimal values and actual starting cash. The
calculator's `complete = all(value is not None for value in raw_values)` and
`total = known if complete else None` preserve the difference between exact total
and incomplete known value. [Portfolio math](../../../backend/app/services/portfolio_math.py#L69)

The normal read holds a `with_for_update(read=True, of=Account)` fence through
serialization. For the scheduler, use the migrator-owned lock-only pattern from
`lock_stock_portfolio_roots`, narrowed to the exact owner and active root. That
existing helper revokes access from `PUBLIC` and grants execution to
`birja_scheduler`. Its stock-instrument lock and broad holding scan are specific
to corporate actions. Keep the new exact-row fence through the daily insert and
commit. [Read fence](../../../backend/app/services/portfolio.py#L205) · [Role precedent](../../../backend/alembic/versions/0017_portfolio_ownership.py#L111)

`amain` gives the dedicated scheduler owned task lifetimes through `TaskGroup`
and registers optional background callbacks with `heartbeat=None`. Reuse that
callback lifetime for bounded per-tick work and failure isolation. Keep existing
valuation and clock settings consistent across web and scheduler entry points.
[Scheduler](../../../backend/app/tasks/scheduler.py#L472) · [Settings](../../../backend/app/core/config.py)

## Versioned schema and recovery

`require_schema` admits an explicit set of revisions per consumer, invokes that
revision's `PORTFOLIO_PREFLIGHT_SQL` and compares its exact grants digest. Pair a
reviewed successor migration with its own revision contract, role grants and
approved migration source path. Preserve old revision bindings. [Schema guard](../../../backend/app/db/schema_contract.py#L30) · [Role manifest](../../../backend/app/db/portfolio_bootstrap.py) · [Migration preflight](../../../backend/app/db/portfolio_migrate.py)

`backup-snapshot.py` limits `SUPPORTED_REVISIONS` and authenticates its snapshot
contracts. `verify-restore.py` selects the corresponding source contract and
validates restored role access and states. `successor_recovery_operations` binds
the archive and source across retained, role, TLS and rollback lanes. Add a
matching successor lane that compares daily rows and identity evidence after a
real restore, including incomplete and terminal-owner observations.
[Backup producer](../../../deploy/backup-snapshot.py) · [Restore verifier](../../../deploy/verify-restore.py) · [Existing runner](../../../deploy/tests/run-portfolio-validation.py#L493)

## Private reads and client fencing

The static `/overview` registration precedes `/{portfolio_id}` on the shared
`ManagementRoute`. It receives `CurrentUserDep` and `DbDep` and supplies an
explicit response model. Register the static trend GET in that order. Query
owned active roots and bounded points, then fence the exact returned IDs with
`fence_owned_active_portfolios` through serialization. [Route](../../../backend/app/api/v2/portfolios.py#L45) · [Ownership service](../../../backend/app/services/portfolios.py#L44)

`fetchPortfolioOverview` uses `apiFetch` with `signal`, `cache: "no-store"` and
`credentials: "same-origin"` before strict parsing of exact IDs and values.
`usePortfolioOverview` compares owner, session epoch and deletion generation
after each awaited fetch. Query a separate trend payload and bind its identity
set to active cards. Purge or fence stale data on logout, active-set changes and
deletion. [Transport and decoder](../../../frontend/src/api/portfolioOverview.ts#L34) · [Overview hook](../../../frontend/src/hooks/usePortfolioOverview.ts#L43) · [Deletion invalidation](../../../frontend/src/hooks/usePortfolioDeletion.ts#L554)

## Portfolio views

The overview already surrounds each whole card with `Link` and puts the
creation button after the list of portfolios. Its `aria-labelledby` points to
the name. Associate the dated trend summary via `aria-describedby` and keep
the retry beside the grid. `HistoryPlot` sets up `ResizeObserver` and disconnects
on cleanup. Reuse this responsive drawing pattern with date-spaced points and
segments split on missing days. [Overview cards](../../../frontend/src/pages/PortfoliosPage.tsx#L184) · [Canvas lifecycle](../../../frontend/src/components/MarketHistoryChart.tsx#L136)

`PortfolioPage` renders sourced value, profit and incomplete count beside
`PortfolioAllocation`, followed by `PortfolioHoldings`. Preserve the existing
toolbar actions and exact trade destinations. Use `compareAmountDescending`
with `current_value` or `unrealized_pl_percent` as dictated by the selected sort,
retain unavailable-last behavior and stable ticker and exact ID tie breaks.
[Selected portfolio](../../../frontend/src/pages/PortfolioPage.tsx#L137) · [Holding sort](../../../frontend/src/components/PortfolioHoldings.tsx#L174) · [Allocation](../../../frontend/src/components/PortfolioAllocation.tsx)

The durable daily value relation and a date-only portfolio series have no direct
feature analog. Their invariants and verification come from the research and UI
contract. [Technical research](24-RESEARCH.md) · [UI contract](24-UI-SPEC.md)
