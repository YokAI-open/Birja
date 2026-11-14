---
phase: 03-prices
plan: 01
subsystem: frontend-e2e
tags: [react-router, playwright, e2e, git-flow]
requires: []
provides:
  - feature/phase-03-prices branch with planning commit
  - react-router 8.5.1 pinned exactly
  - e2e/helpers.ts (readCodeFromLogs, signInNewUser)
  - RED e2e/markets.spec.ts
affects: [03-04]
tech-stack:
  added: [react-router@8.5.1]
key-files:
  created: [frontend/e2e/helpers.ts, frontend/e2e/markets.spec.ts]
  modified: [frontend/package.json, frontend/package-lock.json]
decisions:
  - "react-router 8.5.1 approved by user (blocking legitimacy gate); no install scripts (only build/watch/typecheck scripts); no react-router-dom"
metrics:
  completed: 2026-10-28
  tasks: 3
---

# Phase 3 Plan 01: Branch, react-router and RED markets e2e Summary

Phase 3 branch started, react-router 8.5.1 pinned exactly after user approval, and the Phase 3 happy path captured as a failing (RED by design) Playwright spec.

## Tasks

| Task | Result | Commit |
|------|--------|--------|
| 1 | Branch `feature/phase-03-prices` from up-to-date develop; planning files committed | 895f02e |
| 2 | User replied "Approved" for react-router@8.5.1; `npm view` scripts showed no preinstall/install/postinstall | n/a |
| 3 | Installed react-router, added `e2e/helpers.ts` and `e2e/markets.spec.ts` | 1bcceeb |

## Verification

- `npm ls react-router` shows 8.5.1; typecheck, lint, prettier pass.
- `npx playwright test --list` lists the new test. It was not executed (dev stack uses real email; CI runs it with PRICE_SOURCE=fake).
- `auth.spec.ts` untouched (03-04 switches it to the helper).
- `npm audit --audit-level=high`: only 3 pre-existing low findings (shadcn tooling).

## Deviations from Plan

None in behavior. The spec imports `./helpers.js` because the node tsconfig requires explicit extensions.

## Known Stubs

None. The spec is RED until 03-04, 03-06 and 03-07 land.

## Self-Check: PASSED
