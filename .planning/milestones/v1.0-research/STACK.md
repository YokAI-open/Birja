# Technology Stack

> **Superseded (2026-10-20):** the user chose one simple scheduler-loop container for the price job and FastAPI `BackgroundTasks` for OTP email instead of arq. See PROJECT.md Key Decisions.


**Project:** Birja (crypto paper trading, virtual money, real prices)
**Researched:** 2026-10-20
**Scope:** The core stack is fixed by CLAUDE.md. This file pins current versions, picks the market-data and email providers, picks the scheduler, and fills gaps. Versions were read from PyPI/npm on 2026-10-20 (HIGH confidence).

## Recommended Stack

### Backend core (fixed by CLAUDE.md; versions pinned)
| Technology | Version | Purpose | Why / notes |
|------------|---------|---------|-------------|
| Python | 3.14 | Runtime | Fixed. All hot-path deps ship cp314 wheels (asyncpg 0.32, pydantic-core, uvloop 0.23, httptools 0.9). Use `python:3.14-slim` image. |
| FastAPI | 0.155.0 | API | Current. |
| uvicorn[standard] | 0.54.0 | ASGI server | Current. Pulls uvloop/httptools (cp314 wheels exist). |
| SQLAlchemy[asyncio] | **2.0.55** (pin `>=2.0.55,<2.1`) | ORM | See "SQLAlchemy 2.0 vs 2.1" below. CLAUDE.md says 2.0. Include the `[asyncio]` extra so greenlet is installed. |
| asyncpg | 0.32.0 | Postgres driver | Python 3.14 supported since 0.31. |
| Alembic | 1.20.0 | Migrations | Requires SQLAlchemy>=2.0. Run it with a sync-style `run_sync` async env.py (Alembic's async template). |
| Pydantic | 2.14.1 | Validation | 3.14 support since 2.12. Never go below 2.12 on 3.14. |
| pydantic-settings | 2.16.1 | Settings from `.env` | Requires Python >=3.11. |
| redis (redis-py) | 8.1.0 | Cache, OTP, rate limits | Use `redis.asyncio`. Major 8 is current. |
| httpx | 0.28.1 | Outbound HTTP (prices) | Last release is old but stable. It is the only async client respx supports. |
| PyJWT | 2.15.1 | Access-token JWT | Fixed by CLAUDE.md. |
| orjson | 3.13.0 | `ORJSONResponse` | CLAUDE.md default response class. Check that Decimal is serialized as a string: orjson does not serialize Decimal natively, so serialize via Pydantic (`model_dump(mode="json")`) before orjson sees it. |
| resend | 2.50.0 | OTP email | See "Email" below. Install as `resend[async]` only if calling `send_async` (needs httpx, already present). |
| arq | 0.28.0 | Worker + cron (recommended) | See "Scheduler" below. |

### Backend dev/test
| Library | Version | Notes |
|---------|---------|-------|
| pytest | 9.1.1 | |
| pytest-asyncio | 1.4.0 | Needs pytest >=8.4,<10. Set `asyncio_mode = "auto"` and a session-scoped loop where DB fixtures need it. |
| pytest-cov | 7.1.0 | `--cov-fail-under=80` |
| respx | 0.23.1 | Mock Kraken/CoinGecko/Resend at the httpx boundary. |
| ruff | 0.17.1 | |
| mypy | 2.4.0 | |
| pip-audit | latest | CI, per CLAUDE.md. |

### Frontend
| Technology | Version | Purpose | Notes |
|------------|---------|---------|-------|
| Node.js | **24 LTS ("Krypton", 24.22.0)** | Toolchain | Upgrade from 18.19.1 on this machine (confirmed old). Vite 8 needs ^20.19 or >=22.12, Vitest 5 needs ^22.12 or ^24 or >=26, shadcn needs >=20.18.1, eslint 10 needs ^20.19/^22.13/>=24. Node 24 satisfies all. Pin with `.nvmrc` and `engines`, and use `node:24-slim` in Docker/CI. |
| React | 19.3.1 | UI | |
| Vite | 8.3.4 | Build | Vite 8 is Rolldown-based. |
| @vitejs/plugin-react | 6.1.2 | | Peer: vite ^8. |
| TypeScript | **~6.0.3** (NOT 7.x) | Types | `latest` on npm is 7.0.2, but typescript-eslint 8.72 declares `typescript >=4.8.4 <6.1.0`. Pin `typescript@~6.0.3` until typescript-eslint supports 7. Lint failing in CI is the cost of ignoring this. |
| @tanstack/react-query | 5.104.5 | Server state | Fixed by CLAUDE.md. |
| tailwindcss + @tailwindcss/vite | 4.3.3 | Styling | v4 uses CSS-first config (`@import "tailwindcss"`) and the Vite plugin. No `tailwind.config.js`, no PostCSS. |
| shadcn (CLI) | 4.22.1 | Component source | `npx shadcn@latest init`, Tailwind v4 mode. Requires Node >=20.18.1 (the reason for the upgrade). |
| react-router-dom | 7.18.4 | Routing | Needed gap-fill: login, markets, trade, portfolio, history pages. Use library (SPA) mode. |
| Vitest | 5.0.5 (+ `@vitest/coverage-v8` 5.0.5, jsdom) | Unit tests | |
| @testing-library/react | 16.3.3 | | |
| @playwright/test | 1.64.1 | e2e | |
| ESLint | 10.13.0 + typescript-eslint 8.72.0 + eslint-plugin-react-hooks 7.1.1 | Lint | All three are compatible with each other (peer ranges verified). Flat config only. |
| Prettier | 3.9.10 | | |
| decimal.js (or big.js) | latest | Display math on money strings | Needed only if the UI computes anything (e.g. estimated quantity for a dollar amount). Never use JS `number` on money. Prefer showing server-computed quotes. |

### Data / infra
| Technology | Version | Purpose | Notes |
|------------|---------|---------|-------|
| PostgreSQL | 18 (`postgres:18-bookworm` or `-trixie`) | Source of truth | Pin the minor tag in Compose. |
| Redis | 8.8 (`redis:8.8-trixie`) | Cache, OTP, rate limits, arq queue | `maxmemory-policy noeviction`, `requirepass`, TTL on every key (CLAUDE.md). |
| Docker Compose | v2 | Orchestration | One container per service with `healthcheck:`. |
| nginx | stable image, pinned | Reverse proxy, TLS, static files | Added in the deploy phase only. |
| certbot | official `certbot/certbot` image | TLS certificates | See "Deployment". |

## 1. Market data: recommendation

**Primary: Kraken public REST `Ticker` (no key). Fallback: CoinGecko Demo API (free key, strict monthly budget).**

### Why not CoinGecko as primary (the key finding)
CoinGecko Demo is **100 calls/min but only 10,000 calls/month** (official pricing page, checked 2026-10-20). Polling every 60s is 1,440 calls/day, about 43,200/month, so it would run out in about 7 days. Even one batched `/simple/price` call (up to 515 ids per call) cannot sustain a 60s cadence on Demo. Demo also requires attribution. A third-party guide claiming 30 rpm is outdated or wrong. Official docs say 100 rpm. CoinGecko remains the best fallback because it covers every coin by id and returns `last_updated_at`.

### Comparison
| Source | Key | Limits | USD price | Fit |
|--------|-----|--------|-----------|-----|
| **Kraken** `GET https://api.kraken.com/0/public/Ticker?pair=XBTUSD,ETHUSD,...` | None | Public limits not retrievable from docs. One call per minute for all pairs is far below any known public throttle. | True USD pairs. Returns last trade `c`, bid `b`, ask `a`. | Best primary. Verified live from this host: HTTP 200, multiple pairs in one call. |
| CoinGecko Demo `GET https://api.coingecko.com/api/v3/simple/price?ids=...&vs_currencies=usd&include_last_updated_at=true` + header `x-cg-demo-api-key` | Free key (keyless public tier exists but is IP-shared and unreliable) | 100/min, **10k/month** | USD aggregate across exchanges | Fallback only. Use at most about 5-min cadence, with a Redis counter guard on monthly calls. Show attribution. Keyless request returned 200 here. |
| Binance `https://data-api.binance.vision/api/v3/ticker/price` | None | Not retrieved | **USDT**, not USD | Optional second fallback. `api.binance.com` blocks US-located IPs (reports from 2022 on). `data-api.binance.vision` returned 200 from this host, but its region behavior and ToS for display are unverified. Quote is USDT (about $1, not exactly). |
| CryptoCompare / CoinCap | Not researched in depth. CoinCap search gave no result. | | | Skip. A third option adds code for no v1 gain. |

### Implementation notes
- **Kraken response keys are not the request pair names** (request `XBTUSD`, response key `XXBTZUSD`; BTC is `XBT`, some ETH-family pairs use the `X...Z...` form). Keep a static config map `coin symbol -> kraken request pair -> response key`, and verify it with a recorded-fixture test (respx). The docs mention an `assetVersion=1` parameter that switches keys to display names like `BTC/USD`. Verify live before relying on it (MEDIUM).
- **Kraken gives no per-price timestamp.** The "as of" time is the fetch time (`fetched_at`). That is acceptable given the max-age rule, but record it explicitly. CoinGecko supplies `last_updated_at`, so use the older of the two when falling back.
- Use **mid = (bid+ask)/2** from Kraken as the "market price" (real bid/ask exists, which makes the simulated spread an overlay), or `c` (last trade). Pick one and record which. The simulated spread then applies to mid.
- Parse all numbers with `Decimal(str)` from the raw JSON strings, never via float. Kraken returns strings. CoinGecko returns JSON numbers, so use `json.loads(..., parse_float=Decimal)` or `response.json(parse_float=Decimal)`.
- Curated list must be restricted to coins with a USD pair on Kraken (BTC, ETH, SOL, XRP, ADA, DOGE, LTC, LINK, DOT, AVAX, etc.; confirm each pair live when freezing the list). Anything not on Kraken falls to CoinGecko ids.
- Retries: exponential backoff with jitter, max 3, inside the job. If both sources fail, keep the old price (its age grows) so the max-age rule refuses trades. Never fabricate.
- Confidence: Kraken endpoint shape HIGH (live-verified), Kraken rate limit MEDIUM/unknown, CoinGecko limits HIGH (official pricing page), Binance restrictions LOW.

## 2. Email: Resend

- **SDK**: `resend` 2.50.0 (released 2026-10-16, Python 3.14 classifier present). Call `resend.Emails.send(params, {"idempotency_key": "otp/<email-hash>/<nonce>"})`. Async variant `await resend.Emails.send_async(...)` uses httpx. Errors raise `ResendError` subclasses, so wrap them.
- **Free plan** (official pricing page): **100 emails/day, 3,000/month, 3 custom domains.** At tens of users, OTP traffic fits. The 100/day cap is a real limit for OTP bursts plus brute-force attempts, so the per-email and per-IP code-request rate limits in CLAUDE.md double as quota protection.
- **Domain verification is required for production**: verify the sending domain at resend.com/domains (add the DNS records Resend lists, normally SPF and DKIM) and send from an address on that domain. `onboarding@resend.dev` is test-only and must not be used in production (it only delivers to your own account address). The domain must therefore be bought and DNS-controlled before the deploy phase can finish. Start verification early because DNS propagation can take hours.
- **Dev**: a console/log email backend selected by `EMAIL_BACKEND` setting (CLAUDE.md). In tests, mock `api.resend.com` with respx. Resend test recipients: `delivered@resend.dev`, `bounced@resend.dev`.
- Never log the code or the API key. Send from the worker job, not from the request.
- Confidence: HIGH on SDK and limits (official pages), MEDIUM on exact DNS record set (not on the fetched page).

## 3. Scheduler: recommendation

**Recommend arq 0.28.0 (one `worker` container running both cron and queued jobs). Fallback: Celery 5.6.3 + beat.**

Needs: one periodic price job (every 60s) and one queued job (send OTP email with retries).

| Option | Containers | Fit for this app | Verdict |
|--------|-----------|------------------|---------|
| **arq** (asyncio-native, Redis) | 1 (`arq app.tasks.WorkerSettings`) | Cron and queue in one process. Reuses the async SQLAlchemy engine, httpx and `redis.asyncio` already in the app. No sync engine needed. Cron jobs are deduplicated by (job id + scheduled time) across workers. Retries via `Retry`/`max_tries`. 0.28.0 (2026-04-16) lists Python 3.14. | **Pick.** Simplest correct. |
| Celery + beat | 2 (worker, beat) | CLAUDE.md's stated MVP option. Requires a second (sync) DB engine in `app/db/` because workers have no event loop, a separate beat container, and prefork/solo pool setup. Celery 5.6.3 has no 3.14 classifier (works in practice per reports but not declared). Overkill for 2 jobs. | Fallback if arq is rejected or abandoned. |
| APScheduler 3.11.3 `AsyncIOScheduler` | 1 | Handles the periodic job, but has no queue/retries for email. Email would need `BackgroundTasks` (lost on crash, violates "background job" rule) or a second system. 4.0 is still alpha, so do not use it. | Rejected. |
| FastAPI `BackgroundTasks` / in-process loop | 0 | Runs once per web worker and is lost on restart. Violates CLAUDE.md. | Rejected for the price job. |

**Deviation flag:** CLAUDE.md names "Celery + beat, or a single scheduler process". arq is a single worker process with a scheduler, which matches the second option's intent, but it is a new named dependency. Risk: arq is in maintenance mode (low release cadence). It is small enough (about 1 file of integration) to swap for Celery later. Needs the user's quick confirmation in roadmap discussion.

Rules regardless of choice (from CLAUDE.md): the job must be idempotent (upsert price row keyed by symbol, with `fetched_at`), run in exactly one dedicated container, and take a Redis lock `SET NX PX` if overlap is possible. Write the price to Postgres (source of truth) and refresh the Redis cache (`sim:price:BTC-USD`, TTL slightly above 2x cadence).

Confidence: MEDIUM (reasoned from docs and metadata, not benchmarked).

## 4. Version and compatibility notes

- **SQLAlchemy 2.0 vs 2.1:** 2.1.5 is the current stable release (2026-10-16). Differences matter: greenlet is no longer installed by default (needs `[asyncio]`), Python >=3.11, the default PG driver becomes psycopg (always give the explicit `postgresql+asyncpg://` URL), autoflush now runs on every execution including Core/`text()`, `Row` typing changed (mypy impact). CLAUDE.md says 2.0, Alembic 1.20 only declares `SQLAlchemy>=2.0`, and 2.0.55 is a maintained series. **Stay on 2.0.55 for v1**, and upgrade to 2.1 as a deliberate chore later. (HIGH on facts, MEDIUM on "no Alembic problems with 2.1".)
- **Pydantic:** >=2.12 required for Python 3.14. Fine at 2.14.1.
- **asyncpg:** >=0.31 for 3.14. Fine at 0.32.0.
- **uvloop/httptools:** cp314 wheels present (0.23.0 / 0.9.0), so `uvicorn[standard]` installs without a compiler.
- **psycopg:** not needed. Alembic runs through the asyncpg async env.
- **Celery:** no declared 3.14 support (only if the fallback is used).
- **typescript-eslint vs TypeScript 7:** incompatible today (see Frontend table). TypeScript 7 is a native-compiler rewrite and `latest` on npm, so a naive `npm i typescript` will break lint. Pin it.
- **Vitest 5** requires `@types/node` ^22 or >=24 and Vite ^6.4/7/8. Fine with Vite 8.
- **Project memory:** shadcn setup is deferred to the first frontend phase and needs the Node upgrade (18.19.1 is installed now, confirmed).
- **uv:** use `uv python install 3.14` and `uv sync --frozen` in Docker. Pin `requires-python = ">=3.14,<3.15"`.

## 5. Small-VPS deployment (v1)

**Keep nginx (CLAUDE.md) with certbot in a container. Do not switch to Caddy.** Caddy would be less work (automatic ACME, no renewal hooks), and is the honest simplest-option alternative; mention it to the user but the project instruction names nginx and nothing in the research argues against it hard enough to override.

Recommended shape, one `docker-compose.prod.yml` on a 1-2 vCPU / 2 GB VPS (any provider, Ubuntu LTS):
- Services: `nginx` (80/443 published), `backend` (uvicorn, `--workers 2`), `worker` (arq), `postgres`, `redis`, and `frontend` built to static files (multi-stage Node build, copied into the nginx image or a shared volume; no running Node container in prod).
- Networks: `edge` (nginx + backend) and `internal` (backend, worker, postgres, redis). Postgres/Redis publish no ports.
- TLS: certbot with the **webroot** challenge. nginx serves `/.well-known/acme-challenge/` from a shared volume on port 80, certbot container runs `certbot renew` on a loop (`sleep 12h`), and a cron or sidecar reloads nginx (`nginx -s reload`). Bootstrap the first cert with a temporary HTTP-only nginx config (the classic chicken-and-egg), scripted once.
- nginx config per CLAUDE.md: TLS 1.2/1.3, HTTP to HTTPS redirect, HSTS/CSP/X-Frame-Options/X-Content-Type-Options/Referrer-Policy, `server_tokens off`, gzip, `limit_req` stricter on `/api/v1/auth/*`, long immutable cache on Vite hashed assets, `/api` proxied to backend, `/docs` and OpenAPI disabled in prod (gate by `settings.ENV`).
- Non-root containers, pinned image tags, `healthcheck:` everywhere, secrets in an untracked `.env` on the server.
- DNS: A record to the VPS and the Resend DNS records on the same domain.
- Backups: a nightly `pg_dump` cron to somewhere off the VPS is a v1.x item (flag in roadmap; "mistakes stay" and no reset means data loss is unrecoverable).
- CI: GitHub Actions with Postgres and Redis service containers or the compose test stack, matrix of one Python (3.14) and one Node (24).

Confidence: HIGH on pattern (standard), MEDIUM on certbot bootstrap details (not re-verified against current docs).

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Primary prices | Kraken public | CoinGecko Demo | 10k calls/month cap cannot sustain 60s polling |
| Primary prices | Kraken public | Binance public | Quotes USDT, US-IP block on main host, unclear ToS |
| Fallback prices | CoinGecko Demo (budgeted) | CoinCap/CryptoCompare | Not verified, adds a third integration with no v1 value |
| Scheduler | arq | Celery + beat | 2 containers + sync engine for 2 jobs (kept as fallback) |
| Scheduler | arq | APScheduler | No queue/retry for email |
| ORM | SQLAlchemy 2.0.55 | 2.1.5 | Behavior changes (greenlet extra, autoflush), nothing needed for v1 |
| TypeScript | 6.0.3 | 7.0.2 | typescript-eslint peer range `<6.1.0` |
| TLS | nginx + certbot | Caddy | CLAUDE.md names nginx. Caddy is simpler, so reconsider only if the certbot setup becomes painful |
| JWT | PyJWT | python-jose | Unmaintained (CLAUDE.md) |

## Installation

```bash
# Backend (from backend/, via uv; never pip)
uv python install 3.14
uv add "fastapi==0.155.0" "uvicorn[standard]==0.54.0" "sqlalchemy[asyncio]>=2.0.55,<2.1" \
  "asyncpg==0.32.0" "alembic==1.20.0" "pydantic==2.14.1" "pydantic-settings==2.16.1" \
  "redis==8.1.0" "httpx==0.28.1" "PyJWT==2.15.1" "orjson==3.13.0" "resend==2.50.0" "arq==0.28.0"
uv add --dev "pytest==9.1.1" "pytest-asyncio==1.4.0" "pytest-cov==7.1.0" "respx==0.23.1" \
  "ruff==0.17.1" "mypy==2.4.0" pip-audit

# Frontend (from frontend/, Node 24 LTS first)
npm create vite@latest . -- --template react-ts      # then pin versions below
npm i react@19.3.1 react-dom@19.3.1 @tanstack/react-query@5.104.5 react-router-dom@7.18.4 \
  tailwindcss@4.3.3 @tailwindcss/vite@4.3.3
npm i -D vite@8.3.4 @vitejs/plugin-react@6.1.2 typescript@~6.0.3 \
  vitest@5.0.5 @vitest/coverage-v8@5.0.5 jsdom @testing-library/react@16.3.3 \
  @playwright/test@1.64.1 eslint@10.13.0 typescript-eslint@8.72.0 \
  eslint-plugin-react-hooks@7.1.1 prettier@3.9.10
npx shadcn@latest init
```

## Sources

- PyPI JSON API and npm registry, queried 2026-10-20 (all version numbers and peer ranges): HIGH
- https://docs.coingecko.com/docs/common-errors-rate-limit (Demo 100/min, key header, keyless is IP-shared): HIGH
- https://www.coingecko.com/en/api/pricing (Demo 10k credits/month, attribution required): HIGH
- https://docs.coingecko.com/reference/simple-price (params, 515 ids, `include_last_updated_at`): HIGH
- https://docs.kraken.com/api/docs/rest-api/get-ticker-information (Ticker fields) plus live call from this host: HIGH. Public rate limits: not found
- https://developers.binance.com/docs/binance-spot-api-docs/faqs/market_data_only (data-api.binance.vision, no key): HIGH. US restriction on api.binance.com: LOW (third-party reports)
- https://resend.com/pricing (100/day, 3,000/month, 3 domains): HIGH
- https://resend.com/docs/send-with-python (SDK, async, idempotency, domain verification): HIGH
- https://docs.sqlalchemy.org/en/21/changelog/migration_21.html (2.1 changes; only first 100k chars read): MEDIUM
- https://nodejs.org/dist/index.json (Node 24 is LTS "Krypton"): HIGH
- Caddy vs nginx comparison blogs (directional only): LOW

## Gaps for later phases
- Kraken public rate limit and exact pair/response-key mapping for the final coin list: verify live when freezing the list (market-data phase).
- CoinGecko attribution wording and placement: read the attribution guide before shipping the UI that shows fallback prices.
- Binance as a second fallback: only worth it if both Kraken and CoinGecko prove unreliable.
- certbot bootstrap script and nginx config: verify against current certbot docs in the deploy phase.
- arq under Python 3.14 in practice: smoke-test early in the job phase, and keep the Celery fallback.
