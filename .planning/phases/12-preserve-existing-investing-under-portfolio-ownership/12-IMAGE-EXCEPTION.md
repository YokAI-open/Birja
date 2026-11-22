# Phase12 — same advisory in the Node tooling image

The owner's2026-11-17 acceptance of GHSA-fc5q-39xc-vjpf/CVE-2026-112366,
tracked in https://github.com/YokAI-open/Birja/issues/35, also covers its
identified copy in the development/build tooling image. This is the same
unresolved matcher advisory, not acceptance of a new vulnerability or a claim
of remediation. The new Python CVE-2026-119170 remains blocking.

## Exact image scope

The policy in deploy/scan-images.py accepts only the node target, HIGH
CVE-2026-112366 with VendorIDs exactly GHSA-fc5q-39xc-vjpf, PkgName picomatch,
PkgID picomatch@4.0.4, InstalledVersion4.0.4 and exact PkgPath
usr/local/lib/node_modules/npm/node_modules/tinyglobby/node_modules/picomatch/package.json.
The report group must be Node.js/lang-pkgs/node-pkg. The current
frontend/Dockerfile SHA256 is pinned:
94dbef7eba9db0e2ec652c286cc562eeec294666e29e5ac3e031af8a03d8a148.
That complete source pin includes the existing npm11.21.2 distribution and
its verified archive digest. The exception expires2026-12-17T00:00:00UTC.

All raw Trivy JSON/logs remain unchanged. qualifying_findings retains the full
HIGH/CRITICAL count, while accepted_findings and blocking_findings separately
identify the policy disposition. Accepted records say accepted-risk and include
issue35, expiry, exact source and original finding. No CVE is removed from
the evidence, no image-level ignore or ignore-unfixed option is introduced.
The original immutable-image/config/archive/platform/fresh-database guards
remain enforced. Trivy exit1 is allowed only when actual complete valid
findings exist and every finding is accepted; operational exit2, inconsistent
exit0-with-findings or exit1-without-findings still fails. Other HIGH/CRITICAL
findings, including the new Python advisory, remain blocking.

## Actual offline validation

python3 deploy/tests/test-image-contracts.py:17tests passed in0.754seconds.
The command-boundary fake scanner exercises all five targets, raw retention,
accepted node findings, scanner errors and mixed accepted/new Python findings.
Direct classification tests reject other targets, CVE, severity, vendor ID,
package version/path/identity, malformed result lists, changed source bytes
and expired/naive clocks. Mixed reports preserve all findings and leave the
unrelated finding blocking. No actual image scan, build, pull, install or
network operation was performed by this implementation task.

Only deploy/scan-images.py and deploy/tests/test-image-contracts.py changed.
Independent source review and affected actual image/recovery qualification
remain required; this note is not their result. Existing raw retry1 scan
reports in /tmp/phase12-accepted-retry1-image-reports-f97b2d9/ are preserved.
