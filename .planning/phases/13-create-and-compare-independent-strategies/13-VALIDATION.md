---
phase: 13
slug: create-and-compare-independent-strategies
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-18
---

# Phase 13 — Validation Strategy

## Final Execution Validation Audit

All11primary Phase13 requirements have actual passing behavioral verification.
No test gap was found; per validate-phase Step3 the no-gap path records evidence
without generating speculative new tests. The planner's task/wave/creator map is
retained below as provenance, superseded by this measured execution status.

Actual complete campaign6 at frozen9527e358bc6953cec7580043703324db194ba396:

- all-security exit0,3373.046s:3343backend tests,99.86%overall;61critical modules
  5287statements/1668branches100%;1194frontend tests;79browser passes/one retained
  deployed-CSP skip across all12specs/new20cases; complete infrastructure and all
  five immutable image policies. Raw Python/npm audits are retained, no new waiver.
- recovery exit0,2792.054s:all7passed-authenticated and same_archive_final_ci=true;
  current0020 and complete retained0017/older profiles, destroyed-source cold
  restore/immutable-before oracle/quarantine, exact fresh/upgraded TLS authority,
  supported rollback or safe refusal, unchanged source/archive/image identities.
- New exclusive canonical archive219289600bytes SHA
  6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92. Equal bytes
  to an earlier diagnostic are deterministic generation, not reuse; distinct
  inode/fresh producer receipt is retained. All21owned resource checks are empty.
- Raw command/source/log/image/coverage/cleanup receipts:
  `/tmp/birja-phase13-plan17-campaign6-20261118-9527e35/`. See13-LOCAL-VERIFICATION,
  13-RECOVERY-PROOF and13-17-SUMMARY for the committed readable evidence.
- Both distinct actual owner responses are in13-UAT/13-18-SUMMARY. Final340-input
  packet/source verification passes. Parent reran12strict evidence contracts in
  0.949s; capture flags are unchanged, not invented human outcomes.

Each test anchor below exists and its file SHA matches the frozen actual campaign
source receipt. Assertions were inspected for the stated behavior; full backend/
frontend/browser execution provides green evidence, not filename existence alone.
Companion API/authority/SQL/concurrency and browser tests in the original map below
supply the remaining boundaries. All36tasks retain assigned automated commands;
the two human outcomes are additionally manual by design.

| Requirement | Actual frozen test anchor | Behavioral evidence | Status |
|---|---|---|---|
| PMGT-01 | `backend/tests/test_portfolio_creation.py` | Same-key/name/last-slot races, owner cap10, closed identity/name reuse | COVERED — actual campaign6 PASS |
| PMGT-02 | `backend/tests/test_portfolio_metadata.py` | Actual name/description patch, owner uniqueness and unchanged financial originals | COVERED — actual campaign6 PASS |
| PMGT-06 | `frontend/src/hooks/usePortfolioManagement.test.tsx` | Description empty/default/edit/clear; strict metadata lifetime/recovery | COVERED — actual campaign6 PASS |
| PFUND-01 | `backend/tests/test_portfolio_funding.py` | Once-only signup/init under concurrency, legacy zero-book latch, fixed grant/baseline | COVERED — actual campaign6 PASS |
| PFUND-02 | `backend/tests/test_portfolio_creation.py` | Lost-response original replay before mutable limits; closed original never regrants | COVERED — actual campaign6 PASS |
| PFIN-01 | `backend/tests/test_portfolio_strategy_lifecycle.py` | New API-created same-asset sibling books, isolated money/basis, cross-asset races | COVERED — actual campaign6 PASS |
| PFIN-04 | `backend/tests/test_portfolio_strategy_events.py` | Historical per-book ownership/corrections, duplicate workers and real lock-overlap regressions | COVERED — actual campaign6 PASS |
| PCTX-02 | `frontend/src/hooks/usePortfolioTarget.test.tsx` | Explicit root/owner/session epochs, late replies, logout, root removal and identity events | COVERED — actual campaign6 PASS |
| PVIEW-01 | `backend/tests/test_portfolio_overview.py` | Stable0/1/10 books, stored custom baseline, no pooled total and strict privacy | COVERED — actual campaign6 PASS |
| PVIEW-02 | `frontend/src/hooks/usePortfolioOverview.test.tsx` | Shared-time detail parity, per-book expiry/incomplete semantics and backward-proof refusal | COVERED — actual campaign6 PASS |
| PSAFE-07 | `backend/tests/test_portfolio_strategy_events.py` | Real2/10-books one shared HTTP poll, bounded worker paging and actual capacity refusal | COVERED — actual campaign6 PASS |

### Audit totals and sign-off

| Metric | Count |
|---|---|
| Requirements COVERED |11|
| Partial/missing automated gaps |0/0|
| New tests generated in this audit |0|
| Manual acceptance outcomes |2/2explicitly passed|
| Implementation tasks with feedback |All assigned tasks; no unowned test prerequisite|
| Overall/critical gates |80%minimum retained;100%critical attained|

- [x] Independent13-PLAN-CHECK revision1 passed0blockers/0warnings.
- [x] Wave0 and feature tests were authored meaningfully by owners and executed.
- [x] Real SQL/authz/money/concurrency/browser/current-retained recovery executed.
- [x] Owner UI and actual native200 responses are separate and source-associated.
- [x] No new watch command, dependency install or guard/risk waiver introduced.
- [x] Failed/interrupted/composite attempts retained as history, not final passes.

Nyquist compliance records verification coverage, not global phase completion.
Independent goal verification and requirement tracking closure follow separately.

## Preserved Planning Strategy (superseded by execution audit above)



## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Existing pytest9.1.1/pytest-asyncio, Vitest5.0.5 and Playwright1.64.1 |
| Config | backend/pyproject.toml; frontend/vite.config.ts; frontend/playwright.config.ts |
| Quick existing baseline | cd backend && uv run pytest tests/test_portfolio_identity.py -x (owned isolated stack required even for metadata pytest) |
| Full local qualification | python3 deploy/tests/run-portfolio-validation.py --suite all-security; then --suite recovery |
| Source baseline | Phase12 tested4b4320b; complete security1479.850s and fresh7stage recovery2694.692s are historical qualification, not Phase13 results |
| Execution isolation | All backend/DB-touching ops suites strictly serial; stripped synthetic env/fake prices/console mail; no .env, production or provider calls |

## Sampling Rate

- Per task: smallest meaningful new or affected backend/frontend/API test group from its plan.
- Per wave: affected integration plus schema/role/recovery admission checks; no three implementation tasks without automated verification.
- Before phase verification: actual complete security, current/retained exact same-archive encrypted recovery, independent code/security/UI reviews and implemented new UI/desktop-native200% owner checks.
- Target feedback latency:60seconds for selected groups; actual DB migration/concurrency, full coverage/browser/image/recovery are explicit longer proof exceptions. Measure selectors, do not invent short runtimes.
- Keep original80% overall and100% critical gates. Add actual new money/grant/authz/normalization/overview modules to the critical command instead of preserving only the prior60-module list.

## Initial Requirement Verification Map

Planner must replace group placeholders with its final plan/task/wave IDs while retaining every row and executable creation dependencies.

| Requirement | Proposed new/affected verification | Secure behavior | Planned command | Exists now |
|---|---|---|---|---|
| PMGT-01 | test_portfolio_creation.py | Serialized active cap10, private ownership, closed slot/name reuse and new identity | cd backend && uv run pytest tests/test_portfolio_creation.py -x | New alongside feature |
| PMGT-02 | test_portfolio_metadata.py | SQL-authoritative Unicode normalization/owner uniqueness, rename/create races, unchanged money | cd backend && uv run pytest tests/test_portfolio_metadata.py -x | New alongside feature |
| PMGT-06 | metadata tests; usePortfolioManagement.test.tsx | Empty/default/view/edit/clear description, strict controls/length, no financial mutation | cd frontend && npm run test -- src/hooks/usePortfolioManagement.test.tsx | New alongside feature |
| PFUND-01 | test_portfolio_funding.py; retained identity tests | Fixed10000grant/baseline once; genuine new onboarding; no legacy/zero-book regrant | cd backend && uv run pytest tests/test_portfolio_funding.py tests/test_portfolio_identity.py -x | New plus existing |
| PFUND-02 | creation tests | Permanent original owner/key/payload identity; lost response/rename/cap/closed replay safety | cd backend && uv run pytest tests/test_portfolio_creation.py -x | New |
| PFIN-01 | test_portfolio_strategy_lifecycle.py | API-created siblings trade same assets with isolated money/quantity/basis and cross-asset races | cd backend && uv run pytest tests/test_portfolio_strategy_lifecycle.py -x | New |
| PFIN-04 | strategy lifecycle plus dividend/entitlement/split tests | Correct per-book historical ownership, once-only credits/corrections and active split effects | cd backend && uv run pytest tests/test_portfolio_strategy_lifecycle.py tests/test_portfolio_dividends.py tests/test_portfolio_entitlements.py tests/test_portfolio_splits.py -x | New plus existing; serial |
| PCTX-02 | management/target hooks; portfolio-strategies.spec.ts | Switch/pending create/unknown original/cursor/late callback/logout/cross-tab rename isolation | cd frontend && npm run test -- src/hooks/usePortfolioManagement.test.tsx src/hooks/usePortfolioTarget.test.tsx | New plus existing |
| PVIEW-01 | test_portfolio_overview.py | Stable0/1/10 active owner-only books, original baseline, no pooled total | cd backend && uv run pytest tests/test_portfolio_overview.py -x | New |
| PVIEW-02 | overview and valuation tests | Same marks/time/math as detail; per-book incomplete isolation, shared bounded query plan | cd backend && uv run pytest tests/test_portfolio_overview.py tests/test_portfolio_valuation.py -x | New plus existing |
| PSAFE-07 | creation/overview resource tests; capacity/polling contracts | Key/body/quota/query bounds, one market poll, existing capacity/stock-admission guards | cd backend && uv run pytest tests/test_portfolio_creation.py tests/test_portfolio_overview.py -x | New plus retained deploy contracts |

## Wave 0 / Feature Test Creation Dependencies

- Existing test frameworks and isolated infrastructure remain; no package installation recommended.
- Create meaningful grant/creation/metadata/overview/strategy-lifecycle test files with the owning feature before implementation assertions can pass.
- Add strict frontend API, management/target hooks, pages and actual browser journeys with their implementation owners.
- Shared DB fixtures/test harness/critical list/recovery profiles must have explicit single ownership and sequencing.
- New revision0018+ schema/SQL grants, immutable create/grant journal and initialization latch require fresh/populated/zero-book migration, restricted-role forged amount/baseline/directINSERT/metadata/journal/privateEXECUTE refusals and exact recovery.
- Preserve immutable Phase12 migrations, catalogue/profile fingerprints and actual0017 archive. New current/retained recovery source inventory must be extended, not silently repinned.
- Include negative source/authority/profile mutations, immutable replay and capacity refusal checks before full campaigns.

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Instructions after implementation |
|---|---|---|---|
| New overview/create/edit/switch visual behavior | PMGT-01/02/06; PVIEW-01/02; PCTX-02 | Owner product acceptance | Review actual new screens/states from source-bound packet; planning UI-SPEC approval is not human UAT |
| Native browser200% zoom | Same UI scope | Automation does not prove desktop browser native zoom | Owner checks actual browser zoom with readable/reachable controls, no overlap or horizontal page overflow |

## Accepted and Deferred Boundaries

Issue35 picomatch exception remains exact/hash/path/expiry bound through2026-12-17UTC; full raw audits and unrelated HIGH/critical blockers remain. Approved Python image pins stay unchanged. No dependency refresh or new waiver in planning. Phase7 six live requirements and consumed campaign stay separate; no provider calls/activation. Public deletion belongs to Phase14 and full lifecycle acceptance to15, but new-revision safety/recovery is required now.

## Validation Sign-Off

- [x] Final task IDs/waves/threat IDs mapped by planner
- [x] Every implementation task has automated verification and created-test dependency
- [x] No three consecutive implementation tasks lack feedback
- [x] All missing files have concrete creation owners
- [x] No watch commands or invented test pass
- [x] Critical100/full security/current-retained recovery/reviews/UI-native200 gates retained

Historical planning sign-off is superseded by the actual execution audit above. Independent plan check and Wave0 execution are now recorded; no framework was installed.

## Final executable plan/task/wave and threat map

Revision1: threat register rows01/02 (and03 where applicable) now denote each plan’s concrete attacker/invariant/negative-test scenarios rather than uniform grouped threats. The scenario-to-test mapping in each PLAN is authoritative; SC remains the exact unchanged issue35 entry. Underlying proof targets:17.1 verifies02/06/15 funding/authz/resource/inventory threats,17.2 verifies04/05/15 archive/source/ACL/immutable-state threats,18.1–2 verify16’s current-source and distinct actual human outcomes. No implementation proof is credited by this map.

At planning time, this table superseded the initial proposed map. Its pending execution status is now superseded by the final actual audit above; no runtime pass was claimed during planning. Every new test/command file below is created meaningfully before implementation by its owning task; existing files are extended there. No MISSING command relies on an unassigned creator.

| Plan/tasks | Wave | Test creator / commands (serial when DB-bearing) | Threat IDs | Requirements |
|---|---|---|---|---|
|13-01.1–2|1|Task1: `cd backend && uv run pytest tests/test_portfolio_management_migrations.py -x`<br>Task2: `cd backend && uv run pytest tests/test_portfolio_management_migrations.py -x`|T-13-01-01/02/03/SC|PMGT-02, PMGT-06, PFUND-01, PFUND-02, PSAFE-07|
|13-02.1–2|2|Task1: `cd backend && uv run pytest tests/test_portfolio_management_authority.py -x`<br>Task2: `cd backend && uv run pytest tests/test_portfolio_funding.py tests/test_portfolio_identity.py -x`|T-13-02-01/02/03/SC|PMGT-01, PMGT-02, PMGT-06, PFUND-01, PFUND-02|
|13-03.1–2|3|Task1: `cd backend && uv run pytest tests/test_portfolio_management_admission.py -x`<br>Task2: `cd backend && uv run pytest tests/test_portfolio_management_grants.py tests/test_portfolio_authority.py -x`|T-13-03-01/02/03/SC|PSAFE-07, PFUND-01, PFUND-02|
|13-04.1–2|4|Task1: `python3 deploy/tests/test-portfolio-fixture-contracts.py`<br>Task2: `python3 deploy/tests/test-portfolio-management-recovery.py`|T-13-04-01/02/03/SC|PSAFE-07, PFUND-02|
|13-05.1–2|5|Task1: `python3 deploy/tests/test-portfolio-management-recovery.py`<br>Task2: `python3 deploy/tests/test-portfolio-recovery-contracts.py && python3 deploy/tests/test-portfolio-migration-runner.py && python3 deploy/tests/test-portfolio-smoke-image.py`|T-13-05-01/02/03/SC|PSAFE-07, PFUND-02|
|13-06.1–2|6|Task1: `cd backend && uv run pytest tests/test_portfolio_management_api.py -x`<br>Task2: `cd backend && uv run pytest tests/test_portfolio_creation.py tests/test_portfolio_metadata.py tests/test_portfolio_management_api.py -x`|T-13-06-01/02/03/SC|PMGT-01, PMGT-02, PMGT-06, PFUND-01, PFUND-02, PSAFE-07|
|13-07.1–2|7|Task1: `cd backend && uv run pytest tests/test_portfolio_overview.py tests/test_portfolio_valuation.py -x`<br>Task2: `cd backend && uv run pytest tests/test_portfolio_overview.py -x`|T-13-07-01/02/03/SC|PVIEW-01, PVIEW-02, PSAFE-07|
|13-08.1–2|8|Task1: `cd frontend && npm run test -- src/api/portfolioManagement.test.ts`<br>Task2: `cd frontend && npm run test -- src/api/portfolioOverview.test.ts src/api/portfolioReads.test.ts`|T-13-08-01/02/03/SC|PMGT-02, PMGT-06, PFUND-02, PVIEW-01, PVIEW-02|
|13-09.1–2|9|Task1: `cd frontend && npm run test -- src/lib/portfolioCreationAttempt.test.ts src/hooks/usePortfolioManagement.test.tsx`<br>Task2: `cd frontend && npm run test -- src/hooks/usePortfolioManagement.test.tsx src/lib/portfolioMetadataEvents.test.ts`|T-13-09-01/02/03/SC|PMGT-01, PMGT-02, PMGT-06, PFUND-02, PCTX-02|
|13-10.1–2|10|Task1: `cd frontend && npm run test -- src/hooks/usePortfolioTarget.test.tsx src/hooks/portfolioCrypto.test.tsx`<br>Task2: `cd frontend && npm run test -- src/hooks/portfolioStock.test.tsx src/hooks/useStockTrade.test.tsx`|T-13-10-01/02/03/SC|PCTX-02|
|13-11.1–2|11|Task1: `cd frontend && npm run test -- src/hooks/usePortfolioOverview.test.tsx src/hooks/portfolioValuation.test.tsx`<br>Task2: `cd frontend && npm run test -- src/hooks/portfolioCrypto.test.tsx src/hooks/portfolioStock.test.tsx src/hooks/portfolioHistory.test.tsx`|T-13-11-01/02/03/SC|PCTX-02, PVIEW-01, PVIEW-02|
|13-12.1–2|12|Task1: `cd frontend && npm run test -- src/pages/PortfoliosPage.test.tsx src/components/PortfolioCreateForm.test.tsx`<br>Task2: `cd frontend && npm run test -- src/components/PortfolioMetadataForm.test.tsx src/pages/PortfolioPage.test.tsx`|T-13-12-01/02/03/SC|PMGT-01, PMGT-02, PMGT-06, PFUND-02, PVIEW-01, PVIEW-02|
|13-13.1–2|13|Task1: `cd frontend && npm run test -- src/components/PortfolioSwitcher.test.tsx src/App.test.tsx`<br>Task2: `cd frontend && npm run test -- src/components/PortfolioTargetBoundary.test.tsx src/pages/MarketsPage.test.tsx`|T-13-13-01/02/03/SC|PMGT-01, PCTX-02, PVIEW-01|
|13-14.1–2|8|Task1: `cd backend && uv run pytest tests/test_portfolio_strategy_lifecycle.py tests/test_portfolio_creation.py tests/test_portfolio_metadata.py -x`<br>Task2: `cd backend && uv run pytest tests/test_portfolio_strategy_events.py tests/test_portfolio_dividends.py tests/test_portfolio_entitlements.py tests/test_portfolio_splits.py -x`|T-13-14-01/02/03/SC|PFIN-01, PFIN-04, PMGT-01, PFUND-01, PFUND-02, PCTX-02, PSAFE-07|
|13-15.1–2|14|Task1: `python3 deploy/tests/test-portfolio-browser-contracts.py`<br>Task2: `python3 deploy/tests/test-portfolio-validation-contracts.py`|T-13-15-01/02/03/SC|PSAFE-07, PFUND-02|
|13-16.1–2|15|Task1: `python3 deploy/tests/run-stock-browser.py`<br>Task2: `python3 deploy/tests/test-portfolio-ui-evidence.py && python3 deploy/tests/portfolio-ui-evidence.py`|T-13-16-01/02/03/SC|PMGT-01, PMGT-02, PMGT-06, PFUND-02, PCTX-02, PVIEW-01, PVIEW-02|
|13-17.1–2|16|Task1: `python3 deploy/tests/run-portfolio-validation.py --suite all-security`<br>Task2: `python3 deploy/tests/run-portfolio-validation.py --suite recovery`|T-13-17-01/02/03/SC|PSAFE-07, PFUND-01, PFUND-02, PFIN-01, PFIN-04, PVIEW-02|
|13-18.1–2|17|Task1: `python3 deploy/tests/test-portfolio-ui-evidence.py`<br>Task2: `python3 deploy/tests/test-portfolio-ui-evidence.py`|T-13-18-01/02/03/SC|PMGT-01, PMGT-02, PMGT-06, PCTX-02, PVIEW-01, PVIEW-02|

Every task supplies read_first, files, specific action, behavior, automated verification, acceptance_criteria and done. Both18 checkpoints additionally require explicit separately recorded owner responses; their automated evidence contracts do not replace either response. Source/source-profile/authority mutation tests are assigned03–05 and15, real PostgreSQL concurrency/money/accounting proofs02/06/14, API bounds06/07, parser/hook/component safety08–13, actual browser/capture16, complete frozen-source critical/security/images and current+retained same-archive recovery17.

### Serial resource and sampling contract

Backend pytest ALWAYS acquires the exclusive owned isolated test lane, including test_critical_coverage_config and other nominal pure files because autouse conftest provisions migration ownership. DB ops/browser/recovery likewise serialize with that lane. Same-wave08 frontend and14 DB may overlap only their disjoint non-DB work. Commands within a task run sequentially, not concurrent subprocesses. Provision disposable stacks only with synthetic stripped environment/fake providers/console email and exact-owned cleanup. Never reuse dev/private .env. Measure selectors before claiming60second feedback; full security/recovery/browser/concurrency are explicit long-running gates with raw timing/status updates.

### Final gate contract

- Plan15 explicitly updates the prior60-module critical inventory in CI/docs/assertion with new API/grant/normalization/shared valuation/authz critical modules while retaining overall80/critical100 and raw audit/all5 immutable-image policies.
- Plan17.1 executes actual whole `python3 deploy/tests/run-portfolio-validation.py --suite all-security` at frozen reviewed source;17.2 executes actual whole `python3 deploy/tests/run-portfolio-validation.py --suite recovery` at that same source with new exclusive Phase13 archive. Seven stages name current0020, retain complete authenticated0017/earlier profiles, authenticate exact archive/current+retained/CORE/unit/source/image bytes before/after every stage, destroy original source before cold recovery, compare fresh/upgradedTLS authority and support rollback or explicit before-write refusal. No prior/partial receipts substitute.
- Parent independent code/security/UI reviews and final goal verification remain required. Plan16's source-bound implemented screenshots/instructions cover new UI;18.1 owner UI and18.2 genuine desktop native200 remain separately blocking and cannot autoapprove. Existing Phase12 acceptance is only unchanged-screen evidence.
- Full four-source GOAL/11REQ/20RESEARCH/14CONTEXT and checkedUI audit resides in13-PLAN-COVERAGE. No deferred scope is silently brought forward; active split/dividend/correction and current recovery are not deferred.

### Planned sampling sign-off

- [x] Final tasks/waves/commands/threat IDs assigned in18 bounded plans
- [x] New tests and command files have creation owners and behavioral assertions before implementation
- [x] Every task has automated verification; no three implementation tasks lack feedback
- [x] Exclusive backend/DB resource lane retained and same-wave files disjoint
- [x] Critical100/full security/current-retained exact recovery/reviews/UI-native200 gates retained
- [x] Independent plan checker approval
- [x] Actual Wave0 tests authored and executed during implementation
- [x] Final implementation, full campaigns and both owner outcomes passed

Planning-map completeness alone was not execution. The final audit above now supplies actual independent-check/execution evidence for both flags. Overall Phase13 completion still requires independent goal verification.
