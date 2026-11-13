---
scope: pr31-ci-failures
reviewed: 2026-11-14
reviewer: /root/pr31_debug/security_review
status: secured
threats_closed: 6
threats_open: 0
unregistered_flags: 0
---

# PR31 affected security review

Independent security review of the three-file diff against `95912e0`.
Implementation remained read-only. No Docker workload, package installation,
network operation, publication or production action occurred during this review.
This is bounded engineering verification, not an ASVS certification claim.

## Threat verification

All six assigned threats have disposition **mitigate**. No BLOCKER or WARNING
was found in this reviewed scope.

| Threat | Result | Concrete verification |
|---|---|---|
| T1 authenticated import and binding | CLOSED | `check-recovery-image.py:40` calls unchanged `verify_saved_image` before `docker image load` at55 and binding at63; rewinds the same private temporary file. `verify-restore.py:147` authenticates pinned index/manifest/config plus linux/amd64 linkage. Its232 archive validator rejects duplicate/traversal/non-file members, tagged or additional roots, unapproved blobs and changed layers before import. Regression at `test-image-contracts.py:40` verifies failed archive validation never reaches load/bind. |
| T2 reject wrong preexisting alias | CLOSED | Helper43–50 inspects the alias and invokes unchanged `loaded_recovery_image` before loading. `verify-restore.py:295` accepts only exact config/platform identities for that alias, with exact OS/architecture. `bind_recovery_image:311` selects only authenticated identities and rechecks the bound alias. Wrong-alias regression raises before either load or bind. |
| T3 exact approved package boundary | CLOSED | `test-image-contracts.py:418` checks eight approved calendar full records separately; OTEL1.45.2 version and complete-record hash are pinned separately at451. Independently recomputed historical `e728855` inventory excluding only root/OTEL: `8b0f58d9199b3dad2d27d9b398d33cc578b8a819307a3838dfc1cb32934991f1`, exactly the revised other-entry assertion. Negative controls reject OTEL version/artifact and unrelated dnspython version/FastAPI artifact changes. No blanket inventory refresh. |
| T4 preserve gates and retained authority | CLOSED | Diff changes only helper and two contract files. `deploy/verify-restore.py`, all retained CORE/authority, workflow, build recipes and lock are unchanged. Workflow53 retains unrestricted `uv run pip-audit`; scanner invocation remains the five actual images. Independent16 CI checks pass, including strict image-policy and gate-omission/failure mutations. Helper remains before the standalone PostgreSQL fixture in workflow246/306. No waiver or production recovery change. |
| T5 owned cold reproduction cleanup | CLOSED | Reviewed `/tmp/pr31-ops-cold-before-after.log`: original helper reports strict verification success yet unique `birja-recovery-postgres:pr31-owned-cold-probe` is missing; actual Compose fails `No such image`. Patched authenticated import/bind starts healthy PostgreSQL and unchanged running-image guard reports exact platform42c334e9…/config4ee05252…. Cleanup removes only the named synthetic project container/network and synthetic alias. No retained alias deletion appears. This verifies retained evidence; no independent live Docker inspection is claimed. |
| T6 pending DNS boundary and provenance honesty | CLOSED for current scope | `backend/uv.lock` remains original SHA256 `5622e840e9a8312f930523cd1bedb9830e9ce5679d9aa77d7c1696784eb317c8`; no DNS exception or lock delta is present. `pr31-DEPENDENCY-REVIEW.md` explicitly requests approval before project lock/install and distinguishes parsed publishing attestations from independent cryptographic trust/log verification. Current review does not approve installation or resolve the vulnerable dependency. Any approved later lock/exception needs a delta review. |

## Independent checks and byte scope

- `python3 deploy/tests/test-image-contracts.py`:15 passed,0.699s.
- `python3 deploy/tests/test-ci-ops.py`:16 passed,0.553s.
- Historical all-other full-record digest independently recomputed and matches.
- Read actual before/after cold-start evidence; no Docker rerun competing with
  the investigator's real PostgreSQL suite.

| Reviewed source | SHA256 |
|---|---|
| deploy/tests/check-recovery-image.py | ecc9896db6b4b2f2141e6f686d25aff38fe0e2988ff019f70879c0a7894c5c9a |
| deploy/tests/test-image-contracts.py | 0824f0dcac34c71c2f836ea67b32f568fe62071ded80a02b82a81faf3eb9a787 |
| deploy/tests/test-ci-ops.py | 4f8239d8f1dc281521350e284a81924a170163062223eb8420eaf5b6162384bf |

## Limits and unregistered flags

No unregistered surface was found: importing an authenticated local export and
binding its pinned alias are covered by T1–T2. Unrestricted audit currently still
fails the independently reported dnspython advisory; this report does not mark
that dependency fixed, claim hosted CI success, or authorize publication. Exact
DNS installation/lock changes remain approval-pending and outside these hashes.
Publishing attestation crypto verification and production/provider acceptance
are not established by this review.
