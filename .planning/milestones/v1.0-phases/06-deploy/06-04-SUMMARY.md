---
phase: 06-deploy
plan: "04"
subsystem: database
tags: [postgresql18, least-privilege, ownership, alembic, synthetic-rehearsal]
requires:
  - phase: 06-03
    provides: Fixed isolated PG18 lifecycle and independently installed recovery proof
provides:
  - Explicit populated application ownership transfer and separate runtime roles
  - Guarded inspect/apply administration with private credential input
  - Real account/session/trading/scheduler and concurrent migration role proof
affects: [06-05, 06-06, 06-07, 06-09, 06-12]
tech-stack:
  added: []
  patterns: [allowlisted ownership transfer, psql stdin literal binding, creator-specific private defaults]
key-files:
  created: [deploy/db/bootstrap-roles.sql, deploy/configure-db.sh]
  modified: [deploy/tests/test-db-operations.sh, deploy/tests/ops-fixtures.py]
key-decisions:
  - Keep public schema and unrelated objects under existing ownership; migrator owns only explicit application tables and dependent identities.
  - New migrator-created tables and sequences stay private until a migration grants access explicitly.
  - Apply explicitly updates existing role passwords from private 64-hex files; editing environment variables alone does not rotate database passwords.
requirements-completed: []
duration: "Focused role proof approximately 33s; recovery regression 47.816s"
completed: 2026-11-03
---

# Phase 6 Plan 4: Populated Database Roles Summary

**Scoped PG18 ownership transfer preserves populated records and identities while real signup/session/trading, scheduler upserts and concurrent 0008 work under separate restricted roles.**

## Accomplishments

- `configure-db.sh` requires an exact synthetic or fixed production target, private non-sourced JSON, explicit inspect/apply mode and an apply confirmation token. Production invocation remains subject to the later recovery/rollout approval gates. Passwords are constrained 64-hex private files, delivered as psql literal-bound values over stdin, never argv or printed diagnostics.
- Administration shares `/var/lock/birja-deploy.lock` with deployment/backup, rejects overlapping operations, and preflights populated revision 0007/0008, table ownership, role attributes/memberships and unexpected runtime ownership before mutation. A full SQL transaction rolls back on failure. Inspection performs catalog preflight without changing owners/passwords.
- `bootstrap-roles.sql` transfers exactly nine public application tables including `alembic_version`; table ownership carries seven identity sequences, whose owners/dependencies are checked. No blanket reassignment or merged migration edit occurs. Unrelated bootstrap-owned table, identity and records remain unchanged.
- `birja_migrator`, `birja_app` and `birja_scheduler` have no superuser/CREATEDB/CREATEROLE/replication/BYPASSRLS/inheritance or role memberships. Runtime owns no application objects; only migrator gets public schema CREATE. Existing grants follow actual service operations. Runtime cannot write Alembic state or TRUNCATE. Runtime statement/idle timeouts are 30s; migrator has 120s statement/5s lock limits.
- Creator-specific global/schema table/sequence defaults and function execution defaults remain private. Explicit runtime grants apply only to reviewed existing tables/sequences.

## Task Commits

1. **06-04-01: Prove populated ownership transfer and least-privilege behavior** — `bd4f11a` (test).
2. **06-04-02: Deliver reviewed scoped role administration** — `e252e8d` (feat), `6588ff3` (fix: existing shared deploy lock mode).

## Verification

- Meaningful RED: `--roles-red-probe` populated real PG18 revision 0007 using actual application methods, verified nine bootstrap-owned tables and seven identity dependencies, then failed the explicit expected restricted-migrator ownership assertion. Fixed-project teardown ran. Earlier missing-script and incorrect identity-count runs were setup/assertion development failures, not the behavioral RED evidence.
- GREEN: `bash deploy/tests/test-db-operations.sh --roles` passed, including exact private manifest/sequence preservation across transfer and repeated bootstrap; unsafe existing membership/CREATEDB rejection; actual restricted Alembic 0008 concurrent index with `indisvalid`/`indisready`; account creation/conflict RETURNING; session creation/refresh rotation/revocation; buy/sell/replay and locks; scheduler coin reads and insert/conflict-update through existing services.
- Final role contract includes 65 actual SQLSTATE42501 denials: DDL/schema CREATE, ownership, CREATE ROLE/DB, TRUNCATE, Alembic writes, cross-runtime/migrator/bootstrap SET ROLE, forbidden service-table operations, sequence resets, creator defaults and an actual RLS bypass attempt. Twelve input/lock guard rejections and two unsafe pre-existing role preflights also pass. First full final-security run: setup 4.007s, integration 32.955s, warm existing images. No image/package installation occurred; cold acquisition was not measured.
- Recovery regression: `bash deploy/tests/test-db-operations.sh --backup-restore` passed 47.816s. Independently installed launchers performed encrypted backup/retrieval/restore; concurrent writer, private equality, invariants/identities, deliberate corruption, unavailable repository, installed old-host independence and unchanged old checkout/credentials/Compose/revision all passed. Artifact 199,598,080 bytes, SHA256 `0d56eeabcb1cf51f63b5ab306a39f2971559ffe059811053067d913955fab725` identifies only a synthetic public-tool recovery bundle.
- Restore safety: 3 tests passed 0.930s after integration (also passed before role execution). Fixture ruff check/format, embedded wrapper Python ruff, shell syntax and git whitespace checks passed.

## Deviations from Plan

**[Rule 3 - Blocking integration] Preserve the established deploy lock's 0644 mode.** Existing `deploy.sh` can create its nonsecret lock as 0644. Requiring 0600 would reject a valid shared lock before administration. The wrapper now preserves that inode, requires a regular same-owner file with no other writers, and accepts harmless read permissions; the fixture exercises the existing 0644 mode. Credential/config files still require private permissions. No deployment source changes were needed.

## Issues Encountered

Docker socket and git index writes needed the runtime's scoped sandbox escalation for already authorized synthetic tests/local commits. No authentication gate occurred. Identity GENERATED ALWAYS restrictions can precede permission checking, so negative probes use ordinary mutable columns and DEFAULT VALUES to assert the intended 42501 denial. These test corrections did not relax any grant.

## Remaining Evidence / Next Plan Readiness

- Ready for serial 06-05 TLS configuration. The four owned implementation/test files are the only source changes. Shared recovery interfaces remain compatible; no production Compose or application behavior changed in this plan.
- `--production` is implemented for future reviewed invocation, not exercised or authorized here. Later gates must provision private role files/recovery custody, obtain actual recovery evidence, approve live application and integrate service credential routing/TLS/rollback. The script's apply token is a guard, not evidence of owner permission.
- Both DEPL requirements and live acceptance remain pending; `requirements-completed: []` intentionally records no live criterion as satisfied. Preserve the operations ledger's B2 US$0/latest-only/resource/custody policies; this plan accesses no provider.
- No production/provider/secret files, actual OTP/email/authentication/trade, service deployment, global installs, push/PR/merge/release occurred. All records/credentials were synthetic on fixed internal/tmpfs/no-port `birja-ops-test` with finally cleanup. Unrelated `.claude/` remains untouched.
- Stub/security scan found no goal-blocking placeholders or new boundary beyond the planned privileged database/config/file operations. No security certification or production restore claim is inferred.
- The orchestrator owns STATE/ROADMAP/handoff advancement and its separate metadata commit.

## Self-Check: PASSED

Final lock-mode role regression passed: setup 3.831s, full integration 32.544s, 65 permission denials, 12 input/lock rejections and two unsafe-role preflights. All four declared implementation/test files and this summary exist; all three task commits resolve in history, RED precedes GREEN, and no tracked deletion occurred. Final scoped Docker container/network/volume queries returned empty for `birja-ops-test`. Only unrelated untracked `.claude/` remains. The orchestrator owns shared planning-state advancement.
