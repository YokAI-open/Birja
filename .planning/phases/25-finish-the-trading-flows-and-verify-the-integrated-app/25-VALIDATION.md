---
phase: 25
slug: finish-the-trading-flows-and-verify-the-integrated-app
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-26
---

# Phase 25 — Validation strategy

Use the existing locked environments, guarded disposable PostgreSQL and Redis,
Vitest and Chromium. Existing infrastructure covers Wave 0. Run affected
checks per task and one integrated browser pass on stable runtime inputs. The
normal six-job CI workflow provides final hosted evidence on the authorized
candidate. [Technical research](25-RESEARCH.md#validation-architecture)

| Requirement | Planned evidence |
|---|---|
| FLOW-01 | Component and guarded browser evidence for crypto, curated and catalog stocks, exact preview and original receipt, same-portfolio cash, retained market states and History reconciliation. |
| FLOW-02 | Real PostgreSQL and API checks for filters before pagination, backwards-compatible default cursors, filtered scope, private ownership, exact events and amounts. Client and browser tests for filter and portfolio changes, disclosure, paging and retry. |
| FLOW-03 | Actual auth route and cookie-backed session through generated console OTP, plus pending, failure, resend, focus and door sign-out tests. |
| FLOW-04 | Full frontend checks, targeted backend branch coverage, retained guarded browser series, six matched app and ZIP pairs, code review, measured recovery input comparison and the hosted candidate evidence. |

## Per-task verification

Run commands from the task's `<verify>` block. Use the existing guarded
backend fixtures and locked frontend dependencies. Run focused checks per task,
and one selected real browser campaign after design and filter integration.
Reuse current local evidence with the tested scope and exact input comparison.

| Task | Wave | Requirements | Verification and expected evidence |
|---|---:|---|---|
| 25-01-01 | 2 | FLOW-01 | App, trade page and original-attempt Vitest cases for the one chooser, crypto input modes, preview, repricing and receipt. |
| 25-01-02 | 2 | FLOW-01 | Curated stock ticket, receipt and hook Vitest cases for authorized price and cash, closed/Halted labels and original-result continuation. |
| 25-01-03 | 2 | FLOW-01 | All three trade page suites, retained rename/attempt case and TypeScript. Check exact listing and owner identity. |
| 25-02-01 | 1 | FLOW-02 | Existing cursor and schema pytest with filtered scope and default mixed and legacy shape compatibility cases. |
| 25-02-02 | 1 | FLOW-02 | Guarded service, route, cursor, catalog, portfolio and legacy History tests. Measure 100% branch-aware coverage in the three specified History modules, Ruff and mypy. |
| 25-03-01 | 1 | FLOW-03 | Existing sign-in, auth hooks and client tests for real mutation states, valid inputs, focus and resilience. |
| 25-03-02 | 1 | FLOW-03 | App, sign-in, auth mutations and TypeScript for one accessible door, session transitions and feedback. |
| 25-04-01 | 2 | FLOW-02 | Trade and mixed History client tests for request filters, v4 cursor scope and default compatibility. |
| 25-04-02 | 2 | FLOW-02 | Scoped query, portfolio History, page/disclosure tests and TypeScript. Check pagination, focus, retry, independent stale updates and exact originals. |
| 25-05-01 | 3 | FLOW-01, FLOW-04 | Playwright test discovery and TypeScript for guarded exact trades, reconciled data and captured ticket geometry. |
| 25-05-02 | 3 | FLOW-02, FLOW-03, FLOW-04 | Playwright discovery and TypeScript for real mixed page/filter and generated-code journeys. |
| 25-05-03 | 3 | FLOW-01, FLOW-02, FLOW-03, FLOW-04 | Full frontend lint, format, types, coverage and build. Selected real Chromium and guarded trade/auth/chart API replays. Six valid app and prototype pairs, responsive and exact source/fixture evidence. |
| 25-06-01 | 1 | FLOW-04 | Existing offline CI contracts with finite job, recovery wait and serial time caps, and exact UTC clock cases. |
| 25-06-02 | 1 | FLOW-04 | Offline CI/recovery contracts and seven-stage selector dry-run to preserve job, proof and artifact identity. |
| 25-07-01 | 4 | FLOW-04 | Scoped review, relevant replays, candidate/source/receipt checks and applicable same-scope recovery evidence. |
| 25-07-02 | 4 | FLOW-04 | Local exact candidate identity check. Explicit publication decision gates an external push and PR. |
| 25-07-03 | 4 | FLOW-04 | Authorized run's actual six hosted job outcomes, checkout identity, authenticated seven-stage receipt and archive digest. |

All runtime results remain planned. Each task has automated verification and
all required CI checks still apply. The only publication decision follows
local review and evidence. FLOW-04 remains pending until the matching hosted
run and receipt pass.

## Additional evidence

Bind screenshots, source and fixture hashes to the tested app and the
approved ZIP. Compare 1440 × 1000 and 390 × 1000 and exercise 320px and 200%
CSS text enlargement. Record native browser zoom if exercised. Use synthetic
identities, generated console delivery and deterministic market fixtures.
CHART-04's live provider qualification remains a separately tracked release
condition. No manual test of real provider credentials is part of this plan.

## Planning sign-off

Independent verification passed seven plans and 17 tasks in four waves on
2026-11-26. It confirmed all four FLOW requirements, all five decisions,
collision-free file ownership and discovery of 15 retained Chromium cases
in eight files. The final publication checkpoint names the exact branch
SHA and tree after committing local evidence.
