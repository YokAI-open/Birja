---
phase: 10
slug: dividend-cash-and-event-history
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-12
---

# Phase10 — Validation Strategy

Planning contract only; no test execution or owner acceptance is asserted. Existing isolated pytest/PostgreSQL+Redis, Vitest/RTL and Playwright require no new package. Never use dev/production.

## Sampling and feedback

Per task: meaningful behavior test plus affected static checks. Focused selectors target under30s after owned-stack startup; measure and split slow selectors during execution. New tests are created in the named task before its selector runs. RED means an actual expected-behavior failure, never missing imports or collection errors. Every financial wave also runs full backend≥80% and the complete critical100% statement/branch gate. Frontend waves run full frontend coverage/static checks.

Mandatory retained recovery/TLS/browser/image gates take minutes and run serially at plans06/15/16. They remain required in addition to quick feedback. Plan06 must pass before runtime consumers07/10. Plan16 repeats complete final current-source proof with the same final retained archive and actual current-app replay, original/correction no-doublecash and app/scheduler quarantine. No provider/B2/private keys/installed tool/timer/production action.

## Per-task exact verification map

All entries pending execution. Threat IDs refer to the corresponding plan register; acceptance additionally uses its task behavior/action. No absent test is claimed present.

| Task | Wave | Requirements | Threats | Exact quick command | Test creation prerequisite / long gate |
|---|---|---|---|---|---|
| 10-01-1 | 1 | DIV-03, DIV-04, DIV-05 | T-10-01-01/02/03/SC | `cd backend && uv run pytest tests/test_dividend_schema.py -k 'anchor or zero_target' -q -x` | This task creates its new tests before selector; declared plan dependencies completed first. |
| 10-01-2 | 1 | DIV-03, DIV-04, DIV-05 | T-10-01-01/02/03/SC | `cd backend && uv run pytest tests/test_dividend_schema.py -q -x` | Previous task creates tests; this task extends them where specified; declared plan dependencies completed first. |
| 10-02-1 | 2 | DIV-03, DIV-04, DIV-05 | T-10-02-01/02/03/SC | `cd backend && uv run pytest tests/test_dividend_authority.py -k 'scheduler_boundary or half_even or shadow' -q -x` | This task creates its new tests before selector; declared plan dependencies completed first. |
| 10-02-2 | 2 | DIV-03, DIV-04, DIV-05 | T-10-02-01/02/03/SC | `cd backend && uv run pytest tests/test_dividend_authority.py -k 'acl or identity or direct_write' -q -x` | Previous task creates tests; this task extends them where specified; declared plan dependencies completed first. |
| 10-03-1 | 1 | DIV-03, DIV-05 | T-10-03-01/02/03/SC | `cd backend && uv run pytest tests/test_dividend_rules.py -q -x` | This task creates its new tests before selector; declared plan dependencies completed first. |
| 10-03-2 | 1 | DIV-03, DIV-05 | T-10-03-01/02/03/SC | `cd backend && uv run pytest tests/test_dividend_rules.py -q -x` | Previous task creates tests; this task extends them where specified; declared plan dependencies completed first. |
| 10-04-1 | 3 | DIV-04, DIV-05 | T-10-04-01/02/03/SC | `python3 deploy/tests/test-stock-recovery-contracts.py` | This task creates its new tests before selector; declared plan dependencies completed first. |
| 10-04-2 | 3 | DIV-04, DIV-05 | T-10-04-01/02/03/SC | `python3 deploy/tests/test-stock-recovery-contracts.py` | Previous task creates tests; this task extends them where specified; declared plan dependencies completed first. |
| 10-05-1 | 4 | DIV-03, DIV-04, DIV-05 | T-10-05-01/02/03/SC | `python3 -m py_compile deploy/tests/dividend-execution-fixture.py deploy/tests/ops-fixtures.py` | This task creates its new tests before selector; declared plan dependencies completed first. |
| 10-05-2 | 4 | DIV-03, DIV-04, DIV-05 | T-10-05-01/02/03/SC | `bash -n deploy/tests/test-db-operations.sh deploy/tests/test-restore-safety.sh` | Previous task creates tests; this task extends them where specified; declared plan dependencies completed first. |
| 10-06-1 | 5 | DIV-04, DIV-05 | T-10-06-01/02/03/SC | `python3 -m py_compile deploy/backup-snapshot.py deploy/verify-restore.py deploy/tests/ops-fixtures.py` | 04/05 create actual contracts/fixtures; this plan runs mandatory long retained0007–0014/roles/TLS proof. |
| 10-06-2 | 5 | DIV-04, DIV-05 | T-10-06-01/02/03/SC | `git diff --check` | 04/05 create actual contracts/fixtures; this plan runs mandatory long retained0007–0014/roles/TLS proof. |
| 10-07-1 | 6 | DIV-03, DIV-04, DIV-05 | T-10-07-01/02/03/SC | `cd backend && uv run pytest tests/test_dividend_payments.py tests/test_dividend_corrections.py -k 'due or correction or original' -q -x` | This task creates its new tests before selector; declared plan dependencies completed first. |
| 10-07-2 | 6 | DIV-03, DIV-04, DIV-05 | T-10-07-01/02/03/SC | `cd backend && uv run pytest tests/test_dividend_payments.py tests/test_dividend_corrections.py -q -x` | Previous task creates tests; this task extends them where specified; declared plan dependencies completed first. |
| 10-08-1 | 7 | DIV-03, DIV-04, DIV-05 | T-10-08-01/02/03/SC | `cd backend && uv run pytest tests/test_dividend_concurrency.py -k 'duplicate or spend or rollback' -q -x` | This task creates its new tests before selector; declared plan dependencies completed first. |
| 10-08-2 | 7 | DIV-03, DIV-04, DIV-05 | T-10-08-01/02/03/SC | `cd backend && uv run pytest tests/test_dividend_waits.py -q -x` | Previous task creates tests; this task extends them where specified; declared plan dependencies completed first. |
| 10-09-1 | 8 | DIV-03, DIV-04, DIV-05 | T-10-09-01/02/03/SC | `cd backend && uv run pytest tests/test_dividend_scheduler.py -k 'bounded or retained or duplicate' -q -x` | This task creates its new tests before selector; declared plan dependencies completed first. |
| 10-09-2 | 8 | DIV-03, DIV-04, DIV-05 | T-10-09-01/02/03/SC | `cd backend && uv run pytest tests/test_dividend_scheduler.py tests/test_scheduler_loop.py -q -x` | Previous task creates tests; this task extends them where specified; declared plan dependencies completed first. |
| 10-10-1 | 6 | HIST-03, DIV-03, DIV-05 | T-10-10-01/02/03/SC | `cd backend && uv run pytest tests/test_event_history_cursor.py -q -x` | This task creates its new tests before selector; declared plan dependencies completed first. |
| 10-10-2 | 6 | HIST-03, DIV-03, DIV-05 | T-10-10-01/02/03/SC | `cd backend && uv run pytest tests/test_event_history.py -k 'mixed or owner or lineage' -q -x` | Previous task creates tests; this task extends them where specified; declared plan dependencies completed first. |
| 10-11-1 | 7 | HIST-03, DIV-03, DIV-05 | T-10-11-01/02/03/SC | `cd backend && uv run pytest tests/test_event_history_api.py -q -x` | This task creates its new tests before selector; declared plan dependencies completed first. |
| 10-11-2 | 7 | HIST-03, DIV-03, DIV-05 | T-10-11-01/02/03/SC | `cd backend && uv run pytest tests/test_history_api.py tests/test_portfolio_snapshot.py -q -x` | Previous task creates tests; this task extends them where specified; declared plan dependencies completed first. |
| 10-12-1 | 1 | HIST-03, DIV-03, DIV-05 | T-10-12-01/02/03/SC | `cd frontend && npm run test -- src/api/eventHistory.test.ts` | This task creates its new tests before selector; declared plan dependencies completed first. |
| 10-12-2 | 1 | HIST-03, DIV-03, DIV-05 | T-10-12-01/02/03/SC | `cd frontend && npm run test -- src/api/eventHistory.test.ts` | Previous task creates tests; this task extends them where specified; declared plan dependencies completed first. |
| 10-13-1 | 8 | HIST-03, DIV-04 | T-10-13-01/02/03/SC | `cd frontend && npm run test -- src/hooks/useEventHistory.test.tsx` | This task creates its new tests before selector; declared plan dependencies completed first. |
| 10-13-2 | 8 | HIST-03, DIV-04 | T-10-13-01/02/03/SC | `cd frontend && npm run test -- src/hooks/useEventHistory.test.tsx` | Previous task creates tests; this task extends them where specified; declared plan dependencies completed first. |
| 10-14-1 | 9 | HIST-03, DIV-03, DIV-05 | T-10-14-01/02/03/SC | `cd frontend && npm run test -- src/components/HistoryEventDetails.test.tsx` | This task creates its new tests before selector; declared plan dependencies completed first. |
| 10-14-2 | 9 | HIST-03, DIV-03, DIV-05 | T-10-14-01/02/03/SC | `cd frontend && npm run test -- src/pages/HistoryPage.test.tsx src/components/HistoryEventDetails.test.tsx` | Previous task creates tests; this task extends them where specified; declared plan dependencies completed first. |
| 10-15-1 | 10 | DIV-03, DIV-04, DIV-05, HIST-03 | T-10-15-01/02/03/SC | `python3 -m py_compile deploy/tests/dividend-execution-fixture.py deploy/tests/run-stock-browser.py` | New browser fixture/spec created in15-1; mandatory actual dividends suite and full browser in15-2. |
| 10-15-2 | 10 | DIV-03, DIV-04, DIV-05, HIST-03 | T-10-15-01/02/03/SC | `cd frontend && npx tsc --noEmit` | New browser fixture/spec created in15-1; mandatory actual dividends suite and full browser in15-2. |
| 10-16-1 | 11 | DIV-03, DIV-04, DIV-05, HIST-03 | T-10-16-01/02/03/SC | `cd backend && uv run pytest tests/test_critical_coverage_config.py -q -x` | All preceding tests exist;16-1 extends coverage regression before selector.16-2 full serial suites/audits/five scans/same-archive recovery/TLS/rollback. |
| 10-16-2 | 11 | DIV-03, DIV-04, DIV-05, HIST-03 | T-10-16-01/02/03/SC | `python3 -m py_compile deploy/tests/dividend-execution-fixture.py deploy/tests/stock-runtime-fixture.py` | All preceding tests exist;16-1 extends coverage regression before selector.16-2 full serial suites/audits/five scans/same-archive recovery/TLS/rollback. |
| 10-17-1 | 12 | DIV-03, DIV-04, DIV-05, HIST-03 | T-10-17-01/02/03/SC | `git diff --check` | This task creates its new tests before selector; declared plan dependencies completed first. |
| 10-17-2 | 12 | DIV-03, DIV-04, DIV-05, HIST-03 | T-10-17-01/02/03/SC | `git diff --check` | Previous task creates tests; this task extends them where specified; declared plan dependencies completed first. |
| 10-18-1 | 13 | HIST-03, DIV-03, DIV-05 | T-10-18-01/02/03/SC | `git diff --check` | Actual owner answer, plus previously passed17; human checks cannot be replaced by git diff. |
| 10-18-2 | 13 | HIST-03, DIV-03, DIV-05 | T-10-18-01/02/03/SC | `git diff --check` | Actual owner answer, plus previously passed17; human checks cannot be replaced by git diff. |

## Source and dependency checks

18 plans /36 tasks /13 waves. Same-wave ownership:01(models/migration tests),03(pure rules),12(client parser) are disjoint;07(service) and10(SQL History) are disjoint;08(concurrency) and11(API) are disjoint. Later shared files are dependency-ordered. Models/function02→producer04→actual restricted fixtures05→proof06 before consumers. CI mirrors all39 predecessor critical modules plus every new financial/privacy module; no exclusion to preserve100%.

## Manual-only checks

### Revision1 behavioral additions

-10-01/02 freeze nullable uncertain target/entitlement fields and stable held-status
dedup plus all actual mixed-query indexes before the pre-consumer proof. Both
`apply_stock_dividend(bigint,bigint,text,text)` and
`record_stock_dividend_hold(bigint,text)` enter exact owner/body/path/ACL recovery.
-10-09 now depends on10-11 as well as10-08 for its actual scheduler→restricted
SQL→mixed History regression. Its focused command includes `or uncertain`.
PaidA→held/cancelledB must remain discoverable with no latest eligible row:
one owner-visible held record, no cash change, repeat no duplicate; reviewed
verified reconciliation yields one applied successor and unchanged original.
Pre-anchor uncertainty creates no fabricated zero Dividend/anchor.
- The no-cash function derives owner/current observed revision and optional latest
entitlement internally, requires an existing payment and current retained rights,
and does not require an eligible revision/entitlement. Unknown target/proposal
remain null. Tests02/04/05/07/08/09/10/11/12/15/16 cover authority, recovery,
service, scheduler, projection and strict client rendering of this same state.
- Plan10 cannot edit0014 indexes/schema after proof06. Unforeseen changes require
an explicit successor migration and renewed restricted/TLS/retained gate before
consumers. Every plan now names actual wiring links and task-local source analogs.

18-1 actual owner acceptance of new mixed History, gross Dividend, linked correction, visible held no-cash state and original outside page.18-2 genuine desktop native200% browser zoom readability/reachability/no overlap/no horizontal page overflow when automation cannot prove it. Earlier Phase9 acceptance does not apply. Source/hash-bound offline index/HTML/ZIP supplied before asking. Live Phase7/8 activation and publication remain separately deferred.

## Sign-off

- [ ] Every task's focused behavioral selector and scoped static checks actually pass.
- [ ] Current critical100% statement/branch list agrees in CI/docs/regression.
- [ ] Real postwait/concurrent/shared-cash and restricted SQL bypass denials pass.
- [ ] Exact retained0007–0014 recovery, fresh/upgraded TLS and final same-archive current-app replay/rollback pass.
- [ ] Full backend/frontend/browser/audits/five strict image scans pass.
- [ ] Code/security/UI/goal reviews are recorded with honest attribution.
- [ ] Owner accepts new UI and genuine native200% outcome is recorded.
- [ ] Set nyquist_compliant/wave_0_complete true only from actual execution evidence.
