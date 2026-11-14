---
phase: 06-deploy
plan: "09"
reviewed: 2026-11-09T07:32:05Z
depth: standard
source_commit: 0e47c50f00c8ac847a64e4b6166dafa524931d71
diff_base: 7e4a548
files_reviewed: 2
files_reviewed_list:
  - deploy/backup-snapshot.py
  - deploy/tests/test-deploy-prerequisites.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 06 Plan 09: Lock-alias code review

**Status:** clean — 0 BLOCKER, 0 WARNING.

## Narrative Findings (AI reviewer)

No concrete correctness, security or test-reliability defect found in the
bounded `7e4a548..0e47c50` lock-alias change. Review covered
`acquire_operation_lock`, its new regression fixture/tests and nearby shared
callers; it does not represent a review of the whole backup implementation.

The exception at `deploy/backup-snapshot.py:204–223` accepts only the fixed
production spelling resolving to the exact canonical lock. It checks the
root-owned system alias and its exact absolute or relative target, real
root-owned ancestors, and sticky deletion protection when `/run/lock` is
writable by other users. Under the stated local-user threat boundary these
checks prevent an unprivileged user from replacing the accepted root-owned
lock or redirecting a validated ancestor. Trusted root mutations remain
outside that boundary.

At `deploy/backup-snapshot.py:225–258`, canonicalization preserves the UID 0
requirement for production, final regular-file and same-inode validation,
the ban on group/other file writes, `O_NOFOLLOW`, and nonblocking exclusive
`flock`. Existing root-owned mode `0644` is accepted without truncation or
permission changes. Inherited descriptors still require the same inode and
kernel exclusive-flock evidence; only a duplicate is closed. Canonical
synthetic paths retain their previous behavior, and arbitrary synthetic
directory aliases remain rejected.

Nearby caller tracing confirmed `Job.lock()` and `refresh_quota()` retain
the fixed production path; restore/gate use that shared job lock, and the
role/TLS helpers and deployment handoff call the same acquisition function.
The resolved path therefore selects the same inode as the original fixed
spelling.

The regression at `deploy/tests/test-deploy-prerequisites.py:65–187` models
system metadata while opening a private temporary inode. Its actual kernel
flock assertions cover independent contention, inherited reuse, preservation
of the parent lock after duplicate close, and release after owner close.
Negative metadata cases retain the final-file, directory and alias guards;
existing subprocess contracts cover all five shared synthetic callers,
wrong inode, unheld/shared/closed descriptors and foreign ownership.

## Verification and limits

- Independently ran `python3 deploy/tests/test-deploy-prerequisites.py --locks`:
  **8 passed in 5.787 seconds**.
- `git diff --check 7e4a548..0e47c50` for both scoped files passed; their
  working-tree contents match source commit `0e47c50`.
- The supplied 18-prerequisite, 25-backup and 4-safety results were context;
  full suites were not repeated.
- No live system paths, provider, credentials, Docker or network were
  inspected or used. Production diagnosis and the installed `548bc494...`
  archive status are coordinator-supplied facts. Exact replacement archive,
  replay and installation work remains with the coordinator; this review
  establishes no live backup, restore or timer acceptance.

Only this review artifact was written. No source/configuration/state changes
or commits were made.

_Reviewer: independent gsd-code-reviewer agent_
