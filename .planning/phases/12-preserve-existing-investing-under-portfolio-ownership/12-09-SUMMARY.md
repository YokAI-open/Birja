---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "09"
subsystem: auth
tags: [identity, api-versioning, otp, session, csrf, compatibility]
requires:
  - phase: 12-08
    provides: identity-only account/auth services independent of portfolio count
provides:
  - Actual identity-only v2 verify-code and me routers with existing OTP/session authority
  - Deterministic legacy409 refusal before OTP consumption or session effects
  - Real-router isolated HTTP composition and preserved auth/security regression coverage
affects: [12-15, 12-19, 12-26, 12-27]
tech-stack:
  added: []
  patterns: [thin identity-only routers, explicit compatibility refusal, test-only router composition]
key-files:
  created:
    - backend/app/api/v2/auth.py
    - backend/app/api/v2/me.py
    - backend/app/api/v2/router.py
    - backend/tests/test_portfolio_identity_api.py
  modified:
    - backend/app/api/v1/auth.py
    - backend/app/api/v1/me.py
    - backend/tests/conftest.py
    - backend/tests/helpers.py
    - backend/tests/test_accounts.py
    - backend/tests/test_auth_request_code.py
    - backend/tests/test_auth_session.py
    - backend/tests/test_auth_verify.py
    - backend/tests/test_ratelimit.py
key-decisions:
  - Keep request-code, csrf, refresh, logout and refresh-cookie path at their existing v1 locations
  - Return email-only identity without an implicit portfolio or invented cash balance
  - Test actual v2 routers before Plan15 production registration; isolated composition is not deployment reachability proof
requirements-completed: []
requirements-addressed: [PSAFE-02, PCTX-01]
duration: 7 min
completed: 2026-11-16
---

# Phase 12 Plan 09: Versioned Identity HTTP and Legacy OTP Refusal

**Email-only v2 identity reuses the existing session machinery, while obsolete cash-bearing calls refuse before consuming a valid sign-in code.**

## Accomplishments

- Actual `/api/v2/auth/verify-code` calls the existing OTP/session service,
  retains rate-limit and generic invalid-code behavior, and sets the existing
  Secure/HttpOnly/SameSite cookies. `/api/v2/me` uses the existing authenticated
  user dependency and identity service. Both successful responses contain only
  email and use Cache-Control:no-store.
- Existing request-code, csrf, refresh and logout endpoints remain unchanged;
  refresh cookie scope stays `/api/v1/auth/refresh`, with access scoped to `/api`.
  No parallel OTP/session implementation or financial account selection exists.
- Legacy verify-code returns exactly409 `{detail:{code:api_version_required}}`
  after normal input/CSRF checks, without calling the verification service,
  consuming a code, creating a user/session or setting cookies. Legacy me keeps
  authentication and returns the same409 without looking up a financial root.
- Real PostgreSQL/Redis HTTP tests preserve unequal baseline/cash snapshots for
  zero/one/many/closed roots, exercise account switching and cookie rotation,
  refresh/logout, missing authentication/CSRF and exact one-use OTP semantics.
  Repeated legacy refusals preserve the actual OTP hash/attempt fields; the same
  code then succeeds once at v2 and a second v2 use fails400.
- Retained auth regression requests now exercise v2 identity using real router
  composition, while preserving token forgery, mixed-user/session, revocation,
  refresh race/reuse/expiry, CSRF and rate-limit negatives. Financial expectations
  were moved from obsolete response cash to actual stored balances where needed.

## Task Commits

| Task | Commit | Outcome |
|---|---|---|
|12-09-01|a8f2713|Thin v2 identity routers and eight real HTTP composition cases|
|12-09-02|04bc9fc|Pre-consumption v1 refusal and preserved auth/security regressions|

## Verification

Existing locked virtualenv only, UV_CACHE_DIR=/tmp/birja-uv-cache and
`uv run --no-sync`; no dependency installation or provider requests.

| Check | Result |
|---|---|
| Assigned versioned/cookie/refresh focused HTTP gate | 8 passed in3.23s |
| Entire new identity/refusal module plus retained auth_session/auth_verify/auth_request_code/ratelimit/otp_store families | 96 passed in8.06s; new module contributes11 cases |
| Directly affected existing onboarding HTTP and initial stored-funding checks | 2 passed,6 deselected in2.74s |
| Mypy v1 auth/me and three v2 source modules | PASS,5 modules |
| Ruff lint and format, all13 touched Python files | PASS |
| git diff --check | PASS |

The retained token-negative test emits its existing synthetic SHA512 key-length
warning; no secret or real user data is involved. Initial sandbox execution
could not open localhost sockets; the same guarded test commands passed with
scoped socket escalation. The inherited v1 MeOut type mismatch disappeared once
the planned legacy route was retired; no type-ignore bypass was added.

## Deviations from Plan

1. **[Rule3 — Required test composition/consumer updates]** The plan explicitly
   calls for isolated actual-router composition and auth regression updates but
   its files list omits the existing shared fixtures/helpers and regression
   modules. Added actual v2 router registration only in test conftest, the new
   module composition and custom rate-limit composition; changed shared sign-in
   helper and retained identity requests to v2. No production registration moved
   forward from Plan15, no stub handler or service override substitutes for HTTP.

## Remaining Integration Boundaries

- `create_app()` production source still does not include v2. Plan15 must
  register these actual routers and remove redundant test-only registrations
  from conftest, this module's app fixture and custom rate-limit composition,
  then rerun requests against the actual production composition and exact route
  inventory. These tests are not production reachability or deployment proof.
- Other financial services/routes/browser consumers still await their explicit
  portfolio plans. Shared sign-in now uses v2 in tests; hardcoded legacy identity
  consumers in unrelated older financial test families need migration during
  their own integration. Full backend/browser/coverage success is not claimed.
- No management/create/rename/description/delete features, package changes,
  production access, provider operations, publication or branch switch occurred.
  No milestone requirement is marked complete from this bounded auth plan.
  Phase7 deferred work and unrelated .claude/ remain untouched.

## Known Stubs

None. Production registration is an explicitly planned later composition task,
not a placeholder response or unimplemented auth service.

## Self-Check: PASSED

All13 touched Python outputs exist. Commits a8f2713 and04bc9fc exist on
feature/milestone-v1.2; no tracked files were deleted and no dependency files
changed. Assigned HTTP behavior and affected security regressions pass.
