---
phase: 10-dividend-cash-and-event-history
plan: "06"
subsystem: recovery-verification
tags: [retained-archive, exact-restore, restricted-roles, tls, pre-consumer-gate]
requires: [10-02, 10-04, 10-05]
provides:
  - Complete same-archive retained0007–0014 recovery proof
  - Current-source restricted-role and both verified-TLS lane proof
  - Independent local consumer-readiness review with zero findings
  - Fresh-cluster pregrant ordering repair without weakened canonical validation
affects: [10-07, 10-10, 10-16]
tech-stack:
  added: []
  patterns: [role-independent pregrant structure, preserved failed archive, exact all-mode callable sequence]
key-files:
  created:
    - .planning/phases/10-dividend-cash-and-event-history/10-RECOVERY-REVIEW.md
    - .planning/phases/10-dividend-cash-and-event-history/10-PREGRANT-REVIEW.md
  modified:
    - deploy/verify-restore.py
    - deploy/tests/test-stock-recovery-contracts.py
    - .planning/phases/10-dividend-cash-and-event-history/10-LOCAL-PROOF.md
key-decisions:
  - Pregrant checks expose only independently pinned schema/trigger metadata; all final canonical authority validation remains mandatory.
  - Preserve the first failed archive and rerun every revision/lane using a replacement archive after the reviewed repair.
  - Execute the exact CLI all-mode callable sequence with an explicit retained archive rather than invent an unsupported CLI argument.
requirements-completed: []
requirements-supported: ["DIV-04","DIV-05"]
duration: multi-session; final serial gate1047.402s
completed: 2026-11-13
---

# Plan10-06: Verified recovery before consumers

**Exact encrypted0007–0014 restores, restricted role parity and both TLS lanes
pass before payout-service or mixed-History consumers are introduced.**

## Tasks and commits

1. Actual serial gate/evidence:513f51d. First failed fresh-cluster attempt produced
   regression50eff38 and reviewed repair64f7795; replacement gate passed.
2. Separate independent gsd-code-reviewer pass:10-RECOVERY-REVIEW.md, clean with
   zero blockers/warnings. This is distinct from the executor and prior targeted
   repair reviewers. Root commits the report and canonical completion separately.

## Actual final proof

Retained archive:
`/tmp/birja-backup-test-phase10-preconsumer-fixed/recovery.tar`
SHA256:`1faa8277951d0c2a66ac10ffb8b39b5f85372acdacd10b3b3348126c90052cc1`
Size152320000bytes; deploy-recovery-v2,0007–0014. All11currentCORE/unit bytes,
archive hash and six fixture/bootstrap/migration hashes match before/after.
Independent reviewer recomputed them, rather than relying only on report fields.

| Gate | Actual seconds | Result |
|---|---:|---|
| Retained encrypted0007–0014 |503.681|PASS|
| Restricted roles |210.330|PASS|
| Populated verify-full TLS |163.830|PASS|
| Fresh verify-full TLS |162.172|PASS|

Wrapper total1047.402seconds includes orchestration overhead. Actual command:
`python3 /tmp/birja-phase10-06-fixed-gate.py`. This delegates exactly the CLI
all-mode sequence:roundtrip(explicit_archive),roles(),thenasserttls()==tls(fresh).
The CLI has no all-mode external-archive parameter; no literal CLI invocation
or unsupported argument is claimed. Archive recovery uses the retained tooling;
roles/TLS use the pinned current source/fixtures, with hashes verified separately.

Actual full SQL contracts23/23passed,zero skips125.294s after the repair. The
focused genuine fresh-cluster/dispatch tests passed2/2,30.636s; independent
repair recheck2/2,30.884s. Scoped syntax/RuffF/whitespace passed. No new package.

Logs/report:
- `/tmp/birja-phase10-06-fixed-all.log`
- `/tmp/birja-backup-test-phase10-preconsumer-fixed/gate-report.json`
- `/tmp/birja-phase10-06-sql-green.log`
- `/tmp/birja-phase10-pregrant-review-recheck.log`

Exact data/schema/sequences/financial authority/source identity and corruption
controls pass at every revision.0013 restored actual stock receipt/portfolio
reads preserve quarantine.0014 original/decision/held state, exact saved dividend
fingerprint and runtime42501denials pass. Roles include63denials and fresh/upgrade
parity. Both TLS lanes retain all old consumers and genuine new dividend SQL,
stock/crypto cash/race cases, badCA/hostname/plaintext and isolation checks.
This does not claim that future app dividends.py/History API exists yet.

## Reproduced failure and necessary deviation

Old archive637516d8ccd487ef2c45ccba395782cba035d21d737abdca2827ffa9a9e7bbc5
passed0007–0013 then failed0014 at459.772s before roles/TLS. A genuinely fresh
restore cluster lacked birja_action_operator; the dividend pregrant canonical
query attempted resolution privilege lookup before that role's reconstruction.
Plan05's same-server clone already contained the role and masked this ordering.

Parent explicitly extended ownership to verifier and SQL regression tests.
RED50eff38 reproduces the actual fresh pg_restore path. Repair64f7795 uses a
helper returning only schema/triggers, replaces exactly one trusted resolution
fragment, and fails closed if dispatch changes. Full canonical validation and
reconstruction order are unchanged; no grants precede authentication. Fresh
success, function/schema corruption, unsafe role and runtime quarantine cases
pass. Independent10-PREGRANT-REVIEW.md is clean. Old archive/report stay intact;
only verify-restore changed among the11tool/unit files. Complete replacement
archive replay, not just the failing revision, supplied the final passing proof.

## Threat controls and boundaries

Task2 independently maps T-10-06-01/02/03/SC to actual financial authority,
immutable source/identity/corruption evidence, serial bounded resource ownership,
and unchanged approved tooling. No blanket ASVS certification is claimed.
Reviewer independently confirmed zero containers/volumes/networks for birja-test,
birja-ops-test and birja-restore-check. No source rows or live operations touched.

No provider access, credentials/.env read, B2 operation, timer/installed-tool
change, production access/deployment or publication. Existing live7/8 activation
and publication deferrals remain. Next07/10 local consumers may proceed; final
integration/security/browser/current-service recovery and actual owner UI/native
zoom acceptance remain later obligations. All Phase10 requirements stay pending.

## Self-Check: PASSED

Both tasks have genuine evidence and separate review. Retained archive/current
source hashes and cleanup match. No failed first attempt is represented as a pass.
