---
phase: 10-dividend-cash-and-event-history
plan: "11"
subsystem: event-history-api
tags: [authenticated-history, no-store, exact-wire, legacy-compatibility, portfolio]
requires:
  - phase: 10-10
    provides: Strict mixed-event schemas, owner-first projection and cursorv2
  - phase: 10-07
    provides: Actual restricted dividend and hold transaction services
  - phase: 10-08
    provides: Guarded committed financial fixture and concurrent accounting proof
  - phase: 10-06
    provides: Passed exact retained recovery and restricted-role/TLS prerequisite
provides:
  - Authenticated no-store GET /api/v1/history with bounded fixed input errors
  - Real-cookie owner isolation and immutable offpage Dividend lineage proofs
  - Legacy cursor separation and actual once-only Portfolio dividend integration
affects: [10-09, 10-13, 10-14, 10-15, 10-16, 10-17]
tech-stack:
  added: []
  patterns: [thin-owner-bound-route, exact-response-model, fixed-no-store-errors]
key-files:
  created:
    - backend/app/api/v1/event_history.py
    - backend/tests/test_event_history_api.py
  modified:
    - backend/app/api/v1/router.py
    - backend/tests/test_history_api.py
    - backend/tests/test_portfolio_snapshot.py
key-decisions:
  - Cookie identity alone selects the owner; query-supplied owner/reference values confer no authority.
  - Fixed limit/cursor errors also carry no-store and never echo untrusted values.
  - Preserve existing Portfolio arithmetic and legacy History implementation unchanged.
requirements-completed: []
requirements-supported: [HIST-03, DIV-03, DIV-05]
duration: approximately10min
completed: 2026-11-13
---

# Phase10 Plan11: Authenticated mixed History and once-only cash

**The new private History endpoint projects exact retained events and linked
originals through the current session, while legacy trades and Portfolio keep
their existing accounting and cursor behavior.**

## Tasks and commits

1. RED `d1cce8b`: a genuinely signed-in request returned404 instead of the
   expected200 private empty page;1failed/1.47s. GREEN `5e30e0a`: thin route,
   router registration and23 API tests/3.19s, route16statements/2branches100%.
2. `3b39500`: actual dividend/correction cash integration, held/pre-anchor
   uncertainty, preserved stored labels and legacy/mixed cursor separation.
   Combined API/legacy/Portfolio gate40passed/5.90s.

The route uses CurrentUserDep and DbDep, an explicit EventHistoryPage response
model, limit25 default/range1..100 and the existing strict cursor≤512 decoder.
It calls one owner-bound service, maps invalid input to fixed422 detail, adds
Cache-Control:no-store on success and its own input errors, and performs no
external fetch or financial write. Existing401 authentication is preserved.
OpenAPI exposes only limit/cursor, never an owner parameter. Response headers
use the established project pattern and official
[FastAPI response-header guidance](https://fastapi.tiangolo.com/advanced/response-headers/).
Context7/ctx7 were unavailable; no tool or package was installed.

## Actual verification

| Gate | Result |
|---|---|
| Behavioral authenticated request RED |1failed/1.47s; actual404 rather than import failure |
| Task1 API/owner/error/paging gate |23passed/3.19s; route100% statements/branches |
| Task2 API/legacy/Portfolio gate |40passed/5.90s |
| Final affected API/History/dividend/Portfolio gate |286passed/10.94s;4 existing pandas warnings |
| Four affected critical modules |304statements/126branches,0 missing/partial,100% |
| Scoped Ruff/format |All5 owned source/test files pass |
| Scoped Mypy |Both owned application modules pass |
| Whitespace/deletion/owned-file checks |Pass; no tracked deletion |

Final command uses existing locked `uv run --no-sync --no-cache pytest` for
event_history_api, history_api, history_service, portfolio_snapshot,
event_history, event_history_cursor, dividend_payments and dividend_corrections,
with coverage on api.v1.event_history, services.event_history,
schemas.event_history and services.dividends, `--cov-branch --cov-fail-under=100`.
Logs: `/tmp/birja-phase10-11-task1-red.log`,
`/tmp/birja-phase10-11-task1-green.log`, `/tmp/birja-phase10-11-api.log`,
`/tmp/birja-phase10-11-task2-final.log`, `/tmp/birja-phase10-11-affected.log`.
Coverage data: `/tmp/birja-phase10-11.coverage`. Parent owns the full Wave7 gate.

Real cookie/OTP authentication, actual restricted SQL original/correction/hold
services and PostgreSQL records prove: default25 plus continuation, exact
Decimal/date strings, canonical cursorv2 and rejection of legacyv1/malformed
512/513-character inputs, owner isolation despite editable boundaries or forged
query owner/payment/decision values, and no mutation from repeated reads.
PaidA then uncertain/cancelledB returns the original offpage inside its linked
held correction, explicit null unknown terms/target/proposal, and applied cash0.
Repeated hold attempts add no record. A different signed-in user receives no
foreign original/decision even with their IDs supplied. Public error bodies
do not echo input text or database/provider details.

Actual shared cash100→101 original→101.50 verified correction is read once by
Portfolio, with starting_cash10000 unchanged. Replay does not add cash/events;
held uncertainty changes no cash; known valuation uses cash plus holdings only.
Legacy `/trades` fields/total/cursorv1 remain compatible and reject cursorv2;
mixed History rejects cursorv1. Stock catalog rename cannot rewrite saved
Dividend/correction output. Before any original, uncertain evidence creates no
fabricated Dividend after three refused attempts and reads.

## Deviations and fixture corrections

- Task2 is test-only proof of existing correct legacy/Portfolio behavior. Its
  initial financial assertions passed; no artificial production defect or RED
  was introduced. Task1 has an actual behavioral RED→GREEN pair above.
- Plan09's scheduler is not implemented yet. These API tests use the actual
  current restricted transaction service/SQL; scheduler→SQL→History integration
  remains Plan09 and is not claimed executed here.
- An initial test-only missing `text` import was corrected before execution.
  The first Task2 run reached39passes, then a later fixture refused the renamed
  synthetic catalog symbol. Restored only that owned row; the rename test now
  captures and restores its actual original symbol/name in finally. Final40
  and286-test runs pass with no reset, row deletion or invariant relaxation.
  Earlier log `/tmp/birja-phase10-11-task2.log` remains a failed attempt.
- No Portfolio arithmetic, legacy service/route, SQL authority, schema/index,
  recovery, grant policy, dependency or image change was needed. Parent owns
  canonical STATE/ROADMAP/requirements; no whole requirement is marked complete.

## Cleanup, threats and remaining gates

Final independent owned-database query: head0014; originals0, decisions0,
entitlements0, temporary scheduler roles0, disabled immutability triggers0,
pending clients0, owned renamed catalog residue0; migrator cash UPDATE and
payment INSERT privileges both false. Existing test fixture cleanup restored
only its temporary grants/role. Only birja-test stays running for parent.

T-10-11-01/02 mitigated by current-user binding, actual foreign-user/forged-input
tests, strict output model, preserved immutable lineage and genuine cash checks.
T-10-11-03 mitigated by bounded page/cursor work and no external call or financial
mutation. T-10-11-SC: no installation/package/lock/image change. No new trust
surface beyond the planned authenticated read endpoint, and no known stubs.
Required null uncertainty fields are truthful retained data, not placeholders.

No real.env/secrets, provider, production, B2, timer, installed-tool, push or
deployment operation occurred. Live activation stays deferred. Scheduler/client/
UI/browser integration, final recovery/security gates and real owner new-UI/native
200% acceptance remain later plans; prior synthetic proof does not satisfy them.

## Self-Check: PASSED

All5 owned source/test files and this summary exist. Task commits d1cce8b,
5e30e0a and3b39500 exist without deletion. Actual286 tests, strict100% coverage,
static checks and final cleanup pass. Unrelated `.claude/` and canonical project
state are preserved; DB ownership is released to parent.
