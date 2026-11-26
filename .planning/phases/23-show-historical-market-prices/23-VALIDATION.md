---
phase: 23
slug: show-historical-market-prices
status: executed
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-26
---

# Phase 23 — Validation strategy

Use the locked Python and Node environments, isolated Postgres and Redis,
Vitest, and the existing disposable Playwright stack. Provider tests use
HTTP boundary fixtures. `nyquist_compliant` records the planned verification
coverage. Live provider qualification remains open.

| Task | Requirements | Execution evidence |
|---|---|---|
| 23-01-01 | CHART-04 | Published candidate scope documented. Representative live coverage, rights and measured limits remain open. [Source qualification](23-SOURCE-QUALIFICATION.md) |
| 23-01-02 | CHART-01, CHART-02, CHART-04 | 36 provider and normalization tests passed for exact mapping, bounded reads, completion, Decimal changes and gaps. [Plan 01 summary](23-01-SUMMARY.md) |
| 23-02-01 | CHART-01, CHART-03, CHART-04 | API fixtures passed for authentication, active identity, coalescing, disabled scope and cache failure. [Plan 02 summary](23-02-SUMMARY.md) |
| 23-02-02 | CHART-03, CHART-04 | 335 scoped backend regression tests passed, with 130 focused cases reaching 100% on both critical scheduler modules. The review fixes passed 85 replay checks and 100% stock route coverage. [Code review](23-REVIEW.md) |
| 23-03-01 | CHART-01, CHART-02, CHART-03 | Chart and API decoder tests passed for matching windows, dates and prices, gaps, errors and session boundaries. [Plan 03 summary](23-03-SUMMARY.md) |
| 23-03-02 | CHART-01, CHART-02, CHART-03 | 57 focused post-review tests passed for late replies, aborts, retries, status and current-quote independence. [Code review](23-REVIEW.md) |
| 23-04-01 | CHART-01–04 | All 11 isolated Chromium cases passed for chart ranges, exact identity, preview ask, retained stock and crypto fills, market closure, narrow layout and enlarged-text reflow. [Browser receipt](23-BROWSER-RECEIPT.md) |
| 23-04-02 | CHART-01–04 | Four running-app and ZIP pairs compared. Frontend lint, typecheck, 1,409 Vitest tests and the build passed. [Browser receipt](23-BROWSER-RECEIPT.md) |

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
