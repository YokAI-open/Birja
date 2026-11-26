---
phase: 23
slug: show-historical-market-prices
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-26
---

# Phase 23 — Validation strategy

Use the locked Python and Node environments, isolated Postgres and Redis,
Vitest, and the existing disposable Playwright stack. All rows below are
planned. New provider tests use HTTP boundary fixtures. No separate Wave 0
setup is needed.

| Task | Requirements | Evidence |
|---|---|---|
| 23-01-01 | CHART-04 | Dated source qualification with published scope and bounded observed attempts, or precise unresolved evidence |
| 23-01-02 | CHART-01, CHART-02, CHART-04 | `test_market_history.py` and `test_market_history_providers.py` for explicit mapping, completeness, Decimal prices and limits |
| 23-02-01 | CHART-01, CHART-03, CHART-04 | `test_market_history_api.py` for authority, identity, deduplication, disabled and cache-failure states |
| 23-02-02 | CHART-03, CHART-04 | `test_market_history_scheduler.py` and API tests for actual shared budgets, memory-only cache and safe publication |
| 23-03-01 | CHART-01, CHART-02, CHART-03 | Chart and API decoder Vitest for confirmed dates/prices, range changes, error, late symbols and auth departure |
| 23-03-02 | CHART-01, CHART-02, CHART-03 | Markets Vitest and chart tests, lint and type checking for the ready, closed, partial and unavailable paths |
| 23-04-01 | CHART-01–04 | Focused isolated Playwright selection with named chart tests, Phase 22 Markets and catalog cases, and actual crypto and stock fills |
| 23-04-02 | CHART-01–04 | Full frontend checks, relevant backend replay, scope-relevant review, screenshots and evidence receipt |

After each task run its automated check. At backend integration run the
new provider, history API and scheduler tests together, plus affected
existing quote/action budget and trade tests. For final app verification,
use the planned browser filter and list exact matches before execution.
Required CI still runs the complete release checks.

Visual evidence includes four matched app/ZIP captures. Use 1440px for
open equity, closed equity and crypto and 390px for catalog detail.
Record any permitted fixture and attribution differences. Finish the
comparison only once material mismatches are resolved. Inspect tiles, titles, layout,
price and status, button groups, plot and right-aligned action, plus
keyboard and enlarged-text reflow. Exercise delayed history with current trade still available. Distinguish automated reflow from
a user's native zoom acceptance. Record any human check only if received.
Preserve actual snapshot hashes and effective fixture/runtime sources.

The chart provider authorization and coverage record must identify actual
evidence, quota, freshness, permitted caching and the scope checked.
Measurement against tenant/provider accounts is conditional on existing
authorization. Deterministic results may close local behavior but leave
the applicable live part of CHART-04 unresolved.
