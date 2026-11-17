---
phase: 12-preserve-existing-investing-under-portfolio-ownership
reviewed: 2026-11-17T20:30:25Z
depth: deep
files_reviewed: 5
files_reviewed_list:
  - deploy/audit-frontend.mjs
  - deploy/tests/test-frontend-audit.mjs
  - .github/workflows/ci.yml
  - deploy/tests/run-portfolio-validation.py
  - deploy/tests/test-ci-ops.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
accepted_risk: GHSA-fc5q-39xc-vjpf
issue: https://github.com/YokAI-open/Birja/issues/35
full_qualification: pending
---

# Phase12 accepted-risk audit integration review

## Narrative Findings (AI reviewer)

No new BLOCKER or WARNING was found in the five reviewed source files. This
is an independent review of the narrow audit-policy implementation and its CI
integration, not a claim that picomatch was fixed or that complete Phase12
qualification passed. The owner explicitly accepted this one unresolved
advisory and requested issue35 plus continued development. That authorized
risk disposition is distinguished from new source defects.

The review traced the complete helper, all twelve test bodies, changed CI and
local-runner invocation paths, and the affected policy/mutation assertions in
test-ci-ops.py against base28b6628. Existing financial, application/runtime,
package-manifest and lock content was not changed by this diff.

## Security and behavior checks

- The CLI executes the full npm audit JSON report at HIGH threshold from the
  fixed frontend directory. It does not omit development dependencies; dev
  inclusion and disabled lifecycle scripts are set explicitly. The command
  has a120second timeout and8MiB capture bound. Raw stdout/stderr is emitted
  before evaluation, including on refused reports.
- The exception requires the exact issue/advisory identity, reviewed
  picomatch name/dependency/range and two allowed installed paths, exact
  manifest/lock SHA256 bindings and actual UTC clock before2026-12-17.
  Command-line policy overrides are rejected. Test dependency injection is
  an exported module seam; the executable CLI supplies none of those overrides.
- All critical entries/causes are fatal. Every direct HIGH cause anywhere in
  the report must be the exact accepted advisory; another HIGH on picomatch
  or another package is rejected even when it coexists with an allowed cause.
  Every inherited HIGH entry must additionally reach that real accepted leaf.
  The iterative visited-set traversal supports the legitimate Vitest parent
  cycle and refuses a disconnected cycle without an accepted root. These
  two checks work together; reachability alone is not the exception criterion.
- Report version, object/array structure, entry/advisory severity, cause
  references, lock-backed nodes and metadata counts are validated. Hidden
  direct-cause severity, criticals, invalid npm status/signal, transport/error
  reports, bad JSON and timeout are fatal. Existing moderate reporting stays
  nonblocking under the original HIGH threshold and is retained in output.
- CI and the local complete security runner invoke the same helper and its
  exact Node test command from frontend cwd. All existing backend coverage,
  frontend coverage/build, browser, image and recovery gates remain present.
  CI mutation contracts require both added commands; failure propagation and
  exact owned-stack cleanup remain enforced.

## Independent targeted execution

| Check | Actual result |
|---|---|
|node deploy/tests/test-frontend-audit.mjs|12/12 pass,0skip, exit0|
|node --test deploy/tests/test-frontend-audit.mjs|Exact CI command independently run with sandbox escalation for Node child-process support;12/12 pass,0skip, exit0|
|python3 deploy/tests/test-ci-ops.py|37/37 pass, exit0,7.746seconds|
|Saved actual audit report evaluation|accepted-risk with14HIGH/11moderate/0critical; issue35 and expiry visible|
|git diff --check|Exit0|

The saved-report check used
/tmp/phase12-reviewfix-npm-audit-d9da271.json with the actual unchanged
manifest/lock and a disclosed fixed review time. It is not a new network audit.
No npm audit request, dependency installation, provider/production operation or
financial/browser/recovery campaign was performed by this reviewer.

## Reviewed source binding

| File | SHA256 |
|---|---|
|deploy/audit-frontend.mjs|1ead63130b67037784cae2c65b3164b287a4113c6883736ed3a8150112c871b8|
|deploy/tests/test-frontend-audit.mjs|b2426a3883761144eb27a42f384dade329613f671ef40a9f57134dcf4ea93a1b|
|.github/workflows/ci.yml|b6ee4905e2bb5b1c0e391a572a7dc8e54851bd5ffda630265bc6294307d905ce|
|deploy/tests/run-portfolio-validation.py|4cae0552b24ad5a80454153f31f86a35e68fdbe63286fafbe6428f4562f8e641|
|deploy/tests/test-ci-ops.py|d5b732862d06d0edc9149532dc69fce07d0c20ff8adf74df4410943ea634801b|

## Qualification boundary

Source review and targeted tests support proceeding to Plan31. Actual complete
all-security must still run at the frozen reviewed source, with accepted risk
reported explicitly rather than claiming zero npm HIGH findings. Because the
changed validation runner is in PORTFOLIO_PAYLOAD_V1, fresh complete seven-stage
same-archive recovery is required; the older source/archive proof cannot be
relabelled as this run. Final independent goal verification remains pending.
The prior owner UI/native200 acceptance and separate Phase7 live deferrals are
unaffected by this source-only audit-policy review.

_Reviewer: independent gsd-code-reviewer agent. Only this report was written;
no source, global state, requirement checkboxes or commits were changed._
