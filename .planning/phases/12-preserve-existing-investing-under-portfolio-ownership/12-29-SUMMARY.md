---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "29"
subsystem: security-policy
tags: [accepted-risk, npm-audit, picomatch]
requires: [12-28]
provides: [owner-approved-advisory-deferral]
affects: [12-30, 12-31]
key-files:
  created:
    - .planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-ACCEPTED-RISK.md
  modified: []
tech-stack:
  added: []
  patterns: [exact-advisory-acceptance]
duration: bounded-local-record
completed: 2026-11-17
---

# Phase12 Plan29 — record the owner-approved advisory deferral

The owner explicitly accepted deferring GHSA-fc5q-39xc-vjpf while preserving
visible audit reporting and follow-up issue35. Both revised tasks complete.
The vulnerability is unresolved; previous no_candidate/rejected-fork findings
remain retained rather than relabelled as a fix.

| Task | Outcome |
|---|---|
|29-01|Issue35 read back OPEN; exact decision, exposure limits and locked hashes recorded in12-ACCEPTED-RISK.md.|
|29-02|Exact advisory/hash/expiry scope, unrelated-HIGH/critical/error refusal and qualification obligations recorded.|

Verification: the accepted-risk record exists; gh issue view35 returned the
expected issue URL/state/title; git diff for frontend/package.json and
frontend/package-lock.json is empty. No new network write, package installation,
audit/test campaign or source financial/runtime change occurred in this plan.

This summary is prepared for the parent's local task commit; this executor
made no commit or global state/requirement update as explicitly instructed.
Plan30 requires independent implementation review; Plan31 requires actual full
security and fresh complete same-archive recovery before goal verification.

## Self-Check: PASSED

The declared risk artifact exists, issue35 was read back, current locked inputs
remain unchanged and the exact owner acceptance is quoted. No claim of a fixed
dependency, phase completion or passed future qualification is made.
