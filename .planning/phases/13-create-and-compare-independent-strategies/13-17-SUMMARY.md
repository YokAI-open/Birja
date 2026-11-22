---
phase: 13-create-and-compare-independent-strategies
plan: "17"
subsystem: testing
tags: [security, coverage, immutable-images, encrypted-recovery, postgres, tls]
requires:
  - phase: 13-16
    provides: Implemented management journeys and current source-bound UI evidence
  - phase: 13-15
    provides: Complete security graph and current0020/retained recovery runner
provides:
  - Actual complete final-source financial/security/browser and five-image qualification
  - Uninterrupted seven-stage exact encrypted recovery at the identical frozen source
  - Authenticated current0020 and complete retained0017 cold restore, TLS parity and rollback/refusal receipts
affects: [13-18, phase-13-verification, phase-14, phase-15]
tech-stack:
  added: []
  patterns: [frozen-source whole-command qualification, private first-use immutable image reuse, durable one-shot test supervision]
key-files:
  created:
    - .planning/phases/13-create-and-compare-independent-strategies/13-LOCAL-VERIFICATION.md
    - .planning/phases/13-create-and-compare-independent-strategies/13-RECOVERY-PROOF.md
  modified: []
key-decisions:
  - "Qualify only actual whole commands run consecutively at the same frozen source; preserve earlier failures and diagnostic composites separately."
  - "Retain exact image-ID authentication and reuse private campaign bindings rather than rebuild an already recorded mutable tag."
  - "Validate the exact stripped child tool environment before the final long run; use a durable one-shot PID/receipt without a recurring schedule."
requirements-completed: [PSAFE-07, PFUND-01, PFUND-02, PFIN-01, PFIN-04, PVIEW-02]
duration: 103min final complete campaign, with prior failed attempts preserved separately
completed: 2026-11-19
---

# Phase 13 Plan 17: Complete Security and Exact Recovery Qualification

**One frozen reviewed revision passes the actual full financial/security/browser
graph and all seven authenticated same-archive recovery stages, preserving exact
independent strategy state, restricted TLS authority and retry evidence.**

## Performance and actual results

Final campaign:2026-11-18T22:21:34.733760Z to2026-11-19T00:04:29.267852Z,
6174.534104s total, approximately103minutes;2/2tasks, three evidence documents.
Tested HEAD9527e358bc6953cec7580043703324db194ba396,
tree9e2af2ddb10ddd28ce5df71d445a42bb39d170e0. Later commits only record the
measured result; they do not replace the tested HEAD with a newly tested claim.

| Whole command | Result |
|---|---|
| python3 deploy/tests/run-portfolio-validation.py --suite all-security | Exit0,3373.046358s |
| python3 deploy/tests/run-portfolio-validation.py --suite recovery | Exit0,2792.053910s, all7stages passed-authenticated |

Full backend3343tests/114warnings pass; overall99.86% and all61critical modules
100% statements/branches (5287/1668, zero misses). Frontend55suites/1194tests,
lint/types/format/build pass,96.63%statement/93.92%branch coverage. The actual
unfiltered12-spec browser suite passes79/one retained deployed-CSPskip in714.7s,
including all20new management cases. Complete infrastructure contracts and all
five immutable image policies pass. Python audit is clean; npm has14moderate,
zeroHIGH/CRITICAL/no blocking findings. Fresh image reports have0/0/0
qualifying/accepted/blocking findings on every target. Issue35 remains tracked;
no dependency change, vulnerability remediation or expanded waiver is claimed.

The same source then passed image-transition, retained-roundtrip, current0020-cold,
roles, upgraded TLS, fresh TLS and selected rollback. Both genuine0017/current0020
cold paths destroyed the source server before exact independent-oracle restore.
Fresh/upgraded restricted-TLS authority compares exactly. Supported rollback and
unsupported refusal preserve original data; current incompatible writers refuse.
Final output is same_archive_final_ci=true, archive219289600bytes SHA256
6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92.
The actual new producer used an absent exclusive canonical destination; equal
deterministic content to a preserved diagnostic is not archive reuse.

## Task commits and receipts

1. Task1 complete local security evidence:5acdae8.
2. Task2 authenticated seven-stage recovery evidence:f4ec214.
3. This summary and precise starting-cash-grant wording complete the metadata.

Detailed source hashes, actual five-image IDs/report hashes and oracle/guard
outcomes are in [13-LOCAL-VERIFICATION.md](13-LOCAL-VERIFICATION.md) and
[13-RECOVERY-PROOF.md](13-RECOVERY-PROOF.md).
Private complete receipts are under
/tmp/birja-phase13-plan17-campaign6-20261118-9527e35/:

- all-security.log SHA9ee807da3bcc03f8d062a2da9c46b80df5cf8b84fa4becafc61d9e085a3e56bb.
- recovery.log SHA1d08f0b14d96e4e2bb8d9fdca6d1afa863653665961a298b40dc8054b327a896.
- source-receipt.json SHAf87c577da55dafaf5cc8b2d5231b0ebb0ae7c0d4c9f8877f3a9c9688bdf0127a.
- receipt.json SHA09909cf5b6874c2304b34d6908db90db3408a3778e53612e17b52b1850e8c9b1.

HEAD/all1760tracked inputs, current UI render inputs and all preserved archives
remained unchanged throughout both complete commands. All21owned container/
network/volume checks are empty. The current UI source/artifact verifier also
passes; packet724607e8... and separately recorded owner UI/native200responses
remain valid without recapture or rewritten automated acceptance flags.

## Deviations and retained history

Parent-directed, independently reviewed repairs discovered during earlier full
attempts are recorded in13-REVIEW/13-17-FIXTURE-REVIEW/13-SECURITY. They include
stale current-schema fixtures and exact refusal/coverage expectations; a genuine
owner/FK lock inversion fixed at99166d9; stale authenticated source admission
fixed at74ee5ea; and repeated image-tag builds replacing a recorded OCI identity,
fixed by RED5693083/GREEN312d8c9. Exact current integrity bindings were measured,
and historical migrations/source profiles and strict guards were preserved.
The actual old failed proof and subsequent diagnostic stages remain separate;
none was composed into this final result.

Campaign5 failed at this same repository source because this executor's private
launcher PATH omitted /usr/sbin, hiding existing nginx. Its53minute failed attempt
is preserved, not counted as a pass. Corrected private orchestration preflighted
existing tool bindings, actual nginx -t, recovery runtime/source/image and pinned
restic provenance before campaign6. No package installation, repository/runtime
repair or gate relaxation was needed for that avoidable launcher error.

Because source had to remain frozen until both commands finished, the evidence
documents and per-task commits were written afterward. The parent owns global
STATE/ROADMAP/requirements and final goal/security/validation closeout; this
executor deliberately does not mutate those files or mark the entire phase done.

## Scope and next readiness

No application stub was introduced: this plan produces measured evidence, and
both required commands actually ran. No new trust boundary beyond the authored
test/archive/source/image threat register was added. No provider access, private
.env read, production action, package/pin change, publication or push occurred.
Phase7live gaps and accepted issue35 remain tracked separately; public portfolio
deletion/freeze remains Phase14 and full lifecycle acceptance remains Phase15.

The parent may now finish Plan18's persisted acceptance and independent goal
verification using the successful final receipts. This summary completes Plan17,
not global phase or milestone acceptance.

## Self-Check: PASSED

Both task evidence files exist, their5acdae8/f4ec214commits resolve, and all final
raw command/source/report/status/receipt hashes were checked against disk. The
canonical status lists exactly seven passed-authenticated stages and the log
contains the same-archive final success marker. Supervisor receiptok=true,
sources/head/preserved archives unchanged and cleanup_empty=true. Original
failed/diagnostic artifacts and unrelated.claude remain preserved.
