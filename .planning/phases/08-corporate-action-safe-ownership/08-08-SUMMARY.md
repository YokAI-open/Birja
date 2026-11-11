---
phase: 08-corporate-action-safe-ownership
plan: "08"
subsystem: database
tags: [postgresql, reconciliation, least-privilege, recovery, tls]
requires:
  - phase: 08-07
    provides: Durable monitoring and immutable historical action holds
provides:
  - Evidence-bound scoped SQL reconciliation with a separate NOLOGIN operator
  - Protected private inspect/reconcile tooling and redacted committed receipts
  - Exact0012 authority recovery and actual restricted operator replay/TLS proof
affects: [08-09, 08-12, 09-stock-trading, 10-dividend-payments]
tech-stack:
  added: []
  patterns: [same-snapshot-admission-binding, immutable-resolution-history, quarantined-authority-restore]
key-files:
  created: [backend/alembic/versions/0012_stock_action_resolution.py, backend/app/services/stock_action_reconciliation.py, backend/tests/test_stock_action_resolutions.py, scripts/stock-actions.py]
  modified: [backend/app/services/corporate_actions.py, deploy/db/bootstrap-roles.sql, deploy/backup-snapshot.py, deploy/backup-manifest.sql, deploy/verify-restore.py, deploy/tests/test-stock-recovery-contracts.py, deploy/tests/test-db-operations.sh, deploy/tests/test-restore-safety.sh, deploy/tests/ops-fixtures.py]
key-decisions:
  - Resolution binds the exact action/calendar snapshots actually validated, then rechecks their full hashes under the shared instrument gate.
  - Identical confirmations preserve an approved disposition; new uncertainty or immutable material history invalidates it.
  - Restore authenticates the independently pinned0012 function before fixed operator authority is recreated in a quarantined clone.
requirements-completed: []
requirements-addressed: [DIV-01, DIV-02, ACT-02, ACT-03]
duration: 104min
completed: 2026-11-11
---

# Phase 8 Plan 08: Scoped Reconciliation and Exact Recovery Summary

**An audited, narrowly privileged resolution can clear only a verified event dispute; immutable accounting and independently authenticated SQL authority survive encrypted recovery.**

## Scope and behavior

Three tasks, thirteen implementation/test/tooling files, approximately104minutes.
All database, role, restore and TLS work uses owned isolated synthetic projects.
No dependencies, real credentials/configuration, provider HTTP, production,
B2, timers, existing Phase7 campaign, publication or deployment were accessed.
Stock actions and stock execution remain disabled by default. Whole-phase
requirements and external acceptance remain pending.

Additive0012 creates a fixed SECURITY DEFINER function owned by the migration
owner, with fixed search_path and qualified objects, no dynamic SQL, PUBLIC
EXECUTE revoked and only the preprovisioned NOLOGIN operator granted EXECUTE.
Restricted migration never gains CREATEROLE. Unsafe operator attributes,
outgoing memberships or direct/transitive runtime membership are refused.
Operator reads comprise the existing thirteen action/stock tables and only
five catalogue columns; accounts, holdings, fills and financial mutations stay
outside its authority. Scheduler's six immutable fill columns remain unchanged.

Reconciliation uses the exact existing single-instrument transaction gate,
reloads committed revision/generation/safety epoch/unit/journal identity, checks
fresh DB wall time after waits, and compares complete action/calendar admission
hashes. Python fetches each admission row and its PostgreSQL digest together,
validates that precise snapshot and requires the supplied hash to match it.
SQL then rechecks the same hashes under the gate. Caller-supplied hashes cannot
substitute a different, revoked row between validation and execution.

Supported correction/no-effect/verified same-event alias decisions append an
immutable audit and advance the safety epoch without changing cash, holdings,
fills, prior history or an applied economic event. Alias agreement uses latest
immutable source observations, including legitimate shared revisions; uncertainty
or conflicting economics cannot be skipped. Historical holds clear only for
the exact checked event/revision history. Routine identical polls preserve the
disposition; new uncertainty or changed immutable history invalidates it.
Health still requires independent full monitoring, calendar and quote checks.
Unsupported or historical financial repairs remain held.

The private CLI uses bounded typed owned0600 evidence/config files, protected
parents, descriptor reads, no symlinks, duplicate keys, nonfinite values or
unknown fields. CA bytes receive the same protection and are passed directly
to SSL cadata. Connections use verified TLS and a dedicated NOINHERIT login
with operator membership. Inspection is bounded and sanitized; reconcile emits
only a sanitized receipt after successful commit. There is no provider fetch,
web router, arbitrary SQL/URL, force flag or health override.

## TDD and task commits

- Task1 RED `ccfe1d9`; initial GREEN `6eda9a5`. Additional actual authority,
  identical-poll, alias and membership regressions: `746b9c9`, `eaafba7`,
  `a3235ae`; fixes `f549c86`, `8f5e5aa`.
- Task2 RED `b520cff`, `5092696`, `3485ae7`, `8d9914e`; GREEN `2c0c713`,
  `32451e1`, `8473edd`, `0acb2b2`. These include protected CA loading,
  post-commit receipts and precise validated-snapshot binding.
- Task3 RED `5a88529`, `d9534c0`, `7bbc89d`; GREEN/recovery corrections
  `aaeec79`, `7aac11e`, `05a4321`, `17cbe97`. Actual integration exposed
  fixture authority mismatches, corrected in `29b40d1` and `f6c79f0`.
- Final verified test import formatting: `c5a0b98`.

These RED gates assert behavior, including real PostgreSQL authority and race
facts; missing imports/files are not counted as RED. Independent review of
the final functional and recovery/fixture source records zero active findings
in `08-08-REVIEW.md`.

## Verification

- Final focused actual isolated PostgreSQL suite: **55passed,4 existing calendar
  warnings,18.79s**. New reconciliation service: **121statements/52branches,100%**.
  Log `/tmp/phase08-08-validated-snapshot-green.log`.
- Actual canonical predecessor/accounting suite: **8passed,53.924s**, plus the
  isolated0012 effective-column-authority case **1passed,2.384s**. This exercises
  real manifests and outgoing membership/missing read/column UPDATE/unexpected
  SELECT/grant-option corruptions. Logs `/tmp/phase08-08-canonical-green.log`
  and `/tmp/phase08-08-column-authority-green.log`.
- Final offline contracts: **7active tests pass**;3actual-PG cases intentionally
  skip in offline mode. Restore-safety suite: **6passed,1.33s**. Scoped Ruff,
  format checks, mypy, py_compile and diff checks pass.

The final actual recovery proof used one installed retained tool archive for
**every0007–0012 encrypted backup/retrieval/restore**, including concurrent-writer,
checksum/manifest/truncation and unavailable-repository refusals. Exact rows,
schema, accounting, all17identity states, source container/mount identities and
unchanged source configuration pass. Nine accounting and seventeen identity
corruptions are rejected; all thirteen0012 function/owner/ACL/NOLOGIN/column
authority corruptions are rejected, including a changed body with a forged
self-reported hash. Actual restored operator-service decision replay and actual
split-service replay each run twice without a second effect. Recovery portion
completed **301.665s**, log `/tmp/phase08-08-ops-complete.log`.

That runner subsequently stopped at a fixture-only NOLOGIN direct-login
assertion. After correcting only that test helper, the **remaining**
`bash deploy/tests/test-db-operations.sh --roles` completed with exit0:
roles **158.290s**, populated0011→0012 TLS **105.969s**, fresh0012 TLS
**105.810s**. Effective ACL parity,63denied operations, restricted migration,
actual dedicated nonprivileged operator reconcile/replay/stale refusal and
PUBLIC/app/scheduler denials pass. Bad CA/hostname/plaintext refusals, credential
mount isolation, renewal, actual accounting/ownership/calendar consumers and
legacy0008 compatibility remain proven. No post-upgrade grant repair occurs.
Log `/tmp/phase08-08-roles-tls-final.log`. Do not describe the earlier stopped
runner as an exit0 `--all`; all its constituent lanes are proven serially.

Actual fresh-server diagnostics separately prove restricted0012 restoration,
all thirteen authority refusals, operator/split replay, final canonical equality
and unsafe existing LOGIN-role refusal without repair. These raw-dump diagnostics
are separate from the completed encrypted same-archive proof.

All owned `birja-ops-test` containers/volumes/networks and recovery-check
containers are cleaned. DB lane is released; parent Wave6 full integration gate
is separate from these plan-local checks.

## Retained identities

Protected non-secret tool archive:
`/tmp/birja-backup-test-phase08-final/recovery.tar` (0600 in0700 directory),
152186880bytes, SHA256
`db27d99ba3085c6b93fa4fe4a6ea6bd9be5ea38a89f9e5f3620005de9681b874`.
It contains0012-compatible recovery code; installed production tooling is unchanged.
Earlier archive `b04964b2…` proved only0007–0011 before the initial fresh-role
failure; those historical passes are not substituted for this final proof.

- Independent reviewed PostgreSQL function-definition pin:
  `a612d7fb2f5b4f50549f4d40b01e6e83a2bfaf8a7d4ce1f77ff2df22b13b2dc1`.
- 0011 migration remains byte-exact:
  `ba07623bca2cff4e709971e2157364e417d877b085ff5e4f24dfa3e96fb72af3`.
- 0012 migration `439a36e6…`; service `3633a7a8…`; producer `9e24a224…`;
  restore verifier `1aa43377…`; final fixture `edc0b3ec…`.
- Selected predecessor SQL hashes remain unchanged:0007/8 `52753d97…`,
  0009/10 `30b3ab07…`,0011 `a4917389…`.

## Deviations from plan

1. **[Rule2 — correctness integration]** The existing hold reader needed scoped
   immutable-resolution matching, and the operator needed five catalogue-column
   reads for actual inspection. Both were narrowly authorized; no general
   financial read/write privilege or health override was introduced.
2. **[Rule1 — reviewed races and semantic bugs]** Real regressions corrected
   identical-poll invalidation, conflicting/shared aliases, unsafe memberships,
   calendar/actions changes while waiting, precise validated-snapshot binding,
   unsafe CA reopening and receipts emitted before commit. Each final source
   boundary received independent re-review.
3. **[Rule2 — recovery authority]** pg_restore without owners/ACLs cannot restore
   SECURITY DEFINER authority by implication. The0012-only quarantined path now
   authenticates an independent fixed definition/signature/owner and recreates
   only a reviewed fixed role/read/EXECUTE allowlist. Effective column privileges,
   grant options and outgoing memberships are inventoried. Older selected SQL
   contracts remain byte-compatible.
4. **[Rule3 — fixture/provisioning correctness]** Actual integration exposed
   stale0011 table-count assumptions, multi-instrument seed transactions, fresh
   role creation attempted through a restricted migrator, privileged corruption
   injection attempted through a restricted clone owner, and direct login to a
   NOLOGIN group. Fixtures now preprovision explicitly, use separate instrument
   transactions and bootstrap-only rollback-wrapped injections. Restricted
   production migration/restore consumers gain no CREATEROLE or repair authority.

No new architecture, packages, external access or activation was introduced.
No known implementation stubs remain. Whole-phase integration, later API/UI
work, owner acceptance and external rights/live-data gates are not completed here.

## Self-Check: PASSED

All25recorded task/test/fix commits exist; all five primary created/runtime
artifacts exist. Final retained archive SHA was remeasured, and claims above are
supported by actual focused, recovery, role and TLS logs. Parent full Wave6
integration remains separately owned.
