---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: US Stock Trading
status: executing
stopped_at: Wave 1 complete; 1115 backend tests and 23 critical modules pass; start08-02 exact recovery/TLS.
last_updated: "2026-11-11T10:47:22.510Z"
last_activity: 2026-11-11
progress:
  total_phases: 5
  completed_phases: 0
  total_plans: 27
  completed_plans: 15
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-11-10)

**Core value:** Making a trade at a real, recent market price and seeing its current worth, correct to the cent.
**Current focus:** Phase 8 — Corporate-Action-Safe Ownership (isolated execution)

## Current Position

Phase: 8 (Corporate-Action-Safe Ownership) — EXECUTING
Plan: 2 of 13 executed (29 tasks, 11 waves)
Status: Wave 1 complete; Plans01/03 reviewed and integrated; next08-02
Last activity: 2026-11-11
Progress: Phase 8 execution 2/13 plans complete (Wave 1/11)

## Completion and next action

Wave 1 gate passed:1115backend tests/99.71%overall, expanded23critical modules100%
(1388statements/374branches). Initial22integrationfailures were fixed and
independently re-reviewed. Both01/03reviews are clean. See08-LOCAL-PROOF.md.
Next08-02 must prove exact0011 recovery and actual restricted-role TLS upgrade
before any new runtime consumer. Existing birja-test stack remains available.

Phase 8 planning is complete: 13 plans / 29 tasks / 11 waves. Research, pattern
map, approved UI contract, per-task validation and source audit are saved under
08-corporate-action-safe-ownership. Independent plan review found two blockers;
revision 1 resolved both, with 0 active warnings. See08-PLAN-CHECK.md.
Plan08-01 is complete: additive0011/nine constrained typed models, empty-only
downgrade, epoch-zero quote compatibility/final-statement nonzero refusal and
restricted append/quantity-only grants. Final79isolated tests pass7.45s;
8files Ruff/format and4source mypy pass. Actual42501 denials and transactional
fresh-bootstrap grant parity pass. See08-01-SUMMARY.md. The NOLOGIN operator
must be preprovisioned by privileged bootstrap before restricted0011 migration;
the migrator does not gain CREATEROLE. Recovery/TLS proof remains08-02.
Plan08-03 is complete: independent action REST/replay and durable-accounting
authority, frozen exact action/cutoff/split contracts and persistent-hold safety
decisions.175scoped tests pass2.06s with all3modules100%statements/branches;
259calendar/quote/admission/economic regressions pass4.64s;5file Ruff/format
and3source mypy pass. See08-03-SUMMARY.md. Wave1 integration remains pending
the full backend gate and API-guard review after08-01schema re-review passed.
Fix5d0353a plus retry correctionb389ce1 pass91isolated migration/quote/role
tests11.10s, scoped lint/format
and model types; new observation event_id, application coin_id and composite
economic-cause FKs are included. Actual restricted failed-upgrade/provision/retry,
incompatible-index rejection and cancelled concurrent-index rebuild are proven.
Independent schema re-review atb389ce1 is clean. Full integration then found22
API/seedguard failures; correction32bff2b passes36targeted tests4.56s with scoped
lint/format/types, preserving explicit provider fields and suppressing nonzero
unit quotes. Root owns the full-suite rerun and new API-guard independent review.
Next: complete those integration gates,
then dependency-ordered Wave2 isolated implementation. Stock
execution stays disabled, cash payment/public event History remain Phase 10,
and actual fills integrate in Phase 9. Phase 7 remains13/14 with its live-data
acceptance owner-deferred, not passed; no duplicate campaign or UI approval is
needed. Production and the scheduled one-shot process are unchanged. Plan03's
authorized stock_admission.py change makes the frozen Phase7 source manifest
stale; the unchanged runner must fail closed before calls. Do not refresh its
hashes or launch another campaign; actual results/revalidation remain deferred.

### Preserved Phase 7 execution evidence

Phase7 has14plans/29tasks/13waves, covering all6requirements/5success criteria.
Research, patterns, approved UI contract, validation and source audit are saved;
independent final plan check passed with0blockers/0active warnings.

Plan07-01 completed schema0009 and separate catalogue0010 with49isolated
PostgreSQL tests passed, scoped lint/format and model types passed. Both tasks
have meaningful RED/GREEN commits. Plan07-02 preserves crypto boundaries and
refuses stock execution/replay;137scoped regressions and service static checks
passed. Plan07-03 adds revision-selected exact recovery contracts:25backup tests,
6restore-safety tests and actual isolated four-revision PostgreSQL field/schema/
identity corruption proof passed. Plan07-04 proves actual restricted-role TLS
upgrade without grant repair, fresh-bootstrap parity and exact retained encrypted
dump/retrieval/restore0007/0008/0009/0010 including identities/corruption checks.
Calendar evaluator is proven07-08 and persisted restricted-TLS consumer semantics
are now proven07-13; SQL authority denial remains enforced. Plan07-05 pure scoped admission and disabled
configuration pass74admission/114combined configuration tests and scoped static
checks; private migrator-only evidence import/revoke/TLS rehearsal packet saved.
Plan07-06 exact IEX adapter/predicates and monotonic PostgreSQL persistence pass
94tests,100% scoped critical coverage and scoped static checks. Session bounds
are structural only in07-06; genuine authority/evaluator is now proven07-08. Plan07-07's
official registry/tag/wheel review and exact eight-package prospective resolution
received explicit owner approval for project uv lock changes and isolated local
installation/testing. No lock mutation or installation occurred in07-07.
Legitimacy protocol remains ASSUMED; unsigned source and absent PyPI attestation
remain explicit limitations. Plan07-08 installed the exact approved eight-wheel
resolution, preserving all existing versions, and implements genuine reviewed
calendar/session decisions plus atomic generation/snapshot guarded derived refresh.
88tests pass on host and actual nonroot hardened test-builder; session service has
100% scoped statement/branch coverage, static checks and pip-audit pass. Actual
network-free nonroot runtime session smoke and five final strict image scans pass.
See07-08-SUMMARY.md for exact identities and Task1's explicit TDD limitation.
Plan07-09 independent bounded stock scheduling and concurrent loops pass90focused
tests, static/Compose checks and real simultaneous lease/cancellation proof.
Plan07-10 authenticated no-store catalogue-first API passes33focused tests,
including same-request committed admission/calendar changes, fresh UTC expiry/
age/close decisions, exact decimals, independent unknown status, safe final-read
failure and unchanged crypto contracts. Scoped lint/format/types pass. Permitted
historical quotes retain truthful original times without recent/executable claims.
Plan07-11 strict twenty-stock validation, auth/generation-isolated queries and
conservative monotonic full-RTT deadlines pass34client tests; visible escaped
IEX/simulation attribution passes4component tests. Scoped static checks pass.
Plan07-12 read-only stock discovery UI preserves crypto trading, twenty stock
identities, visible IEX attribution and separate quote/session/status facts.
16required component tests (20with attribution) and11real authenticated Chromium
stories pass, including responsive/keyboard recovery, permission expiry/revocation,
120second boundary and early close. Scoped static checks pass. Dedicated tmpfs
e2e project cleanup is verified empty; provider fixture data is not live permission.
Plan07-13 completed actual local gates:969backend tests,99.68%overall and all21
critical modules100%;310frontend tests/static/audits,20actual browser journeys
with1expected deployed-CSP skip;158nonroot hardened-image tests and runtime
calendar smoke; five actual strict HIGH/CRITICAL including-unfixed scans clear.
Current --all proves exact0007/0008/0009/0010 recovery and both real persisted
restricted-TLS calendar consumer lanes. Actual image-transition and distinct
legacy0008 v0.4.0→v0.3.1 retained rollback/cutover pass; no unsupported old-runtime
on0010 claim. Independent code/security/UI review findings are fixed and
re-reviewed:0active code findings,47/47local threats closed,UI24/24. Existing
response deadlines bound retained-value exposure; actual DB/recovery storage
rights or approved verified cleanup remain prerequisites before live activation.
Plan07-14's concrete07-ACTIVATION.md packet is prepared. Task07-14-01 is accepted
on owner attestation (1/3tasks complete): on2026-11-11 the owner reported a Paper
account, privately saved keys and provider approval, then instructed “just do all
the way, we have planned.” This supersedes further paperwork/repeated approval
requests within the previously presented fixed30-attempt scope. No provider
document, terms version or conditions were independently verified or invented.
A concrete local bounded
measurement harness is prepared in/tmp/birja-phase07-measurement;42synthetic
tests and Ruff lint/format pass, with source hashes in07-ACTIVATION.md. Initial
independent focused review had0blockers/3warnings; all3have observed failing
regressions and corrections. Independent re-review confirmed0active findings,
matching hashes and42offline tests passed11.46s. A separate one-shot runner is
prepared at/tmp/birja-phase07-one-shot/runner.py:23offline tests pass1.02s,
including real calendar/admission evaluation, time/hash/claim/deadline guards,
sanitized failures and secret-free default. Independent review reproduced all23
tests with matching hashes and0active findings. Parent launched the reviewed
runner in managed session60401; same-host verification confirms exactly one
waiting PID3191116, private claim present/no receipt. Earlier sandbox process
inspection hid the first host waiter; its claim is preserved and exact extra
PID3189601 was terminated before opening. No private calls or keys were read.
Authorized start is2026-11-11at17:30Moscow,
at most5minutes late, then one900second campaign/max30private HTTP attempts
(20reference/10quote samples), no next-day fallback. Frozen hashes and exact
limits are in07-ACTIVATION.md. Account context and permission are owner-attested;
internal validity limits do not invent provider grant duration or account quota.
No credentials read, private calls, admission import or collection activation.
Owner explicitly requested continuing the phase without waiting for live data;
review of the live measurement is deferred rather than waived or passed.
The scheduled one-shot remains authorized with its original limits; this
deferral does not authorize another campaign or activate ongoing collection.
Owner deferred measurement review until later and authorized continuing
independent preparation.07-HUMAN-UAT.md now contains the final acceptance
checklist, existing final-run screenshot links and explicit pending owner
outcomes. Owner subsequently stated “i accept ui” on2026-11-11; this explicit
UI acceptance is now recorded. No new preview server, browser run or individually
observed manual checks are claimed. Live-dependent07-14-03 remains pending. No completed07-14SUMMARY and no
phase-complete or live criteria claim from fixtures. See07-ACTIVATION.md for
reviewed source/locks/images/tools, product checklist, exact call bounds and
continuation handoff. Actions/status remain separately disabled and unverified;
their rights are required before those products are used, not invented now.
Successor canonical callers must
use manifest_sql/schema_guard_sql or verify-restore.canonical; raw SQL is legacy-only.
Exact reviewed calendar-package approval is recorded; provider permission is
owner-attested, with actual access and20symbol coverage/freshness remaining
explicit measured gates; owner UI acceptance is recorded.
Stock execution remains disabled through Phase8; no real stock orders in Phase7.
Live data or completed acceptance cannot be claimed from fixtures/disabled state.

Planning and execution commits remain local on feature/v1.1-stock-planning. Owner deferred
publication; do not re-ask or push/openPR without a later request. Execution,
provider contact/signup/agreement/payment and deployment are not inferred from
plan completion. Published application remains v0.4.0/46d24c8/schema0008.

## Performance Metrics

- v1.1: 13/14 Phase7 plans completed;07-13 approximately46minutes; prior summaries retain actual timings.
- v1.0: 7 phases / 69 plans archived; published software remains v0.4.0 at
  main 46d24c8, schema 0008. Archival PR #30 merged as 7d81010.

## Accumulated Context

### Decisions

- Exactly 20 NYSE/Nasdaq USD common stocks, whole-share regular-session orders,
  shared original USD account; sale proceeds immediately reusable with disclosure.

- Conditional Alpaca IEX, visible labels on listings/previews/valuations;
  about 60-second collection, source age strictly below 120 seconds.

- Buy at eligible ask, sell at bid; zero stock commission/added spread/regulatory
  fees, with simplifications disclosed. Existing crypto rules remain unchanged.

- Gross ordinary USD dividends, no tax/reinvestment; historical cutoff eligibility,
  announcement revisions, atomic once-only cash/History and separate corrections.
  Uncertain or unaffordable negative corrections stay held for reconciliation.

- Verified ordinary forward splits conserve basis; unsupported/uncertain actions
  suspend affected stocks and make valuations unavailable. Stock marks use midpoint.
  Capture entitlement history from the first fill and order actions with trading.

- [Phase 7]: 07-01 authoritative calendar evidence stays in migrator-owned admissions; derived sessions have no review or override authority.
- [Phase 7]: 07-02 unsupported stock holdings remain visible/unpriced; crypto-only replay and holding lookups reject injected stock state.
- [Phase 7]: 07-03 preserves byte-compatible legacy SQL; successor recovery dispatch includes exact evidence/generations without repairing authority.
- [Phase 7]: 07-07 owner approved the exact eight-package calendar resolution for local uv lock/install/tests; provenance limitations and all runtime/image/security gates remain.
- [Phase 7]: Local gates pass with configured scope, retention disclosure deadlines and separate legacy0008/successor0010 proofs; provider/storage rights and owner acceptance remain07-14.

### Blockers/Concerns

- Quote/action/status access, coverage, rights, quotas and observed freshness
  remain activation gates. Feed selection is not display permission.

- Phases 7–8 keep stock execution disabled; Phase 9 integrates eligibility capture
  and monitoring/freeze safeguards before its first fill. Phase 10 pays dividends.

- Every schema change carries migration, restricted-role/TLS and recovery-contract
  compatibility checks. Phase 11's exact restore proof precedes public rollout.

- Research SUMMARY retains formerly open policy alternatives; approved requirements
  and PROJECT decisions supersede those alternatives, not unresolved provider gates.

## Deferred Items

Owner-approved follow-ups at close, 2026-11-10:

| Category | Item | Status |
|---|---|---|
| Auth resilience | W01 cross-tab refresh/result handling | Accepted follow-up |
| UI resilience | W02 malformed response/render recovery | Accepted follow-up |
| Health | W03 cancellation/accessibility/readiness | Accepted follow-up |
| Infrastructure | W04 optional container/Redis/proxy/header hardening | Accepted follow-up |
| Admin tools | W05 reject unknown Cloudflare helper arguments | Accepted follow-up |
| Verification | W06 stronger transport/proxy/config assertions | Accepted follow-up |
| Browser coverage | W07 authenticated production CSP | Accepted follow-up |
| CI/protection | W08 immutable action refs/admin bypass policy | Accepted follow-up |
| Historical validation | Phases 1/2/2.1/3 retain draft task records | Accepted follow-up |

Detailed impact, evidence and historical accepted risks remain in
[milestone audit](milestones/v1.0-MILESTONE-AUDIT.md) and
[integration audit](milestones/v1.0-INTEGRATION-AUDIT.md).
| Phase 07 P01 | 14min | 2 tasks | 10 files |
| Phase 07 P02 | 7min | 2 tasks | 4 files |
| Phase 07 P03 | 16min | 2 tasks | 7 files |
| Phase 07 P04 | 25min | 2 tasks | 3 files |
| Phase 07 P05 | 8min | 2 tasks | 5 files |
| Phase 7 P06 | 11min | 2 tasks | 6 files |
| Phase 7 P07 | 5min continuation | 2 tasks | 2 plan artifacts |
| Phase 7 P08 | 14min | 2 tasks | 5 files |
| Phase 7 P09 | 12min | 2 tasks | 7 files |
| Phase 7 P10 | 10min | 2 tasks | 5 files |
| Phase 7 P11 | 10min | 2 tasks | 6 files |
| Phase 7 P12 | 16min | 2 tasks | 6 files |
| Phase 7 P13 | 46min | 2 tasks | 35 files |
| Phase 08 P01 | 18 min | 2 tasks | 9 files |
| Phase 08 P03 | 10 min | 2 tasks | 5 files |

## Operations

Continue daily backup freshness/status and certificate-expiry checks under
deploy/RUNBOOK.md. Recovery material has confirmed off-server custody. Historical
nightly upload and separately exact-restored retained snapshot remain distinct.

## Session Continuity

Last session:2026-11-11T10:47:22.492Z
Stopped at: Completed08-03; Wave1 integration pending Plan01 schema-review fixes.
Resume: Execute the reviewed Phase 8 plans via $gsd-execute-phase 8, preserving its explicit activation checkpoint. For the separately deferred Phase 7 review, read07-LOCAL-READINESS.md and07-ACTIVATION.md. Local implementation and owner UI acceptance are complete; live review is owner-deferred. When resuming that review, observe managed exec session60401 / waiting host PID3191116, then read sanitized result-20261111/receipt.json under/tmp/birja-phase07-one-shot after the single2026-11-11at17:30Moscow measurement. No further paperwork/repeated scope approval or new launch is required. Waiting is not measured success; record real results/failures. Permission/account scope remains owner-attested, not independently provider-verified. No credentials/private calls occurred before opening. Stock execution stays disabled; owner UI acceptance is recorded in07-HUMAN-UAT.md, while live-dependent07-14-03 remains pending. Do not ask for duplicate UI approval. No completedSUMMARY or phase completion before remaining gates pass.
Active plans: .planning/phases/08-corporate-action-safe-ownership/08-01-PLAN.md through08-13.
Active review: .planning/phases/08-corporate-action-safe-ownership/08-PLAN-CHECK.md.
Deferred Phase 7 plans/review remain in07-permitted-stock-discovery.
07-01 through07-13 summaries committed; whole-phase requirements remain pending.
Plan13 proof resources were cleaned; no stack started for this documentation
checkpoint. No production services changed or provider data activated.
