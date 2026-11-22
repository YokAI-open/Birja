---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "31"
subsystem: qualification
tags: [accepted-risk, recovery, tls, source-bound-proof]
requires: [12-30]
provides: [complete-current-security-qualification, fresh-seven-stage-recovery]
affects: [phase12-final-verification]
key-files:
  modified:
    - .planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-LOCAL-VERIFICATION.md
    - .planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-RECOVERY-PROOF.md
    - .planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-REVIEW-QUALIFICATION.md
completed: 2026-11-17
source_commit: 4b4320b4cc373268a8d598612a563cd5ef199700
accepted_risk: GHSA-fc5q-39xc-vjpf
---

# Phase12 Plan31 — actual accepted-risk security and fresh recovery qualification

Both tasks completed with actual serial whole-command passes at one frozen
reviewed source, not a composite of earlier diagnostic runs. Final independent
goal verification belongs to the parent and remains a separate phase gate.

| Task | Actual result |
|---|---|
|31-01 full all-security|Exit0,1479.850s; backend3114,60critical modules100%, Python auditclean, frontend958/fullchecks, audit12, browser59/1originalskip501.4s, builds/smoke5, all5image policy scans pass|
|31-02 fresh complete recovery|Exit0,2694.692s; all7stages, final same_archive_final_ci=true, exact financial/source/image/authority parity and cleanup|

Actual security findings remain **accepted-risk**, not fixed/clean: npm14HIGH/
11moderate and Node image1rawHIGH are the exact owner-approved picomatch
exception tied to issue35. Runtime/builder/Postgres/Redis have0qualifyingHIGH.
The approved Python patch fixes the independently surfaced runtime advisory;
no unrelated finding is waived. The rejected fork remains uninstalled.

New archive196689920bytes:
`d253bc51b876c7d629ee246ee47bd57274a5d9333e71318e11fcef586cff26be`.
Old archive94365aff and complete directory are preserved unchanged at
`/tmp/birja-phase12-proof-d9da271-preserved-before-4b4320b/`.
Current raw receipts use
`/tmp/phase12-accepted-retry2-{security,recovery}-4b4320b.*`;
full image reports are privately preserved at
`/tmp/phase12-accepted-retry2-image-reports-4b4320b/`.

Both wrappers record unchanged source HEAD, no tracked-file drift and zero
containers/networks/volumes across all six exact-owned projects. Logs/source
receipts and old/new archive hashes were recomputed after completion.
Failed attempts e4c0a9f/f97b2d9 are retained without relabelling. No new
production/provider/publication action occurred. Accepted UI/native200 and
separate Phase7 deferred outcomes remain unchanged.

## Deviations and limits

The first actual attempt exposed an ambiguous unordered metadata-test selector;
the parent applied and independently reviewed a deterministic test-only repair.
The next attempt exposed an unrelated Python image advisory plus the already
accepted picomatch in the Node toolchain. The parent separately obtained exact
Python patch approval, reviewed both fixes and froze the current source before
this final retry. No repair, gate expansion or package installation occurred
inside this successful campaign. The complete history is retained in the
qualification and repair reports.

## Self-Check: PASSED

All declared proof files and raw receipts exist; both actual result exit codes
are0, receipt hashes match, current archive hash matches final output, old
archive is untouched, and all exact-owned resources are clean. This executor
made no source change, commit, global-state update or requirement-completion
mutation. Parent will commit these evidence-only updates and request final
independent verification before phase closure.
