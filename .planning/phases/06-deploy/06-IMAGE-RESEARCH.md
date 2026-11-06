# Phase 06 Plan 08 — Image security attribution research

**Researched:** 2026-11-06. **Confidence:** HIGH for existing-image attribution and registry identities; MEDIUM for remediation outcomes pending candidate scans.

## User Constraints

No Phase 06 CONTEXT exists. Preserve Python 3.14, PostgreSQL major 18, populated data/volume layout, postgres UID 999, verified TLS, actual v0.3.1 rollback and recovery provenance. Research only: no runtime replacement pulls, source/lock/image/CI edits, deployment, provider access, waiver or completion claim. No blanket ignore-unfixed or CVE suppression. [VERIFIED: parent assignment; 06-08-PLAN.md; 06-OPERATIONS-DECISIONS.md]

## Summary

The five existing images fail the unchanged HIGH/CRITICAL Trivy gate. Fresh JSON reproduces the previous counts. Each Debian target has exactly **two findings with listed fixed versions**, both apt-source binaries for CVE-2026-109518; every other Debian finding has no listed fixed version. Updating bases is useful but cannot honestly be promised to achieve zero HIGH/CRITICAL today. Debian explicitly reports multiple affected trixie packages, including PostgreSQL's CRITICAL libxml2 finding. [VERIFIED: fresh JSON listed below; CITED: https://security-tracker.debian.org/tracker/CVE-2026-109518; CITED: https://security-tracker.debian.org/tracker/CVE-2026-6653]

Python aggregate findings originate in **global pip 26.2.2's vendored CycloneDX SBOM**, with matching actual vendor files and an additional copy in ensurepip's wheel. They are not evidence that the application virtualenv contains those standalone distributions. Two important subset distinctions are proven: pip vendors only `pkg_resources` from setuptools, excluding vulnerable `PackageIndex`; pip's msgpack is the pure-Python fallback, excluding the C extension implicated by CVE-2026-114613. urllib3 remains actually present and affected by the vendor version range. Do not dismiss the entire aggregate or update app locks to repair global pip. [VERIFIED: image-only Python inspection; runtime.json; CITED: https://pip.pypa.io/en/stable/development/vendoring-policy/; CITED: https://github.com/pypa/setuptools/security/advisories/GHSA-5rjg-fvgr-3xxf; CITED: https://github.com/msgpack/msgpack-python/security/advisories/GHSA-j586-36cw-2gc2]

**Primary recommendation:** refresh only the verified same-major candidates below, inspect their actual contents and rescan, then address the residual component-specific findings. Preserve strict failure until all required findings are fixed or a separately reviewed, evidence-based not-affected disposition is accepted; this research creates no such policy exception.

## Project Constraints (from AGENTS.md)

- Read full CLAUDE.md and shared planning artifacts; continue existing phase history. Use GSD adapter and preserve checkpoints, separate review and verification. [VERIFIED: AGENTS.md]
- Respect money precision, least privilege, TLS, non-root containers, pinned/scanned images, committed lockfiles and CI audit gates. Never install pip dependencies directly into the project. [VERIFIED: CLAUDE.md]
- No push/merge without explicit approval; preserve unrelated edits and `.claude/`; no reset/clean/stage-all. This researcher makes no commits, per delegated scope. [VERIFIED: AGENTS.md; CLAUDE.md; parent assignment]
- This operational image slice has no UI work. Full isolated app/operations checks, independent review and exact recovery-artifact replay remain required for Plan 08 closeout. [VERIFIED: 06-08-PLAN.md]

## Architectural Responsibility Map

| Capability | Owner | Consequence |
|---|---|---|
| Debian packages, global pip/ensurepip | Base-image/build pipeline | Fix actual image contents; application lock audits do not cover these inventories. [VERIFIED: Dockerfiles; fresh JSON] |
| Bundled npm dependencies | Node image/npm distribution | Update image/toolchain distribution; frontend package-lock edits do not change global npm. [VERIFIED: node.json paths] |
| Embedded Go stdlib | PostgreSQL image's gosu executable | Assess binary reachability and vendor policy; no application Go dependency exists in this attribution. [VERIFIED: postgres.json target] |
| Scan enforcement/provenance | CI and recovery tooling | Scan exact identities; maintain recovery/old-image replay evidence after any image change. [VERIFIED: 06-08-PLAN.md] |

## Reproducible scan evidence

Existing official scanner: `aquasec/trivy@sha256:2e6c00d711ab4ae41d8a30c2c1fd3bd3b62704c177bb120f95012e939edfb3df`, version **0.76.1**. No replacement scanner or package installed. Fresh DB metadata: schema 2, UpdatedAt `2026-11-06T12:55:02.577403897Z`, DownloadedAt `2026-11-06T13:37:51.943374451Z`, NextUpdate `2026-11-07T12:55:02.577403513Z`. [VERIFIED: JSON Trivy.Version; cache/db/metadata.json]

Public image/package-only reports: `/tmp/birja-image-research-5yhyvf54/{runtime,builder,postgres,redis,node}.json` and corresponding `.log`. Exact driver: `/tmp/birja-image-research.py`; registry-only driver: `/tmp/birja-registry-research.py`. These temporary files are reproducibility aids, not committed durable artifacts. Prior `/tmp/birja-plan08-image-scans.json` holds timing results, not vulnerability JSON. [VERIFIED: filesystem reads and executed commands]

Each image was saved using `docker image save -o <temp>/<name>.tar <image>` and scanned with:

```text
docker run --rm --read-only --tmpfs /tmp:rw,noexec,nosuid,size=512m \
  --cap-drop=ALL --security-opt=no-new-privileges \
  --mount type=bind,src=<image-archive>,dst=/scan/image.tar,readonly \
  --mount type=bind,src=<private-cache>,dst=/cache \
  aquasec/trivy@sha256:2e6c00d711ab4ae41d8a30c2c1fd3bd3b62704c177bb120f95012e939edfb3df \
  image --cache-dir /cache --input /scan/image.tar --scanners vuln \
  --severity HIGH,CRITICAL --exit-code 1 --timeout 5m --format json
```

No source tree, private configuration or Docker socket was mounted into scanner containers. Generated archives were removed after each scan; reports and public DB cache remain under the temporary research directory. Initial attempts under `/tmp/birja-image-research-ft3_b47c` failed **before scanning** because read-only `/tmp` prevented DB download; their exit 1 is not vulnerability evidence. The corrected command above supplied private tmpfs and produced valid JSON for all five images. [VERIFIED: executed driver; first-attempt logs; valid fresh JSON]

| Image | Debian H/C | Debian listed fix / no listed fix | Other H/C | Exit | Scan seconds |
|---|---:|---:|---:|---:|---:|
| birja-backend-runtime:phase06-08 | 51/0 | 2 / 49 | Python 5/0 | 1 | 12.636 |
| birja-backend-test:phase05-07 | 51/0 | 2 / 49 | Python 5/0 | 1 | 2.228 |
| postgres:18.6-trixie | 68/1 | 2 / 67 | gosu Go 25/1 | 1 | 3.601 |
| redis:8.8.3-trixie | 50/0 | 2 / 48 | — | 1 | 1.332 |
| node:24.22.1-trixie-slim | 50/0 | 2 / 48 | npm 6/0 | 1 | 2.125 |

Counts are package-CVE finding rows, not unique CVEs. `Status: fixed` means a fixed version is available, **not that the installed image is fixed**. [VERIFIED: JSON InstalledVersion, FixedVersion and Status]

| Report | SHA-256 |
|---|---|
| runtime.json | `25fe096c42a290d01372119d11cf6effdafc758fcbc68d413d749669436b4738` |
| builder.json | `5b54fd322d7b7deb627b173c172451820ceaaa9f0b299da587c6ae0c475b7e73` |
| postgres.json | `03622207f3f7480f0b375e202abe55fad88bc597ae1a9c8542c277ad5b6226e3` |
| redis.json | `931292480730bf3b677f7ea588436f321c38bba373dd729080e0b2541bce657f` |
| node.json | `a979060e9ec0a6cbf1002f5d42cca8070bba9284153c24baa5fe775bab54a6b7` |

Hashes computed from report bytes with Python hashlib. [VERIFIED: local hash command]

## Exact package, file and vendor attribution

### Python: global pip vendor SBOM, not application requirements

Image reads used ephemeral `docker run --rm --network none --read-only --cap-drop=ALL --security-opt=no-new-privileges --entrypoint /usr/local/bin/python <existing-image> -c <inspection>`, without mounts. `/usr/local/bin/python` is essential: the default `python` resolves to `/opt/venv/bin/python`, where global pip cannot be imported. One attempted import with the venv interpreter failed; the corrected global interpreter printed `pip._vendor.msgpack.fallback`. [VERIFIED: image inspection command/results]

Exact distributed origins:

- `/usr/local/lib/python3.14/site-packages/pip/_vendor/bom.cdx.json`: CycloneDX components msgpack 1.1.2, setuptools 70.3.0, urllib3 2.7.0. Matching `/usr/local/lib/python3.14/site-packages/pip/_vendor/vendor.txt` and actual `msgpack/`, `pkg_resources/`, `urllib3/`. [VERIFIED: image file reads]
- `/usr/local/lib/python3.14/ensurepip/_bundled/pip-26.2.2-py3-none-any.whl` contains `pip/_vendor/bom.cdx.json` and matching `vendor.txt`; any complete pip cleanup must account for this second distribution. [VERIFIED: zipfile member and file reads]
- JSON aggregate omits PkgPath but contains BOMRef `pkg:pypi/<name>@<version>` and the same Python-base layer digest `sha256:2cb672340c81d54eae68bd73635134ad5ede9da3664d3d638e94bae1666adae8`. All app METADATA targets report zero qualifying vulnerabilities in these scans. [VERIFIED: runtime.json; builder.json]

| Finding | Vendor finding / actual image evidence | Disposition for planning |
|---|---|---|
| setuptools CVE-2025-47273, 70.3.0 → 78.1.1 | Vendor identifies `setuptools.package_index.PackageIndex`; pip README says setuptools is stripped to pkg_resources. No `package_index.py` under global vendor directory or ensurepip wheel. [CITED: https://github.com/pypa/setuptools/security/advisories/GHSA-5rjg-fvgr-3xxf; VERIFIED: actual README and file inventory] | Vulnerable component absent from this pip subset; strong **not-affected evidence**, subject to independent review. Still reported by scanner; no ignore entry created. |
| msgpack CVE-2026-114613, 1.1.2 → 1.2.3 | Vendor advisory explicitly concerns C extension; image contains no msgpack `.so`, actual Unpacker module is `pip._vendor.msgpack.fallback`. Vendor advisory lists affected =1.2.2 while scanner broadens range to <1.2.3. [CITED: https://github.com/msgpack/msgpack-python/security/advisories/GHSA-j586-36cw-2gc2; VERIFIED: actual file inventory, runtime import, JSON] | Proven C-extension absence supports **not affected by stated C-extension flaw**; flag range discrepancy to reviewer/vendor rather than claim image clean. |
| msgpack GHSA-6v7p-g79w-8964, 1.1.2 → 1.2.1 | Vendor describes SEGV after reusing Unpacker following an error; upstream patch/changelog concern C code, but this research did not perform a full symbol/patch comparison for this separate advisory. [CITED: https://github.com/msgpack/msgpack-python/security/advisories/GHSA-6v7p-g79w-8964; CITED: https://github.com/msgpack/msgpack-python/blob/main/CHANGELOG.md] | **Unresolved**, pure-Python evidence alone does not approve disposition of this separate advisory. |
| urllib3 CVE-2026-97687 / CVE-2026-97689, 2.7.0 → 2.8.0 | Actual vendored code exists; vendor describes HTTPS-proxy TLS configuration confusion and unbounded chunk-size-line buffering. [CITED: https://github.com/urllib3/urllib3/security/advisories/GHSA-8988-9cw3-xx77; CITED: https://github.com/urllib3/urllib3/security/advisories/GHSA-vxq7-64xx-v4gw; VERIFIED: image vendor files] | **Affected version distributed; fix or remove unneeded complete tool distribution**, not an application-lock update. Runtime reachability does not by itself make distribution-wide scan pass. |

Prefer a supported updated base whose bundled toolchain fixes the findings. If pip is unnecessary in a uv-built final runtime, complete removal of global pip/entrypoints/metadata and ensurepip distribution is a narrowly scoped alternative for review and smoke verification; do not delete just the SBOM, edit vendor versions, partially debundle pip, or delete library files opportunistically. Builder retention/removal must preserve actual uv build/test workflows. This is a proposed implementation choice, not an implemented cleanup. [VERIFIED: backend/Dockerfile uses uv and copies prepared venv; CITED: https://pip.pypa.io/en/stable/development/vendoring-policy/]

### Node: npm's global distribution

Exact scanner paths are `usr/local/lib/node_modules/npm/node_modules/brace-expansion/package.json` and `usr/local/lib/node_modules/npm/node_modules/undici/package.json`; all six findings belong to these global npm packages, not the frontend's lockfile. [VERIFIED: node.json PkgPath]

| Package | Findings | Minimum same-major package fix |
|---|---|---|
| brace-expansion 5.0.9 | CVE-2026-102276 / CVE-2026-102278 | 5.0.11 covers both (first fixed 5.0.10, second 5.0.11). [VERIFIED: node.json; vendor advisory links https://github.com/juliangruber/brace-expansion/security/advisories/GHSA-6j4f-fj2g-mc7p and https://github.com/juliangruber/brace-expansion/security/advisories/GHSA-qhr7-859c-m2p7 recorded in JSON; advisory contents not independently fetched in this bounded pass] |
| undici 6.28.0 | CVE-2026-109383 / 109869 / 87018 / 19534 | 6.29.1 covers all four; 6.28.1 covers only 19534. [VERIFIED: node.json; CITED: https://github.com/nodejs/undici/releases; CITED: https://github.com/nodejs/undici/security/advisories/GHSA-2m5v-pch6-74hx; CITED: https://github.com/nodejs/undici/security/advisories/GHSA-rfgv-xxqx-mfg5] |

Use the updated official Node 24 image first and inspect its bundled npm versions. Do not assume Node's internal undici version is npm's independent nested undici, or patch npm by changing frontend dependencies. [VERIFIED: existing nested package paths; remediation recommendation]

### PostgreSQL: gosu and Debian

JSON target `usr/local/bin/gosu`, gobinary stdlib Go 1.24.6, contributes 26 rows (25 HIGH, one CRITICAL). CRITICAL CVE-2025-68121 / GO-2026-4337 concerns `crypto/tls` session resumption after CA configuration mutation; official fixes are Go 1.24.13 / 1.25.7 / 1.26.0-rc.3. This is gosu's compiled stdlib, not PostgreSQL's native TLS implementation or the backend's database SSLContext. [VERIFIED: postgres.json; CITED: https://pkg.go.dev/vuln/GO-2026-4337]

gosu's vendor says it does not rebuild for unused Go functionality and requires its govulncheck wrapper before declaring a binary affected. Current official PostgreSQL 18 trixie Dockerfile still sets gosu 1.19. Even gosu 1.20 release notes say built with Go 1.24.6, so bumping gosu's version blindly cannot prove this scanner finding fixed. This pass did not install/run govulncheck; **all 26 reachability dispositions remain unapproved**, despite the vendor's general explanation. [CITED: https://raw.githubusercontent.com/tianon/gosu/master/SECURITY.md; CITED: https://github.com/tianon/gosu/releases; CITED: https://raw.githubusercontent.com/docker-library/postgres/e00e1bd34ec5c8a8e7ad89b273b3d42efaf6d5bc/18/trixie/Dockerfile]

### Debian: real fixes versus no-dsa/deferred findings

OS findings originate in Debian package inventory (`debian 13.7`), not app manifests. Debian source-package classification can repeat one CVE across several binary packages; this is why 51 rows are not 51 independent defects. [VERIFIED: fresh JSON targets and package repetition; CITED: Debian tracker pages below]

| Source / installed binary family | CVEs | Vendor disposition today |
|---|---|---|
| apt / apt, libapt-pkg7.0 3.0.3 | CVE-2026-109518 | **Fix available** trixie-security 3.0.4; preserve authenticated package retrieval. [CITED: https://security-tracker.debian.org/tracker/CVE-2026-109518] |
| libxml2 2.12.7+dfsg+really2.9.14-2.1+deb13u3, PG only | CRITICAL CVE-2026-6653 | trixie **vulnerable**, no-dsa minor; forky/sid fixed. Reverted `really2.9.14` matters: apparent 2.12.7 prefix is not proof of an upstream fix. [CITED: https://security-tracker.debian.org/tracker/CVE-2026-6653] |
| util-linux 2.41.5-0+deb13u1 / bsdutils, mount, login, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1 | CVE-2026-76642, 78408, 78409, 78410 | All trixie vulnerable; source-specific fixes in unstable, no fixed trixie version listed. Bookworm is not affected for 76642/78408/78409 but remains vulnerable for 78410. Downgrading distro does not establish a clean image. [CITED: https://security-tracker.debian.org/tracker/CVE-2026-76642; CITED: https://security-tracker.debian.org/tracker/CVE-2026-78408; CITED: https://security-tracker.debian.org/tracker/CVE-2026-78409; CITED: https://security-tracker.debian.org/tracker/CVE-2026-78410] |
| acl / libacl1 2.3.2-2+b1 | CVE-2026-54369 | trixie vulnerable/no-dsa; vendor plans point-release fix, new ABI complicates individual backports. [CITED: https://security-tracker.debian.org/tracker/CVE-2026-54369] |
| systemd / libsystemd0, libudev1 257.13-1~deb13u1 | CVE-2026-16742 | Source vulnerable/no-dsa; flaw concerns systemd-homed. Runtime `/usr/lib/systemd/systemd-homed` absent, suggesting a possible precise binary-subpackage disposition, **not yet established for all images**. [CITED: https://security-tracker.debian.org/tracker/CVE-2026-16742; VERIFIED: runtime path check] |
| sqlite3 / libsqlite3-0 3.46.1-7+deb13u2 | CVE-2026-119373, 119374, 119379 | trixie vulnerable/no-dsa, fixed in sid 3.54.1-1; FTS5/session functionality conditions need actual build/use analysis before not-affected claim. [CITED: https://security-tracker.debian.org/tracker/CVE-2026-119373; CITED: https://security-tracker.debian.org/tracker/CVE-2026-119374; CITED: https://security-tracker.debian.org/tracker/CVE-2026-119379] |
| ncurses 6.5+20250216-2 | CVE-2025-69720 | trixie vulnerable/no-dsa; flaw in infocmp CLI. Runtime **does contain `/usr/bin/infocmp`**; cannot dismiss entire family as library-only. [CITED: https://security-tracker.debian.org/tracker/CVE-2025-69720; VERIFIED: runtime path check] |
| zlib / zlib1g 1:1.3.dfsg+really1.3.1-1+b1 | CVE-2026-76844, 85091 | trixie vulnerable; sid fixed 1:1.3.dfsg+really1.3.2-4. 76844's scanner title incorrectly mentions webpack-dev-middleware; Debian description identifies zlib gz_write heap overflow, so title alone is misleading. [CITED: https://security-tracker.debian.org/tracker/CVE-2026-76844; CITED: https://security-tracker.debian.org/tracker/CVE-2026-85091; VERIFIED: JSON title] |
| perl 5.40.1-6+deb13u1 | CVE-2026-9538 | trixie vulnerable; scanner fix_deferred; Archive::Tar code subset/reachability not resolved here. [CITED: https://security-tracker.debian.org/tracker/CVE-2026-9538; VERIFIED: JSON] |

PG additionally reports gnupg-family CVE-2026-24882 and seven further libxml2 HIGH CVEs (74860, 86138, 86139, 86140, 86142, 86143, 86144), all with no listed fix. These remain **unresolved vendor/package dispositions**; no blanket classification is inferred from the one researched libxml2 CVE. Exact rows, versions, references and fingerprints remain in postgres.json. [VERIFIED: postgres.json]

`no-dsa`, `fix_deferred`, lower vendor urgency and difficult exploit prerequisites are not equivalent to fixed or not affected. Keep these distinctions in any CI-policy proposal; do not relabel them as false positives. [VERIFIED: tracker statuses and descriptions above; prescribed gate interpretation]

## Standard Stack: verified same-major candidate pins

Official-images manifests advertise Python **3.14.10-slim-trixie**, PostgreSQL **18.6-trixie** (new rebuild of same tag), Redis **8.8.4-trixie** (minimal 8.8 patch rather than 8.10 minor), Node **24.22.2-trixie-slim**. All use Debian trixie/glibc. [CITED: https://raw.githubusercontent.com/docker-library/official-images/master/library/python; CITED: https://raw.githubusercontent.com/docker-library/official-images/master/library/postgres; CITED: https://raw.githubusercontent.com/docker-library/official-images/master/library/redis; CITED: https://raw.githubusercontent.com/docker-library/official-images/master/library/node]

Registry identities below were verified through public `auth.docker.io` pull-scope token → `registry-1.docker.io/v2/library/<repo>/manifests/<tag>` → selected linux/amd64 manifest → config blob. Manifest SHA-256 calculated from response bytes. No image layer was pulled and no token printed. These are **candidate identities, not security-pass attestations**. [VERIFIED: /tmp/birja-registry-research.py output]

| Candidate | Multi-platform index digest | linux/amd64 manifest digest | Config creation UTC |
|---|---|---|---|
| python:3.14.10-slim-trixie | `sha256:af8a5aa14780025dbfbcfbc81bd8a91ebd87711dd5b0f48ed71090949dd7cb1d` | `sha256:ac25e5afbfdb4a94ff99cc24b0345719210133144481480bcba6085efa36a341` | 2026-11-05T07:58:35.457948388Z |
| postgres:18.6-trixie | `sha256:bd5dfa494a5a259704365813dbfa5fa6b3e69be7348d43b547f540c730478583` | `sha256:e923a22ac074261dd73970c57edf659475bf0497cb9456f17d98ed7cdd3ca913` | 2026-11-05T07:29:44.528257177Z |
| redis:8.8.4-trixie | `sha256:a008e2cb5579f3616b29bd9e9913a25f16ec09ae2f56ddab524664663b581228` | `sha256:f00c54d05acbb9f6b9ce47e3dbd03d7ed16d94c274470be17acd6b0112734162` | 2026-11-05T07:38:44.991282091Z |
| node:24.22.2-trixie-slim | `sha256:0820eaa85e07d0490446dd01d14707e17e6108a36988cf374899cd057eb3812d` | `sha256:947528b072c170d980592b851c802155d84dcad60d3f550b8a0451b84d65dabd` | 2026-11-05T07:42:08.882162295Z |

Use `repository:version@sha256:<index>` for a reviewed portable multi-platform pin or the explicit amd64 manifest with the architecture constraint. Do not confuse config/image IDs with registry manifest digests. Existing cached PG/Redis/Node configs were created Oct 21, so their tags are stale relative to Nov 5 candidates. [VERIFIED: docker image inspect; registry query]

| Existing local image | Config/image ID |
|---|---|
| backend runtime | `sha256:c987258161bf419e3c31e697bf473a71cf6cbc9c7bfc8136940be3fba57c983f` |
| backend test-builder | `sha256:818bf5a068fdcf3c112b9e41583378b40d6f90fc79b60ca51cd0f52c708997d5` |
| postgres:18.6-trixie | `sha256:edb0c08dc33befd0262ab3b5cf1c4f3f8cfd8b09e88c05b45adee29d6761ddb6` |
| redis:8.8.3-trixie | `sha256:418e397fd48d66e450af13baab123397f2d2580b07ef310c3a5dbe96c3d731f1` |
| node:24.22.1-trixie-slim | `sha256:43b9ba1142b8dcf33fa8f922ca1be85714adc444e0586c7cf7726daaeabc1bea` |

Existing IDs verified with `docker image inspect ... --format '{{.Id}} {{.Created}} {{json .RepoDigests}}'`; preserve old recovery identity rather than overwriting its provenance. [VERIFIED: inspection output; 06-08-PLAN.md]

## Bounded remediation proposal and independent review scope

1. **Candidate contents first:** after parent review/authorized implementation, pull the four exact candidates, inspect apt/libapt, bundled pip/ensurepip, npm nested versions, gosu metadata; scan archive JSON with the same policy and fresh DB. Compare residual IDs/paths rather than only totals. These candidate contents are unmeasured in this report.
2. **Minimal source changes:** `backend/Dockerfile` (both Python FROM pins and only justified complete build-tool cleanup); `frontend/Dockerfile` plus actual production build Dockerfile/CI Node image references; existing `docker-compose.yml`, `docker-compose.test.yml`, `docker-compose.prod.yml`, `docker-compose.ops-test.yml` image pins and exact image-identity/provenance allowlists in deployment test/recovery tooling. Locate all references with `rg -n 'python:|postgres:|redis:|node:|sha256:|image_id' backend frontend deploy docker-compose*.yml .github/workflows` before editing. Do not change application locks without an independent application audit finding. [VERIFIED: source Dockerfiles and Compose references; proposed bounded task]
3. **Target remaining findings:** prefer supported distro fixes. If no candidate passes, do not copy unstable libraries into trixie, force-remove essential packages, rebuild PostgreSQL without XML, or switch populated PG to Alpine/musl simply to satisfy scan counts. Those become separately scoped compatibility/maintenance decisions. Reachability review can prove a particular finding inapplicable, but the current strict scanner will still fail until an explicitly agreed enforcement mechanism exists. [VERIFIED: vendor statuses above; project preservation constraints]
4. **CI enforcement:** add the pinned scanner to the existing required image job, covering built backend runtime/test-builder and selected PostgreSQL/Redis/Node identities. Fail on HIGH/CRITICAL and scanner/DB errors; preserve JSON output and scanner/DB/image identities. Add meaningful CI contract assertions in `deploy/tests/test-ci-ops.py` or an image-specific existing test location to prevent silently omitted targets/fail-open flags; ensure `ci-pass` still depends on image job. No `--ignore-unfixed`, ignorefile, VEX override, severity downgrade or waiver is authorized by this report. [VERIFIED: current CI lacks scanner step per 06-LOCAL-GATES.md; proposed task]
5. **Focused verification:** rebuild affected stages, scan exact produced images, run in-image non-root/import/migration CLI smoke, unchanged locked audits, frontend build and isolated affected integration tests. PG identity changes require serial populated PG18 restore/roles/TLS and actual v0.3.1 compatibility replay; regenerate final recovery artifact only after all necessary fixes, then replay that exact artifact and record its hash. Parent still owns the pending final-artifact replay after source-review fixes. [VERIFIED: 06-08-PLAN.md; parent assignment]
6. **Independent review:** check same-major/glibc/UID/volume preservation, image digest type/platform, legitimate package cleanup versus scanner-evidence deletion, all residual vendor dispositions, CI target completeness/failure propagation, and recovery/old-image identity provenance. Keep Plan 08 incomplete and do not advance 09 while the required gate fails. [VERIFIED: plan acceptance criteria; proposed review scope]

## Don't Hand-Roll / Common Pitfalls

- Do not edit vendor SBOM/version text to hide a match; remove an unnecessary entire tool distribution or use an upstream fixed distribution. [CITED: pip vendoring policy above; integrity recommendation]
- Do not treat a clean application pip/npm audit as a clean base image. Paths prove separate inventories here. [VERIFIED: fresh JSON and Dockerfiles]
- Do not count exit 1 from DB initialization as a completed vulnerability scan. Require valid JSON and actual Results. [VERIFIED: initial and corrected scanner executions]
- Do not infer a fix from tag text or a newer gosu release. Record actual manifest/config and compiler/package versions. [VERIFIED: registry identities; gosu release/compiler evidence]
- No new external package installation is recommended by this bounded proposal; package-legitimacy install audit is therefore not applicable. Any future govulncheck acquisition must have its own authoritative provenance and bounded execution review. [VERIFIED: proposed tasks and no-install research scope]

## Runtime State Inventory

| Category | Evidence / action |
|---|---|
| Stored data | Production explicitly uninspected. Preserve populated PostgreSQL major18/data layout and validate only isolated copies under existing authorization; no migration inferred from image refresh. [VERIFIED: assignment; plan] |
| Live service config | Uninspected by design; image-only operations did not inspect running app/DB containers. Future deployed identity changes remain separately gated. [VERIFIED: executed command scope] |
| OS-registered state | No service/timer installation or registration touched. [VERIFIED: executed command scope] |
| Secrets/env vars | No `.env`, `.aws`, private config or credential files read; public registry token remained internal to request script. [VERIFIED: executed command scope] |
| Build artifacts | Five cached scanned images have IDs above; eventual refresh invalidates image-specific test/recovery evidence. Existing old rollback image remains untouched. [VERIFIED: inspection; plan] |

## Validation Architecture

Use unchanged scanner command above for the immediate fail-closed gate; `/tmp/birja-image-research.py` is a research driver, not proposed production CI code. Existing app/ops frameworks and commands remain as documented in `06-VALIDATION.md` and `06-08-PLAN.md`; no new test framework needed. Required additions are CI scanner-target/failure contracts and focused complete-tool-cleanup smoke only if that cleanup is implemented. Scan failures are presently expected and block closeout. [VERIFIED: plan, source and scan results]

## Security Domain

This slice concerns software supply-chain integrity, vulnerable distributed components, scanner/DB error handling, and CI enforcement. Preserve ASVS 5.0 L1 phase review, privileged infrastructure boundaries and secret handling from the existing phase threat model. Older ASVS V2/V3/V4 category numbering should not be copied into an ASVS5 compliance assertion. No whole-app certification or live security verification is claimed. [VERIFIED: 06-08-PLAN.md threat model; bounded assessment scope]

## Environment Availability

Docker image inspection/ephemeral image-only commands and pinned scanner available with reviewed escalation; sandbox denied direct Docker socket access initially. Ordinary network Python registry queries failed DNS in sandbox, then succeeded under reviewed escalation. Context7 tools and `ctx7` CLI were absent; official web/vendor sources used. No global scanner/tool/package installation occurred. [VERIFIED: tool outputs]

## Open Questions and blocking condition

- Will the exact candidates ship apt3.0.4, fixed pip-vendored urllib3 and fixed npm packages? **Not measured**; candidates not pulled. Creation after an advisory is not proof of inclusion.
- Can the separate msgpack Unpacker advisory, all 26 gosu findings and repeated OS binary-subpackage matches be precisely shown not affected? **Not yet**; general vendor statements do not establish each result.
- Several trixie source packages are explicitly vulnerable with no stable fix. Under the current zero-HIGH/CRITICAL policy, **no bounded same-major tag update is proven sufficient**. Minimum safe choices are to retain the block while vendor fixes arrive, or separately scope a supported rebuilt/minimized image solution with compatibility/security review. A policy revision or accepted VEX/disposition mechanism requires an explicit decision and independent evidence; it is not silently invented here.

The above are measured gaps, not `[ASSUMED]` claims. There are no new locked decisions in this report. [VERIFIED: evidence and research limits documented above]

## Metadata

Source hierarchy: direct image/registry evidence and official vendor/distro documentation; no community source used for a disposition. Standard candidate identity confidence HIGH; existing-file attribution HIGH; residual not-affected assessments MEDIUM or explicitly unresolved; zero-HIGH remediation outcome LOW until rescanned. Research valid until the next image/DB/advisory update; reverify registry/DB identities at execution. This report changes no source, pins, locks, CI, runtime, state or completion status. [VERIFIED: scoped research execution]

## Authorized candidate validation — measured follow-up

**Result: ordinary same-major patch/rebuild refresh fixes apt/libapt only; all five actual candidate scan targets still fail HIGH/CRITICAL.** This follow-up supersedes the earlier candidate-unpulled/unmeasured statements above. It does not adopt new source pins or change policy. [VERIFIED: candidate JSON and multiset comparison below]

Parent explicitly authorized four exact public candidate pulls, temporary backend builds changing only both Python FROM lines, version inspection and scans. Immediately before pulling, the registry-only query reverified all four index/amd64 identities above unchanged. Commands pulled `python@sha256:ac25e5afbfdb4a94ff99cc24b0345719210133144481480bcba6085efa36a341`, `postgres@sha256:e923a22ac074261dd73970c57edf659475bf0497cb9456f17d98ed7cdd3ca913`, `redis@sha256:f00c54d05acbb9f6b9ce47e3dbd03d7ed16d94c274470be17acd6b0112734162`, and `node@sha256:947528b072c170d980592b851c802155d84dcad60d3f550b8a0451b84d65dabd` using `docker pull --platform linux/amd64 <digest-ref>`. No tag retargeting or replacement fallback occurred. [VERIFIED: /tmp/birja-candidate-research.py; pull logs; registry script output]

Build context remained `/home/YokaiExchange/backend`. Read `backend/.dockerignore`: excludes `.venv`, `.env`, `.env.*`, caches and coverage artifacts; bounded filename audit found no additional key/credential/private files. Temporary `/tmp/birja-candidate-research-4n5r71mi/Dockerfile` replaces exactly two occurrences of `FROM python:3.14.9-slim-trixie` with the verified candidate Python digest, preserving uv 0.13.5 and committed locked dependency resolution. Dockerfile SHA256 `d89a305180e56bceba0bad4bf378c4da1cbd820bc31567eddf89be794d9b15ca`. Builds used:

```text
docker build --platform linux/amd64 --target runtime \
  -f /tmp/birja-candidate-research-4n5r71mi/Dockerfile \
  -t birja-image-research-runtime:phase06-python31410 /home/YokaiExchange/backend
docker build --platform linux/amd64 --target test-builder \
  -f /tmp/birja-candidate-research-4n5r71mi/Dockerfile \
  -t birja-image-research-builder:phase06-python31410 /home/YokaiExchange/backend
```

Both builds exit0: runtime12.893s, test-builder13.931s. These are image build checks, not runtime/app/DB test results. No package cleanup or app lock update was performed. [VERIFIED: build-runtime.log; build-builder.log; temporary Dockerfile construction]

Version inspection used network-disabled, read-only, cap-drop-ALL ephemeral containers with no mounts; script `/tmp/birja-candidate-versions.py`, outputs `versions-{python,postgres,redis,node}.txt` under the same temporary directory. [VERIFIED: executed inspection]

| Candidate | Actual public versions/components |
|---|---|
| Python | Python3.14.10; global pip26.2.2; ensurepip `pip-26.2.2-py3-none-any.whl`; vendor.txt still msgpack1.1.2, setuptools70.3.0, urllib3 2.7.0. [VERIFIED: versions-python.txt] |
| PostgreSQL | PostgreSQL18.6 Debian18.6-1.pgdg13+2; gosu1.19 Go1.24.6; postgres UID/GID999; apt/libapt3.0.4; libxml2 still2.12.7+dfsg+really2.9.14-2.1+deb13u3. [VERIFIED: versions-postgres.txt] |
| Redis | Redis8.8.4, jemalloc5.3.0; apt/libapt3.0.4. [VERIFIED: versions-redis.txt] |
| Node | Node24.22.2; npm11.19.1; npm nested undici still6.28.0 and brace-expansion still5.0.9. [VERIFIED: versions-node.txt] |

Scanner command, pinned scanner image and severity/error policy are identical to the earlier successful JSON run. Reused existing private cache `/tmp/birja-image-research-5yhyvf54/cache`; DB UpdatedAt/DownloadedAt/NextUpdate remain exactly as recorded above, allowing comparison without DB drift. Scan inputs were the two **actually built backend candidate images**, PostgreSQL, Redis and Node candidates; Python base alone was not substituted for backend scans. [VERIFIED: candidate driver and cache metadata]

| Actual candidate scan target | Debian HIGH / CRITICAL | Other HIGH / CRITICAL | Debian rows with listed fix | Exit | Seconds |
|---|---:|---:|---:|---:|---:|
| birja-image-research-runtime:phase06-python31410 |49 /0|Python5 /0|0|1|2.408|
| birja-image-research-builder:phase06-python31410 |49 /0|Python5 /0|0|1|2.527|
| postgres candidate digest |66 /1|gosu25 /1|0|1|3.948|
| redis candidate digest |48 /0|—|0|1|1.413|
| node candidate digest |48 /0|npm6 /0|0|1|2.208|

Exact comparison used a multiset of `(Result.Type, PkgName, VulnerabilityID, InstalledVersion)` across all finding rows. In **each** target, the only removed rows are `apt / CVE-2026-109518 /3.0.3` and `libapt-pkg7.0 / CVE-2026-109518 /3.0.3`; **no rows added**. Therefore every other earlier exact finding/path/version persists. Listed-fix residual non-OS totals remain Python5, gosu26 and npm6; no claim that the refresh clears all fixable findings is justified. [VERIFIED: Python collections.Counter comparison of original/candidate JSON]

Exact remaining shared Debian CVE set: `CVE-2025-69720`, `CVE-2026-119373`, `CVE-2026-119374`, `CVE-2026-119379`, `CVE-2026-16742`, `CVE-2026-54369`, `CVE-2026-76642`, `CVE-2026-76844`, `CVE-2026-78408`, `CVE-2026-78409`, `CVE-2026-78410`, `CVE-2026-85091`, `CVE-2026-9538`. PostgreSQL additionally retains `CVE-2026-24882`, `CVE-2026-6653`, `CVE-2026-74860`, `CVE-2026-86138`, `CVE-2026-86139`, `CVE-2026-86140`, `CVE-2026-86142`, `CVE-2026-86143`, `CVE-2026-86144`. Exact binary-package attribution and the unchanged non-OS findings are in the earlier tables and candidate JSON. [VERIFIED: candidate JSON result sets]

| Candidate report in `/tmp/birja-candidate-research-4n5r71mi/` | SHA256 |
|---|---|
| runtime.json | `1eead28e8fe50e58cd242988bb8850d52ea077262a74f7efc4cd0b672fecc2ac` |
| builder.json | `1b15d90315bd9ef97fd5382816dc062279e044be541d666ea77c6a4753e315bc` |
| postgres.json | `2b7863fc1e35dd68461755bce08e4e0db2e385459f5b9cf13057c2a7a0be2147` |
| redis.json | `4b74999f7b324ba6c0f0008bf0fa724db5e95b9f06a401bc3eb2c573a103dc09` |
| node.json | `74753cb4d378beddf78d503f3871a456cfe087aafc3e144e5c8095a263ed0ecd` |

Temporary research runtime inspection identity `sha256:93eb5781f642e5d125d8649ca353e089c6398e58d083446f677aba0a4956ce9b`; builder `sha256:282d02b93aa23006f03d05a7a7fbaac0a3e96bbd631e7d45214550e9505d8501`. Full `docker image inspect` outputs, creation times and RepoDigests retained in `identities.txt`. After all pulls/builds/scans, reinspection of the five original tags matched **all five earlier identities exactly**; no prior recovery image or artifact was changed. Generated scan archives were removed; research images and public report/cache files remain for review. [VERIFIED: identities.txt; original-tag postcheck; driver cleanup]

**Decision support:** applying these candidate pins is a real apt security improvement but does not satisfy Plan08. A further bounded remediation plan must separately address distributed pip/npm toolchains, gosu exact dispositions and unfixed Debian components; strict zero-HIGH/CRITICAL remains demonstrably blocked. No cleanup, waiver, VEX, ignorefile, policy change, service/DB change or phase advancement is authorized or implemented by this validation. [VERIFIED: measured results and assignment scope]
