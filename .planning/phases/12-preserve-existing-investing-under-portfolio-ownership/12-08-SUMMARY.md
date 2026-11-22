---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "08"
subsystem: auth
tags: [portfolio, identity, authorization, onboarding, exact-money]
requires:
  - phase: 12-07
    provides: actual0017 owned-root constraints and admitted test runtime
provides:
  - Frozen explicitly resolved active portfolio authority with indistinguishable unavailable targets
  - Identity-only response and ordered private string-ID metadata contracts
  - Once-only initial named funding independent of returning identity and session operations
affects: [12-09, 12-10, 12-11, 12-14, 12-15, 12-19, 12-27]
tech-stack:
  added: []
  patterns: [explicit paired active-root resolver, identity-only account lookup]
key-files:
  created:
    - backend/app/schemas/portfolios.py
    - backend/app/services/portfolios.py
    - backend/tests/test_portfolio_identity.py
  modified:
    - backend/app/core/deps.py
    - backend/app/schemas/auth.py
    - backend/app/services/accounts.py
    - backend/app/services/auth.py
    - backend/tests/test_portfolio_ownership.py
key-decisions:
  - Resolve only explicit Account.id plus authenticated User.id and active state; never choose an alternate root
  - Keep the resolver in a narrow service consumed by dependency adapters and preauthored ownership tests
  - Identity reads User alone and returning authentication never creates or replenishes portfolios
requirements-completed: []
requirements-addressed: [PSAFE-02, PFIN-02, PFUND-03]
duration: 8 min
completed: 2026-11-16
---

# Phase 12 Plan 08: Owned-Active Resolver and Identity-Only Account Services

**Explicit paired portfolio authority and user-only identity preserve original finances while sign-in, refresh and logout work independently of financial-root count.**

## Accomplishments

- Added frozen OwnedActivePortfolio(portfolio_id,user_id) and
  resolve_owned_active_portfolio(db,user,portfolio_id). The resolver queries only
  the requested owned active Account; unknown, foreign and closed targets all
  raise404 with exactly {code:portfolio_unavailable}. No first/only/newest fallback.
- Added get_owned_active_portfolio/OwnedActivePortfolioDep using existing
  CurrentUserDep and DbDep. FastAPI validates positive bigint-range path IDs;
  malformed, fractional, nonpositive and overflowing values return422.
- IdentityOut contains only email. PortfolioSummary transports positive bigint
  IDs as JSON strings and plain-text names; list_active_portfolios returns only
  the owner's active metadata ordered by ID, including an honest empty array.
- get_me reads users alone. verify_code returns IdentityOut through the existing
  OTP/rate-limit/session transaction, without financial joins. Only successful
  insertion of a genuinely new User creates one My portfolio with the unchanged
  $10,000 cash and stored baseline. Returning lookups/read/sign-in never regrant.
- Real PostgreSQL/Redis tests cover zero/one/many/closed roots, unchanged actual
  balances and nonstandard baselines, eight concurrent onboarding calls, atomic
  rollback, consumed OTP refusal, refresh and revoked-session/logout behavior.

## Task Commits

| Task | Commit | Outcome |
|---|---|---|
|12-08-01|e5e9dba|Frozen explicit resolver, metadata/identity schemas and exact refusal/path proofs|
|12-08-02|01b8810|Identity-only services and once-only onboarding/session proofs|

## Verification

- Assigned resolver/identity-contract/malformed command:11 passed,29 deselected.
- Assigned test_portfolio_identity.py command:12 passed.
- Ruff lint/format on all eight changed Python files:PASS.
- Focused mypy on six changed source modules:PASS.
- git diff --check:PASS.
- Additional existing OTP/session regression attempt:40 passed,16 failed.
  All16 failures originate at legacy POST/api/v1/auth/verify-code still declaring
  MeOut and requiring cash_usd, while the service now intentionally returns
  IdentityOut. Plan09 owns retiring that route before OTP consumption and adding
  identity-only v2 routes; its tests must replace these obsolete v1 expectations
  and rerun real cookie/session journeys. This is an explicit integration debt,
  not a claimed green full auth suite. No auth check was weakened to hide it.
- Two optional regression invocations initially named nonexistent OTP test paths;
  neither executed tests. The actual discovered test_otp_store.py was used for
  the recorded40/16 run. The assigned plan commands passed independently.

## Deviations from Plan

1. **[Rule3 — Blocking file-path omission]** The plan names the resolver but omits
   its service output path; preauthored Plan01 tests already import
   app.services.portfolios. Added that narrow module following existing account
   service/query patterns, with deps importing it. This avoids putting business
   authorization into routers or duplicating it in consumers. No new layer,
   endpoint, dependency or architecture decision is introduced.
2. **[Rule3 — Test fixture correction]** The transactional portfolio_world fixture
   authenticates as restricted migrator and cannot SET ROLE birja_app. Removed
   that invalid fixture assumption without changing memberships or grants.
   Resolver tests use the existing guarded real database transaction. Exact
   deployed-role bootstrap/TLS qualification remains16/27, not claimed here.

## Integration Obligations and Scope

- Plan09 must update legacy identity HTTP response/refusal and new v2 composition;
  production registration remains15. Existing v1 financial and cash-bearing
  consumers are intentionally not made compatible through an implicit root.
- Financial services10/11/14 must accept the resolved root and recheck active
  state under their locks. A frozen resolver value alone does not establish
  lifecycle safety across a later transaction.
- No management/create/rename/description/delete UI or routes, provider calls,
  package changes, production access, publication or branch switch occurred.
- No requirement is marked complete from this bounded service plan. Full
  coverage/security/TLS/recovery and owner UI/native200% checkpoints remain.
- No blocking stubs were introduced; later route integration is explicitly
  owned by09/15. Phase7 deferred outcomes and unrelated .claude/ remain intact.

## Self-Check: PASSED

All eight output Python files and the summary exist. Task commits e5e9dba and
01b8810 are present on feature/milestone-v1.2. Assigned focused commands pass;
the optional legacy HTTP regression failures are explicitly retained above.
