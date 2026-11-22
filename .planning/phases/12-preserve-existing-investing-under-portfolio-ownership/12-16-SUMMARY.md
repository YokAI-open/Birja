---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "16"
subsystem: infra
tags: [postgresql, bootstrap, portfolio, migration, authorization, compatibility]
requires:
  - phase: 12-07
    provides: final0017 schema and private active-write authority
  - phase: 12-12
    provides: scheduler-only lock authority and terminal stock records
  - phase: 12-13
    provides: portfolio-bound entitlement and dividend consumers
provides:
  - Source-owned final0017 function/relation/marker/trigger and narrow-grant bootstrap
  - Authenticated source-pinned migration-to-final with explicit staged runtime refusal
  - Actual fresh, retained0014 and staged0015/16 dev bootstrap/resume proofs
  - Pre-checkout source/schema deployment refusal and stopped-writer finalization contract
affects: [12-15, 12-17, 12-18, 12-26, 12-27]
tech-stack:
  added: []
  patterns: [fixed bootstrap SQL identity, authenticated migration child, explicit upgrade admission]
key-files:
  created:
    - backend/app/db/portfolio_bootstrap.py
    - backend/app/db/portfolio_migrate.py
    - deploy/tests/test-portfolio-migration-runner.py
  modified:
    - backend/app/db/dev_bootstrap.py
    - deploy/db/bootstrap-roles.sql
    - deploy/configure-db.sh
    - deploy/deploy.sh
    - deploy/tests/test-dev-bootstrap.py
    - docker-compose.yml
    - docker-compose.override.yml
key-decisions:
  - Authenticate the dev child as birja_migrator with an ephemeral password; retain the parent identity and disable the role after the child
  - Keep normal bootstrap at0015/16 explicitly migration_only; only the pinned restricted runner can reach0017 before final grants
  - Preserve scheduler lock-only authority without account cash UPDATE or lifecycle privileges
  - Separate an explicit forward portfolio-upgrade admission from runtime/rollback source admission
requirements-completed: []
requirements-addressed: [PSAFE-03, PFUND-03]
duration: 28 min
completed: 2026-11-16
---

# Phase 12 Plan 16: Restricted Bootstrap and Resumable Finalization

**Fixed0017 authority and authenticated migration-to-final keep intermediate schemas closed while fresh and upgraded local investing prerequisites remain reachable.**

## Accomplishments

- The final bootstrap preflight authenticates nine changed/private routine
  bodies and declaration properties against fixed source hashes, expected
  migration ownership, search paths and bounded EXECUTE ACLs. It validates
  all27 relation owners, seven required-root columns, the nullable/no-default
  SMALLINT marker and its exact CHECK, global split trigger identity and final
  active-write trigger inventory. The finite association helper must be absent.
- Production SQL mirrors the source-owned contract while retaining its explicit
  historical revision branches. Normal0015/16 bootstrap returns migration_only.
  Final app cash and holding quantity/basis UPDATE grants are column-limited;
  name, baseline, owner and closure writes remain denied. Scheduler accounts
  UPDATE remains denied; lock_stock_portfolio_roots(bigint) remains scheduler
  EXECUTE only, and check_portfolio_financial_write() remains trigger-only.
  Revision metadata is readable but not runtime-writable.
- Local dev startup provisions only guarded local roles and transfers only a
  fixed relation/signature allowlist. Its migration child authenticates as the
  actual birja_migrator, with an in-memory random password and child-only URL.
  Parent settings/identity remain unchanged; the login and password are disabled
  after the child. Current Compose commands invoke this explicit lane instead
  of attempting authenticated0015 with an administrative session.
- portfolio_migrate.py pins the three portfolio migrations and both SQL assets
  before connection. It requires the exact Compose endpoint/database/migrator,
  actual session identity, safe schema/runtime-role attributes and memberships,
  fixed object ownership/signatures and one allowed revision. Prod connections
  use the shared verified-TLS context. Only dev permits an empty initial schema.
  The runner serializes finalization, invokes actual Alembic0017 and validates
  the final contract before reporting success. Child diagnostics are redacted.
- configure-db.sh has an explicit production-only resume operation,
  --resume-portfolio-migration --approved-operation portfolio-migration-to-final.
  It checks stopped backend/scheduler writers, then runs the authenticated
  source-pinned migration service before ordinary bootstrap. Recovery-only
  synthetic Compose has no migration service and intentionally refuses this
  operation; actual staged tests use exclusively owned dev Compose.
- Deployment source admission distinguishes a reviewed forward upgrade from
  runtime/rollback compatibility. New deploys require the exact tested source
  and pinned0017 blob before checkout/writes; old code cannot be selected and
  then paired with a newly migrated schema. Runtime rollback refuses current
  portfolio code against old schema and old code against0017. Writers stop
  before migration and restart only on the final-schema path.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| 12-16-01 | 4df970a | Fixed final authority, exact grants and authenticated dev startup/roles proof |
| 12-16-02 | a4f62a1 | Explicit migration resume, pre-write schema/source/role refusal and staged proofs |

## Verification

No dependency install, image build, provider operation, production access or
publication occurred. Existing cached runtime e5c153f was used with current
read-only app/Alembic source mounts. These are source/bootstrap proofs, not a
qualification of a rebuilt image. Every Compose project was uniquely named,
checked absent before creation and fully removed with owned volumes afterward.

| Check | Result |
|---|---|
| python3 deploy/tests/test-dev-bootstrap.py | PASS, actual fresh and populated0014→0017 lanes (19.034s/22.392s) |
| python3 deploy/tests/test-portfolio-migration-runner.py | PASS, five source/identity/command/refusal contracts plus actual durable0015/16→0017 lanes (26.452s/27.028s) |
| Final pre-checkout runtime versus upgrade-admission contracts | 5/5 PASS after the final admission refinement |
| Focused mypy for all three changed/new DB modules | PASS |
| Ruff check/format, three DB modules | PASS |
| Bash syntax and embedded configure Python AST | PASS |
| git diff --check | PASS |

The actual role proof executes both the dev final contract and production SQL
bootstrap. It preserves retained cash321.12/baseline8765, creates a synthetic
cash123.45/baseline7777 root, proves only its justified cash UPDATE to124.45,
then repeats bootstrap with unchanged rows. It checks denied lifecycle/baseline
privileges, scheduler cash denial, private trigger execution and closure DML.
Real restricted connections reject unsafe schema CREATE, unsafe runtime roles,
unsupported revision and an unreviewed routine overload before financial writes.
Unsafe role attributes, membership and relation-owner negatives refuse repair.

Staged tests commit actual Alembic0015/16, stop before finalization, verify both
ordinary dev and production SQL bootstrap refusal with unchanged finances, and
deny SET ROLE as a substitute for authenticated migration identity. A fresh
normal command resumes through0017, applies final bootstrap and preserves the
same cash/baseline. Source substitution and unsafe endpoint/caller tests refuse
before connection; legacy deployment tests refuse before checkout/install.
No help-only output, manually fabricated final schema, skip or xfail substitutes
for these proofs.

## Deviations from Plan

1. **[Rules2/3 — Required authenticated dev startup]** Existing Compose ran
   Alembic as the admin, which cannot satisfy0015's session_user predicate.
   Added the bounded dev child and changed both Compose commands. The two new
   DB modules hold shared fixed contracts and the source-pinned runner rather
   than duplicating unrelated auth or introducing infrastructure.
2. **[Rule1 — Missing preflight enforcement]** The first actual unsafe-owner
   negative exposed a missing relation-ownership check in the final dev path.
   Added the exact27-table preflight before grants and reran both fresh and
   upgraded proofs. Exact function signatures, not just names, bound transfer
   and runner inventories; overload substitution is rejected.
3. **[Rule2 — Safe finalization entry]** Explicit resume now requires stopped
   financial writers and reviewed new source. A retained old source cannot
   pass ordinary old-schema admission and then inherit an automatic0017
   upgrade. Runtime/rollback and forward-upgrade admission are distinct.
4. **[Rule3 — Updated dev proof]** The old dev financial fixture called
   user-only services and assumed schema0014. Replaced it with source-mounted
   actual final-role/bootstrap/preservation and staged-runner proofs. Existing
   domain accounting proofs remain in the earlier plan summaries and final27
   integrated campaign; this script does not claim those full journeys.

## Threat Flags

| Flag | File | Description |
|---|---|---|
| threat_flag: migration_child | backend/app/db/portfolio_migrate.py | Explicit privileged operation; preserve source hashes, actual-role/schema guard, timeout/lock and redacted diagnostics in retained packaging/qualification |
| threat_flag: dev_role_setup | backend/app/db/dev_bootstrap.py | Exact local endpoint/admin/object guard and ephemeral child login; never use for production provisioning |

## Known Stubs

None in the assigned bootstrap/runner contract. Production execution and
verified-TLS cold qualification are deliberately not represented by local dev
or command tests.

## Carry Forward

- Plan17 must include portfolio_bootstrap.py and portfolio_migrate.py and the
  updated dev bootstrap/Compose commands where retained producer/consumer
  packaging needs them. Preserve the fixed migration/SQL hashes and the exact
  source/schema upgrade-versus-runtime admission contract.
- Both existing private helpers remain exact migration-owned functions:
  check_portfolio_financial_write() is trigger-only; the scheduler-only
  lock_stock_portfolio_roots(bigint) acquires instrument then ordered root locks
  without economic mutation. Their body/config/owner/ACL/trigger inventories
  must agree in the recovery manifests and actual restored roles.
- Plan18/27 must qualify the actual retained production-like resume command,
  role application and current/retained same-archive TLS/restore/rollback with
  one source-bound rebuilt image set. This plan did not invoke --production,
  read private host configuration or run a live deployment.
- Full backend/browser coverage, strict audits/five rebuilt image scans, cold
  recovery and owner UI/native200% acceptance remain pending. Current new DB
  authorization modules must be included in the final critical proof inventory.
  All28 milestone requirements remain unchecked; Phase7 live gaps/gates stay
  untouched. Everything is local on feature/milestone-v1.2.

## Self-Check: PASSED

Both task commits and all ten task/deviation files exist. Required commands and
focused checks pass; no tracked deletion or dependency change occurred.
Unrelated .claude/ remains untouched.
