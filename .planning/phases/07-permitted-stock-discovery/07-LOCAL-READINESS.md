---
phase: 07-permitted-stock-discovery
assessed: 2026-11-11
status: local-implementation-ready-live-verification-deferred
final_verification: false
owner_ui_acceptance: accepted
live_activation: disabled
---

# Phase 7 local readiness assessment

The owner explicitly requested continuing without awaiting live data and checking
it later. This is a bounded assessment of current implementation and existing
local receipts, not final goal verification or completion of Plan 14. No phase
requirement is marked complete by this report. No code, dependency, service,
provider call, credential, scheduled process or production state was changed.

## Current roadmap criteria

| Criterion | Local evidence inspected directly | Local result | External result still required |
| --- | --- | --- | --- |
| 1. Twenty distinguishable stock identities alongside crypto, with reusable IEX attribution | `backend/alembic/versions/0010_seed_stock_catalog.py` contains the twenty fixed identities and listing exchanges, inserts generated instrument IDs without financial credits and leaves provider mappings unverified. `backend/app/services/stocks.py` selects this SEC-sourced catalogue. `frontend/src/pages/MarketsPage.tsx` renders `StockSection` independently beside crypto; `frontend/src/components/StockAttribution.tsx` supplies listing/preview/valuation contexts and visible single-venue/simulation wording. | VERIFIED implementation; owner UI accepted | Actual provider mappings, common-stock/USD corroboration and coverage remain deferred; catalogue metadata alone does not prove them. |
| 2. Bid/ask and source times, roughly minute collection, strict age/session eligibility | `backend/app/services/stock_quote_rules.py` validates exact Decimal sides, IEX venue/conditions, source age strictly below 120 seconds and current-session bounds. `backend/app/tasks/stock_scheduler.py` performs bounded collection with current mappings/admissions and post-await rechecks. `backend/app/services/stocks.py` returns original event times; `frontend/src/hooks/useStocks.ts` uses monotonic elapsed time plus full request duration to reduce freshness and permission windows. | VERIFIED implementation | Real access, all-twenty observations and actual eligible source ages are not established by synthetic tests. |
| 3. Product-specific permission gates, disabled fallback and independent crypto | `backend/app/services/stock_admission.py` checks each purpose, scope, fields, quota, validity and generation. `backend/app/core/config.py` defaults collection off and restricts private keys to scheduler settings. The API's final committed authority read precedes synchronous disclosure; expiry/retention redacts values. `backend/app/tasks/scheduler.py` isolates stock and crypto loops. Status/actions remain unknown and stock execution false. | VERIFIED local enforcement | Approval is owner-attested, not an independently inspected provider grant. Actual access and storage conditions are not inferred from keys or UI acceptance. No live activation/import is performed. |
| 4. Server-side regular sessions, holidays, early closes and DST | `backend/app/services/stock_sessions.py` builds XNYS/XNAS bounds using the actual approved calendar dependency, evaluates current migrator-owned authority and rejects mismatched derived rows. `stock_scheduler.py` and `stocks.py` consume these decisions. Session state cannot enable stock execution; the client never promotes a closed/unknown session to open. | VERIFIED implementation | Current real campaign results remain deferred. Actual order-time enforcement belongs to Phase 9 and is not claimed here. |
| 5. Existing accounts/history preserved, restricted-role verified-TLS compatibility | `backend/alembic/versions/0009_stock_discovery_schema.py` adds default-crypto classification without replacing financial IDs, grants app read-only discovery and scheduler bounded writes, and leaves admission authority privileged. Catalogue seeding never grants cash. `backend/app/services/trading.py` and `prices.py` explicitly retain crypto-only behavior. Existing actual TLS/restore receipts below corroborate populated upgrade and fresh bootstrap. | VERIFIED local compatibility evidence | No migration or deployment of this branch has occurred in production; this assessment grants no rollout permission. |

These are implementation verdicts, not five passed end-to-end roadmap criteria.
No missing or disconnected source artifact was found in this bounded pass.

## Data-flow check

The actual application wiring is `app/main.py` → `api/v1/router.py` →
authenticated `api/v1/stocks.py` → `services/stocks.py` → SQL catalogue, quotes,
admissions and sessions. The response is `no-store`. On the browser side,
`api/stocks.ts` validates the response, `hooks/useStocks.ts` owns authenticated
TanStack queries and expiry projection, and `components/StockSection.tsx`
renders identities, quotes and separate session/status facts on Markets.
The scheduler writes independently collected, admitted quotes to the same
persisted discovery state. This is real database-backed wiring with deliberately
empty provider state until admission and mapping prerequisites pass; it is not
evidence that live provider values have already flowed through it.

## Existing receipts checked

No suite was rerun for this documentation-only readiness assessment. The actual
saved outputs, rather than summary statements alone, were read:

- `/tmp/birja-phase07-plan13-backend-final2.log`: 969 passed in 54.59 seconds.
- `/tmp/birja-phase07-plan13-critical-final.log`: all 21 listed critical modules,
  1,221 statements and 304 branches, report 100% coverage.
- `/tmp/birja-phase07-plan13-frontend-final.log`: 310 tests across 28 files passed.
- `/tmp/birja-phase07-e2e-7ypm63gm/all-browser.log`: 20 passed; the existing
  production-CSP skip remains separately documented in `07-LOCAL-PROOF.md`.
- `/tmp/birja-phase07-plan13-all.log` and
  `/tmp/birja-phase07-plan13-roles-final.log`: actual populated-0008/no-grant-repair
  and fresh-bootstrap calendar consumer lanes report verified PostgreSQL TLS,
  bad-CA/hostname/plaintext rejection and restricted-role authority checks.

Full existing image, dependency, recovery and review evidence is retained in
`07-LOCAL-PROOF.md`, `07-REVIEW.md`, `07-SECURITY.md` and `07-UI-REVIEW.md`.
Those historical gates were not newly executed or expanded by this assessment.

## Remaining handoff

The owner's “i accept ui” is already recorded in `07-HUMAN-UAT.md`; no repeat
UI approval is needed. Individual manual viewport/keyboard checks are not
invented from that aggregate acceptance.

The authorized single 2026-11-11 17:30 Moscow campaign, maximum thirty read-only
attempts, remains exactly as documented in `07-ACTIVATION.md`. Its process and
results were not inspected or altered by this assessment. Later review must use
the actual sanitized receipt, record missing/stale cases and distinguish public
product facts, owner attestation and API observations. Waiting is not a pass.

Plan 14 and final live-data acceptance remain open. Preserve disabled activation,
unknown status/actions and disabled stock execution. No final `VERIFICATION.md`,
completed `07-14-SUMMARY.md`, Phase 8 execution, publication or deployment follows
from this local-readiness record.
