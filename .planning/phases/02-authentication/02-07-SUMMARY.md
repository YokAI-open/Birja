---
phase: 02-authentication
plan: 07
subsystem: auth
tags: [refresh-rotation, logout, single-flight, playwright]
requires:
  - phase: 02-authentication
    provides: sessions and cookies (02-04), frontend apiFetch and AccountPage (02-05), rate limits (02-06)
provides:
  - POST /auth/refresh (rotation, 10 s reuse grace, family revoke) and POST /auth/logout
  - single-flight silent refresh in apiFetch with one retry
  - Sign out button and useLogout
  - e2e: access cookie gone, sign out, sign in again
affects: [02-09]
key-files:
  modified: [backend/app/services/auth.py, backend/app/api/v1/auth.py, backend/tests/test_auth_session.py, backend/tests/test_accounts.py, frontend/src/api/client.ts, frontend/src/api/client.test.ts, frontend/src/api/auth.ts, frontend/src/hooks/useAuthMutations.ts, frontend/src/pages/AccountPage.tsx, frontend/src/App.test.tsx, frontend/src/pages/SignInPage.test.tsx, frontend/e2e/auth.spec.ts]
key-decisions:
  - "Refresh keeps the existing yk_csrf value so in-flight requests keep working"
  - "Logout finds the session via the access cookie sid (decoded with verify_exp=False)"
requirements-completed: []
duration: 40min
completed: 2026-10-27
---

# Phase 2 Plan 07: Stay signed in and sign out Summary

Refresh tokens rotate on every use under a row lock, reuse past a 10 s grace window revokes the whole session, and logout revokes server-side via the access cookie's sid; the frontend refreshes silently with a single shared in-flight request and retries once.

## Tasks

| Task | Result | Commit |
|------|--------|--------|
| 1 Backend rotation and logout | rotate_session (FOR UPDATE, grace, family revoke), end_session, /refresh and /logout, tests for every behavior case incl. concurrent race | 7e3ee2f |
| 2 Frontend refresh, Sign out, e2e | single-flight refresh, retry-once, useLogout, Sign out button, unit and e2e coverage | deab068 |

## Verification

- Backend: 135 passed, 99%+ coverage, 100% on the critical modules; ruff, format, mypy clean.
- Frontend: 60 Vitest passed, lint, typecheck, prettier, build clean.
- Playwright (whole suite, health + auth): 2 passed on the rebuilt dev stack, including clearing only yk_access, sign out, and signing in again showing $10,000.00.
- Dev stack torn down (`down -v --rmi local`), temporary `.env` deleted, test stack taken down.

## Deviations from Plan

**1. [Rule 1 - Bug] useLogout uses removeQueries instead of queryClient.clear()**
- **Issue:** `clear()` detaches useMe's observer from the "me" query, so after `setQueryData(["me"], null)` the UI never switched to the sign-in card (unit test failed).
- **Fix:** `removeQueries` with a predicate that drops every query except "me", then `setQueryData(["me"], null)`. All cached data is still cleared and ["me"] is null.
- **Effect:** the plan's `grep -c "queryClient.clear()"` acceptance check prints 0 (it appears only in a comment explaining why).

**2. [Rule 1 - Test adjustment] SignInPage test now expects two /me calls**
- A signed-out `/me` 401 now triggers a silent refresh and one retry, so the initial load makes two calls; sign-in adds none.

## Accepted risk T-02-54

Logout without an access cookie (cookie deleted or cleared by the browser) cannot identify the session, so the session is NOT revoked server-side. Logout still clears all three cookies, so the client loses its refresh token, and the session expires with its refresh token (at most 30 days). Accepted, no design change.

## Known Stubs

None.

## Self-Check: PASSED

Commits 7e3ee2f and deab068 exist; modified files verified present.
