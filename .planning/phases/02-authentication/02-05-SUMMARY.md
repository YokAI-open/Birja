---
phase: 02-authentication
plan: 05
subsystem: frontend-auth
tags: [react, tanstack-query, playwright, shadcn]
requires:
  - phase: 02-authentication
    provides: request-code, verify-code, /me, cookies and CSRF (02-02..02-04)
provides:
  - apiFetch (single /api fetch wrapper, CSRF header, ApiError) and auth API calls
  - useMe, useRequestCode, useVerifyCode
  - SignInPage (email -> code), AccountPage, /me auth switch in App (no router)
  - formatUsd string-only money formatter
  - e2e sign-in happy path reading the code from docker compose logs
affects: [02-07]
tech-stack:
  added: []
  patterns: [auth state derived only from the ["me"] query; fixed client-side error copy]
key-files:
  created:
    - frontend/e2e/auth.spec.ts
    - frontend/src/api/client.ts
    - frontend/src/api/auth.ts
    - frontend/src/lib/money.ts
    - frontend/src/components/ui/input.tsx
    - frontend/src/hooks/useMe.ts
    - frontend/src/hooks/useAuthMutations.ts
    - frontend/src/pages/SignInPage.tsx
    - frontend/src/pages/AccountPage.tsx
  modified:
    - frontend/src/App.tsx
    - frontend/src/App.test.tsx
key-decisions:
  - "Error text comes from a fixed client map keyed on status/code; server messages are never rendered"
  - "Code input strips non-digits and Sign in stays disabled until 6 digits"
requirements-completed: [AUTH-01, AUTH-02, AUTH-04, ACCT-01]
duration: 20min
completed: 2026-10-27
---

# Phase 2 Plan 05: Browser sign-in Summary

**A user can enter an email, type the code from the backend log, see exactly $10,000.00, and stay signed in after a reload, driven by a single /me auth switch with no router.**

## Tasks

| Task | Commit |
|------|--------|
| 1. Failing e2e + apiFetch, auth calls, formatUsd | a58fd36 |
| 2. Sign-in card, account view, /me switch (e2e green) | a083e78 |

## Verification

- Vitest: 53 passed, coverage 98.2% stmts / 94.6% branches (thresholds 80%).
- eslint, tsc, prettier, vite build clean.
- RED confirmed (auth.spec failed, health.spec passed) before Task 2; after rebuild, Playwright: health + auth both pass.
- Acceptance greps: no localStorage/sessionStorage, no react-router, no useEffect or raw hex in the new pages, no package.json/package-lock.json changes.
- Dev stack torn down (`down -v --rmi local`), temporary `.env` removed.

## Deviations from Plan

- `npx shadcn add input` worked without adding any npm package; its output (dark variants, 36px) was rewritten to MASTER tokens (h-12, rounded-control, bg-popover, no dark).
- Loading skeleton uses `role="status"` plus aria-label so the "Loading your account" accessible name is queryable.
- 429 without a Retry-After header shows "Too many attempts. Try again in a moment." (plan did not specify).
- A 422 on the code step falls to the generic message (the "valid email" copy applies only to the email step).

## Known Stubs

None.

## Self-Check: PASSED
