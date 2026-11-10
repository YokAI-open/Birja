# Phase 6: Deploy — Pattern Map

**Mapped:** 2026-10-30
**Files classified:** 31 proposed new/modified files
**Analogs:** 25 with useful existing patterns; 6 without a close implementation analog
**Scope:** DEPL-01/02 and all four roadmap success criteria. Research-based planning; no CONTEXT.md exists. No UI changes. Proposed names below are planning targets, not claims that files exist.

## File Classification

Quality: **exact** means the same existing file owns this responsibility; **role-match** means reusable structure with materially new behavior; **none** means use reviewed research design. Grouped assignments below share excerpts rather than repeat them per file.

| New/modified file | Role | Data flow | Closest analog | Quality |
|---|---|---|---|---|
| `deploy/backup.sh` (new) | service | batch, file-I/O | `deploy/deploy.sh` | role-match |
| `deploy/backup-status.sh` (new) | utility | request-response, file-I/O | `deploy/smoke-prod.sh` | role-match |
| `deploy/restore-check.sh` (new) | service | batch, file-I/O | `deploy/deploy.sh`; `backend/tests/guard.py` | role-match |
| `deploy/verify-restore.py` (new) | utility | transform, batch | `backend/tests/test_migrations.py` | role-match |
| `deploy/backup-manifest.sql` (new, or reviewed equivalent) | utility | transform, batch | None: migration snapshots cover only part of schema | none |
| `deploy/systemd/birja-backup.service` (new) | config | event-driven | None | none |
| `deploy/systemd/birja-backup.timer` (new) | config | event-driven | None | none |
| `deploy/db/bootstrap-roles.sql` (new) | utility | CRUD, batch | None: no scoped role/bootstrap implementation | none |
| `deploy/configure-db.sh` (new) | service | batch, file-I/O | `deploy/init-prod-env.sh`; `deploy/deploy.sh` | role-match |
| `deploy/db/pg_hba.conf` (new) | config | request-response | None | none |
| `deploy/provision-db-tls.sh` (implied new name) | utility | file-I/O | `deploy/renew-cert.sh`; `deploy/init-prod-env.sh` | role-match |
| `backend/app/db/connection.py` (new) | utility | request-response | engine construction in `backend/app/main.py` | role-match |
| `backend/app/core/config.py` (modify) | config | transform | same file, Settings/SchedulerSettings | exact |
| `backend/app/main.py` (modify) | provider | request-response | same file, lifespan | exact |
| `backend/app/tasks/scheduler.py` (modify) | service | batch | same file, amain | exact |
| `backend/alembic/env.py` (modify) | config | batch | same file, run_async_migrations | exact |
| `docker-compose.prod.yml` (modify) | config | request-response, batch | same file | exact |
| `deploy/deploy.sh` (modify) | service | batch, file-I/O | same file | exact |
| `deploy/smoke-prod.sh` (modify) | utility | request-response | same file | exact |
| `deploy/RUNBOOK.md` (modify) | config/documentation | batch | same file | exact |
| `deploy/init-prod-env.sh` (modify) | utility | file-I/O | same file | exact |
| `docker-compose.ops-test.yml` (new) | config | batch | `docker-compose.test.yml`; prod internal network | role-match |
| `deploy/tests/test-backup.sh` (new) | test | batch, file-I/O | `deploy/tests/test-app-services.sh` | role-match |
| `deploy/tests/test-restore-safety.sh` (new) | test | batch | `deploy/tests/test-smoke-ports.sh`; test guard | role-match |
| `deploy/tests/test-db-operations.sh` (new) | test | CRUD, batch | `backend/tests/test_migrations.py`; test Compose | role-match |
| `deploy/tests/test-rollback-db-security.sh` (new) | test | batch | `deploy/tests/test-reexec.sh`; rollback tests | role-match |
| `.github/workflows/ci.yml` (modify) | config | event-driven, batch | same file | exact |
| `backend/tests/test_config_db.py` (implied new name) | test | transform | `backend/tests/test_config_scheduler.py` | role-match |
| `backend/tests/test_db_connection.py` (implied new name) | test | request-response | `backend/tests/test_config_scheduler.py`; engine callers | role-match |
| `deploy/stable-deploy.sh` (implied new name) | service | batch, file-I/O | `deploy/deploy.sh` | role-match |
| `deploy/db-security.compose.yml` (implied new name) | config | request-response | None: no retained hardening overlay | none |

The last two files make research's stable rollback adapter concrete. Planner must settle their names and install location outside `/srv/birja` before tasks reference them. A stable entrypoint may instead be implemented within an explicitly retained, versioned script bundle; do not add two competing orchestrators. TLS/ops seed helper names also remain planner choices. No application schema migration is implied solely by credential/HBA administration; any schema change needs a new Alembic revision, never an edit to 0001–0008.

## Pattern Assignments

### Backup, status, restore and DB administration scripts

**Apply to:** `backup.sh`, `backup-status.sh`, `restore-check.sh`, `configure-db.sh`, `stable-deploy.sh`, and modifications to `deploy.sh`.

**Primary analog:** `deploy/deploy.sh`. Shell scripts have no imports; source guards and command wrappers are their dependency seam. Copy strict failure propagation (line 29), explicit step state (line 50), and quoted command wrapper (lines 52–54):

```bash
set -Eeuo pipefail
STEP="startup"
dc() {
  docker compose -f "$APP_DIR/docker-compose.prod.yml" --env-file "$ENV_FILE" "$@"
}
```

The wrapper shape is reusable; restore/ops wrappers must name their own standalone Compose/project and must never load the production env. Backup/administration may use the approved production wrapper only at execution checkpoints.

**Guard and lock pattern:** `deploy/deploy.sh:98–111`:

```bash
[ "$(id -u)" -eq 0 ] || { echo "must run as root" >&2; exit 1; }
if [ "${BIRJA_DEPLOY_REEXEC:-}" = 1 ] && [ /dev/fd/9 -ef "$LOCK" ]; then :
else exec 9>"$LOCK"
fi
flock -n 9 || { echo "another deploy is running" >&2; exit 1; }
```

Copy descriptor-preserving locking where shared with deploy/administration. Define which layer owns the lock: a deploy calling backup while holding it must pass a verified held descriptor or use a clearly internal function, otherwise separate lock opens can deadlock/fail. Reject unsupported target/ref/config before side effects. Restore target guard must run before Docker, SQL or downloads that create sensitive state.

**Source safety:** `deploy/deploy.sh:387–390`:

```bash
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
  exit
fi
```

Keep top-level code free of operational side effects so offline tests can source functions. A sourced settings/definition file must not read secrets, contact Docker or allocate production resources.

**Atomic state publication:** copy same-filesystem replace from `deploy/deploy.sh:175–178`:

```bash
ln -sfn "$1" "$WEB_ROOT/current.tmp"
mv -Tf "$WEB_ROOT/current.tmp" "$WEB_ROOT/current"
```

For backup, use a private temporary status file and rename only after successful dump, archive validation, restic upload and exact snapshot retrieval verification. Keep last good success separate from last attempt/failure. Implement cleanup in EXIT/finally with bounded fixed directories; never print archive/manifests or raw tool errors containing credentials. `deploy.sh:82–93` currently prints service logs: **do not copy this error handler** into backup/restore/admin scripts. Use sanitized step, exit, UTC and snapshot/status evidence.

**Status/smoke pattern:** `deploy/smoke-prod.sh:77–81`:

```bash
TOTAL=0
FAILED=0
pass() { TOTAL=$((TOTAL + 1)); echo "PASS  $1"; }
fail() { TOTAL=$((TOTAL + 1)); FAILED=$((FAILED + 1)); echo "FAIL  $1"; }
warn() { echo "WARN  $1"; }
```

Apply to `backup-status.sh` and new role/TLS/status checks in `smoke-prod.sh`. Machine-readable backup status must have a documented exit contract for absent/stale/failed state. Counts/booleans only for DB checks. Sourceable smoke functions belong before `smoke-prod.sh:68` (its source-return guard); otherwise current shell tests cannot import them. Existing smoke includes a synthetic failed verify request, so invoking the whole script is an operational action, not an offline check.

### Private secret/config writes and certificate provisioning

**Apply to:** `init-prod-env.sh`, `configure-db.sh`, `provision-db-tls.sh`, backup/recovery configuration.

**Analog:** `deploy/init-prod-env.sh:14–21,43–45`:

```bash
if [ -e "$ENV_FILE" ]; then
  echo "$ENV_FILE exists, not overwriting" >&2
  exit 1
fi
umask 077
install -d -m 700 "$ENV_DIR"
tmp=$(mktemp "$ENV_DIR/prod.env.XXXXXX")
# ... generate private content ...
chown root:root "$tmp"
chmod 600 "$tmp"
mv "$tmp" "$ENV_FILE"
```

Preserve existing values on populated deployments. Initial env generation is **not** password rotation or a migration for an existing PG volume. Add reviewed credential augmentation rather than regenerating JWT/OTP/Redis/bootstrap secrets. Add cleanup for unfinished temporary writes. Passwords/URLs must not appear in argv, SQL echo, xtrace, repr or validation errors.

**Partial TLS analog:** `deploy/renew-cert.sh:153–158` installs into a restricted directory and applies key mode 600; `deploy/deploy.sh:117–120` checks certificate expiry with `openssl x509 -checkend`. Reuse those permission/expiry habits only. Public nginx wildcard certificate and manual ACME state are unrelated to the private PG CA/SAN `postgres`; PostgreSQL's runtime UID and key ownership must be tested with the pinned image. No existing DB TLS provisioning/HBA implementation exists.

### Shared DB connection utility and its three consumers

**Apply to:** `connection.py`, `main.py`, `tasks/scheduler.py`, `alembic/env.py`.

**Analog imports:** `backend/app/main.py:1–15` uses stdlib, third-party, then absolute `app.*` imports. `scheduler.py:7–32` follows the same grouping. New helper uses stdlib `ssl` and typed settings/config inputs, no global engine or environment mutation.

**Core engine pattern:** `backend/app/main.py:21–31`:

```python
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={
        "timeout": 5,
        "server_settings": {
            "statement_timeout": "30000",
            "idle_in_transaction_session_timeout": "30000",
        },
    },
)
```

`scheduler.py:273–283` duplicates this; both consumers must use the same verified SSLContext builder while preserving timeouts. Return connect arguments/context, keep lifecycle ownership in callers: `main.py:45–50` and `scheduler.py:315–318` close HTTP/Redis/engine in finally. SSLContext logic itself has no existing analog: follow `06-RESEARCH.md` verified-CA/hostname example and test it; never use TLS fallback modes.

**Migrator difference:** `backend/alembic/env.py:80–87`:

```python
connectable = async_engine_from_config(
    config.get_section(config.config_ini_section, {}),
    prefix="sqlalchemy.",
    poolclass=pool.NullPool,
)
async with connectable.connect() as connection:
    await connection.run_sync(do_run_migrations)
```

Pass shared verified connection args here too; retain NullPool, URL percent escaping at line 28 and transaction-per-migration at lines 62–71. Alembic currently calls full `get_settings()`, requiring auth/email settings; deliberately supply its minimum valid environment or explicitly design separate migration settings. Do not leak migrator credentials into backend/scheduler. Migration timeout must accommodate concurrent 0008 and remain bounded.

### Settings and focused Python tests

**Apply to:** `core/config.py`, `test_config_db.py`, `test_db_connection.py`.

**Analog:** `core/config.py:11–19`:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", hide_input_in_errors=True)
    env: Literal["dev", "test", "prod"]
    database_url: str = Field(repr=False)
    redis_url: str = Field(repr=False)
    otp_hmac_secret: SecretStr = Field(repr=False)
    jwt_secret: SecretStr = Field(repr=False)
```

Mirror DB-TLS settings/validation in `SchedulerSettings` (lines 196–220); it intentionally has no auth/email fields. Existing production refusal style is `config.py:124–128` (`@model_validator(mode="after")`, ValueError then return self); URL validators at 136–141/216–221 only check driver prefix today. Add explicit production trust requirements without breaking intentional dev/test settings.

**Test imports/validation:** `backend/tests/test_config_scheduler.py:1–6,55–62`:

```python
import pytest
from pydantic import ValidationError
from app.core.config import SchedulerSettings, get_scheduler_settings

def test_fake_source_refused_in_prod() -> None:
    with pytest.raises(ValidationError, match="price_source 'fake' is not allowed in prod"):
        _settings(env="prod", price_source="fake")
```

Copy `_settings` construction at lines 13–19, parametrized nonprod allowances at 60–62, secret-absence assertions at 22–43, and lru-cache clearing in try/finally at 29–33. Add meaningful TLS assertions for every engine caller; certificate trust/hostname/plaintext success/failure must be exercised against real isolated PG, not only a mocked constructor. Settings unit tests under `backend/tests` still inherit conftest's Redis cleanup; their runtime commands need the isolated app test stack unless test collection is deliberately separated.

### Production and operations Compose

**Apply to:** `docker-compose.prod.yml`, `docker-compose.ops-test.yml`, retained hardening overlay.

**Existing isolation analog:** `docker-compose.test.yml:4–18`:

```yaml
name: birja-test
services:
  postgres:
    image: postgres:18.6-trixie
    environment:
      POSTGRES_USER: birja_test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: birja_test
    tmpfs:
      - /var/lib/postgresql
```

Use the pin, PG18 mount and readiness behavior, replacing project/credentials with fixed ops-only synthetic values. Omit existing test published ports; add an internal-only network copied from prod lines 6–8. Neither restored real data nor ops fixture goes through `birja-test`, dev or production mounts. Separate ops producer owns lifecycle/seed/TLS files/cleanup. If compatibility requires Redis/app processes, keep those strictly synthetic and console-email/fake-price; never start a real-email clone of restored users.

**Production ownership:** prod lines 25–47 own bootstrap PG credentials/volume; backend lines 77–85 and scheduler 129–133 currently reuse those credentials. Replace runtime routing with explicit app/scheduler roles. Preserve scheduler secret minimization and hardcoded real prices; add one-shot migration service with only migration-needed settings. PostgreSQL has no published port; only backend loopback binding exists. Data network has no fixed subnet: app network `172.29.50.0/24` is not evidence of the data subnet for HBA.

### Offline operational shell tests and isolated integration

**Apply to:** all four new `deploy/tests/test-*.sh` files.

**Strong test analog:** `deploy/tests/test-app-services.sh:8–12,31–34`:

```bash
HERE="$(dirname "$(readlink -f "$0")")"
. "$HERE/../deploy.sh"
set +e
trap - ERR
# Stub, then assert status and output independently.
dc() { echo "invalid interpolation format" >&2; return 1; }
OUT=$(app_services 2>/dev/null); RC=$?
check "dc config failure -> non-zero" 1 "$RC"
check "dc config failure -> no service list printed" "" "$OUT"
```

Copy failure assertions, not just happy-path messages. Lines 38–45 run the real call-site shape in a strict subprocess to verify failure stops the build; use this for failed dump/upload/validation stopping status publication. Shell errexit behaves differently inside `if`, `!`, `&&`, subshells and command substitution: test exact invocation context. `test-smoke-ports.sh:38–48` demonstrates stubbing `docker`; restore rejection tests must record **zero command calls**. `test-reexec.sh:15–16,65–80` covers temporary cleanup and real flock descriptor handover; use it for backup/deploy overlap and stable launcher regressions.

**Integration analog:** `backend/tests/test_migrations.py:54–140` creates synthetic populated data, snapshots rows+constraints, upgrades 0007→0008, checks index readiness/validity and equality, then cleans up in finally. Useful verifier excerpt at 111–128:

```python
assert index[0] is True and index[1] is True
assert index[3] == ["user_id", "created_at", "id"]
assert await snapshot() == before
```

Adapt its explicit catalog assertions and bound parameters, not its actual fixture engine/downgrades. Ops runner must start fresh synthetic PG18, seed at 0007, transfer allowlisted ownership/grants, migrate as restricted owner to 0008, prove runtime CRUD/identity/upsert and forbidden DDL/table access. Restore integration then verifies retrieved encrypted snapshot, exact private manifest, constraints, indexes, Decimal/timestamps and identity progression; deliberate tampering must fail. Build an actual v0.3.1 image from a local archived ref, retaining newer schema/adapter; no host worktree checkout or production DB for compatibility tests.

### CI and runbook changes

**Apply to:** `.github/workflows/ci.yml`, `deploy/RUNBOOK.md`.

**CI cleanup pattern:** current backend lines 40–53 and image lines 99–105 pair isolated setup with `if: always()` cleanup. Ops producer must have its own fixed project and cleanup, with serial DB/rollback integration; preserve existing five offline deploy regressions. Add operational job to the required aggregate, currently lines 172–180:

```yaml
ci-pass:
  needs: [backend, frontend, image, e2e]
  if: always()
```

Without adding the new job to `needs`, branch-protection success would not gate operational failures. Keep timeouts, contents-read permissions, coverage/audits and real browser jobs. CI e2e lines 112–118 explicitly enforce fake prices/console email and lines 152–154 run `npx playwright test`.

Runbook analog lines 9–18 inventory paths/state; 32–68 distinguish deployment/rollback; 164–200 document nontransactional index failure recovery. Add backup/recovery key custody, timer install/disable/status, storage/retention decisions, DB TLS renewal and rollback-support contract. Correct stale “no backups until Phase 6” statements only with delivered behavior/evidence. No automatic schema downgrade/production restore as app rollback.

## Shared Patterns

### Isolation before imports or side effects

`backend/tests/conftest.py:23–24` calls `ensure_test_stack(...)` before app imports; `backend/tests/guard.py:15–21` rejects wrong host/port/database. Copy the **ordering**, not the app fixture allowlist, into restore guards. Restore needs stricter fixed project/mount/target rules. Conftest automatically migrates at 68–74 and deletes scoped Redis keys at 146–150; never repoint its URLs to a restored clone. Existing migration tests downgrade shared fixture schema and must not run concurrently with ops transitions.

### SQL/grant ownership follows real operations

Read references for the grants plan: `accounts.py:13–29` uses users INSERT ON CONFLICT/RETURNING and account INSERT; `auth.py:73–87,138–190` inserts sessions/tokens and locks/updates revocation; `trading.py:228–335` SELECT FOR UPDATE plus account/holding UPDATE and trade INSERT/RETURNING/refresh; `prices.py:75–113` scheduler reads coins/prices and INSERT ON CONFLICT UPDATE prices. Runtime SELECT FOR UPDATE also needs the relevant update permissions. Grant required identity/sequence access and prove generated inserts. No runtime ownership, schema CREATE, role administration, TRUNCATE or alembic_version writes. Scheduler cannot inherit general application grants.

Model inventory is eight app tables plus alembic_version: users/accounts/auth_sessions/refresh_tokens/coins/prices/holdings/trades. Model definitions use Numeric(20,8), timezone-aware DateTime, Identity(always=True), foreign keys, CHECKs and user-scoped uniqueness; canonical private manifests must preserve these values precisely and test constraints independently of hashes. The research's exported-snapshot lifecycle and safe sequence progression have no existing complete implementation.

### Preserve actual happy-path evidence

`frontend/e2e/trade.spec.ts:21–65` signs in, previews/buys exactly $100, asserts $9,900 cash and fee, then sells the full holding. `portfolio-history.spec.ts:197+` captures real fill responses; its earlier viewport presentation cases mock portfolio/history data and alone are not trading evidence. Preserve both real browser stories in actual CI. Neither fixtures nor signed-out smoke prove Gmail/Outlook inbox delivery: friends type their own OTP and verify their account's trade/portfolio/history after an authorized release. Record provider class and pass/fail only.

### Rollback security survives checkout

`deploy/deploy.sh:52–54` reads Compose from APP_DIR; `279–281` checks out then may self-reexec; `334–357` rollback checks out an old ref and rebuilds/restarts its service definitions. Preserve rollback stack semantics (`192–207`, tested by `test-rollback-target.sh`) and lock tests while introducing the stable adapter. An overlay alone is insufficient if subsequent invocations use the overwritten old entrypoint. Install retained versioned orchestration/config outside checkout, explicitly gate supported refs, and prove v0.3.1 sign-in/trade with restricted roles + verified TLS. Never weaken HBA or reintroduce bootstrap URLs to make rollback work.

## No Analog Found

| File / behavior | Missing pattern | Planner source |
|---|---|---|
| `backup-manifest.sql` | Shared exported-snapshot canonical complete manifest and identity validation | Research backup/restore patterns; PG18 integration producer |
| backup service/timer (2 files) | No existing host backup timer | Research systemd example; actual scheduled snapshot evidence |
| `bootstrap-roles.sql` | Populated ownership transfer/default grants/identity dependencies | Research role map; explicit existing object allowlist; PG18 negatives |
| `pg_hba.conf` | PostgreSQL hostssl/SCRAM/plaintext rejection | Research TLS decision; positive/negative session checks |
| retained `db-security.compose.yml` | Old-ref credential/trust routing independent of checkout | Research rollback adapter; old-image compatibility test |

Other role matches are structural only: there is no existing restic upload/retrieve/status workflow or verified asyncpg SSLContext helper. Do not present those behaviors as copied, tested implementations.

## Revision contract: prerelease recovery artifact

Plan 06-03 task 2 also owns `deploy/recovery-bundle.sh`: source-safe shell,
private atomic install and lock/path guard patterns above apply. There is
no existing complete bundle analog. Package only backup/status/snapshot SQL
and stdlib verifier/restore/fixed Compose, approved restic and pinned PG18
client/server image closure plus content manifest/runtime inventory. Verify
archive identity independently before extraction, reject links/traversal and
unexpected members, and resolve retained helper paths from canonical
`/var/lib/birja/recovery/releases/<archive-sha>`. Stable recovery launchers
are distinct from the later retained deployment bundle. Rehearse installation
with no feature checkout on a synthetic populated v0.3.1/0007 target; repeat
with the same installed entrypoints after role/TLS rollout. 06-08 adds final
tested units using the same producer; 06-09 installs that exact artifact
under scoped approval before backup or feature publication. Existing five
06-07 regression tests permit import/call-site edits only; broader changes
require a separately planned serial scope. Restore actions explicitly read
`backend/tests/test_migrations.py` for catalog/equality/finally patterns,
without importing its fixtures or borrowing its destructive engine.

All these are execution contracts, not implemented or tested artifacts.

## Metadata

**Search scope:** deployment scripts/tests/runbook, production/test Compose, app settings/three async engine factories, migration 0008 and tests, guards/fixtures, models/services, actual browser stories and CI. Five primary pattern families: deployment shell, settings/engines, isolation fixtures, catalog migration verification, CI/browser flows. Additional reads establish consumers and hazards, not a search for more analogs.

**Ownership:** one plan/task owner per shared `deploy.sh`, prod Compose, core config and CI file; backup, DB security and rollback tasks coordinate these dependencies. Root orchestrator owns shared planning state/validation. This mapper writes only this document.

**Execution status:** read-only source analysis; no tests, Docker/services, installs, env/credential reads, live DB/log/OTP/email/balance access, remote operations, commits or branch changes. Paths/line numbers reflect this checkout on 2026-10-30; live state and execution inputs remain unverified.
