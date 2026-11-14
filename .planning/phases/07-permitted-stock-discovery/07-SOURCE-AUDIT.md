# Phase 7 — Multi-Source Coverage Audit

**Status:** full planning coverage; independent checker and execution pending. COVERED denotes an executable task or legitimate gate, never implemented/live evidence. No CONTEXT.md exists.

| Source | ID | Obligation | Plans | Status |
|---|---|---|---|---|
| GOAL | SC1 | Exactly20stable common stocks,15crypto, IEX attribution | 01,02,10,11,12,14 | COVERED |
| GOAL | SC2 | Source-event bid/ask, minute collection, strictage and reopen safety | 06,08,09,10,12,14 | COVERED |
| GOAL | SC3 | Actual product rights/access/quota/attribution; denied branch | 05,09,10,11,13,14 | COVERED |
| GOAL | SC4 | Server regular sessions, holidays/earlyclose/DST, no executable claim | 07,08,09,10,12,14 | COVERED |
| GOAL | SC5 | Original financial rows, restricted verified-TLS roles and migrations | 01,02,03,04,13 | COVERED |
| REQ | STOCK-01 | Approved requirement preserved in full | 01,02,10,11,12,14 | COVERED |
| REQ | STOCK-02 | Approved requirement preserved in full | 10,11,12,14 | COVERED |
| REQ | STOCK-03 | Approved requirement preserved in full | 06,08,09,10,11,12,13,14 | COVERED |
| REQ | DATA-01 | Approved requirement preserved in full | 05,06,09,10,11,12,13,14 | COVERED |
| REQ | MKT-01 | Approved requirement preserved in full | 07,08,09,10,12,13,14 | COVERED |
| REQ | SAFE-01 | Approved requirement preserved in full | 01,02,03,04,09,13,14 | COVERED |
| RESEARCH | Identity | Physical coin/FKIDs, asset+symbol uniqueness, stock-null Kraken mapping, separate seed | 01,02 | COVERED |
| RESEARCH | Catalogue A2 | SEC-provenance candidates and bounded approved private20symbol identity verification | 01,14 | COVERED |
| RESEARCH | Quote rules | Raw Decimal/conditions/feed validation; source versus collection;119.999/120;future/old/equal/reorder races | 06,08,09,10 | COVERED |
| RESEARCH | Calendar A1 | ASSUMED package/transitive legitimacy gate before install;actual3.14lock/image proof | 07,08,13 | COVERED |
| RESEARCH | Calendar policy | Official XNYS/XNAS, 45/90-day bounds and24h review; migrator-owned calendar admission evidence/overrides, derived session generation, current-evidence/fresh-UTC consumers and real role denial | 01,03,04,05,08,09,10,12 | COVERED |
| RESEARCH | Status | Open+recent does not establish halt-free; unknown remains separate; timely-source external gate | 05,08,09,10,12,14 | COVERED |
| RESEARCH | Admission | Reference/quotes/actions/status separately; collection/display/derived/retention/scope/attribution/quota | 05,09,10,14 | COVERED |
| RESEARCH | Revocation | Generation/expiry checked before fetch/store/exposure; final committed evidence and UTC after request awaits; current-request blocked-read transitions and client RTT/deadline purge | 05,09,10,11,12 | COVERED |
| RESEARCH | Scheduler | One process independent leases/budgets/cadence/cancellation; no per-user provider calls | 09 | COVERED |
| RESEARCH | Read model | Authenticated no-store catalogue leftjoin, all20metadata rows, nullable exact-money payload | 10 | COVERED |
| RESEARCH | UI | Independent queries, allstates/copy/layout, no stock Trade links, responsive/accessibility | 11,12,14 | COVERED |
| RESEARCH | Legacy bypass | Explicit crypto filters at all catalogue/price/trade/holding paths, collision tests | 02,09,10 | COVERED |
| RESEARCH | Recovery | Versioned exact tables/columns/hashes/constraints/identities; old0007/0008 and retained packages | 03,04 | COVERED |
| RESEARCH | Roles | Revision0009 owns conditional grants/revocations and session identity USAGE; app reads, scheduler data-only writes, migrator ownership; actual TLS upgrade allow/deny without post-upgrade bootstrap repair | 01,04 | COVERED |
| RESEARCH | Test gates | RealPG/HTTP/browser;original+new100%critical/80%overall; strict actualimage/dependency scans | 01–13 | COVERED |
| RESEARCH | Environment | No host upgrades/global packages/privateprod probes; runtime proof in isolated fixture | 04,07,08,13,14 | COVERED |
| RESEARCH | Live honesty | Fixtures/API credentials cannot grant rights or prove live20stock discovery | 05,13,14 | COVERED |
| CONTEXT | Absent | No CONTEXT.md; do not invent D-XX. Approved requirements/owner choices are binding | All | COVERED |
| CONTEXT | Owner choices | Conditional IEX/visiblelabel/exact20/sharedcash/crypto preserved/stockexecutionoff7–8 | 01,02,05,10,11,12,14 | COVERED |

## Exclusions, not missing work

| Item | Disposition and source |
|---|---|
| Stock fills/previews/whole-share orders/post-lock execution checks | Phase9 STKTR/MKT-02; Phase7 provides reusable rules and closes legacy bypasses only. |
| Dividend announcements/eligibility/splits/monitoring/reconciliation | Phase8 DIV-01/02/ACT; Phase7 defines product gates and truthful unknown states. |
| Combined stock holdings and portfolio marks | Phase9 PORT; only reusable attribution is built here. |
| Dividend payments/corrections and event History | Phase10; no speculative accounting tables in Phase7. |
| Full mixed-asset dividend/action recovery | Phase11; current Phase7 schema proof remains mandatory03/04. |
| SDK/queue/WebSocket prices/provider registry | Research explicitly recommends existing HTTP/single scheduler instead. |
| Paid data, alternate feed, provider contact/signup/agreement, production tools/install/deploy | Not authorized; separate scoped owner decision required. |
| W01–W08 and historicalv1 validation debt | Separate accepted backlog, not silently fixed. |

## Dependencies, ownership and reachability

| Plan | Needs | Creates | Checkpoint | Wave |
|---|---|---|---|---|
| 07-01 | Existing v1 contracts | Expand stable instrument and discovery storage | no | 1 |
| 07-02 | 07-01 | Preserve crypto routes and refuse stock execution | no | 2 |
| 07-03 | 07-02 | Version exact recovery contracts with the schema | no | 3 |
| 07-04 | 07-03 | Prove restricted-role TLS upgrade and exact restore | no | 4 |
| 07-05 | 07-04 | Implement product-specific fail-closed admission | no | 5 |
| 07-06 | 07-05 | Validate exact IEX quotes and monotonic persistence | no | 6 |
| 07-07 | 07-05 | Review calendar dependency before installation | yes | 6 |
| 07-08 | 07-06,07-07 | Implement verified regular-session calendars | no | 7 |
| 07-09 | 07-04,07-08 | Collect stocks independently inside the single scheduler | no | 8 |
| 07-10 | 07-09 | Expose authenticated catalogue-first stock discovery | no | 9 |
| 07-11 | 07-10 | Validate and isolate stock client state | no | 10 |
| 07-12 | 07-11 | Deliver responsive read-only stocks beside crypto | no | 11 |
| 07-13 | 07-12 | Close local coverage, image and recovery gates | no | 12 |
| 07-14 | 07-13 | Verify external admission and final discovery acceptance | yes | 13 |

DB migrations/teardown/role application/real restore are serial01→02→03→04; later shared DB suites remain serial.06 and07 share a wave only because07 owns a documentation-only package packet with no install/DB activity.08 alone owns pyproject/uv.lock; config/examples are ordered05→09; fixture reset is owned01, Markets UI12, CI13. No same-wave files overlap. Never run destructive ops beside another DB suite.

Creation paths: reviewed migrations create metadata/quotes/sessions/admissions; seed adds20 catalogue rows; migrator-only procedure grants real evidence; scheduler populates permitted quotes/sessions; authenticated API exposes only currently admitted data; /markets renders it. No unused flag without consumer or unlinked route is planned.

## Checker revision 1 coverage

- Migration grants are assigned to07-01-01's owned revision0009, including conditional existing-role handling, exact table privileges, PUBLIC/unintended privilege revocations and scheduler session identity USAGE.07-04-01 bootstraps populated0008 only before actual verified-TLS migrator upgrade, then tests allowed generated-identity inserts and denials without any grant repair; a separate fresh-bootstrap lane checks parity.
- Discovery has a precise final decision boundary: after awaited data reads, a final current committed evidence query reads admission generation, authoritative calendar admission review/overrides, derived session generation and status, followed by fresh UTC and synchronous redaction/recalculation. No further application await occurs after projection. Current-request tests block actual DB work while another connection commits revocation, or while permission/quote/calendar/session boundaries pass. This does not promise to predict changes after the final evidence snapshot or during response delivery.
- Client remaining permission/session lifetime subtracts full monotonic request RTT, including retries and server waits; quote age adds RTT and later elapsed time. Conservative server-time intervals avoid an early-open claim. Delayed first-render expiry/age/close and skewed browser wall-clock cases belong to07-11-01.
- All fourteen plans now name actual runtime/recovery artifacts and critical producer/consumer interfaces in must_haves; each task explicitly names its assigned current source analogs and stock-specific departures. No generic first-two-file links remain.07-07's malformed threat row is replaced by a concrete ASSUMED-package gate.
- The existing eleven-file07-01 scope is bounded to two schema/seed tasks and directly affected fixtures/head assertions; more ownership requires expansion/splitting before edits. Sampling and slow migration/TLS/restore/image classifications remain explicit. No new plan/task/wave, source implementation, grant execution, package installation, provider permission, test result or external authorization is implied by this revision.

Independent checker re-verification is pending; these statements describe executable planning changes, not implementation evidence.

## Checker revision 2 coverage

- Calendar review/override authority lives only in the existing migrator-owned stock_data_admissions calendar-product evidence. No new table, task or plan is introduced. stock_sessions stores derived UTC boundaries, coverage and calendar_admission_generation only; app/scheduler cannot establish or renew evidence. The logical generation reference fails closed when mismatched, without an FK that would prevent administrative generation changes.
- 07-01 owns this schema and conditional migration ACL; 07-05 owns validated calendar review/override administration; 07-08 evaluates current authoritative evidence and UTC; 07-09 refreshes derived rows only; 07-10's preserved final committed read includes current authoritative calendar facts. Runtime refresh never grants authority.
- 07-04 requires actual populated-upgrade and fresh-bootstrap role-positive/negative proofs: scheduler cannot modify admission review/overrides or inject authority-bearing session columns; derived refresh remains permitted; expired review/forged or stale generations remain unknown. 07-03 hashes every authoritative calendar field/override/provenance and derived generation, with exact restore equality and mutation detection.
- Research open questions are annotated RESOLVED-FOR-PLANNING with exact owning plans. Actual package approval/runtime compatibility and provider rights/access remain UNSATISFIED, with checkpoints intact. Timely status remains unknown; Phase8 monitoring is not implemented by Phase7.

Independent delta re-verification remains pending. These are planning contracts, not test results, permissions or live evidence. Existing response-time/migration corrections and14plans/29tasks/13waves are unchanged.

## Constraint/pre-mortem audit

External rights are the hardest unknown: contract and concrete packet are prepared05; actual authorization is deliberately late14 after reviewed local proofs. Passing fixtures never resolves it. Calendar installation has an independent explicit pre-install gate07. Schema/history identity is the irreversible risk: preserve IDs and financial rows, guard downgrade and prove exact old/new restore03/04. Likely failure modes—stock leakage into crypto, source-age laundering and fixed-schema recovery omission—have early targeted proofs02,06 and03/04. Fourteen bounded plans correspond to separate schema/crypto/recovery/roles/admission/quotes/package/calendar/collection/API/client/UI/proof/external outcomes, rather than helper-only foundations.


## Final scoped gap analysis —2026-11-10

All6IDs mapped to Phase7 (STOCK01/02/03,DATA01,MKT01,SAFE01) occur in plan
frontmatter with concrete tasks. The SDK milestone-wide gap command also lists
20requirements assigned to Phases8–11 as uncovered by Phase7; these are expected
scope exclusions, not dropped Phase7 requirements. NoCONTEXT exists, so its
separate decision-coverage check is not applicable; approved REQUIREMENTS,
PROJECT and UI-SPEC decisions were independently checked. Final plan checker
passed after revision2 with0blockers/0active warnings; see07-PLAN-CHECK.md.
