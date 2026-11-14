---
phase: 04-trading
plan: 09
subsystem: testing
tags: [trading, validation, github, release, codex]
requires: [04-01, 04-02, 04-03, 04-04, 04-05, 04-06, 04-07, 04-08]
provides:
  - Approved live-price dev trading check
  - Phase 4 PR into develop and release-now decision
affects: [04-10, 05-portfolio-and-history]
tech-stack:
  added: []
  patterns: []
key-files:
  created: [.planning/phases/04-trading/04-09-SUMMARY.md]
  modified: [.planning/phases/04-trading/04-VALIDATION.md]
key-decisions:
  - "User chose push-pr and release-now; the user merges PRs after green CI."
requirements-completed: [TRADE-01, TRADE-02, TRADE-03, TRADE-04, TRADE-05, TRADE-06, TRADE-07, TRADE-08]
release_decision: release-now
pr: https://github.com/YokAI-open/Birja/pull/19
completed: 2026-10-29
---

# Phase 4 Plan 09: Local validation, dev approval and PR Summary

Market buys and sells passed local validation and the user's live-price dev
check; PR #19 targets develop, with release 0.3 chosen for the next plan.

## Task Commits

1. Task 1: `3c834f5` — record the full local validation results.
2. Task 2: `0ea63e9` — record approved manual trading and aggregate evidence.
3. Task 3: `f5294a9` — fix the named preview/fill regions exposed by CI;
   push and PR creation are remote actions, with CI result recorded below.

Related setup commit: `cb122e6` adds the user-requested Codex migration.

## Verification

### Full local suite (recorded run)

The full CI-equivalent run recorded at `3c834f5` passed backend 476 tests
(99.89% total coverage, critical-path list 100%), frontend 161 tests
(98.88% coverage), and deploy tests 58/58. Lint, formatting, types, build,
pip-audit and npm audit at the high threshold passed. This resumed execution
did not rerun the backend suite: backend, dependency, CI and deployment
code was verified unchanged since that run. Critical-path lists in ci.yml
and CLAUDE.md match and include trade_math.py and trading.py. No lockfile
changes against origin/develop and no tracked Resend-key pattern matches.

Codex setup validation passed locally and in a separate checkout directory:
68 skills and 33 GSD roles.

### User's live-price dev check

- User said `go` before rebuilding, and `approved` after testing.
- `docker compose up --build -d --wait` exited 0.
- Backend, frontend, Postgres, Redis and scheduler were healthy.
- Alembic: `0007 (head)`.
- Price aggregate at verification: `15 17` (15 prices; oldest 17 seconds).
- Trade count after user approval: `2`.
- The assistant sent no login request and placed no trades.

### GitHub CI

Run [40842519915](https://github.com/YokAI-open/Birja/actions/runs/40842519915)
passed backend, frontend, image, e2e and ci-pass on `f5294a9`. PR #19
was merged by the user into develop as `5dc514d` after those checks passed.

Initial run `40841931118` passed backend/frontend/image but failed the trade
e2e because the preview and fill cards had no accessible region names. The
component tests were changed to query the same named regions; before the
fix, five assertions failed and 20 tests passed. Commit `f5294a9` gives the
summary card a region role named by its current visible heading. Afterwards
all 161 frontend tests passed (98.88% statements, 99.76% lines), as did lint,
types, formatting and build. The Playwright assertions were retained.

## Decisions Made

The user explicitly chose `push-pr, release-now` before the push or PR.
The feature branch was pushed normally and PR #19 was opened into develop.
The user must merge with Create a merge commit after ci-pass is green.
Plan 04-10 continues after that merge; no production action occurred here.

## Issues Encountered

Dev sign-in initially failed because Resend returned 401 on email sending.
The user updated the dev API key, then authorized backend recreation; the
backend became healthy and the user subsequently approved the dev check.
No secret, code, recipient address or account balance was recorded.

## Deviations from Plan

- Resumed the already-recorded Task 1 validation rather than repeating it,
  after confirming backend and verification inputs had not changed;
  frontend validation was rerun for the CI-discovered accessibility fix.
- Fixed missing named trade regions found by the first CI e2e run, with
  component-level regression evidence and a normal follow-up push.
- The user migrated to Codex and requested its setup be committed alongside
  trading. PR attribution describes Codex and prior Claude work accurately.

## Next Phase Readiness

Release decision is release-now. The user merged PR #19;
continue 04-10 on release-0.3 under the existing release and deploy gates.

## Self-Check: PASSED

Summary and validation files exist; recorded commits exist; PR #19 targets
develop and is merged; all five checks on the implementation head passed.
Task 1 is backed by the recorded local run, Task 2 by explicit user approval,
and Task 3 by the explicit push-pr/release-now choice and GitHub CI results.
