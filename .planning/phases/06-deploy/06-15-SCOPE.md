# 06-15 image refresh and CI prerequisite scope

Additive to existing Phase06: 06-07/14 are complete; 06-08 tasks01/02 are implemented and task03 is blocked. The independently reviewed source through c8e23fd has zero active source findings; final retained-artifact replay after those fixes remains pending. Candidate research already built/scanned all five targets. This plan delivers available fixes plus strict enforcement and accurate residual evidence. It does not promise zero HIGH/CRITICAL when stable vendor patches are absent.

Plan15 is wave9, depends on07 and14, never08. Parent owns metadata:08 becomes wave10 with07/15 dependencies;09..13 become waves11..15,15 plans total. Preserve08 partial history and original completed plans. No branch change, source execution, commit or state update belongs to this planning assignment.

## Exact reviewed candidate references

Use these portable version@index references; select/verify linux/amd64 against the measured manifest digests. Existing candidate cache can be reused by digest; no floating-tag pull or original-tag retarget is needed.

| Consumer | Version@index pin | Measured amd64 manifest |
|---|---|---|
| Both backend Python bases | python:3.14.10-slim-trixie@sha256:af8a5aa14780025dbfbcfbc81bd8a91ebd87711dd5b0f48ed71090949dd7cb1d | sha256:ac25e5afbfdb4a94ff99cc24b0345719210133144481480bcba6085efa36a341 |
| PG dev/test/prod and recovery acquisition/provenance | postgres:18.6-trixie@sha256:bd5dfa494a5a259704365813dbfa5fa6b3e69be7348d43b547f540c730478583 | sha256:e923a22ac074261dd73970c57edf659475bf0497cb9456f17d98ed7cdd3ca913 |
| Dev/test/prod Redis | redis:8.8.4-trixie@sha256:a008e2cb5579f3616b29bd9e9913a25f16ec09ae2f56ddab524664663b581228 | sha256:f00c54d05acbb9f6b9ce47e3dbd03d7ed16d94c274470be17acd6b0112734162 |
| Frontend Dockerfile and deploy.sh NODE_IMAGE | node:24.22.2-trixie-slim@sha256:0820eaa85e07d0490446dd01d14707e17e6108a36988cf374899cd057eb3812d | sha256:947528b072c170d980592b851c802155d84dcad60d3f550b8a0451b84d65dabd |

The Node production build is a docker run in deploy/deploy.sh; frontend/Dockerfile.prod does not exist. frontend/.nvmrc=24 and backend/.python-version=3.14 already express the preserved major/minor policy and need no unrelated edit. CI setup-node remains the established host tool setup; image scans cover actual container consumers.

## File ownership and producers

| Serial task | Needs | Creates / changes | Consumer / proof |
|---|---|---|---|
|15-01| Verified candidate contents, existing Dockerfiles and recovery APIs | Ten existing consumer/provenance files plus two targeted test files: backend/Dockerfile, frontend/Dockerfile, four root Compose files, deploy/deploy.sh, deploy/backup-snapshot.py, deploy/configure-db.sh, deploy/verify-restore.py, deploy/tests/test-deploy-prerequisites.py, new deploy/tests/test-image-contracts.py | Actual locked builds, exact provenance and before-effects negative contracts;15-02 and15-03 consume final pins |
|15-02| Final identities and15-01 test module | One bounded stdlib producer deploy/scan-images.py; extend test-image-contracts.py and test-ci-ops.py; wire existing .github/workflows/ci.yml | Five scan targets → required image job → ci-pass; fake-boundary behavioral failure/omission tests |
|15-03| Final images/helpers after focused review corrections | New evidence06-IMAGE-GATES.md; external temporary JSON/artifact bytes referenced by hashes | Actual affected builds/smoke/audits, fresh raw scans, same final retained supplied recovery/roles/TLS/actual-old rollback; independent review |

Total ownership:16 files:13 existing and three new paths (scan-images.py, test-image-contracts.py and IMAGE-GATES.md). The count is inventory, not a context estimate. Task01's ten existing consumer/provenance files include eight mechanical frontend/Compose/deploy pin updates; substantive changes are the existing verifier/provenance and backend Dockerfile's tightly bounded complete pip cleanup plus focused tests. No new image framework, dependency manager, data model or application feature. Estimated executor context: task01 roughly20%, task02 roughly15%, task03 roughly10–15%; total45–50% with source references/evidence already available. If verified npm repair needs a shared build subsystem or expanded retained-bundle ownership, report that exact additional scope rather than inventing it within this plan. No existing source/test file outside the16 owned paths may be edited without a bounded explicit scope update.

## Mandatory constraints and residual interpretation

All candidates preserve trixie/glibc and same runtime majors. PG18.6 candidate is a rebuild, postgres UID/GID999 and data layout preserved. They remove exactly apt/libapt CVE-2026-109518 rows (two per target); measured residual counts are runtime49 OS+5 pip HIGH, builder49 OS+5 pip HIGH, PG66 OS HIGH/1 CRITICAL plus gosu25 HIGH/1 CRITICAL, Redis48 OS HIGH, Node48 OS+6 npm HIGH. These are finding rows, not unique CVEs. Fresh DB scans may differ; report exact results rather than asserting frozen totals. Known stable Debian fixes are absent for the remaining OS rows. No not-affected disposition has been accepted for gosu or Python subsets.

Complete unnecessary pip/ensurepip removal is allowed only with actual uv/build/test/runtime proof; removing the SBOM alone or breaking build tooling is forbidden. npm11 candidate still distributes vulnerable nested libraries; check official supported complete npm releases and provenance before claiming an available fix. Never edit its SBOM/version fields or delete nested files to alter scanner output. If a verified complete npm update requires ownership expansion, stop that optional expansion and retain the explicit finding; available apt fixes/CI enforcement remain executable. No application lock refresh, unsupported sid copy, essential-runtime stripping, libc/major switch, PostgreSQL-without-XML rebuild, govulncheck acquisition or VEX/waiver mechanism is included.

Recovery provenance must distinguish registry index, platform manifest and Docker config ID. Current verifier's image_digest=postgres@+IMAGE_ID label must be corrected in both producer and authenticated verifier without reducing inventory/config-byte/Compose checks. Derive the new config ID from actual inspected/saved content rather than guessing. Authenticate exact retained index/platform manifest bytes and descriptor links from the pinned index through linux/amd64 manifest to config digest and actual saved config bytes before load/install. The registry pin remains acquisition provenance and the source dev/test/prod consumer. Fixed docker-compose.ops-test.yml recovery execution instead names only the authenticated config/image ID with pull_policy: never; installed startup additionally passes --pull never. Synchronize its exact hash in all three owned consumers. No arbitrary image/project override, interpolation variable, unreviewed Compose override or registry fallback is permitted. Docker load does not have to recreate RepoDigests; recovery must work from verified loaded config bytes alone. Assert actual resolved Compose and actual running container Image/config ID/platform match the imported identity.

Cold/import-only closure is proved without deleting shared images/cache or creating a privileged daemon: task01's stdlib fake Docker boundary models only the imported verified config ID, with registry-reference resolution/RepoDigests absent and an asserted zero pull-attempt counter. Exercise the actual installed recovery resolution/start consumer; require success in that state and rejection for missing/wrong IDs, forged descriptor links or fallback attempts. Task03 complements this with actual same-final-artifact installed Compose running explicitly by config ID with pull disabled, checking running container ID/platform. Warm cached registry resolution alone is insufficient. Keep mapping/resolution inside the owned verifier, fixed ops Compose and image-contract tests; no additional subsystem. Record both the import-only behavioral proof and actual execution identity in IMAGE-GATES.

Finalize all image/helper changes before one new retained package and exact supplied replay. Historical archive aea60b9 and old source evidence are retained as historical, never rewritten. Actual old v0.3.1 source/lock comparison remains in rollback proof.

Scan policy stays HIGH/CRITICAL including unfixed; scanner/DB/JSON errors fail. Five targets are mandatory: actual built backend runtime/test-builder and consumed immutable PostgreSQL/Redis/Node. Retain all obtainable reports after a target fails and nonzero overall status. Correct enforcement tests may pass while raw scans fail. Plan15 can complete its bounded remediation/enforcement/evidence criteria with these failures accurately recorded;08 task03, Phase06 and downstream09 stay blocked. Neither requirement is completed by synthetic local evidence. Actual CI execution follows later approved push; no push/deploy authority is created here.

## Additive multi-source coverage audit

The existing06-SOURCE-AUDIT and01..14 preserve all other Phase06 obligations. No CONTEXT exists and no D-ID is fabricated; operations-ledger choices remain binding.

| Source | Item | Coverage | Status |
|---|---|---|---|
| GOAL | Friends trade live with safely backed-up data |15-01..03 →08..13 secure image/recovery prerequisite; live user proof remains13 | COVERED across existing plan set; phase outcome pending |
| REQ | DEPL-01 HTTPS/signup/trade |15-01/02 compatibility/security →10..13 actual publication/live proof | COVERED; not complete |
| REQ | DEPL-02 nightly off-server backup/tested restore |15-01/03 image-bound final replay →08/09/12 real provider/timer/rollout | COVERED; not complete |
| RESEARCH | Exact same-major candidates and measured apt fixes |15-01 immutable pins for all actual consumers | COVERED |
| RESEARCH | pip/ensurepip and npm distributed-tool attribution |15-01 legitimate complete cleanup/verified complete release check;15-03 actual residual record | COVERED; no automatic not-affected acceptance |
| RESEARCH | Unfixed OS and gosu findings cannot be cleared by ordinary pin refresh |15-03 raw failure/residual vendor block;08 acceptance remains blocked | COVERED as explicit dependency blocker; no omission or waiver |
| RESEARCH | Required strict scanner/DB failure policy and all target JSON identities |15-02 actual producer/CI behavioral tests and15-03 exact outputs | COVERED |
| RESEARCH | PG major/layout/UID/TLS/roles/recovery and actual old-image preservation |15-01 verifier/provenance;15-03 serial exact supplied replays | COVERED |
| PLAN CHECK | Registry provenance → archive-imported image → actual offline recovery execution |15-01 authenticated descriptor/config mapping, fixed config-ID Compose and absent-registry zero-pull tests;15-03 actual installed/container identity proof | COVERED; no dependence on host registry cache |
| RESEARCH | Independent final diff/security review and pending source-fix artifact acceptance |15-03 review plus single finalized archive/hash and both supplied runners | COVERED |
| CONTEXT | Phase06 D-IDs / deferred ideas | None exists; no decision invented | EXCLUDED: absent artifact |
| OPERATIONS | $0 B2 policy,26h recovery, latest-only replacement, independent custody | Preserved unchanged;15-03 isolated local evidence only;09/12 retain live gates | COVERED by existing ledger and downstream plans |
| SCOPE |08 partial tasks/history; no high finding advances live |15 bounded criteria explicitly separate from08/09 security acceptance | COVERED |

No implementation/runtime test, private/provider access, installation, branch change, commit or state update was performed by this planning assignment. Parent owns independent plan check, final metadata and any scoped planning commit. Preserve unrelated .claude/ and other workers' edits.

Root coverage correction before independentcheck: rg found the exact recovery
Compose SHA also in backup-snapshot.py:149 and configure-db.sh:71. Both are
explicit task01 ownership for literal authenticated-hash synchronization;
no guard broadening. This avoids an out-of-scope runtime fix at execution.
