# Phase 06 Plan 15 image gates — bounded acceptance complete

Image/build observations: 2026-11-06. Closeout checked 2026-11-07 on `feature/phase-06-deploy`. Tasks01/02 and bounded task03 acceptance are complete through source `de331fb`. Independent source/security review and both focused rechecks have zero active findings. The previously recorded export failure below was corrected and the final exact archive passed recovery/roles/TLS/actual-old rollback. **Raw vendor HIGH/CRITICAL findings still block Plan08 task03 and all downstream live gates.** No08 SUMMARY or DEPL completion is justified.

## Implemented and reviewed source

- `a126899` / `5bc74ed`: image/provenance RED/GREEN, exact same-major pins, complete unused global pip/ensurepip removal and offline recovery mapping.
- `500a724` / `a5dd5a2`: strict five-target scanner RED/GREEN, actual loaded stages, exact image/config evidence, retained reports and required CI enforcement.
- `4c77542` / `be09c3f`: complete official npm11.21.2, production/retained toolchain consumer and inventory closure.
- `3bc1ca7`: 60-second/10-MiB bounded streamed acquisition before SHA512 verification and extraction.
- `26614f5`: missing built-image IDs become explicit failed named records while the other available reports are collected; original Docker errors survive. Independent WR-01 recheck passed.

All four upstream pins remain the exact reviewed version@index values in `06-15-SCOPE.md`. Application locks, Python3.14, PG18.6/layout/UID999, Redis8.8, Node24, trixie/glibc and uv0.13.5 remain preserved.

The actual Docker29 containerd store distinguishes engine/manifest IDs from config digests. Recovery authenticates registry index → selected platform manifest → config bytes and layers, then binds a fixed local alias to an allowed verified imported immutable engine identity. Classic config-ID and containerd manifest-ID import-only tests pass without registry refs/RepoDigests or pull fallback. The final actual execution proof below complements the import-only behavioral tests.

Approved ownership additions: `deploy/deploy-entrypoint.sh` requires/packages the trusted current frontend Dockerfile so old-source builds use the retained toolchain; `deploy/tests/test-rollback-db-security.sh` adds only that file to its synthetic source inventory. No shared framework or application dependency update was added.

## Actual builds and affected checks

Public/synthetic detailed logs: `/tmp/birja-plan15-build-{builder,runtime,node,frontend}.log`, `/tmp/birja-plan15-frontend-gates.log`, `/tmp/birja-plan15-affected.{json,log}`, `/tmp/birja-plan15-retained-contract.log`, `/tmp/birja-plan15-backup.log`, `/tmp/birja-plan15-prerequisites-final.log` and `/tmp/birja-plan15-safety-final.log`.

- Actual pinned backend test-builder/runtime builds passed. Builder locked `uv sync --locked --no-install-project --offline`, imports, pytest9.1.1 and migration CLI passed. Runtime UID1001 imports, application factory, uvicorn/migration CLI and actual synthetic `alembic upgrade head` passed.
- Global `/usr/local` pip and ensurepip are absent in both stages, including bundled wheel/entrypoints/metadata. The test virtualenv legitimately retains pip26.2.2 through locked `pip-audit2.10.1 → pip-api0.0.35 → pip26.2.2`; its five scanner findings remain. No required audit tooling or lock was stripped.
- Serial fixed `birja-test` actual image smoke:5 passed,4.589s; runtime app import2.323s; runtime migration2.123s; locked in-image pip-audit passed3.279s. Finally cleanup passed.
- Complete official npm11.21.2 tarball SHA256 `8ad8563b81e71b90ef405b140bccf3ba9b5e7884ab210bd49ee4e2f4bc6f61f5`; independently verified registry SHA512 `7HPApk+AflMUavSseL1Pm6CnYqMIHk53x+KmuhqmTDqPkjPMgxIpTPcTqsE91EKNw4gFBJV9fnXiSdGm1DXq9A==` before inspection/extraction. Actual inventory: Node24.22.2/npm11.21.2, brace-expansion5.0.12/undici6.29.1. Official metadata: https://registry.npmjs.org/npm/11.21.2 .
- Actual initial frontend consumer image build, npm audit and static build passed. Actual v0.3.1 frontend archived source/unchanged lock built with the complete toolchain as UID1000 using `npm ci --ignore-scripts && npm run build`,71.685s. These app build checks preceded the final streamed-download guard; only the finalized toolchain target was rebuilt afterward. No claim is made that a final dev frontend image was rebuilt after that guard.
- Final reviewed toolchain rebuild passed: `docker build --platform linux/amd64 --target toolchain -t birja-node-toolchain:phase06-15 frontend`, log `/tmp/birja-plan15-final-build-node.log`.
- Focused source checkpoint:8 image methods covering12 scanner modes,4 CI methods,15 prerequisite methods,4 safety methods,25 backup methods (51.818s),20 input rejections; retained-installer real-Git rollback contract, reexec14/rollback-target18/app-services8 passed. Affected Ruff/format, shell syntax, whitespace and cached offline actionlint passed. The independent WR-01 recheck separately reran8 image/4 CI methods. Historical full616/264 coverage was not repeated.

## Raw image security remains FAILED

Scanner remains Trivy0.76.1 at `aquasec/trivy@sha256:2e6c00d711ab4ae41d8a30c2c1fd3bd3b62704c177bb120f95012e939edfb3df`. Read-only root, bounded writable tmpfs, cap-drop ALL/no-new-privileges; only generated image archive/private cache mounts. No source/private configuration/socket mount, ignore-unfixed, VEX, waiver or severity change.

Actual five-target producer returned1 with valid JSON for every target. Reports in `/tmp/birja-plan15-final-image-reports/`; DB UpdatedAt `2026-11-06T18:59:52.855177206Z`, DownloadedAt `2026-11-06T20:02:11.714417141Z`, NextUpdate `2026-11-07T18:59:52.855177045Z`. These four unchanged-image reports are reused by exact identity below. The initial Node report in that directory is historical after the final acquisition-guard rebuild; the changed Node identity was scanned separately, avoiding four redundant scans.

| Final selected target | Debian HIGH/CRITICAL | Other HIGH/CRITICAL | Raw exit | Scan seconds | Report SHA256 |
|---|---:|---:|---:|---:|---|
|Runtime|49/0|0/0|1|13.648|`f5ee15dae5727661a5bc69760dad6cfd65569ca55079ee0e9ac9c3277db0ca28`|
|Test-builder|49/0|Python5/0|1|6.025|`ba64c3dba62f7e851245a27b638f77efe6744fa31bf9321d50634ec033a5a629`|
|PostgreSQL|66/1|gosu25/1|1|8.763|`3e64f38b84c5c9f2999f0720b0b71557b020a319228e238888fce1ffedc6dad9`|
|Redis|48/0|0/0|1|3.518|`981269125278951ecca5abd6e42fe0577a55c1daf37ac708ec9eb6683cbaca79`|
|Final Node toolchain|48/0|0/0|1|16.183 including export|`57301c9bd65f535a15da5831717f446e6a04baf28b754fcae3ff0cb07a64d666`|

Final Node JSON/log/evidence: `/tmp/birja-plan15-final-node-0t6brzg7/`; fresh DB DownloadedAt `2026-11-06T20:18:55.512380458Z`, same UpdatedAt/NextUpdate as above. Its scan used the identical pinned scanner/archive isolation/severity/error policy, verified report config identity against exported config bytes, and removed its private archive/cache afterward. Runtime/builder/PG/Redis contents did not change between their reports and this checkpoint. Counts are package-CVE rows, not unique CVEs or a pass.

| Target | Engine image identity | Exported config digest |
|---|---|---|
|Runtime|`sha256:4ee72846293ae245237e8e2d28abbedafdd9ab4698c01963035ea3578052b6de`|`sha256:f9eb01e13a5480042d6c2d459f04f80fd1e4434025d9caa8e1f1f6f2745cdd43`|
|Test-builder|`sha256:0a54af1e919adc5a2f74c8439c1b25b0c14d77977834be4863e39a2b2f267f6b`|`sha256:16a2032d7e9b110f061bd7794a067c9d9a5d0f7758c1b2d8b68346403f553982`|
|PG source index|`sha256:bd5dfa494a5a259704365813dbfa5fa6b3e69be7348d43b547f540c730478583`|`sha256:8bca9649e52d948114ccc8164b55b7ab26b64e729893e420114bb5c87bf7c7cc`|
|Redis source index|`sha256:a008e2cb5579f3616b29bd9e9913a25f16ec09ae2f56ddab524664663b581228`|`sha256:12be8ae6a26778e7cb90c22c7324a7355ae2651146aa7120ffdadec80668227e`|
|Final Node toolchain|`sha256:4faa35ee6b9d4bfcd53f51be74ed54aa3cbdba70dd8ff93983a4a727ba522555`|`sha256:643cb7be5fceb1d8814c45b3568b59026df8260427aeef71599e0ba3664d5285`|

The PG index selects linux/amd64 platform manifest `sha256:e923a22ac074261dd73970c57edf659475bf0497cb9456f17d98ed7cdd3ca913`. Explicit-platform Docker inspection returns that engine manifest ID; ordinary source-index inspection can expose the index ID. Neither is labeled a config digest.

Apt/libapt CVE-2026-109518 rows are absent after the reviewed rebuild/patch refresh. Runtime's five distributed global-pip rows and all six npm rows are removed by complete-tool changes. Remaining builder Python rows: msgpack1.1.2 CVE-2026-114613/GHSA-6v7p-g79w-8964, setuptools70.3.0 CVE-2025-47273, urllib3 2.7.0 CVE-2026-97687/97689, with scanner-listed fixed versions1.2.3/1.2.1,78.1.1,2.8.0. Their aggregate `Python` target originates in required `/opt/venv/.../pip/_vendor`, not remaining global pip. PG target `usr/local/bin/gosu` still reports Go1.24.6 including CRITICAL CVE-2025-68121; PG libxml2 CRITICAL CVE-2026-6653 remains. Exact remaining rows/paths/installed/fixed versions are retained in JSON and the existing research. No not-affected disposition or vendor fix is invented.

## Historical packaging failure — resolved by `de331fb`

Final attempt command:

```text
bash deploy/recovery-bundle.sh package --output /tmp/birja-backup-test-plan15-final-o3bb9vxl/recovery.tar --include-units
```

Exit1 after5.884s. Wrapper logged `recovery=false step=guard-or-verification`. A direct stdlib diagnostic call confirmed the exact rejection:

```text
bundle_package -> verify_saved_image
deploy/verify-restore.py:201
require(len(saved_index["manifests"]) == 1)
ValueError: recovery guard
```

**No recovery.tar or separate SHA file was created.** No supplied recovery, roles, TLS or actual-old rollback runner was started during this final attempt. The older `aea60b9...` bundle remains historical and does not satisfy current acceptance.

Actual `docker image save --platform linux/amd64` exports two OCI root descriptors: the authenticated runnable manifest `e923a22...` and attestation sibling `sha256:9676119228eeb6a3405ee1aa59e7b7a0d2d0c083e90eda6c09eb963856beab40`, annotated with subject `e923a22...`. The strict verifier intentionally permits only its authenticated runnable graph and rejects this extra graph before image load/install.

A proposed two-line selection fix was tested rather than assumed: capture explicit-platform inspected engineID and save that immutable ID instead of the source index. Its mocked regression passed, but **actual export still included the same attestation sibling and failed the unchanged guard**. The ineffective source/test changes were removed; no fix commit or weakened verifier was retained.

| Diagnostic Docker-save input | Export bytes | Export SHA256 | Actual strict verification |
|---|---:|---|---|
|Canonical PG index pin|168550912|`3f7da981b33a850dcf1a9ba69a1056fc26ce0b892b3ef1f4f1991da3a387fe81`|Reject extra root descriptor|
|Selected immutable engineID `sha256:e923a22...`|168550400|`aff0ec8ac56f9f89bd36ce7d6417521a921bb813f64580a97cc71ab9b51d1559`|Same rejection|

Small exact exported index evidence is retained as `/tmp/birja-plan15-export-index.json` and `/tmp/birja-plan15-selected-index.json`; diagnostic image export archives were removed after recording hashes. Approved upstream exact index/platform manifest bytes remain in `/tmp/birja-plan15-registry/`. Attempt log/status: `/tmp/birja-plan15-final-ops.{log,json}`. The following bounded, independently reviewed correction resolves this historical failure without relaxing unknown-graph rejection.

## Final correction and exact supplied-artifact acceptance

`de331fb` authenticates at most one optional selected-platform attestation from the exact pinned upstream registry index, requires its subject/platform association, hashes its manifest/config/every in-toto layer, and retains exact known-blob membership. Unknown roots, unknown blobs, duplicates, mismatched subjects and changed bytes/sizes reject. Classic Docker exports and runnable-only OCI behavior remain supported. No arbitrary image, registry dependency or pull fallback was added. Independent focused security review passed with zero new findings;9 image contracts,15 prerequisites,4 safety methods and affected Ruff/format/whitespace passed. See `06-15-REVIEW.md` for the separate reviewer evidence.

Actual packaging plus generic verification succeeded in8.082s. One finalized archive was used unchanged for both supplied-artifact entrypoints; no repackaging or feature-checkout fallback occurred:

- Path: `/tmp/birja-backup-test-plan15-fixed-zl4pb12y/recovery.tar`;199,669,760bytes.
- External SHA256 and separate `.tar.sha256`: `cb766040b9eed5eed4dce00400d39c0d8bcb7a02fc4c6d4030c9e6cf6da16814`.
- Inventory: `deploy-recovery-v2`,19 payloads plus INVENTORY.json/SHA256SUMS, including both systemd units, quota preflight, exact index/platform manifest, PG archive and signed-restic provenance/tool.
- Index `bd5dfa49...`, platform manifest `e923a22a...`, config `8bca9649...` are the full digests recorded above and in INVENTORY.json. Actual recovery log confirms running `sha256:e923a22ac074261dd73970c57edf659475bf0497cb9456f17d98ed7cdd3ca913`, config `sha256:8bca9649e52d948114ccc8164b55b7ab26b64e729893e420114bb5c87bf7c7cc`, fixed alias `birja-recovery-postgres:verified-8bca9649e52d948114ccc8164b55b7ab26b64e729893e420114bb5c87bf7c7cc`, linux/amd64 and `pull_policy=never`. Startup retains explicit `--pull never`; import-only absent-registry contract tests prove zero fallback without deleting shared images.

| Exact command after `bash deploy/tests/` | Exit | Wall seconds |
|---|---:|---:|
|`test-db-operations.sh --backup-restore --recovery-bundle /tmp/birja-backup-test-plan15-fixed-zl4pb12y/recovery.tar`|0|73.507|
|`test-db-operations.sh --roles`|0|31.845|
|`test-db-operations.sh --tls`|0|57.607|
|`test-rollback-db-security.sh --recovery-bundle /tmp/birja-backup-test-plan15-fixed-zl4pb12y/recovery.tar`|0|119.673|

Supplied recovery proves installed launchers, concurrent-writer snapshot consistency, row/money/session equality, invariants, generated identities, FK/index/sequence and encrypted checksum/manifest negatives, staging removal and denied feature-checkout access. Roles proves populated repeatable transfer, actual services/scheduler, valid concurrent0008 and65 denied operations. TLS proves app/scheduler/migrator verified transport plus bad-CA/hostname/plaintext rejection, credential/mount isolation and renewal. Actual v0.3.1 rollback proves retained installer/real-Git legacy routing, recovery-gate negatives, the same installed recovery before/after hardening and after old-image rollback, old-image TLS negatives and preserved0008. Roles/TLS commands retain their own existing fixtures; the two explicitly supplied runners use the same final archive.

Execution evidence: `/tmp/birja-plan15-fixed-package.json`, `/tmp/birja-plan15-replay.json`, `/tmp/birja-plan15-{supplied-recovery,roles,tls,supplied-old-rollback}.log`. The executor hit a usage limit after starting rollback; closeout inspected the completed persisted result (all four exit0), rather than rerunning successful fixtures. Archive size/hash/separate checksum were rechecked during closeout.

## Cleanup and remaining gates

All four finally-cleanup commands returned0. Fresh read-only label-filtered queries on2026-11-07 confirm **zero containers, networks and volumes** for `birja-test`, `birja-ops-test`, `birja-restore-check`, `birja-rollback-test`. No shared cache/images were removed.

Plan15 bounded compatibility/review/evidence criteria pass. Raw vendor HIGH/CRITICAL findings independently keep Plan08 task03 and09/live advancement blocked; no suppression, waiver or pass is claimed. Existing image reports date2026-11-06 and were not rescanned on closeout because image contents did not change. Actual remote CI/provider/timer/production/inbox gates remain later work. No private config/.env/.aws, provider, real authentication/trade/email, live installation/restart, push/PR/merge/release/deploy occurred. Unrelated `.claude/` remains preserved.
