---
phase: 02-authentication
plan: 06
subsystem: auth
tags: [rate-limit, redis, fastapi]
requires:
  - phase: 02-authentication
    provides: request-code / verify-code endpoints, OtpStore, sessions (02-02..02-04)
provides:
  - Fixed-window limiter (services/ratelimit.py: hit, enforce, RateLimited)
  - 429 + Retry-After on request-code and verify-code
  - ClientIpDep and ten rl_* settings
affects: [02-05, 02-07]
key-files:
  created:
    - backend/app/services/ratelimit.py
    - backend/tests/test_ratelimit.py
    - backend/tests/test_config_ratelimit.py
  modified:
    - backend/app/core/config.py
    - backend/app/core/deps.py
    - backend/app/services/auth.py
    - backend/app/api/v1/auth.py
    - .env.example
key-decisions:
  - "Per-IP defaults are env-dependent: 20/h request and 30/10min verify in test/prod, 200 and 300 in dev (explicit env values win)"
  - "Client IP read only from request.client.host; uvicorn proxy-headers trusts loopback only by default"
requirements-completed: [AUTH-03]
duration: 20min
completed: 2026-10-27
---

# Phase 2 Plan 06: Rate Limits Summary

**Fixed-window Redis limiter (INCR + EXPIRE NX + TTL in one MULTI) caps code requests per email/IP/global and verify attempts per email/IP, answering 429 with Retry-After and no code issued.**

## Tasks

Both tasks landed in one commit (the shared test file and service signatures are interdependent): see `git log` for `feat(02-06): rate-limit code requests and verify attempts`.

## Limits (defaults)

| Key | Limit | Window |
|-----|-------|--------|
| sim:rl:req:email:<hmac> | 5 | 10 min |
| sim:rl:req:ip:<ip> | 20 (dev: 200) | 1 h |
| sim:rl:req:global | 500 | 24 h |
| sim:rl:ver:email:<hmac> | 10 | 10 min |
| sim:rl:ver:ip:<ip> | 30 (dev: 300) | 10 min |

Note for the Playwright suite (02-05): in dev (ENV=dev, the compose default) all traffic shares one IP. With the dev defaults (200 requests/h, 300 verifies/10 min) a sign-in costs 1 + 1 hits, so about 100 sign-ins per hour fit. Per-email limits (5 requests / 10 verifies per 10 min) apply per test email: use a unique email per run. The global cap (500/day) is shared by all runs; override via `RL_*` env vars in `.env` if needed. CI that runs with ENV=test would get the strict 20/30 IP limits, so set `ENV` dev (compose default) or `RL_REQUEST_IP_LIMIT` there. To clear counters locally, delete `sim:rl:*` keys (SCAN) or wait out the window.

## Verification

- Backend suite: 107 passed, coverage 99.46%; 100% on otp, auth, accounts, ratelimit, security, deps.
- ruff, ruff format, mypy clean. No X-Forwarded-For in app code; 5 `enforce(` calls in services/auth.py.

## Deviations from Plan

- **Dev-only loosened IP defaults** (config validator keyed on `env == "dev"`), per the orchestrator's instruction about e2e; the plan's numbers remain the defaults for test/prod. No compose change was needed.
- uvicorn's default `forwarded_allow_ips` in the installed version is `127.0.0.1,::1`, not only `127.0.0.1`; test asserts loopback-only (no wildcard) instead.
- Config tests live in `tests/test_config_ratelimit.py` (new file) rather than editing `test_config.py`.
- Two tests carry `# noqa: SIM117` (two clients on one app need nested async with).
- The plan's standalone-uvicorn proxy-header check was covered by the `uvicorn.Config` unit assertion only.

## Known Stubs

None.

## Self-Check: PASSED
