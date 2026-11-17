---
phase: 12-preserve-existing-investing-under-portfolio-ownership
reviewed: 2026-11-17T21:28:53Z
depth: deep
files_reviewed: 2
files_reviewed_list:
  - deploy/scan-images.py
  - deploy/tests/test-image-contracts.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
accepted_risk: GHSA-fc5q-39xc-vjpf
issue: https://github.com/YokAI-open/Birja/issues/35
actual_image_qualification: pending
---

# Phase12 Node image exception alignment review

## Narrative Findings (AI reviewer)

No new BLOCKER or WARNING was found in the complete two-file diff against
f97b2d9. The review traced the new classifier and acceptance predicate through
run_scans, immutable image/archive/config identity checks, scanner-result
validation, fresh database metadata, evidence output and aggregate exit status.
The new negative and command-boundary tests were read in full. The accompanying
12-IMAGE-EXCEPTION.md correctly describes an accepted unresolved advisory,
not remediation or acceptance of unrelated findings.

This aligns the already owner-accepted GHSA-fc5q-39xc-vjpf/CVE-2026-112366 in
issue35 with its identified copy inside npm's Node build-toolchain image.
No other CVE or target receives an exception. In particular, the newly found
Python CVE-2026-119170 remains an unresolved blocking finding; this report
does not authorize changing its package or accepting that separate risk.

## Scope and failure-path checks

- Acceptance requires target name node, the Node.js/lang-pkgs/node-pkg report
  group, HIGH severity, exact CVE and sole expected VendorIDs advisory, package
  name picomatch, PkgID picomatch@4.0.4, InstalledVersion4.0.4 and the exact
  npm/tinyglobby package.json path. Different version/path/identity, critical
  severity, another advisory/CVE or any of the other four image targets is
  not accepted.
- Actual UTC expiry is checked before2026-12-17. A naive test clock is
  refused, and exact current frontend/Dockerfile SHA256 is required. That
  source pin retains the existing npm distribution/artifact checksum. No
  command-line policy override was added. Injectable clock/source arguments
  are test seams; run_scans uses actual clock/source.
- Every HIGH/CRITICAL row remains in qualifying_findings. Accepted and
  blocking counts are separate, original findings and issue/expiry/source
  bindings are retained in accepted_risk, and raw Trivy JSON/logs remain
  unchanged. A mixed report retains accepted1/blocking1 and fails.
- Trivy's original HIGH,CRITICAL severity filter and exit-code1 remain;
  neither ignore-unfixed nor a broad ignore/CVE exclusion is introduced.
  Acceptance requires scanner exit1 with actual findings or exit0 without
  findings. Operational exit2 and contradictory statuses fail even when
  an otherwise eligible accepted row is present.
- Existing schema/scanner version, immutable engine identity, exported
  config/report identity, linux/amd64, complete five-target handling, saved
  raw evidence, fresh database guard and aggregate failure propagation remain
  enforced. Invalid classifications, unknown severity, malformed/missing
  reports and scanner/identity failures do not yield a passing record.

## Independent targeted execution

python3 deploy/tests/test-image-contracts.py independently passed17/17 tests
in0.713seconds, exit0. This is an offline command-boundary test using injected
scanner/Docker results, not an actual image scan. Assertions exercise accepted
node results, error and mixed findings, raw retention, all other targets,
identity resolution failure, schema/report failure, source/expiry mutation
and unchanged image/container/config guards.

The inspected two-file diff passes git diff --check. Source bindings:

| File | SHA256 |
|---|---|
|deploy/scan-images.py|77fec4f0971d04526a7334e3bddeb32e21b54707c459ee11fbe11a1383db0595|
|deploy/tests/test-image-contracts.py|191ee0211d4788d4d9cde35fd877be8cb87513092228cce464ec5a0f531cdd9c|
|frontend/Dockerfile policy input|94dbef7eba9db0e2ec652c286cc562eeec294666e29e5ac3e031af8a03d8a148|

## Qualification boundary

The scoped source change is suitable for affected qualification. This does not
claim zero HIGH findings, a new passing actual scan, complete security success
or current recovery acceptance. Prior failed scans must stay failed, including
their unrelated Python finding. Any Python repair requires its separate exact
package authorization/review. The final whole security and fresh same-archive
recovery proofs remain required at the resulting frozen reviewed source.

_Reviewer: independent gsd-code-reviewer agent. Only this report was written.
No source, global state, dependencies or commits changed; no actual image
scan, pull, build, package installation, network/provider or production
operation was performed._
