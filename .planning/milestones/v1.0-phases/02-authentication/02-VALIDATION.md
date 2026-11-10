---
phase: 2
slug: authentication
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-10-27
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9 + pytest-asyncio 1.x + httpx ASGITransport + respx (backend); Vitest + RTL (frontend); Playwright (e2e) |
| **Config file** | `backend/pyproject.toml`, `frontend/vite.config.ts`, `frontend/playwright.config.ts` (all exist from Phase 1) |
| **Quick run command** | `cd backend && uv run pytest tests/test_auth_*.py -x -q` / `cd frontend && npm run test` |
| **Full suite command** | `docker compose -f docker-compose.test.yml up -d --wait && cd backend && uv run pytest --cov=app --cov-fail-under=80; cd ../frontend && npm run test -- --coverage && npx playwright test` |
| **Estimated runtime** | ~90 seconds (excluding image builds) |

---

## Sampling Rate

- **After every task commit:** Run the quick command for the area you touched, plus `ruff check` or `npm run lint`
- **After every plan wave:** Run the full suite command
- **Before `/gsd:verify-work`:** Full suite plus e2e must be green. Coverage must be 80% overall and 100% on `services/otp.py`, `services/auth.py`, `core/security.py`, `services/ratelimit.py`, the current-user dependency and the CSRF dependency
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

Task-level map (one row per `auto` task; full commands are in each task's `<automated>`; `<critical modules>` = otp, auth, accounts, ratelimit, email (from 02-08), security, deps):

| Task ID | Plan | Wave | Requirement | Behavior | Test Type | Automated Command | Status |
|---------|------|------|-------------|----------|-----------|-------------------|--------|
| 02-01-T3 | 02-01 | 1 | AUTH-06 (WR-02/04/05) | Packages locked; app logs visible; template ruff-clean; .env.* ignored | integration + check | `cd backend && uv sync --locked && uv run ruff check . && uv run mypy app && uv run pytest tests/test_health.py tests/test_migrations.py tests/test_smoke.py -q; git check-ignore -q .env.local` | ⬜ pending |
| 02-02-T1 | 02-02 | 2 | AUTH-02 | OtpStore issue/verify, single use, 5-attempt kill, race-free; secret validation | unit | `cd backend && uv run pytest tests/test_otp_store.py tests/test_config.py -q --cov=app.services.otp --cov-branch --cov-fail-under=100` | ⬜ pending |
| 02-02-T2 | 02-02 | 2 | AUTH-01, AUTH-06 | CSRF 403s, identical 202, console line, 503 on Redis error, https cookie-jar smoke | api | `cd backend && uv run pytest tests/test_csrf.py tests/test_auth_request_code.py -q && uv run pytest -q --cov=app --cov-fail-under=80` | ⬜ pending |
| 02-03-T1 | 02-03 | 3 | ACCT-01, ACCT-02 | Migration 0002 roundtrip + no drift; $10,000 exactly once; CHECK/UNIQUE | integration + DB | `cd backend && uv run pytest tests/test_migrations.py tests/test_accounts.py -q` | ⬜ pending |
| 02-03-T2 | 02-03 | 3 | AUTH-01, AUTH-02, ACCT-01, ACCT-02 | verify-code success/failure modes, concurrency, route allow-list | api | `cd backend && uv run pytest -q --cov=app --cov-fail-under=80 && uv run coverage report --include=<critical modules> --fail-under=100` | ⬜ pending |
| 02-04-T1 | 02-04 | 4 | AUTH-04 | JWT encode/decode rejections, refresh hashing, cookie attributes, migration 0003 | unit + integration | `cd backend && uv run pytest tests/test_auth_session.py tests/test_config.py tests/test_migrations.py -q` | ⬜ pending |
| 02-04-T2 | 02-04 | 4 | AUTH-02, AUTH-04 | verify-code sets cookies; /me 200/401 incl. revoked session | api | `cd backend && uv run pytest -q --cov=app --cov-fail-under=80 && uv run coverage report --include=<critical modules> --fail-under=100` | ⬜ pending |
| 02-05-T1 | 02-05 | 5 | AUTH-01, AUTH-04 | apiFetch CSRF/ApiError, fetchMe, money format; e2e RED | vitest + e2e (expected fail) | `cd frontend && npm run test -- src/api src/lib && ! npx playwright test e2e/auth.spec.ts` | ⬜ pending |
| 02-05-T2 | 02-05 | 5 | AUTH-01, AUTH-02, AUTH-04, ACCT-01 | Auth switch, sign-in flow + error messages; e2e GREEN | vitest + e2e | `cd frontend && npm run test -- --coverage && npm run build && npx playwright test` | ⬜ pending |
| 02-06-T1 | 02-06 | 5 | AUTH-03 | Fixed-window hit/enforce, TTL always set, window expiry | unit | `cd backend && uv run pytest tests/test_ratelimit.py tests/test_config.py -q --cov=app.services.ratelimit --cov-branch --cov-fail-under=100` | ⬜ pending |
| 02-06-T2 | 02-06 | 5 | AUTH-03 | Per-email/IP/global 429 + Retry-After, no code on 429, uvicorn proxy defaults | api | `cd backend && uv run pytest -q --cov=app --cov-fail-under=80 && uv run coverage report --include=<critical modules> --fail-under=100` | ⬜ pending |
| 02-07-T1 | 02-07 | 6 | AUTH-04, AUTH-05, ACCT-01 | Refresh rotation, grace, family revoke, logout revokes at once | api | `cd backend && uv run pytest -q --cov=app --cov-fail-under=80 && uv run coverage report --include=<critical modules> --fail-under=100` | ⬜ pending |
| 02-07-T2 | 02-07 | 6 | AUTH-04, AUTH-05 | Single-flight refresh, Sign out; e2e cleared access cookie + sign-out | vitest + e2e | `cd frontend && npm run test -- --coverage && npx playwright test` | ⬜ pending |
| 02-08-T1 | 02-08 | 6 | AUTH-06 | Email backend settings, prod refuses console, no key in errors/repo | unit | `cd backend && uv run pytest tests/test_config.py -q; git grep -nE 're_[A-Za-z0-9_]{16,}' finds nothing` | ⬜ pending |
| 02-08-T2 | 02-08 | 6 | AUTH-06 | ResendSender request shape, retries, idempotency, log hygiene (respx) | unit | `cd backend && uv run pytest -q --cov=app --cov-fail-under=80 && uv run coverage report --include=app/services/email.py,<critical modules> --fail-under=100 && uv run pip-audit` | ⬜ pending |
| 02-09-T1 | 02-09 | 7 | all | Full suite + CI critical-coverage step | full suite | `backend lint/types/pytest + critical coverage, frontend lint/typecheck/test/build, docker compose up --build -d --wait && npx playwright test` | ⬜ pending |

Checkpoint tasks (no automated test): 02-01-T1 (branch after PR #2), 02-01-T2 (package gate), 02-09-T2 (real email, manual-only below), 02-09-T3 (push gate).

Requirement-level map:

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| AUTH-01 | Same response for new and existing email; request-code creates no rows; invalid email → 422 | api | `uv run pytest tests/test_auth_request_code.py` | ❌ W0 | ⬜ pending |
| AUTH-02 | Single-use, expiry, 5-attempt kill, new request invalidates old, concurrent verify → exactly one 200 | api + unit | `uv run pytest tests/test_otp_store.py tests/test_auth_verify.py` | ❌ W0 | ⬜ pending |
| AUTH-03 | Per-email and per-IP limits → 429 + Retry-After; counters have TTL | api | `uv run pytest tests/test_ratelimit.py` | ❌ W0 | ⬜ pending |
| AUTH-04 | Refresh rotation, reuse revokes family (grace window), cookie attributes, CSRF 403, bad JWT 401, single-flight refresh | api + vitest | `uv run pytest tests/test_auth_session.py tests/test_csrf.py` / `npm run test -- src/api` | ❌ W0 | ⬜ pending |
| AUTH-05 | Logout revokes the session at once; refresh after logout 401 | api | `uv run pytest tests/test_auth_session.py` | ❌ W0 | ⬜ pending |
| AUTH-06 | Resend sender request shape, retries, no code/key in logs; console sender in dev; prod refuses console | unit | `uv run pytest tests/test_email.py tests/test_config.py` | ❌ W0 | ⬜ pending |
| ACCT-01 | Exactly $10,000.00 once; concurrent first sign-ins → 1 user, 1 account | api + DB | `uv run pytest tests/test_accounts.py` | ❌ W0 | ⬜ pending |
| ACCT-02 | No reset/add-cash route; DB CHECK rejects negative cash; money sent as string | api | `uv run pytest tests/test_accounts.py` | ❌ W0 | ⬜ pending |
| Migration | 0002 upgrade/downgrade, no model drift | integration | `uv run pytest tests/test_migrations.py` | edit | ⬜ pending |
| UI | Sign-in flow, error/429 messages, auth gate, money format | vitest | `npm run test -- --coverage` | ❌ W0 | ⬜ pending |
| E2E | Fresh email → code from compose logs → $10,000.00 → reload still signed in → sign out | e2e | `npx playwright test e2e/auth.spec.ts` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Phase 1 review fixes: WR-04 (alembic template), WR-02 (logging), WR-05 (`.env.*` ignore)
- [ ] New packages approved via checkpoint, then installed: pyjwt, `pydantic[email]`, respx; httpx promoted to main deps
- [ ] `conftest.py` secrets in env; `auth_client` fixture (base_url `https://test`), outbox, Redis cleanup
- [ ] Smoke checks: httpx cookie jar on `https://test`; uvicorn proxy-header defaults
- [ ] `frontend/e2e/auth.spec.ts` helper reading the code from compose logs

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real code arrives from the verified domain | AUTH-06 | Needs the user's Resend key and inbox (D-01, D-02) | User puts their key in the local `.env` only, sets the email backend to resend, restarts the stack, requests a code to their own address, and signs in with it |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
