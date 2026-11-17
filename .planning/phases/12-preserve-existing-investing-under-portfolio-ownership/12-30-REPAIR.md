# Plan12-30 — scoped audit exception implementation

**Status:** implementation, targeted checks and independent review pass.
Independent12-EXCEPTION-REVIEW.md has0blockers/0warnings; exact CI Node
--test command12/12 and all37 CI contracts passed. See12-30-SUMMARY.md.

The Node-built-in checker deploy/audit-frontend.mjs executes full
npm audit --json --audit-level=high with dev inclusion,120second timeout and
8MiB output bound. It prints raw stdout/stderr before policy evaluation.
The exact advisory, reviewed range/nodes, manifest/lock SHA256 and UTC expiry
bind the exception to issue35. The parsed report must have a valid version2
schema, consistent counts, lock-backed nodes and real advisory causes.
Criticals and every unrelated HIGH leaf are rejected. All HIGH inherited
entries must reach an actual allowed root; legitimate parent cycles can reach
that root but a disconnected cycle cannot invent acceptance. Error/transport/
malformed/status inconsistency, changed hash and expiry remain fatal.

CI and run-portfolio-validation.py both invoke node ../deploy/audit-frontend.mjs
from frontend cwd, and both run the exact new audit unit test command. Existing
coverage/browser/image/recovery commands remain. The CI mutation contract checks
require both new commands and preserve the aggregate gates.

## Actual targeted verification

- Node audit suite:12tests pass (about0.1second), including inherited parent
  cycles, mixed/new HIGH, criticals, spoofed advisory identity/range/nodes,
  malformed report/counts, disconnected cycles, expiry/hash mutation, exit
  status inconsistency, timeout/network/badJSON and CLI-override refusal.
- Actual saved baseline /tmp/phase12-reviewfix-npm-audit-d9da271.json evaluated
  accepted-risk, counts14HIGH/11moderate/0critical, issue35, review expiry.
  This is evaluation of saved evidence, not a fresh npm audit result.
- python3 deploy/tests/test-ci-ops.py:37tests pass (7.4seconds).
- Selected new JS formatted with the existing project Prettier binary.
- Direct CLI with --ignore-all exits1 before audit and reports no overrides.
- Manifest/lock diff remains empty; no package installation occurred.

The sandbox refuses Node child spawning with EPERM; the CLI negative test calls
the same exported main function with a fake runner and also has a separately
observed direct CLI result. No hidden skip or weaker assertion is used.

No full audit, browser, financial or recovery campaign ran in this executor.
The packaged validation runner changed, so Plan31 must qualify a fresh complete
recovery archive at the frozen reviewed source. Previous receipts remain intact.
