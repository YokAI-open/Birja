---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "01"
subsystem: testing
tags: [postgresql, migrations, ownership, preservation, authorization]
requires:
  - phase: 11
    provides: retained schema0014 and isolated migration test infrastructure
provides:
  - Authenticated restricted disposable migration child process with unchanged parent identity
  - Independent legacy economic snapshots and a real two-user global split fixture
  - Staged preservation/refusal/resume tests and final root-isolation scenario matrix
affects: [12-02, 12-03, 12-04, 12-07, 12-08, 12-10, 12-12, 12-13, 12-27]
tech-stack:
  added: []
  patterns: [guarded child-only migration DSN, independent exact legacy snapshots]
key-files:
  created:
    - backend/tests/portfolio_fixtures.py
    - backend/tests/test_portfolio_migrations.py
    - backend/tests/test_portfolio_ownership.py
    - backend/tests/test_portfolio_authority.py
  modified:
    - backend/tests/conftest.py
    - backend/tests/test_migrations.py
    - backend/tests/test_stock_migrations.py
key-decisions:
  - Keep migration credentials only in memory and the disposable database; authenticate child processes rather than SET ROLE
  - Keep future feature assertions unskipped and pending; collection is not economic feature verification
requirements-completed: []
requirements-addressed: [PFUND-03, PFIN-03, PSAFE-03]
duration: 17 min
completed: 2026-11-16
---

# Phase 12 Plan 01: Ownership Proof Oracles and Fixture Contracts

**Real restricted migration authentication and exact synthetic legacy snapshots establish the tests for the portfolio transition without inventing a passing final schema.**

## Performance

- Phase dispatch: 2026-11-16T07:56:48Z
- Closeout: 2026-11-16T08:13Z
- Tasks: 2/2
- Application/source packages changed: none
- Test files created/modified: 7

## Accomplishments

- Guarded exact localhost/birja_test administration provisions a LOGIN,
  NOINHERIT and otherwise restricted birja_migrator with a random in-memory
  password. Membership and dangerous attributes are rejected. A fixed inventory
  bounds schema/table/sequence/function ownership transfers; production setup
  and application migration bodies are unchanged.
- Every online caller in the assigned migration families and conftest.migrated
  now runs Alembic in a fresh authenticated child interpreter. Parent Settings,
  environment and application engine retain birja_test. Offline rendering is
  unchanged. Structured child errors preserve DBAPIError and SQLSTATE assertions.
- Synthetic legacy books include unequal actual cash/baselines, crypto/stock
  holdings, original fills/keys, one global split with two user movements,
  earned unpaid entitlements, a payment and a held correction. Snapshots retain
  original column values, IDs, timestamps, JSON text and digest bytes.
- Staged tests cover retained0007–0014 source paths through0015/16/17,
  authenticated finite association, ordinary/SET ROLE/forged-owner refusal,
  committed partial association and resumable re-entry.
- Thirteen additional collected cases cover zero/one/two active roots, a closed
  root, foreign owner, sibling balances/holdings, cross-root retry uniqueness,
  original lookup, explicit resolver outcomes and restricted SQL authorities.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| 12-01-01 | 06c05df | Guarded migration lane, legacy fixtures and migration proofs |
| 12-01-02 | 4c3f5f6 | Root isolation and authority matrix |

## Verification

All commands used the existing locked environment (`UV_CACHE_DIR=/tmp/birja-uv-cache
uv run --no-sync`); no dependency installation or lock change occurred.

| Check | Result |
|---|---|
| test_portfolio_migrations.py -q -k migrator_connection | 14 passed, 9 deselected |
| test_portfolio_migrations.py --collect-only -q | 23 collected |
| test_migrations.py + test_stock_migrations.py | 37 passed in43.63s |
| test_portfolio_ownership.py + test_portfolio_authority.py --collect-only -q | 13 collected |
| Ruff check/format on changed test files | Passed |
| git diff --check | Passed |
| Explicit preservation RED probe at legacy0014 | Failed exactly at missing revision0015; valid legacy seed and isolated teardown completed |

The final SQL/ownership assertions have **not** passed:0015–0017 and the resolver
do not exist yet. There are no skipped/xfail/always-green feature substitutes.
No primary milestone requirement is marked complete by fixture creation.

## Deviations from Plan

- [Rule3 — Blocking infrastructure] The default UV cache is read-only under
  the current sandbox. Use the temporary cache with --no-sync and the already
  installed environment. Local socket tests require sandbox escalation.
- [Rule2 — Preserve verification semantics] Child migration errors carry their
  original database category/SQLSTATE across the process boundary so existing
  retained downgrade/refusal tests remain meaningful.
- [Rule3 — Isolated fixture lifecycle] Populated immutable ledgers cannot be
  SQL-deleted or downgraded. Staged fixtures discard only the exact guarded
  disposable public schema in teardown and restore it through genuine Alembic;
  no final schema is simulated with hand-written test DDL or create_all.

## Known Pending Proofs and Next Plan Readiness

- 12-02/03 extend metadata and lineage scenarios;12-04 owns staged migration
  success/refusal/resume;12-07 owns the first required green final SQL run;
  12-08 and domain plans extend resolver/retry/worker proofs. Runtime authority
  tests intentionally require the real restricted roles, never fabricated ACLs.
- The fixed test migration inventory must be extended explicitly when later
  migrations introduce their reviewed objects; unknown objects fail closed.
- Retained0014 oracle seeding currently uses existing dividend schema helpers.
  Later model changes must preserve explicit retained-schema seed compatibility
  rather than leaking new ORM columns into an old-schema fixture.
- The connection proof currently targets0014; final-head qualification must
  retain this isolated retained lane and update current-head admission tests.
- Earned-unpaid terminal worker effects, complete original-receipt execution,
  final SQL/TLS/security/image/recovery gates and owner UI/native200% remain
  future execution obligations. These fixtures are not their result receipts.
- Phase7 deferred live outcomes and disabled admissions remain untouched.
  No provider, production, package, publication or branch operation occurred.

## Self-Check: PASSED

All seven assigned test files exist; task commits06c05df and4c3f5f6 exist on
feature/milestone-v1.2; both task-specific verification contracts passed with
their explicit collection-only limits. No runtime/product stub was introduced.
