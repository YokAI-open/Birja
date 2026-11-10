---
phase: 06-deploy
plan: "05"
subsystem: database
tags: [asyncpg, tls, sslcontext, alembic, synthetic-tests]
requires:
  - phase: 06-04
    provides: Populated PostgreSQL role proof and isolated operations fixture
provides:
  - Shared verified CA and hostname policy for backend, scheduler and migrations
  - Fail-closed production trust settings and redacted validation
  - Fixed synthetic test lifecycle with actual startup and migration regression
affects: [06-06, 06-07, 06-08, 06-12]
tech-stack:
  added: []
  patterns: [shared settings protocol, explicit asyncpg SSLContext, bounded migration timeouts]
key-files:
  created: [backend/app/db/connection.py, backend/tests/test_db_connection.py, deploy/tests/test-db-config.sh]
  modified: [backend/app/core/config.py, backend/app/main.py, backend/app/tasks/scheduler.py, backend/alembic/env.py, backend/tests/test_config.py, backend/tests/test_config_scheduler.py]
key-decisions:
  - Require explicit valid production CA trust; retain default CERT_REQUIRED and hostname verification.
  - Keep runtime connection/statement/idle limits at 5s/30s/30s; migrations use 120s statement and 5s lock limits with 30s idle limit.
  - Reject TLS query options and production Unix-socket or query-host bypasses; nonproduction needs no CA unless explicitly configured.
requirements-completed: []
duration: "Wall-clock start not recorded; final focused pytest 12.54s, fixture setup 3.428s"
completed: 2026-11-03
---

# Phase 6 Plan 5: Verified Database TLS Summary

**Backend, scheduler and Alembic share verified asyncpg SSLContext trust, reject production plaintext bypasses and retain bounded connection/session limits.**

## Accomplishments

- `DatabaseSettings` is a small shared protocol covering environment, database URL and CA path. Both application and scheduler settings expose a private `database_ssl_ca_file`; scheduler still receives no authentication/email secrets. Production constructors validate trust, and engine construction revalidates it to fail closed if a file disappears after settings load.
- `ssl.create_default_context(cafile=...)` preserves certificate-chain and hostname checks, TLS 1.2 minimum and explicit selected trust. Missing, unreadable, directory and malformed CA inputs raise generic messages without paths or URL credentials. Existing URL `repr=False` and `hide_input_in_errors` remain intact.
- All three actual startup functions call `database_connect_args` directly. Tests execute each startup path and intercept its engine factory to assert that the returned shared arguments are passed through unchanged. This is execution-path evidence, not source-string matching or a TLS handshake claim.
- Runtime timeouts remain connection 5s, statement 30s and idle transaction 30s. Alembic receives connection 5s, statement 120s, idle transaction 30s and lock 5s. Existing transaction-per-migration and concurrent-index migration behavior remain intact; no schema migration or dependency was added.
- Development/test retain the previous arguments without requiring a certificate; explicitly configured nonproduction trust is verified. Existing valid production constructor tests now generate their own synthetic CA.
- `test-db-config.sh` uses an absolute Compose file, `/dev/null` env file, fixed `birja-test` project and Python `try/finally` cleanup. It runs locked existing dependencies without synchronization/installation and removes only that fixed project. No operational fixture runs concurrently.

## Task Commits

1. **06-05-01: Specify secure engine settings** — `1047d61` (test). Includes a callable prior-policy helper so RED failures are behavioral assertions.
2. **06-05-02: Wire verified SSLContext** — `a92687c` (feat). Includes final startup regression selection and URL bypass cases.

## Verification

- Behavioral RED: 31 failed / 60 passed in 6.52s; fixture setup 3.227s, focused command 8.102s. Failures asserted missing trust rejection, missing SSLContext, URL override acceptance and absent shared-policy consumption at backend/scheduler/Alembic startup. No missing-import failure was counted as RED. Finally cleanup succeeded despite pytest failure.
- Initial GREEN: 91 passed in 7.85s. Expanded startup checks include actual Alembic upgrade to head, backend health and scheduler fake-source cycle against real isolated PostgreSQL/Redis.
- Final GREEN: **117 passed in 12.54s**, fixture setup **3.428s**, focused command **14.072s**. Warm existing image cache; no image acquisition or cold-cache duration claimed. All CA/key material and service credentials are synthetic and temporary.
- `bash deploy/tests/test-restore-safety.sh`: **3 passed**, final safety run 0.987s.
- Affected eight Python files pass Ruff check and format verification; `mypy app` passes across **50 source files**. Shell syntax and git whitespace checks pass. The first uv type-check invocation hit the sandbox's read-only cache; the existing local mypy executable completed successfully without installation.
- Final read-only Docker queries for project `birja-test` containers, networks and volumes all returned empty. No tracked deletion occurred. Unrelated `.claude/` remains untouched.

## Deviations from Plan

**[Rule 2 - Missing critical protection] Prevent production Unix-socket TLS bypass.** asyncpg can skip TLS on Unix sockets even with an SSLContext. Production now requires a TCP hostname, rejects encoded socket-host paths and query-string host overrides. Six focused settings tests cover omitted host, encoded socket host and socket query override for both settings classes. This stays within the planned configuration boundary and adds no architecture or provider decision.

The baseline callable helper was added to the RED commit to satisfy the explicit meaningful-RED requirement. The runtime implementation follows in GREEN. Existing health/scheduler-loop tests were added to the focused runner to verify real synthetic nonproduction operation and migration compatibility; their source files were not edited.

## Issues Encountered

Docker and git index operations needed scoped sandbox escalation for already authorized synthetic tests/local commits. No authentication gate occurred. No full application regression was run here; plan 06-08 owns that gate. Total execution wall-clock start was not captured, so measured test durations are reported instead of an invented elapsed duration.

## Next Plan Readiness

- Ready for serial 06-06 production Compose role/TLS/migrator rehearsal. Real PG18 TLS handshake, trusted `pg_stat_ssl` evidence, untrusted CA, wrong hostname and plaintext rejection remain mandatory there. Unit/config/startup results do not prove those handshakes or any live state.
- This intermediate source change requires the forthcoming production CA routing before a production startup; no deployment was attempted. DEPL-01/02 and live success criteria remain pending (`requirements-completed: []`).
- Preserve the operations ledger: B2 free allowances / US$0 paid usage, latest-only create-before-delete retention, resource constraints and independent custody remain binding. No provider or production data/configuration was accessed.
- No private production/provider files, real OTP/email/authentication/trade, deployment, global/new package installation, push, PR, merge or release occurred. The orchestrator owns STATE/ROADMAP/handoff advancement.
- Stub scan found no goal-blocking stubs. The existing secret-placeholder rejection is a security guard. Threat-surface scan found no boundary outside the planned database trust/configuration/file-read surface.

## Documentation Checked

Context7/ctx7 were unavailable; official [asyncpg connection API](https://magicstack.github.io/asyncpg/current/api/index.html), [SQLAlchemy asyncpg dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#asyncpg) and [Python SSL context API](https://docs.python.org/3/library/ssl.html#ssl.create_default_context) were consulted. No dependency was downloaded.

## Self-Check: PASSED

All nine declared source/test artifacts exist, the lifecycle producer is executable, RED `1047d61` precedes GREEN `a92687c`, both commits resolve in history, and no tracked file was deleted. Focused verification and cleanup are recorded above; this summary completes the owned execution record while the orchestrator advances shared state.
