---
phase: 14-end-strategies-safely
plan: "18"
subsystem: testing
tags: [portfolios, recovery, verification, ui-evidence]
requires:
  - phase: 14-17
    provides: Implemented lifecycle journeys and accepted visual review
provides:
  - Owner-amended source-bound local security qualification
  - Actual current0023 source-destroyed recovery and exact same-archive component proof
  - Current R7 review packet with human acceptance still pending
affects: [14-19, phase-goal-verification]
tech-stack:
  added: []
  patterns: [explicit component evidence reuse, immutable archive provenance]
key-files:
  created:
    - backend/tests/test_portfolio_closure_critical.py
    - .planning/phases/14-end-strategies-safely/14-RECOVERY-PROOF.md
    - .planning/phases/14-end-strategies-safely/14-18-SUMMARY.md
  modified:
    - .planning/phases/14-end-strategies-safely/14-18-PLAN.md
    - .planning/phases/14-end-strategies-safely/14-LOCAL-VERIFICATION.md
    - .planning/phases/14-end-strategies-safely/14-REVIEW.md
    - .planning/phases/14-end-strategies-safely/14-SECURITY.md
    - .planning/phases/14-end-strategies-safely/14-UI-REVIEW.md
    - .planning/phases/14-end-strategies-safely/14-VALIDATION.md
key-decisions:
  - Explicit owner amendments permit authenticated unchanged-component reuse; failed whole runs remain failed.
  - Select the real same-archive installed verifier for cold recovery; never repin historical source or replace financial verification.
  - Full CI before merge and both Plan19 human outcomes remain required.
requirements-completed: []
requirements-addressed: [PMGT-03, PMGT-04, PMGT-05, PFIN-05, PFIN-06, PCTX-03, PSAFE-01]
duration: about 30h elapsed including interruptions
completed: 2026-11-21
---

# Phase14 Plan18: Local security and same-archive recovery qualification

**Both amended tasks pass with exact component provenance, genuine current cold recovery and unchanged financial/security thresholds.**

| Scope | Actual result |
|---|---|
| Backend | R2 source09c70f5:3691passed;64critical modules100%, overall99.87%. All277 relevant backend files remain identical. |
| Frontend | R2:1330passed/build/audits at unchanged155-file inputs; fresh lint/type/format and corrected normal History pass. |
| Browser | Explicit composite92 prior passes + corrected History +1retained CSPskip. No whole-browser pass or forced optional-branch coverage claimed. |
| Remaining security | All28 required command components pass through authenticated16+12 receipts; all5 strict images HIGH0/CRITICAL0. |
| Recovery |6/6 actual remaining components pass, exit0/2266.665s; original retained results reused only under explicit amendment. |
| Reviews | Distinct source code/security/UI roles retained; bounded repairs/context-driver rechecks0blockers/0warnings. |
| Human/global state | Plan19 owner UI/native200 pending; all seven whole requirements remain parent-owned/pending. |

Recovery continuation source`628f0afcf9a6ae56d3948a81d40373d17d157bdc` verifies actual
fixed0020/current0023 source-destroyed cold restores, independent before-oracles,
roles, upgraded0014/0020 and fresh TLS, selected rollback/refusal and original
financial replay. Exact cold/upgraded/fresh catalogue/object/default ACL triples
match. The original archive remains:

`/tmp/birja-phase14-proof/recovery.tar.gz`

SHA256`1a41c8b9a55986998e46ea6341dfea93dd2b7c8da0e0428af08251d21d6b742f`,
inode943123/device64512,244346880bytes, producer source2f70a12. Original failed
whole status is unchanged; whole7 and same_archive_final_ci remainfalse.

Current packet:`/tmp/birja-phase14-ui-review.zip`, SHA256
`886805a094fad7495ae53539da7ea80d0ddff6c67b1ce0aa0465899a493d32e0`.
Actual6-case R7 capture239.459s,114 state pages/190PNG/114 traces/index419,
strict current/ZIP verification and190 offline layouts with zero HTTP pass.
Both capture human flags remainfalse. Source747d5d7/render digest9b62b226…a7f6
remain valid at unchanged render inputs; original visual acceptance review is reused.

## Evidence and cleanup

- [Local ledger](14-LOCAL-VERIFICATION.md), [recovery proof](14-RECOVERY-PROOF.md),
  [review dispositions](14-REVIEW.md), [security](14-SECURITY.md).
- Private root:`/tmp/birja-phase14-campaign-plan18-repair/` contains
  `reuse-input-analysis.json`, `component-qualification.json`,
  `recovery-components-final-integrity.json`, `final-preserved-evidence.json`,
  driver/hash bindings and preserved scan reports in`image-reports-final/`.
- Original failed whole-security R1/R2, failed browser runs and genuine recoveryR1
  remain preserved. Recovery component receipt:
  `/tmp/birja-phase14-campaign-recovery-components-plan18-r1`.
- All original owned groups and exact synthetic project resources are empty;
  source/tracked/CORE/unit/image/archive guards pass. Eight prior/current archive
  and packet hashes match. Existing unrelated services/data remain untouched.

## Commits

Task1 implementation/review/evidence:
`407a6c0`, `d2e8885`, `5e0803a`, `a21eae3`, `64c35b3`, `48aec5b`,
`1c97c50`, `7a29129`, `09c70f5`, `85c6040`, `747d5d7`, `429edca`, `2f70a12`.

Task2 explicit amendment and final task evidence:`628f0af`, `d3146ad`.
Proof documentation was committed after guarded work ended to preserve its freeze.

## Deviations and limits

The owner explicitly amended both original whole-local-run criteria after
measured failures. Exact unchanged inputs justify reuse; every still-required
component ran. No successful whole all-security/browser/recovery or same-head
hosted CI is claimed. Full CI before merge remains required.

Scoped fixes cover source inventory traversal, long-suite quote clocks, bounded
closure retries/pure result validation, browser fixture gate/public DELETE/
finite console capacity/deadlines, and stale restore unit signatures. Historical
source hashes, SQL/schema/ACL, dependency/image versions and issue35 scope remain
unchanged. The0020 cold refusal correctly exposed missing installed source context;
the private factory selects genuine archived code, without production edits or
verify/SQL/row/result substitution. Failed timing experiments were removed and
preserved honestly. No product stubs or new external services were introduced.

No push, merge, deployment, provider operation or global requirement advancement
occurred. Parent completes Plan19 and independent phase-goal verification.

## Self-Check: PASSED

All8 required evidence files and15 recorded task commits exist. Final cleanup,
archive identity, preserved hashes and current packet verification are attested
by the linked receipts; no additional test run is inferred from this check.
