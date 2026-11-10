---
phase: 06-deploy
plan: "12"
status: approved-rollout-complete
source: 46d24c8591de2207cf219429aac0768962bed4c3
retained_manifest: 70e568a8c0f9953926e40de4ed79ec25272b3cdd777e474b3967a09849edb0b2
recovery_archive: d5fe2059b3e984ffcd0dff6b1763dd5a97deddb0be638ca23e49381d35a54401
rollout_executed: true
---

# Production rollout execution evidence

Prepared packet:06-12-MAINTENANCE.md. Independent review:
06-12-MAINTENANCE-REVIEW.md (0blockers/0warnings). Immediate window/sole Birja
writers and off-server custody confirmed. Publication, read-only preflight and
host preparation completed under their own approvals. Owner subsequently approved the exact rollout; live role/TLS/data/image /
application transition is now complete, with recovery and smoke verification.

Record actual approval and each runtime stage here only after execution:

| Stage | Actual result |
|---|---|
| Target/retained/recovery/custody revalidation | PASS: exact source/129retained/20recovery hashes and identities |
| Writer stop and final bound configuration | PASS: approved writers stopped, unrelated env values preserved |
| Pre-copy B2 backup/exact isolated restore | PASS: eac31e13... / source010770,0007 |
| Stopped originals/fingerprints/candidate copy | PASS: approved empty candidates only, originals unchanged |
| Secure candidate startup/compatibility/collation | PASS: private data/schema/sequences equal,5indexed/seq comparisons |
| Candidate role transition and fresh exact recovery | PASS:3restricted roles/9migrator-owned tables; c1e1d901... |
| Approved deployment/0008/role TLS/origin/public smoke | PASS: exact46d24c8/0008; TLS both roles;41/41origin,9/9public |
| Same-tool post-rollout B2 backup/exact restore | PASS:50008a08... / exact46d24c8,0008 |
| Original preservation and isolated-resource cleanup | PASS: stopped original fingerprints equal; restore resources empty |
| Refreshed private export/custody | PASS:26member encrypted7z verified; prior secret custody confirmed; refreshed settings download available |

No live proof is inferred from CI or host preparation. Plan09's first actual
nightly observation remains owner-deferred and Plan13 friend acceptance remains
pending. No DEPL or phase completion claim.

## Historical start checkpoint —2026-11-10

Owner selected “Approve production rollout now” for the reviewed packet.
Continuous shared deployment lock held by private rollout session. All retained
and independent recovery hashes/source/volume/image preconditions passed.
Only approved old writers stopped; final bound material prepared without changing
unrelated env values. Fresh pre-copy B2 backup and exact isolated restore passed:
`eac31e13efdc0b3dc82beb49076604e5e0952ce7188b19837e93df3d03fef847`.
Exact source010770/revision0007/config/tool recovery gate passed.
Clean original datastore shutdown and candidate copy completed; secure candidate
startup/compatibility is currently in progress. No application writer startup
yet; no phase completion. Private runtime ledger is rollout-live/state.json.

## Completed runtime evidence —2026-11-10

All approved stages passed; original volumes and old images preserved. Candidate
copy/ownership and REINDEX-before-collation-refresh applied only to candidates.
Runtime app/scheduler are non-owner restricted logins over verified TLS; migrator
is separate. Fresh exact recovery passed before copy, after roles and after
deploy using unchanged independentd5fe2059 payload. First two snapshot IDs below
are historical successful proof; one-copy policy may already have rotated them.

| Stage | Exact snapshot |
|---|---|
| Pre-copy/source010770/revision0007 | eac31e13efdc0b3dc82beb49076604e5e0952ce7188b19837e93df3d03fef847 |
| After roles/source010770/revision0007 | c1e1d90193a8ef42f6f6d099cd2e20e9a5027e8b20c51ba015a8af2b209df766 |
| Post-deploy/source46d24c8/revision0008 | 50008a08ea9dd6041d4dcbcc5de43871324abb5233a2650c58872f799d4f7444 |

Outage measured365.719seconds (about6min6s), from writer stop through successful
deployment return. Four live services healthy. Origin smoke41passed/0failed;
public smoke9passed/0failed. No live trade/account was created by the assistant.
All five default-collation index comparisons, private table/schema/financial /
identity sequence equality and original stopped-file fingerprints passed.
Temporary private row-comparison outputs were removed after successful equality
checks; only protected digest/aggregate evidence retained. Shared lock released
after final recovery and export; no process remains running. No gate/source/image
change, schema repair or abort/rollback was needed. Initial temporary script
filename shadowed stdlib operator; renamed before any production operation.

Final refreshed export: `birja-offserver-recovery-20261110T104354Z-v040.7z`,
127,261,213bytes,26members, encrypted contents/headers and all extracted hashes
verified, no plaintext staging retained. SHA256:
`f8d235e0ff6def63659b6b1366fe8bbff4c4b7b1ae5bc98c8bf011c294e91afe`.
Uses existing restic password; no secret/key changed from confirmed off-server
custody. Refreshed config contains final role URLs and backup binding, so offer
owner download to update their local configuration copy. Actual DB remains
separately backed up in B2.

Private sanitized receipt:rollout-live/sanitized-execution-receipt.json; it
contains stage timestamps and results, no rows or secret values. Protected
full runtime state/logs remain ignored and are not committed or published.
Nightly activation and Gmail/Outlook friend acceptance remain unverified; no
DEPL-01/02 or whole-phase completion.

## Required focused contracts

Actual required post-rollout local checks: backup25tests PASS in51.218s
(including encrypted local restic rotation), restore-safety4PASS in1.371s,
CI contracts9PASS in0.419s. No production/provider/timer access by these tests.
No full app/image test rerun: source/runtime artifacts unchanged from approved
exact-head green CI; this plan adds live execution evidence, not source changes.

## Closeout

Independent06-12-CLOSEOUT-REVIEW passes with0active blockers/warnings after two
documentation corrections. Plan12 is COMPLETE; actual rollout and recovery
evidence accepted. Plan09/Plan13 and DEPL-01/02 remain pending. No13SUMMARY or
whole-phase acceptance follows. Updated archive download is offered to owner.
