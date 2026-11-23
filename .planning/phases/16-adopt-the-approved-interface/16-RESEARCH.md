# Phase 16 Research

## Integration findings

- The redesign already uses local logo variants and the existing Inter, Lucide,
  Tailwind and React components. Package and backend boundaries match the v0.6.2
  baseline. This phase needs repository-specific integration checks.
- `App.tsx` uses owner-scoped route boundaries, `useMe` and `useLogout`.
  OTP verification uses `/api/v2/auth/verify-code` and the existing logout API
  at `/api/v1/auth/logout`. Preserve session/query cleanup and direct routes.
- Market pricing and stock discovery use `/api/v1/prices` and `/api/v1/stocks`.
  Trades, portfolio metadata and event History remain scoped under
  `/api/v2/portfolios/{id}`. Keep eligibility, values, reference links and
  retry identities bound to the server-confirmed portfolio.
- The existing browser runner supplies fake prices, console email, restricted
  isolated services and disposable data. It can verify current React against
  the actual backend without contacting market or email providers.
- The uncommitted Impeccable install and other tooling setup changes have their
  own provenance. They are outside the app changes needed to ship the redesign.

## Validation Architecture

Use Vitest for session, view state, layout semantics and endpoint interactions.
Use locally rendered responsive checks for focus and overflow. Use the existing
isolated Compose runner for real OTP, owner isolation, actual trade, lifecycle
and money assertions. Keep browser output and screenshots tied to the source
they exercised. Record owner acceptance separately from automated reflow.
