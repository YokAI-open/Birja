# Phase 2: Authentication - Research

**Researched:** 2026-10-27
**Domain:** Email one-time-code login, cookie sessions (JWT + rotating refresh), CSRF, Redis OTP/rate limits, first Postgres tables, React auth gate
**Confidence:** MEDIUM-HIGH (design follows CLAUDE.md and project research; Resend REST API and Secure-on-localhost verified against official docs; library versions checked on PyPI; Package Legitimacy gate could NOT be run, see audit)

<user_constraints>
## User Constraints

No CONTEXT.md exists for this phase (user chose to plan without discuss-phase and without UI-SPEC).

### Locked Decisions (from the session brief and CLAUDE.md)
- CLAUDE.md "Security" (Login, Session), "Data/caching" (Redis keys, rate limits, transactions), "Money and numbers" and "API" sections are authoritative: research HOW, not whether.
- Signup is open: anyone with an email can sign in; the first successful sign-in creates the account.
- No UI-SPEC; style comes from `design-system/yokaiexchange/MASTER.md` plus the existing shadcn card/badge/button.
- Mode: MVP. Push back on bloat.

### Claude's Discretion
Everything else in the brief's "key questions" (Resend client choice, token claims, schema shape, CSRF mechanics, rate-limit numbers, routing, e2e code retrieval).

### Deferred Ideas (OUT OF SCOPE)
Anything in REQUIREMENTS.md v2 or Phases 3-6. Not for this phase: account deletion, email change, "remember me" toggles, magic links, multiple devices UI, session list, admin, Celery, nginx, DB role hardening.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUTH-01 | Request 6-digit code, identical response regardless of account | `POST /auth/request-code` does no user lookup at all (account is created on verify), so responses and code path are identical by construction. Always enqueue the send. |
| AUTH-02 | Single-use code, ~10 min, dies after 5 wrong attempts | Redis HASH `sim:otp:<email-hmac>` {mac, attempts}, TTL 600; attempt counted atomically BEFORE compare (Lua), consume via compare-and-delete Lua. |
| AUTH-03 | Rate limits per email and per IP | Fixed window `INCR` + `EXPIRE NX` in one MULTI pipeline; 429 + `Retry-After`; IP from `request.client.host` only (uvicorn proxy-headers does the trust work). |
| AUTH-04 | Stay signed in up to ~30 days | 15 min access JWT cookie + 30 d opaque refresh cookie (Path-scoped), hash in Postgres, rotation with reuse detection; frontend single-flight silent refresh. |
| AUTH-05 | Sign out ends session server-side | `auth_sessions.revoked_at`; access JWT carries `sid` and `get_current_user` checks the session row, so logout is immediate (not "up to 15 min later"). |
| AUTH-06 | Real email via Resend, console in dev | `EmailSender` protocol: Console, Resend (plain `httpx` to `POST https://api.resend.com/emails`), in-memory Outbox for tests. |
| ACCT-01 | $10,000.00 granted exactly once | `accounts` row inserted in the same transaction as the `users` row created via `INSERT ... ON CONFLICT (email) DO NOTHING RETURNING id`. |
| ACCT-02 | No reset / add cash | Zero endpoints that mutate `accounts.cash`; route-allow-list test; DB `CHECK (cash >= 0)`. |
</phase_requirements>

## Summary

The phase adds the first three real concerns of the app: Redis-backed one-time codes with rate limits, cookie sessions (short access JWT + rotating refresh token stored hashed in Postgres) with double-submit CSRF, and the first domain tables (`users`, `accounts`, `auth_sessions`, `refresh_tokens`). All of it fits the Phase 1 skeleton without changing its decisions: relative `/api` URLs through the Vite proxy (single origin, so no CORS), `create_app()` + `lifespan` for shared resources, `Annotated` deps in `core/deps.py`, thin routes over `services/`.

Three design choices go beyond what CLAUDE.md spells out and are the most important for the planner: (1) the OTP verify path is split into two atomic Redis steps so the compare can use `hmac.compare_digest` yet still be race-free; (2) the access JWT carries a session id (`sid`) that is checked against Postgres on every authenticated request, so sign-out ends the session immediately, which success criterion 4 requires ("the session no longer works"); (3) no new infrastructure: email goes through plain `httpx.AsyncClient` (no Resend SDK), the e2e test reads the dev code from `docker compose logs` (no debug route), and no react-router yet (an auth-state switch is enough until Phase 3 adds a second signed-in page).

Phase 1 left three open review warnings that this phase trips over and must fix in its first plan: WR-04 (the Alembic template emits migrations that fail the repo's own ruff gate; this phase writes the first real migration), WR-02 (app loggers are not configured, so the dev console email backend would print NOTHING), WR-05 (`.env.*` not ignored/dockerignored; this phase introduces real secrets in env files).

**Primary recommendation:** Build in this order: (0) fix WR-04/WR-02/WR-05 + settings/secrets; (1) models + migration 0002; (2) Redis OTP store + rate limiter + email senders; (3) token/session service, cookies, CSRF, deps, endpoints; (4) frontend apiFetch + auth gate + sign-in UI; (5) tests/e2e. Keep it to 6 endpoints.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Code generation, HMAC, attempt limits | API / Backend | Redis | Secrets and counters must be server-side; Redis holds only disposable state |
| Rate limiting (email, IP) | API / Backend | Redis | Counters in Redis with TTL; client IP resolved by uvicorn proxy-headers |
| Sending email | API / Backend (BackgroundTasks) | External (Resend) | After the response, so latency and failure never leak account existence |
| Session / refresh tokens | API / Backend | Database | Refresh hashes must survive Redis restarts and be revocable: Postgres |
| Cookie issuing, CSRF validation | API / Backend | Browser | HttpOnly cookies set by server; the browser only echoes the CSRF header |
| Authorization of every route | API / Backend | — | `CurrentUserDep`; frontend gate is UX only |
| Account + $10,000 grant | Database | API | Constraints (UNIQUE email, CHECK cash >= 0, one account per user) enforce "exactly once" |
| Auth state in UI, silent refresh, money display | Browser / Client | — | TanStack Query `/me`; formatting of server strings only |
| Single-origin cookie behavior | Vite proxy (dev) / nginx (Phase 6) | — | Same path layout in both so Path-scoped cookies match |

## Standard Stack

### Core (new in this phase)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyJWT | 2.15.1 (PyPI, checked 2026-10-27) | Access token encode/decode | CLAUDE.md mandates PyJWT, not python-jose |
| email-validator (via `pydantic[email]`) | 2.3.0 (PyPI) | `EmailStr` validation | Pydantic's supported way; avoids a hand-rolled regex. Keep `pydantic==2.14.1`, change dependency to `pydantic[email]==2.14.1` |
| httpx | 0.28.1 (already a **dev** dep) | Resend REST calls | Move to main dependencies; already used in tests; native async |
| respx | 0.23.1 (PyPI) | Mock Resend at the HTTP boundary | CLAUDE.md test rule; dev group only |

Already present and reused: FastAPI 0.162, SQLAlchemy 2 async + asyncpg, Alembic 1.20.1, `redis==8.1.0` (asyncio, `register_script`), pydantic-settings.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| httpx to Resend REST | `resend` PyPI SDK (2.50.0) | SDK would add a dependency; I did not verify whether it is sync (assumed requests-based). Starlette runs sync background callables in a threadpool, so it would not block the loop, but plain httpx is one call, async, and respx-testable. [ASSUMED: SDK internals] |
| Log-scraping e2e | Dev-only `GET /dev/last-code` route | Route is a backdoor surface CLAUDE.md forbids "reachable outside local dev"; log scraping needs no app code. Use log scraping. |
| react-router now | Auth-state switch in `App` | See Frontend section: switch now, router in Phase 3 |
| Redis denylist for logout | `sid` check in Postgres | Redis is not the source of truth; Postgres lookup is one indexed PK join we already do for the user |

**Installation:**
```bash
cd backend
uv add "pyjwt==2.15.1"
uv add "pydantic[email]==2.14.1"        # replaces the plain pydantic pin
uv add "httpx==0.28.1"                  # promote from dev group to main dependencies (remove from dev group)
uv add --dev "respx==0.23.1"
```
No frontend npm packages are required. Add shadcn `input` (and `label`) via the already-installed `shadcn` CLI (source copied to `src/components/ui/`).

## Package Legitimacy Audit

slopcheck could NOT be run: the auto-mode classifier denied `pip install slopcheck`, so per protocol **all packages below are `[ASSUMED]` for legitimacy** and the planner must gate each install behind a `checkpoint:human-verify` task (the Phase 1 plan 01 pattern of "user confirms package list" already exists). Existence and latest versions were confirmed with `pip index versions` only (registry existence does not confer verified status).

| Package | Registry | Latest (checked) | Source Repo | slopcheck | Disposition |
|---------|----------|------------------|-------------|-----------|-------------|
| pyjwt | PyPI | 2.15.1 | github.com/jpadilla/pyjwt (well known; named in CLAUDE.md) | not run | Approved by CLAUDE.md; confirm in checkpoint |
| pydantic[email] / email-validator | PyPI | 2.3.0 | github.com/JoshData/python-email-validator (official pydantic extra) | not run | `[ASSUMED]` gate |
| respx | PyPI | 0.23.1 | github.com/lundberg/respx (named in CLAUDE.md) | not run | Approved by CLAUDE.md; confirm in checkpoint |
| httpx | PyPI | 0.28.1 | already locked | n/a | already installed |

**Packages removed ([SLOP]):** none (check not run). **Flagged [SUS]:** none known. Verify each version resolves for Python 3.14 when running `uv add` (respx 0.23.1 + httpx 0.28.1 compatibility is `[ASSUMED]`; the first test run in Wave 0 proves it).

## Architecture Patterns

### System Architecture Diagram

```
Browser (React, TanStack Query, apiFetch)
  | relative /api/v1/... , cookies: yk_access(HttpOnly) yk_refresh(HttpOnly, Path=/api/v1/auth/refresh) yk_csrf(JS-readable)
  v
Vite proxy (dev) / nginx (Phase 6)  --- sets client IP; uvicorn --proxy-headers trusts only that hop
  v
FastAPI router /api/v1
  |-- GET  /auth/csrf ------------------------------------------> set yk_csrf if absent (204)
  |-- POST /auth/request-code {email}  [CSRF]
  |      normalize email -> rate limit (email, ip, global) --429--> Retry-After
  |      -> OtpStore.issue (Redis: DEL+HSET+EXPIRE, replaces old code) -> BackgroundTasks.add(send_code)
  |      -> 202 {"status":"code_sent"}  (same for every email)
  |         BackgroundTask: EmailSender (Console -> log line | Resend -> httpx POST api.resend.com/emails, retries)
  |-- POST /auth/verify-code {email, code}  [CSRF]
  |      rate limit (email, ip) -> OtpStore.attempt (Lua: INCR attempts, >5 => DEL) -> compare_digest
  |      -> OtpStore.consume (Lua compare-and-delete)  -> get_or_create_user (Postgres txn: users+accounts)
  |      -> create auth_session + refresh_token row -> set 3 cookies -> 200 {email, cash_usd}
  |-- POST /auth/refresh [CSRF, cookie yk_refresh]
  |      SELECT refresh_tokens ... FOR UPDATE -> used? (grace window | revoke family) -> rotate -> set cookies -> 204
  |-- POST /auth/logout [CSRF, access cookie] -> auth_sessions.revoked_at = now -> clear cookies -> 204
  |-- GET  /me [access cookie] -> CurrentUserDep (JWT decode + users JOIN auth_sessions revoked_at IS NULL)
  v
Postgres: users, accounts, auth_sessions, refresh_tokens        Redis: sim:otp:*, sim:rl:*  (all with TTL)
```

### Recommended Project Structure
```
backend/app/
├── api/v1/auth.py            # 5 auth routes (thin)
├── api/v1/me.py              # GET /me
├── core/security.py          # JWT encode/decode, token hashing, cookie helpers, csrf compare
├── core/logging.py           # configure_logging() (fixes WR-02)
├── core/deps.py              # + CurrentUserDep, CsrfDep, HttpDep, EmailSenderDep, ClientIpDep
├── models/{__init__,user,auth}.py   # first use of models/ (import all in __init__ for Alembic)
├── schemas/auth.py           # RequestCodeIn, VerifyCodeIn, MeOut (Decimal -> string)
├── services/auth.py          # request_code, verify_code, refresh, logout, get_or_create_user
├── services/otp.py           # OtpStore (Redis + Lua)
├── services/ratelimit.py     # fixed-window limiter
└── services/email.py         # EmailSender protocol, ConsoleSender, ResendSender, OutboxSender
backend/alembic/versions/0002_auth_tables.py
frontend/src/{api/client.ts,api/auth.ts,hooks/useMe.ts,hooks/useAuthMutations.ts,lib/money.ts,pages/SignInPage.tsx,pages/AccountPage.tsx}
frontend/e2e/auth.spec.ts
```

### Pattern 1: Resend via plain httpx (verified API)
**What:** `POST https://api.resend.com/emails`, header `Authorization: Bearer <key>`, JSON body `{from, to, subject, text, html}`, success `{"id": "..."}`; optional `Idempotency-Key` header (unique per request, up to 256 chars, expires after 24 h). Default team limit is 10 requests/s, 429 on excess with `retry-after`. [CITED: resend.com/docs/api-reference/emails/send-email, resend.com/docs/api-reference/rate-limit]
**When:** the `resend` backend; one shared `httpx.AsyncClient(timeout=10)` created in `lifespan` as `app.state.http`.
```python
# services/email.py
class EmailSender(Protocol):
    async def send_code(self, to: str, code: str) -> None: ...

class ResendSender:
    def __init__(self, client: httpx.AsyncClient, api_key: str, sender: str) -> None: ...
    async def send_code(self, to: str, code: str) -> None:
        key = secrets.token_urlsafe(16)               # Idempotency-Key: retries cannot double-send
        for attempt in range(3):                       # bounded; code is useless after 10 min anyway
            try:
                r = await self._client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {self._key}", "Idempotency-Key": key},
                    json={"from": self._from, "to": [to], "subject": "Your YokaiExchange sign-in code",
                          "text": f"Your sign-in code is {code}. It expires in 10 minutes."},
                )
                if r.status_code < 300: return
                if r.status_code not in (429, 500, 502, 503, 504): break   # 4xx: do not retry
            except httpx.TransportError: pass
            await asyncio.sleep(min(2**attempt, 4) + random.random())      # exponential + jitter
        logger.error("email send failed")              # NEVER log the code or key
```
Rules: failures are logged and swallowed (the user can request another code); never raise out of a BackgroundTask silently without a log line; the raw code must not appear in any log in `resend` mode.

### Pattern 2: Dev console backend and e2e retrieval
`ConsoleSender` logs one line: `DEV EMAIL to=<email> code=<code>` at INFO. This is the explicit CLAUDE.md exception ("console/log backend in local dev"). Guard: `Settings` validator refuses `EMAIL_BACKEND=console` when `ENV=prod` (and refuses `resend` without `RESEND_API_KEY`/`EMAIL_FROM`). Playwright reads the code with `execSync("docker compose logs --no-color --since 2m backend", {cwd: repoRoot})` and a regex on the unique test email. No HTTP route, no file. Tests (pytest) use `OutboxSender` (list of `(to, code)`) swapped in through `app.state.email_sender`.

### Pattern 3: OTP store in Redis (atomic, compare_digest-compatible)
Key `sim:otp:<hmac(email)>` HASH `{mac, attempts}`, TTL 600 s. `email_key = HMAC-SHA256(otp_secret, "email:"+norm_email).hexdigest()`; `mac = HMAC-SHA256(otp_secret, f"otp:{norm_email}:{code}").hexdigest()`; code via `f"{secrets.randbelow(10**6):06d}"`.
- **issue** (MULTI pipeline): `DEL key; HSET key mac <mac> attempts 0; EXPIRE key 600` (new request invalidates the old code).
- **attempt** (Lua, atomic): if no key -> return nil. `n = HINCRBY key attempts 1`; if `n > 5` then `DEL key` return nil; else return `{mac, n}`. Python then runs `hmac.compare_digest(stored, candidate)`.
- On mismatch with `n >= 5`: `DEL key` (5th wrong attempt kills the code).
- **consume** (Lua compare-and-delete): `if HGET key mac == ARGV[1] then DEL key return 1 else return 0`. Only one concurrent verifier gets 1, so a code is single-use even under parallel requests. Attempts are counted before the compare, so N parallel guesses still total at most 5.
- All failure modes (no key, expired, locked, wrong) return the same `400 {"detail": {"code":"invalid_code","message":"..."}}`.
```python
ATTEMPT = redis.register_script("""
local mac = redis.call('HGET', KEYS[1], 'mac')
if not mac then return nil end
local n = redis.call('HINCRBY', KEYS[1], 'attempts', 1)
if n > tonumber(ARGV[1]) then redis.call('DEL', KEYS[1]); return nil end
return {mac, n}
""")
```
Redis outage: auth cannot work without Redis; return `503` (not 500). This is not a cache, so "cold cache is normal" does not apply.

### Pattern 4: Fixed-window rate limiter
```python
async def hit(redis, key: str, limit: int, window: int) -> tuple[bool, int]:
    async with redis.pipeline(transaction=True) as p:
        p.incr(key); p.expire(key, window, nx=True); p.ttl(key)
        n, _, ttl = await p.execute()
    return n <= limit, max(ttl, 1)
```
`EXPIRE ... NX` (Redis 7+; image is Redis 8.8) in the same MULTI means a key can never be left without TTL. On deny raise `HTTPException(429, headers={"Retry-After": str(ttl)})`. Keys: `sim:rl:req:email:<email_key>`, `sim:rl:req:ip:<ip>`, `sim:rl:ver:email:<email_key>`, `sim:rl:ver:ip:<ip>`, `sim:rl:req:global`. Suggested defaults, all in Settings so tests/e2e can adjust: request per email 5 / 10 min, per IP 20 / hour, verify per email 10 / 10 min, per IP 30 / 10 min, global sends 500 / day (protects the Resend quota; free-tier numbers unverified `[ASSUMED]`). Enforce limits BEFORE doing OTP work; count the request even when the email is invalid-looking. Known trade-off: an attacker can burn a victim's per-email request quota (nuisance lockout); acceptable for a friends-only app, say so in the code comment.

### Pattern 5: Client IP
App code reads only `request.client.host`. Let uvicorn resolve proxies: `--proxy-headers` is on by default and trusts only `--forwarded-allow-ips` (default `127.0.0.1`) `[ASSUMED from uvicorn docs, confirm in Wave 0]`. Dev: the Vite proxy (http-proxy) does not add `X-Forwarded-For` by default and connects from the frontend container, so every dev/e2e request shares one IP bucket: fine, but it is why the per-IP defaults must tolerate repeated local e2e runs. Phase 6: nginx sets `X-Forwarded-For $remote_addr` (overwrite, not append) and uvicorn runs with `--forwarded-allow-ips=<nginx container IP/CIDR>`. Never parse `X-Forwarded-For` in app code. Test with `httpx.ASGITransport(client=("203.0.113.9", 1234))` for per-IP limit tests.

### Pattern 6: Sessions and tokens
- **Access token**: PyJWT HS256 with `JWT_SECRET` (distinct from `OTP_HMAC_SECRET`, both >= 32 chars). Claims: `sub` (user id **as str**; PyJWT >= 2.10 validates `sub` is a string `[ASSUMED]`), `sid` (auth_sessions.id), `iat`, `exp` (15 min), `iss="yokai"`, `aud="yokai-web"`, `typ="access"`. Decode: `jwt.decode(token, secret, algorithms=["HS256"], audience=..., issuer=..., options={"require": ["exp","iat","sub","sid"]})`; catch `jwt.PyJWTError` -> 401. Never accept `alg` from the header.
- **`get_current_user`** (CurrentUserDep): decode, then one query: `users JOIN auth_sessions ON sid WHERE users.id=:sub AND auth_sessions.user_id=users.id AND revoked_at IS NULL`. Missing/invalid -> 401. This is what makes logout immediate.
- **Refresh token**: `secrets.token_urlsafe(32)`; store `sha256(token).hexdigest()` (fast hash is fine for 256-bit randomness).
- **Rotation** (one transaction): `SELECT ... FROM refresh_tokens WHERE token_hash=:h FOR UPDATE` joined to session; none/expired/session revoked -> 401 and clear cookies. If `used_at IS NOT NULL`: if `now - used_at <= REFRESH_REUSE_GRACE_SECONDS` (default 10) -> 401 **without** revoking (two tabs racing; the winner's response already put new cookies in the shared jar); else **revoke the whole family** (`auth_sessions.revoked_at = now`) -> 401. Otherwise set `used_at=now`, insert the new token (sliding `expires_at = now+30d`), re-issue cookies.
- **Cookies** (all `Secure`, `SameSite=Strict`): `yk_access` HttpOnly Path=/api Max-Age 900; `yk_refresh` HttpOnly **Path=/api/v1/auth/refresh** Max-Age 2592000; `yk_csrf` NOT HttpOnly Path=/ (Max-Age 30 d, rotated at login, cleared at logout). Delete = same name+Path with `Max-Age=0`. A response from `/auth/logout` may delete the refresh cookie by sending `Set-Cookie` with the refresh Path (Path need not equal the request path). [CITED: developer.mozilla.org Set-Cookie]
- **Logout vs Path-scoped refresh cookie**: `/auth/logout` never receives `yk_refresh`, so it identifies the session through the access cookie's `sid` and revokes it; it must still clear all cookies and return 204 even if the access token is invalid.
- **`Secure` on http://localhost**: browsers ignore the https requirement for localhost, so Chrome/Firefox (and Playwright Chromium at `http://localhost:5173`) accept and return Secure cookies. [CITED: MDN Set-Cookie: "The https: requirements are ignored when the Secure attribute is set by localhost"]. Safari is the known exception (not a target). Use `localhost`, not a LAN hostname, in dev. Backend pytest: httpx's cookie jar will NOT resend Secure cookies over `http://`, so build the auth test client with `base_url="https://test"` (ASGITransport ignores the scheme). Do not add a `COOKIE_SECURE=false` switch.

### Pattern 7: CSRF double-submit
`GET /auth/csrf` sets `yk_csrf` (32 random bytes urlsafe) if absent and returns 204. A `CsrfDep` dependency (cookie vs `X-CSRF-Token` header, `hmac.compare_digest`, missing/mismatch -> **403**) is attached at router level to every POST in the auth router (request-code, verify-code, refresh, logout) and by convention to every future state-changing router. Pre-auth endpoints are covered too (CLAUDE.md: every state-changing request). GET /me and GET /auth/csrf never change auth state. Frontend `apiFetch` reads `document.cookie`; if absent on a mutation it calls `/auth/csrf` first. No `CORSMiddleware` at all (single origin).

### Pattern 8: Accounts, exactly once
```python
stmt = (pg_insert(User).values(email=email).on_conflict_do_nothing(index_elements=["email"])
        .returning(User.id))
user_id = (await db.execute(stmt)).scalar_one_or_none()
created = user_id is not None
if created:
    db.add(Account(user_id=user_id, cash=STARTING_CASH, starting_cash=STARTING_CASH))
else:
    user_id = (await db.execute(select(User.id).where(User.email == email))).scalar_one()
await db.commit()   # user + account atomically; a repeat sign-in never touches accounts
```
`STARTING_CASH = Decimal("10000.00")` constant in code (no hidden server default). Concurrent first sign-ins: the loser's INSERT waits on the winner's unique-index entry, returns no row, then the SELECT sees the committed row (READ COMMITTED).

### Schema (migration `0002_auth_tables`, hand-reviewed)
| Table | Columns / constraints |
|-------|----------------------|
| `users` | `id bigint GENERATED ALWAYS AS IDENTITY` PK; `email text NOT NULL UNIQUE`; `CHECK (email = lower(email))`; `CHECK (length(email) <= 254)`; `created_at timestamptz NOT NULL DEFAULT now()` |
| `accounts` | `id` identity PK; `user_id bigint NOT NULL UNIQUE REFERENCES users` (the UNIQUE index covers FK lookups); `cash numeric(20,8) NOT NULL CHECK (cash >= 0)`; `starting_cash numeric(20,8) NOT NULL CHECK (starting_cash >= 0)`; `created_at` |
| `auth_sessions` | `id` identity PK; `user_id` FK NOT NULL + `ix_auth_sessions_user_id`; `created_at`; `revoked_at timestamptz NULL` |
| `refresh_tokens` | `id` identity PK; `session_id` FK NOT NULL + `ix_refresh_tokens_session_id`; `token_hash text NOT NULL UNIQUE`; `expires_at timestamptz NOT NULL`; `used_at timestamptz NULL`; `created_at` |
Deviation from `.planning/research/ARCHITECTURE.md` (single `refresh_tokens` with `family_id`): a separate `auth_sessions` table gives the JWT a stable `sid` and a single place for family revocation. Autogenerate does not emit CHECK constraints: write them by hand and give each `name=` (naming convention `ck_%(table_name)s_%(constraint_name)s`). Use `sa.Identity(always=True)`. Import `app.models` in `alembic/env.py` so `Base.metadata` is populated. Extend `test_migrations.py` (expects `["0001"]` today) to `["0002"]` and add a drift check (`alembic check` equivalent) so models and migration cannot diverge. Expired token cleanup is out of scope (v2).

### Pattern 9: Frontend
- **No react-router in Phase 2.** The brief asks whether it is needed: it is not. `App` renders: `useMe` pending -> skeleton; `null` -> `SignInPage`; user -> `AccountPage` (email, cash chip `$10,000.00`, Sign out). Phase 1's SKELETON.md said router "arrives in Phase 2", but nothing in this phase needs a URL; add it in Phase 3 with Markets (CLAUDE.md: no speculative code). Flag this as a conscious change to the planner.
- **`apiFetch`** (`src/api/client.ts`), the only place that calls `fetch` for the API: same-origin default credentials; adds `X-CSRF-Token` on non-GET (fetching `/auth/csrf` first if the cookie is missing); on 401 from a non-`/auth/*` request run ONE shared in-flight refresh promise (single-flight), then retry the original request once **regardless of the refresh result** (covers the two-tab grace case); throws `ApiError{status, code, message, retryAfter}`. 429 surfaces `Retry-After` for the UI message.
- **`useMe`**: `queryKey ["me"]`, `queryFn` returns `User | null` (401 -> `null`, not an error), `retry: false`, `staleTime` ~60 s, `refetchOnWindowFocus` default. Mutations (`useRequestCode`, `useVerifyCode`, `useLogout`) via `useMutation`; verify success -> `setQueryData(["me"], user)`; logout success -> `queryClient.clear()` then `["me"] = null`. No hand-rolled `useEffect` fetching.
- **Money**: `/me` returns `cash_usd: "10000.00000000"` (Pydantic Decimal as string). `lib/money.ts` formats with `Intl.NumberFormat("en-US", {style:"currency", currency:"USD"}).format(value as \`${number}\`)`; Intl.NumberFormat accepts decimal strings without a float round trip in current engines `[ASSUMED: ES2023 NumberFormat v3; confirm with a Vitest case on "10000.00000000" and a 20-digit string]`. No JS arithmetic.
- **Sign-in UI** (MASTER.md): two steps in one Card (email, then code). Visible label above each 48px input, errors under the field with `aria-invalid`/`aria-describedby` and `role="alert"`, focus ring untouched, `autoComplete="one-time-code"`, `inputMode="numeric"`, `maxLength=6`. MASTER.md asks for six boxes with paste support: ship ONE input for the MVP (accessible, paste works, no new dependency) and log six-box as polish. Primary pill button, disabled with text reason. Generic copy for wrong/expired code; countdown/message for 429 from `Retry-After`. Keep `HealthPage` mounted below the main content on both views so the existing health e2e and tests keep passing (removing it is a Phase 3 router-time decision).

### Anti-Patterns to Avoid
- Looking up the user in `request-code` (creates the enumeration/timing channel). The account is created on verify.
- `async with db.begin()` after any earlier query on the same `AsyncSession` (autobegin makes it raise "transaction already begun"). `get_current_user` already queried on that session; services must use `await db.commit()` explicitly (or `try/commit/rollback`).
- Comparing the code with `==`, checking attempts non-atomically, or "GET then DEL" for consume.
- Per-tab refresh without single-flight; revoking the family on a use within the grace window.
- Setting cookies via `response.set_cookie` on a `Response` that the route then discards (when returning a new `Response` object, set cookies on that object).
- Logging the raw email + code outside the dev console sender; logging tokens, hashes, or the Resend key.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT signing/verification | custom HMAC token format | PyJWT | alg confusion, claim validation |
| Email format validation | regex | `EmailStr` (email-validator) | RFC edge cases; pydantic-supported |
| Code/token randomness | `random` | `secrets` | CSPRNG |
| Constant-time compare | `==` | `hmac.compare_digest` | timing |
| OTP atomicity | read-modify-write in Python | Redis Lua scripts via `register_script` | races on verify |
| HTTP retries | ad hoc loops everywhere | one small helper in `ResendSender` (3 tries, backoff+jitter) | bounded, testable |
| Currency formatting | string concatenation | `Intl.NumberFormat` | locale/rounding |

## Runtime State Inventory

Not a rename/refactor phase: skipped. (New tables only; nothing renamed.) One carry-over: the dev stack's Redis uses `appendonly yes`, so rate-limit counters persist across restarts; harmless, TTL-bound.

## Common Pitfalls

### Pitfall 1: Console email prints nothing (WR-02)
**What goes wrong:** `logger.info("DEV EMAIL ...")` is invisible: uvicorn only configures `uvicorn.*` loggers; `app.*` falls to the last-resort handler (WARNING+, message only).
**How to avoid:** Add `core/logging.py::configure_logging()` (dictConfig, `disable_existing_loggers=False`, stderr handler, format with timestamp/level/logger name, root INFO) called in `create_app`; make it idempotent. Also fixes the health-service log detail (WR-02) with `%s` args in the message.
**Warning signs:** e2e cannot find the code in `docker compose logs`.

### Pitfall 2: Alembic template fails ruff (WR-04)
`script.py.mako` emits `typing.Sequence/Union` and unsorted imports -> UP035/UP007/I001 on every autogenerated file. Rewrite the template to match `0001_baseline.py` (`from collections.abc import Sequence`, `X | None`, imports sorted, `import sqlalchemy as sa` and `from alembic import op` ordered the way ruff expects) BEFORE autogenerating 0002. Also add `[tool.ruff.lint.isort] known-third-party = ["alembic"]` (IN-01), because the local `backend/alembic/` dir makes ruff treat it as first-party.

### Pitfall 3: Secrets in env files (WR-05)
Add `.env.*` + `!.env.example` to `.gitignore`, and `.env.*` to both `.dockerignore` files, before introducing `JWT_SECRET`, `OTP_HMAC_SECRET`, `RESEND_API_KEY`. The repo is public.

### Pitfall 4: Placeholder secrets and CI
CI e2e does `cp .env.example .env`, so `.env.example` needs working dev placeholders (>= 32 chars) and compose must pass `JWT_SECRET`, `OTP_HMAC_SECRET`, `EMAIL_BACKEND`, `RESEND_API_KEY`, `EMAIL_FROM` into `backend.environment`. A Settings validator must reject placeholder-looking secrets (`change-me`) when `ENV=prod`. `tests/conftest.py` must set the new env vars before `Settings()` is built; update `test_config.py` accordingly. Settings errors must keep `hide_input_in_errors=True` (WR-01 fix already in place); use `SecretStr` for the three secrets and never print them.

### Pitfall 5: Secure cookies not returned in pytest
httpx cookie jar drops Secure cookies on `http://test`. Use `https://test` base URL and assert attributes from `Set-Cookie` headers directly (HttpOnly, Secure, SameSite=Strict, Path, Max-Age). Verify early that the jar works with the non-FQDN host `test`; fallback is to read `Set-Cookie` and pass `cookies=` explicitly.

### Pitfall 6: Refresh cookie never sent
Path must equal the exact proxied path `/api/v1/auth/refresh` in dev and prod. A frontend refresh to another path silently omits it. E2E must cover "reload after access cookie expired".

### Pitfall 7: Two-tab refresh logs the user out
Strict reuse detection revokes the family when tab B races tab A. Use the grace window + single-flight + retry-once described above, and test: two concurrent refreshes with the same cookie -> exactly one 204, the other 401 with family NOT revoked; a replay after the grace -> family revoked and the newest token also dead.

### Pitfall 8: Rate-limit bucket collapse and test bleed
All dev/e2e traffic shares one IP bucket; pytest shares Redis across tests. Provide a fixture that scoped-deletes `sim:rl:*` and `sim:otp:*` with `scan_iter` (never FLUSHALL in app code), use unique emails per test, and keep per-IP defaults high enough for repeated local e2e (>= 20/hour).

### Pitfall 9: Background email and `ASGITransport`
Starlette runs `BackgroundTasks` after the response body is sent; with `httpx.ASGITransport` the task completes before `await client.post` returns (the app call finishes), so tests can read the outbox immediately. Do not rely on this in e2e (real server): poll the logs.

### Pitfall 10: Email case/aliases
Normalize `strip().lower()` BEFORE hashing, rate limiting, storing; the `users` CHECK enforces lowercase. `+alias` farming is accepted for friends (note in docs, not code).

## Code Examples

### Cookie helper
```python
def set_session_cookies(resp: Response, access: str, refresh: str, csrf: str, s: Settings) -> None:
    common = {"secure": True, "samesite": "strict"}
    resp.set_cookie("yk_access", access, max_age=900, path="/api", httponly=True, **common)
    resp.set_cookie("yk_refresh", refresh, max_age=30*86400, path="/api/v1/auth/refresh", httponly=True, **common)
    resp.set_cookie("yk_csrf", csrf, max_age=30*86400, path="/", httponly=False, **common)
```

### CSRF dependency
```python
def verify_csrf(request: Request) -> None:
    cookie, header = request.cookies.get("yk_csrf"), request.headers.get("x-csrf-token")
    if not cookie or not header or not hmac.compare_digest(cookie, header):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail={"code": "csrf", "message": "..."})
CsrfDep = Annotated[None, Depends(verify_csrf)]
```

### Route shape
```python
@router.post("/request-code", status_code=202, response_model=CodeSentOut, summary="Email a sign-in code")
async def request_code(body: RequestCodeIn, bg: BackgroundTasks, redis: RedisDep, sender: EmailSenderDep,
                       ip: ClientIpDep, settings: SettingsDep, _: CsrfDep) -> CodeSentOut:
    code = await auth_service.request_code(redis, settings, body.email, ip)   # raises 429
    bg.add_task(sender.send_code, body.email, code)
    return CodeSentOut(status="code_sent")
```

## State of the Art

| Old | Current | Impact |
|-----|---------|--------|
| python-jose | PyJWT | mandated by CLAUDE.md |
| Resend SDK | REST with httpx | one fewer dependency, native async |
| Redis `EXPIRE` then check | `EXPIRE ... NX` (Redis 7+) | atomic TTL set only once per window |
| localStorage tokens | HttpOnly SameSite=Strict cookies + double-submit CSRF | mandated |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | slopcheck not run; PyJWT, email-validator, respx legitimacy unverified by tool | Package Legitimacy Audit | Slopsquatted install; mitigated by human-verify checkpoint |
| A2 | `resend` SDK is sync/requests-based | Alternatives | Low; we do not use it |
| A3 | uvicorn `--proxy-headers` default on, `--forwarded-allow-ips` default 127.0.0.1 | Pattern 5 | IP buckets wrong; check once in Wave 0 |
| A4 | PyJWT >= 2.10 requires `sub` to be a string | Pattern 6 | Encode/decode errors; trivial to fix |
| A5 | `Intl.NumberFormat.format` accepts decimal strings precisely | Pattern 9 | Display imprecision on huge values; Vitest case proves it |
| A6 | respx 0.23.1 works with httpx 0.28.1 on Python 3.14 | Stack | Tests fail to import; swap `httpx.MockTransport` (no extra dep) |
| A7 | Resend free tier daily/monthly caps (global send cap number) | Rate limiter | Cap too low/high; configurable |
| A8 | Rate-limit numbers (5/10min, 20/h, 10/10min, 30/10min, 500/day) | Pattern 4 | Product choice; user may tune |
| A9 | Domain bought and verified in Resend; `onboarding@resend.dev` only delivers to the account owner (from project research) | Open Questions | SC1 real-email check cannot be completed |

## Open Questions (RESOLVED)

1. **Is the sending domain bought and verified in Resend (SPF/DKIM)?** Pending todo from STATE.md. Without it, the real-delivery half of SC1 can only be tested to the owner's own address. Recommendation: make "send a real code to a non-owner address" a manual `checkpoint:human-verify` at the end of the phase; everything else is automated.
   RESOLVED: D-01. The domain is verified in Resend; the real-email `checkpoint:human-verify` is 02-09 Task 2.
2. **Rate-limit numbers**: proposed defaults above; confirm or let the planner keep them as settings.
   RESOLVED: settings with the RESEARCH defaults (02-CONTEXT.md, Claude's Discretion); implemented in 02-06.
3. **HealthPage placement** after the auth gate (kept below content vs moved): recommended keep-both-views for now.
   RESOLVED: D-03. The health card stays visible on every view (02-05).
4. **Absolute session cap**: refresh expiry is sliding 30 days from last use; an absolute cap (e.g. 90 d) is a one-line change if wanted. Not needed for MVP.
   RESOLVED: not needed for MVP; sessions end at the sliding 30-day refresh expiry (02-04, 02-07).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv, Node 24 | backend/frontend work | yes (linked in /usr/local/bin per memory) | — | — |
| Docker + compose | test stack, e2e, log scraping | assumed yes (Phase 1 ran it) | — | — |
| Postgres 18.6 / Redis 8.8.3 | tests (test stack ports 55432/56379) | via compose | pinned | — |
| Resend account + verified domain | real email (SC1) | unknown | — | console backend; manual check deferred |
| `pip install slopcheck` | package gate | no (denied in this session) | — | human-verify checkpoint |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Backend | pytest 9.1.1 + pytest-asyncio 1.4.1 (session loop), httpx ASGITransport, real Postgres/Redis on the test stack, respx for Resend |
| Frontend | Vitest 5 + React Testing Library, stubbed `fetch` |
| E2E | Playwright 1.64 against the Compose stack |
| Config | `backend/pyproject.toml`, `frontend/vite.config.ts`, `frontend/playwright.config.ts` |
| Quick run | `cd backend && uv run pytest tests/test_auth_*.py -x` ; `cd frontend && npm run test -- src/api src/pages` |
| Full suite | `docker compose -f docker-compose.test.yml up -d --wait && cd backend && uv run pytest --cov=app --cov-fail-under=80` ; `cd frontend && npm run test -- --coverage` ; `npx playwright test` |

### Phase Requirements -> Test Map
| Req | Behavior | Type | Command / file | Exists |
|-----|----------|------|----------------|--------|
| AUTH-01 | Same 202 body for new/existing/never-seen email; no user rows created by request-code; invalid email -> 422 | api | `tests/test_auth_request_code.py` | Wave 0 |
| AUTH-02 | Right code signs in; reuse -> 400; expired (delete key / TTL) -> 400; 5 wrong attempts kill the correct code; new request invalidates old; concurrent double verify -> exactly one 200; compare_digest used | api + unit (100% coverage) | `tests/test_otp_store.py`, `tests/test_auth_verify.py` | Wave 0 |
| AUTH-03 | 6th request per email -> 429 + Retry-After; per-IP via `ASGITransport(client=(ip,..))`; verify limits; window expiry; counters have TTL | api | `tests/test_ratelimit.py` | Wave 0 |
| AUTH-04 | Refresh rotates, old token rejected; reuse after grace revokes family; grace case keeps family; expired token 401; cookie attributes (HttpOnly, Secure, SameSite=Strict, Path, Max-Age); CSRF missing/mismatch -> 403; expired access -> 401; tampered/wrong-alg JWT -> 401; frontend single-flight refresh | api + vitest + e2e | `tests/test_auth_session.py`, `tests/test_csrf.py`, `src/api/client.test.ts` | Wave 0 |
| AUTH-05 | Logout revokes session; old access cookie then 401 at once; refresh after logout 401; cookies cleared | api + e2e | `tests/test_auth_session.py` | Wave 0 |
| AUTH-06 | ResendSender: correct URL/headers/body (respx), retry on 429/5xx, no retry on 4xx, failure logged without code; ConsoleSender logs line; prod refuses console backend; no code/key in logs in resend mode | unit | `tests/test_email.py`, `tests/test_config.py` | Wave 0 |
| ACCT-01 | New user cash == `Decimal("10000.00")` exactly one account; second sign-in unchanged; 10 concurrent `get_or_create_user` -> 1 user, 1 account | api + DB | `tests/test_accounts.py` | Wave 0 |
| ACCT-02 | OpenAPI/route allow-list contains no reset/cash endpoint; DB rejects negative cash (CHECK); `/me` returns string money | api | `tests/test_accounts.py` | Wave 0 |
| Migration | upgrade/downgrade 0002 and no model drift | integration | `tests/test_migrations.py` (update `["0001"]`) | exists, edit |
| UI | sign-in flow, error + 429 messages, auth gate, money format | vitest | `src/pages/SignInPage.test.tsx`, `src/App.test.tsx`, `src/lib/money.test.ts` | Wave 0 |
| E2E | fresh email -> code from `docker compose logs` -> $10,000.00 -> reload still signed in -> sign out -> form shown; sign-in again shows $10,000.00 | e2e | `frontend/e2e/auth.spec.ts` | Wave 0 |
| Manual | Real Resend email from verified domain arrives; code works | manual-only | human checkpoint (needs DNS + inbox) | — |

### Sampling Rate
- Per task commit: quick run for touched area. Per wave merge: full backend + frontend suites. Phase gate: full suite + e2e green, coverage 80% overall and 100% on `services/otp.py`, `services/auth.py`, `core/security.py`, `services/ratelimit.py`, `CurrentUserDep`, CSRF dep (assert behavior, not just execution).

### Wave 0 Gaps
- [ ] Add pyjwt, `pydantic[email]`, respx, promote httpx (after checkpoint)
- [ ] `conftest.py`: set JWT/OTP secrets in env; fixtures `auth_client` (base_url `https://test`), `outbox`, `clean_redis_state`, `make_client(settings_override)`
- [ ] Fix WR-04/WR-02/WR-05 first; update `test_migrations.py` expectations
- [ ] Verify (one smoke test each) that httpx jar returns cookies on `https://test`, and that uvicorn proxy-header defaults are as assumed
- [ ] `frontend/e2e/auth.spec.ts` helper to read the code from compose logs

## Security Domain

### Applicable ASVS Categories
| Category | Applies | Control |
|----------|---------|---------|
| V2 Authentication | yes | Email OTP, HMAC-SHA256 stored, 10 min TTL, 5 attempts, single-use, rate limits |
| V3 Session Management | yes | 15 min HttpOnly JWT + rotating 30 d refresh (hashed in Postgres), reuse detection, server-side revoke |
| V4 Access Control | yes | `CurrentUserDep` on every authed route; 401 vs 403 split (CSRF -> 403) |
| V5 Input Validation | yes | Pydantic `EmailStr`, `^\d{6}$` code pattern |
| V6 Cryptography | yes | `secrets`, HMAC-SHA256, PyJWT HS256, separate secrets; nothing hand-rolled |
| V8/V9 Data protection / comms | partial | Secure cookies; TLS arrives in Phase 6 |

### Known Threat Patterns
| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Account enumeration (body/status/timing) | Info disclosure | No user lookup in request-code; always enqueue; identical 202 |
| OTP brute force (1M space) | Spoofing | 5 attempts atomic, per-email/IP verify limits, HMAC at rest |
| Concurrent code reuse | Tampering | Lua compare-and-delete |
| Refresh token theft/replay | Spoofing/EoP | Rotation, hashed storage, family revoke on reuse |
| CSRF | Tampering | SameSite=Strict + double-submit header on all POSTs |
| Spoofed X-Forwarded-For to dodge limits | Spoofing | Trust only configured proxy via uvicorn; never parse XFF in app |
| Secrets/codes in logs | Info disclosure | Console sender dev-only, prod validator, no code/token logging |
| Email bombing via request-code | DoS | Per-email, per-IP, global caps; bounded retries |
| JWT alg confusion / missing claims | Spoofing | Pinned `algorithms`, required claims, iss/aud |
| Negative or duplicated cash | Tampering | DB CHECK, UNIQUE(user_id), no cash-mutating routes |

## Sources

### Primary (HIGH)
- https://resend.com/docs/api-reference/emails/send-email : endpoint, auth header, Idempotency-Key, body fields
- https://resend.com/docs/api-reference/rate-limit : 10 req/s per team, 429 + retry-after
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie : Secure on localhost, Path semantics, Max-Age=0 deletion
- PyPI via `pip index versions` : pyjwt 2.15.1, respx 0.23.1, email-validator 2.3.0, resend 2.50.0
- Repo files: Phase 1 SKELETON/REVIEW, `backend/app/*`, `tests/conftest.py`, compose files, `.planning/research/{ARCHITECTURE,PITFALLS}.md`, MASTER.md

### Secondary (MEDIUM)
- Project research PITFALLS.md (OTP, cookie/CSRF items) : established engineering practice, not re-verified here

### Tertiary (LOW)
- uvicorn proxy-header defaults, PyJWT `sub` rule, Intl decimal strings, respx/httpx compatibility (see Assumptions)

## Project Constraints (from CLAUDE.md)
- MVP-first, no speculative code; push back on bloat (applied: no router, no SDK, no extra services, one OTP input, no cleanup job).
- Backend: FastAPI factory + lifespan; `Annotated` deps in `core/`; thin routes; services own transactions; uniqueness via constraints + IntegrityError/ON CONFLICT; 401 vs 403 split; PyJWT only; explicit `response_model`, summaries, tags; `/api/v1`.
- Money: `Decimal`/`NUMERIC(20,8)`, strings in JSON, explicit rounding, `timestamptz` UTC.
- DB: identity bigint PKs, `text`, CHECKs, FK indexes, migrations reviewed, schema vs data separate, never `create_all`.
- Redis: keys `sim:<resource>:<id>`, every key has TTL, no KEYS/FLUSHALL in app code, fixed-window `INCR+EXPIRE` pipeline, `redis.asyncio`; Postgres is source of truth.
- Security: OTP HMAC + compare_digest, 5 attempts, per-email/IP limits, no enumeration, email via background job with console backend in dev; cookies HttpOnly/Secure/SameSite=Strict, refresh scoped to its path and hashed in Postgres, CSRF on every state-changing request; no CORS wildcard; never log tokens/PII; no backdoors reachable outside local dev; docs off in prod.
- Tests: 80% overall, 100% on money, login/OTP, authorization; API tests per endpoint; respx for external APIs; real DB/Redis in the test stack; Playwright happy path; CI lint+types+tests (`ruff`, `mypy` strict, eslint, prettier).
- Ask before pushing; git-flow; commit message style.

## Metadata
**Confidence breakdown:**
- Standard stack: MEDIUM (versions verified on PyPI; legitimacy gate not run)
- Architecture/security design: HIGH (CLAUDE.md-driven; atomicity reasoning is standard)
- Pitfalls: HIGH for repo-specific ones (verified against actual files), MEDIUM for httpx cookie-jar and uvicorn defaults (to be proven in Wave 0)

**Research date:** 2026-10-27
**Valid until:** 2026-11-26
