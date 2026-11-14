# Pitfalls Research: US Stock Trading

**Domain:** Add 20 curated NYSE/Nasdaq stocks to Birja's existing virtual-money crypto simulator
**Milestone:** v1.1 — US Stock Trading
**Researched:** 2026-11-10
**Confidence:** HIGH for documented market/feed behavior and repository constraints; MEDIUM for proposed simulator policies; production data entitlement remains UNRESOLVED

## Scope and recommendation

Keep the existing cash account, exact arithmetic, transaction locks and stored
fills. Add stock-specific eligibility, source timestamps and session checks.
Do not interpret “like real stock markets” as approval for brokerage settlement,
margin, shorting, an order book or queued orders. Whole-share market orders and
regular sessions are confirmed; corporate-action treatment and stock execution
costs still need explicit product decisions.

The largest risk is a superficially live demo: an API responds successfully,
but its data is delayed, covers one venue, cannot be displayed to other users,
or values shares on the wrong side of a split. Establish those contracts before
stock execution is enabled. Phase labels below are proposed responsibilities,
not an approved roadmap.

## Critical Pitfalls

### 1. Treating a free personal API subscription as permission to serve friends

**What goes wrong:** A shared server fetches prices using the owner's key and
redistributes them through Birja, despite the plan being personal-use only.

**Why it happens:** Authentication, free quotas and commercial/noncommercial use
are mistaken for display rights. A simulator with no payments still has other
users. Alpaca's linked terms require advance notice for an application made
available to others and reserve the right to restrict it; this is not a blanket
redistribution grant. [Alpaca terms](https://s3.amazonaws.com/files.alpaca.markets/disclosures/library/TermsAndConditions.pdf).
Another provider explicitly limits self-service plans to personal use and
requires a commercial license for redistribution. [Market Data policy](https://www.marketdata.app/docs/account/data-policies/data-redistribution/).

**Prevention:** Phase 7 must record the exact provider, feed, plan, user audience,
server location/access eligibility, display/derived-price permissions,
attribution and cost. Obtain provider clarification where published terms do
not grant this application's use. An API spike may prove transport, not rights.
Do not silently buy a plan, publish provider data, or weaken freshness to solve
this gate. No permission has been established by this research.

**Detection:** “API key works” is the only acceptance evidence; a personal plan
is described as a public application license; no terms/version/date are saved.

**Phase:** Phase 7 provider feasibility and entitlement gate. **Confidence:** HIGH
for restrictions cited; UNKNOWN for Birja-specific authorization.

### 2. Confusing listing exchange, source venue and consolidated market coverage

**What goes wrong:** Prices for NYSE/Nasdaq-listed stocks are presented as the
whole US market even though the source is only IEX. Price differences become
unexplained gains/losses when users compare Birja with another application.

**Evidence:** Alpaca documents IEX as a single exchange, free live data as IEX,
and SIP as consolidated exchange reporting. Recent SIP access requires the
appropriate subscription. [Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq).

**Prevention:** Keep listing venue separate from data feed. If the owner accepts
IEX coverage after research, name it honestly in requirements/UI and persisted
execution provenance. Select 20 liquid common stocks only after verifying feed
availability; do not assume a listing implies continuous activity on IEX.
Specify valuation reference and simulated execution pricing independently.

**Detection:** Provider defaults choose the feed implicitly; stored fills only
say “stock”; tests accept SIP and IEX interchangeably.

**Phase:** Phase 7 feed decision, then ingestion and execution. **Confidence:** HIGH
for feed differences; MEDIUM for proposed product handling.

### 3. Resetting quote age whenever a poll returns

**What goes wrong:** A delayed or unchanged old quote is stamped with receipt
time and becomes executable. Frequent polling disguises fifteen-minute delay.

**Why:** Crypto's current ticker adapter does not establish stock event-time
semantics. A stock response contains distinct trade, quote and bar timestamps;
a minute bar is an aggregate, not an instantaneous executable quote.
Alpaca's schemas expose event timestamps, conditions and separate bid/ask data;
minute bars can include extended-hours trades and later revisions.
[Real-time stock schemas](https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data).

**Prevention:** Persist provider event time separately from received/fetched time
and source/feed. Enforce an explicit source-age bound, reject implausible future
times, out-of-order updates, missing/zero/crossed sides and unsuitable conditions.
Preserve Decimal decoding from raw numeric JSON rather than passing through
binary floats. Set freshness by the chosen quote semantics, not HTTP success.
For first-open execution, require a valid current-session observation; yesterday's
close must not become a fresh opening price. Repeated unchanged event timestamps
must not be refreshed artificially. Reduced trade availability is preferable to
manufactured freshness; evaluate that availability during the provider spike.

**Detection:** Poll age is always near zero while source timestamps lag; no test
has HTTP 200 containing an old quote; bar close is labelled current bid/ask.

**Phase:** Phase 7 acceptance spike, ingestion and execution. **Confidence:** HIGH
for timestamp distinction; MEDIUM for exact threshold until requirements approval.

### 4. A weekday timer is mistaken for exchange and instrument eligibility

**What goes wrong:** Trades execute on holidays, after an early close, during a
halt, or after waiting past the closing boundary. Conversely, closing stocks
accidentally disables 24/7 crypto.

**Evidence:** NYSE core sessions currently run 09:30–16:00 Eastern, with specified
holidays and 13:00 early closes. Nasdaq publishes its own holiday calendar.
[NYSE hours](https://www.nyse.com/trade/hours-calendars),
[Nasdaq calendar](https://www.nasdaq.com/market-activity/stock-market-holiday-schedule).
Instrument pauses and regulatory halts are separate from scheduled sessions.
[Nasdaq halt codes](https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltCodes).

**Prevention:** Use an authoritative date-specific calendar and
`America/New_York`, converting to UTC instants; never hardcode a UTC offset or
derive sessions from the VDS/user timezone. Define open-inclusive/close-exclusive
boundaries. Refuse new stock fills when calendar/status is unknown, stale,
halted or manually frozen. A fresh quote alone does not prove tradability.
Choose a usable halt/status source and outage policy before enabling stocks;
if unavailable, expose that unresolved limitation rather than promise halt
correctness. Closed orders are refused, not queued for tomorrow.

**Detection:** Tests cover ordinary Tuesday only; a cached `is_open` boolean
survives close; no date coverage expiry; stock status is a global trading flag.

**Phase:** Market-state foundation, execution and rollout. **Confidence:** HIGH
for exchange behavior; MEDIUM for status-source feasibility.

### 5. Whole-share orders are mistaken for a complete corporate-action policy

**What goes wrong:** A 2:1 split halves price while quantity remains unchanged,
apparently destroying half the portfolio. A reverse split leaves fractions that
cannot be sold; dividends reduce quoted price without corresponding cash; a
symbol change loses the holding's identity.

**Evidence:** Reverse splits can produce cash in lieu of fractional shares.
[Investor.gov reverse splits](https://www.investor.gov/introduction-investing/investing-basics/glossary/reverse-stock-splits).
Dividend entitlement depends on the event's dates, not simply holdings on the
payment day. [Investor.gov ex-dividend dates](https://www.investor.gov/introduction-investing/investing-basics/glossary/ex-dividend-dates-when-are-you-entitled-stock-and).
Alpaca's corporate-action API covers multiple event types but expressly does not
guarantee timely availability; default complete records may omit incomplete
announcements. [Corporate actions API](https://docs.alpaca.markets/us/reference/corporateactions-1).

**Prevention:** Make the owner choose the bounded policy before requirements
freeze. Recommended MVP: audited per-instrument freeze and controlled manual
reconciliation, with explicit operator responsibility, event identity,
effective time, idempotency, cash/basis effects and visible history. This still
requires reliable event monitoring; “we will notice eventually” is insufficient.
Automation may follow only where source/event coverage is established.
Never silently ignore actions, rewrite old fills or round away fractional
entitlements. Whole-share *order* rules need not imply integral post-action
holdings; choose residual/cash-in-lieu handling explicitly. Ordinary splits
preserve aggregate cost basis; allocations/distributions need event-specific
rules. Document whether performance includes dividends or excludes them under
an explicitly accepted limitation. These are proposed policies, not consent.

**Detection:** All fixtures have unchanged symbols/quantities forever; adjusted
prices are mixed with unadjusted holdings; corporate events are inserted as
fictional user buys/sells. Existing spike confirmation accepts a repeated
post-split price without repairing holdings.

**Phase:** Provider/policy gate, accounting foundation, portfolio and rollout.
**Confidence:** HIGH for event risks; MEDIUM for proposed MVP mechanism.

### 6. Parallel asset engines bypass the single cash lock and replay contract

**What goes wrong:** A crypto buy and stock buy both spend the same cash;
retries create another fill; a successful fill replay is refused because the
market is now closed; an order approved before close fills after a lock wait.

**Repository evidence:** `backend/app/services/trading.py` acquires the account
row lock before holding locks, looks up existing user-scoped idempotency keys
before price checks, and commits cash/holding/basis/fill atomically. Preserve
this contract for every asset class. A separate stock account is incompatible
with the approved single balance.

**Prevention:** Share account serialization and user-scoped replay across crypto
and stocks. Include stable instrument identity and complete order semantics in
replay matching. For a new fill, re-evaluate session, halt/freeze state and source
age after blocking locks and immediately before applying the write; avoid network
I/O while holding financial locks. A replay returns the immutable original fill
even after closure. Reject altered payloads using an old key. Prove whole-share
order validation server-side while preserving fractional crypto.

**Detection:** Concurrency tests exercise only stock/stock; idempotency keys are
unique per asset engine; eligibility is checked only at preview or request entry.

**Phase:** Shared trading foundation and stock execution. **Confidence:** HIGH
for existing contract; MEDIUM for proposed extension details.

### 7. Successful migrations silently break least privilege and exact recovery

**What goes wrong:** The app works as a test superuser, then production refuses
new tables or backups omit stock/accounting state. A dump succeeds but the
installed verifier rejects the new revision or verifies only crypto-era tables.

**Repository evidence:** `deploy/backup-manifest.sql` explicitly hashes nine
tables and crypto-specific columns; `deploy/backup-snapshot.py` and
`deploy/verify-restore.py` expect table/invariant sets;
`deploy/db/bootstrap-roles.sql` admits revisions 0007/0008 and grants explicit
table/sequence privileges. `Coin.kraken_pair`, price source constraints,
`Holding.coin_id` and `Trade.coin_id` encode crypto assumptions.

**Prevention:** Review these contracts in the same design as stock schema work.
Preserve existing IDs, fills and quantities through expand/backfill migration.
Version recovery manifests and supported schema contracts deliberately, with
compatible retained tooling. Prove old-data upgrade, mixed-asset exact restore,
restricted app/scheduler access, forbidden operations and rollback behavior
before release. No live role/tool replacement is implied by planning approval.

**Detection:** All grants come from a superuser fixture; backup success means only
archive creation; row hashes cover coins but no stock/event rows; migration
tests create empty databases only.

**Phase:** Schema/accounting foundation; mandatory rollout/recovery gate.
**Confidence:** HIGH from repository inspection.

## Integration, performance and UX gotchas

| Trap | Consequence | Prevention / detection |
|---|---|---|
| One provider call per browser or per symbol per request | Quotas fail even with a few users; web latency follows provider outages | One bounded scheduler, batch the 20 symbols, budget retries/status calls, respect 429/backoff; prove crypto refresh continues when stocks fail |
| One timestamp for combined portfolio | Closed stock values are mistaken for live values; a stock outage hides crypto performance | Per-instrument as-of/state; use last known stock valuation with explicit closed/stale status, never for a new fill; keep cash and missing-value semantics honest |
| Symbol used as durable identity | Rename or reuse attaches history to another security | Stable instrument IDs, explicit provider mappings, immutable execution identity; preserve inactive holdings/history |
| Crypto quantity UI reused without capability metadata | Fractional stock or dollar-total order slips through | Whole-share stock input and server rejection; crypto keeps existing dollar/fractional modes |
| Source bid/ask plus existing spread applied without policy | Unexpected double spread and misleading comparison | Decide stock reference/fee/spread policy, show preview totals, store actual reference and cost inputs |
| Provider key sent to the browser or generic arbitrary-symbol proxy exposed | Credentials or paid quota are consumed by outsiders | Server-only secrets, curated allowlist and bounded responses; never add real brokerage order endpoints |
| Overnight gap accepted as just another crypto spike | Legitimate opening gap remains stale or a split is accepted as ordinary movement | Session-aware reference handling and corporate-action freeze; never reset timestamps to bypass rejection |

## Acceptable debt versus unsafe shortcuts

| Shortcut | Disposition |
|---|---|
| Curated 20-stock catalog rather than search/universe ingestion | Appropriate confirmed MVP scope; review status/mapping changes operationally |
| One polling scheduler rather than streaming infrastructure | Appropriate if source age, coverage, quotas and rights meet the confirmed contract |
| Manual corporate-action reconciliation | Conditional on owner approval, monitoring, freeze and auditable/idempotent accounting; not permission to ignore events |
| No settlement/margin/order-book simulation | Appropriate simulator scope; do not imply brokerage-level execution fidelity |
| Personal license treated as redistributable, fresh fetch time replacing old event time, or ignored splits | Never acceptable substitutes for the approved core value |

## Looks done but is not: verification checklist

- [ ] Provider gate records permitted multi-user display, exact feed, free quota and actual source-age observations for all 20 symbols.
- [ ] An HTTP 200 carrying an old quote cannot execute; later-arriving old data cannot overwrite newer data.
- [ ] Open/close, early close, holiday, DST transitions, unknown calendar and halt/freeze cases are tested with controlled time.
- [ ] A queued-on-lock new request crosses close/age boundaries and is refused; successful replay still returns its original fill.
- [ ] A simultaneous crypto buy and stock buy cannot overspend the same cash; altered-key replay cannot target another instrument.
- [ ] Whole-share stock orders coexist with fractional crypto; stock closed state never closes crypto.
- [ ] Split, reverse-split residual, dividend entitlement and symbol-change fixtures match the explicitly approved policy.
- [ ] Historical fills remain unchanged after reconciliation; basis, cash and aggregate valuation reconcile exactly.
- [ ] Mixed-asset portfolio/history retain per-asset identity, provenance, age and deterministic pagination.
- [ ] Existing crypto database upgrades preserve balances/fills; restricted roles and exact mixed-state recovery pass before rollout.

## Recovery strategies

| Failure | Immediate containment | Recovery |
|---|---|---|
| Rights or feed eligibility unresolved | Keep stock production display/execution disabled; crypto continues | Establish permitted provider scope or return the explicit scope/budget decision to the owner |
| Stale data, bad calendar or status outage | Refuse new affected-stock fills; show last valuation honestly | Restore trustworthy source/state and require fresh valid-session data before reopening |
| Corporate action missed | Freeze instrument and affected accounting display where misleading | Snapshot/audit affected fills and holdings, apply reviewed compensating events under the selected policy; never silently edit old fills |
| Duplicate/incorrect fill discovered | Stop affected execution path | Reconcile cash/basis with audited correction; restore only under separately approved real-data recovery procedure |
| Recovery/role mismatch after migration rehearsal | Block release | Version/fix and replay isolated exact restore and least-privilege tests; retain original source/tool artifacts |

## Pitfall-to-phase mapping

| Responsibility | Prevents | Required evidence |
|---|---|---|
| **Phase 7: data/policy feasibility gate** | Unlicensed display, hidden delay, IEX/SIP confusion, undefined action/cost policy | Source/rights decision and explicit unresolved gates; owner dispositions rather than inferred acceptance |
| **Market-state and ingestion foundation** | Fabricated freshness, holiday/DST/early-close mistakes, halts, quota starvation | Time-controlled fixtures, invalid/stale/provider-failure tests and independent crypto continuity |
| **Shared schema/accounting and stock execution** | Lost cash serialization, fractional-order leakage, bad action reconciliation | Existing-data migration, real-Postgres mixed concurrency and replay tests; exact accounting fixtures |
| **Combined portfolio/history** | Wrong P/L, hidden closed values, identity and pagination loss | Mixed holdings/fills/actions with exact totals, per-price times and persisted identities |
| **Rollout/recovery acceptance** | Restricted-role failure, incomplete backup, unsafe rollback | Candidate upgrade, exact mixed-asset restore and app/scheduler permission proofs before approved deployment |

## Source confidence and open decisions

Primary provider, exchange and regulator pages above were checked on 2026-11-10.
Most operational pages do not give a durable publication date; preserve versions
of the applicable agreements/calendar at implementation time. Provider terms
and feature eligibility can change. No private account, key, live trade, provider
subscription or production configuration was accessed for this research.

Open decisions: permitted free multi-user feed; whether explicitly labelled IEX
coverage is acceptable; exact quote-age and session-state availability contract;
halt/status source; manual versus automated corporate actions and residuals;
dividend/performance treatment; stock reference spread/fees. Research establishes
risks and candidate mitigations, not owner approval of those choices.
