---
phase: 04-trading
plan: 10
subsystem: release
tags: [git-flow, release, trading, production, deploy]
requires: [04-09]
provides:
  - "v0.3.0 release with trading"
  - "v0.3.1 freshness hotfix after final code review"
affects: [05-portfolio-and-history]
key-files:
  modified:
    - backend/pyproject.toml
    - backend/uv.lock
    - frontend/package.json
    - frontend/package-lock.json
    - backend/app/services/trading.py
    - backend/tests/test_trading_service.py
requirements-completed: [TRADE-01, TRADE-02, TRADE-03, TRADE-04, TRADE-05, TRADE-06, TRADE-07, TRADE-08]
completed: 2026-10-29
metrics:
  tasks: 3
release_decision: release-now
release_tag: v0.3.0
latest_release_tag: v0.3.1
latest_release_sha: 0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7
release_sha: 6425dad1b9c5718eb969688cbe3e2b0ac7cd3224
release_pr: https://github.com/YokAI-open/Birja/pull/20
backmerge_pr: https://github.com/YokAI-open/Birja/pull/21
---

# Phase 4 Plan 10: Release 0.3 and production deploy Summary

**Trading shipped in v0.3.0 with user-approved live buy/sell verification.
The reviewed freshness fix is now live in v0.3.1, with green release and
back-merge CI and passing origin/public smoke checks.**

## Authorization

The user chose `push-pr, release-now`, approved the prepared release, and
then explicitly said `yes, do it all`. This authorized remaining release
pushes, PRs, merge commits after green CI, tag publication, back-merge and
deployment. The assistant retained the final live browser trade check for
the user and did not authenticate or place trades on the user's behalf.

## Task 1: Release decision

PR #19 merged into develop as `5dc514d`; 04-09 records release-now.

## Task 2: Git-flow release

- Cut release-0.3 from updated develop.
- `22ff0d5` updates both project versions and lockfile project entries to
  0.3.0. Both lockfiles were verified to contain no dependency changes.
- Local release validation: 476 backend tests, 99.89% total coverage,
  critical paths 100%; 161 frontend tests, 98.88% statements and 99.76%
  lines. Lint, formatting, mypy, TypeScript and frontend build passed.
- PR #20 into main was BEHIND on production hotfix ancestry. `b605079`
  merges origin/main without changing the release tree.
- Run `40843969400` passed backend, frontend, image, e2e and ci-pass.
- PR #20 merged as `6425dad`; annotated v0.3.0 was published on that SHA.
- `0388183` merges the tagged main commit back into release-0.3 without
  changing files, so the tag will also be an ancestor of develop.
- PR #21 passed all five checks in run `40844466345` and was merged
  into develop as `130dfb6`. Read-only GitHub state showed it already
  merged when the assistant reached the merge step. The published tag
  was verified as an ancestor of both origin/main and origin/develop.

## Task 3: Production

- Before deployment, read-only aggregate check found 0 accounts with
  sub-cent cash.
- `deploy.sh` ran once, exited 0 and printed `Deploy complete: main`;
  migrations 0006/0007 applied and services became healthy. Deployment log
  entry `2026-10-29T08:50:10Z` and checkout match the release SHA.
- Origin smoke passed 38/38; public smoke passed 9/9. Both modes
  verified holdings returns 401 and quote returns 403 signed out. All
  15 coins were priced; oldest age 28 seconds at the origin smoke check.
- User replied `appoved` to the live-site buy/sell check (accepted
  as approval). Aggregate production trade count increased from 0 to 2.
  No individual balances, addresses, codes or secrets were recorded.

## Deviations from Plan

- PR #19 merged before its final planning closeout commits were created.
  The two planning-only commits were carried onto the release branch,
  alongside the four version files.
- The user's explicit blanket approval superseded repeated per-step
  approval prompts and authorized the assistant to merge after green CI.
- Main's tagged merge commit was included in the back-merge ancestry so
  the release tag is an ancestor of both main and develop.

## Next Phase Readiness

Trading is released and the final live check is approved. Code review is
clean, regression checks passed and final goal verification passed 5/5
(`04-VERIFICATION.md`). Phase 5 is ready for discussion and has not started.

## Self-Check: PASSED

Version files at tag v0.3.0 read 0.3.0; the published release tag is an ancestor of
main and develop; deployed SHA matches the tag; all release and back-merge
checks passed; smoke suites passed; the user approved the final live check.

## Final review hotfix: v0.3.1

- Review CR-01 found the clock was captured before account lock/price-read
  waits. A 119-second-old price could fill at actual age 121.
- `0d52202` reproduces the defect with actual PostgreSQL blocking and a
  controlled clock: 3 stale cases fail before the fix, 2 fresh controls pass.
- `d0ee5fd` samples the real clock at freshness enforcement after the DB
  waits; explicit clocks and replay-before-freshness ordering remain intact.
- Full backend suite: 481 passed; overall 99.88%; critical list 100%;
  lint, format and mypy passed. The reviewer independently confirmed closure.
- Hotfix PR #22 passed all five checks in run `40847508779`, then merged
  into main as `0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7`.
- Annotated v0.3.1 was published. Back-merge PR #23 passed all five checks
  in run `40848088770` and merged as `dd50ad77bfc99c1b7905227973e530995e2c57cc`.
- Both main and develop contain the patch tag. This follows git-flow under
  the user's existing authorization to finish release actions.
- Pre-patch production cents check: 0. One patch deploy exited 0 and
  printed Deploy complete: main; no new migrations were introduced.
- Patch origin/public smoke passed 38/38 and 9/9; 15 coins priced, oldest
  age 36 seconds. Production checkout and deploy log match v0.3.1.
- Patch deploy log: `2026-10-29T09:15:27Z 0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7 /var/www/birja/releases/0107706-20261029T091506Z main`.
- The prior user-approved live buy/sell flow remains applicable; UI and
  ordinary successful trading behavior are unchanged. No repeat user test
  was requested; the new lock-delay edge case is covered by the regression.

The post-release code-review fix is an additional deviation handled inside
this release plan, following the Phase 3 hotfix precedent. Final phase goal
verification subsequently passed all five roadmap criteria and all eight
TRADE requirements; Phase 4 is complete. No further deployment is needed
for the planning-only closeout PR.
