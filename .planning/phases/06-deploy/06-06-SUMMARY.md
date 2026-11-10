---
phase: 06-deploy
plan: "06"
subsystem: database
tags: [postgresql18, tls, scram, compose, synthetic-tests]
requires:
  - phase: 06-05
    provides: Shared verified SSLContext policy at backend, scheduler and Alembic engines
provides:
  - Private PostgreSQL CA/server lifecycle with permission, expiry and renewal checks
  - SCRAM hostssl routing with explicit plaintext and network bootstrap rejection
  - Separate app, scheduler and one-shot migration credential/trust routes
  - Real PG18 TLS, populated migration and credential exposure regression
affects: [06-07, 06-08, 06-12]
tech-stack:
  added: []
  patterns: [per-service credential routes, private CA custody, production-derived synthetic Compose]
key-files:
  created: [deploy/provision-db-tls.sh, deploy/db/pg_hba.conf]
  modified: [docker-compose.prod.yml, deploy/init-prod-env.sh, deploy/tests/test-db-operations.sh, deploy/tests/ops-fixtures.py]
key-decisions:
  - Use PostgreSQL samenet against its directly attached internal data network rather than inventing a fixed Docker subnet.
  - Keep the CA signing key outside mounted server/client material; root-owned server keys use PostgreSQL group 999 with mode 0640.
  - Supply only inert unrelated Settings inputs to one-shot Alembic; never share actual web authentication or email credentials with migration.
  - Preserve the immutable recovery-only Compose definition and generate the TLS fixture from controlled production service routing.
requirements-completed: []
duration: "Measured final recovery 48.256s, roles 33.489s, TLS 35.853s; initial reading start not captured"
completed: 2026-11-03
---

# Phase 6 Plan 6: Production-shaped PostgreSQL TLS Summary

**Separate app, scheduler and migrator logins connect to PostgreSQL 18 through verified TLS, with private certificate custody and explicit plaintext rejection.**

## Accomplishments

- Production Postgres enables TLS 1.2 minimum, mounts server leaf/key and HBA read-only, and retains the existing `pgdata:/var/lib/postgresql` identity. Only its internal data network is attached. Redis/Postgres still publish no ports; backend retains loopback `127.0.0.1:18000`; the scheduler remains a single dedicated service.
- Backend receives only APP_DATABASE_URL as DATABASE_URL; scheduler receives only SCHEDULER_DATABASE_URL; the `migrate` profile receives only MIGRATOR_DATABASE_URL. Each client mounts only the public CA. Bootstrap/server key material never reaches clients; scheduler has no web authentication/email secrets. The one-shot migrator uses the existing runtime build and Alembic/shared timeout policy. Its command supplies distinct inert JWT/OTP and unused email settings because Alembic loads full Settings; these are not actual authentication/provider credentials and no email/Redis operation is invoked.
- HBA preserves intentional local socket administration/backup, rejects all plaintext TCP, permits only the three restricted logins over SCRAM hostssl from directly attached networks, then rejects other TCP. The successful synthetic connections exercise samenet against actual Docker allocation; no production network/subnet was inspected or fabricated.
- `provision-db-tls.sh` accepts only the exact production target or guarded private synthetic roots, explicit custody and production-operation gates, and the shared operation lock. It refuses symlinks/unsafe modes/ownership, duplicate creation and lock contention; errors are redacted. The independent signing key is root-only 0600 outside all mounts. The server key is root:999 0640 under root:999 0750; the pinned PG18 image's actual postgres group is asserted 999 and real server startup proves readability.
- CA validity is 3650 days and leaf validity 365 days with SAN postgres and serverAuth. `--check` verifies trust, hostname, SAN, key pairs, permissions, a 30-day leaf warning window and one-year CA headroom. Renewal preserves the CA and replaces only leaf material. Tests sign an actual one-day leaf, assert the warning gate fails, then renew successfully. No automatic reload/restart or off-server export is performed; independently recovered custody and an explicitly approved reload remain operational prerequisites.
- New-install env generation creates four distinct 64-character random database credentials, keeps generated content root-only and publishes with atomic no-clobber hard-link creation. Tests run only in a new synthetic root, assert distinctness privately and preserve the exact file on a second invocation. Existing production env/auth/Redis/bootstrap credentials were never read, overwritten or rotated. Environment generation alone does not provision roles; the deliberate schema/role bootstrap procedure remains required before starting a new installation.
- The TLS producer renders production Compose using an explicit synthetic environment and `/dev/null` env file, adapts it into fixed `birja-ops-test` internal/tmpfs/no-host-port resources, and binds current application source read-only over the existing pinned test image. Actual app signup/account, session rotation/revocation, buy/sell/replay and scheduler price service calls use the shared helper. Each role's own `pg_stat_ssl` session reports SSL. Missing trust, unrelated CA, wrong DNS hostname and SSL-disabled TCP fail. Actual one-shot Alembic migrates a populated 0007 database to 0008 and verifies its concurrent index is valid. Service environment/mount inspection proves credential isolation. All lifecycle cleanup is in finally.

## Task Commits

1. **06-06-01: Specify real TLS and credential isolation** — `5f3c58f` (test).
2. **06-06-02: Deliver private TLS/HBA and explicit migrator routing** — `82f5d6c` (feat).

## Verification

- Meaningful RED: restore-safety **3 passed in 0.988s**, then a real PG18 session using the current helper failed the intended assertion `real_pg18_verified_tls=false plaintext_session=true`. Missing artifacts/imports were not counted as RED; cleanup ran.
- Initial direct `--tls` GREEN passed, setup **9.275s**, integration **34.867s**. Initial fixture bring-up exposed umask masking requested directory modes; server/HBA permissions were corrected and verified with actual PostgreSQL startup.
- Final prescribed serial `test-restore-safety.sh && test-db-operations.sh --all && test-restore-safety.sh` **passed**. Safety **3/3**, **1.085s** before and **1.039s** after. Recovery **48.256s**; roles setup **3.987s**, integration **33.489s**; TLS setup **11.433s**, integration **35.853s**. These measurements use existing warm images/dependencies; no cold-cache acquisition claim is made. Integration measurements exclude their following finally teardown.
- Recovery replay installed the immutable recovery artifact against the actual old checkout under Landlock, preserved unchanged source checkout/configuration, performed encrypted backup/retrieval/restore with a concurrent writer, and rejected row/manifest/FK/index/sequence/checksum/truncated-archive corruption. New production credential variables did not break the independent recovery dependency closure.
- Role regression retained **12 input/lock rejections**, **65 actual permission denials**, populated ownership/identity transfer, repeatability and concurrent 0008 migration validity. TLS additionally passed actual per-role SSL, bad CA/hostname/plaintext/missing-trust negatives, certificate permissions/ownership/expiry/renewal/lock checks, and synthetic init distinctness/nonoverwrite.
- Existing backup regression **17 passed in 45.784s**, including actual approved local restic encryption/rotation and failure preservation. Its local benchmark: 11,772 archive bytes, 932 packed bytes added, 3,408 repository bytes, 14 tool invocations, 7,651ms measured local transaction, 5,285ms child CPU, 60,032 KiB peak child RSS, zero network bytes/requests. This is synthetic local evidence, not provider cost or live size evidence.
- Ruff check and format verification pass for the changed Python fixture. Shell syntax, embedded provisioner Python AST and git whitespace checks pass. Final read-only fixed-project container/network/volume queries returned empty. No tracked deletion occurred; unrelated `.claude/` remains untouched.

## Deviations from Plan

**[Rule 3 - Blocking fixture interface] Extend `deploy/tests/ops-fixtures.py`.** The declared shell runner delegates the actual lifecycle to this file; real TLS assertions cannot be delivered in the shell wrapper alone. The parent explicitly authorized this necessary fixture change. No application runtime source/dependency was changed in this plan.

**[Rule 2 - Preserve independent recovery safety] Keep `docker-compose.ops-test.yml` unchanged.** Recovery validates its exact reviewed hash and recovery-only service closure. Adding TLS/client services there would break that boundary and require unrelated recovery artifacts. The new fixture instead derives a private temporary Compose definition from production routes, while `--all` runs recovery, roles and TLS serially. The existing hash/closure remained valid and its full rehearsal passed.

## Limitations and Next Plan Readiness

- Plan 06-07 still owns the retained deployment/rollback adapter, actual v0.3.1 compatibility and migrator invocation in deployment. Existing deploy.sh has not been changed here; this intermediate production Compose requires its forthcoming secure deployment integration before use. No production start/restart occurred.
- These tests exercise synthetic role sessions and actual service methods, not live friends, public email delivery, production database state or an external provider. The temporary backend/scheduler fixture containers use inert commands for environment/mount inspection; service behavior runs through Compose one-shot Python clients with the corresponding routes. Startup helper wiring was verified in plan 06-05. No long-running real Kraken scheduler/network operation was attempted.
- Full application/frontend/browser/CI and separate security/review gates remain plan 06-08 or later. DEPL-01/02 and all live criteria remain pending, hence `requirements-completed: []`.
- All operations-ledger policies persist: B2 free allowances/US$0 paid use, latest-only create-before-delete rotation, bounded resource/headroom checks, independent recovery custody and owner daily checks. No provider account/configuration, production/private secret files, real authentication/trade/email, deployment, global/new dependency installation, push, PR or merge occurred.
- The orchestrator owns STATE/ROADMAP/requirements/handoff advancement. This executor supplies only its scoped source/test commits and summary. No authentication gate occurred. No goal-blocking stub or new trust boundary beyond the plan's file/TLS/database surface was found.

## Documentation Checked

Context7 and ctx7 were unavailable. Consulted official [PostgreSQL 18 TLS](https://www.postgresql.org/docs/18/ssl-tcp.html), [HBA rules](https://www.postgresql.org/docs/18/auth-pg-hba-conf.html), and [Compose services](https://docs.docker.com/reference/compose-file/services/) documentation; reused the existing locked dependencies and image pins.

## Self-Check: PASSED

All six owned source/test files exist, including the executable provisioner and the runner invoked through Bash; the independent ops Compose remains intact. RED `5f3c58f` precedes GREEN `82f5d6c` and both resolve in history. Required serial verification, explicit cleanup queries and absence of tracked deletions are recorded above. Shared state is intentionally left for the orchestrator.
