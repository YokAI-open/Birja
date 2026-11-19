---
phase: 14
slug: end-strategies-safely
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-19
---

# Phase 14 — Validation Strategy

Planning contract only. No Phase14 implementation, test result or human
acceptance is claimed. The concrete38-task map below assigns plan/task/wave IDs, threat references
and test-creation owners; no task has executed yet.

## Test Infrastructure

Existing pytest/pytest-asyncio and isolated real PostgreSQL/Redis;
Vitest/React Testing Library and Playwright. Configuration remains
`backend/pyproject.toml`, `frontend/vite.config.ts`,
`frontend/playwright.config.ts`. No framework/dependency installation.

After each task use its bounded selector, source static checks and relevant
retained regressions. After each wave run affected integrations, not a repeat
of the hour-long final campaign. Before verification run complete:

```
python3 deploy/tests/run-portfolio-validation.py --suite all-security
python3 deploy/tests/run-portfolio-validation.py --suite recovery
```

These are final qualification commands, run sequentially at one frozen source.
Current runner requires planned successor adaptation before execution. Prior
actual Phase13 times were3373s security and2792s recovery; new scope may exceed
these. Routine target feedback aims under60s where feasible; real DB startup,
transactions/races and integration groups are measured latency exceptions.
Never substitute DB mocks or report an unmeasured short latency promise.

## Sampling and Resource Discipline

- Every task has automated verification or an explicit earlier test-creation
  dependency; never three consecutive tasks without automated feedback.
- All backend pytest (including nominal pure tests), DB operations, browser
  runners and recovery use one exclusive serial disposable lane. No dev/prod
  stack, secrets or provider calls. Frontend pure units/offline contracts can
  overlap only with explicitly disjoint files/resources.
- Use actual blocked-PID/lock barriers, not sleeps as evidence of concurrency.
  Historical migrations use separate databases and explicit revision targets;
  never downgrade a shared current database or blindly upgrade history to head.
- Before long campaigns run bounded current fixture/admission/compatibility
  diagnostics in the exact stripped child environment. PATH includes
  `/usr/sbin`; preflight existing Node24/uv/Python/restic/nginx and owned
  resources, authenticated immutable image IDs and archive/source bindings.
- Durable one-shot PID/start/log/status/exit receipts survive status questions;
  do not restart or assemble partial diagnostics into a whole-gate pass.
  A source repair requires fresh whole qualification.
- One new Phase14-specific exclusive archive path; preserve qualified
  `/tmp/birja-phase13-proof/recovery.tar.gz` and prior Phase12/13 archives.
  Recovery proves all seven stage families using the same pinned archive,
  successor current plus fixed0020/0017/older profiles, exact roles/TLS,
  source-destroyed independent oracles and safe rollback/refusal.
- Preserve all61 existing critical modules; include every new critical
  closure/authorization module at100%. Existing issue35 disposition is neither
  expanded nor remediated by this planning contract.

## Per-Task Verification Map

Proposed new files are MISSING until the named feature owner creates them.
Concrete creation ownership is mapped below; each command runs only after its
file and fixtures exist. The first table groups behaviors; the concrete map
uses the per-plan T-14-NN identifiers. Neither table claims passing evidence.

| Task/creation owner | Requirement | Threat / secure behavior | Test type | Automated command after creation | File exists / status |
|---|---|---|---|---|---|
| Closure authority/API | PMGT-03 | T-API: owner+CSRF, exact named intent, minimal replay, no retarget | real API | `cd backend && uv run pytest tests/test_portfolio_closure_api.py -k 'repeat or confirmation' -x` | MISSING / pending |
| Financial terminal boundary | PMGT-04 | T-FREEZE: immutable before/after oracle, unpaid/future effects excluded, no financial History append | real DB/jobs | `cd backend && uv run pytest tests/test_portfolio_closure_events.py -k 'unpaid or negative' -x` | MISSING / pending |
| Zero/replacement identity | PMGT-05 | T-IDENTITY: reads/login never grant, new ID only on explicit create | real API | `cd backend && uv run pytest tests/test_portfolio_closure_identity.py -k 'last or replacement' -x` | MISSING / pending |
| Stock continuity | PFIN-05 | T-STOCK: all historical instruments incl sold-out, global tails/units and sibling continuity | real DB | `cd backend && uv run pytest tests/test_portfolio_closure_stocks.py -k 'sold_out or successive' -x` | MISSING / pending |
| Commit/clock/management races | PFIN-06 | T-RACE: sorted gates before account, first-buy rediscovery, no grant/cap/effect duplication | real concurrency | `cd backend && uv run pytest tests/test_portfolio_closure_races.py -k 'first_buy or management' -x` | MISSING / pending |
| Privacy/final response fence | PSAFE-01 | T-PRIVACY: all normal reads/replays/cursors/originals reject closed/foreign; restricted TLS | real API/DB | `cd backend && uv run pytest tests/test_portfolio_closure_privacy.py -k 'cursor or original' -x` | MISSING / pending |
| Browser deletion/target lifetime | PCTX-03, PMGT-03/05, PSAFE-01 | T-UI: before-send persistence, same-ID unknown recovery, late/session/cross-tab privacy | unit | `cd frontend && npm run test -- src/hooks/usePortfolioDeletion.test.tsx src/components/PortfolioDeleteForm.test.tsx` | MISSING / pending |
| Full-stack deletion journeys | All seven | T-E2E: public DELETE, siblings, stale routes, replacement and zero-book state | real browser | `python3 deploy/tests/run-stock-browser.py` after runner includes `frontend/e2e/portfolio-deletion.spec.ts` | runner exists; new spec MISSING / pending |
| Recovery contracts | PMGT-04, PFIN-05/06, PSAFE-01 | T-RECOVERY: complete immutable lifecycle evidence, exact authority, no downgrade loss | offline+real restore | `python3 deploy/tests/test-portfolio-recovery-contracts.py` and `python3 deploy/tests/test-portfolio-validation-contracts.py`, then whole recovery above | files exist; successor cases pending |

## Wave 0 Requirements and Creation Dependencies

- [ ] Lifecycle schema/authority plan creates the independent frozen-finance
  oracle, multi-instrument/sold-out/clock fixtures and migration/SQL negatives.
  Lock exact lifecycle/stock interfaces before API/jobs consume them.
- [ ] API owner creates confirmation/status schemas and strict endpoint tests
  before frontend transport consumers; dedicated DELETE body parser, no PATCH
  validation flag workaround.
- [ ] Job/race owners create real before/after closure, unpaid/held correction,
  two-owner/sibling, first-buy and equal/backward-clock tests without weakening
  the existing one-instrument financial guard.
- [ ] UI owners create the hook/component tests named above and real e2e spec;
  existing suites are extended for owner/session, receipts, cursors and stale
  financial target boundaries. No command references an uncreated test owner.
- [ ] Recovery owner supplies successor inventories, immutable qualified0020
  source9527e35, complete0017source4b4320b and earlier profiles; explicit
  closed-fixture provenance, quarantine/ACL/catalogue parity, final runner
  preflight/image/archive and durable receipt contracts before long campaigns.

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Instructions |
|---|---|---|---|
| New deletion UI acceptance | PMGT-03/04/05, PCTX-03 | Owner assessment of actual reviewed screens | Download source-bound synthetic review packet; inspect named effects/Cancel, pending/unknown/recovery, rename refusal, stale/private boundary and empty/Create. Record actual answer. |
| Genuine native200% zoom | PCTX-03, PSAFE-01 | Viewport emulation is not native browser zoom | In desktop browser menu select200%; new screens remain readable/reachable without overlap or horizontal page scroll. Record actual owner outcome separately. |

## Validation Sign-Off

- [ ] Concrete task/wave/threat map filled and every task automated or dependent
- [ ] No three consecutive tasks without meaningful automated feedback
- [ ] All MISSING tests have explicit earlier creation owners
- [ ] No watch-mode flags, provider calls or production operations
- [ ] Bounded feedback measured; long exceptions and resource ownership recorded
- [ ] Independent security/code/UI review and whole final qualification pass
- [ ] New owner UI and native200 outcomes actually recorded
- [ ] `nyquist_compliant: true` set only after actual validation

**Approval:** Pending execution; this draft does not complete any requirement.

## Concrete Plan / Task / Wave Map

Revision1 prerequisite ownership:01-task1 adapts the finite migration-owner and
session-autouse harness before any successor tests;01-task2 registers models
and proves repeated post-backfill invocation.04-task1 owns independent SQL
deploy/db/bootstrap-roles.sql plus Python exact0023 authority parity;04-task2
owns current install_current_test_grants and runs the focused admission command
twice in independent pytest processes after0023 exists. Unknown objects,
unsafe owners and historical-schema substitution still refuse.15 only adapts
broader whole-suite fixtures after these prerequisites.14-task2 explicitly
owns App.test.tsx for route precedence, private unavailable target and stale
owner/session/navigation callbacks. No task/wave count changes.

The planning owner labels above resolve to these actual tasks. Existing framework
is reused; no framework-install Wave0 exists. NEW test/module files are created
by their task before command execution; earlier plan dependencies provide fixture
and protocol interfaces. None has run in Phase14 yet. T-14-NN threat controls are
in each plan; actual security dispositions and counts are execution evidence.

|Task|Wave|Requirements|Threat|Secure behavior / creation owner|Automated command|Existence / status|
|---|---|---|---|---|---|---|
|14-01-01|1|PMGT-04, PFIN-05, PSAFE-01|T-14-01|Add additive lifecycle and immutable intent schema| `cd backend && uv run pytest tests/test_portfolio_closure_migrations.py -k 'expansion or immutable' -x` |test/feature creation in this task; pending|
|14-01-02|1|PMGT-04, PFIN-05, PSAFE-01|T-14-01|Backfill only verified historical closed boundaries and validate links| `cd backend && uv run pytest tests/test_portfolio_closure_migrations.py -k 'backfill or corrupt or downgrade' -x` |test/feature creation in this task; pending|
|14-02-01|2|PMGT-03, PMGT-04, PFIN-06, PSAFE-01|T-14-02|Install narrow sorted-gate closure SQL authority| `cd backend && uv run pytest tests/test_portfolio_closure_authority.py -k 'named or sold_out or replay' -x` |test/feature creation in this task; pending|
|14-02-02|2|PMGT-03, PMGT-04, PFIN-06, PSAFE-01|T-14-02|Seal terminal named refusals and bound durable intent growth| `cd backend && uv run pytest tests/test_portfolio_closure_authority.py -k 'refusal or quota or replay or rollback' -x` |test/feature creation in this task; pending|
|14-03-01|3|PMGT-04, PFIN-05, PFIN-06|T-14-03|Share complete read-only stock proof without relaxing financial guard| `cd backend && uv run pytest tests/test_portfolio_closure_stocks.py -k 'guard or corrupt or multi' -x` |test/feature creation in this task; pending|
|14-03-02|3|PMGT-04, PFIN-05, PFIN-06|T-14-03|Fence equal/backward global stock times at successor boundary| `cd backend && uv run pytest tests/test_portfolio_closure_clocks.py -x` |test/feature creation in this task; pending|
|14-04-01|4|PMGT-04, PSAFE-01, PFIN-06|T-14-04|Version current0023 bootstrap and grant inventory| `cd backend && uv run pytest tests/test_portfolio_closure_admission.py tests/test_portfolio_management_grants.py -x` |test/feature creation in this task; pending|
|14-04-02|4|PMGT-04, PSAFE-01, PFIN-06|T-14-04|Wire migration-only transitions and runtime admission| `cd backend && uv run pytest tests/test_portfolio_closure_admission.py -k 'fresh or upgraded or partial or downgrade or repeated_bootstrap' -x && uv run pytest tests/test_portfolio_closure_admission.py -k 'fresh or upgraded or partial or downgrade or repeated_bootstrap' -x` |test/feature creation in this task; pending|
|14-05-01|5|PMGT-04, PFIN-05, PSAFE-01|T-14-05|Freeze qualified0020 source dispatch and build lifecycle oracle| `python3 deploy/tests/test-portfolio-fixture-contracts.py` |test/feature creation in this task; pending|
|14-05-02|5|PMGT-04, PFIN-05, PSAFE-01|T-14-05|Produce V3 authenticated inventory and validate lifecycle integrity| `python3 deploy/tests/test-portfolio-recovery-contracts.py` |test/feature creation in this task; pending|
|14-06-01|6|PMGT-04, PFIN-05, PFIN-06, PSAFE-01|T-14-06|Consume strictV3 quarantine and exact regrant| `python3 deploy/tests/test-portfolio-management-recovery.py --postgres` |test/feature creation in this task; pending|
|14-06-02|6|PMGT-04, PFIN-05, PFIN-06, PSAFE-01|T-14-06|Extend selected deployment/rollback and operating contracts| `bash deploy/tests/test-deploy-compatibility.sh` |test/feature creation in this task; pending|
|14-07-01|7|PMGT-03, PMGT-04, PMGT-05, PSAFE-01|T-14-07|Parse strict deletion intent and publish authenticated endpoint| `cd backend && uv run pytest tests/test_portfolio_closure_api.py -k 'confirmation or csrf or repeat or malformed' -x` |test/feature creation in this task; pending|
|14-07-02|7|PMGT-03, PMGT-04, PMGT-05, PSAFE-01|T-14-07|Prove real commit/response-loss and terminal refusal recovery| `cd backend && uv run pytest tests/test_portfolio_closure_api.py tests/test_portfolio_closure_identity.py -k 'response or delayed or last or replacement' -x` |test/feature creation in this task; pending|
|14-08-01|8|PMGT-04, PFIN-05, PFIN-06|T-14-08|Define retained lifecycle disposition and fence selected-before-close jobs| `cd backend && uv run pytest tests/test_portfolio_closure_events.py -k 'unpaid or negative or selected' -x` |test/feature creation in this task; pending|
|14-08-02|8|PMGT-04, PFIN-05, PFIN-06|T-14-08|Prove event boundary both orders and sibling independence| `cd backend && uv run pytest tests/test_portfolio_closure_events.py -x` |test/feature creation in this task; pending|
|14-09-01|9|PMGT-03, PMGT-04, PMGT-05, PFIN-05, PFIN-06|T-14-09|Exercise multi-stock sold-out closure and successive sibling splits| `cd backend && uv run pytest tests/test_portfolio_closure_stocks.py -k 'sold_out or successive or closed_market' -x` |test/feature creation in this task; pending|
|14-09-02|9|PMGT-03, PMGT-04, PMGT-05, PFIN-05, PFIN-06|T-14-09|Exercise real first-buy, duplicate-close and create/delete concurrency| `cd backend && uv run pytest tests/test_portfolio_closure_races.py -k 'first_buy or management or duplicate' -x` |test/feature creation in this task; pending|
|14-10-01|10|PCTX-03, PSAFE-01, PMGT-04|T-14-10|Inventory and fence late reads and metadata discovery| `cd backend && uv run pytest tests/test_portfolio_closure_privacy.py -k 'history or metadata or late_read' -x` |test/feature creation in this task; pending|
|14-10-02|10|PCTX-03, PSAFE-01, PMGT-04|T-14-10|Close original-reference and execution/retry authorization gaps| `cd backend && uv run pytest tests/test_portfolio_closure_privacy.py -k 'cursor or original or retry' -x` |test/feature creation in this task; pending|
|14-11-01|8|PMGT-03, PCTX-03, PSAFE-01|T-14-11|Parse exact deletion request, result and terminal errors| `cd frontend && npm run test -- src/api/portfolioDeletion.test.ts` |test/feature creation in this task; pending|
|14-11-02|8|PMGT-03, PCTX-03, PSAFE-01|T-14-11|Persist bounded metadata-only original before send| `cd frontend && npm run test -- src/lib/portfolioDeletionAttempt.test.ts` |test/feature creation in this task; pending|
|14-12-01|9|PMGT-03, PMGT-04, PCTX-03, PSAFE-01|T-14-12|Implement owner/session deletion state machine and explicit recovery| `cd frontend && npm run test -- src/hooks/usePortfolioDeletion.test.tsx -t 'unknown|original|refusal|persist'` |test/feature creation in this task; pending|
|14-12-02|9|PMGT-03, PMGT-04, PCTX-03, PSAFE-01|T-14-12|Reconcile lifecycle navigation and sibling independence| `cd frontend && npm run test -- src/hooks/usePortfolioDeletion.test.tsx src/hooks/usePortfolioManagement.test.tsx` |test/feature creation in this task; pending|
|14-13-01|10|PCTX-03, PSAFE-01, PFIN-06|T-14-13|Publish identity-only lifecycle invalidation and quarantine| `cd frontend && npm run test -- src/lib/portfolioMetadataEvents.test.ts src/hooks/usePortfolioTarget.test.tsx` |test/feature creation in this task; pending|
|14-13-02|10|PCTX-03, PSAFE-01, PFIN-06|T-14-13|Mask scoped finances and preserve safe unavailable recovery| `cd frontend && npm run test -- src/components/PortfolioTargetBoundary.test.tsx src/hooks/usePortfolioOverview.test.tsx` |test/feature creation in this task; pending|
|14-14-01|11|PMGT-03, PMGT-04, PMGT-05, PCTX-03, PSAFE-01|T-14-14|Build accessible named confirmation and unknown-result form| `cd frontend && npm run test -- src/components/PortfolioDeleteForm.test.tsx src/components/PortfolioMetadataForm.test.tsx` |test/feature creation in this task; pending|
|14-14-02|11|PMGT-03, PMGT-04, PMGT-05, PCTX-03, PSAFE-01|T-14-14|Mount metadata-only recovery and definitive empty/overview navigation| `cd frontend && npm run test -- src/pages/PortfolioDeletionPage.test.tsx src/pages/PortfoliosPage.test.tsx src/App.test.tsx` |test/feature creation in this task; pending|
|14-15-01|11|PMGT-04, PMGT-05, PFIN-05, PFIN-06, PSAFE-01|T-14-15|Make whole backend fixtures explicitly current or retained| `cd backend && uv run pytest tests/test_migrations.py tests/test_portfolio_closure_admission.py -x` |test/feature creation in this task; pending|
|14-15-02|11|PMGT-04, PMGT-05, PFIN-05, PFIN-06, PSAFE-01|T-14-15|Qualify actual fresh/upgraded TLS and rollback-tail successor branches| `bash deploy/tests/test-db-config.sh` |test/feature creation in this task; pending|
|14-16-01|12|PMGT-04, PFIN-05, PFIN-06, PSAFE-01|T-14-16|Extend CI critical paths and offline runner contracts| `python3 deploy/tests/test-portfolio-validation-contracts.py` |test/feature creation in this task; pending|
|14-16-02|12|PMGT-04, PFIN-05, PFIN-06, PSAFE-01|T-14-16|Implement bounded preflight and interruption-safe one-shot campaigns| `python3 deploy/tests/test-portfolio-validation-contracts.py && python3 deploy/tests/test-portfolio-smoke-image.py` |test/feature creation in this task; pending|
|14-17-01|13|PMGT-03, PMGT-04, PMGT-05, PFIN-05, PFIN-06, PCTX-03, PSAFE-01|T-14-17|Add public lifecycle browser journeys and register exact spec| `python3 deploy/tests/test-portfolio-browser-contracts.py && python3 deploy/tests/run-stock-browser.py --suite portfolios --grep 'deletion'` |test/feature creation in this task; pending|
|14-17-02|13|PMGT-03, PMGT-04, PMGT-05, PFIN-05, PFIN-06, PCTX-03, PSAFE-01|T-14-17|Build separate Phase14 packet and refusal contracts| `python3 deploy/tests/test-portfolio-ui-evidence.py && python3 deploy/tests/portfolio-ui-evidence.py --phase 14 --output /tmp/birja-phase14-ui-review` |test/feature creation in this task; pending|
|14-18-01|14|PMGT-03, PMGT-04, PMGT-05, PFIN-05, PFIN-06, PCTX-03, PSAFE-01|T-14-18|Review, preflight and run complete security at frozen source| `python3 deploy/tests/run-portfolio-validation.py --suite all-security` |existing runner, actual result pending|
|14-18-02|14|PMGT-03, PMGT-04, PMGT-05, PFIN-05, PFIN-06, PCTX-03, PSAFE-01|T-14-18|Run fresh seven-stage same-archive proof and exact final evidence| `python3 deploy/tests/run-portfolio-validation.py --suite recovery` |existing runner, actual result pending|
|14-19-01|15|PMGT-03/04/05,PCTX-03,PSAFE-01|T-14-19|Actual new UI owner outcome|`python3 deploy/tests/portfolio-ui-evidence.py --phase 14 --verify /tmp/birja-phase14-ui-review`|tool created17; human pending|
|14-19-02|15|PCTX-03,PSAFE-01|T-14-19|Separate actual native200 outcome|same current packet verify; actual human result required|human pending|

All38 tasks have an automated selector/entrypoint (the two manual checkpoints
also require actual owner answers). No three-task sampling gap or watch mode.
Focused realDB cases may exceed60s; finalwhole security/recovery are measured
long exceptions. No false green is inferred from file creation or planning checks.
