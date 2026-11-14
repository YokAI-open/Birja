---
phase: 02-authentication
plan: 08
subsystem: auth
tags: [email, resend, httpx, respx, settings]
requires:
  - phase: 02-authentication
    provides: EmailSender protocol, ConsoleSender, rate-limit settings (02-02, 02-06)
provides:
  - ResendSender (plain httpx, Idempotency-Key, bounded retries) and build_email_sender
  - email_backend / resend_api_key / email_from settings with prod and resend guards
  - app.state.http shared httpx.AsyncClient owned by the lifespan
affects: [02-09]
key-files:
  created: [backend/tests/test_email.py]
  modified: [backend/app/core/config.py, backend/app/services/email.py, backend/app/main.py, docker-compose.yml, .env.example, backend/tests/test_config.py]
key-decisions:
  - "No Resend SDK (D-01): plain httpx POST to https://api.resend.com/emails"
  - "ENV=prod refuses the console backend at settings validation"
requirements-completed: []
duration: 15min
completed: 2026-10-27
---

# Phase 2 Plan 08: Resend email sender Summary

Sign-in codes can be sent through Resend (Bearer key, one Idempotency-Key per send reused across up to 3 retries on 429/5xx/network errors with backoff and jitter), console stays the dev default, and prod refuses console.

## Tasks

| Task | Result | Commit |
|------|--------|--------|
| 1 Email settings + guards + compose/.env.example | email_backend, SecretStr key (repr hidden), empty-string to None, resend needs key and "@" sender, prod requires resend; empty placeholders in compose and .env.example | cea2850 |
| 2 ResendSender + lifespan wiring | respx-mocked tests for success, 5xx/429/network retries, no retry on 4xx, retry-after cap, log hygiene (no code, key or address in any record), lifespan opens and closes the http client | bb2094f |

## Verification

- Backend suite: 124 passed, coverage 99.7% (branch); critical modules (incl. services/email.py) at 100%.
- ruff, ruff format, mypy, pip-audit clean.
- `git grep -nE 're_[A-Za-z0-9]{20,}'` finds nothing; tests use `dummy-key-not-real`. Real Resend API never called; `.env` never read or created.
- Test stack torn down with `down -v`.

## Deviations from Plan

- Existing prod placeholder-secret tests in test_config.py now pass resend settings, because the new prod email guard would otherwise fire first.
- `build_email_sender` uses a conditional instead of `assert` (ruff S101); behavior identical.
- The dev-stack smoke check of console logging was not re-run; the default console path is covered by the existing request-code tests (outbox/console) and `test_console_sender_still_logs_code`.

## Known Stubs

None.

## Self-Check: PASSED

- Commits cea2850 and bb2094f exist; test_email.py present.
