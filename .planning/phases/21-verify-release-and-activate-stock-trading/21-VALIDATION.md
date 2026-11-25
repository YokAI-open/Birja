---
phase: 21
slug: verify-release-and-activate-stock-trading
status: ready_for_execution
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-25
---

# Phase 21 validation

Reuse the locked toolchain, disposable test services, guarded browser runner,
CI contracts and protected recovery harness. The release candidate and
resulting main commit each need their own exact CI outcome. Component results
retain their input scope. Preserve the existing coverage and image policies.

| Requirement | Verification |
|---|---|
| SV-01 | `python3 deploy/tests/run-stock-browser.py --suite catalog` for changes to the catalog journey, and the complete browser run in hosted CI. Check the existing [browser contract](21-UI-SPEC.md). |
| SV-02 | Exact candidate source, existing test and coverage commands, CI workflow contracts, retained and successor restore evidence, strictly checked bundle/image, populated cutover rehearsal from the verified predecessor, and compatible recovery. |
| SV-03 | CI receipts bound to the resulting main commit and its v7 recovery bundle, authorized cutover and encrypted isolated restores, plus a production regular-session simulated buy and sell reconciled by cash, position and History. |
| SC-01 and SC-03 | Inherited Phase 19 acceptance. Complete admitted two-directory manifest and exact live out-of-list selection/quote evidence. Keep the original requirement assignment. |

The [research validation map](21-RESEARCH.md#validation-architecture) records
the relevant command and evidence cadence. Live tasks need source and operator
approval, exact run inputs, a bounded budget and a sanitized result.

## Evidence at each task

Run the automated check in each named plan task. Operator approvals are
recorded decisions, and the following live and hosted observations must also
be collected. Disposable fixtures check the mechanism and keep test inputs
independent of provider availability. They supply no production authority.

| Task | Requirements | When to verify | Required observation |
|---|---|---|---|
| 21-01-01 | SV-02, SV-03 | After runner changes | The new dry run selects the exact v7 0026 campaign, separate from prior modes. Check strict source, image and profile refusal. |
| 21-01-02 | SV-02, SV-03 | After workflow and runner edits | Both portable workflow suites pass. Required jobs and success-only upload attest the whole successor graph and exact tested source. |
| 21-02-01 | SV-02, SV-03 | After operator packet and renewal | Disposable catalog publish/promotion tests check review/apply roles, exact listing changes, rejected scope and preserved original identity. |
| 21-02-02 | SV-02, SV-03 | After applicable config and API wiring | Scoped Ruff and effective Compose inspection validate selected cache routing and fail-closed behavior. |
| 21-02-03 | SV-02, SV-03 | After applicable scheduler wiring | Disposable tests cover owned quote contexts, one shared reservation, atomic completion, restart and any volatile-lane canary absence. |
| 21-03-01 | SV-02, SV-03 | After successor stage wiring | Portable recovery checks and full same-archive graph on the supported runner exercise exact retained and 0026 cold recovery, populated predecessor migration, roles and TLS. |
| 21-03-02 | SV-02, SV-03 | After selected recovery wiring | Deploy compatibility contracts and selected stage evidence prove the pre-write and after-write recovery paths and refusal of an incompatible predecessor. |
| 21-04-01 | SV-01, SV-02 | After affected integration changes | Guarded browser behavior or exact unaffected proof is linked to each [UI acceptance outcome](21-UI-SPEC.md). |
| 21-04-02 | SV-01, SV-02 | At the release-candidate boundary | Full backend and frontend coverage, lint, type and build, scoped review and available local archive evidence are recorded. |
| 21-05-01 | SV-02, SV-03 | Before each proposed publication | Verify actual candidate branch/head and the exact approved scope. |
| 21-05-02 | SV-02, SV-03 | At each PR and confirmed main commit | Require all six successful check jobs, exact head/test tree evidence and the actual main run for the resulting commit. |
| 21-05-03 | SV-02, SV-03 | Before approving release publication or transferring artifact | Independent archive SHA, profile/source/runtime and seven-stage receipt match the exact main CI; tag and any back-merge use approved SHA and green CI. |
| 21-06-01 | SV-03 | Before requesting scoped live access | Inventory CLI, dated permissions and finite campaign proposal identify exact fields, allowed capture/retention, timing, capacity and closure conditions. |
| 21-06-02 | SV-03 | Before any bounded live request | Record authorization for the exact operator, window, methods, endpoints, attempt limits and private scope. |
| 21-06-03 | SV-03 | After every permitted source and listing/sample stage | Fixture suites stay green. The live receipts show full directory reconciliation, selected and held-only quote timestamps under one shared cap, and bounded halt/action results. |
| 21-07-01 | SV-02, SV-03 | Before production inspection | Owner approves the exact read-only host scope; syntax and local release receipt checks pass. |
| 21-07-02 | SV-02, SV-03 | After authorized inspection | Runtime, mounted stores, exact schema and capacity match rehearsal and production proposal. |
| 21-07-03 | SV-02, SV-03 | Before protected install or isolated real-data restore | Approved exact manifests, independently authenticated profile/digest, host and limited recovery operations. |
| 21-08-01 | SV-02, SV-03 | After authorized tooling setup and pre-change clone | Actual installed source/profile and fresh exact isolated predecessor recovery match approved protected state. |
| 21-08-02 | SV-02, SV-03 | Before stopping writers or admitting production changes | Explicit decision covers exact restore, source, named operations, data/custody and activation bounds. |
| 21-08-03 | SV-02, SV-03 | Before protected routing and after approved migration and admission | Fenced predecessor fingerprints match the verified snapshot under the held lock. Origin/public smoke, exact current 0026 encrypted restore, balanced active catalog, admitted listing/cache and matching deployed SHA. |
| 21-09-01 | SV-01, SV-02, SV-03 | Before the designated browser trade | Owner confirms exact one-share virtual effects, eligible issue, intended portfolio and current market window. |
| 21-09-02 | SV-01, SV-02, SV-03 | After each leg and final ledger check | Two original production fills, both exact receipt identities in History, fresh IEX ask/bid, net cash, zero final quantity and crypto availability. |
| 21-09-03 | SV-01, SV-02, SV-03 | At independent phase verification | Update only observed requirement outcomes. SC-01/SC-03 retain their Phase 19 assignment and need the actual admitted production generation and out-of-list quote/UI result. |

The full release coverage and hosted same-bundle checks are mandatory even
when a workstation runs only the directly applicable selected tests. The
live-source and hosted release plans can advance independently. The protected
preflight requires both completed outcomes.

## Planning source coverage

| Source | Item | Plans |
|---|---|---|
| Roadmap goal | Verified production search and simulated out-of-list buy and sell | 06–09 |
| Requirement | SV-01 browser and private portfolio acceptance | 04, 09 |
| Requirement | SV-02 candidate correctness, review, migration and recovery | 01–05, 07–09 |
| Requirement | SV-03 exact green CI, approved rollout and live receipt | 01–03, 05–09 |
| Research | Exact v7 artifacts, retained families and populated predecessor transition | 01, 03, 05, 07–08 |
| Research | Admission writer, renewal, cache rights and bounded live source use | 02, 06–08 |
| Research | Inherited Phase 19 coverage and quote evidence | 06, 08–09 |
| Context | D-01 simulator and existing interface | 04, 09 |
| Context | D-02 existing free sources, rights and evidence | 02, 06–08 |
| Context | D-03 proportionate evidence reuse and unchanged release gates | 01–05, 09 |
| Context | D-04 approved Git-flow and protected exact rollout | 01, 03, 05, 07–08 |
| Context | D-05 designated test portfolio and truthful completion | 06, 09 |

## Plan check

Independent review passed all nine plans after the held-only quote receipt,
locked predecessor fingerprint check, and runnable verification corrections.
The final review covered SV-01 through SV-03, both inherited Phase 19 live
checks and all five context decisions. The 24-task matrix describes execution
evidence to collect.
