---
phase: 02-authentication
plan: 09
subsystem: ci
tags: [coverage-gate, resend, real-email, push-gate]
requires: [02-07, 02-08]
provides:
  - "CI step enforcing 100% coverage on the critical auth modules"
  - "Human-verified real sign-in email from the verified domain (D-01)"
  - "Phase 2 branch pushed with a PR into develop"
affects: [all later phases]
key-files:
  created: []
  modified:
    - .github/workflows/ci.yml
    - CLAUDE.md
    - .planning/phases/01-skeleton-and-ci/SKELETON.md
key-decisions:
  - "Code review and phase verification ran before the push gate, so the pushed branch is reviewed and verified"
  - "The nist.one deployment becomes the next phase (user decision 2026-10-27)"
duration: 2h (incl. human checkpoint)
completed: 2026-10-27
---

# Phase 2 Plan 09: Coverage gate, real email and push Summary

**The CI backend job now fails if any critical auth module drops below 100% coverage. A real sign-in code arrived from `noreply@nist.one`. Phase 2 is pushed for review.**

## Tasks

| # | Task | Commit | Result |
|---|------|--------|--------|
| 1 | Critical-path coverage in CI, CLAUDE.md commands, SKELETON note on D-03 | a939de1 | actionlint is clean. Every CI job passed locally: backend 135 tests with the critical modules at 100%, frontend, image smoke and Playwright |
| 2 | Real email from the verified Resend domain (checkpoint:human-verify) | — | **Approved** by the user. See below |
| 3 | Push gate (checkpoint:decision) | — | The user chose **push + PR into develop** and deleting the merged Phase 1 branch |

## Task 2: real-email check

- The user set `EMAIL_BACKEND=resend`, their own `RESEND_API_KEY` and `EMAIL_FROM=noreply@nist.one` in the local, git-ignored `.env` (D-02). The key never entered the repo or any committed file.
- The app runs on a remote VDS, so the user reached it with VS Code port forwarding of 5173. A code arrived from `noreply@nist.one` and signing in worked.
- Backend logs for that window: 0 `DEV EMAIL` lines, 0 `bearer` lines, 0 email warnings, one `request-code` 202 and one `verify-code` 200.

## Deviations from Plan

**1. Code review, review fixes and verification before the push gate**
- The plan had the push right after the real-email check. The orchestrator ran the phase code review (02-REVIEW.md) first. That review found 5 warnings, all fixed with regression tests (710e0a9, fe3cd88, 04304ef, 1538f5a, 1673e4e). Phase verification then passed 5/5 before the push.

**2. e2e not rerun locally after the review fixes**
- The dev stack was running with the user's real Resend configuration, so a local Playwright run would have mailed fake addresses. The frontend was untouched by the fixes, the backend changes have API tests, and CI runs the e2e test with the console backend on the PR.

## Notes

- The user's server already has nginx and a `*.nist.one` ZeroSSL certificate (expired 2026-10-21; acme.sh is in manual DNS mode, so it cannot renew by itself). nist.one is proxied by Cloudflare. All of this feeds the deployment phase.
- Review items IN-01..IN-05 are open and advisory. IN-04 (`ENV` defaults to dev) and IN-03 (e2e failure logs print dev codes to public CI logs) belong in the deployment phase.

## Self-Check: PASSED
