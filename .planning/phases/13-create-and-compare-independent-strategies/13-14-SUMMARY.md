---
phase: 13-create-and-compare-independent-strategies
plan: "14"
subsystem: testing
tags: [postgresql, portfolios, decimal, concurrency, dividends, splits, restricted-roles]
requires:
  - phase: 13-06
    provides: Public authenticated creation and metadata APIs with exact current0020 grants
  - phase: 13-07
    provides: Shared exact bounded overview and individual statements
provides:
  - Public-created same-symbol crypto and stock buy/sell isolation with independent money oracles
  - Current0020 active historical dividends, corrections and splits through installed scheduler authority
  - Immutable original fills, deterministic instrument-lock ordering and bounded shared-job guards
affects: [13-15, 13-16, 13-17, 13-18]
tech-stack:
  added: []
  patterns: [public-created accounting fixtures, independent sessions, exact immutable evidence comparisons]
key-files:
  created:
    - backend/tests/test_portfolio_strategy_lifecycle.py
    - backend/tests/test_portfolio_strategy_events.py
  modified:
    - backend/tests/test_portfolio_creation.py
    - backend/tests/test_portfolio_metadata.py
    - backend/tests/test_portfolio_dividends.py
    - backend/tests/test_portfolio_entitlements.py
    - backend/tests/test_portfolio_splits.py
key-decisions:
  - "Retain every accounting assertion while moving owned fixtures to real current0020 and public-created roots; shared retained migration fixtures remain unchanged."
  - "This plan adds tests for accepted engines; no artificial production RED, runtime implementation or feature commit is warranted."
requirements-completed: [PFIN-01, PFIN-04, PMGT-01, PFUND-01, PFUND-02, PCTX-02, PSAFE-07]
duration: approximately25min
completed: 2026-11-18
---

# Phase 13 Plan 14: Newly Created Strategy Accounting Summary

**Public-created books independently buy and sell identical crypto and stock, receive exact historical dividend corrections and active splits once, and preserve immutable originals under real restricted authority and contention.**

## Performance and Task Commits

- Approximately25 minutes on2026-11-18;2/2 tasks, seven test modules.
- Task1: `4ee728c` — Prove newly created strategy financial isolation. Initial named group20passed in69.95s.
- Task1 supplement: `d1a38a2` — Preserve original fills through metadata edits. Final named group21passed in73.55s.
- Task2: `22eb447` — Prove active accounting across new strategy roots. Final named group60passed in151.91s.
- All seven owned modules pass Ruff lint and format checks; `git diff --check` passes. No tracked file was deleted.

## Delivered Evidence

Actual production `create_app` and its authenticated HTTPS cookie/CSRF routes create every new strategy identity. The existing Plan06 fixture authenticates a real `birja_app` login and installs the exact current source-owned `GRANTS_SQL` before production lifespan/admission. Accounts are not inserted by sibling fixtures. App stock collection remains OFF; synthetic market/calendar/admission evidence supplies isolated financial scenarios without provider credentials or network access. Scheduler business calls run under the installed `birja_scheduler` role, with role reset before pooled connections return.

Task1 independently checks BTC100mid with spread/fee and AAPL100bid/102ask. Both strategies buy identical assets; only the first sells. Expected first cash9794.50, AAPL1/basis102 and BTC1/basis100.50 remain separate from sibling cash9392.50, AAPL3/basis306 and BTC3/basis301.50. History has exactly the original root's SQL trade IDs and signed totals; overview/detail preserve financial/source parity while separate requests may advance observation ages. Overview totals and profit/loss are independently calculated, with no pooled balance.

Same/different-key crossasset races permit only one spend from a root, with exact aggregate fee rounding and an unchanged sibling. Concurrent rename/create and stock execution preserve name uniqueness, original financial identity and one10000 grant per genuinely created root. A separately connected uncommitted initial grant blocks explicit HTTP creation; rolling back that winner permits exactly one explicit root and journal without an initialization latch or extra baseline. Existing creation tests retain original-key parallel replay,9→10 cap, Unicode name collisions, rename/cap/closed/name-reuse replay, durable100/day grant quota,30/min owner and60/min IP attempt policy, lost responses, owner/CSRF/body/key refusals and rollback. Metadata now compares nonempty real stock fill facts, stock ownership, crypto holdings, trades, original grants and mixed History before/after rename/description changes.

Task2 starts with distinct2/4-share historical openings on actual newly funded books. Genuine scheduler ingestion/entitlement derivation and payment/correction services credit0.50/1.00, then append1.00/2.00 corrections for a0.75 rate, producing10001.50/10003 cash. Duplicate actual workers cannot multiply credits or decisions. Original payment JSON remains unchanged; public event History contains each root's attributable correction and immutable original. Uncertain replacements retain both originals, append one held decision per root, and change no cash.

Concurrent actual split processors return the same single global application. A2:1 split produces4/8 shares with unchanged20/40 basis; repeat application preserves effects and old dividend units remain2/4 at epoch0. Public History exposes each root's own quantity/basis effect. A later real stock buy changes current holdings without changing prior historical entitlement; subsequent corrections and metadata preserve original trades/fill-facts byte-for-byte.

A deterministic barrier observes a stock request reaching the real instrument gate while the scheduler owns it. Metadata and creation complete under that gate, the split commits, and the waiting stock order refuses changed unit evidence without a fill. Separate dividend/crypto/metadata/create contention completes with exact per-root cash. Retained tests preserve app/scheduler privilege refusals, malformed identities/fingerprints, foreign/crossed targets, historical sales, closed-root fixtures, negative correction affordability, held/reverse splits and all-or-nothing split rollback.

Worker pages are bounded by lowering the existing candidate ceiling for a real two-root cycle and proving cursor/restart replay cannot duplicate payment. Actual Kraken HTTP is mocked with `respx`: one shared cycle makes one request at two books and one request at ten books. The actual backup storage-capacity guard refuses over-budget synthetic inventory before any backup subprocess; created books and financial evidence remain unchanged. No public deletion or freeze activation is added.

## Verification Commands

All DB commands ran serially against owned disposable project `birja-p13-14`, using cached pinned PostgreSQL/Redis images and the existing Python3.14.9 environment. Synthetic stripped environment, fake prices and console email were retained.

```text
env -i PATH="$PATH" HOME=/tmp UV_OFFLINE=1 backend/.venv/bin/python -m pytest \
  --rootdir=backend backend/tests/test_portfolio_strategy_lifecycle.py \
  backend/tests/test_portfolio_creation.py backend/tests/test_portfolio_metadata.py -x -q
21 passed in73.55s

cd backend
env -i PATH="$PATH" HOME=/tmp UV_OFFLINE=1 UV_NO_SYNC=1 uv run pytest \
  tests/test_portfolio_strategy_events.py tests/test_portfolio_dividends.py \
  tests/test_portfolio_entitlements.py tests/test_portfolio_splits.py -x -q
60 passed,16 warnings in151.91s
```

The16 warnings are retained pandas/calendar timezone deprecations. An intermediate current0020 events/entitlements/splits run passed42 tests in86.08s; an intermediate current dividend/events run passed21 in75.25s. These overlap final groups and are not additional distinct qualification counts. No full coverage/security/image/recovery or browser/native200 campaign was run or claimed.

## Deviations from Plan

**1. [Rule3 - Blocking] Local current-schema accounting fixture adaptation.** Retained accounting modules imported an unowned fixture that explicitly asserted0017 and inserted accounts without the new canonical metadata authority. Rather than weaken that assertion, downgrade current runtime or modify shared fixtures, the owned lifecycle module now supplies the same case contract using current0020 production admission, installed exact grants and HTTP-created roots. Entitlements/splits import that fixture and keep their economic assertions unchanged. Dividend fixtures similarly derive current actual entitlements on new public roots, preserving their100cash affordability/spending oracles through explicit disposable cash setup while keeping original10000 baselines and journals immutable. Committed in `22eb447`.

**2. Test-only TDD handling.** Both tasks qualify accepted existing engines. Per execution authorization, tests were authored before verification without inventing a runtime failure, artificial feature implementation or production GREEN commit. Plan frontmatter is autonomous rather than a whole-feature `type:tdd` plan. No engine defect requiring a parent runtime replan was established.

Test authoring corrections resolved actual wire field names/signed totals, aggregate fee rounding and internally consistent supported split source dates. The baseline immutability trigger correctly refused an attempted legacy fixture baseline rewrite; only mutable cash is seeded. No financial trigger, admission or source authority was disabled to make tests pass. The initial sandbox local-socket refusal was resolved by scoped escalation for the disposable test services, not an authentication gate.

## Cleanup and Limits

- Exact-owned Compose containers/network were removed with `down -v`. Project-label queries for containers, networks and volumes return empty. The exclusive DB lane is released.
- No production code, shared conftest/migration inventory, dependency, lockfile, image/Python pin, private environment, provider, production database, deployment, push or merge change occurred. Unrelated `.claude/` remains preserved.
- Existing issue35 acceptance retains its exact scope and2026-12-17T00:00:00Z deadline; approved Python image pin20261111 and Phase7 OFF/live-gap boundaries remain unchanged.
- Stub scan found no unfinished stub. Empty collections are expected absence assertions or bounded test setup. These test changes introduce no new production threat surface beyond the plan's existing financial boundaries.
- Parent owns STATE/ROADMAP/REQUIREMENTS updates and independent review. Requirement IDs record this plan's contribution, not whole-requirement or phase acceptance. Plans15/17 still own inventory completion and whole campaigns; UI/native200 acceptance remains later work.

## Self-Check: PASSED

Both created test modules, all five modified test modules and this summary exist. Task commits `4ee728c`, `d1a38a2` and `22eb447` resolve. Final named groups pass, seven-file static checks pass, and no tracked deletion or owned disposable resource remains.
