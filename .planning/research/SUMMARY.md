# Project Research Summary

**Project:** Birja — v1.1 US Stock Trading
**Domain:** Adding US equities to an existing virtual-money crypto simulator
**Researched:** 2026-11-10
**Confidence:** HIGH for documented restrictions and existing invariants; MEDIUM for the proposed design; public stock-feed entitlement unresolved

## Executive Summary

The owner confirmed twenty curated NYSE/Nasdaq common stocks, whole-share market
orders, regular sessions only, one existing USD balance and combined
portfolio/history. Quotes must be about as recent as crypto; fifteen-minute
delay is unacceptable. This is an extension of the working simulator, not a
brokerage integration. Keep its FastAPI/React stack, one scheduler, shared account
lock and exact Decimal accounting. Planning milestone v1.1 is distinct from the
currently deployed software release v0.4.0.

**The requested free public stock-data arrangement is not yet established.**
Twenty symbols are a modest technical workload, but free personal API access
does not establish rights to show quotes, stored fills or derived valuations to
other users. Alpaca Basic/IEX is the strongest conditional technical candidate:
one batched request per minute fits its documented quotas, but IEX is one venue,
not consolidated SIP/NBBO. Current Alpaca terms require advance notice for a
User Application and reserve restrictions; older Broker sandbox wording does
not grant this deployment permission. Seek explicit permission only if the
owner authorizes that next step. Do not silently pay, contact providers, create
accounts, lower freshness or treat login protection as a display license.

After the owner resolves data feasibility and simulator policies, build in
runnable slices: truthful stock discovery, whole-share trading with basic
combined holdings/history, then complete acceptance and recovery rehearsal.
Preserve source-event time separately from collection time, enforce session and
instrument status after lock waits, and protect holdings against corporate
actions. Calendar rules alone do not detect halts, and ignoring splits can
fabricate large investment losses. New schema must also update restricted-role
and exact-recovery contracts. **Research is complete; final requirements and
implementation are gated on the decisions below.**

## Key Findings

### Recommended Stack

Retain the deployed stack and lockfiles. No new framework, queue, brokerage SDK
or WebSocket service is justified. Detailed versions and validation limitations
are in [STACK.md](STACK.md).

**Core technologies:**

- **FastAPI/Python 3.14 and existing httpx:** provider-boundary validation and
  bounded async REST collection without adding an SDK.
- **PostgreSQL, SQLAlchemy, asyncpg and Alembic:** authoritative instrument,
  quote, cash, holding and immutable fill state; preserve existing IDs and money
  with new migrations after schema 0008.
- **Redis and one scheduler process:** existing leases/cache, separate bounded
  crypto and stock work; no provider calls per user or trade preview.
- **React/TypeScript, TanStack Query and existing design system:** extend current
  discovery, ticket, portfolio and history with asset identity and market state.
- **`exchange_calendars` 4.13.2, conditional candidate:** tagged source declares
  Python 3.14 support. Its pandas/NumPy dependencies still require real lock,
  hardened-image and scan validation; it is neither installed nor a halt feed.
  Standard-library `zoneinfo` handles America/New_York boundaries.

**Provider feasibility:** [FEASIBILITY.md](FEASIBILITY.md) is the detailed gate.

| Candidate | Key finding | Disposition |
|---|---|---|
| Alpaca Basic/IEX | Documented 200 calls/minute; latest-quotes batch can cover 20 symbols in one call. Single-venue data, with application permission unresolved. | Best conditional technical candidate; not selected or licensed for Birja |
| Finnhub | Terms require written approval for sharing source or derived data; current dynamic pricing/quota text could not be independently read. | Permission and current plan details unresolved |
| Twelve Data Basic | Eight credits/minute, 800/day; per-symbol batch credit accounting and internal non-display scope. | Fails requested workload and usage scope |
| Massive free | End-of-day data, five calls/minute and individual-use scope. | Fails freshness; minute aggregation is not current delivery |
| Alpha Vantage standard free | 25 requests/day; current US equity data premium-only. | Fails cadence/freshness |
| Market Data self-service | Public app display routed to Commercial plan; no sufficient free entitlement verified. | No verified free public option |

A normal 390-minute session needs roughly 7,800 single-symbol requests, or 390
verified batch calls, before retries, status/calendar maintenance and boundary
samples. Batch HTTP does not reduce a provider's per-symbol credit accounting.
No investigation established that every possible free agreement is impossible;
none established the full permission/access/freshness contract for Birja.

### Expected Features

See [FEATURES.md](FEATURES.md) for proposed acceptance outcomes and policy choices.

**Confirmed owner scope:**

- Exactly twenty curated NYSE/Nasdaq common stocks alongside existing crypto.
- Whole-share quantity buy/sell orders; no fractional-stock or dollar-input stock
  orders, and no overnight queuing.
- One shared USD balance, combined portfolio and stored history; no second
  starting-cash grant.
- Stock trading only during regular sessions; crypto remains independent.
- Crypto-like price recency, not fifteen-minute-delayed stock trading.

**Required engineering outcomes proposed for requirements approval:**

- Stable instrument identities, explicit provider mapping and visible feed/source
  time; listing venue and quote venue remain distinct.
- Server-owned session, holiday, early-close, DST and instrument eligibility.
  Unknown/expired/halted/frozen state refuses new stock fills.
- Exact preview/cash/basis/fill accounting, shared account serialization and
  user-scoped idempotency across both asset classes.
- Closed stock marks remain visible with their actual timestamps; missing or
  quarantined values make totals explicitly incomplete, never silently zero.
- A bounded, enforceable corporate-action safety policy plus migration,
  least-privilege and mixed-asset recovery proofs.

**Useful small additions:** concise reasons for unavailable trading, next session
when known, asset-class filters and honest simulated-fill explanations. Additional
allocation breakdown is optional, not a substitute for correct combined totals.

**Defer:** charts, watchlists, fundamentals, broad symbol search, ETFs/options/OTC,
extended hours, limit/stop orders, fractionals, margin, shorts and real order
routing. Deferring dividend credits or settlement restrictions requires owner
acceptance of those simulator limitations; whole-share orders do not resolve
reverse-split entitlements.

### Architecture Approach

[ARCHITECTURE.md](ARCHITECTURE.md) recommends expanding the existing instrument,
holding and fills model rather than adding a parallel stock engine. Preserve
crypto IDs, FKs, historical values and legacy symbol-only crypto API semantics.
Physical `coins`/`coin_id` names can remain compatibility storage names while
new API requests and query keys use stable asset IDs. Avoid a broad rename or
generic provider registry without a concrete need.

**Major components:**

1. **Instrument catalogue and capabilities:** asset class, USD denomination,
   provider mapping, listing/calendar metadata and whole-share order rules.
2. **Quote/session/status ingestion:** typed Decimal observations with provider,
   feed, reference-price kind, event time, fetch time and adjustment semantics;
   monotonic persistence and independent bounded source failures.
3. **Shared executor:** existing account lock before holding locks; replay lookup
   before present-day eligibility; resampled time/status after blocking locks;
   one transaction for cash, holding, basis and immutable provenance-bearing fill.
4. **Combined read models/UI:** one portfolio statement and keyset history, with
   honest per-instrument valuation and availability rather than a global closed
   flag or one timestamp for the whole account.
5. **Versioned operational contracts:** explicit new-table grants, schema-aware
   backup hashes/validators and retained-tool compatibility. Repository edits
   alone do not update installed production tools or authorize rollout.

**Proposed freshness contract, not yet approved:** collect about every 60 seconds
and consider crypto's strict source-age <120 seconds bound for stocks. Use the
provider event time, require a valid current-session observation at reopening,
and recheck after lock waits. A last trade is not a midpoint; derive midpoint
only from eligible bid/ask data decoded without binary-float money conversion.
Exact price-reference and status-validity rules depend on the permitted feed.

### Critical Pitfalls

1. **A working API key is mistaken for permission:** record actual product,
   audience, display/derived-data/retention rights, attribution, access and cost
   before publishing stock data. Preserve the applicable terms/version.
2. **Collection time conceals old or partial data:** keep source-event time and
   explicit feed coverage, reject stale/future/out-of-order or malformed quotes,
   and never silently substitute delayed SIP or yesterday's mark for a fill.
3. **An open calendar is mistaken for a tradable stock:** validate date-specific
   sessions, DST/early closes and separately bounded instrument status; test
   close/expiry while waiting on locks and successful replay after closure.
4. **Whole-share orders conceal broken corporate-action accounting:** detect and
   quarantine affected instruments, preserve historical fills, reconcile units
   and total basis idempotently, and explicitly resolve reverse-split residuals
   and dividend-return semantics.
5. **Stocks bypass existing money or recovery invariants:** serialize crypto and
   stock spending on the same account and prove cross-asset contention; update
   least-privilege and exact restore contracts for every new schema element.

See [PITFALLS.md](PITFALLS.md) for detection fixtures and recovery boundaries.

## Implications for Roadmap

The following three runnable slices are recommendations, **not an approved
roadmap**. Numbering starts at Phase 7 after archived v1.0. Do not finalize their
requirements before owner disposition of the feasibility/policy decisions.

### Phase 7: Permitted Stock Data and Truthful Market Discovery

**Rationale:** Display entitlement and actual quote semantics constrain every
downstream feature. They must be resolved before public data display or promises
of executable stock prices.

**Delivers:** A recorded provider/coverage/rights decision, twenty verified
instruments, bounded quote/calendar/status ingestion and a runnable stock market
view with honest source age and closed/unknown state. Existing crypto remains
fully usable; stock execution remains disabled until eligibility is proven.

**Addresses:** Catalogue, current-price visibility and per-asset status. Approved
corporate-action monitoring/freeze policy must be established before risky marks
are exposed. New schema brings its migration, grant and recovery compatibility
work in this phase, not as a last-minute release add-on.

**Avoids:** Personal-license assumptions, IEX/SIP confusion, forged freshness,
fixed-UTC sessions, quota starvation and crypto outages from a failing stock feed.

### Phase 8: Whole-Share Trading with Shared Cash and Combined Positions

**Rationale:** A fill is not a completed user slice unless users can see its cash,
holding, basis and persisted history in the existing account.

**Delivers:** Server preview, integral quantity buy/sell, approved simulated costs,
immutable provenance, basic combined portfolio/history and approved corporate
action safeguards. Crypto dollar/fractional orders retain their existing behavior.

**Addresses:** The full first-stock-trade loop, truthful closed valuations and
account persistence. Implement any approved action/income accounting here rather
than enabling fills with undefined position rules.

**Avoids:** Cross-asset overspend, duplicate fills, replay refusal after closure,
expiry during lock waits, fractional-order leakage and split-induced false P/L.
Require real-Postgres concurrency, time-controlled market boundary and exact
accounting tests.

### Phase 9: Multi-Asset Acceptance and Release Readiness

**Rationale:** Validate the expanded account end to end and prove operational
compatibility before an explicitly approved production release.

**Delivers:** Completed labels/filtering and mixed-asset acceptance, existing-data
upgrade rehearsal, restricted-role proofs, exact mixed-state restore, current
image/security gates and a reviewable release/operations handoff. Public live
acceptance occurs only with permitted data and separately approved rollout.

**Addresses:** Normal open-session trading, closed-stock/working-crypto behavior,
provider/status failures, action quarantine and complete holdings/history totals.

**Avoids:** Superuser-only success, backups omitting new state and automatic
production changes inferred from planning approval. Do not defer essential
money/status/recovery tests until this phase; it validates the integrated result.

### Phase Ordering Rationale

- Data rights, coverage and approved product policies determine safe execution.
- Discovery works before orders; each later slice leaves the app runnable.
- Basic combined valuation/history ships with the first stock fill.
- Migrations, restricted roles and backup contracts evolve together; final
  release acceptance validates them with retained tooling and mixed holdings.
- Accepted v1.0 W01–W08 debt remains separately tracked unless deliberately
  required by this feature, rather than silently expanding the milestone.

### Research Flags

**Needs focused research during planning:**

- **Phase 7:** actual provider permission/account access, acceptable feed coverage,
  source-age availability across twenty symbols, calendar dependencies, halt-feed
  reuse/expiry and corporate-action monitoring. A successful quote request is
  insufficient evidence of rights or reliable availability.
- **Phase 8:** action/residual/dividend semantics under the chosen scope, stock
  fee/reference-price policy and constraints compatible with post-action holdings.
- **Phase 9:** exact schema/manifest/grant compatibility and successor retained
  artifacts; current source/image/provider eligibility must be revalidated.

**Established patterns needing no broad stack survey:** existing HTTP mocks,
Decimal math, account lock/idempotency, React/TanStack Query, keyset history and
isolated database tests. Reuse these patterns while specifically testing their
new cross-asset behavior.

## Confidence Assessment

| Area | Confidence | Notes |
|---|---|---|
| Stack | HIGH existing; MEDIUM additions | Existing versions are repository evidence; calendar declared support is not a successful hardened-image build |
| Features | HIGH confirmed scope; MEDIUM proposed boundaries | Exchange/regulator mechanics are documented; costs, action/income and settlement choices need owner approval |
| Architecture | HIGH invariants; MEDIUM proposed schema | Existing locks, IDs, migration and recovery contracts inspected; final status/provider design conditional |
| Pitfalls | HIGH documented risks | Primary provider/exchange/regulator sources and local operational contracts; mitigation scope remains proposed |
| Feasibility | HIGH restrictions; LOW unconfirmed entitlement | No investigated free arrangement verified the full public-app contract; no private account or provider permission obtained |

**Overall confidence:** MEDIUM for a buildable plan, with a blocking data-rights
and product-policy gate. This is not uncertainty about the confirmed user goal.

### Gaps to Address — Owner Decision Priority

1. **Data approach first:** retain $0/current freshness and authorize pursuing
   explicit permission, starting with Alpaca IEX, or explicitly change budget or
   defer/change live-stock scope. Ask whether labelled single-venue IEX coverage
   is acceptable. Do not quote personal subscription prices as public-app license
   prices. No provider signup/contact/spend or agreement acceptance is authorized.
2. **Execution contract:** approve exact source-age threshold, eligible reference
   price and simulated stock fee/spread. Do not silently copy crypto's 0.25%
   spread plus 0.25% fee or call a last trade a midpoint.
3. **Position safety and income:** approve enforceable monitored freeze/manual
   reconciliation or supported automation, including responsibility, event timing,
   reverse-split residuals and audit records. Choose price-return-only without
   dividend credits (smallest recommendation) versus ordinary dividend entitlement
   and payment accounting. Neither choice permits ignoring splits.
4. **Settlement simplification:** explicitly accept immediate simulated sale
   proceeds while deferring real settlement restrictions, or scope an alternative.
5. **Implementation evidence after decisions:** verify selected provider access
   without a credit card where required, permitted server/account location,
   attribution/retention, observed recency, status/event-source rights, maintained
   calendar horizon and calendar wheel/image compatibility. No accounts, private
   APIs, installations, runtime tests or production changes occurred in research.

The orchestrator should surface the first decision now and gather the remaining
policy choices before final requirements approval/commit. Research authorization
does not settle them. Conditional roadmap recommendations must not be presented
as a provider-selected, implementation-ready commitment.

## Sources

Primary sources were checked by the contributing researchers on **2026-11-10**.
Rolling pages are current research readbacks, not future entitlement guarantees.
See the five dimension files for the full source inventory and access limitations.

### Primary — HIGH Confidence for Published Text

- [Alpaca market-data plans](https://docs.alpaca.markets/us/docs/about-market-data-api),
  [latest quotes](https://docs.alpaca.markets/us/reference/stocklatestquotes-1),
  [FAQ](https://docs.alpaca.markets/us/docs/market-data-faq) — feed, quotas and batching.
- [Alpaca terms](https://s3.amazonaws.com/files.alpaca.markets/disclosures/library/TermsAndConditions.pdf)
  — User Application advance notice and reserved restrictions; not Birja permission.
- [Official older Broker documentation](https://github.com/alpacahq/bkdocs/blob/master/content/market-data/_index.md)
  — limited sandbox context; no production entitlement inference.
- [Finnhub terms](https://finnhub.io/terms-of-service),
  [Twelve Data pricing](https://twelvedata.com/pricing-business) and
  [credits](https://support.twelvedata.com/en/articles/5615854-credits),
  [Massive pricing](https://massive.com/pricing?product=stocks),
  [Alpha Vantage support](https://www.alphavantage.co/support/),
  [Market Data redistribution policy](https://www.marketdata.app/docs/account/data-policies/data-redistribution/)
  — restrictions and free-tier feasibility, subject to each file's limitations.
- [NYSE calendar](https://www.nyse.com/markets/hours-calendars),
  [Nasdaq calendar](https://nasdaqtrader.com/Trader.aspx?id=Calendar),
  [Nasdaq halt RSS](https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS)
  — scheduled sessions and candidate halt source, not guaranteed instantaneous status.
- [Calendar 4.13.2 metadata](https://raw.githubusercontent.com/gerrymanoim/exchange_calendars/4.13.2/pyproject.toml)
  — declared Python 3.14 compatibility and dependencies, not local validation.
- [SEC fractional-share bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/fractional-share-investing-buying-slice-instead-whole-share),
  [reverse splits](https://www.investor.gov/introduction-investing/investing-basics/glossary/reverse-stock-splits),
  [ex-dividend dates](https://www.investor.gov/introduction-investing/investing-basics/glossary/ex-dividend-dates-when-are-you-entitled-stock-and),
  [IRS split/basis FAQ](https://www.irs.gov/faqs/capital-gains-losses-and-sale-of-home/stocks-options-splits-traders/stocks-options-splits-traders-7)
  — order variability, share-unit/basis and income mechanics.
- Repository models/services, `backend/pyproject.toml`, lockfiles,
  `deploy/db/bootstrap-roles.sql`, `deploy/backup-manifest.sql` and
  `deploy/backup-snapshot.py` — existing architecture and operational boundaries.

### Unverified or Conditional

- Finnhub's current numerical pricing/quota details were not verified from
  readable dynamic primary pages; do not promote advertised figures to fact.
- Public-display permission, actual symbol freshness, specific account access,
  halt-feed rights and complete timely event coverage are not established.
- No secondary commentary overrides the relevant provider agreement or owner
  scope choices. No recommendation is an investment recommendation.

---
*Research completed: 2026-11-10*
*Ready for final requirements/roadmap: no — owner data and simulator-policy decisions required.*
