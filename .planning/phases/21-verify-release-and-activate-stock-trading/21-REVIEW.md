---
phase: 21-verify-release-and-activate-stock-trading
reviewed: 2026-11-25T08:31:00Z
re_reviewed: 2026-11-25T11:00:19Z
depth: standard
diff_base: ada94ab
reviewed_head: 705566c
tested_source: bb81292
files_reviewed: 43
files_reviewed_list:
  - .github/workflows/ci.yml
  - backend/app/api/v2/stock_catalog.py
  - backend/app/core/config.py
  - backend/app/core/deps.py
  - backend/app/main.py
  - backend/app/tasks/scheduler.py
  - backend/app/tasks/stock_catalog_import.py
  - backend/app/tasks/stock_catalog_quotes.py
  - backend/app/tasks/stock_halts.py
  - backend/tests/test_accounts.py
  - backend/tests/test_configured0008_migration.py
  - backend/tests/test_event_history.py
  - backend/tests/test_migrations.py
  - backend/tests/test_portfolio_closure_admission.py
  - backend/tests/test_portfolio_management_admission.py
  - backend/tests/test_portfolio_management_grants.py
  - backend/tests/test_portfolio_routes.py
  - backend/tests/test_portfolio_stock_authority.py
  - backend/tests/test_scheduler.py
  - backend/tests/test_stock_action_monitoring.py
  - backend/tests/test_stock_admission.py
  - backend/tests/test_stock_catalog_event_history.py
  - backend/tests/test_stock_catalog_financial_actions.py
  - backend/tests/test_stock_catalog_publish.py
  - backend/tests/test_stock_catalog_quote_scheduler.py
  - backend/tests/test_stock_catalog_trade_context.py
  - backend/tests/test_stock_catalog_valuation.py
  - backend/tests/test_stock_halts.py
  - backend/tests/test_stock_trading_waits.py
  - deploy/RUNBOOK.md
  - deploy/STOCK-DATA-ADMISSION.md
  - deploy/tests/ops-fixtures.py
  - deploy/tests/portfolio-smoke.py
  - deploy/tests/portfolio-sources.py
  - deploy/tests/run-portfolio-validation.py
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-deploy-compatibility.sh
  - deploy/tests/test-portfolio-recovery-contracts.py
  - deploy/tests/test-portfolio-validation-contracts.py
  - deploy/tests/test-rollback-db-security.sh
  - deploy/tests/test-stock-catalog-finance-recovery.sh
  - docker-compose.prod.yml
  - frontend/e2e/stock-trade-fixture.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 21 Code Review

The review traced the changed recovery and CI stages, catalog operator and
runtime, and guarded browser refresh. Both original blockers are resolved.
The corrected candidate still requires a clean hosted run on its exact tree.

## Narrative Findings (AI reviewer)

### CR-01 Resolved · The guarded browser catalog worker supplies the quota client

**Files** `frontend/e2e/stock-trade-fixture.py:1063` and `backend/app/tasks/stock_catalog_quotes.py:334`

The original fixture omitted the quota client required by the background
quote worker and could fail on the first pending quote. Commit `762629f`
passes the disposable shared Redis client in both roles. The guarded catalog
browser run passed all seven cases on that source. The scheduler integration
test covers separate clients.

### CR-02 Resolved · Operator admission grants usable catalog action scope

**Files** `backend/app/tasks/stock_catalog_import.py:116` and `:356`, and
`backend/tests/test_stock_action_monitoring.py:136`

The original shared listing schema rejected the policy fields the scheduler
needed for action collection. Commit `a69ddc9` adds a strict artifact-specific
scope, reuses `catalog_action_policy`, and binds reviewed symbols to the
listing. The disposable PostgreSQL receipt checks dry-run rollback, refusal
of invalid scope, apply with the exact packet digest, and policy consumption
by the restricted scheduler.

## Verification

The review traced the seven stage callbacks and success-only archive staging,
the exact old and candidate runtime image bindings, and synthetic pre-write
and post-write checks. It also traced API authentication and cache refusals,
shared quota reservation, and admission reads and writes. The re-review
checked the corrective diff, including retained and current ACL assertions,
history projection refusal, and state checks around a PostgreSQL order wait.
Both reviewed ranges passed `git diff --check`.

The baseline full backend run recorded 3,810 passes, 57 failures, and 42
setup errors. Targeted reruns passed the identified cases after correction.
The aggregate across identical `backend/app` bytes reports 94.41% overall and
100% critical branch coverage. The browser, admission, baseline and aggregate
receipt hashes matched the candidate record. The evidence consists of a red
baseline run and passing focused receipts. The exact integrated test tree
requires a fresh hosted full-suite run, along with the browser, audit, image
scan and seven-stage recovery gates. Live stock acceptance remains pending.
