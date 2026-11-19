---
phase: 14-end-strategies-safely
plan: "04"
subsystem: database-authority
tags: [postgresql, bootstrap, admission, migrations, least-privilege]
requires:
  - phase: 14-03
    provides: Complete closure proof and final successor clock guards
provides:
  - Exact0023 runtime admission with independent SQL and Python bootstrap parity
  - Finite authenticated forward migration and migration-only0021/22 inventories
  - Effective private default privileges and bounded no-ACL quarantine entry
  - Repeated current test-bootstrap and real closed-evidence preservation proof
affects: [14-05, 14-06, 14-07, 14-15, 14-16, 14-18]
tech-stack:
  added: []
  patterns:
    - Independently versioned successor catalogue and object/default ACL contracts
    - Empty non-owner ACL permits authenticated regrant but never runtime admission
key-files:
  created:
    - backend/tests/test_portfolio_closure_admission.py
  modified:
    - backend/app/db/portfolio_bootstrap.py
    - backend/app/db/schema_contract.py
    - backend/app/db/portfolio_migrate.py
    - backend/app/db/dev_bootstrap.py
    - backend/tests/test_portfolio_management_grants.py
    - backend/tests/test_portfolio_migrate.py
    - backend/tests/test_migrations.py
    - deploy/db/bootstrap-roles.sql
key-decisions:
  - Qualified0017/0020 constants and SQL branches remain unchanged; current consumers explicitly select0023 exports.
  - Effective default privileges include implicit PUBLIC EXECUTE when a global function-default row is absent.
  - A source-owned empty-ACL quarantine state is bootstrap-only; runtime requires exact final object and default ACLs.
requirements-completed: []
requirements-progress: [PMGT-04, PSAFE-01, PFIN-06]
duration: 45min measured first-RED-to-cleanup-receipt interval
completed: 2026-11-19
---

# Phase 14 Plan 04: Exact Successor Admission and Forward Migration

**Only the complete31-table/24-identity/21-routine0023 authority is admitted;
both bootstrap implementations preserve finances and agree on object and
effective future privileges.**

## Task commits and performance

| Task | RED | GREEN | Result |
|---|---|---|---|
|1 — successor identity/grants|b1732e4|e2fa0ba|Real missing-profile RED5.00s; new admission matrix and75retained management checks qualified below|
|2 — authenticated forward path/reentry|dcf2684|a2ed33c|Missing successor source-pin RED; final85affected cases342.99s plus4stateful cases24.62s|

First RED was2026-11-19T09:51:46UTC. The cleanup/evidence receipt was recorded
at10:36:52UTC. This measured45-minute interval includes implementation,
fixture corrections and serial integration groups; it is not a short-feedback
latency claim. Parent-owned STATE/ROADMAP and whole requirements remain pending.

## Implemented authority

- Added independent0023 catalogue, initial/final object ACL and effective-default
  privilege contracts. Qualified0017/0020 literals and their production SQL
  identity/grant branches are byte-equal to the fixed sources. No Alembic asset
  changed, including0021–23. The new projection includes rules, policies and
  unexpected relation kinds, in addition to the existing complete relation,
  column, routine, constraint, trigger, index and identity definitions.
- Both source-owned bootstrap paths check role attributes/memberships, trusted
  database/schema ownership, exact catalogue and permitted entry ACL states
  before grants. Added lifecycle/root/intent linkage, frozen confirmation-name
  coherence, historical-stock boundary presence and global sequence/unit checks.
  Full financial reconstruction remains the service/recovery proof obligation;
  a bootstrap hash alone does not certify every retained fill.
- App receives the exact closure EXECUTE signature and required read access;
  scheduler/PUBLIC cannot execute it. No general lifecycle/intent/stock-closure
  mutation or new identity allocation is granted to runtime roles. Existing
  management funding/trading privileges remain bounded.
- Future default privileges are private in both implementations. Normalization
  distinguishes an absent global function-default row (implicit PUBLIC EXECUTE)
  from an absent schema-local row (no extra grants). Current runtime rejects
  the implicit-public state even when all current object ACLs are otherwise
  correct. PostgreSQL-empty ACL arrays are handled through unnest before
  aclexplode, without replacing them with fabricated privileges.
- The explicit empty non-owner ACL hash is a finite quarantine entry for a
  trusted exact-catalogue restore. It allows regrant, never app startup: current
  admission separately requires the final object/default ACLs. This was tested
  as a privilege-quarantine fixture, not misrepresented as encrypted recovery.
- Current runtime accepts0023;0021/22 remain migration-only. Forward migration
  authenticates exact new asset hashes and finite revision-indexed inventories.
  Older constants stay available unchanged; new intermediate/current profiles
  reject missing/extra relations, sequences, signatures and unsafe owners.
  Operator LOGIN/membership is refused before forward finalization.
- Current test grants and developer finalization select the exact successor
  profile. Two independent pytest invocations prove the session-autouse owner
  prerequisite and regrant work when the prior process leaves0023 installed.
  Current-head ORM/schema parity passes without model or migration alteration.

## Actual verification and limits

Raw receipts and logs: `/tmp/birja-phase14-plan04/receipt.json` and adjacent
files. Actual runtime source commit: `a2ed33c1756b1d36ad24909b46348cc5c2584784`.

| Check | Actual result |
|---|---|
|Task1 initial parity|2fresh/upgraded SQL/Python cases pass11.79s|
|Task1 focused permission/parity|7cases pass33.11s|
|New admission matrix before old fixture correction|41new cases pass within the mixed run; that invocation then fails the old17-routine expectation; no whole mixed-run pass claimed|
|Complete updated management regressions|75cases pass438.83s, before Task2 effective-default strengthening|
|Task2 source/authenticated migration/child cleanup subset|9cases pass9.08s|
|Bounded current head/model prerequisite|3cases pass2.67s|
|Independent admission/reentry invocation1|14cases pass71.35s|
|Independent admission/reentry invocation2|14cases pass71.90s, starting after the preceding process left0023|
|Final affected frozen-source run|85cases pass342.99s: all32migrator/orchestration plus53admission cases|
|Subsequent test-only stateful strengthening|4cases pass24.62s: actual closed records through both bootstraps/corruption refusal and populated downgrade refusal|
|Static checks|All8touched Python files pass Ruff/format; all4DB source modules pass mypy|
|Historical/qualified byte checks|All Alembic bytes unchanged fromc7e7f36; fixed0017/0020 Python literals and SQL identity/grant blocks unchanged|
|Owned cleanup|`birja-p14-04` containers, networks and volumes removed; project-label queries empty|

The final85-case run preserved all9captured source/test/SQL hashes. Its receipt
capture happened early in the run after correcting a receipt-only cwd prefix;
no implementation or test bytes changed between launch and capture. The later
four-case strengthening changes only the admission test file; runtime bytes
remain identical. Its results are separate, not relabelled into the85-case run.
One retained runpy module-entrypoint warning is recorded, with no suppression.
No full security/image/browser/TLS/encrypted-recovery qualification is claimed.

## Deviations and concrete repairs

1. **Rule3 — current-grant prerequisite:** Moved the small
   install_current_test_grants selection into Task1 so current fixture teardown
   did not continue requesting0020 while testing0023. Broader fixture adaptation
   remains Plan15; no autouse validation was skipped.
2. **Rule3 — retained fixture expectations:** Updated the existing current grant
   tests to0023 and21exact routines, preserving their retained0017 equality
   check. A negative test initially repeated an existing SECURITY DEFINER
   setting; it now requests real SECURITY INVOKER drift. Trigger helper EXECUTE
   denial is measured through PostgreSQL privileges instead of attempting an
   uncallable trigger-returning expression through asyncpg.
3. **Rule2 — complete default/quarantine contract:** Added private future-default
   resets and effective-default checking to ensure SQL/Python semantic parity;
   included a finite empty-ACL entry so later no-ACL restore/regrant is possible
   without permitting arbitrary authority drift or partial runtime startup.
   This is the planned authority/recovery requirement, not new product scope.
4. **Rule1 — empty ACL decoding:** Real PostgreSQL refused aclexplode on a
   zero-dimensional empty array. Unnesting entries before explosion preserves
   correct no-additional-grant semantics and passes implicit-public negatives.
5. **Test-only closed fixture correction:** Initialization and deletion were
   initially placed in one transaction, conflicting with the existing deferred
   terminal-root invariant. The fixture now commits initialization before the
   distinct closure transaction, matching actual separate requests. No guard
   was disabled to make normal initialization/deletion pass.

## Handoff

- Use `PREFLIGHT_0023_SQL`, `GRANTS_0023_SQL`, `CATALOGUE_0023_SQL` and the new
  final object/default hashes for current recovery consumers. Generic
  PREFLIGHT_SQL/GRANTS_SQL and the old catalogue/ACL exports deliberately remain
  qualified0020; do not reinterpret those old names as current.
- New catalogue SHA is
  `3a7e0dbe6a908890a1e0e493aa025938b8f03dbd84cf5f799ea0a1895dc164ec`;
  final object ACL SHA is
  `71896f41a9310ada0af0961b78e78f5364654f1513c11bf9310c250ad545f748`.
  Empty non-owner quarantine and final effective-default digest is
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.
- Existing TABLES/FUNCTION_SIGNATURES literals in dev bootstrap remain legacy;
  `migration_objects(revision)` supplies the finite successor dispatch. Never
  use the old29-table literal as a31-table recovery inventory.
- Plans05/06 still own complete V3 producer/consumer/quarantine/cold source
  oracles and selected rollback/refusal. Plan15 still owns actual verified-TLS
  fresh/upgraded qualification and broader whole-suite retained fixtures.
- Plan16/18 must retain all61critical paths, qualify new authority paths,
  strict images and complete source-frozen security/seven-stage recovery.
  No Phase7 provider/live-activation prerequisite has changed.
- Keep Plan03's complete same-transaction closure proof and valid0021
  pre-backfill verifier path. These bootstrap checks do not replace them.

## Known Stubs and Threat Surface

No goal-blocking stub or unplanned endpoint/package/provider/production surface
was introduced. Strict schema/role/file trust boundaries implement the declared
threat model. No dependency/image change, publication, live activation or
production operation occurred. Issue35, older proof archives and unrelated
`.claude/` remain untouched. Independent review is still required before05.

## Self-Check: PASSED

All9source/test/SQL artifacts exist and all4task commits are present. The raw
receipt records source/log hashes and empty owned cleanup. Actual test runs,
their source boundaries and the test-only strengthening are distinguished.
No whole feature requirement is completed by this plan; parent owns tracking.
