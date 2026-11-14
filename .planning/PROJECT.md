# Birja

## What This Is

A virtual-money investing simulator. Deployed v0.4.0 offers crypto trading;
prepared software v0.5.0 adds the locally verified twenty-stock US implementation,
shared cash/portfolio, dividends/splits and mixed History. Live stock activation
remains gated because accepted provider/live-verification gaps are unresolved.
Planning milestone v1.1 is closed with known gaps, not fully live-validated.

## Core Value

Making a trade at a real, recent market price and then seeing what it's worth now. If everything else fails, "buy at today's price, check back later, see real P/L" must work and must be correct to the cent.

## Requirements

### Validated

- [x] Sign in with email + one-time code (no passwords); codes emailed via Resend — Phase 2, live delivery verified in Phase 2.1
- [x] New account starts with $10,000 virtual cash, once, with no reset — Phase 2
- [x] Curated list of 15 major cryptocurrencies with prices refreshed about every minute and visible age — Phase 3
- [x] Market buy/sell orders by dollar amount or fractional quantity up to eight decimals — validated in Phase 4: Trading
- [x] Configured simulated spread and fee shown in a server-computed preview, followed by the actual fill — validated in Phase 4: Trading
- [x] Refuse prices aged 120 seconds or more, including time spent waiting for database locks — validated in Phase 4: Trading

- [x] Portfolio cash, holdings at mid, total value and dollar/percent return against stored starting cash — Phase 5

- [x] Fee-inclusive per-holding average cost, unrealized P/L and cash-inclusive allocation with used-price times — Phase 5

- [x] Stored newest-first trade history with exact signed totals and keyset pagination — Phase 5

- [x] Public HTTPS deployment with Gmail/Outlook signup and live trade acceptance — Phase 6
- [x] Nightly encrypted off-server backups and successful exact restores — Phase 6

- [x] Retained structured dividend revisions and historical eligibility snapshots
  without cash publication (DIV-01/02) — locally verified in Phase8
- [x] Exact once-only forward splits, basis preservation and auditable uncertainty
  holds with safe UI (ACT-01–03) — locally verified in Phase8; live activation deferred

- [x] Whole-share regular-session stock execution, eligible IEX ask/bid with zero
  commission/added spread, exact previews/repricing and immutable retry receipts
  — locally validated in Phase9; live activation deferred.
- [x] Shared original USD cash, immediately reusable proceeds, cross-asset
  concurrency safety and combined midpoint/dated/incomplete portfolio valuation
  — locally validated in Phase9; dividend cash publication validated in Phase10.

- [x] Verified ordinary gross USD dividends credit shared cash once, with
  immutable corrections, affordability/uncertainty holds and recovery-safe
  duplicate protection (DIV-03–05) — validated in Phase10.
- [x] Private paginated mixed stock/crypto/Dividend/split/correction History,
  original-reference details and owner/session isolation (HIST-03) — validated
  in Phase10; owner accepted the new UI and genuine native200% on2026-11-13.

- [x] Exact mixed-asset encrypted recovery, current0014 cutover/replay/refusal/
  tested-source rollback and complete protected local journeys (SAFE-02/03) —
  verified in Phase11 with four independent reviews; live activation deferred.

### Active

- [ ] Use IEX stock quotes with visible feed labels and crypto-like freshness; display permission remains a prerequisite for enabling live data.
- [ ] Accepted deferredv1.1Phase7live acceptance (STOCK-01/02/03,DATA-01,MKT-01,SAFE-01); publication and production rollout stay separately gated.

### Out of Scope

- Gold/metals, FX and bonds: deferred. US stocks are now selected for v1.1; other asset classes remain outside its scope.
- Portfolio value-over-time chart: v2. It needs a snapshot job and stored history.
- Limit/stop orders: v2+. They need a background matcher. Market orders cover the core loop.
- Short selling, leverage, margin: not planned. Too complex for a learning tool aimed at beginners.
- Leaderboard and social features: v2+. v1 is solo; each user sees only their own portfolio.
- Portfolio reset: deliberately excluded. Mistakes stay, like real investing.
- Streaming tick-by-tick prices (websockets): not planned for v1. Prices about 1 minute old are enough and work on free data tiers.
- Real money, deposits, brokerage integration: never. This is a simulator.
- Full order-book execution and real order routing: excluded. Stock fills use eligible IEX bid/ask quotes; crypto retains its configured simulated spread.

## Context

- Motivation: most people learn investing by losing real money. This removes that risk. No hindsight or time travel: you decide today and find out over weeks and months.
- Users: the author plus friends. Small scale (tens of users), but it is public on the internet, so security still matters (see CLAUDE.md Security).
- Market data: free tiers only. The curated coin list keeps API calls within free rate limits. Prices are fetched by a single scheduled job and cached in Redis, with the latest price also persisted in Postgres, which is the source of truth.
- Crypto pricing: buy = mid × (1 + spread), sell = mid × (1 − spread), plus configured fee. Approved stock policy: simulated buy at eligible IEX ask, sell at bid; zero commission, zero added spread and no regulatory fees, with clear disclosure. Executed price and source timestamp remain recorded.
- The repo started with only `main`. Git-flow is mapped as `main` = production (the "master" role in CLAUDE.md) and `develop` = integration.
- The design system lives in `design-system/birja/MASTER.md`; existing Tailwind/shadcn components and Node 24 were established in Phase 1. Codex discovers maintained skills through `.agents/skills/`; shared project rules remain in CLAUDE.md.

## Current State

The v1.0 MVP milestone is shipped and archived (2026-11-10): all 7 phases,
69 plans and 31 requirements validated. Software release v0.4.0 is live at
https://birja.nist.one from main 46d24c8, schema 0008. This archive does not
publish or deploy a new software version.

The app delivers email OTP, $10,000 once, fifteen crypto prices, exact atomic
market buys/sells, mid-valued portfolio performance/allocation and stored seek
history. Required CI and independent milestone integration review pass; owner
confirmed both Gmail and Outlook full live flows.

Production uses distinct restricted verified-TLS DB roles, immutable recovery
and retained deployment tooling. Actual rollout passed 41 origin / 9 public
smoke checks and three exact encrypted B2 restores; originals were preserved.
One genuine nightly upload was observed and later rotated under the approved
one-copy policy; the retained post-rollout point was separately fully restored.
Daily backup freshness and certificate-expiry checking remain owner operations.

The owner explicitly accepted W01–W08 and four incomplete historical validation
records as follow-up debt, without claiming fixes. See
[milestone audit](milestones/v1.0-MILESTONE-AUDIT.md),
[integration audit](milestones/v1.0-INTEGRATION-AUDIT.md) and
[retrospective](RETROSPECTIVE.md). Historical accepted logout/protection caveats
remain recorded there. All v1 phase execution history is preserved in `milestones/v1.0-phases/`.

Phases8 and9 are locally complete. Phase9 delivers whole-share IEX ask/bid
simulated execution with zero stock fee, shared original USD cash, idempotent
original receipts and truthful mixed crypto/stock valuations. All15plans/30tasks
and nine assigned requirements pass local verification; owner accepted the ticket,
receipt and combined portfolio and confirmed actual native200%browser zoom on
2026-11-12. Full financial/browser/security/image/recovery/TLS/rollback proof is
recorded in09-LOCAL-PROOF. Distinct inline late reviews do not claim agent independence.

Phase7 live evidence and Phase8/live status/data activation remain deferred;
rights/access/quotas/latency are not established by synthetic tests. Production
remains v0.4.0/schema0008. Phase10 is locally complete:18plans/36tasks/13waves,
all4assigned requirements verified, all four independent review roles complete,
and both current UI/native200%owner outcomes passed. Final backend2557tests,
47critical modules100%statements/branches, frontend697 and browser49plus one
expected deployed-CSPskip pass, with five strict image scans0HIGH/CRITICAL.
Current0014 retained/current-service recovery and legacy0008 selected cutover/
old-app rollback remain distinct. Exact authority/CORE bytes were preserved;
actual review findings were fixed and affected gates independently rechecked.
See10-VERIFICATION/18-SUMMARY/VALIDATION. No software publication or deployment
occurred. Phase11 mixed-asset recovery/acceptance is locally complete:4plans/8tasks,
SAFE-02/03 verified3/3, independentcode0/0,security14/14,UI24/24. Exact samearchive
proof is qualified acrossfb926d8/22c44d6/a7f965f with unchanged retained/runtime
bytes; no fresh completeCIblock or hostedCIpass atfinalsource is claimed.
The approved OpenTelemetry1.45.2 patch passes all affected gates; finalbackend
2557/47critical100%,frontend697,browser49+existingCSPskip,PG24 andfive strict
scans0HIGH/CRITICAL pass. See11-VERIFICATION and11-03/04SUMMARY. Phase7live
acceptance remains unverified. The owner2026-11-14 accepted closure/archive of
v1.1with those six requirement gaps. Softwarev0.5.0 is prepared on release-0.5.0;
no publication, live activation or production change has occurred. See archived
v1.1ROADMAP/REQUIREMENTS/MILESTONE-AUDIT and integration audit.

<details>
<summary>Original v1.1 planning decisions, closed with accepted live gaps</summary>

## Closed Milestone: v1.1 US Stock Trading — accepted live gaps

**Goal:** Let users practise trading 20 curated US stocks alongside crypto,
using the same virtual USD balance and combined portfolio.

**Confirmed target features:**
- NYSE/Nasdaq common stocks; curated list of 20 for the first stock version.
- Whole-share market buy/sell orders; fractional stock orders are excluded.
- One shared USD cash balance, holdings valuation and stored history across assets.
- Regular US trading sessions only; refuse stock orders while closed, including
  holidays and early closes, while preserving crypto's independent availability.
- Stock prices target crypto-like recency (about one-minute refresh rather than
  fifteen-minute-delayed data). Actual source timestamps, permitted feed coverage,
  free-tier quota and user display rights must be researched before committing
  to an implementation/provider. User approved research first.

**Approved follow-up decisions (2026-11-10):**
- Alpaca IEX feed is selected conditionally on access/display permission. User
  accepts single-venue coverage and explicitly requires an IEX prices label.
  Show it on stock listings, previews and valuations; explain simulated execution.
- No stock commission, added percentage spread or regulatory fees. Buys use
  eligible ask, sells use bid; crypto fees/spread stay unchanged.
- Include cash dividends as shared-USD credits and separate History events.
  Regularly refresh structured announcements and known events for corrections;
  preserve revisions, calculate historical eligibility and pay each event once.
  Record post-payment corrections separately; hold uncertain/conflicting cases
  for review rather than guess. Owner accepted this monitoring approach.

**Additional confirmed choices:** automatically process ordinary cash dividends
and straightforward forward splits; suspend the affected stock and mark its
valuation unavailable for uncertain/unsupported events requiring reconciliation.
Virtual sale proceeds are immediately reusable, with real settlement restrictions
outside this milestone and the simplification disclosed.

**Requirements approved (2026-11-10):** all 26 requirements, including gross
ordinary USD dividends without tax/reinvestment, source quote age below 120
seconds, midpoint valuation and holding uncertain or unaffordable negative
corrections for review. Proposed roadmap creation is authorized; approval of
its phase structure remains the next checkpoint. Proposed freshness matches crypto's source
age <120 seconds with about 60-second collection; quotes carry source-event
rather than fetch time. Provider rights, quote/status and dividend-event access
remain activation gates, not assumed satisfied by selecting IEX. No paid plan,
provider contact, signup or deployment is authorized.

**Scope confirmation:** Owner approved the above feature summary, whole-share
approach and milestone v1.1 name on 2026-11-10. Start roadmap numbering at Phase 7.
Research then requirements and roadmap approval precede implementation. Existing
v1 advisory debt remains separately recorded, not added to this scope by default.

</details>

## Next Milestone Goals

No next milestone is selected. Accepted live-activation gaps remain follow-up,
not automatically approved new feature scope. The existing November16manual
measurement approval remains bounded/no automatic process. Use archivedv1.1
requirements/audit when the owner selects further work.

## Constraints

- **Tech stack**: FastAPI/Python 3.14, async SQLAlchemy 2.0 + asyncpg, Alembic, Postgres, Redis, React + Vite + TS, Tailwind + shadcn/ui, TanStack Query, Docker Compose. Defined in CLAUDE.md. Components are added when a step first needs them.
- **Budget**: free market-data tiers only. Resend free tier for email. A small VPS for hosting.
- **Money correctness**: `Decimal` / `NUMERIC(20,8)`, explicit `ROUND_HALF_EVEN` at trade execution, money sent as JSON strings, trades in one DB transaction with row locks.
- **Security**: email OTP stored as an HMAC in Redis, JWT access + rotating refresh token in HttpOnly cookies, CSRF double-submit, rate limits. Per CLAUDE.md.
- **Process**: MVP-first. Each phase leaves the app runnable. Tests ship with features; 80% coverage, and 100% on money, trade execution, login and authorization.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Close v1.1 with six accepted live gaps | Owner requested release/finish anyway; keep truthful history and gated admissions | Accepted deferred, 2026-11-14 |
| Crypto only in v1 | 24/7 market, free near-real-time APIs, fractional quantities; proves the core loop with one data source | ✓ Good — prices and trading shipped in Phases 3/4 |
| Prices refreshed about every 1 min by one scheduled job, not streamed | Fits free tiers; much less infra; "as of" time shown | ✓ Good — Phase 3 live scheduler verified |
| Market orders only | Delivers the core value without a background order matcher | ✓ Good — Phase 4 buy/sell flow verified |
| Fixed % simulated spread + fixed % fee | Free APIs give no bid/ask; still teaches that trading costs money | ✓ Good — Phase 4: 0.25% each, $0.01 minimum fee, sell fee capped at notional |
| $10k start, no reset | Mistakes stay, like real investing | ✓ Good — Phase 2 account invariants verified |
| Curated ~10–20 coins | Keeps API calls within free rate limits | ✓ Good — 15 coins live in Phase 3 |
| Resend for one-time-code email | Free tier, simple API | ✓ Good — real delivery approved in Phases 2.1/4 |
| v1 done = deployed for friends | Real use by real people is the validation | ✓ Verified in Phase 6: Gmail/Outlook flows and backup recovery |
| `main` acts as master; `develop` created from it | Repo started with `main`; avoids renaming the default branch | ✓ Good — release/hotfix PR and back-merge flow verified |
| Kraken public Ticker as the price source | No key, one batched call, real bid/ask; CoinGecko's free 10k calls/month can't sustain a 60s poll | ✓ Good — Phase 3 live data verified |
| Holdings valued at mid price | Simple; a fresh buy shows the cost of spread + fee, which teaches that trading costs money | ✓ Good — Phase 5 valuation, exact performance and browser flow verified |
| One simple scheduler-loop container for prices; OTP email via FastAPI BackgroundTasks | Fewest dependencies; Celery has no declared Python 3.14 support; a lost email just means re-requesting | ✓ Good — Phases 2/3 verified |
| "$ amount" on buys = total cash spent including fee | Cash drops by exactly what the user typed | ✓ Good — Phase 4 exact-cent API, math and e2e assertions |
| Trade only at price age <120 seconds; compare preview/current mid | Reuses the Live threshold and requires renewed confirmation if price moves | ✓ Good — Phase 4; v0.3.1 checks freshness after DB waits |
| Account row lock before holding lock; user-scoped idempotency key | One transaction prevents overspend and duplicate fills | ✓ Good — Phase 4 real-Postgres concurrency verified |
| Maintain holding cost basis during trade execution | Phase 5 can compute average cost including fees without reconstructing history | ✓ Good — Phase 4 updates basis atomically; valuation UI remains Phase 5 |
| Repo made public so branch protection can require `ci-pass` on `develop` and `main` (D-01) | Free real merge blocking. The private plan returned 403 for protection. A git-history secret scan came back clean before the switch | ✓ Good (2026-10-26: protection verified, strict, enforce_admins off) |
| No `ORJSONResponse`/`orjson` (D-02) | Deprecated in FastAPI. Pydantic already serializes `response_model` output | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated:2026-11-14 after owner-approved v1.1close with known gaps; softwarev0.5.0prepared only*
