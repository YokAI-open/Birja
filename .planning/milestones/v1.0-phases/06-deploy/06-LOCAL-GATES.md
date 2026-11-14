> Current local acceptance: **T3C passed2026-11-08** on unchanged reviewed
> `e40f688` source. See `06-08-T3C-EVIDENCE.md` and `06-IMAGE-GATES.md`.
> Fresh five-image raw0HIGH/0CRITICAL; backend616/99.80%/critical100,
> frontend264/audit/build, actual browser10pass/1expectedskip and one new
> exact-artifact recovery/roles/TLS/actual-old rollback passed. New archive
> SHA256 `83f4f5151807b67072d99e13a89c6b5f90617d54b7a8261c55931705d6f5044d`
> is preserved in ignored `.local/phase-06-handoff/candidate-cgr/`.
> All six synthetic projects have zero resources. Parent owns08 closure;
> remote CI/provider/live/DEPL acceptance remains pending. The dated records
> and earlier archives below are historical and are not new-source acceptance.

# Phase 06 local gates — Plan 08 checkpoint

Observed 2026-11-06 on `feature/phase-06-deploy`. **Plan 08 is incomplete:**
tasks 01/02 implemented; task 03 image security gate failed, independent
code/security review and goal verification pending. No SUMMARY is created
because it would incorrectly increase SDK completed-plan counts. DEPL-01/02,
actual remote/browser CI, provider account setup and live acceptance remain open.

## Commits and scope

- `8d38095` — task01 meaningful callable RED: preflight was not called and
  approved retained schedule/launcher assertions failed.
- `5d22241` — task02 RED: required ops job/aggregate contract failed while
  existing application/browser assertions passed.
- `68f622b` — task02 GREEN: required serial ops job, exact signed restic
  acquisition, failure/cancel/skip aggregate and preserved existing gates.
- `e2b02b4` — task01 implementation: measured quota wrapper, protected setup
  attestation, mandatory recovery inventory/units, procedures and regressions.

RED01 recorded 12:47:20 UTC; implementation commit 12:58:26 UTC. Work continued
through the final serial checks below. No retrospective RED was fabricated.
Task03 is verification/documentation work, not a new product behavior.

One authorized fixture adaptation outside original08 file list: the authentic
legacy-profile negative in `test-deploy-prerequisites.py` initially failed
generic verification because it declared `units=[]`. Its fixture now includes
`CORE + UNITS` and declares exact units, preserving every original assertion
and the meaningful legacy-profile rejection before runtime/Docker/install.
The separate ops input negative fixture required no change and still rejects.

## Environment and execution

Host Python3.12.3; application Python3.14.9; Node24.22.1; npm11.19.1;
uv0.13.5; Ruff0.17.2; mypy2.4.0; pip-audit2.10.1; Docker29.2.1;
Compose5.0.0; systemd255.4; approved restic0.19.1, binary SHA
`20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639`.
Existing locks and installed dependencies were used; no new npm/pip/global tool
was installed. Docker test-builder/runtime builds use the committed uv lock.

Application fixtures and operational fixtures ran serially, each with finally
cleanup. Full backend driver used absolute Compose path,
`docker compose -p birja-test --env-file /dev/null -f
/home/YokaiExchange/docker-compose.test.yml`; `up -d --wait` and finally
`down --volumes --remove-orphans --timeout 10`. Original failures were preserved
if cleanup also failed. No dev/prod stack was used.

An unprivileged attempt at `test-db-config.sh` in the initial offline batch
failed immediately on Docker socket permission before lifecycle access; it did
not start/stop any fixture. It was subsequently run with scoped Docker access
after full backend cleanup and passed. Audits initially failed sandbox DNS;
the authorized network rerun below passed. Neither was counted as a test pass.

## Application, audit and image build gates

Commands below ran from the named directory with existing installed locked
tools. Wall durations include process startup; pytest also reports its own time.

| Directory | Exact command | Result | Wall seconds |
|---|---|---|---:|
| backend | `.venv/bin/ruff check .` | pass | 0.034 |
| backend | `.venv/bin/ruff format --check .` | pass | 0.023 |
| backend | `.venv/bin/mypy app` | pass | 0.782 |
| backend | `.venv/bin/pytest --cov=app --cov-fail-under=80` | 616 passed,99.80% | 28.230 |
| backend | `.venv/bin/coverage report --include=<critical list below> --fail-under=100` |100% |0.244|
| backend | `.venv/bin/pip-audit` | no known vulnerabilities |2.138|
| frontend | `npm run lint` | pass |5.507|
| frontend | `npm run typecheck` | pass |6.553|
| frontend | `npm run format:check` | pass |2.181|
| frontend | `npm run test -- --coverage` |24 files/264 tests pass |19.989|
| frontend | `npm run build` | pass |7.351|
| frontend | `npm audit --audit-level=high` | pass |53.743|
| root | `docker build --target test-builder -t birja-backend-test:phase05-07 backend` | pass |12.942|
| root | `docker build --target runtime -t birja-backend-runtime:phase06-08 backend` |pass|2.600|
| root | `docker run --rm --network host birja-backend-test:phase05-07 pytest tests/test_smoke.py -q` |5 passed|4.309|
| root | fixed `birja-test` finally cleanup above |pass|0.700|

Critical include argument is identical to CI:
`app/services/otp.py,app/services/auth.py,app/services/accounts.py,app/services/ratelimit.py,app/services/email.py,app/core/security.py,app/core/deps.py,app/services/price_rules.py,app/services/prices.py,app/services/trade_math.py,app/services/trading.py,app/services/portfolio_math.py,app/services/portfolio.py,app/services/history.py,app/api/v1/history.py`.
Backend pytest reports616 passed in25.59s and one existing test-only JWT
InsecureKeyLengthWarning (40-byte synthetic HS512 key versus64 recommended).
No application warning was changed. Frontend statements99.06%, branches97.57%,
functions100%, lines99.83%. These are fresh measured results, not historical
Phase05 counts reused as evidence.

## Offline and synthetic operational gates

| Command from root | Result | Wall seconds |
|---|---|---:|
| `bash deploy/tests/test-reexec.sh` |14 assertions pass|0.096|
| `bash deploy/tests/test-rollback-target.sh` |18 assertions pass|0.165|
| `bash deploy/tests/test-app-services.sh` |8 assertions pass|0.058|
| `bash deploy/tests/test-smoke-ports.sh` |11 assertions pass|0.061|
| `bash deploy/tests/test-smoke-trading.sh` |7 assertions pass|0.029|
| `bash deploy/tests/test-restore-safety.sh` |4 tests pass|1.176|
| `python3 deploy/tests/test-deploy-prerequisites.py` |14 tests pass|8.001|
| `python3 deploy/tests/test-ci-ops.py` |3 tests pass|0.060|
| `bash deploy/tests/test-backup.sh` |22 methods pass|50.081|
| `bash deploy/tests/test-backup.sh Backup.test_nightly_success_and_local_inventory_exhaustion` |new23rd method pass|1.205 unittest time|
| `bash deploy/tests/test-db-config.sh` |117 tests pass, finally cleanup|17.619|
| `bash deploy/check-nginx-config.sh` |syntax pass|0.073|

The new23rd method was added after the full22-method process loaded its tests;
it was then run separately. Final focused native tests also passed after their
additional assertions: versions across pagination/hide markers/other buckets;
unfinished parts and rejected other-bucket unfinished use; read-only inventory
capabilities and bucket-scoped part authorization; unsafe endpoints/redirects;
128-call/120-second limits, oversized streamed response; private setup controls,
10-minute maturity,31-day renewal, unknown keys and insufficient local headroom;
actual wrapper invocation, failure status and previous-success preservation.
All provider behavior is synthetic; no credential/account/provider API was used.
Native call counts are distinct from restic subprocess counts. Wire bytes and
actual restic HTTP request totals remain unmeasured; local budget fields are
admission reserves, not remaining B2 account allowances or exact counters.

`python3 deploy/tests/ops-fixtures.py --self-test-recovery-bundle-inputs`
passed20 rejection cases with zero Docker/package/install calls. The final
supplied-artifact runners validate archive hashes/manifests/profile and forbid
feature-checkout/default-package fallbacks. Safety tests reject omitted quota,
either unit and unchecked extra members before runtime/Docker.

`systemd-analyze verify` passed in a private synthetic root containing the
exact units, inert executable and inert dependency targets. Direct host verify
initially reported the intentionally uninstalled stable launcher missing. This
proves parser/directive compatibility, not an actual activated host service.
Existing `rhysd/actionlint:1.7.7 -color -` passed with only CI YAML on stdin and
network disabled. Affected Python Ruff/format, shell syntax and git whitespace
checks pass. No real timer was installed/enabled or systemd service started.

## Final exact recovery artifact and serial runtime proof

Final archive:
`/tmp/birja-backup-test-plan08-final-ytdyw6o6/recovery.tar`
with independently stored `.tar.sha256`;199,639,040 bytes, SHA256:
`aea60b9f7b05a997660983968ac9eb28a32c4821ba025e8b445fb4851d4bbc8f`.
Package command: `bash deploy/recovery-bundle.sh package --output <that-path>
--include-units`,7.876s. Final source implementation is `e2b02b4`; later
runbook/evidence edits are not archive members.

The exact `deploy-recovery-v2` inventory includes17 payload files plus
INVENTORY.json and SHA256SUMS: backup/status/restore wrappers, backup producer,
quota producer, manifest SQL, bundle producer/verifier, both units, fixed ops
Compose, PostgreSQL image archive, four provenance records and approved restic.
Quota SHA `9276184f2a387c60e3587d1e72f4fcfb943b85bd482b0ae96d627dd103433b54`;
service SHA `e4751dd6cd602178d56a7225a1affa7f34a014b1b88a920f733aea52018cd298`;
timer SHA `e79fb4c343f6a2b71d51a6c6dd080beb0264bcb8953aeae70d842b84e890253a`;
verifier SHA `74d8546f7c8622c44805594e03299baca6562e8d99f389a53623443b2bafbeab`.
Image identity remains the approved PostgreSQL18.6 ID
`sha256:edb0c08dc33befd0262ab3b5cf1c4f3f8cfd8b09e88c05b45adee29d6761ddb6`.

- Exact supplied recovery command: `bash deploy/tests/test-db-operations.sh
  --backup-restore --recovery-bundle <final-path>` passed78.936s wall,
  77.245s integration. Old checkout0007/feature access denial, installed
  launchers, concurrent-writer snapshot consistency, private exact equality,
  financial invariants, schema/FK/index/sequence/identity negatives, encrypted
  checksum/private-manifest negatives, retained original credentials/Compose
  and staging/clone cleanup passed.
- `bash deploy/tests/test-db-operations.sh --roles` passed35.434s wall:
  populated transfer/repeatability, actual services/scheduler,12 guards and65
  denied operations. `--tls` passed60.772s wall: actual18.6 TLS, CA/hostname/
  plaintext negatives, app/scheduler/migrator isolation and renewal.
- `bash deploy/tests/test-rollback-db-security.sh --recovery-bundle <final-path>`
  passed120.277s wall/115.713s integration. Exact deployment recovery gate
  rejected missing/failed/stale evidence; the same installed recovery worked
  before hardening, after roles/TLS and after actual v0.3.1 rollback. Current
  and old services used TLS; bad CA/hostname/plaintext were rejected;0008 was
  preserved. Installer/real-Git repeated legacy entrypoints, immutable routing,
  checkout failure restoration and changed-launcher/unheld-lock negatives passed.
  The earlier superseded artifact
  `01183ade473541bed6e61c3e45db29ee95becc50e68c1362210ce34b331af855`
  passed83.653s recovery/120.072s rollback, but is **not** the final artifact:
  the subsequent security pass bounded streamed reads and tightened read-only
  capability validation. No final-artifact claim relies on that earlier run.

## FAILED image security gate — blocks completion/live advancement

Official Trivy0.76.1 amd64 image was selected through official installation/
release sources and registry manifest, pulled with authorization and pinned to
`aquasec/trivy@sha256:2e6c00d711ab4ae41d8a30c2c1fd3bd3b62704c177bb120f95012e939edfb3df`.
Its `--version` returned0.76.1. A later newer-version notice was not permission
to substitute a floating image. Official sources:
https://trivy.dev/docs/latest/getting-started/installation/ and
https://github.com/aquasecurity/trivy/releases/tag/v0.76.1 .

Each image was exported with `docker image save -o <private-temp>/image.tar
<image>`, scanned in a read-only/cap-drop-ALL/no-new-privileges container with
only that generated archive mounted read-only and a private temporary DB cache.
No source tree, secrets, production files or Docker socket was mounted.
Exact scanner arguments: `image --cache-dir /cache --input /scan/image.tar
--scanners vuln --severity HIGH,CRITICAL --exit-code 1 --timeout 5m`.
The vulnerability DB132.18MiB downloaded successfully. No ignore-unfixed,
ignorefile, CVE suppression or severity reduction was used.

| Image | Observed HIGH / CRITICAL categories | Exit | Seconds |
|---|---|---:|---:|
| birja-backend-runtime:phase06-08 |Debian51/0; Python aggregate5/0|1|16.424|
| birja-backend-test:phase05-07 |Debian51/0; Python aggregate5/0|1|7.418|
| postgres:18.6-trixie |Debian68/1; gosu Go25/1|1|8.619|
| redis:8.8.3-trixie |Debian50/0|1|3.190|
| node:24.22.1-trixie-slim |Debian50/0; Node packages6/0|1|4.956|

Concrete findings needing review:

- PostgreSQL libxml2 `CVE-2026-6653` CRITICAL, installed
  `2.12.7+dfsg+really2.9.14-2.1+deb13u3`, no fixed version listed. gosu embedded
  Go1.24.6 `CVE-2025-68121` CRITICAL, scanner fixes1.24.13/1.25.7/1.26.0-rc.3.
- Debian apt/libapt `CVE-2026-109518` installed3.0.3, fixed3.0.4. Many
  util-linux/ACL/zlib/other OS findings have no scanner-listed fix. Exact
  fixed-versus-unfixed counts were not emitted as JSON; merged table cells
  are not reliable enough to fabricate a fixability tally.
- Python aggregate: msgpack1.1.2 `CVE-2026-114613` fixed1.2.3 and
  `GHSA-6v7p-g79w-8964` fixed1.2.1; setuptools70.3.0 `CVE-2025-47273`
  fixed78.1.1; urllib3 2.7.0 `CVE-2026-97687`/`CVE-2026-97689` fixed2.8.0.
  All individual app `/opt/venv` METADATA targets report0. Actual in-image
  importlib.metadata inspection found none of those three packages in either
  `/usr/local/lib/python3.14/site-packages` or `/opt/venv/lib/python3.14/site-packages`.
  Scanner warns third-party SBOMs may be inaccurate. The aggregate may describe
  bundled/SBOM components; its origin remains unresolved. No false-positive
  waiver is claimed and no app lock was changed based on this ambiguity.
- Node bundled brace-expansion5.0.9 `CVE-2026-102276` fixed5.0.10 and
  `CVE-2026-102278` fixed5.0.11 (other major fixes listed); undici6.28.0
  `CVE-2026-109383`/`CVE-2026-109869`/`CVE-2026-87018` fixed6.29.1 and
  `CVE-2026-19534` fixed6.28.1 (other major fixes listed).

Current CI image job has **no Trivy step**, threshold or ignore-unfixed policy;
it builds both targets and smokes only. Thus local scan is a newly measured
required project gate, not an existing CI scan claimed to pass. Backend
pip-audit and frontend npm audit passing do not satisfy base-image findings.

Bounded next-step proposal for parent review: inspect exact Trivy JSON/SBOM
locations/vendor advisories first; establish which components are distributed
and fixed, without dismissing findings from lack of Python METADATA alone.
Research supported patched same-major Python3.14/Postgres18/Redis8/Node24
base-image pins and immutable digests. Propose only necessary Dockerfile/image
pin or tightly bounded build-tool cleanup changes with explicit affected
files; do not refresh application locks or remove runtime libraries blindly.
Unfixed distribution findings need vendor-supported disposition or remain
blocking; no blanket ignore-unfixed or automatic waiver. Add the agreed pinned
scan to required CI image gates so the accepted policy is enforced remotely.
Image changes require affected build/smoke/scan and image-bound recovery
provenance/rehearsal updates, not unrelated application rewrites.

## Separate inline reviews and remaining authority

Inline code pass examined final source/diff: canonical lock lifetime and failed
attempt publication, exact bundle membership/hashes/profile before runtime,
stable launchers independent of old checkout, preserved aggregate/browser
commands and cleanup failure behavior. No additional source defect found after
focused corrections. This is author review, **not independent review**.

Separate inline ASVS5 L1/security pass examined provider credential/endpoint/
redirect/pagination/response boundaries, read-only account scope, bucket-bound
writer use, private JSON/atomic writes, no secret logs/argv and fail-before-
upload/delete behavior. Corrected potentially unbounded streamed response
reads and rejected all non-read/list inventory capabilities. Focused regressions
pass. Whole-image HIGH/CRITICAL findings above remain unresolved and block
completion. No full-app ASVS certification is claimed. UI review N/A: no UI
changes. Parent must arrange independent code/security review and goal check.

Pending: image remediation/disposition and CI scan policy; independent reviews;
real actual CI/browser execution after separately approved push; provider
caps/private key setup and actual off-server recovery; real scheduled-trigger
evidence; production roles/TLS/deploy; friend Gmail/Outlook trade acceptance.
No provider/account/production action, private config/.env/.aws read, real
authentication/trade/email, install/enable/restart, push/PR/merge/release occurred.
Unrelated `.claude/` is preserved. STATE/ROADMAP/requirements remain parent-owned.

Public/synthetic detailed evidence remains in `/tmp/birja-plan08-app-gates.log`
and `.json`, `/tmp/birja-plan08-backend-gates.log` and `.json`,
`/tmp/birja-plan08-audits-network.log` and `.json`,
`/tmp/birja-plan08-offline-gates.log` and `.json`,
`/tmp/birja-plan08-final-ops.log` and `.json`,
`/tmp/birja-plan08-image-scans.log` and `.json` (the scan `.json` is timing/status,
not vulnerability detail). Do not confuse these public artifact/tool findings
with private production evidence. Temporary image-scan archives/cache were
removed in finally. Final exact recovery artifact is retained privately for
the parent's review; it contains public tools/units/image, no application data.

## Checkpoint self-check

At13:05:57 UTC, explicit Docker label-filtered queries found **zero containers,
networks and volumes** for each of `birja-test`, `birja-ops-test` and
`birja-restore-check`. All four listed RED/GREEN commits exist; declared quota,
units, verifier/tests/runbook and final archive exist. No tracked deletion
occurred. Only this evidence document and the scoped0008 runbook clarification
remain for the checkpoint documentation commit. No source gap/stub was hidden;
the failed security gate above remains explicit. No SUMMARY/state advance or
requirements completion was performed.

## Actual isolated browser rehearsal — 2026-11-07

At source `ba1897d19f4a3b0eae89925d0d501c2269936a5f`, existing installed
Playwright1.64.1/Chromium1248 ran the actual browser suite: **10 passed,
1 skipped,0 failed,0 flaky**, starting16:27:34 UTC. Covered sign-in/session/
sign-out, connected services, markets, responsive portfolio/history at four
widths, real cash-only portfolio, exact server-valued buy/portfolio/history/
whole-position sell and the separate trading round trip. The existing CSP
test skipped because `E2E_PROD_URL` was unset; no deployed-site proof is claimed.

Only throwaway `birja-e2e-test` was used. Absolute base Compose plus a private
temporary override, `COMPOSE_PROJECT_NAME=birja-e2e-test`, synthetic
`COMPOSE_ENV_FILES` and `COMPOSE_DISABLE_ENV_FILE=1` were inherited by the
existing console-code helper. The rendered definition was checked before
startup: internal data network, tmpfs datastores, no named volumes/source
mounts, no backend/datastore host ports, frontend bound only to127.0.0.1 on a
free port; fake prices/console email and example.com accounts only. No real
`.env`, credentials, market API, email, account or trade was used. No tool,
browser or system dependency was installed; application locks were unchanged.

The first temporary fixture also made the app network internal: all services
were healthy, but host navigation was refused (10 failed/1 CSP skip in10.629s).
That failure is preserved at `/tmp/birja-e2e-local-mkapjajz/`; cleanup passed.
Only the temporary app network was returned to the base bridge, retaining the
internal data network and loopback publishing. A localhost HTTP200 probe then
passed before browser execution; no repository source fix was needed.

Initial final-image build/start took108.450s; `docker compose exec -T frontend
npm run build` passed6.353s. The successful rehearsal reused those exact images
with `up --no-build -d --wait --wait-timeout 180` (18.072s), then existing
`frontend/node_modules/.bin/playwright test --workers=1 --retries=0
--reporter=list,json --output <private-temp>/test-results` (57.391s).

| Running consumer | Actual linux/amd64 engine image ID |
|---|---|
|Frontend final Dockerfile/toolchain|`sha256:0ed8023343303f9f1061a5dd3ac8a0ac4cf8accf0fa32605ee27c0501b890b70`|
|Backend runtime|`sha256:d93f802d73240b78a97ea497d4786d31b3ad9487108e70c8a1424f90db99c5da`|
|Scheduler runtime|`sha256:28beb53cafd236a33a25324307cbaf1c840b4d9572df56a319e736dec3bd07ac`|
|PostgreSQL pinned index|`sha256:bd5dfa494a5a259704365813dbfa5fa6b3e69be7348d43b547f540c730478583`|
|Redis pinned index|`sha256:a008e2cb5579f3616b29bd9e9913a25f16ec09ae2f56ddab524664663b581228`|

Final frontend Dockerfile SHA256:
`5bc2ebb43ab48a7223272e560d4e0c0138b1e5ee6444b67b83e76b0f4c6717fe`.
Successful evidence/sanitized logs/JSON: `/tmp/birja-e2e-local-bigoocoe/`;
`playwright.json` SHA256
`babc68fe287cd16481e7fe52e4235e4f62e3efc8aa6ac5233e1e3007662777d6`.
Finally `down --volumes --remove-orphans --timeout 10` passed2.484s; label
queries found zero project containers/networks/volumes. Other projects and
shared caches were untouched. This closes the local browser execution gap;
remote CI, image security acceptance and provider/live gates remain separate.
No push or Plan08 completion is implied.
