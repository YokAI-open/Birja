---
phase: 10-dividend-cash-and-event-history
plan: "01"
subsystem: database
tags: [postgresql, alembic, dividend, immutability, composite-foreign-keys]
requires:
  - phase: 08-corporate-action-safe-ownership
    provides: retained event/revision/owner-entitlement identities
  - phase: 09-whole-share-trading-and-combined-portfolio
    provides: reviewed0013 execution schema and owned test stack
provides:
  - Typed immutable dividend originals and append-only decisions in additive0014
  - Exact owner/event/revision/fingerprint/entitlement composite foreign keys
  - NULL-safe held-status deduplication without consuming successful target identity
  - Empty-only downgrade and minimal read-only application grants
affects: [10-02, 10-04, 10-05, 10-06, 10-07, 10-10]
tech-stack:
  added: []
  patterns: [immutable-original, append-only-decisions, null-safe-held-dedup, concurrent-index-recovery]
key-files:
  created:
    - backend/app/models/dividend.py
    - backend/alembic/versions/0014_dividend_accounting.py
    - backend/tests/test_dividend_schema.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/models/corporate_action.py
    - backend/tests/test_migrations.py
    - backend/tests/test_stock_action_migrations.py
    - backend/tests/test_stock_execution_migrations.py
key-decisions:
  - Existing revision and entitlement composite UNIQUE identities are added only in0014; predecessor migrations and retained rows remain unchanged.
  - Uncertain decisions require an existing payment and unknown verified amounts; polling times and cash are excluded from stable held deduplication.
  - Runtime INSERT is absent; the later reviewed narrow SQL authority owns financial publication.
requirements-completed: []
requirements-supported: [DIV-03, DIV-04, DIV-05]
duration: approximately14min
completed: 2026-11-12
---

# Phase 10 Plan 01: Retained Dividend Accounting Summary

**Additive0014 binds immutable originals and correction/hold decisions to exact retained identities, with zero targets, NULL-safe deduplication and safe downgrade refusal.**

## Performance

- Tasks:2/2; implementation/test files:8, plus this summary.
- Approximate session duration14minutes; exact observed task-commit interval
  18:57:59–19:07:14UTC on2026-11-12 is9m15s, excluding initial reads/setup.
- Focused new schema suite:30tests; final affected migration suite:112tests16.43s.
- No dependency installation, lockfile change, provider request, production/B2/
  timer/installed-tool action or publication.

## Accomplishments

- `StockDividendPayment` is unique per economic event/owner and retains saved
  symbol/name, cutoff/rule/units, exact quantity/rate, dates, initial rounded
  amount and historical cash-after. Zero is accepted; negative, nonfinite,
  overflowing and noncent original amounts are rejected by real PostgreSQL.
- Composite foreign keys bind event/coin, revision/fingerprint and entitlement/
  owner/event/revision/fingerprint. Individually valid other-owner, other-event
  and other-revision IDs cannot be cross-linked. New retained identity UNIQUE
  constraints preserve all predecessor rows without backfill or mutation.
- Decisions retain current revision, optional uncertain entitlement, saved terms,
  desired/cumulative/proposed/applied amounts, fixed outcome/reason and owner-bound
  predecessor/application links. Uncertainty forbids invented target/terms;
  no-anchor uncertainty fails its FK. A held decision can have a separate applied
  successor; successful-target uniqueness prevents duplicate application, while
  NULLS NOT DISTINCT held identity ignores polling timestamps and cash balance.
- UPDATE/DELETE triggers protect originals/decisions even for table-owner direct
  SQL. A decision application reference must point to a successful predecessor,
  not a held proposal. This trigger helper also belongs in later exact recovery
  identity validation: `public.reject_stock_dividend_mutation()` is invoker with
  fixed `search_path=pg_catalog,public,pg_temp`, PUBLIC EXECUTE revoked.
- New tables/sequences grant no runtime INSERT/UPDATE/DELETE or scheduler cash
  privilege. The migration grants application SELECT only when that role exists.
  Later plan02 adds the deliberate scheduler-only definer boundary and actual
  fresh/upgraded bootstrap/configuration parity; no payout function exists yet.
- All actual query/FK indexes are frozen here, including payment/decision owner
  chronology, target/hold dedup, predecessor references, entitlement work and split
  owner chronology. Existing-table indexes build CONCURRENTLY, validating exact
  owner/definition/state before reuse of interrupted builds, matching the reviewed
  predecessor pattern; unrelated same-name objects are refused.
- Downgrade checks both new financial tables before any DDL. Empty downgrade
  removes only0014 objects. Actual populated0013 entitlement bytes remain equal
  after upgrade, empty downgrade and repeated upgrade. No predecessor migration
  file changed.

## Task Commits and TDD Gates

1. Task1 RED `6333c5c`: migrated PostgreSQL lacked both durable relations;
   actual assertion failed, without import/collection errors.
2. Task1 GREEN `623f6b3`: typed models, generated/reviewed0014, constrained
   identities, indexes and immutable accounting;15tests pass1.05s.
3. Task2 RED `84492e9`: actual populated downgrade incorrectly succeeded in a
   rollback-owned transaction; expected populated guard exception was absent.
4. Task2 GREEN `18990a4`: safe guard, narrow grants, decision lineage, nullable
   uncertainty/dedup and historical migration compatibility;112tests pass16.43s.

Both behavioral tasks have actual RED followed by GREEN commits. No successful
financial effect is mocked. These schema tests use synthetic direct owner inserts
to test storage, and do not claim to authorize payment from uncertain provider
terms; plan02 owns genuine economic authority and cash publication.

## Verification Executed

Commands used existing `uv run --no-sync --no-cache`, with no package sync/install.
All PostgreSQL/Redis access used the owned `docker-compose.test.yml` project
`birja-test`, loopback55432/56379, tmpfs and test-only credentials.

| Gate | Actual result / evidence |
|---|---|
| Actual0013→autogenerate0014 | PASS; `/tmp/birja-phase10-01-autogenerate.log` |
| Task1 behavior RED |1failed/14deselected1.00s; `/tmp/birja-phase10-01-red.log` |
| Task1 schema GREEN |15passed1.05s; `/tmp/birja-phase10-01-task1-green.log` |
| Task2 populated downgrade RED |1failed/21deselected0.88s; `/tmp/birja-phase10-01-task2-red.log` |
| Intermediate new schema GREEN |29passed1.96s before adding independently valid cross-link regression; `/tmp/birja-phase10-01-task2-green.log` |
| Final schema + predecessor migrations |112passed16.43s, including all30new schema cases; `/tmp/birja-phase10-01-affected.log` |
| Scoped Ruff |PASS, all8implementation/test/migration files |
| Scoped Ruff format |PASS, all8files |
| Scoped Mypy |PASS,3model/registration sources |
| Actual metadata/migration parity |PASS, Alembic compare_metadata returns no differences |
| Actual restricted direct SQL |App SELECT succeeds; app/scheduler12INSERT/UPDATE/DELETE attempts return42501 |
| Final schema/data cleanup |0014; payments0, decisions0, entitlements0 |
| Whitespace/deletion review |git diff --check PASS; no tracked file deletions |

The autogenerated draft was read and explicitly corrected: referenced composite
UNIQUE constraints now precede child FKs, existing indexes are concurrent with
exact retry validation, omitted trigger/grant/downgrade logic is explicit, and
drop ordering removes child tables before referenced predecessor constraints.
Official version-specific references consulted:
[PostgreSQL18 constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)
and [SQLAlchemy2.0 PostgreSQL dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html).

Root owns the full financial-wave backend/critical coverage gate after other
Wave1 plans. It has not run in this executor, and no full-phase/image/recovery/
TLS/browser/owner acceptance pass is claimed here.

## Deviations from Plan

1. **[Rule2 — Exact identity metadata parity]** Parent explicitly extended
   ownership to `models/corporate_action.py`: new referenced composite UNIQUE
   keys and current-work/split chronology metadata are necessary for exact C01
   FKs and autogenerate parity. All DDL is additive0014. Verified by actual valid
   cross-link refusals, metadata equality and unchanged predecessor entitlement;
   committed `623f6b3`.
2. **[Rule3 — Historical test compatibility]** The actual broader run first
   passed66tests then met a hardcoded0013 current-head assertion; after correcting
   true head expectations,71passed before the old bootstrap deliberately rejected
   unsupported0014. Parent authorized narrow test ownership expansion. True
   current-head checks use EXPECTED_HEAD0014; the historical runtime/bootstrap
   fixture explicitly runs its intended0013 then restores head after cleanup.
   No old grant/constraint assertion is weakened and bootstrap remains unchanged
   for plan02. Final112tests pass; committed `18990a4`.

## Issues Encountered

- Sandbox denied initial Docker socket access; scoped approved escalation started
  only the owned disposable test stack and enabled test-network/Git operations.
- Reused0014 test DB initially retained the prior trigger definition after local
  migration editing. An explicit empty0014→0013→0014 refresh applied the revised
  draft. One FK test also initially hit held-status uniqueness first; a distinct
  synthetic status identity isolates the intended FK behavior. Both were fixed;
  no failure remains.
- No authentication gate occurred. No full requirement is marked complete from
  schema infrastructure alone. Root remains sole writer of canonical STATE/
  ROADMAP/REQUIREMENTS and preserves the unrelated `.claude/` directory.

## Threat Results and Stub Scan

- T-10-01-01: scoped storage boundary CLOSED by exact FKs/checks, immutability and
  actual42501runtime denials; economic definer authority remains02 as planned.
- T-10-01-02: CLOSED for this plan by saved immutable originals, linked exact
  owner/event terms and byte-equal predecessor evidence; no source identity
  fabricated as live evidence.
- T-10-01-03: CLOSED for this plan by concrete bounded query indexes, bounded
  stored strings/numeric fields and owned rollback-cleaned SQL tests; no worker
  or external I/O was introduced.
- T-10-01-SC: CLOSED; zero dependency/image/install/lockfile change.
- No threat surface outside C01 was added. New trigger function is part of its
  planned immutable schema boundary and must be pinned by recovery plans04–06.
- No TODO/FIXME, financial success stub, placeholder UI or runtime consumer is
  present. Nullable uncertain fields are required unknown authority, not a stub.

## Next Plan Readiness

Ready for02 using exact0014 models and frozen indexes. It must implement both
reviewed definer functions, fresh/upgraded restricted-role identity, final
advancing authority checks and scheduler cash isolation before actual runtime
consumers. Retained/TLS/recovery gates04–06 still precede07/10. Live provider/data/
action permissions, publication, production and human acceptance remain deferred
under existing boundaries. Test stack remains running, empty at0014, for root.

## Self-Check: PASSED

All8owned implementation/test/migration files exist. All four RED/GREEN hashes
exist locally; no task commit deletes tracked files. Actual final112test gate,
model/migration equality, scoped checks and clean0014 tables passed. Canonical
state and unrelated `.claude/` edits were not staged or changed by this executor.
