---
phase: 25-finish-the-trading-flows-and-verify-the-integrated-app
plan: "05"
subsystem: integrated-verification
tags: [playwright, trading, history, auth, comparison]
requires:
  - phase: 25-02
    provides: Owned server History filters, exact cursor behavior and guarded backend proof
  - phase: 25-03
    provides: Trades, previews, receipts and portfolio chooser alignment
  - phase: 25-04
    provides: Responsive History and focused email sign-in workspaces
provides:
  - Exact browser proof for the trade, History and sign-in flows
  - Six paired screenshots from the approved prototype and guarded application
affects: [25-06, FLOW-04]
tech-stack:
  added: []
  patterns: [isolated synthetic Playwright, exact ledger reconciliation, paired viewport geometry]
key-files:
  created:
    - frontend/e2e/phase25-review-capture.ts
    - .planning/phases/25-finish-the-trading-flows-and-verify-the-integrated-app/25-BROWSER-RECEIPT.md
  modified:
    - frontend/e2e/trade.spec.ts
    - frontend/e2e/stock-trades.spec.ts
    - frontend/e2e/stock-catalog.spec.ts
    - frontend/e2e/dividends-history.spec.ts
    - frontend/e2e/auth.spec.ts
    - frontend/e2e/stock-trade-fixture.py
    - deploy/tests/dividend-execution-fixture.py
key-decisions:
  - Use separate curated symbols for the real dividend correction and retained split scenarios.
  - Measure computed 200% CSS text sizes at 320px and retain native zoom as an unmeasured check.
requirements-completed: [FLOW-01, FLOW-02, FLOW-03]
completed: 2026-11-26
---

# Phase 25 Plan 05 — Integrated browser verification

The guarded app completed 18 Chromium journeys on `0087e99`. Actual crypto
and stock fills reconciled with the selected portfolio and History, History
filtered and paginated its owned ledger, and a generated one-time code signed
in and out through the real session. All six desktop and phone comparisons
were inspected with viewport geometry from the same commit.

| Task | Final evidence | Commit |
|---|---|---|
| 25-05-01 | The crypto draft capture and existing stock journeys exercised both crypto buy modes, curated and catalog whole-share orders, last permitted marks, repricing, receipt focus, and same-owner statement and ledger values. | `e9a08d3` |
| 25-05-02 | The filtered real cursor appended an off-page original and preserved keyboard recovery. The signed-out application requested, validated and verified a console-delivered code and returned focus after sign-out. Trade, History and sign-in passed measured enlarged-text checks. | `381d951` |
| 25-05-03 | The exact 18-case run passed in 246.6 seconds and cleaned up all owned resources. Six matching-viewport pairs, per-input identities and earlier repair evidence are in the [browser receipt](25-BROWSER-RECEIPT.md). | `48f8e6b` |

Frontend lint, formatting, TypeScript and build passed on `0087e99`. Vitest
passed 1,441 cases with 94.58% statement and 92.37% branch coverage. The
guarded API replay passed 108 cases in 121.10 seconds, and the backend and
test Compose inputs matched the final browser candidate. FLOW-04 has local
browser and visual evidence here. Hosted recovery and required CI are
tracked through Plan 25-06 and release qualification.

## Adjustments

- `9d3c6cb` used the actual trade chooser labels, kept the isolated catalog
  fixture on revision `0028`, and measured the doubled computed font sizes
  at 320px. The comparison manifest binds the source and fixture digests.
- `aec88bc` reduced the added dividend filter fixture to one payment and
  its correction within a short real server page and matched the current
  holding-card names. `729f216` kept the existing 28-payment and split case
  on KO to preserve MSFT execution for the retained portfolio case.
- `f99b1eb` aligned the History toolbar and event list. `0087e99` kept the
  active append retry in view after the error alert appeared. The final
  integrated replay retested both runtime changes.

## Self-Check: PASSED

The receipt and paired archive exist. The 20-entry archive passed its
integrity check. The three task commits and fixture and runtime corrections
are present. The run log, all three empty ownership inventories, matching
source maps and archive digest were verified.
