# Phase 2: Authentication - Context

**Gathered:** 2026-10-27
**Status:** Ready for planning
**Source:** plan-phase questions after research (no discuss-phase run, no UI-SPEC)

<domain>
## Phase Boundary

Users sign in with an emailed one-time code, stay signed in for up to about 30 days, can sign out, and get a $10,000.00 account exactly once. Signup is open: the first successful sign-in creates the user and the account. Requirements: AUTH-01 to AUTH-06, ACCT-01, ACCT-02.

</domain>

<decisions>
## Implementation Decisions

### Email delivery
- **D-01:** The user's domain is verified in Resend (SPF/DKIM). Build the Resend sender with plain `httpx.AsyncClient` (per RESEARCH.md) and test it against a mocked API. The phase ends with a `checkpoint:human-verify` where the user puts their own `RESEND_API_KEY` and sender address into the local, git-ignored `.env`, signs in, and receives a real code from the verified domain.
- **D-02:** Never put a Resend API key in any committed file, plan, test, fixture, log or CI config. `.env.example` holds only an empty placeholder. The repo and its CI logs are public. Plans must not ask the user to paste the key into chat.

### Frontend navigation
- **D-03:** No react-router in Phase 2. One auth-state switch driven by the `/me` query shows a loading skeleton, the sign-in flow, or the signed-in account view. The router moves to Phase 3, which deviates from SKELETON.md. The Phase 1 health check stays reachable, so the existing e2e test keeps passing.

### Claude's Discretion
- Rate-limit numbers are settings, defaulting to the RESEARCH.md proposals.
- Session, CSRF, OTP and schema design follow RESEARCH.md and CLAUDE.md.
- Copy and layout of the three screens use MASTER.md tokens and the existing shadcn card, badge and button.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `CLAUDE.md`: Security (Login, Session), Data (Redis keys, rate limits, transactions), Money, API and Test culture rules
- `.planning/phases/02-authentication/02-RESEARCH.md`: stack, patterns, pitfalls, schema, validation architecture
- `.planning/REQUIREMENTS.md`: AUTH-01..06, ACCT-01..02
- `.planning/phases/01-skeleton-and-ci/01-REVIEW.md`: open warnings WR-02, WR-04 and WR-05, to fix early in this phase
- `design-system/yokaiexchange/MASTER.md`: UI tokens

</canonical_refs>

<deferred>
## Deferred Ideas

- react-router, to Phase 3 (D-03)
- Six-box OTP input from MASTER.md: visual polish, so a single input for now
- UI-SPEC: skipped by the user

</deferred>

---

*Phase: 02-authentication*
