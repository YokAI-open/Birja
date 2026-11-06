---
phase: 06-deploy
plan: "15"
reviewed: 2026-11-06T20:11:04Z
rereviewed: 2026-11-06T20:16:37Z
depth: deep
source_base: 89c7039
source_head: 3bc1ca7
context_head: ffcceb2a65cdb8746afb2317d584424fbe9d7d9c
rereview_head: 26614f5c6131eba26b8977894c5fdd134dfec907
files_reviewed: 17
files_reviewed_list:
  - .github/workflows/ci.yml
  - backend/Dockerfile
  - deploy/backup-snapshot.py
  - deploy/configure-db.sh
  - deploy/deploy-entrypoint.sh
  - deploy/deploy.sh
  - deploy/scan-images.py
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-deploy-prerequisites.py
  - deploy/tests/test-image-contracts.py
  - deploy/tests/test-rollback-db-security.sh
  - deploy/verify-restore.py
  - docker-compose.ops-test.yml
  - docker-compose.prod.yml
  - docker-compose.test.yml
  - docker-compose.yml
  - frontend/Dockerfile
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan 06-15: Independent Code and Security Review

**Current result:** zero active source findings after focused independent re-review of `26614f5`. WR-01 below is retained as resolved history. The external image gate and final artifact acceptance remain pending; `clean` describes source review only.

## Narrative Findings (AI reviewer)

### WR-01: WARNING — Missing built-image identity aborts collection for every available image

**Disposition:** resolved by `26614f5`; independent verification below.

**File:** `/home/YokaiExchange/.github/workflows/ci.yml:130-135`, crossing `/home/YokaiExchange/deploy/scan-images.py:81-89`.

**Issue:** The always-run scan step resolves built image IDs using command substitution before invoking the producer. If a build failed or did not load an image, `docker image inspect` prints no ID, so the producer receives an empty argument. Its global reference validation raises before creating evidence or entering the per-target failure/collection loop. For example, failure of the Node toolchain build occurs after both backend images have loaded; the always-run scan invocation then loses both obtainable backend reports because the missing Node ID invalidates the entire request. It can upload only the initial `build-not-completed` status. This does not allow CI to pass, but breaks the required failure-evidence collection behavior. The existing inspect-failure test starts with five syntactically valid IDs and therefore does not exercise this actual CI path.

**Reproduction:** Called the actual `run_scans()` with the same empty built-image value produced by failed CI inspection, four valid remaining identities, and an intercepted Docker command boundary. It raised `ValueError` with `docker_calls=0 reports=0`. No Docker, image or network operation occurred. Shell `set -e` does not turn a failed substitution inside the Python command's arguments into per-target evidence.

**Minimal fix:** Preserve exactly five named targets while representing failed identity resolution as a per-target failed record. Continue scanning each available immutable resolved ID, retain its original inspect error, and return nonzero overall. This can be a bounded CI-to-producer interface correction; do not substitute a floating image or silently omit the missing target. Keep malformed/duplicate target declarations fail-closed.

**Regression:** Exercise the real scan-step/producer boundary with a missing Node built image and available runtime/builder images, then with a missing runtime image. Assert nonzero overall result, explicit failed identity-resolution evidence for the unavailable target, and valid reports for all remaining available targets. Preserve always-upload and required image aggregation.

## Reviewed boundaries and conclusions

Reviewed the actual `89c7039..3bc1ca7` diff and affected consumers against Plan 15, its scope/refinements, independent plan check and candidate evidence. Git reports **17 changed source paths**; the 18-path ownership includes the later planning evidence artifact `06-IMAGE-GATES.md`, not an eighteenth changed source path. The original clean `06-REVIEW.md` remains intact.

- Registry index, linux/amd64 platform manifest, config digest and engine image identity remain distinct. Recovery verification authenticates descriptor links and saved config/layer bytes before loading; classic config and containerd platform identities are narrowly allowed. Installed execution binds the fixed local alias to these identities, disables pulls and checks actual resolved/running identity/platform. Import-only tests exercise absent registry references/RepoDigests rather than relying on a warm registry cache.
- The complete npm 11.21.2 distribution is SHA512 checked before extraction, with redirect rejection, a 60-second abort signal retained during streamed body consumption and a 10-MiB body bound. Dev, retained production and CI scan consumers use the built toolchain. The retained deployment manifest now includes the actual frontend Dockerfile; production builds select its verified toolchain and use the actual built image ID. Global pip/ensurepip removal is complete rather than SBOM-only; application locks and the uv-managed test environment are preserved.
- The scanner uses the pinned scanner image with read-only root, bounded writable tmpfs, dropped capabilities and only public archive/private cache mounts. Five distinct targets are mandatory. Once valid target identities reach its loop, inspect/export/scanner/JSON/DB/identity/vulnerability failures retain the other obtainable target reports and return nonzero. CI loads both backend stages and the actual changed Node toolchain, preserves strict HIGH/CRITICAL policy including unfixed findings, always uploads evidence and keeps image required by `ci-pass`. WR-01 is the missing pre-loop failure connection.
- Backup/configure-db changes only synchronize the exact finalized recovery Compose hash; privileged target guards, credential routing, shared locks and previously corrected data-time/RPO checks are preserved. No additional confirmed injection, authorization, provenance substitution or pull-fallback defect was found in this bounded pass.

This is a phase-specific ASVS 5 Level 1/STRIDE supply-chain assessment of registry/build-to-image, archive-to-privileged-installer and scan-to-CI-result boundaries, not whole-application certification. Root-owned host/config and trusted Docker daemon remain the accepted boundary; no hypothetical malicious-root findings are introduced.

## Verification and remaining gates

Independently ran `python3 deploy/tests/test-image-contracts.py`: **8 passed in 0.118s**, including ten scanner failure modes and classic/containerd import-only consumers. `python3 deploy/tests/test-ci-ops.py`: **4 passed in 0.002s**. The additional missing-ID probe above exposed WR-01 despite these passing contracts. This review did not rerun full fixtures, builds, audits or scans; previously supplied results remain execution evidence rather than results independently repeated here.

**External image gate remains blocked:** fresh raw HIGH/CRITICAL vendor findings are a separate existing supply-chain acceptance gate, not waived or counted as new source findings in this report. No CVE-by-CVE reinvestigation or replacement image pull occurred. The final streamed-fetch build and one finalized retained artifact with supplied recovery/roles/TLS/actual-old rollback replays remain orchestrator acceptance work after confirmed fixes. No Plan 08/phase/live completion is implied.

Only this new report was written. No source/state modification, commit, image lifecycle, private/provider access, real authentication/email/trade, publication or deployment occurred.

## Focused fix re-review — `26614f5`

Read the complete four-file correction and traced the actual CI shell -> CLI -> per-target producer path. An empty identity is now permitted only for the three named built-image targets. The producer creates an explicit failed identity-resolution record, retains/hash-binds the original CI inspect diagnostic and proceeds through the other four targets. That failed record keeps the aggregate nonzero. Mandatory target names, distinct nonempty identities, immutable-reference validation, empty-datastore rejection and malformed-input failure remain enforced. No floating fallback or silently omitted target was introduced.

The regression executes the actual workflow shell with fake Docker identity inspection, captures the resulting CLI arguments, then calls the actual producer CLI with intercepted scan boundaries. Missing Node and missing runtime cases both retain the original inspect error, record the failed named target, collect all four available reports and return nonzero. Existing scanner/error/provenance cases remain included.

Independently reran `python3 deploy/tests/test-image-contracts.py`: **8 passed in 0.347s**, including the two new workflow/CLI handoff cases (12 scanner modes total). `python3 deploy/tests/test-ci-ops.py`: **4 passed in 0.002s**. No new confirmed defect was found in this bounded correction. WR-01 is resolved; active counts are zero.

This was a focused recheck, not a repeat of the original 17-file deep review, actual builds/scans or artifact replays. External vendor HIGH/CRITICAL acceptance remains blocked separately. Only this report was updated; no source change, commit, image/build/provider/private operation occurred. The orchestrator retains report commit and final artifact acceptance.
