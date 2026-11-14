# Plan06-08 task03 T3C — final local acceptance passed

Observed2026-11-08 on `feature/phase-06-deploy`, HEAD `e72dcda`.
All22 source paths remain byte-identical to reviewed `e40f688`; the independent
replacement review has0 blockers/0 warnings. No source fix or new review cycle
was needed. Parent owns08 SUMMARY/state/roadmap and later handoff decisions.
This record does not complete DEPL-01/02, remote CI or any live gate.

Private logs, commands, UTC start/finish timestamps, immediate exits/timings,
tool/package inventories, source hashes, scanner identities and raw reports are
retained in ignored `.local/phase-06-handoff/t3c-evidence/`.
Its166-file `SHA256SUMS.json` has SHA256
`6a95813377aa41c9d6daa12beb7404df2a8b2b22c60c09c4b4dc6aacb81e3dad`.
`acceptance.json` verifies50 final command records, their log hashes, all five
raw reports, identical supplied-artifact inputs, copied bytes and cleanup.

## Fresh application and image gates

- Actual final `test-builder`, `runtime`, consumed Node `toolchain` and current
  frontend `dev` builds passed with existing cache. Actual frontend RootFS
  contains the scanned toolchain's complete layer prefix; UID1000,
  Node24.22.2/npm11.21.2 and APK inventory are retained.
- Actual test-builder locked/offline sync and native asyncpg/pydantic-core/
  uvloop/httptools/watchfiles imports passed, with pytest/Alembic/Ruff/mypy/uv
  CLIs. Runtime UID1001 imports, application factory and real migration to head
  passed. Installed distributions remain34 runtime/49 test-builder; the entire
 24-distribution audit-exclusive closure is absent from both.
- Host default `uv sync --locked --offline --no-install-project` retained the
  audit group. `uv run --locked pip-audit`, full Ruff/format and mypy passed.
  No new host tool/package/browser/system dependency was installed.
- Prescribed host suite against isolated candidate `birja-test`: **616 passed**,
  23.02s pytest/24.702s command, **99.80% overall**. The unchanged15-file critical
  list in CLAUDE/CI passed **100%** (797 statements/160 branches). Actual final
  test-builder smoke: **5 passed**, command2.574s. Explicit absolute Compose
  path and `/dev/null` env input were used, followed by finally cleanup.
- Actual final frontend image: lint/types/format, **264 tests**, audit and
  static build passed. Coverage:99.06% statements/97.57% branches/100% functions/
  99.83% lines. Audit exit0 has0HIGH/0CRITICAL and **13moderate/2low**,15total;
  it is not a zero-advisory claim. Static-build command8.960s.
- Unchanged `deploy/scan-images.py` passed29.325s with all five explicit final
  targets, raw exit0 and **0HIGH/0CRITICAL each**. See IMAGE-GATES for exact
  identities/DB dates. No VEX, ignores, waiver, vendor/metadata deletion or
  unfixed suppression was used.

Actual immutable v0.3.1 source/unchanged-lock retained-Dockerfile backend and
frontend build proof from T3B18.751s remains applicable: no source consumer
changed. It was not repeated. The final actual-old integration below is fresh.

## Browser and offline operational checks

Installed Playwright1.64.1 ran the unfiltered suite: **10 passed,1 expected
production-CSP skip**, exit0,57.406s, workers1/retries0. Actual list output and
`.last-run.json` report passed/no failed tests. No production URL was supplied.
The fresh `birja-e2e-test` rendered/actual identities were checked before use:
explicit synthetic Compose environment, fake prices, console email/example.com
accounts, internal data network, normal app bridge, no source mounts/volumes,
private UID70/65532 tmpfs, only frontend loopback publishing. HTTP200 preceded
browser execution. Runtime/scheduler UID1001 and frontend UID1000 were checked.

Fresh offline checks passed: image13,CI4,prerequisites15,backup25 (49.387s),
restore safety4,configuration117 (15.677s), five shell suites58 assertions,
actual nginx syntax,20 recovery input rejections and rollback input guards.
Actual populated image transition passed37.064s: UID999/glibc2.41 original,
clone-only UID70/glibc2.44 conversion, actual collation drift, REINDEX before
refresh, indexed behavior/full invariants, logical restore and untouched-original
abort; Redis UID65532 AOF clone/auth/noeviction/restart/original abort passed.

Two private harness issues are retained honestly. An extra full-suite attempt
inside the smoke-test image failed559pass/28fail/29error because it lacks host
OpenSSL/repository CI fixtures and was given smoke-only environment settings.
The prescribed host full suite then passed all616; no source change resulted.
After successful browser execution, the private command-status writer overwrote
the detailed reporter JSON through a filename collision. The original harness
error remains in `e2e-evidence.json`; `e2e-evidence-final.json` verifies the
actual retained list output and actual copied `.last-run.json`. No raw reporter
document was reconstructed and no passing browser suite was rerun. The private
driver filename is corrected. The backend's one warning concerns a synthetic
40-byte HS512 test key, as recorded in the full log.

## One exact new recovery artifact

Created once with `bash deploy/recovery-bundle.sh package --output
/tmp/birja-backup-test-t3c-final-y6a42d3w/recovery.tar --include-units`.
Packaging4.952s and generic required-profile verification0.736s passed.
152,156,160bytes; separate checksum and SHA256:
`83f4f5151807b67072d99e13a89c6b5f90617d54b7a8261c55931705d6f5044d`.
Inventory has19 payloads plus INVENTORY.json/SHA256SUMS, profile
`deploy-recovery-v2`, both units/quota preflight and the authenticated CGR graph.

All runners below exited0 serially. The two supplied runners received identical
unchanged archive bytes, verified before/after each command; no repackaging or
feature-checkout fallback occurred.

| Command after `bash deploy/tests/` | Seconds |
|---|---:|
| `test-db-operations.sh --backup-restore --recovery-bundle <exact-new-archive>` |65.167|
| `test-db-operations.sh --roles` |30.099|
| `test-db-operations.sh --tls` |49.578|
| `test-rollback-db-security.sh --recovery-bundle <same-exact-archive>` |102.263|

Recovery proved installed launchers, denied checkout access, concurrent-writer
consistency, equality/invariants/identities, FK/index/sequence/constraint and
encrypted checksum/manifest negatives. Roles proved65 denials, repeated populated
transfer, pre-role collation rejection, scheduler/services and valid0008.
TLS proved actual app/scheduler/migrator verification, CA/hostname/plaintext
negatives, mount/credential isolation and renewal. Actual v0.3.1 rollback proved
retained real-Git/legacy routing, recovery-gate failures and same installed
recovery before/after hardening and after old-image rollback, old/current TLS
and preserved0008. Imported PG runs authenticated platform `4401cf29...`,
config `91c89cf7...`, fixed verified-config alias and `pull_policy=never`.

Preserved private packet: `.local/phase-06-handoff/candidate-cgr/` contains the
byte-identical archive/separate checksum, exact raw inventory, trusted current
verifier and `SHA256SUMS`; the historical root `cb766040...` packet is untouched.
Copied archive passed standalone generic verification0.789s. Inventory SHA256:
`55069a4ecca727f85f8f55f33f3e4dc9b9e7887a1ff60841b0aa14a7b45d15ea`;
verifier SHA256:
`c3fed604fbf14ad9c3df0e43b00874d7761223391eb55c7cb0c45a8cde98b4de`.

## Cleanup and self-check

Fresh label queries found0 containers/networks/volumes for all six fixed projects:
`birja-test`, `birja-ops-test`, `birja-restore-check`, `birja-rollback-test`,
`birja-e2e-test`, `birja-image-transition-test`. All bounded cleanup commands
returned0; no global prune/shared-image deletion occurred. All22 reviewed
source hashes, final50 command statuses/log hashes, reports and packet bytes
were verified: **Self-check PASSED**. No new stub or threat surface was added.

No real `.env`/`.aws`, provider/production data, real OTP/email/trade, live
installation/restart, publication or push was used. Unrelated `.claude/` is
preserved. Parent may now evaluate original08 closure; Phase06, DEPL-01/02,
actual current-head CI and09..13 live acceptance remain separately gated.
