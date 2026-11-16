---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "14"
subsystem: accounting
tags: [portfolio, valuation, history, cursor, authorization, immutable-evidence]
requires:
  - phase: 12-10
    provides: explicit-root crypto execution and immutable receipts
  - phase: 12-11
    provides: paired stock fills and original-root replay
  - phase: 12-13
    provides: owned dividend effects and private causal ancestry
provides:
  - Exact owned valuation against each stored baseline with string root identity and name
  - Owner/root-filtered trade and mixed History sources, hydration and original references
  - Strict root-bound trade2 and mixed3 cursors with complete deterministic seek tuples
affects: [12-15, 12-17, 12-20, 12-22, 12-25, 12-27]
tech-stack:
  added: []
  patterns: [paired read snapshots, root-bound canonical cursors, lifecycle recheck before publication]
key-files:
  created:
    - backend/tests/test_portfolio_valuation.py
    - backend/tests/test_portfolio_scoped_history.py
  modified:
    - backend/app/services/portfolio.py
    - backend/app/schemas/portfolio.py
    - backend/app/services/history.py
    - backend/app/services/event_history.py
key-decisions:
  - Require OwnedActivePortfolio at every financial read and independently filter owner and root
  - Retain stored starting_cash, existing dated/incomplete marks and unchanged valuation arithmetic
  - Reject old or crossed-root cursors before queries; cursor contents never authorize financial access
requirements-completed: []
requirements-addressed: [PVIEW-03, PCTX-01, PFUND-03]
duration: 12 min
completed: 2026-11-16
---

# Phase 12 Plan 14: Scoped Valuation and Private Mixed History

**Exact statements and versioned History continuations preserve one portfolio's actual finances while excluding sibling rows and linked originals.**

## Performance

- Started: 2026-11-16T11:00Z
- Focused verification complete: 2026-11-16T11:12Z
- Tasks: 2/2
- Files created/modified: 6
- Dependencies, SQL privileges, providers and production changes: none

## Accomplishments

- get_portfolio requires frozen OwnedActivePortfolio and selects the exact
  active Account by root/owner. Holdings join on both columns, and immutable
  stock source-rights proof is paired to the same root. Cash, actual stored
  starting_cash, midpoint math, incomplete known value and unavailable returns
  retain their existing meanings. PortfolioSnapshot/PortfolioOut add the string
  portfolio_id and stored plain-text name without pooling siblings.
- Both History services require the explicit root. Every source union arm,
  trade/fact join, payment, split movement, decision and hydrated original
  filters owner and portfolio. Split applications remain global and are
  reached through the selected owned movement. Missing immutable stock facts
  or incomplete hydration refuse rather than publish guessed/partial rows.
- Trade cursor2 and mixed cursor3 include a canonical decimal-string root ID
  plus their retained complete seek tuple. Decode requires the expected root,
  rejects old versions, malformed/extra/duplicate fields and crossed-root use,
  and runs before any SQL. Limits remain bounded to100 with limit+1 lookahead.
  Lifecycle is checked independently of the cursor and again before History
  publication so a root closed during multi-query hydration is suppressed.

## Task Commits

1. **12-14-01: Value one root against its actual stored baseline** — `3d1f736`
2. **12-14-02: Bind History cursors and hydration to the owned root** — `6ae951e`

## Verification

Existing locked environment only, uv run --no-sync with a temporary uv cache.
Scoped socket access reached only the guarded disposable birja_test database
and Redis stack. No install or real provider/data operation occurred.

| Check | Result |
|---|---|
| tests/test_portfolio_valuation.py | 13 passed |
| tests/test_portfolio_scoped_history.py | 43 passed in52.07s,12 fixture transaction warnings |
| Unchanged tests/test_portfolio_math.py | 17 passed |
| Four changed source modules, focused mypy | PASS |
| Six changed source/test files, Ruff check/format | PASS |
| git diff --check | PASS |

Real valuation tests cover unequal actual baselines, sibling same-symbol
positions, unknown/foreign/closed404, cash-only roots, unpriced holdings,
unchanged crypto age thresholds, exact stock midpoint and original dated
halt/closed marks. Real History tests cover all event kinds, owner/root
exclusion, tied trade and mixed-kind ordering, append continuations, private
off-page correction originals, held zero-cash corrections, immutable stock
facts, two distinct movements from one global split and restricted birja_app
reads. Cursor and limit negatives prove rejection before a query. No skipped,
xfail, manual schema or fabricated financial-authority substitute is used.

Initial tests corrected fixture expectations for the established two-decimal
cash wire, fresh mark label, actual stock_action_state health enum and stock
receipt trade_id; runtime economics and guards were not relaxed.

## Deviations from Plan

None in scope or delivery. The shared validate_portfolio_read helper lives in
the existing History service and is reused by mixed History; no new layer,
endpoint, grant or schema is introduced. All immutable economic records are
read-only and unchanged.

## Known Stubs

None in the scoped read paths delivered here. Actual production registration
and browser consumers are separately planned work, not claimed reachability.

## Carry Forward

- Plan15 must mount scoped valuation and History routes using the required
  portfolio argument, handle InvalidCursor as the existing private422, and
  refuse obsolete unscoped v1 financial routes. Current v1 read callers still
  supply user_id; whole-application typing/reachability is not claimed here.
- Plans20/22/25 must consume portfolio_id/name and retain explicit root context
  through cursor pages and embedded originals. Old cursor fixtures/parsers must
  move to trade2/mixed3 without accepting old unbound versions or hiding
  cross-root negative cases. Retained user-only valuation/History fixture
  adaptation remains part of Plan27's full-suite integration.
- Restricted TLS/cold recovery, security/images/full coverage, production route
  composition, browser journeys and owner UI/native200% acceptance remain
  pending. All28 milestone requirements stay unchecked; the six Phase7 live
  outcomes remain separately deferred with stock activation gated off.

## Self-Check: PASSED

Both task commits and all six output files exist, the assigned behavioral
gates pass, and no tracked file was deleted. Unrelated .claude/ remains
untouched. All changes are local on feature/milestone-v1.2.
