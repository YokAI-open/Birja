---
phase: 8
slug: corporate-action-safe-ownership
status: executing
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-11
---

# Phase 8 validation strategy

Execution contract:13plans,29tasks,11waves,all five assigned requirements.
Actual results remain distinct from planned commands below. Nyquist sign-off
follows complete execution/verification.

## Executed progress

Plans01–12 are complete and independently reviewed; Waves1–10 local gates pass.
Plan02 includes actual retained encrypted0007–0011 recovery and restricted-role
populated/fresh TLS proofs. Plan05 adds actual ownership-service TLS consumers
and the minimum scheduler immutable-trade column reads. Review-discovered schema,
sequence-capture and journal bugs have observed regressions and fixes.

Plan08 adds actual exact0007–0012 encrypted recovery, nonprivileged operator
replay and populated/fresh restrictedTLS authority parity; reviewed fixes have
actual regressions. Latest Wave7:1551backend tests pass153.59s,99.82%overall;
29critical modules retain100%statements/branches. Plans10–12 now pass their
strict client, real browser, final coverage/security/image gates as recorded
below. Plan13 actual owner UI/external disposition remains pending. Whole-phase requirements,
human acceptance, live activation and Nyquist compliance are not marked complete.
See08-LOCAL-PROOF.md and individual summaries/reviews for actual receipts.

## Environment and sampling

Use locked pytest/asyncio/respx, Vitest/RTL, Chromium and guarded real isolated
PostgreSQL/Redis. Mock external HTTP only; no private keys, provider requests,
production/dev DB, host timers or Phase7 one-shot changes. Financial concurrency
uses observable barriers and real sessions, not mocked locks/sleep-only checks.

Every eligible task first creates meaningful failing assertions, then GREEN and
scoped static checks. Import/missing-file failure is not RED. Pure/HTTP/component
quick feedback targets under30s; measure actual execution, never claim unmeasured
timing. Database/operations/full suites/scans are separate longer serial gates.
Each task has feedback, each wave affected suites. Repeat broad gates only when
new changes/failures/unresolved concerns justify it.

## Exact per-task map

Threat IDs link each plan's STRIDE register. ASVS Level1 applies; V-category
labels use explicitly legacy4.0.3 taxonomy without certification claims.

| Task | Wave | Threat obligations | Automated command |
| --- | --- | --- | --- |
| 08-01-01 | 1 | T-08-01-01, T-08-01-02, T-08-01-SC | `cd backend && uv run pytest tests/test_stock_action_migrations.py tests/test_stock_quotes.py -q -x` |
| 08-01-02 | 1 | T-08-01-01, T-08-01-02, T-08-01-SC | `cd backend && uv run pytest tests/test_stock_action_migrations.py -k grants -q -x` |
| 08-02-01 | 2 | T-08-02-01, T-08-02-02, T-08-02-SC | `python3 deploy/tests/test-stock-recovery-contracts.py` |
| 08-02-02 | 2 | T-08-02-01, T-08-02-02, T-08-02-SC | `bash deploy/tests/test-db-operations.sh --all` |
| 08-03-01 | 1 | T-08-03-01, T-08-03-02, T-08-03-SC | `cd backend && uv run pytest tests/test_stock_admission.py -q -x` |
| 08-03-02 | 1 | T-08-03-01, T-08-03-02, T-08-03-SC | `cd backend && uv run pytest tests/test_corporate_action_rules.py -q -x` |
| 08-04-01 | 2 | T-08-04-01, T-08-04-02, T-08-04-03, T-08-04-SC | `cd backend && uv run pytest tests/test_alpaca_actions.py -k rest -q -x` |
| 08-04-02 | 2 | T-08-04-01, T-08-04-02, T-08-04-03, T-08-04-SC | `cd backend && uv run pytest tests/test_alpaca_actions.py -q -x` |
| 08-05-01 | 3 | T-08-05-01, T-08-05-02, T-08-05-03, T-08-05-SC | `cd backend && uv run pytest tests/test_stock_ownership.py -k 'movement or lock or race' -q -x` |
| 08-05-02 | 3 | T-08-05-01, T-08-05-02, T-08-05-03, T-08-05-SC | `cd backend && uv run pytest tests/test_stock_ownership.py -q -x` |
| 08-06-01 | 4 | T-08-06-01, T-08-06-02, T-08-06-03, T-08-06-SC | `cd backend && uv run pytest tests/test_corporate_actions.py -k 'revision or ingest or late' -q -x` |
| 08-06-02 | 4 | T-08-06-01, T-08-06-02, T-08-06-03, T-08-06-SC | `cd backend && uv run pytest tests/test_corporate_actions.py -k split -q -x` |
| 08-06-03 | 4 | T-08-06-01, T-08-06-02, T-08-06-03, T-08-06-SC | `cd backend && uv run pytest tests/test_corporate_actions.py -k entitlement -q -x` |
| 08-07-01 | 5 | T-08-07-01, T-08-07-02, T-08-07-03, T-08-07-SC | `cd backend && uv run pytest tests/test_stock_action_monitoring.py -q -x` |
| 08-07-02 | 5 | T-08-07-01, T-08-07-02, T-08-07-03, T-08-07-SC | `cd backend && uv run pytest tests/test_stock_action_monitoring.py tests/test_config.py tests/test_scheduler.py -q -x` |
| 08-08-01 | 6 | T-08-08-01, T-08-08-02, T-08-08-03, T-08-08-04, T-08-08-SC | `cd backend && uv run pytest tests/test_stock_action_resolutions.py -k authority -q -x` |
| 08-08-02 | 6 | T-08-08-01, T-08-08-02, T-08-08-03, T-08-08-04, T-08-08-SC | `cd backend && uv run pytest tests/test_stock_action_resolutions.py -q -x` |
| 08-08-03 | 6 | T-08-08-01, T-08-08-02, T-08-08-03, T-08-08-04, T-08-08-SC | `python3 deploy/tests/test-stock-recovery-contracts.py && bash deploy/tests/test-db-operations.sh --all` |
| 08-09-01 | 7 | T-08-09-01, T-08-09-02, T-08-09-03, T-08-09-SC | `cd backend && uv run pytest tests/test_stocks_api.py -k action -q -x` |
| 08-09-02 | 7 | T-08-09-01, T-08-09-02, T-08-09-03, T-08-09-SC | `cd backend && uv run pytest tests/test_stock_quotes.py tests/test_stocks_api.py -q -x` |
| 08-10-01 | 8 | T-08-10-01, T-08-10-02, T-08-10-SC | `cd frontend && npm run test -- src/api/stocks.test.ts` |
| 08-10-02 | 8 | T-08-10-01, T-08-10-02, T-08-10-SC | `cd frontend && npm run test -- src/hooks/useStocks.test.tsx src/api/stocks.test.ts` |
| 08-11-01 | 9 | T-08-11-01, T-08-11-02, T-08-11-SC | `cd frontend && npm run test -- src/components/StockSection.test.tsx` |
| 08-11-02 | 9 | T-08-11-01, T-08-11-02, T-08-11-SC | `cd frontend && npx playwright test e2e/stock-actions.spec.ts` |
| 08-12-01 | 10 | T-08-12-01, T-08-12-02, T-08-12-03, T-08-12-SC | `cd backend && uv run pytest tests/test_stock_scheduler.py tests/test_stock_action_monitoring.py tests/test_critical_coverage_config.py -q -x` |
| 08-12-02 | 10 | T-08-12-01, T-08-12-02, T-08-12-03, T-08-12-SC | `cd backend && uv run pytest --cov=app --cov-fail-under=80` |
| 08-12-03 | 10 | T-08-12-01, T-08-12-02, T-08-12-03, T-08-12-SC | `git diff --check` |
| 08-13-01 | 11 | T-08-13-01, T-08-13-02, T-08-13-SC | `git diff --check` |
| 08-13-02 | 11 | T-08-13-01, T-08-13-02, T-08-13-SC | `git diff --check` |

For checkpoints/documentation, git diff --check validates only record syntax;
it never establishes external permission, live suitability or human acceptance.
The behavioral/operations proof and actual owner answers are separate obligations.

## Missing tests and creation dependencies

| Wave/plan | Target creation before implementation | Prerequisite |
| --- | --- | --- |
| 1/01 | test_stock_action_migrations.py, constrained0011 models; existing test_stock_quotes.py epoch-zero compatibility/nonzero-refusal regressions | Existing guardedPG/migration and admitted catalogue quote fixtures; migrated head |
| 1/03 | test_corporate_action_rules.py; existing admission regressions | Existing pure rules/calendar analog |
| 2/02 | Extend exact recovery/TLS fixtures | Reviewed0011 |
| 2/04 | test_alpaca_actions.py | Plan03 exported contracts |
| 3/05 | test_stock_ownership.py, stock_action_fixtures.py | Plan02 recovery proof + Plan03 rules |
| 4/06 | test_corporate_actions.py | Bounded adapter + journal |
| 5/07 | test_stock_action_monitoring.py; config/scheduler regressions | Transactional event services |
| 6/08 | test_stock_action_resolutions.py;0012 exact recovery/TLS/ACL cases | Durable monitor/holds |
| 7/09 | Extend existing test_stocks_api.py/test_stock_quotes.py |0012 recovery/authority proof |
| 8/10 | Existing stocks.test.ts/useStocks.test.tsx action cases | Final API contract |
| 9/11 | Existing StockSection.test.tsx; new stock-actions.spec.ts | Strict client safety |
| 10/12 | Existing critical coverage/shared quota regressions | All implementation |
| 11/13 | Concrete UAT/activation records; actual owner outcomes | All local gates |

Same-wave Plans01/03 and02/04 have exclusive modified files. Every task lists
actual targets/analogs in read_first; a new target is confirmed absent, then
created with behavioral assertions before implementation. No test-framework
installation is required. Configuration/documentation do not need contrived RED.

Plan01 owns the schema-adjacent explicit quote-column mapping and epoch-zero
compatibility tests as soon as unit_epoch is introduced; it must not leave the
existing writer broken until Plan09. Nonzero-unit writes stay closed meanwhile.
Plan03 retains admission/rules ownership with no overlapping files. Plan09 owns
authentic gate-bound current-unit provenance and the real quote/split race proof;
Plan01's final-statement zero-unit guard does not claim that complete proof.

## Requirement proof matrix

| Requirement | Tasks | Required behavior |
| --- | --- | --- |
| DIV-01 |03-01/02,04-01/02,06-01,07-01,08-02 | Explicit ordinaryUSD/dates/identity, immutable economic/source revisions, current process_date/known-ID rechecks, deletion ambiguity, complete bounded catch-up |
| DIV-02 |05-01/02,06-03 | Before/at/after cutoff, sold-out owner, genuine calendar/DST, complete historical journal, processed split units, entitlement revision lineage |
| ACT-01 |03-02,06-02,09-02 | Exact rational whole shares; every-owner fractional/overflow refusal, byte-identical total basis/fills, post-split quote invalidation |
| ACT-02 |06-01,07-01,08-01/02,09-01,10-01/02,11-01/02 | Persistent holds, audited scoped resolution, no green-poll override, final committed API, strict client/cache and accessible UI |
| ACT-03 |05-01,06-01/02/03,07-01/02,08-03,12-01 | Economic-key once-only effects, post-lock time, rollback/races, same-boundary units, explicit monitoring loss/complete recovery and restored replay |
| Compatibility |01-01/02,02-01/02,08-03,12-02 | Legacy preservation, exact0011/0012 and predecessor recovery/identities/ACL, actual upgraded/fresh restrictiveTLS parity |

## Required real PostgreSQL experiments

1. Split/split replay, fault after quantity/before marker: one application or
   no effects; exact unchanged total basis and immutable fills.
2. Fill-like journal append blocked across cutoff/monitor expiry: actual
   post-lock wall clock/current authority refuses new unsafe movement. These
   fixtures do not expose stock orders; Phase9 first fill must use this contract.
3. Freeze versus fill-like movement, split versus entitlement, quote versus
   split: shared gate and deterministic order, unknown same-boundary units held.
4. Stale operator decision versus source revision/generation/epoch: immutable
   scoped audit/conflict, no runtime override or cash mutation.
5. Exact restored state replay: no repeated split/resolution; cursor, journal,
   entitlements and next identities preserved. Redis loss cannot recreate effects.

Use at least two real sessions, explicit barriers and bounded lock waits; test
both acquisition orders where relevant.

## Final gates and rollout order

Full backend80%overall and expanded exact100%critical coverage, frontend
coverage/static, crypto/auth/API regressions, isolated browser journeys, audits,
hardened nonroot runtime smoke and strictHIGH/CRITICAL including-unfixed image
scans remain enforced. Independent code/security/UI reviews close blocking/high
findings. Record actual source identities, commands, counts, elapsed durations
and measured quick lane. No broad repeated test runs without justification.

Operations: `python3 deploy/tests/test-stock-recovery-contracts.py` then serial
`bash deploy/tests/test-db-operations.sh --all`. Exact0007–0012 manifests,
schema/rows/sequences/functionACL, populated restrictiveTLS upgrade without
grant-repair and fresh parity, same retained encrypted archive and nonempty
financial/action state are required. Restore replay must not duplicate effects.

Future rollout order: reviewed compatible recovery tooling/backup, schema0011,
schema0012, then runtime consuming new tables/function. Populated downgrade
refuses; binary rollback preserves current candidate ledger/units. Installed
tool replacement/production provisioning/deployment require separate approval.

## Human/external gates

Phase7 UI remains accepted; live identity/freshness remains owner-deferred,
not passed. Do not duplicate or alter that campaign. Plan13 asks only new
Phase8 UI acceptance after actual automated screenshots/proof.

Distinct action REST/replay access, broader transport scope, durable normalized
derived accounting/DB/backup rights, quotas, history/deletion continuity/latency
and attribution require explicit activation evidence. Existing IEX approval is
not a new action grant. Numerical defaults are internal safety policy, not SLA.
Unknown inputs keep live activation disabled; owner may defer external evidence
and continue isolated development. Deferred never equals passed.

No execution/compliance/activation is claimed. Flags remain false until actual
proof and independent validation.

## Wave8 measured client gate

Plan10 focused144tests pass5.15s; strict parser100%allmetrics. Full frontend
419tests/28files pass15.96s with98.84%statements/97.09%branches/99.6%functions/
99.53%lines; lint, types, all-file Prettier and build pass. Independent review
at7473df3 has0active findings. Exact-deadline, raw authority high-water, denial/
cache-remount and recovery regressions passed; Phase8 browser/UI proof is next.

## Wave9 measured presentation gate

Plan11 focused17RTL tests pass5.56s. Broad stock browser matrix21stories69.4s;
final4responsive widths plusCSS200%/640CSS reflow5stories21.5s. Exact source and
zoom limitations are retained in08-11-BROWSER.md. Full frontend429tests/28files
pass15.68s,98.87%statements/97.29%branches/99.61%functions/99.66%lines; full
lint/types/Prettier/build pass. Independent UI24/24,0active findings; independent
33-source runtime review is clear. Final CI/test mirror follow-up and Plan12
full backend/browser/image gates remain pending. No owner acceptance inferred.

## Wave10 final local gate

Final1551backend tests pass163.92s,99.82%overall; exactCI/CLAUDE/test29-module
critical mirror passes2972statements/978branches100%. Frontend429tests and all
static/build checks pass. Full browser31pass/1expected production-CSP skip,
retries0,130.4s; owned cleanup empty. Hardened nonroot native77tests pass2.36s
using isolated testRedis; separate actual runtime network-free smoke passes.
All five strict image scans exit0 with0HIGH/CRITICAL including unfixed; audits
pass required thresholds. Image13/CI10contracts and explicit realSQL recovery
10/10 contracts pass. Same retained encrypted0007–0012 exact recovery/roles/both
verifiedTLS proofs remain current. Code review0active, UI24/24, security44/44
implementation mitigations closed;3Plan13 checkpoint threats remain pending.

All27 automatic tasks have implementation/proof; two owner checkpoints remain.
No Nyquist/whole-phase sign-off or requirement completion is inferred before
actual Plan13 disposition and goal verification. See final08-LOCAL-PROOF.md.
