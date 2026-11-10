---
phase: 05-portfolio-and-history
plan: "04"
subsystem: history
tags: [fastapi, postgresql, keyset, react, tanstack-query, security]
requires:
  - phase: 05-03
    provides: Completed portfolio slice and serial isolated-database verification baseline
provides:
  - Authenticated read-only stored-fill history with strict versioned keyset cursors
  - Exact signed cash totals, microsecond boundaries and bigint string identities
  - Reachable first-page History table/mobile cards with guarded abortable infinite query
affects: [05-05, 05-06, 05-07, 05-08]
tech-stack:
  added: []
  patterns: [Bound scalar tuple seek, Canonical bounded stdlib cursor, Unpolled infinite query]
key-files:
  created:
    - backend/app/services/history.py
    - backend/app/schemas/history.py
    - backend/app/api/v1/history.py
    - backend/tests/test_history_service.py
    - backend/tests/test_history_api.py
    - frontend/src/api/history.ts
    - frontend/src/api/history.test.ts
    - frontend/src/hooks/useHistory.ts
    - frontend/src/pages/HistoryPage.tsx
    - frontend/src/pages/HistoryPage.test.tsx
  modified:
    - backend/app/api/v1/router.py
    - backend/tests/test_accounts.py
    - frontend/src/App.tsx
    - frontend/e2e/portfolio-history.spec.ts
key-decisions:
  - Cursor payloads require compact canonical JSON and unpadded canonical base64url; identity always comes from the session.
  - Validate page-size query text explicitly before integer conversion to reject coercible noninteger forms.
requirements-completed: [HIST-01, HIST-02]
requirements-status: Plan implementation evidence only; Load more UX and phase acceptance remain with later gates.
duration: 8 min
completed: 2026-10-30
---

# Phase 5 Plan 4: Stored Trade History Summary

**Signed-in users can inspect exact persisted fills through a private cursor-backed API and a real first-page History view.**

## Performance

- **Duration:** Approximately 8 minutes, including required context, RED/GREEN and verification.
- **Started:** Approximately 2026-10-30T07:21:00Z.
- **Completed:** 2026-10-30T07:29:00Z.
- **Tasks:** 2/2.
- **Source/test files changed:** 14.

## Accomplishments

- GET `/api/v1/trades` is additive beside the unchanged POST contracts, authenticated through CurrentUserDep, read-only and `Cache-Control: no-store`. A scalar Trade/Coin projection includes inactive coins and maps stored `cash_delta` directly to signed `total`; it does not reconstruct amounts or apply another fee. Decimal values use plain JSON strings and history IDs use strings.
- The stdlib codec bounds input to 512 characters, enforces canonical unpadded base64url and compact JSON, rejects duplicate/missing/extra keys, excludes bool/float/string versions, requires exact UTC timestamps with six microsecond digits, and validates positive decimal-string IDs within signed bigint. Parser failures return structured 422 `invalid_cursor` with fixed copy. Page sizes default to 25, accept 1..100, and reject coercible invalid text before conversion.
- Every query keeps the session-derived user predicate, uses bound `(created_at,id)` tuple seeks, orders newest first with ID tie-breaking and requests `limit+1`. The cursor comes from the last returned row only when lookahead exists. Real PostgreSQL tests prove tied timestamp traversal, no skipped lookahead/duplicate rows, fresh visibility of newer inserts, inactive fills, zero-proceeds sells, and IDs beyond JavaScript's safe integer range. Forged/foreign cursor boundaries never grant another user's fills.
- `/history` is reachable from the signed-in shell. The guarded API wrapper preserves money and ID strings and forwards AbortSignal. The infinite query has no polling, uses opaque continuation parameters, refetches on stale focus/re-entry and invalidates `me` after final 401. Desktop semantic table/row headers and ordered mobile definition lists show local full timestamps with exact UTC detail, neutral Buy/Sell, quantity, execution price, fee and signed total cash change. Loading, initial retry, successful empty state, pending refresh and retained-data retry remain distinct.
- Added a CI-only fake-price/console-email browser case that captures the actual fill response and compares displayed fee, quantity, execution price and negative total. Its price-change reconfirmation is bounded to three attempts.

## Task Commits

1. **Task 1: Specify failing real history and strict seek behavior** — `4a39280` (test).
2. **Task 2: Make actual stored trade history reachable** — `44439c9` (feat).

## Verification

- **RED backend:** Required service/API command failed at collection because `app.services.history` did not exist. **RED frontend:** Required guard/page suites failed because the history wrapper and page did not exist. These are missing-capability failures, not broken fixture setup. The subsequent GREEN run exercised the actual guarded PostgreSQL fixtures successfully.
- **GREEN backend:** `test_history_service.py`, `test_history_api.py`, `test_accounts.py`, and existing `test_trades_api.py` — **93 passed**. This includes the exact route allow-list, stored values, no-store/401/read-only behavior, bounds, strict parser matrix, ties, lookahead, inactive/high-ID fills and service/API user isolation.
- **GREEN frontend:** History API, HistoryPage and App — **41 passed** across three files. Tests include runtime string guards, decimal/exponent rejection, cursor bounds, malformed timestamps, real first-page fields, initial/retained errors, retry, no false end message, disabled in-flight refresh and abort on unmount.
- Backend changed files pass Ruff lint and format; mypy passes all **49 application modules**. Frontend ESLint, TypeScript and changed-file Prettier pass. `git diff --check` passes. No tracked file deletions occurred.
- `npm run e2e -- --list` discovers **7 tests in 6 files**, including the new stored-history case. Discovery is not an executed browser pass. No browsers, dev/prod authentication, trades, real email, rebuilds or deployment were performed.
- All database runs were serial on the isolated `docker compose --env-file /dev/null -f /home/YokaiExchange/docker-compose.test.yml` stack. Every run used Python `finally` to execute absolute-path `down -v`. No dev/prod data or secrets were inspected.

## Decisions Made

Followed the existing design system and approved UI-SPEC. The UI skill's generic design-system result was off-target for Birja and was not applied; the React semantic-HTML guidance fits this table/list view. No dependencies, signing secret, schema/migration, authorization mechanism or financial execution behavior changed. TanStack infinite-query and SQLAlchemy tuple APIs were checked against official documentation after the local ctx7 CLI was found unavailable.

## Deviations from Plan

None in product scope. The plan's two tasks already divide RED specification and GREEN implementation, so one RED task commit precedes one GREEN task commit. Formatting and additional cancellation/foreign-boundary assertions were completed with the GREEN commit. Shared STATE/ROADMAP/REQUIREMENTS/config updates remain the orchestrator's responsibility under the assigned ownership boundary.

## Issues Encountered

The first host uv lint invocation could not write its cache under the sandbox; the authorized local check was rerun with escalation. SQLAlchemy's type checker requires explicit `literal(...)` elements for the right-hand tuple; these remain bound SQL values and all database regressions pass. No blocker remains.

## User Setup Required

None.

## Next Phase Readiness

Ready for 05-05: the API and infinite query expose the real next cursor. That plan owns Load more/retry/end-focus controls and the reversible concurrent history index. No fake end marker is displayed while more data exists. 05-06 owns fill invalidation/private-cache identity lifecycle; 05-07/05-08 retain full phase coverage/review, CI browser execution and responsive human verification. No claim of completed HIST-02 user pagination acceptance is made by this first-page plan alone.

## Self-Check: PASSED

All ten newly created source/test files exist, both task commits resolve, scoped checks pass, and no unknown generated files remain. The pre-existing untracked `.claude/` directory was preserved.
