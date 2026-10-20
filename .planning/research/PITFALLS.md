# Pitfalls Research

**Domain:** Crypto paper-trading web app (virtual USD, real prices, market orders with simulated spread + fee, email OTP, small VPS)
**Researched:** 2026-10-20
**Confidence:** MEDIUM. Money, concurrency, OTP, cookie and deploy items are well-established engineering knowledge (HIGH). Free-API limits are volatile (MEDIUM/LOW, verify at implementation). The Python 3.14 wheel check was done against PyPI (HIGH for the packages listed).

Phase names below are suggestions. Map them to the real roadmap: (A) Foundation/Compose/CI, (B) Auth/OTP, (C) Prices ingestion, (D) Trading engine + ledger, (E) Portfolio/P&L + frontend, (F) Deploy.

---

## Critical Pitfalls

### Pitfall 1: Free price API quota is smaller than a 60-second poll implies

**What goes wrong:**
CoinGecko's free Demo plan is reported at about 10,000 calls/month (per-minute limit reported as 30 or about 100; sources conflict). One call per minute is about 43,200 calls/month, so the poller silently hits 429s mid-month and prices go stale for days. Calling per coin (15 coins x 1/min) is far worse.

**Why it happens:**
People check the per-minute limit and forget the monthly cap. Per-coin endpoints are the first thing in tutorials.

**How to avoid:**
- Use ONE batched call for all coins (CoinGecko `/simple/price?ids=a,b,c`, or Binance/Kraken/Coinbase public ticker endpoints, which have no monthly cap and generous per-minute limits). Pick the source by computing calls/month = (60*24*30)/interval before choosing.
- Put the provider behind a small interface so a fallback source can be added. A second provider for v1 is optional, but the seam is cheap.
- Honour `429`/`Retry-After`; exponential backoff with jitter and a max retry (per CLAUDE.md); never retry in a tight loop.
- Log remaining quota if the provider returns it.

**Warning signs:**
429s in logs; "as of" timestamps drifting; the poll interval was chosen without a calls/month figure in the docs.

**Phase to address:** C (Prices ingestion). Needs a short research spike on the chosen provider's CURRENT limits and terms (attribution, key requirement) before coding.

---

### Pitfall 2: Executing a trade on a stale, missing or garbage price

**What goes wrong:**
(a) Trade executes with a price hours old because the poller died, (b) price is `0`/`null`/negative/NaN from a bad API response and a buy gives "infinite" quantity or a division by zero, (c) a one-tick spike (e.g. 100x) lets a user buy or sell at a fantasy price, (d) the trade uses a price different from what the user saw and confirmed.

**Why it happens:**
Staleness is only checked in the UI; the price is re-read inside the trade without a timestamp; no sanity validation on ingest.

**How to avoid:**
- Persist `price`, `as_of` (timestamptz) per symbol in Postgres (source of truth); Redis is cache-aside only. Trade service reads price+as_of, and refuses with a clear error if `now - as_of > MAX_PRICE_AGE` (config, e.g. 3x poll interval). Cold Redis must fall back to Postgres, not fail.
- Ingest validation before overwriting the stored price: `Decimal` parse from the raw string/number (parse JSON with `parse_float=Decimal` or request strings; never go through `float` then Decimal), reject `<= 0`, non-finite, and moves beyond a threshold vs previous price (e.g. >30-50% in one interval) unless confirmed by a second reading. Keep last good price and its older `as_of` so staleness logic naturally protects users.
- Quote/confirm flow: the confirm screen shows spread, fee and price `as_of`. Execution either (1) re-prices server-side and rejects if the price changed beyond a tolerance from the quoted one (return 409 with the new quote), or (2) accepts a signed/short-lived quote id. Pick one, document it; never silently execute at a different price.
- Record price used, as_of, spread and fee on every trade row (already in PROJECT.md).
- Poller must not overwrite `as_of` when the fetch failed.

**Warning signs:**
Prices with identical `as_of` for hours; trades table with `price = 0`; users report "filled at a different price than shown"; any `float(` in price code.

**Phase to address:** C (ingest validation), D (staleness gate + quote semantics). Tests: 100% on the gate.

---

### Pitfall 3: Double-spend / lost-update races on concurrent trades

**What goes wrong:**
Two simultaneous buys both read cash = 10,000, both succeed; or two sells of the same holding oversell. Also: double-click or retried request creates two trades. Also deadlocks when locking rows in inconsistent order.

**Why it happens:**
Read-then-write in Python, no row locks, or locks taken on the wrong row (e.g. lock the holding but not the cash row). SQLAlchemy async session: `expire_on_commit` and autoflush surprises hide stale reads. Holdings row may not exist yet for a first buy, so `FOR UPDATE` locks nothing.

**How to avoid:**
- One transaction: `SELECT ... FOR UPDATE` on the user's account/cash row FIRST (serialises all of that user's trades; simplest correct design for per-user balances), then the holding row (upsert via `INSERT ... ON CONFLICT (user_id, asset) DO UPDATE` or lock-by-account-row makes this safe), then insert the trade.
- Schema backstops: `CHECK (cash >= 0)`, `CHECK (quantity >= 0)`, `UNIQUE (user_id, asset)` on holdings. A violation must roll back and map to a domain error (insufficient funds), never a 500.
- Idempotency key per order (client-generated UUID, `UNIQUE (user_id, idempotency_key)` on trades); on conflict return the original result. Disable the confirm button while pending (UX only, not protection).
- Always acquire locks in the same order. Keep the transaction short: fetch the price BEFORE opening the lock, not inside it over HTTP.
- Test with real concurrency against the real Postgres test stack: `asyncio.gather` of N parallel buys that together exceed cash; assert exactly the affordable number succeed and cash never goes negative. Do not mock the DB.

**Warning signs:**
No `with_for_update()` in the trade service; trade tests are all sequential; cash can show tiny negative values.

**Phase to address:** D (Trading engine). Concurrency test is a phase exit criterion.

---

### Pitfall 4: Decimal/rounding errors in fees, spread, quantity and "sell all" dust

**What goes wrong:**
- `float` sneaks in (JSON numbers, `Decimal(0.1)`, pandas, API client libs).
- Cash and quantity use the same precision (NUMERIC(20,8)), but USD should be settled in cents while quantity is in the asset's precision; mixing leaves sub-cent cash drift or `cash 9999.999999`.
- Rounding intermediate values (price after spread, then notional, then fee, each rounded) so totals do not reconcile; buy of `$100` yields cash debit of `$100.00000001`.
- "Buy by dollar amount": quantity = amount / price is non-terminating; rounding quantity UP lets the user spend more than they have, rounding to nearest breaks `cash >= 0`.
- "Sell all" leaves residue like `0.00000001` because the UI sends a rounded displayed quantity, or the sell quantity is computed from a float percentage. Dust holdings then clutter the portfolio and can fail minimum checks.
- Decimal context default precision is 28 digits; fine, but `quantize` raises `InvalidOperation` if the result exceeds context precision (huge values), and the default context is thread/task-local state that someone may alter.
- Python's `round()` on Decimal, or f-string formatting for storage.

**Why it happens:**
No single place defines "who rounds what, when". CLAUDE.md says "round explicitly at defined points" but the points have not been defined for this app.

**How to avoid:**
Define and document ONE pricing function (pure, no I/O, 100% tested incl. property tests with Hypothesis):
1. `exec_price = mid * (1 +/- spread)`; keep full precision, round only to price precision (8 dp) with ROUND_HALF_EVEN.
2. Buy by quantity: `qty` quantized to asset precision (8 dp; DOWN is not needed, user gave it); `notional = quantize(qty * exec_price, 0.01)`; `fee = quantize(notional * fee_rate, 0.01)`; `cash_debit = notional + fee`. Cash is always whole cents. Store cents-rounded cash in NUMERIC(20,8) column but the invariant is "cash has at most 2 dp" (add a CHECK if desired).
3. Buy by dollars: treat the dollar amount as the total debit D (fee included, or excluded, pick one and show it). `qty = quantize((D/(1+fee_rate)) / exec_price, 1e-8, ROUND_DOWN)`, then recompute notional/fee from qty via step 2 and assert `debit <= D`. ROUND_DOWN here is deliberate (document it as the one exception to HALF_EVEN, because rounding up can overspend).
4. Sell by quantity: proceeds = notional - fee, cents-rounded; sell-all sends an explicit `sell_all: true` flag (or the server reads the exact stored quantity under the lock) so no displayed-and-rounded value is round-tripped. Reject sells with `qty > held` using Decimal compare under the lock.
5. After a sell, if remaining qty < asset's minimum unit (dust threshold, e.g. < 1e-8 is impossible at 8dp, but set a per-asset minimum if you want), either block partial sells that leave dust or auto-close. Choose and test.
6. Serialize all money as strings in JSON; frontend never does arithmetic with JS numbers for money (use string display or `decimal.js`/`big.js` only for previews, server is authoritative for the confirm quote).
7. Per-asset precision: store `qty_decimals` per asset config (BTC 8, but SHIB-like coins need a different scale; NUMERIC(20,8) can hold 8dp only, so exclude ultra-low-priced coins from the curated list or accept that quantity of e.g. 1,000,000 units at 8 dp is fine).
8. Reconciliation test: `10000 = cash + sum(open lots cost) + sum(realized loss) + total fees paid + total spread cost` style invariant over random trade sequences.

**Warning signs:**
`float` or `round(` in diff; Decimal built from float; displayed cash differs from sum of trades by cents; sell-all button leaves `0.00000001`; Hypothesis not in test deps.

**Phase to address:** D (pure pricing/ledger module first, before endpoints), verified again in E.

---

### Pitfall 5: Average-cost math wrong on partial sells and re-buys

**What goes wrong:**
Average cost is recomputed on sells (it must NOT change on a sell), or it is stored as a rounded per-unit price that drifts after many trades; selling everything then re-buying inherits the old average; realized vs unrealized P/L are mixed; fees are dropped from cost basis (or double-counted); total P/L vs $10k does not equal the sum of per-holding P/L plus realized P/L.

**Why it happens:**
Storing `avg_price` and mutating it incrementally with rounding at every step.

**How to avoid:**
- Store `total_cost` (cost basis in USD, including buy fee) and `quantity` per holding, derive `avg_cost = total_cost / quantity` at read time (division only for display, 8 dp HALF_EVEN).
- Buy: `qty += q; total_cost += debit` (debit including fee, decide once whether fees are in basis; recommended yes).
- Sell: `cost_removed = total_cost * (sold_qty / qty)` computed BEFORE reducing, quantized to cents (use the final-sell case `sold_qty == qty` to remove ALL remaining cost exactly, so no residual cost with zero quantity); `realized_pnl = proceeds - cost_removed`; `qty -= sold_qty`; `total_cost -= cost_removed`. When qty hits 0, total_cost MUST be exactly 0 (CHECK constraint: `quantity = 0 -> total_cost = 0`).
- Persist `realized_pnl` on each sell trade row so history and total P/L are reproducible without replaying.
- Headline total P/L = `(cash + sum(qty * mark_price)) - 10000`. Mark-to-market at mid price (not sell price) is simplest, but say which in the UI; showing spread-adjusted liquidation value is arguably more honest, pick one.
- Golden tests: hand-computed scenarios (buy 1 @100, buy 1 @200, sell 1 @300 -> avg stays 150, realized 150 minus fees; sell rest; re-buy) plus the invariant from Pitfall 4.

**Warning signs:**
Average cost changes after a sell; cost basis nonzero at zero quantity; portfolio P/L total does not match components by a cent.

**Phase to address:** D (ledger), E (display).

---

### Pitfall 6: Scheduler (price poller) running in every web worker

**What goes wrong:**
APScheduler/`asyncio.create_task` loop started in FastAPI `lifespan` runs once per uvicorn worker (and again on `--reload`), multiplying API calls, exhausting the quota (Pitfall 1) and racing on writes.

**Why it happens:**
It is the easiest place to put it, and it works in single-process dev.

**How to avoid:**
- Dedicated `scheduler`/`worker` Compose service (Celery beat + worker, or a single small loop process), web containers contain no scheduling code. A leader lock (`SET NX PX` with token per CLAUDE.md) as a belt-and-braces guard if the poller ever shares a process. Task must be idempotent and tolerate being skipped.
- Celery in MVP: ask whether a plain single-process async loop container is enough for ONE periodic job (CLAUDE.md allows it). Celery adds a worker, beat, sync DB engine and broker; adopt only when OTP email sending also moves to a queue.
- Celery beat: exactly one beat instance; a stale beat schedule file/volume is not shared; never `--scale` the beat service.
- If the poller is a Celery task: sync engine needed (no event loop), `psycopg`/`psycopg2` or `asyncio.run` inside the task; do not reuse the async engine across event loops.

**Warning signs:**
Provider call count = N x expected; duplicate log lines per minute; `docker compose up --scale backend=2` doubles polling.

**Phase to address:** C.

---

### Pitfall 7: OTP login flaws (enumeration, brute force, replay, logging)

**What goes wrong:**
- Response/timing differs for known vs unknown email (enumeration), including 429 only for existing accounts, or Resend being called only for existing users making response time differ.
- Brute force: 6 digits = 1,000,000; per-IP limits alone are bypassed by many IPs; per-email limits alone allow lock-out DoS of a victim.
- Attempt counter not atomic (GET then SET) so parallel guesses exceed 5; counter resets when a new code is requested (attacker requests new code to reset attempts: bound total requests per email per hour).
- Code compared with `==`; raw code logged (the console email backend in dev logs it; make sure it is disabled in prod by `ENV`); code stored as plain hash.
- Code not single-use (race: two verifies simultaneously both succeed; use atomic `GETDEL`/Lua).
- Email normalisation: `A@x.com` vs `a@x.com` create two accounts or two rate-limit buckets. Normalise (strip, lowercase) BEFORE hashing/limiting. Also `+` aliases are a free account-farming path (acceptable for friends; note it).
- Behind nginx, `request.client.host` is the proxy IP, so all users share one IP bucket (or attacker spoofs `X-Forwarded-For`). Trust only the proxy's header (uvicorn `--proxy-headers --forwarded-allow-ips` set to the nginx container, or nginx `real_ip`).
- Sending synchronously inside the request makes timing reveal account existence and ties request latency to Resend.

**How to avoid:**
Follow CLAUDE.md Security exactly, plus: Lua/`INCR`-based atomic attempt counter; `GETDEL` or Lua compare-and-delete for consume; per-email AND per-IP AND global caps on code sends; identical response body/status/latency path for all emails (always enqueue, user creation happens on successful verify, not on request); constant dummy work; HMAC secret from `.env` and distinct from JWT secret; test each rule (login is a 100% coverage path).

**Warning signs:**
Different JSON for unknown emails; all rate-limit keys use the proxy IP; code visible in production logs; verify endpoint has no per-email limit.

**Phase to address:** B (Auth). Re-check IP handling in F once nginx is in front.

---

### Pitfall 8: Resend deliverability (SPF/DKIM/DMARC, sandbox sender) makes login impossible

**What goes wrong:**
Codes land in spam or never arrive, so friends cannot sign in, which blocks the whole "v1 done" definition. Common causes: sending from `onboarding@resend.dev` (Resend's test sender only delivers to the account owner's own address, so it works for the author and silently fails for friends); domain not verified; missing SPF/DKIM DNS records (Resend gives them on domain verification); no DMARC record; free-tier daily/monthly sending caps (check current numbers) hit by retries or abuse; a rate limit on sends does not exist so a bot burns the quota.

**How to avoid:**
- Verify a sending domain (preferably a subdomain like `mail.<domain>`) in Resend EARLY; add SPF, DKIM (and a DMARC `p=none` record to start) in DNS; check the Resend dashboard shows "Verified"; send a test to Gmail/Outlook/iCloud and read headers for `spf=pass dkim=pass dmarc=pass`.
- Plain-text-friendly short email, subject with no spammy words, code in body; set `Reply-To`; `From` on the verified domain.
- Handle Resend errors: do not tell the user "sent" while swallowing a 4xx; log provider error id (not the code); retry with backoff via the background job; surface a generic "try again" only after repeated failure.
- Global + per-email send caps below the provider's free quota; alert (or at least a log line) at 80% usage.
- DNS propagation can take hours: start this before the deploy phase, not on deploy day.

**Warning signs:**
Only the author receives codes; `resend.dev` sender in config; no DMARC record; emails in spam folder.

**Phase to address:** B for code (console backend in dev + Resend adapter), F for DNS/domain verification. Put "domain purchased + Resend domain verified" as an early external-dependency task, since it has wall-clock latency.

---

### Pitfall 9: Cookie/CSRF auth that works in Vite dev but breaks (or is insecure) in prod

**What goes wrong:**
- Dev: frontend at `localhost:5173`, API at `localhost:8000` are different origins; `SameSite=Strict` + `Secure` cookies are dropped (Secure cookies over plain http are accepted on `localhost` by Chrome/Firefox but not on other hostnames or Safari), CORS requires `allow_credentials` with explicit origin, fetch needs `credentials: 'include'`. Developers "fix" it by loosening to `SameSite=None`, `allow_origins=["*"]`, or putting tokens in localStorage, all banned by CLAUDE.md.
- Correct fix: use the Vite dev proxy (`server.proxy: { '/api': 'http://backend:8000' }`) so the browser sees ONE origin in dev AND in prod (nginx serves static + proxies `/api`). Cookies and CSRF then behave identically. Set `changeOrigin` appropriately; inside Compose target the service name, not localhost.
- `Secure` flag set from `ENV` so dev over http still works; do not hardcode `Secure=False`.
- Refresh cookie `Path` scoped to `/api/v1/auth/refresh`: dev proxy path must match prod path exactly, or the cookie is never sent. Cookie `Path` scoping plus `SameSite=Strict`: top-level navigation from an email link does not carry Strict cookies (not an issue for OTP codes typed in, but matters if a magic-link is added later).
- CSRF double-submit: the CSRF cookie must be JS-readable (NOT HttpOnly) while the auth cookies are HttpOnly; header name must be read by the frontend wrapper once (single fetch client) rather than ad hoc; CSRF cookie must be set on first visit and rotated at login; state-changing endpoints including logout and the OTP request endpoint should be covered (login CSRF) or at least rate-limited; compare with `hmac.compare_digest`. TanStack Query mutations go through one `apiFetch` wrapper that adds the header; GETs must never change state.
- Refresh rotation race: two browser tabs refresh at once, second presents an already-used token and the "reuse detected, revoke family" logic logs the user out (or worse, a legit parallel request from a slow network triggers it). Mitigate with a short grace window (e.g. 10-30s accepting the previous token and returning the same successor) or a single-flight refresh in the frontend (one refresh promise shared across queries); decide explicitly.
- 401 handling: TanStack Query retries 401s by default; configure `retry: false` for 401 and a global handler that attempts one refresh then redirects to login, otherwise refresh storms.
- Behind nginx TLS termination, FastAPI sees http: cookie `Secure` is set by the app regardless, but redirect URLs and `request.url.scheme` can be wrong without `--proxy-headers`.
- HSTS added before TLS works permanently locks out; start with a short `max-age`.

**How to avoid:**
Adopt "single origin everywhere" as a Phase A/B architecture decision (Vite proxy in dev, nginx in prod, no CORS needed at all, which also removes a whole class of misconfig). Add an e2e Playwright test of login -> authenticated call -> refresh -> logout that runs against the Compose stack, and a backend test asserting cookie attributes (HttpOnly, Secure, SameSite, Path) and that a POST without CSRF header gets 403.

**Warning signs:**
`allow_origins=["*"]`, `SameSite=None`, `localStorage` anywhere in auth code, "works on my machine but 401 after deploy", refresh cookie missing from network tab on `/refresh`.

**Phase to address:** A (proxy/origin decision), B (implementation + e2e).

---

### Pitfall 10: First VPS deploy mistakes (exposed ports, TLS, secrets, backups)

**What goes wrong:**
- Docker publishes ports by writing iptables rules that BYPASS `ufw`. `ports: "5432:5432"` or `"6379:6379"` in compose exposes Postgres/Redis to the internet within minutes (Redis without auth gets compromised fast; bots scan constantly). Dev override file with published ports copied to prod.
- Compose dev stack used in prod: `--reload`, debug, `/docs` exposed, `ENV=dev`, dev console email backend (codes in logs, and nothing is emailed).
- TLS: certbot standalone fails because nginx owns port 80; first issuance rate limits when retrying (Let's Encrypt has failed-validation limits; use `--staging` first); renewal never tested, cert silently expires after ~90 days and nginx needs a reload to pick up the renewed cert; DNS A record not propagated; IPv6 AAAA record pointing nowhere.
- Secrets: `.env` committed or world-readable, default `POSTGRES_PASSWORD`, same secret for HMAC and JWT, secrets baked into the image, `JWT_SECRET` regenerated each deploy (logs everyone out) or left as a placeholder from `.env.example`.
- Backups: none, or `pg_dump` to the same disk, or never restore-tested. With "no reset" accounts, losing the DB loses friends' history for good. Postgres volume is a named volume that `docker compose down -v` deletes.
- No `restart: unless-stopped`; containers die on reboot; no healthchecks; disk fills with Docker logs (set `logging` driver `max-size`/`max-file`); no swap and OOM-killed small VPS (Postgres + Redis + backend + worker + nginx on 1-2 GB RAM: set memory-conscious Postgres settings, one uvicorn worker is plenty for tens of users, do not run 4 workers x preload).
- SSH: password login enabled, root login; no firewall allowing only 22/80/443; no unattended security upgrades.
- Alembic migration run manually or racing in every replica on startup; use a one-shot `migrate` service or entrypoint step that runs once before the app, never `create_all`.
- Frontend built with the wrong API base URL or Vite env var baked in at build time.
- Clock skew: timestamps and JWT `exp` break if NTP is off.

**How to avoid:**
Separate `docker-compose.prod.yml` (no published ports except nginx 80/443; `internal` network for db/redis; Redis `requirepass`; non-root; pinned image tags). After deploy verify externally: `nmap <ip>` or an online port scan shows only 22/80/443. Certbot with a deploy hook (`nginx -s reload`), test `certbot renew --dry-run`, and a calendar/monitor on cert expiry. Nightly `pg_dump` (cron on host or a backup container) to off-box storage (object storage / another machine), keep N days, and do ONE restore drill into a scratch DB before launch. Add a free uptime monitor hitting a `/healthz` that also reports price age (so a dead poller pages you). Keep `.env` mode 600, outside git, document every variable in `.env.example`. Run `docker compose config` to inspect the effective merged config. Firewall deny-by-default and fail2ban or SSH key-only.

**Warning signs:**
`ss -ltnp` on the host shows 5432/6379/8000 on 0.0.0.0; `docker ps` PORTS column has `0.0.0.0:` for anything but nginx; no cron entry for backups; certbot timer not listed in `systemctl list-timers`.

**Phase to address:** F (Deploy), but the prod compose file split and "no published DB ports" rule should start in A.

---

### Pitfall 11: Symbol mapping and asset identity between provider and app

**What goes wrong:**
Provider IDs differ (CoinGecko uses ids like `bitcoin`; exchanges use pairs like `BTCUSDT`, Kraken uses `XBT`); tickers collide (many tokens share `UNI`, `LUNA` was reused after the Terra collapse); a coin is delisted or renamed and the price disappears; USDT price treated as USD (it is a stablecoin, small depeg is realistic: label prices as USD-equivalent or use a USD-quoted pair); mixing quote currencies between coins.

**How to avoid:**
An `assets` table/config with internal `symbol` (stable, our key), `name`, `provider_id`, `quote`, `qty_decimals`, `enabled`. Never use the provider's symbol as a foreign key. A startup/ingest check that every enabled asset got a price and an alert when one is missing (mark just that asset stale and non-tradable, do not fail the batch). Trades store the internal symbol. Disabling an asset must still let users SELL existing holdings (decide policy: allow sell at last price? block with message?), handle explicitly rather than orphaning positions.

**Warning signs:**
String matching on `"btc"`; a batch response missing a key crashes the whole job (`KeyError`); no `enabled` flag.

**Phase to address:** C.

---

## Moderate Pitfalls

### Pitfall 12: Python 3.14 library compatibility surprises

**What goes wrong:**
A dependency has no cp314 wheel and falls back to a source build that fails in the slim Docker image (no compiler), or it works but lags. Free-threaded and the new default `annotationlib` deferred annotation evaluation (PEP 649/749) can break libraries that introspect annotations (older Pydantic/FastAPI/SQLAlchemy `Mapped[...]` forward references, dataclass tools). Docker base images and `uv` managed Python must both be on 3.14; mypy/ruff versions must support 3.14 syntax.

**Verified today (PyPI, 2026-10-20):** cp314 wheels exist for asyncpg 0.32.0, pydantic-core 2.50.1, uvloop 0.23.0, httptools 0.9.0, orjson 3.13.0, psycopg2-binary 2.9.13 (macOS wheels were visible in the sample; Linux manylinux wheels were not individually confirmed, so confirm in the Docker build). Treat as HIGH for existence on PyPI, MEDIUM for the Linux x86_64/arm64 images.

**How to avoid:**
- In Phase A, build the backend Docker image with `uv sync --frozen` and run a smoke test (import app, hit `/healthz`, run one DB query via asyncpg, one Pydantic Decimal round-trip) in CI. This catches wheel gaps on day one.
- Pin `requires-python = ">=3.14,<3.15"`, commit `uv.lock`, use `uv sync --frozen` in CI and Docker so a surprise upgrade is impossible.
- Prefer maintained, wheel-publishing libs (`PyJWT`, `redis`, `httpx`, `celery`). Check Celery/kombu, `respx`, `pytest-asyncio` and `hypothesis` release notes for 3.14 support before adopting each. Celery is the riskiest of the set (large dependency tree); verify before committing to it.
- Do not adopt 3.14-only features (template strings, free-threading) in app code for no reason.
- Fallback decision recorded: if a critical dep blocks, drop to 3.13 for the image rather than fighting it (CLAUDE.md says 3.14, so this needs the user's OK).

**Warning signs:**
`Building wheel for ...` in Docker logs; `NameError` on forward-ref annotations at import; mypy crashes.

**Phase to address:** A.

---

### Pitfall 13: Async SQLAlchemy gotchas that become money bugs

**What goes wrong:**
`MissingGreenlet` from lazy loads; `expire_on_commit=True` default re-fetching after commit in async; one session shared across concurrent tasks (`asyncio.gather` on one `AsyncSession`) corrupts state; `statement_timeout` killing a legit long lock wait mid-trade; `idle_in_transaction` timeout hit because an external HTTP call (price fetch, email) happens inside an open transaction; pool exhaustion on a tiny Postgres (`max_connections` vs pool_size x workers); autogenerated Alembic migrations miss CHECK constraints and server defaults (the very constraints Pitfalls 3-5 rely on).

**How to avoid:**
`async_sessionmaker(expire_on_commit=False)`; one session per request via dependency; no network I/O inside the trade transaction; set role-level timeouts; add CHECK constraints by hand in migrations and assert them in a test (insert a negative cash row, expect `IntegrityError`); small pool (5-10).

**Phase to address:** A (session factory), D (constraints).

---

### Pitfall 14: Displaying money and time incorrectly in the UI

**What goes wrong:**
`Number(string)` on money in JS; `toFixed` rounding differs from server HALF_EVEN so the shown total differs by a cent from the backend; showing 8 dp USD or 2 dp BTC; timestamps shown in UTC without label or "as of" computed against client clock (wrong if device clock is off); portfolio total computed on the client from stale per-coin prices that were fetched at different times so it is inconsistent with the server.

**How to avoid:**
Server computes portfolio valuation in one consistent snapshot (single price read) and returns strings including the `as_of`; client only formats with `Intl.NumberFormat` on strings via a decimal lib or just displays server-formatted-precision strings. Relative "as of" age shown with a stale badge when older than the max age; disable trade buttons client-side when stale (server remains authoritative). Use a TanStack Query `refetchInterval` aligned with the poll interval, not tight polling.

**Phase to address:** E.

---

### Pitfall 15: Testing gaps that hide the above

**What goes wrong:**
Tests mock the DB so races and CHECK constraints are never exercised; time-dependent staleness tests use real `sleep`; provider tests hit the network; coverage hits 80% but money paths assert nothing; e2e uses the dev stack and pollutes data.

**How to avoid:**
Inject a clock (`now()` dependency) so staleness is testable; `respx` for the provider including 429, malformed JSON, `price: 0`, missing key, spike; Hypothesis property tests for the ledger; concurrency test (Pitfall 3); CI set up in Phase A with the isolated test compose stack; mutation-style sanity check (deliberately break rounding and confirm a test fails) on the money module.

**Phase to address:** A (CI), D.

---

## Minor Pitfalls

### Pitfall 16: New-account bootstrap done twice or not at all

**What goes wrong:**
$10,000 credited on every OTP verify, or two concurrent first verifies create two accounts/two bonuses (no reset is a product promise).
**Prevention:** Account creation + opening balance in one transaction with `UNIQUE (email_normalized)`; insert, catch `IntegrityError`, then select (per CLAUDE.md uniqueness rule); record the starting grant as a ledger/trade-like row so cash is auditable.
**Phase:** B/D.

### Pitfall 17: Spread/fee config changes rewriting history or confusing users

**What goes wrong:** Changing `SPREAD`/`FEE` env values alters displayed past costs if recomputed. **Prevention:** store the applied spread, fee rate and fee amount on each trade; never recompute history from current config. **Phase:** D.

### Pitfall 18: Over-building v1 (scope creep against the MVP rule)

**What goes wrong:** RabbitMQ, nginx tuning, PgBouncer, websockets, charts, multi-provider fallback and Celery before they are needed delay the deploy that defines "done". **Prevention:** a poller as a single scheduler container, Redis only (noeviction), nginx added only in the deploy phase, and park chart/snapshots in v2 as PROJECT.md says. **Phase:** all, roadmap review.

### Pitfall 19: No visibility when the poller silently dies

**What goes wrong:** Everything "works" but all trades are refused as stale, or worse the gate is misconfigured too loose. **Prevention:** `/healthz` includes newest price age; uptime monitor; log one line per poll cycle with count updated/skipped. **Phase:** C/F.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Store `avg_price` instead of `total_cost` | Simpler model | Drift, wrong realized P/L | Never |
| Poller in FastAPI lifespan | No extra service | Duplicate polls per worker | Never (even for dev if `--workers>1`) |
| Check staleness only in UI | Faster UI work | Stale trades possible via API | Never |
| Single provider, no fallback | Less code | Outage = no trading | OK for v1 if staleness refusal is graceful and provider sits behind an interface |
| Console email in prod | Skips Resend setup | Nobody can log in | Never |
| Skip idempotency keys | Fewer fields | Double-click duplicate trades | Only if the confirm UI guards and DB has a short dedupe window; prefer keys |
| Manual `pg_dump` "when I remember" | No cron | Data loss | Never after friends have accounts |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Price API | Per-coin calls; ignoring monthly cap; floats | One batched call; compute calls/month; Decimal from raw string |
| Resend | `resend.dev` sender; unverified domain; swallowing errors | Verified subdomain with SPF/DKIM/DMARC; surface/log provider errors; send in a background job |
| Redis | Keys without TTL; `noeviction` with no memory alert; OTP counters non-atomic | TTL everywhere; Lua/`INCR`; alert on memory |
| nginx | Missing `X-Forwarded-*`; HSTS too early | `--proxy-headers` with trusted proxy only; short HSTS first |
| Let's Encrypt | Testing on prod endpoint; no reload on renew | `--staging` first; deploy hook; `renew --dry-run` |

## "Looks Done But Isn't" Checklist

- [ ] **Trade engine:** 20 parallel buys exceeding cash leave cash >= 0 and exactly N successes (real Postgres)
- [ ] **Sell all:** leaves exactly 0 quantity and 0 cost basis
- [ ] **Staleness:** trade refused when `as_of` is older than max age, with Redis empty AND with Postgres-only price
- [ ] **Bad ticks:** zero/negative/spiked/missing coin in provider response does not overwrite a good price or crash the batch
- [ ] **Quota:** calls/month computed and documented for the chosen provider
- [ ] **OTP:** identical response for known/unknown email; 5-attempt limit holds under parallel guesses; raw code never in prod logs
- [ ] **Email:** a friend on Gmail AND Outlook receives the code (not spam) from the verified domain
- [ ] **Cookies:** attributes asserted in tests; refresh in two tabs does not log the user out; prod and dev share one origin
- [ ] **Scheduler:** `docker compose up --scale backend=2` does not double polling
- [ ] **Deploy:** external port scan shows only 22/80/443; `certbot renew --dry-run` passes; backup restored once into a scratch DB
- [ ] **Docs:** `/docs` and `/openapi.json` return 404 in prod
- [ ] **Python 3.14:** Docker build from `uv.lock` with no source builds; smoke test in CI

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 12 Python 3.14 compat | A | CI Docker smoke test |
| 13 Async SQLAlchemy gotchas | A, D | constraint tests |
| 15 Testing gaps | A | clock injection, respx, concurrency test |
| 9 Cookie/CSRF/origin | A (decision), B | Playwright login e2e, cookie attribute tests |
| 7 OTP flaws | B | login tests at 100% coverage |
| 8 Resend deliverability | B (code), F (DNS) | real inbox test from verified domain |
| 16 Account bootstrap | B/D | concurrent first-verify test |
| 1 API quota | C | documented calls/month, 429 handling test |
| 6 Scheduler duplication | C | `--scale backend=2` check |
| 11 Symbol mapping | C | missing-key test |
| 2 Stale/bad prices | C, D | respx bad-tick tests, staleness gate tests |
| 19 Poller visibility | C, F | `/healthz` price age |
| 3 Double-spend races | D | parallel trade test |
| 4 Decimal/rounding/dust | D | Hypothesis + reconciliation invariant |
| 5 Average-cost math | D, E | golden scenarios |
| 17 Config rewriting history | D | trade row stores applied rates |
| 14 UI money display | E | server-formatted strings, Vitest |
| 10 VPS deploy | F (prod compose split from A) | port scan, renew dry-run, restore drill |
| 18 Scope creep | roadmap | review each phase against MVP rule |

## Research Flags for Roadmap

- **Phase C (Prices):** needs a spike on the chosen provider's CURRENT free-tier limits, key requirement, terms and symbol list. Search results disagreed (30 vs about 100 calls/min; key required or not) while the 10,000/month cap was consistent; verify on the official page before committing.
- **Phase B/F (Resend):** verify current free-tier daily/monthly send limits and domain verification steps in Resend docs; DNS wall-clock delay means starting domain work early.
- **Phase A (Celery on 3.14):** verify Celery/kombu support for 3.14 before choosing Celery over a single-loop scheduler container.
- **Phases D, E, F:** standard patterns, specific design decisions above suffice.

## Sources

- PyPI JSON API for asyncpg, pydantic-core, uvloop, httptools, orjson, psycopg2-binary (queried 2026-10-20): cp314 wheels present. HIGH.
- CoinGecko Demo plan summaries via web search (zuplo.com learning center, costbench, spark.money, python-coingecko docs): 10,000 calls/month cap consistent; per-minute limit and key requirement conflicting. MEDIUM for monthly cap, LOW for per-minute figure. Verify at https://www.coingecko.com/en/api/pricing.
- Project files: /home/YokaiExchange/CLAUDE.md, /home/YokaiExchange/.planning/PROJECT.md.
- Resend sender/domain behaviour, Docker/ufw iptables bypass, Let's Encrypt renewal and rate limits, Postgres row-locking semantics, PEP 649/749, OWASP session/CSRF guidance: established engineering knowledge, not re-verified in this session. MEDIUM.
