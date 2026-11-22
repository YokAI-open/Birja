---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "19"
subsystem: auth
tags: [portfolio, browser, identity, query-cache, authorization, lifecycle]
requires:
  - phase: 12-15
    provides: actual production v2 identity and active metadata routes
provides:
  - Strict email-only v2 browser identity with existing v1 session lifecycle
  - Owner/session cache invalidation and stale identity-response refusal
  - Exact bounded metadata parser and explicit portfolio target epochs
  - Opt-in legacy sole-root navigation without financial authority or fallback
affects: [12-20, 12-21, 12-22, 12-23, 12-24, 12-25, 12-26, 12-27]
tech-stack:
  added: []
  patterns: [owner-scoped metadata query, captured target scope, navigation-only discovery]
key-files:
  created:
    - frontend/src/api/portfolios.ts
    - frontend/src/hooks/usePortfolioTarget.ts
    - frontend/src/hooks/usePortfolioTarget.test.tsx
  modified:
    - frontend/src/api/auth.ts
    - frontend/src/api/client.ts
    - frontend/src/hooks/useMe.ts
    - frontend/src/api/auth.test.ts
    - frontend/src/hooks/useAuthMutations.test.tsx
key-decisions:
  - Reject cash-bearing or otherwise extended identity responses rather than inventing a financial fallback
  - Keep v2 OTP verification outside automatic expired-session retry, preserving one verification attempt per request
  - Legacy discovery must be explicitly enabled and returns only a navigation ID; an explicit target never substitutes another root
  - Capture owner, route and session scope and check cache/query identity before publishing metadata or using target handles
requirements-completed: []
requirements-addressed: [PSAFE-02, PCTX-01]
duration: 12 min
completed: 2026-11-16
---

# Phase 12 Plan 19: Identity and Explicit Browser Target Discovery

**Email-only browser identity and owner-scoped metadata resolve an explicit portfolio before financial work without cash fallbacks or arbitrary selection.**

## Performance

- Started: 2026-11-16T12:22Z
- Focused gates complete: 2026-11-16T12:33Z
- Tasks: 2/2
- Files created/modified: 8
- Packages, visual controls, backend routes and production operations changed: none

## Accomplishments

- Me now contains only email. Identity reads use /api/v2/me and verification
  uses /api/v2/auth/verify-code, both no-store; request-code, csrf, refresh,
  logout and cookie transport retain their existing v1 paths and semantics.
  Old cash-bearing identity bodies and malformed/extended bodies fail parsing.
- useMe retains its observed identity query while removing private cached
  projections on owner/sign-out changes. A captured identity epoch prevents an
  older in-flight result from publishing after a session change. Existing auth
  mutation cancellation ordering and observer retention remain tested.
- The metadata client accepts only an ordered array of at most ten immutable
  id/name summaries with canonical positive bigint strings, unique IDs and
  bounded plain-text names. It rejects financial fields, malformed IDs,
  controls, duplicates, unexpected ordering and malformed wrappers.
- usePortfolioTarget(routePortfolioId?, {legacyEntry?:boolean}) consumes only
  private metadata under ["portfolios", email]. Its status is signed_out,
  loading, required, empty, ambiguous, unavailable, error, redirect or ready.
  Only ready returns target authority: owner, portfolioId, name, frozen epoch
  and isCurrent(). Financial consumers must capture this value and check its
  currentness; metadata never replaces server authorization.
- Missing/malformed explicit targets return required without metadata work;
  absent/foreign/closed IDs return unavailable with no alternative. Legacy
  discovery is opt-in: zero is empty, many ambiguous, one redirect with only
  redirectPortfolioId and no financial target. Plan23 must replace-navigate
  before starting a financial query or attempt.
- Captured route scopes invalidate old target/recovery callbacks on route
  changes/unmount. Owner/session epochs, cancellation, request serials and
  query-object identity discard late metadata across account switch,
  logout-and-return and removed/replaced cache queries. Root loss or metadata
  failure suppresses target authority without exposing another portfolio.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| 12-19-01 | 91bb27d | Identity-only client, transport retry correction and owner cache lifecycle |
| 12-19-02 | 5ab98d5 | Bounded metadata client and explicit target discovery/epoch hook |

## Verification

- Assigned auth tests pass; auth/client/auth-mutation/private-cache regression
  run passes46 cases across four files.
- Assigned target test module passes52 cases: parser bounds and string IDs,
  no-store/AbortSignal, zero/one/many legacy states, explicit invalid and
  unavailable targets, route changes before/after response, stale callbacks,
  owner switch, logout/return, cancelled older root-loss response, retry
  failure, version refusal and identity expiry.
- Final combined five-file run passes98 cases. No provider/backend network or
  production resource was used; fetch is intercepted at the HTTP boundary.
- Changed-file ESLint and Prettier checks pass; git diff --check passes.
- Full frontend typecheck was run and reports exactly two pending planned
  consumers: AccountPage.tsx:20 and TradePage.tsx:406 still read Me.cash_usd.
  Plans23/24 own replacing these with identity-only or explicitly scoped
  financial reads. No cash compatibility shim or complete build success is
  claimed; all new/changed task modules have no reported type errors.

## Deviations from Plan

1. **[Rule2 — single verification attempt]** Updated api/client.ts to exclude
   /api/v2/auth/ from automatic401 refresh/retry. The old exclusion only knew
   v1; moving OTP verification without this correction would repeat a failed
   verification. Tests prove one rejected attempt, while expired v2/me still
   refreshes through v1/auth/refresh and retries once. Commit91bb27d.
2. **[Rule3 — affected regression contracts]** Updated the existing
   useAuthMutations.test.tsx identity/path fixtures and added immediate owner
   cache invalidation assertions. Cancellation/observer/security assertions
   remain intact. Commit91bb27d.

Initial target-test fixture corrections removed a JavaScript default that
mistook an explicit undefined route for ID1 and awaited TanStack observer
notifications rather than asserting stale rendered snapshots. These did not
change application authorization behavior or loosen assertions.

## Known Stubs

None. The new hook/client are deliberately not mounted in pages yet: Plans20–25
own financial clients, hooks, target boundary and visible named surfaces.

## Carry Forward

- Plan23 must use legacyEntry:true only at deliberate old unscoped entry paths,
  navigate redirectPortfolioId with replace, and never pass a redirect state to
  financial children. Explicit routes use the default no-fallback mode.
- Plans20–25 must include captured owner/portfolio identity in all financial
  requests, caches, pending attempts and callbacks; the epoch object is opaque
  and target.isCurrent() validates its captured lifecycle. Metadata is not a
  substitute for server or current execution authority.
- Plans23/24 must remove the two remaining Me.cash_usd page consumers. Plan27
  must adapt older page/hook fixtures still returning cash-bearing v1 bodies;
  they must not be accepted by the strict identity parser.
- No visible UI acceptance, full frontend suite/build, coverage, browser,
  strict audit/image or encrypted/TLS recovery result is claimed. Requirements
  remain unchecked and Phase7 live outcomes remain separately deferred.
- All commits remain local; unrelated .claude/ remains untouched.

## Self-Check: PASSED

The three new files and both task commits exist. The final98-case run and
changed-file lint/format checks pass. The two explicitly pending page type
errors are documented without claiming whole-app readiness or hiding failures.
