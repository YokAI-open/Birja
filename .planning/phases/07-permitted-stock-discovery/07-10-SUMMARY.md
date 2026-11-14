---
phase: 07-permitted-stock-discovery
plan: "10"
subsystem: api
tags: [stocks, postgres, admission, authentication, decimal]
requires:
  - phase: 07-01
    provides: Stable SEC catalogue and exact quote/session storage
  - phase: 07-05
    provides: Scoped purpose-specific admission evaluator
  - phase: 07-08
    provides: Migrator-authorized calendar and derived session evaluator
  - phase: 07-09
    provides: Independently persisted scheduler quote/session inputs
provides:
  - Authenticated no-store GET /api/v1/stocks with twenty stable metadata rows
  - Final committed admission/calendar read and fresh synchronous UTC projection
  - Exact string-money quotes with independent session/status/execution facts
affects: [07-11, 07-12, 07-13, 07-14]
tech-stack:
  added: []
  patterns: [Catalogue-first left join, Final READ COMMITTED evidence snapshot, Immutable response projection]
key-files:
  created: [backend/app/schemas/stocks.py, backend/app/services/stocks.py, backend/app/api/v1/stocks.py, backend/tests/test_stocks_api.py]
  modified: [backend/app/api/v1/router.py]
key-decisions:
  - "The final bounded Core query reloads current committed admission and session evidence without ORM identity-cache reuse. Unexpected isolation or failed evidence reads redact payloads."
  - "Permitted historical quotes retain original times and truthful ages for UI-SPEC last-quote display, without a recent or executable claim. Unknown calendar authority and mismatched quote generations still redact."
  - "Status remains explicitly unknown because no persisted verified halt/action facts exist in this phase. An open calendar never establishes normal status."
requirements-completed: []
requirements-addressed: [STOCK-01, STOCK-02, STOCK-03, DATA-01, MKT-01]
duration: 10min
completed: 2026-11-10
---

# Phase 7 Plan 10: Authenticated catalogue-first discovery Summary

**Twenty independently verified stock identities now have a protected discovery response whose quotes are projected only after a current committed admission/calendar query and fresh UTC evaluation.**

## Performance

- Approximately 10 minutes, 2026-11-10T18:55Z–19:05Z; two tasks, five owned source/test files.
- Local implementation is complete. Whole-phase requirements and permitted live discovery remain pending.

## Accomplishments

- Added `GET /api/v1/stocks` through the existing application router with `CurrentUserDep`, `DbDep`, explicit `StocksResponse`, `Cache-Control: no-store`, and `Vary: Cookie, Authorization`. No mutation, administration or provider proxy endpoint exists.
- The metadata-first query preserves all twenty stable curated SEC identities even when all quotes or permissions are missing. It left-joins quotes and orders by catalogue sort order plus unique ID. Crypto response keys, exact values and fifteen seeded identities remain isolated.
- Service performs three bounded reads: catalogue/quotes; preliminary sessions; one final statement returning at most six admission records and 273 current-horizon derived sessions, plus the actual transaction isolation. Core columns/JSON bypass ORM identity-map values. Exceeding admitted bounds or using isolation other than READ COMMITTED cannot establish permission.
- The final statement occurs after preparatory blocking work. Immediately afterwards the service samples fresh UTC, evaluates current quote display/derived rights and generation, validates current migrator-owned calendar review/overrides against derived generations, and builds an immutable Pydantic response. No further application await, network request or DB read follows projection in the service/handler. The boundary is this final statement snapshot plus immediately sampled clock; it cannot predict later revocations during delivery.
- Denial, expiry, stale quote generation, unknown/expired calendar authority, or failure of the final evidence read redact quote numbers and event/collection times. Independently verified metadata survives. Database exceptions/evidence references are never serialized.
- Decimal bid/ask/mid values remain JSON strings. Quote source and collection times remain distinct. Regular session, quote freshness, unknown status and phase-disabled execution are separate facts. All items have `execution_enabled=false`, `execution_reason=phase_disabled`; calendar-open never implies halt-free or actionable.

## Task Commits

1. **07-10-01 RED** — `3c1f637`: Specify catalogue-first stock discovery.
2. **07-10-01 GREEN** — `4c85c6b`: Project stocks from current committed authority.
3. **07-10-02 RED** — `9648d2c`: Specify authenticated stock response boundaries.
4. **Historical display RED** — `0a6c05c`: Distinguish historical display from fresh eligibility.
5. **07-10-02 GREEN** — `2fbb1fa`: Expose protected no-store stock discovery.

Task1 RED used an intentionally inert callable returning zero catalogue rows, yielding behavioral assertion failures rather than import failure. Task2 RED failed observable auth/route expectations. Historical-display RED observed six failures before projection was corrected.

## Verification

- Exact plan slice `uv run pytest tests/test_stocks_api.py tests/test_prices_api.py tests/test_stock_isolation.py -q` — **33 passed in 3.40 seconds**, including twenty stock tests.
- Same HTTP request pauses after a real preliminary PostgreSQL read. A second real connection commits quote revocation, permissive quote generation replacement, calendar generation replacement or a verified exceptional closure. Releasing that request proves its own final response uses current committed evidence and redacts invalidated payloads; prior-request revocation is also covered.
- Injected UTC changes after actual preparatory DB work test permission expiry, source age 119.999→120 seconds, regular-session close and calendar-review expiry. Exact server time and reason/state transitions are asserted. Historical quotes retain original source/collection timestamps and truthful ages; they never regain a recent/executable claim.
- An actual final database error (`SELECT 1 / 0` in the isolated test DB) yields metadata-only stock results without SQL/driver/error/evidence text. Missing permission and quotes preserve all twenty entries. No real provider request is made.
- Query instrumentation asserts exactly three service statements and no application DB work after immutable response construction. Auth, no-store/Vary, response key sets, no mutation route and preserved fifteen-row crypto byte-shape contracts pass.
- Scoped Ruff check, Ruff format check on all five owned files and mypy on all four source files pass. `git diff --check` passes; no tracked file deletion or dependency/image change.
- Four existing upstream calendar-package pandas deprecation warnings occurred; they do not fail the checks and no unrelated package was changed.

## Contract Disposition

The UI-SPEC explicitly requires dated last quotes while closed and truthful out-of-date displays. The initial conservative projection removed those values. Before Task2 completion, regression tests were changed to require permitted historical values while retaining independent stale/session-unavailable reasons; their observed RED failures were committed, then fixed. Owner/orchestrator direction confirmed this interpretation. This does not relax permission, generation, calendar authority or execution gates.

Final frontend interface is authoritative in `backend/app/schemas/stocks.py`: envelope `server_now`, `admission {state: approved|unavailable, generation, valid_until}`, `attribution {label, explanation, required_text}`, and twenty `items`. Each item includes metadata, nullable exact quote, session bounds/deadline/timezone, explicitly unknown status, execution-disabled fields and separate quote/session/status reason codes. Historical quotes may be non-null with `quote_reason=stale|session_unavailable`; only `recent` establishes the freshness claim, never execution. The frontend must preserve this distinction and locally enforce all supplied admission/calendar deadlines.

## Deviations from Plan

No scope expansion. The historical-display correction above reconciles the explicit UI contract with the plan's independent factual states. Calendar JSON and derived session evidence are reloaded together in the final query; scheduler rows cannot renew migrator-owned review. Status remains unknown because no trusted status storage exists, rather than inventing a successful status observation.

## Known Stubs

No stub prevents local discovery. Nullable quote/session fields represent real absent or denied evidence. Unknown status and disabled execution are required Phase7/8 behavior. Synthetic permission fixtures do not establish live rights or access.

## Next Plan Readiness

Ready for Plan11 strict frontend validation and auth/generation/deadline-isolated queries, then Plan12 UI. Actual restricted-role TLS consumer checks and complete phase gates remain Plan13. Provider rights, private current quote coverage/freshness and human UI acceptance remain explicit Plan14 checkpoints. Test-only PostgreSQL/Redis remain healthy for serial reuse.

No private configuration, production datastore/service, provider API/contact, B2 storage, publication or deployment was accessed or changed.

## Self-Check: PASSED

All five owned files exist and all five task commits above exist on the current branch. Exact verification passed; no tracked deletion or task-generated untracked file remains. Whole-phase requirements intentionally remain pending.
