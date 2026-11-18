---
phase: 13-create-and-compare-independent-strategies
plan: "07"
subsystem: api
tags: [portfolios, decimal, valuation, stock-authority, ownership, bounded-sql]
requires:
  - phase: 13-06
    provides: Actual private management routes and finalized restricted0020 test authority
provides:
  - Shared bounded financial snapshots and common per-root valuation assembler
  - Private bounded overview with exact independent statements and metadata
  - Original-stock-proof, current-authority, shared-time and late-closure race proofs
affects: [13-08, 13-11, 13-12, 13-14, 13-15, 13-17]
tech-stack:
  added: []
  patterns: [two-statement batch snapshots, ordered shared root locks, shared statement conversion]
key-files:
  created: [backend/tests/test_portfolio_overview.py]
  modified:
    - backend/app/services/portfolio.py
    - backend/tests/test_portfolio_valuation.py
    - backend/app/schemas/portfolios.py
    - backend/app/api/v2/portfolios.py
key-decisions:
  - "Overview replaces detail's portfolio_id with canonical id and adds description; all other statement fields retain their existing meaning."
  - "Final membership uses ordered FOR SHARE locks until the existing request transaction releases, preventing closure between the last awaited read and response serialization."
requirements-completed: [PVIEW-01, PVIEW-02, PSAFE-07]
duration: 23min
completed: 2026-11-18
---

# Phase 13 Plan 07: Shared Bounded Portfolio Statements Summary

**One captured financial snapshot, shared current authority and exact Decimal calculation now power private comparisons and individual portfolio statements without pooling strategy wealth.**

## Performance and Task Commits

- Approximately09:54–10:17UTC on2026-11-18;2/2 tasks, five implementation/test files.
- Task1 RED `0c6d5bb`: missing load_portfolio_snapshots fails after actual0020 restricted application setup succeeds.
- Task1 GREEN `f8ccf5e`: shared loader/common assembler and owned valuation fixture adaptation. Fifteen overview cases and twenty valuation cases pass through the recorded focused runs; expanded ten-root mixed holdings and advancing-time cases are explicitly verified.
- Task2 RED `1d78ce9`: actual production /overview returns422 through the old dynamic-ID route before implementation.
- Additional race RED `09027cc`: an independent closer commits after the final awaited query, reproducing an unprotected response assembly window. Also records actual mixed-asset HTTP parity and strict schema assertions.
- Task2 GREEN `c47523c`: private overview and ordered shared membership protection. Final combined41-case regression and final57-case overview/management-schema regression pass.

Both tasks have actual RED before GREEN. No tracked file deletion occurred.

## Delivered Behavior

`load_portfolio_snapshots(db, owner_id, portfolio_ids=None, settings, now=None)` selects all active owned roots, or validates every explicitly requested root. Empty explicit IDs return an empty tuple without SQL. Malformed IDs, duplicates and more than ten explicit IDs refuse422. Missing/foreign/closed explicit roots refuse404 without partial output. An eleven-root corrupted overview refuses409 rather than truncating.

One bounded ordered roots/holdings/crypto marks/stock evidence/original-proof statement captures financial values. One final statement obtains shared current authority and rechecks active membership with ordered FOR SHARE locks. Both overview and get_portfolio use the common assembler; neither loops over get_portfolio, polls providers per book, nor concurrently uses an AsyncSession. Financial loading is at most two SQL statements independent of0–10 roots; actual overview HTTP uses at most three total statements including its real session/authentication check.

Original stock proof correlates both owner and portfolio to the holding's coin and quote generation. A sibling without its own proof stays incomplete while an independently proven book remains usable. Common evidence is projected once; every book has the same valued_at, sampled after both awaits. Newer quotes never replace the captured financial price. Changes to unit/action epochs or permissions invalidate captured stock marks. Advancing time after the final await expires rights rather than renewing them. Existing halted/closed dated marks, original source times, safe-unit flags, unavailable average cost and incomplete-value semantics remain intact.

Each book retains its stored baseline, cash, holdings and exact return. Tests independently check a7654 legacy baseline, zero-baseline unavailable percentage, same-symbol quantities, complete and incomplete books, known cash/value and unavailable overall returns. Monetary JSON remains decimal strings; no JS float, annualized ranking or pooled total is added. Existing trading and History records are untouched.

## Exact Transport Handoff for Plan08

GET `/api/v2/portfolios/overview` is registered before `/{portfolio_id}` on the actual production router. It returns an array with at most ten records in ascending numeric ID order. Each record has exactly these19 keys:

```text
id, name, description, cash, starting_cash, total_value, total_pl,
total_pl_percent, cash_allocation_percent, valuation_complete, known_value,
unvalued_holding_count, class_values, class_allocation_percent, valued_at,
prices_as_of, fresh_seconds, stale_seconds, holdings
```

`id` is a canonical bigint string. `holdings` uses the existing HoldingOut contract, including stock_mark, price/status/source time and original safety semantics; class values/allocation use their existing statement types. Nullable totals/returns mean unavailable, not zero. Every row shares valued_at; prices_as_of remains that book's oldest available captured source time, or null. There is no duplicate portfolio_id in overview.

Existing GET `/api/v2/portfolios` remains exactly `[{id,name}]`. Existing detail GET keeps exactly its original PortfolioOut shape, including portfolio_id and no description. Overview conversion calls PortfolioOut.from_value, then replaces only identity and adds description. The new model forbids extra fields; its list and actual OpenAPI response enforce maxItems10. Financial types are bound after imports via model_rebuild to preserve the existing low-level PortfolioId dependency without an import cycle; this follows [Pydantic's model rebuilding pattern](https://docs.pydantic.dev/latest/concepts/models/#rebuilding-model-schema).

Owner/active boundaries and private no-store/Vary headers apply to success and refusal. A foreign owner's overview contains only that owner's active roots; signed-out requests refuse401. No new CSRF exemption, financial mutation or public lifecycle action is introduced.

## Verification Evidence

All backend tests used existing Python3.14.9, a stripped synthetic environment, the owned cached-image disposable stack, fake prices and console email. The explicit current0020 harness authenticates a real birja_app connection and actual production lifespan/admission; no temporary router is mounted.

```text
env -i PATH="$PATH" HOME=/tmp UV_OFFLINE=1 backend/.venv/bin/python -m pytest \
  --rootdir=backend backend/tests/test_portfolio_overview.py \
  backend/tests/test_portfolio_valuation.py -x -q \
  --cov=app.services.portfolio --cov-branch --cov-report=term-missing --cov-fail-under=0
41 passed in135.38s; scoped service coverage98%, only explicit empty-ID return unexecuted.

env -i PATH="$PATH" HOME=/tmp UV_OFFLINE=1 backend/.venv/bin/python -m pytest \
  --rootdir=backend backend/tests/test_portfolio_overview.py \
  backend/tests/test_portfolio_management_api.py -x -q \
  --cov=app.services.portfolio --cov-branch --cov-report=term-missing --cov-fail-under=100
57 passed in68.36s after adding the zero-SQL explicit-empty assertion.
```

The final shared service reaches100% statement/branch coverage:86 statements,26 branches, no missed or partial branches. This is one scoped critical module, not the full critical inventory or security gate. The57-case command comprises21 overview cases plus36 retained management boundary/schema cases; it overlaps the41-case run rather than representing98 distinct cases. Whole backend `mypy app` passes103 source files. Changed five-file Ruff lint/format, three-source focused strict typing and git diff checks pass.

Query event capture proves at most two financial statements for0/1/10 roots and exactly two for2/10 same-symbol stock books, including mixed crypto and independently unproved stock holdings. Actual mixed HTTP overview/detail rows are identical at fixed time after the documented identity/description conversion; independent expected money and custom baselines are asserted. The original thirteen valuation cases still pass, including freshness boundaries and halted/closed dated marks.

## Deviations from Plan

**1. [Rule3 — Blocking] Local current-schema fixtures.** Retained shared migration provisioning still records0017 and older imported Account fixtures omit canonical name_key. The owned valuation test locally reuses Plan06's explicit authority/lifespan harness and supplies canonical current-schema sibling fixtures, preserving every existing assertion and stored7654 baseline. Shared conftest, migration admission, unowned fixtures and schema guards remain untouched. Baseline setup inserts original values; the immutable baseline UPDATE guard was not bypassed. Commit:`f8ccf5e`.

**2. [Rule2 — Correctness] Protect the final ownership check through response assembly.** The initial membership recheck caught closure during the first await but could return stale ownership if closure committed after the final query and before Python resumed. RED09027cc reproduces that exact window with an independent actual writer. The same final statement now acquires stable-order shared Account locks using existing privileges. The competing closer receives actual55P03 with a50ms test-only lock timeout; once the reader transaction closes, closure succeeds and the next overview is empty. Commit:`c47523c`.

The service never commits/releases these locks. Existing get_db yields its session until request completion. Installed FastAPI0.162.0 source confirms Pydantic JSON serialization occurs inside the route handler, with the default request dependency stack exiting after response sending. The lock therefore protects the response's authorization window; it does not claim that a returned snapshot remains current after request completion. No instrument lock, new privilege, SQL statement, writer or lock-order inversion was introduced.

Routine test corrections used the required price source column, actual stored action epoch and existing unsafe-unit transport semantics. The schema's deferred references resolve an import cycle within the owned files. No architecture, dependency or financial authority changed.

## Cleanup, Limits and Next Readiness

Owned Compose project birja-p13-07 containers/network were removed; exact label queries for containers, networks and volumes are empty. Only cached pinned images and disposable tmpfs on guarded55432/56379 ports were used. No private environment, provider, production, package/lock/pin, push, merge or deployment operation occurred. Unrelated.claude remains preserved. Issue35's exact accepted-risk deadline2026-12-17T00:00:00Z, Python image pin20261111 and Phase7 live OFF remain unchanged.

No goal-blocking stub or unplanned security surface was found. Empty description defaults and collection accumulators are intentional. The new endpoint is the planned authenticated read boundary; there is no additional schema/auth/network surface requiring a threat flag.

Parent owns independent review and STATE/ROADMAP/REQUIREMENTS updates; these files were not edited or staged. Requirement IDs record this plan's contribution, not final whole-requirement acceptance. Plan08 can consume the exact contract above. Plans15/17 still own complete inventories, whole suites, critical/security gates and full encrypted/TLS/image/recovery qualification. Browser/UI/native200 acceptance remains later work; no full phase/campaign result is claimed here.

## Self-Check: PASSED

All five implementation/test paths and this summary exist. All five task commits resolve, with RED preceding GREEN for both tasks and the final-await repair. Focused tests, source typing/lint/format, diff checks and owned-resource cleanup pass. Only unrelated.claude remains untracked before the summary commit.
