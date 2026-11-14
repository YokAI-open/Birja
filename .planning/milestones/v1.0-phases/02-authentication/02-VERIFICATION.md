---
phase: 02-authentication
verified: 2026-10-27T16:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 2: Authentication Verification Report

**Phase Goal:** Users can sign in with an emailed one-time code, stay signed in, and get their $10,000 account once
**Status:** passed
**Re-verification:** No, initial verification

## Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Same "code sent" response with or without an account; console code in dev; real email via Resend | VERIFIED | `request_code` in `services/auth.py` does no user lookup and the route always returns 202 `code_sent`. `ConsoleSender` logs `DEV EMAIL ...`. `ResendSender` posts to Resend with retries and an idempotency key. Prod config refuses the console backend (`config.py:104`). Real-email half **human-verified by the user on 2026-10-27**: a code arrived from noreply@nist.one and the user signed in. Backend logs for that window had 0 "DEV EMAIL" lines, 1 request-code 202 and 1 verify-code 200. |
| 2 | Correct code signs in; single-use; ~10 min expiry; dies after 5 wrong attempts | VERIFIED | `otp.py` stores an HMAC under `sim:otp:*` with a 600 s TTL. An atomic Lua script counts each attempt and deletes the code on the 6th. A compare-and-delete consume makes it single-use under concurrency. Covered by `test_otp_store.py` and `test_auth_verify.py`. |
| 3 | Repeated requests or wrong attempts from one email or IP are refused with a rate-limit message | VERIFIED | `request_code` and `verify_code` enforce per-IP, per-email and global limits (plus a daily verify cap). The route returns 429 with `Retry-After` and message "Too many requests. Try again later." Covered by `test_ratelimit.py` and the auth tests. |
| 4 | Stays signed in across refresh and restart (~30 days); sign-out ends the session | VERIFIED | `yk_refresh` has Max-Age 2592000 and HttpOnly/Secure/SameSite=Strict. Only the SHA-256 of the token is stored in Postgres. Rotation, a 10 s reuse grace window and whole-session revocation on replay are implemented in `rotate_session`. `end_session` sets `revoked_at`, and `/me` checks the session. The e2e spec covers reload, a cleared access cookie with silent refresh, sign-out and reload. `test_auth_session.py` and `test_csrf.py` pass. |
| 5 | First-time user sees exactly $10,000.00; sign-in again never grants more; no reset or add-cash path | VERIFIED | `get_or_create_user` uses `INSERT ... ON CONFLICT DO NOTHING` and creates the Account only for the winner. `STARTING_CASH` is 10000.00 as `NUMERIC(20,8)`, with CHECK cash>=0, UNIQUE(user_id) and a lowercase-email CHECK. The only route that touches cash is the read-only `GET /me`. Returned as a string and formatted with Intl in the UI. `test_accounts.py` covers concurrent first sign-ins. |

**Score:** 5/5

## Requirements Coverage

| Req | Status | Evidence |
|-----|--------|----------|
| AUTH-01 | SATISFIED | Truth 1 |
| AUTH-02 | SATISFIED | Truth 2 |
| AUTH-03 | SATISFIED | Truth 3 |
| AUTH-04 | SATISFIED | Truth 4 |
| AUTH-05 | SATISFIED | Truth 4 (server-side revoke) |
| AUTH-06 | SATISFIED | Console backend in dev; Resend human-verified |
| ACCT-01 | SATISFIED | Truth 5 |
| ACCT-02 | SATISFIED | Truth 5 |

All 8 IDs are mapped to Phase 2 in REQUIREMENTS.md and claimed by the plans. No orphaned requirements. (The REQUIREMENTS.md checkboxes and traceability table still read Pending. Update them at phase close.)

## Behavioral Spot-Checks

| Check | Result | Status |
|-------|--------|--------|
| Backend `pytest --cov` against docker-compose.test.yml (stack torn down afterwards) | 149 passed, 99.73% coverage (gate 80%) | PASS |
| `ruff check` | all checks passed | PASS |
| `mypy app` | no issues in 28 files | PASS |
| Frontend Vitest | 60 passed in 7 files | PASS |
| Playwright e2e (`frontend/e2e/auth.spec.ts`) | not run locally, by constraint (the dev stack holds a real Resend key). Spec read: it covers sign-in, $10,000.00, reload, silent refresh, sign-out and re-sign-in. It runs in CI on the PR. | SKIPPED |

## Anti-Patterns

No TBD, FIXME or XXX markers in `backend/app`, `frontend/src` or `frontend/e2e`. WR-01..WR-05 from the code review are fixed. Accepted risk T-02-54 (02-07) is noted.

Advisory items remain (none block the goal):
- IN-01: a refresh race grace case may briefly show the sign-in card until reload.
- IN-02: no error boundary around `formatUsd`.
- IN-03: CI failure logs include dev codes for throwaway accounts.
- IN-04: `ENV` defaults to `dev`. Address in the deploy phase.
- IN-05: `apiFetch` retries even after a failed refresh.

## Human Verification

The only item that needed a human was the real-email half of SC1. It was completed and recorded above. The Plan 02-09 Task 3 push gate is pending by design and is not a gap.

## Gaps Summary

None. The phase goal is achieved in the codebase.

---

_Verified: 2026-10-27_
_Verifier: Claude (gsd-verifier)_
