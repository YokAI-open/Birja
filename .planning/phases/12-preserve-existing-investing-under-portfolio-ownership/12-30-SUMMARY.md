---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "30"
subsystem: security-policy
tags: [accepted-risk, npm-audit, fail-closed]
requires: [12-29]
provides: [scoped-shared-audit-exception]
affects: [12-31]
key-files:
  created:
    - deploy/audit-frontend.mjs
    - deploy/tests/test-frontend-audit.mjs
  modified:
    - .github/workflows/ci.yml
    - deploy/tests/run-portfolio-validation.py
    - deploy/tests/test-ci-ops.py
completed: 2026-11-17
---

# Phase12 Plan30 — shared advisory-specific audit policy

Both tasks are complete. The Node-only helper preserves the full npm report,
labels the exact accepted advisory with issue35 and rejects unrelated
HIGH/critical, malformed/network/timeout, changed dependency hashes and expired
approval. CI and local qualification run the same helper and12audit tests.
No manifest, lock, package or financial/runtime authority changed.

Actual targeted evidence: independent exact Node --test command12/12pass,
CI policy contracts37/37pass; saved original report accepted-risk14HIGH/
11moderate, not a fresh or clean audit. Separate independent five-file source/
security review found0blockers/0warnings; see12-EXCEPTION-REVIEW.md.
The earlier sandbox child-spawn limit was resolved by the independent exact
command run; no test was skipped. Source and actual full qualification remain
distinct: no complete security or new recovery pass is claimed by this summary.

Plan31 must run both full security and fresh seven-stage same-archive recovery
because the changed validation runner is a packaged recovery payload.
Original failed receipts, prior actual recovery and both owner checks remain.

## Self-Check: PASSED

All five source files and independent report exist, targeted checks pass and
current manifest/lock are unchanged. Parent records the reviewed local commit;
no publication, production change or requirement closure is included here.
