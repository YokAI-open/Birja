---
phase: 03-prices
plan: 10
subsystem: release
tags: [git-flow, release, hotfix, deploy, production]
requires: [03-09]
provides:
  - "v0.2.0 released and deployed to https://birja.nist.one"
  - "Hotfixes v0.2.1 and v0.2.2 released and deployed"
affects: [phase 4]
key-files:
  created:
    - deploy/tests/test-reexec.sh
    - deploy/tests/test-smoke-ports.sh
    - deploy/tests/test-app-services.sh
  modified:
    - deploy/deploy.sh
    - deploy/smoke-prod.sh
    - frontend/e2e/markets.spec.ts
duration: 3h (incl. two hotfixes and human merges)
completed: 2026-10-28
---

# Phase 3 Plan 10: Release 0.2 and production deploy Summary

**Phase 3 is live on https://birja.nist.one as v0.2.2. The scheduler fetches 15 Kraken prices every 60 s and every smoke check passes.**

The orchestrator ran this plan inline. Every push and merge was approved by the user, and the user pre-approved tagging, deploying and opening back-merge PRs.

## Release 0.2 (v0.2.0)

- `release-0.2` was cut from `develop` (`228930c`) with the version bump `12c1f78`. PR #12 into `main` was opened.
- The first CI run failed in e2e. `markets.spec.ts` read `page.url()` once right after `/nope`, racing the client-side redirect. It was fixed on the release branch with `toHaveURL` (`0d6436e`).
- PR #12 was also BEHIND, because `main` had the hotfix-0.1.1 merge commit. Merging `main` into the release (`6d90487`) changed no files.
- With CI green, the user merged it (`2430012`), it was tagged `v0.2.0`, and it was back-merged by PR #13.
- First deploy: migrations 0003→0004→0005 ran and the health check passed, but **the scheduler was not started**. The running v0.1.1 `deploy.sh` had already loaded its old logic before the checkout replaced it on disk. Running it again started the scheduler.
- The smoke check then had one false positive, "scheduler publishes ports": `docker ps` lists the image's `EXPOSE 8000`, but nothing was bound.

## Hotfix 0.2.1 (deploy tooling)

- `747b00a`: `deploy.sh` re-execs the new script once if the checkout changed it. The flock on fd 9 is inherited, the commit is pinned via `BIRJA_DEPLOY_SHA`, and rollback never re-execs. Test: test-reexec 14/14.
- `a4bac80`: the smoke check uses real host bindings (`docker port`). Test: test-smoke-ports 11/11.
- PR #14 was merged (`38ebdca`), tagged `v0.2.1`, deployed, and back-merged by PR #15. Smoke: 36/36 local, 7/7 public.

## Hotfix 0.2.2 (Phase 3 code review)

- CR-01 and WR-01..WR-07 were fixed (see 03-REVIEW.md "Fix log"). Backend has 331 tests and the frontend 118.
- PR #16 was merged (`9ddea52`), tagged `v0.2.2`, and back-merged by PR #17.
- The deploy logged `deploy.sh changed in main; re-running the new version`, the first live proof of the 0.2.1 fix.
- Smoke: 36/36 local, 7/7 public. All 15 coins are priced, the oldest 24 s.
- Scheduler logs are visible: `price cycle: status=ok accepted=15 rejected=0`, 60 s apart.
- The scheduler env is only `DATABASE_URL ENV PRICE_SOURCE REDIS_URL`.

## Deviations from Plan

**1. Two hotfixes inside the release plan.** The double-run and the smoke false positive (found by deploying) became hotfix 0.2.1. The Phase 3 code review findings became hotfix 0.2.2. Both followed git-flow with the user's approval.

**2. Flaky e2e test fixed on the release branch** (`0d6436e`), reaching `develop` through the back-merge.

## Backlog

- The six info items IN-01..IN-06 from 03-REVIEW.md.
- CI does not run the `deploy/tests/*.sh` scripts.

## Self-Check: PASSED
