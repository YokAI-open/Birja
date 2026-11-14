---
phase: 07-permitted-stock-discovery
plan: "04"
subsystem: database-operations
tags: [postgresql, verified-tls, least-privilege, exact-recovery, stock-discovery]
requires:
  - phase: 07-03
    provides: Revision-selected producer/consumer contracts for0007/0008/0009/0010
provides:
  - Exact successor bootstrap grants matching migration0009
  - Populated0008 restricted-role TLS upgrade without grant repair
  - Independent retained encrypted dump/retrieval/restore proof across all four revisions
affects: [07-05, 07-08, 07-13, 11-mixed-asset-recovery]
tech-stack:
  added: []
  patterns:
    - Hold real verified-TLS runtime connections across the migrator upgrade
    - Separate migration-owned ACL proof from fresh bootstrap parity
    - Compare controlled no-writer source and clone identity state exactly
key-files:
  created: []
  modified:
    - deploy/db/bootstrap-roles.sql
    - deploy/tests/ops-fixtures.py
    - deploy/tests/test-db-operations.sh
key-decisions:
  - Calendar authority SQL denial is proven here; genuine evaluator semantics and integrated persisted-role proof remain required in07-08/13.
  - Keep strict recovery schema validation while role-only manifests deliberately include an unrelated fixture relation.
  - Disable the already-proven legacy concurrent writer before exact successor sequence comparisons.
requirements-completed: []
requirements-supported: [SAFE-01]
duration: 25min
completed: 2026-11-10
---

# Phase 7 Plan 04: Restricted TLS and Exact Recovery Summary

**Actual restricted-role verified-TLS stock-schema upgrades and fresh retained encrypted restores preserve exact financial, discovery, evidence and identity state.**

## Performance and Task Commits

- Approximately25minutes including context loading, meaningful RED gates, fixture adaptation and actual isolated operations.
- Tasks:2/2. Three source/test files changed; existing test-db-config.sh needed no change.
- Task07-04-01 RED:`81573c7` — Specify successor role and TLS boundaries.
- Task07-04-01 GREEN:`121784f` — Mirror stock grants and prove verified TLS upgrade.
- Task07-04-02 RED:`42d8e52` — Require retained successor recovery rehearsal.
- Task07-04-02 GREEN:`5a2d72b` — Replay exact retained stock discovery recovery.

First RED passed migration-owned permissions but rejected fresh successor bootstrap at its legacy revision guard. Second RED completed the actual retained legacy round trip and then failed because no successor recovery had been exercised. Import/seed-harness failures were diagnosed separately and do not count as behavioral RED.

## Actual Role and TLS Proof

Bootstrap now explicitly accepts0009/0010, validates and transfers only the four reviewed new tables and their dependent identities, revokes old runtime/PUBLIC privileges, and mirrors migration0009 exactly. App receives stock-table SELECT only. Scheduler reads catalogue/admissions and receives SELECT/INSERT/UPDATE on quotes/sessions plus USAGE only on the session identity sequence. No admission-sequence access, broad default grant, financial write, new membership or ownership is introduced.

The fixture populates legacy financial state through actual historical application services, migrates to0008, and bootstraps before upgrading. In the verified-TLS lane, already-connected app and scheduler clients remain connected while the actual migrator upgrades0008→0010. Their immediate new-table reads, quote/session inserts/updates and generated session identity succeed **without post-upgrade bootstrap or grant repair**. Financial hashes compare unchanged. A separate newly created successor database tests fresh-bootstrap ownership and equivalent intended ACLs.

Real SQL tests check table privileges, sequence USAGE/SELECT/UPDATE, migrator ownership, absence of PUBLIC privileges and exactly eight derived session columns. App quote/session writes and both runtime roles' admission establishment/renewal/calendar-override/catalogue writes and admission-sequence use are refused. Attempts to update nonexistent review/override session fields return42703. Existing65 financial, DDL, role-assumption, unrelated-object, default-privilege and row-security denial cases remain. TLS wrong CA, hostname, missing CA and plaintext controls, certificate renewal and credential-mount isolation pass.

**Proof ordering:** independent reviewed correction`9881e0b` removes the original dependency cycle without waiving assertions. The real session_at evaluator is introduced in07-08; its generation mismatch/replacement/expiry cases and07-13's actual restricted-role persisted SQL integration remain required before activation or phase completion. This plan proves SQL ownership/denial and allowed derived writes; no fixture predicate substitutes for the runtime evaluator.

## Actual Retained Recovery Proof

Fresh archive SHA256:`155743d84c3ae2d7ed765dc21245d3050e73f15afd30ce90d0abc47cb969bc9a`,152,166,400bytes. It was verified and installed only into a disposable synthetic host. Installed launchers run with the feature checkout denied by Landlock; no live tool was replaced.

The installed tools perform encrypted local-restic backup, independent retrieval, actual pg_dump/pg_restore into a separate database and recovery-gate verification for0007,0008,0009 and0010. The successor fixture contains twenty stock identities/quotes with exact8-decimal prices and microsecond source/collection timestamps; nullable and synthetic verified provider identities; five closed/early-close/mismatched-generation derived sessions; four approved/denied/revoked evidence records, including expired review, official provenance, bounded date-specific override revisions, quotas, attribution and retained rights. Evidence is recovered exactly, never renewed or repaired.

All supported schemas compare full table hashes, financial totals, constraints, indexes, column/identity metadata and exact controlled source/clone sequence values. Calendar-generation corruption is refused; after restoring it, verification passes. Session/admission generated IDs advance to their exact next values without collisions. Existing legacy cash/FK/index/sequence, encrypted checksum/manifest, truncated dump and unavailable-repository negative controls remain.

Before and after each successor round trip, source canonical state, all identity values, private configuration hash, historical checkout/credentials/Compose fingerprints and actual source container/mount identities compare unchanged. The legacy concurrent-writer test remains separate: ON CONFLICT still consumes sequence values, so its deliberate injector is disabled before no-writer exact successor comparisons. Only fixture-owned clone/database/container/network/tmpfs resources are removed.

## Verification

- Exact task1 commands:`bash deploy/tests/test-db-operations.sh --roles` passed76.478s; `--tls` passed55.626s.
- Exact final task2 command:`bash deploy/tests/test-db-operations.sh --all` passed: retained recovery180.524s, roles73.124s, TLS52.987s. All lanes serial; final teardown succeeded.
- Scoped Ruff E9/F/I, both owned shell scripts' syntax and git whitespace checks passed. No tracked-file deletion.
- Existing verified PostgreSQL image config digest:`sha256:91c89cf7f1f18cc4d96fcb5b9e2438108569c1dfcd5aa7286f9cad7d75742ed4`; Docker engine image identity was verified independently. No image family, dependency or security gate changed.

## Deviations and Issues

No architecture expansion. Root's independently checked ordering correction is recorded above. Owned harness adaptations were necessary: historical app services populate old schema before current read-only application/migration mounts; TLS test probes preserve the actual migration command's inert Settings fields; the source-denied bootstrap receives the trusted sibling recovery producer required by the new verifier. Role-only equality uses revision-selected manifest SQL directly because its intentionally unrelated relation must survive; recovery lanes retain strict schema guards. A first successor rehearsal caught the legacy writer's nontransactional sequence consumption; separation of that intentional injection fixed exact no-writer comparison without weakening any invariant.

## Stubs, Threats and Boundaries

No blocking stubs or unplanned security surface. SQL grants, trusted payload copying, private fixture files, fixed identifiers, authority denials and source-isolated restore implement the planned threat mitigations. Synthetic denied/expired/forged evidence tests preservation and refusal, not external permission.

No production/dev configuration, secrets, rows, paths, services, timers or volumes were accessed. No B2/provider/private API request, global install, external upload, retained live installation, push, PR, merge or deployment occurred. Unrelated .claude/ work is preserved. All commits remain local; publication remains deferred.

Ready for07-05 product-specific admission. SAFE-01 remains pending whole-phase verification. Actual provider rights/access, calendar package approval, genuine calendar evaluator/cross-role proof, final application/browser/image gates and live acceptance remain outstanding in their assigned plans.

## Self-Check: PASSED

All three changed artifacts exist; all four task commits are in branch history and include behavioral RED before GREEN. The exact final --all proof and scoped static checks passed; fixture cleanup succeeded. No phase-completion or provider-activation claim is made.
