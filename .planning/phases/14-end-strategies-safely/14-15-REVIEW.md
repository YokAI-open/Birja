---
phase: 14-end-strategies-safely
plan: "15"
reviewed: 2026-11-19
depth: deep
source_commit: 24f716f
diff_base: aac0897
files_reviewed: 46
files_reviewed_list:
  - backend/app/db/portfolio_bootstrap.py
  - backend/app/db/portfolio_migrate.py
  - backend/tests/portfolio_fixtures.py
  - backend/tests/stock_action_fixtures.py
  - backend/tests/test_dev_bootstrap.py
  - backend/tests/test_dividend_authority.py
  - backend/tests/test_history_service.py
  - backend/tests/test_portfolio_closure_admission.py
  - backend/tests/test_portfolio_closure_authority.py
  - backend/tests/test_portfolio_closure_migrations.py
  - backend/tests/test_portfolio_creation.py
  - backend/tests/test_portfolio_crypto.py
  - backend/tests/test_portfolio_crypto_api.py
  - backend/tests/test_portfolio_dividend_authority.py
  - backend/tests/test_portfolio_dividend_first_buy.py
  - backend/tests/test_portfolio_dividends.py
  - backend/tests/test_portfolio_funding.py
  - backend/tests/test_portfolio_identity.py
  - backend/tests/test_portfolio_identity_api.py
  - backend/tests/test_portfolio_management_admission.py
  - backend/tests/test_portfolio_metadata.py
  - backend/tests/test_portfolio_migrate.py
  - backend/tests/test_portfolio_overview.py
  - backend/tests/test_portfolio_routes.py
  - backend/tests/test_portfolio_schema_admission.py
  - backend/tests/test_portfolio_scoped_history.py
  - backend/tests/test_portfolio_stock_authority.py
  - backend/tests/test_portfolio_stock_ownership.py
  - backend/tests/test_portfolio_stock_trading.py
  - backend/tests/test_portfolio_strategy_lifecycle.py
  - backend/tests/test_portfolio_valuation.py
  - backend/tests/test_stock_action_migrations.py
  - backend/tests/test_stock_execution_authority.py
  - backend/tests/test_stock_execution_migrations.py
  - backend/tests/test_stock_isolation.py
  - deploy/backup-snapshot.py
  - deploy/db/bootstrap-roles.sql
  - deploy/deploy.sh
  - deploy/tests/ops-fixtures.py
  - deploy/tests/portfolio-smoke.py
  - deploy/tests/test-db-config.sh
  - deploy/tests/test-db-operations.sh
  - deploy/tests/test-deploy-compatibility.sh
  - deploy/tests/test-portfolio-recovery-contracts.py
  - deploy/tests/test-portfolio-smoke-image.py
  - deploy/verify-restore.py
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 14 Plan 15 — Independent Code Review

## Narrative Findings (AI reviewer)

One proven **BLOCKER** remains in the newly added authentication of prior
schemas. No additional proven warning was identified in the scoped fixture,
source-pin, recovery-dispatch or TLS harness changes. No structural pre-pass
was supplied. Review scope is the exact46-file aac0897→24f716f change set;
this report does not certify the pending Plans16–19.

## Critical Issues

### CR-01: Prior authentication misses policy drift until after Alembic mutates the schema

**Classification:** BLOCKER.

**Files:** `backend/app/db/portfolio_bootstrap.py:448`;
`backend/app/db/portfolio_migrate.py:152`.

**Issue:** The new `PRE_CLOSURE_MIGRATION_SQL` recognizers are built from the
retained `PREFLIGHT_SQL` and its `CATALOGUE_SQL`. That historical projection
does not include policies, rules outside its separate rewrite check, or the
complete relation-kind inventory. In particular, adding a policy while RLS
remains disabled changes neither its catalogue hash nor the ACL/default hashes.
The separate relation inventory in `require_migrator` examines only ordinary
tables and sequences; it does not close this policy gap.

Consequently the current migration entry admits an unrecognized prior schema
and starts Alembic. The final0023 projection does include policies, so it refuses
only **after**0021/22/23 schema changes have occurred. This violates the new
before-child/no-mutation guarantee rather than merely producing a different
error message. The existing new index/grant/default negatives do not exercise
objects excluded from the historical projection.

**Independent reproduction:** With parent authorization, the reviewer used
only a disposable `birja-p14-r15-policy` stack, explicit
`--env-file /dev/null`, stripped environment and installed local tools. Starting
from genuine0020 runtime grants, the reviewer committed:

```sql
CREATE POLICY unexpected_review_policy ON accounts USING (true);
```

RLS remained disabled. Actual PostgreSQL results were:

```text
prior_catalogue_unchanged=true
prior_migrator_admitted=0020
revision_after_alembic=0023
final_preflight_rejected=true
```

The complete owned proof and cleanup took8.89s; its process returned0. Afterward
the exact project had zero containers, networks and volumes. No real data,
provider, production resource, repository source or dependency was changed.

**Fix:** Keep the frozen qualified0020/0017 projections and fingerprints
unchanged. Add a **current-only** supplemental prior-catalogue check before
Alembic that rejects policies and unexpected relation/object kinds (and covers
the applicable rules/RLS surface), or introduce separately measured complete
current migration-entry projections for0020/21/22. Run it alongside the exact
historical catalogue/ACL/default pairing. Add real drift tests for every
20/21/22 entry that assert no migration child is created, version/schema/data
remain unchanged and the unexpected object is retained for diagnosis. Update
only coordinated current source pins, then repeat the affected admission,
upgrade and source-bound recovery checks. Do not weaken the final0023 gate or
repair/drop unrecognized objects to make the transition succeed.

## Other assessed boundaries

- Final ordinary runtime still requires the unchanged final object ACL and
  private effective defaults. The additional exact inherited0020 object ACL
  is accepted only by explicit bootstrap; partial read grants, missing final
  reads, extra grants and explicit unsafe future defaults remain refusals.
- Python and administrative SQL carry matching transition-pair logic. Current
  producer, consumer and selected deployment pins consistently bind the changed
  bootstrap and migrator. Protected historical literals and migrations are not
  rewritten by this plan.
- Current service/API fixtures use genuine0023 authority and actual public
  DELETE where appropriate. The financial assertions remain present. Synthetic
  financial writers acquire the real instrument gate; pending announcements
  remain independent. Narrow deferred-root negative cases remain rollback-only.
  History tests end simulated requests before independent writers, while
  separate same-request final-fence assertions are retained.
- Current recovery calls forward the original source manifest before regrant.
  Family selection is authenticated and finite; fixed0020/0017 fixtures and
  images use complete historical source trees. Current image bindings retain
  source/context/config/ID verification and refuse lost or changed identities.
- Borrowed configuration stacks are authenticated before use and do not gain
  cleanup ownership. Child configuration is synthetic and strips inherited
  application environment. Owned resource cleanup remains scoped.

## Evidence and limits

The executor's3538 passing scenarios are explicitly diagnostic partitions,
not an uninterrupted final backend run. Its121-case repaired admission group,
100% coverage of both changed modules, source-pin contracts and actual
fresh/upgraded/cold TLS receipts were assessed against their assertions; they
do not cover CR-01. The reviewer independently executed only the bounded policy
reproduction above, not those entire suites.

Final uninterrupted backend/security qualification (expected3572 cases before
this repair's additional regressions), browser proof, exact seven-stage
same-archive recovery and owner/native200% acceptance remain pending. Planned
Plan16 runner/profile/path integration was not relabelled as a Plan15 defect.
No push, merge or deployment authorization follows from this review.
