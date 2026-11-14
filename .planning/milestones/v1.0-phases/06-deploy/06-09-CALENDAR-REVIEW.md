---
phase: 06-deploy
reviewed: 2026-11-10T11:06:48Z
depth: standard
review_type: bounded-calendar-evidence
files_reviewed: 2
files_reviewed_list:
  - .planning/phases/06-deploy/06-09-PLAN.md
  - deploy/backup-snapshot.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
calendar_evidence: sufficient_with_explicit_historical_limits
whole_phase_verified: false
---

# Plan09 genuine-calendar evidence assessment

## Narrative Findings (AI reviewer)

PASS for the outstanding calendar evidence requirement, subject to preserving
the distinctions below. No material BLOCKER or WARNING gap requires waiting
for another night or starting a new backup/restore solely to replace historical
evidence. Plan09 closure still incorporates its previously recorded installation,
approval, exact restore, custody and cleanup evidence; this report assesses only
the newly supplied calendar/remote evidence and its sufficiency.

### What Plan09 requires

Plan09 task02 requires a successful real exact remote retrieval/isolated restore
and a remotely stored snapshot attributable to an actual calendar activation.
Its done clause calls for both, but does not require that the calendar-produced
snapshot itself be restore-tested, nor retained indefinitely. DEPL-02 similarly
requires nightly off-server backup and a restore tested once. The approved
single-copy replacement policy permits later verified backups to rotate earlier
points; it must not be misrepresented as multi-snapshot retention.

### Historical nightly creation

The supplied calendar receipt binds a single completion record to invocation
`cba2df6f9fd349e1ab82058d34e5c601`, with actual timer trigger matching service
start and service exit status0. The reported start is2026-11-10 03:11:51Z;
the invocation's completion is03:12:15Z and names exact snapshot
`8d15d199f1f2da34e0b0576f5cb9a500c93ad33c5be4bbb5d654a4b248037cac`.
The receipt explicitly distinguishes this from a manual backup start.

Supplied unit provenance verifies retained unit hashes, actual loaded fragments,
absence of drop-ins and approved backup ExecStart. The reviewed retained timer
has the daily03:00UTC calendar plus bounded jitter, and its service invokes the
approved backup entrypoint.

The installed producer's completion path is stronger than a successful process
exit alone. Before printing the exact `step=complete` snapshot, it requires the
remote exact snapshot, expected file sizes/names, exact manifest equality and
restic repository check. Rotation then follows repository verification and is
checked again; staging cleanup and protected success publication precede the
completion print. Correlated approved invocation/unit provenance plus this
specific completion record therefore supports historical verified remote
creation, even though that point has subsequently rotated.

### Current recovery is separate evidence

The supplied bounded read-only repository receipt shows one current point,
`50008a08ea9dd6041d4dcbcc5de43871324abb5233a2650c58872f799d4f7444`,
with current files/profile/source/revision verified. This is the exact
post-rollout point already retrieved and restored successfully in Plan12.
The repository inspection used only snapshots/ls/dump, did not start a backup
or restore and did not modify the timer/data.

The nightly8d15… point is explicitly absent now. Its historical completion and
the subsequent approved single-copy rollout backups explain this consistently;
the current remote snapshot must not be attributed to the nightly invocation.
Current recoverability rests on the separate exact current-snapshot restore,
while genuine scheduling rests on the historical invocation evidence.

## Required wording and limits

Record the nightly point as historically uploaded and repository-verified,
subsequently rotated under the approved policy. Do not claim it is currently
retained, retrieved or individually restore-tested. The producer expressly labels
its upload assurance `restore-not-proven`; repository checks do not replace an
exact isolated restore. Record the successful current exact restore separately.

One observed genuine calendar success demonstrates activation and production
upload behavior; it is not a guarantee of future nights or a waiver of daily
status/freshness checks. Owner-reported Gmail/Outlook acceptance is a separate
Plan13 input. This assessment performs no whole-phase goal verification.

Review used Plan09, DEPL-02 wording, relevant retained backup/service/timer source
and only the three explicitly supplied sanitized calendar/repository/unit
receipts. No production/provider/private configuration/journal access, tests,
source changes, commits or operational mutations were performed. The receipt
collection was performed by the root agent; this reviewer assessed consistency
and source semantics rather than independently re-running live observations.
