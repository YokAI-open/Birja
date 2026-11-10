# 06-08 task03 T3A — actual image feasibility passed

2026-11-07; source base `e728855`, RED `956d782`. This bounded segment
changes only the two Dockerfiles, backend audit-group metadata/lock and
focused image contracts. T3B consumer/data transition and T3C final
acceptance remain pending. No08 SUMMARY, phase advance, publication,
provider/private configuration or live operation occurred.

Evidence is retained in ignored `.local/phase-06-handoff/t3a-evidence/`
(original `/tmp/birja-t3a/`). `SHA256SUMS.json` authenticates the copied
logs, raw reports, inventories, driver commands and signed APK index.
Copied46-file inventory SHA256:
`9602da5f1b0ee27123271cd47dc13472c56e87d1a144adf3436e5a079bea8549`.
Every copied file was rehashed successfully; source hashes are retained.

## Exact assembled raw scan results

Each actual named target built with `docker build --platform linux/amd64
--target <target> -t <tag> <backend|frontend>`. The three-target driver
`scan-three.py` imports unchanged `deploy/scan-images.py` helpers for
archive/config verification, isolation, command bounds and DB freshness.
It scans saved actual engine IDs, without source/socket mounts or policy
edits. Scanner is pinned Trivy0.76.1
`aquasec/trivy@sha256:2e6c00d711ab4ae41d8a30c2c1fd3bd3b62704c177bb120f95012e939edfb3df`.
Readonly root, cap-drop ALL, no-new-privileges, bounded512MiB tmpfs,
readonly archive, `--severity HIGH,CRITICAL --exit-code 1`; no ignores,
VEX, unfixed suppression, vendor-file/package metadata deletion or SBOM
masking. Required `py3-pip-wheel26.2.2-r2` remains intact.

| Target/tag suffix `:phase06-08` | Raw exit | HIGH | CRITICAL | Seconds |
|---|---:|---:|---:|---:|
| runtime / birja-backend-runtime |0|0|0|12.064|
| test-builder / birja-backend-test |0|0|0|5.071|
| toolchain / birja-node-toolchain |0|0|0|3.561|

Engine identities (Docker29 uses index IDs; config identity separately
verified against archive and raw report):

- Runtime engine `sha256:34a3a3321cb2197dcb5ee599bfb4e182f062d6e6b82fb7661191178b01fbf629`;
  config `sha256:5836d30ac3421fc9d16c53943734e5c1ef4a40fc0aa81feb789830c778219955`;
  archive SHA256 `5a8d1d06ce7ac1764e08b11b3301e8ca838fd9fd79a6df5e2b2236d951caa389`;
  report SHA256 `a604030e3c93b5c593163927313a2b1dded0f605a91f1ce251020b7e14d2a4c6`.
- Test-builder engine `sha256:e7804d7bbd0f3095f588d68309d3b35d38ac27d86fcf2ec60501430605ecb7c1`;
  config `sha256:d997f88545647ac1b13199c159113fbde804b0a3c7ff9ba04de005c1c3946231`;
  archive SHA256 `8ee280cc3a3d0cd6ed6c6fd4098cc944bbcc087fee2bf86db35fb557be5bc4df`;
  report SHA256 `92c3370b2182244a6d208973b7d306295938001c26b5d611aa9fef78767648f0`.
- Node engine `sha256:8cdd4015a6ea589405c5d2b956064851d0368913f70a01d55d4c751af559c709`;
  config `sha256:e48ee6f317d450011ead650f051498593a54338b3e41f901e8e4f4481c317c34`;
  archive SHA256 `f2420d157afd8f35799e5a7813a7c03963fd8e2d1c1595b8c3075e48a9f3c1f3`;
  report SHA256 `eb72a55582847879489cb41e2c3ba7816918ce3bc5ae1ac89e9abddbf9e4cab2`.

All reports use DB UpdatedAt `2026-11-07T12:52:01.765289267Z`,
DownloadedAt `2026-11-07T17:39:19.073695312Z`,
NextUpdate `2026-11-08T12:52:01.765289037Z`. Raw JSON and status retained;
temporary scan archives removed after config/hash proof.

## Signed package and dependency boundaries

Both languages use exact Wolfi base index
`24f549a7fcace88e69b9557941168c74645688ecc4acf7fb6d734a6b74e9019d`.
Python builder/runtime inherit the same installed Python base; no
cross-distribution interpreter/native library copying. Exact packages:
`python-3.14` and `python-3.14-base=3.14.10_git20261104-r0`,
`nodejs-24=24.22.2-r2`. uv remains0.13.5.

The pinned base's configured trusted repository is
`https://apk.cgr.dev/chainguard`, rather than the separate public Wolfi
research index. APK successfully verified the official repository with
the base's shipped keys; no repository override or untrusted flag.
Retained authenticated index `APKINDEX.7bec2991.tar.gz` SHA256
`e4de900fa477777ad3b2f5cc55dcc229510b0963c7602e0e82fc0976499cd7ad`
contains three RSA256 signatures using the shipped Chainguard keys.
`apk-index-proof.log` records signature-verifying update, key SHA256s and
repository; package inventories and production-builder APK database
retain actual installed versions/checksums. The verification index was
fetched after the builds; build logs identify the same trusted repository
and exact packages, without claiming the earlier fetch bytes were captured.

All existing locked non-project distributions, versions, wheel/sdist URLs
and hashes compare equal to `e728855`. Only project audit-group/default
metadata changed. Default groups are dev+audit. Actual uv0.13.5 locked,
offline isolated syncs proved:

| Selection | Installed Linux distributions | Seconds |
|---|---:|---:|
| default |73|0.208|
| --no-dev |60|0.171|
| --no-group audit |49|0.182|
| --no-default-groups |34|0.150|
| --no-default-groups --group dev |49|0.179|

The entire24-distribution audit-exclusive closure, including pip-audit,
pip-api and pip, is absent from actual runtime/test-builder installed
inventories. Actual production-builder offline sync also uses
`--no-default-groups`; runtime has34 and test-builder49 distributions.
Shared dependencies remain intact. Default host `uv sync --locked` and
actual `uv run --locked pip-audit` pass, with no known vulnerabilities.
`groups-status.json` retains complete inventories and closure proof.

## Actual consumers and cleanup

- Focused stdlib contracts: RED2 failures/8passes before implementation;
  GREEN10/10. RED commit retained.
- Test-builder: locked offline sync, imports asyncpg/pydantic-core/uvloop/
  httptools/watchfiles; pytest9.1.1, Alembic1.20.1, ruff0.17.2,
  mypy2.4.0 and uv0.13.5 CLIs pass. Coverage is installed7.17.0.
- Runtime UID1001: same native imports, actual app factory/health OpenAPI,
  real `alembic upgrade head` pass in2.941s.
- Actual test image `pytest tests/test_smoke.py -q`:5passed in0.78s
  (container2.977s), real PostgreSQL/Redis. Fixed `birja-test` Compose
  used absolute file path, `--env-file /dev/null`, explicit synthetic
  environment and finally cleanup. Existing Debian datastores used only
  for feasibility. Zero labeled containers/networks/volumes afterward.
- Actual frontend dev image builds unchanged package-lock via `npm ci`,
  then UID1000 `npm run build` passes (Vite1.25s), Node24.22.2/npm11.21.2.
  Complete npm tar acquisition retains60s/10MiB streaming bounds and the
  existing SHA512. Actual `npm audit --audit-level=high --json` exits0:
  0high/0critical,13moderate/2low. Raw affected dependency paths retained
  in `npm-audit.json`; no lock refresh.
- Initial frontend check imposed a readonly filesystem that prevented
  TypeScript's normal tsbuildinfo output. Retained failure log; corrected
  disposable writable container build passes. Scanner stays readonly.
- The first extra inventory proof omitted activated dependency extras
  and normalized `boolean.py` incorrectly. Corrected proof resolves extras
  and normalization; actual syncs/inventories now match. No source/package
  change was needed.

No unresolved T3A feasibility failure. Wider deployment/Compose/recovery
consumers deliberately remain at prior identities until T3B; full backend,
browser, new datastore transition and final five-image acceptance are T3C
requirements. These three candidate scans do not complete Plan08.

Self-check: all three named images/raw reports and retained evidence files
exist; RED commit exists; contracts10/10, production-builder/runtime
inventory equality and copied evidence hashes pass; no tracked deletion.
