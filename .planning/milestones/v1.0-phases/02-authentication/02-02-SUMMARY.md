---
phase: 02-authentication
plan: 02
subsystem: auth
tags: [otp, redis, lua, csrf, hmac, fastapi]
requires:
  - phase: 02-authentication
    provides: packages, logging, branch (02-01)
provides:
  - OtpStore (issue/verify) with Lua attempt counter and compare-and-delete
  - POST /api/v1/auth/request-code and GET /api/v1/auth/csrf
  - CSRF double-submit dependency, ConsoleSender, otp_hmac_secret setting
  - test fixtures running_app, auth_client, outbox, clean_auth_redis, helpers
affects: [02-03, 02-06, 02-08]
key-files:
  created: [backend/app/core/security.py, backend/app/services/otp.py, backend/app/services/email.py, backend/app/services/auth.py, backend/app/schemas/auth.py, backend/app/api/v1/auth.py, backend/tests/helpers.py, backend/tests/test_otp_store.py, backend/tests/test_auth_request_code.py, backend/tests/test_csrf.py]
  modified: [backend/app/core/config.py, backend/app/core/deps.py, backend/app/main.py, backend/app/api/v1/router.py, backend/tests/conftest.py, backend/tests/test_config.py, .env.example, docker-compose.yml]
key-decisions:
  - "Redis errors map to 503 + Retry-After via an app-level RedisError handler"
  - "No COOKIE_SECURE switch: the CSRF cookie is always Secure"
requirements-completed: []
duration: 25min
completed: 2026-10-27
---

# Phase 2 Plan 02: request-code, OTP store and CSRF Summary

A user can request a sign-in code; the code is HMAC-stored in Redis with race-free single-use and 5-attempt semantics, and shows in the backend log in dev.

## Tasks

| Task | Result | Commit |
|------|--------|--------|
| 1 OTP secret + OtpStore | otp_hmac_secret (SecretStr, >= 32 chars, placeholder refused in prod); Lua scripts; 100% line+branch on otp.py | 6d92576 |
| 2 CSRF + request-code + console sender | routes, verify_csrf, ConsoleSender, 503 handler, test fixtures | 694ab03 |

## Verification

- Backend suite: 47 passed, coverage 98.6% (branch); ruff, ruff format, mypy clean.
- Dev-stack smoke (throwaway compose project with env vars exported inline): request-code returned 202 and `DEV EMAIL to=` appeared in backend logs. Stack and test stack torn down with `down -v`.

## Deviations from Plan

- No local `.env` exists, so the guarded append of OTP_HMAC_SECRET was skipped (not created). The user must run `cp .env.example .env` (or add the key) before `docker compose up`.
- Because of that, the dev-stack smoke test used inline-exported env vars with project name `smoke02` instead of `.env`.
- `app/core/config.py` gained `from __future__ import annotations` for the `-> Settings` return annotation in the model validator.

## Known Stubs

None. Rate limits (T-02-12) are deferred to 02-06 as planned; prod guard for ConsoleSender to 02-08.

## Self-Check: PASSED

- Commits 6d92576 and 694ab03 exist; created files present.
