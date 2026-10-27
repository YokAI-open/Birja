---
phase: 02-authentication
reviewed: 2026-10-27T14:27:52Z
depth: standard
files_reviewed: 58
files_reviewed_list:
  - .env.example
  - .github/workflows/ci.yml
  - .gitignore
  - backend/.dockerignore
  - backend/alembic/env.py
  - backend/alembic/script.py.mako
  - backend/alembic/versions/0002_users_and_accounts.py
  - backend/alembic/versions/0003_auth_sessions.py
  - backend/app/api/v1/auth.py
  - backend/app/api/v1/me.py
  - backend/app/api/v1/router.py
  - backend/app/core/config.py
  - backend/app/core/deps.py
  - backend/app/core/logging.py
  - backend/app/core/security.py
  - backend/app/main.py
  - backend/app/models/__init__.py
  - backend/app/models/auth.py
  - backend/app/models/user.py
  - backend/app/schemas/auth.py
  - backend/app/services/accounts.py
  - backend/app/services/auth.py
  - backend/app/services/email.py
  - backend/app/services/health.py
  - backend/app/services/otp.py
  - backend/app/services/ratelimit.py
  - backend/pyproject.toml
  - backend/tests/conftest.py
  - backend/tests/helpers.py
  - backend/tests/test_accounts.py
  - backend/tests/test_auth_request_code.py
  - backend/tests/test_auth_session.py
  - backend/tests/test_auth_verify.py
  - backend/tests/test_config.py
  - backend/tests/test_config_ratelimit.py
  - backend/tests/test_csrf.py
  - backend/tests/test_email.py
  - backend/tests/test_health.py
  - backend/tests/test_migrations.py
  - backend/tests/test_otp_store.py
  - backend/tests/test_ratelimit.py
  - docker-compose.yml
  - frontend/.dockerignore
  - frontend/e2e/auth.spec.ts
  - frontend/src/App.test.tsx
  - frontend/src/App.tsx
  - frontend/src/api/auth.test.ts
  - frontend/src/api/auth.ts
  - frontend/src/api/client.test.ts
  - frontend/src/api/client.ts
  - frontend/src/components/ui/input.tsx
  - frontend/src/hooks/useAuthMutations.ts
  - frontend/src/hooks/useMe.ts
  - frontend/src/lib/money.test.ts
  - frontend/src/lib/money.ts
  - frontend/src/pages/AccountPage.tsx
  - frontend/src/pages/SignInPage.test.tsx
  - frontend/src/pages/SignInPage.tsx
findings:
  critical: 0
  warning: 5
  info: 5
  total: 10
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-10-27T14:27:52Z
**Depth:** standard
**Files Reviewed:** 58
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

I reviewed the full auth surface: OTP store (Lua attempt and consume scripts), rate limiter, request and verify flows, JWT issue and decode, the refresh rotation and reuse detection, logout, CSRF double-submit, cookie flags and paths, the schema and migrations, the Resend sender, settings validation, CI, and the frontend single-flight refresh client and sign-in UI.

The core design holds up. Here is what I checked and found correct:
- **OTP:** codes come from `secrets`. Only an HMAC keyed by email and code is stored, with a 600 s TTL. Attempts are counted atomically before any compare, `compare_digest` is used, the code is consumed by compare-and-delete, and issuing a new code replaces the old one.
- **Enumeration:** `request-code` does no user lookup. Every verify failure returns one 400 body.
- **JWT:** the algorithm is pinned to HS256. `exp`, `iat`, `sub` and `sid` are required, `iss`, `aud` and `typ` are checked, and every request looks up the session (`revoked_at IS NULL`).
- **Refresh:** rotation runs under `FOR UPDATE`, has a grace window and revokes the session on reuse.
- **Logout:** it revokes even when the JWT has expired. Accepted risk T-02-54 was not re-flagged.
- **CSRF:** every POST is covered.
- **Cookies:** all are `Secure` and `SameSite=Strict`. The refresh cookie is scoped to its path.
- **Money:** amounts are `NUMERIC(20,8)`, serialized as strings, and formatted without float conversion.
- **Schema:** CHECK, UNIQUE and FK constraints are present, and FK columns are indexed.

I found no BLOCKER. The warnings are about how the rate-limit keys and order make cheap targeted or app-wide sign-in denial possible, one CSRF input that triggers a 500, a long-run gap in the brute-force limit, and a small non-atomic delete in the OTP store.

## Warnings

### WR-01: CSRF check raises 500 on non-ASCII cookie/header values

**Status:** Fixed in `710e0a9`.

**File:** `backend/app/core/deps.py:48`
**Issue:** `hmac.compare_digest(cookie, header)` on `str` arguments raises `TypeError("comparing strings with non-ASCII characters is not supported")`. Starlette decodes headers as latin-1, so a request with byte `0xE9` in `yk_csrf` or `X-CSRF-Token` crashes the dependency. I confirmed it with an ASGI probe against `POST /api/v1/auth/logout`: a non-ASCII token returns `500 Internal Server Error`, and a mismatched ASCII token returns the expected 403 `csrf_failed`. It is not exploitable for a bypass. Still, attacker-controlled input produces unhandled exceptions and stack traces in logs on every state-changing route, and the status code is wrong.
**Fix:**
```python
def verify_csrf(request: Request) -> None:
    cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get(CSRF_HEADER)
    if (
        not cookie
        or not header
        or not hmac.compare_digest(cookie.encode("utf-8"), header.encode("utf-8"))
    ):
        raise HTTPException(status_code=403, detail={...})
```
Add a regression test that sends raw latin-1 header bytes and expects 403.

### WR-02: Per-email counters are charged before the per-IP limit, so one IP can lock any number of users out of sign-in

**Status:** Fixed in `fe3cd88`.

**File:** `backend/app/services/auth.py:33-44, 81-89`
**Issue:** In both `request_code` and `verify_code`, the per-email `enforce` (INCR) runs before the per-IP `enforce`. Once an IP is over its own limit, each of its requests is still counted against the target email's bucket before the IP check rejects it. So the per-IP limit puts no ceiling on how many victims one IP can affect.
- On verify, 10 junk `verify-code` calls per 10 minutes per victim keep the victim's `sim:rl:ver:email:*` bucket full. Their correct code then always gets 429.
- 5 wrong attempts also delete the victim's live code.

The trade-off in `ratelimit.py` only accepts a nuisance lockout of the request quota, and only for one window. This is a lasting, targeted sign-in denial against any known email, from a single IP, at roughly one request per minute per victim.
**Fix:** Check the IP bucket first, so requests the IP limit refuses never touch per-email state:
```python
await enforce(redis, f"sim:rl:ver:ip:{ip}", settings.rl_verify_ip_limit, settings.rl_verify_ip_window)
await enforce(redis, f"sim:rl:ver:email:{otp.email_key(email)}", ...)
```
Do the same in `request_code` (IP, then email, then global). Add a test that an IP-limited caller does not increment the email key. Separately, consider recording the trade-off that verify lockout of a victim is accepted, or mitigate it (for example, don't count verify attempts when no code is pending).

### WR-03: The global send cap is a cheap app-wide kill switch (24 h), and per-IP keys use the raw address

**Status:** Fixed in `04304ef`.

**File:** `backend/app/services/auth.py:39-44`, `backend/app/core/config.py:30-37`
**Issue:**
- `sim:rl:req:global` allows 500 sends per fixed 86 400 s window, and per-IP allows 20 per hour. One IP gets to 480 per day by itself. 25 IPs exhaust the cap within an hour, and then nobody can request a code until the window resets (`Retry-After` up to ~86 400).
- The per-IP key is the full `request.client.host`. Once IPv6 is served, any /64 holder has unlimited distinct per-IP buckets.

This is not an enumeration leak, but for a friends-only app it turns the abuse protection into the easiest denial-of-service.
**Fix:** Keep the global cap as a cost guard, but make it harder to trip and quicker to recover from:
- Use a shorter window, for example an hourly cap of about 50, so recovery takes at most an hour.
- Bucket IPv6 by /64 in `get_client_ip`:
  ```python
  addr = ipaddress.ip_address(host)
  key = str(ipaddress.ip_network(f"{host}/64", strict=False)) if addr.version == 6 else host
  ```
- Log a warning when the global cap trips, so an operator notices.

### WR-04: No long-horizon cap on verify attempts per email (slow brute force)

**Status:** Fixed in `1538f5a`.

**File:** `backend/app/core/config.py:32-33`, `backend/app/services/auth.py:81-91`
**Issue:**
- An attacker can request codes for a victim (5 per 600 s) and guess against them (10 verifies per 600 s per email). That is 1 440 guesses a day against a 10^6 code space: about 0.14% success per day, about 4% over 30 days, about 40% over a year.
- Per-IP limits don't bound this (see WR-02 and WR-03).
- Nothing escalates. No daily cap or lockout exists, and repeated 5-strike code deaths have no consequence.

CLAUDE.md asks for limits that "block ... brute force". These windows only slow it down.
**Fix:** Add a second, long-window per-email verify bucket, for example `rl_verify_email_daily_limit=30` over 86 400 s, checked in `verify_code`. With 30 guesses a day, a year of attempts gives a success chance below 1.1%. Alternatively, count killed codes per email and lock the email for 24 h after N kills.

### WR-05: Non-atomic DEL after the 5th wrong attempt can delete a freshly issued code

**Status:** Fixed in `1673e4e`.

**File:** `backend/app/services/otp.py:76-77`
**Issue:** When `attempts >= self._max`, `verify` runs a plain `DEL` in a separate round trip after the Lua attempt script. If `issue()` replaces the key between the two calls, which happens when the user clicks "Send a new code" right as a 5th wrong guess lands, the unconditional `DEL` removes the new code. The user then gets "wrong or expired" for a code that was just emailed. The rest of the store is carefully atomic (attempt script, compare-and-delete consume), and this one step is not.
**Fix:** Delete only if the key still holds the MAC that was attempted, reusing the existing consume script:
```python
if attempts >= self._max:
    await self._consume(keys=[key], args=[stored_mac])  # compare-and-delete
```
Or move the "delete on the max-th wrong attempt" into a single Lua script that also receives the candidate MAC. The Redis-side equality check on HMAC values leaks nothing usable without the key.

## Fix log

All five warnings were fixed on 2026-10-27, one commit each. The Info items are not addressed.

| Finding | Commit | Change |
|---------|--------|--------|
| WR-01 | `710e0a9` | `verify_csrf` compares cookie and header as UTF-8 bytes, so non-ASCII input returns 403 `csrf_failed`, not 500. Regression tests cover a non-ASCII header and cookie. |
| WR-02 | `fe3cd88` | `request_code` checks IP, then email, then global; `verify_code` checks IP before email. Tests show an IP over its limit no longer increments a victim's per-email counter. |
| WR-03 | `04304ef` | `ip_bucket()` in `ratelimit.py` groups IPv6 by /64 (IPv4 and IPv4-mapped addresses stay per address) and is used for every per-IP key. The global cap is now 100 per hour (`RL_SEND_GLOBAL_LIMIT` / `RL_SEND_GLOBAL_WINDOW`, existing names kept). Tripping it logs a WARNING under `app.*` with no email or IP. |
| WR-04 | `1538f5a` | New per-email daily verify bucket `sim:rl:ver:email-day:<hmac>`, default 30 per 86 400 s (`RL_VERIFY_EMAIL_DAILY_LIMIT` / `RL_VERIFY_EMAIL_DAILY_WINDOW`). It returns the same generic 429 with Retry-After. |
| WR-05 | `1673e4e` | The kill on the 5th wrong attempt reuses the compare-and-delete script with the attempted MAC. A regression test shows a code issued in between survives. |

## Info

### IN-01: Cross-tab refresh grace path can still show the losing tab as signed out

**File:** `frontend/src/api/client.ts:99-104`, `backend/app/services/auth.py:126-129`
**Issue:**
- The grace branch returns 401 without clearing cookies, on the assumption that the winner's `Set-Cookie` is already in the shared jar.
- `apiFetch` retries straight away, so this works only if the winning tab's response has been processed first. The server commits before it sends the response, and the loser's row lock is released at commit, so the loser's 401 can arrive before the winner's cookies land.
- In that case the retry gets 401, `fetchMe` returns `null`, and the tab shows the sign-in card even though the session is valid. A reload fixes it.

**Fix:** When refresh returns 401 without `max-age=0` cookies (the grace case), wait briefly (for example 200–500 ms) before retrying. Or return a distinct body code, such as `refresh_raced`, and retry once on it.

### IN-02: `formatUsd` throws during render with no error boundary

**File:** `frontend/src/lib/money.ts:5-7`, `frontend/src/api/auth.ts:10`, `frontend/src/pages/AccountPage.tsx:20`
**Issue:** `isMe` checks only `typeof cash_usd === "string"`. A malformed value (for example `"NaN"` or `"1e5"`) passes the guard, and `formatUsd` throws inside render. With no error boundary, the whole app unmounts to a blank page.
**Fix:** Validate the decimal format in `isMe`, with the same regex as `formatUsd`, so the query errors cleanly. Or add an error boundary around `AuthSwitch`.

### IN-03: Dev email codes and addresses land in public CI logs on e2e failure

**File:** `.github/workflows/ci.yml:133-135`, `backend/app/services/email.py:28`
**Issue:** The failure step runs `docker compose logs`, which prints `DEV EMAIL to=<email> code=<code>` lines into public Actions logs. The accounts are throwaway (`e2e-*@example.com`) and the stack is ephemeral, so there is no real exposure. It does go against "never log the raw code", and it would leak real addresses if anyone ever ran e2e with real emails.
**Fix:** Filter the dump, for example `docker compose logs --no-color | sed -E 's/code=[0-9]{6}/code=******/'`, or exclude the backend log lines that match `DEV EMAIL`.

### IN-04: `ENV` defaults to `dev` (fail-open)

**File:** `backend/app/core/config.py:14`, `docker-compose.yml:52`
**Issue:** If `ENV` is omitted, the app silently runs as dev:
- `/docs`, `/redoc` and the OpenAPI schema are exposed.
- The console email backend, which logs codes, is allowed.
- Per-IP limits are loosened to 200/300.

This is fine for local work, but a missed variable at deploy time weakens auth without any error.
**Fix:** In the deploy phase, require `ENV` explicitly (no default, `${ENV:?}` in compose), or default to `prod` and set `dev` in `.env.example`.

### IN-05: `apiFetch` ignores the refresh result and retries anyway

**File:** `frontend/src/api/client.ts:101-104`
**Issue:** `await refreshSession()` returns `false` when refresh fails, but the original request is re-sent regardless. That is a doomed extra round trip on every signed-out load of `/me`. Once non-idempotent endpoints exist (trades in Phase 3+), retrying a POST after a failed refresh is also an easy footgun.
**Fix:** `if (!(await refreshSession())) throw await toApiError(response);` (or return the original 401), and retry only when refresh returned `true`. Keep the IN-01 grace handling in mind if you change this.

---

_Reviewed: 2026-10-27T14:27:52Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
