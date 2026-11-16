---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "04"
subsystem: database
tags: [postgresql, alembic, preservation, immutable-evidence, authorization, resumability]
requires:
  - phase: 12-01
    provides: authenticated disposable migrator and independent legacy snapshots
  - phase: 12-03
    provides: reviewed final ownership, global digest marker and terminal model contracts
provides:
  - Real migration-only0015 expansion with authenticated finite owned-row association guard
  - Bounded causal0016 association with durable per-row checkpoints and fail-closed lineage checks
  - Populated retained-origin preservation, immutable global split and actual interruption/resume proof
affects: [12-05, 12-06, 12-07, 12-16, 12-17, 12-18, 12-27]
tech-stack:
  added: []
  patterns: [session_user finite association, concurrent owned-root candidate key, committed bounded backfill]
key-files:
  created:
    - backend/alembic/versions/0015_portfolio_expansion.py
    - backend/alembic/versions/0016_portfolio_association.py
  modified:
    - backend/tests/test_portfolio_migrations.py
    - backend/tests/test_migrations.py
key-decisions:
  - Keep unique accounts.user_id until0017; associate only the seven reviewed owned tables
  - Non-NULL association is the immutable durable per-row checkpoint; no progress table or runtime GUC
  - Keep global applications unassociated with untouched legacy NULL markers and exact digest bytes
  - Refuse both stage downgrades before writes; intermediate schemas are not deployable runtime releases
requirements-completed: []
requirements-addressed: [PFUND-03, PSAFE-03]
duration: 14 min
completed: 2026-11-16
---

# Phase 12 Plan 04: Finite Immutable Legacy Association Migrations

**Authenticated, bounded migrations attach existing financial rows to their original portfolio without changing money, immutable payloads or global split interpretation.**

## Performance

- Started: 2026-11-16T08:29Z
- Verification complete: 2026-11-16T08:43Z
- Tasks: 2/2
- Files created/modified: 4
- Dependencies, providers and production operations: none

## Accomplishments

-0015 builds the accounts(id,user_id) candidate index concurrently with exact
  resumable-index validation, attaches its constraint, adds My portfolio/name
  and nullable closed_at, seven nullable portfolio associations, the nullable
  SMALLINT digest marker without a default, and the terminal closure table.
  Existing accounts.user_id uniqueness remains; no new account or money is
  created. New-table indexes are transactional; existing-table index work is
  concurrent. Additional final lineage indexes/constraints belong to0017.
- public.associate_legacy_portfolio_only() is migrator-owned, SECURITY INVOKER,
  pinned to pg_catalog,public,pg_temp and PUBLIC EXECUTE revoked. It authorizes
  only authenticated session_user=birja_migrator, a fixed owned-table list,
  NULL old association, the user's sole original root, and exact JSON equality
  of every other old column. Ordinary and SET ROLE sessions, economic/owner
  edits, foreign roots, reassociation, NULL resets and deletes are denied.
- Existing deferred stock-fill and dividend INSERT-link triggers remain intact.
  Only necessary BEFORE mutation triggers are replaced. Global split
  applications never gain portfolio_id or the finite association trigger;
  their marker/digests cannot be updated or deleted. Closure records also reject
  UPDATE/DELETE. No ordinary role receives a new write grant.
-0016 preflights authenticated identity, missing/ambiguous/mismatched roots and
  old causal owner/coin links. Fixed causal batches of at most500 rows update
  only portfolio_id. Each batch commits independently; its populated association
  is its durable checkpoint. Re-entry addresses only remaining NULL rows and
  verifies complete valid ownership afterward. Both downgrade functions refuse
  before any mutation;0016 requires online authenticated execution.
- Actual historical-source tests now seed crypto money/holding/fill rows on
  each0007–0014 source before upgrading, then add the full retained0014 stock,
  two-user global split and dividend books. Original IDs, timestamps, monetary
  values, JSON text and digests remain identical through0016 with no grant.
- A private child-interpreter fault injects interruption into actual Alembic
  after two committed one-row batches, proves their persistence with revision
  still0015, then reconnects normally and finishes with identical economics.
  No runtime fault hook, GUC or trigger bypass is introduced.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| 12-04-01 | dccc260 | Expansion, finite guard, marker/closure shape and real SQL negative proofs |
| 12-04-02 | 7e003f1 | Bounded association, historical-source preservation, actual interruption/resume and refusal tests |

## Verification

Existing installed environment only: UV_CACHE_DIR=/tmp/birja-uv-cache,
uv run --no-sync. Socket checks used scoped access to the guarded disposable
test stack. No packages were installed or upgraded.

| Check | Result |
|---|---|
| Initial expansion/association guard gate | 9 passed in43.63s |
| Initial preservation/resume/downgrade gate | 12 passed in81.94s |
| Combined expansion, guard, backfill, preservation, resume and downgrade gate | 22 passed,14 deselected in133.64s |
| Strengthened historical-source seeding cases after their change | 8 passed,28 deselected in55.53s |
| Migration file collection | 36 cases collected |
| Ruff check and format on four changed files | Passed |
| git diff --check | Passed |

The combined run includes genuine child-process interruption and economic-edit
negatives on every owned table. The final change only strengthens the eight
historical-source cases; all eight were rechecked. Connection-only0014 tests,
generic head/metadata-diff suites and full runtime tests were not represented as
green at this migration-only intermediate head. Final0017 remains unimplemented.
No primary requirement is marked complete from a staged migration alone.

## Deviations from Plan

- [Rule3 — Blocking fixture inventory] Added exactly
  portfolio_stock_closures and associate_legacy_portfolio_only() to the fixed
  disposable migration inventory in test_migrations.py. Unknown objects and
  unsafe role attributes remain rejected; production bootstrap is unchanged.
- [Rule2 — Missing immutable enforcement] Retained migration SQL did not install
  an unconditional global split mutation trigger (retained role policy used ACLs).
  Added a BEFORE UPDATE/DELETE trigger on global applications and closure rows
  using the existing unconditional reject_stock_dividend_mutation() function.
  It introduces no new function/grant or finite exception for global records.
- [Rule2 — Stronger preservation proof] Historical-origin cases previously
  reached0014 before seeding any economics. They now seed genuine original
  crypto rows before each source upgrade, retaining the full0014 stock book
  supplement. Planned0017 assertions are owned by07; these stage proofs stop
  at0016 rather than failing at a revision that does not yet exist.

Installed Alembic's autocommit_block documentation was read to verify that
entering/exiting the block commits batches and requires transaction_per_migration;
the existing env.py already configures that setting. The real interruption
proof establishes the behavior rather than relying only on that documentation.

## Known Pending Proofs and Next Plan Readiness

- These are migration-only states in a coordinated delivery. Do not run or
  deploy the app at0015/16.07 owns final0017, explicit runtime revision admission
  and first green final_sql matrix;16–18 own final bootstrap/recovery inventory
  and intermediate operational refusal. Existing backup revision allowlists
  still exclude0015/16. No intermediate runtime qualification is claimed here.
-05/06 define final immutable SQL authority.07 must restore unconditional
  owned-row rejection and drop associate_legacy_portfolio_only(), while preserving
  deferred/INSERT checks and the global marker guard. Relevant trigger names:
  stock_record_immutable on trades/facts/movements; stock_dividend_immutable on
  payments/decisions; portfolio_association_only on holdings/entitlements;
  portfolio_record_immutable on global applications and closure records.
- Final0017 adds required portfolio NOT NULL/FKs/uniqueness and removes only the
  old one-root constraints in concert with coherent services. Extend the exact
  test inventory for its reviewed routines. Preserve retained0014 fixtures and
  source-specific admission rather than replacing them with final ORM seeding.
- Actual SQL role/TLS, root-aware services, exact cold restore, strict full
  coverage/security/images and owner UI/native200% remain future gates. All28
  milestone requirements remain unchecked. Phase7 live deferrals and stock
  admissions are unchanged; no provider, package, publication, branch or
  production action occurred. Unrelated .claude/ remains untouched.

## Self-Check: PASSED

Both new migrations and the two modified test files exist. Task commitsdccc260
and7e003f1 exist on feature/milestone-v1.2. Both task-specific contracts passed
with actual isolated PostgreSQL and no skips/xfails/manual final-schema DDL.
No product stub or tracked deletion was introduced.
