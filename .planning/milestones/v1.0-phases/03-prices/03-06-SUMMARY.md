---
phase: 03-prices
plan: 06
subsystem: frontend
tags: [freshness, badge, prices, a11y]
requires: [03-04]
provides:
  - formatAge/freshnessStatus/statusLabel (lib/age.ts)
  - useNow display timer
  - FreshnessBadge + Badge `warning` variant
  - Markets "Updated" column and "Oldest price" header
affects: []
key-files:
  created:
    - frontend/src/lib/age.ts
    - frontend/src/lib/age.test.ts
    - frontend/src/hooks/useNow.ts
    - frontend/src/hooks/useNow.test.ts
    - frontend/src/components/FreshnessBadge.tsx
    - frontend/src/components/FreshnessBadge.test.tsx
  modified:
    - frontend/src/components/ui/badge.tsx
    - frontend/src/pages/MarketsPage.tsx
    - frontend/src/pages/MarketsPage.test.tsx
decisions:
  - "Icons: CircleDot (Live), Clock (Delayed), TriangleAlert (Stale), all aria-hidden; text label carries the meaning"
  - "One page-level useNow(1000); age = age_seconds + elapsed since dataUpdatedAt; thresholds from the API response"
metrics:
  completed: 2026-10-28
  tasks: 2
---

# Phase 3 Plan 06: Price freshness UI Summary

Every Markets row shows a text-labelled badge ("Live · 42s ago", "Delayed · 2m ago", "Stale · 7m ago") that ticks each second and flips status using the API's fresh_seconds/stale_seconds (D-03), with "Oldest price Xm ago" in the header.

## Tasks

| Task | Result | Commit |
|------|--------|--------|
| 1 | age helpers, useNow, warning badge variant, FreshnessBadge, tests | f3fcf3d |
| 2 | Updated column, ticking ages, oldest-age header, tests | 09c2e14 |

## Verification

- Vitest 116 tests pass; coverage 98.9% statements, 95.5% branches.
- lint, typecheck, prettier, build pass. Playwright not run (per instructions).

## Deviations from Plan

- Added `hooks/useNow.test.ts` (plan listed only the hook; the behavior section required its tests).
- `FreshnessBadge` is a named export (no default).
- Worktree started on a wrong base; reset to f36577d as the branch check instructed.

## Known Stubs

None.

## Self-Check: PASSED
