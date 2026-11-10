# Feature Research: v1.1 US Stock Trading

**Domain:** Virtual-money stock trading added to Birja's existing crypto simulator
**Researched:** 2026-11-10
**Confidence:** HIGH on exchange mechanics and confirmed scope; MEDIUM on the proposed MVP boundary; stock-feed feasibility and public display rights remain unresolved by this features research.

## Scope and evidence

The owner confirmed 20 curated NYSE/Nasdaq stocks, whole-share market orders,
one existing virtual USD balance, combined portfolio/history, and regular-session
trading only. Desired quote recency is comparable to crypto's roughly one-minute
refresh; a fifteen-minute delay was explicitly rejected. This document proposes
requirements for approval, not additional owner decisions.

NYSE's published core session is 09:30–16:00 Eastern Time. Its calendar and
Nasdaq's calendar include holidays and 13:00 early closes. Nasdaq explicitly
lists 27 November and 24 December 2026 as early closes. A Monday–Friday timer is
insufficient. [NYSE calendar](https://www.nyse.com/trade/hours-calendars),
[Nasdaq calendar](https://www.nasdaqtrader.com/Trader.aspx?id=Calendar).

Fractional shares are offered by some brokers under varying conditions;
whole-share orders are Birja's confirmed first-version choice, not a universal
claim about stock markets. [SEC fractional-share bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/fractional-share-investing-buying-slice-instead-whole-share).

## Feature Landscape

### Table Stakes

| Feature | Why expected | Complexity | Proposed acceptance outcome |
|---|---|---|---|
| Curated stock catalogue with stable identities | Tickers, exchange and asset class must be distinguishable | MEDIUM | Exactly 20 enabled common-stock instruments with name, display ticker, USD denomination, primary listing metadata and provider mapping; ambiguous/unknown symbols cannot execute |
| Stock and crypto discovery in the existing app | Users need to find both without confusing their rules | MEDIUM | Clear asset-class labels/filtering; stock closure never disables crypto |
| Timestamped, honestly described stock prices | Recent polling cannot repair delayed source data | HIGH | Show source event time and feed coverage; refuse missing, future, stale, malformed or nonpositive execution prices; never relabel a fifteen-minute feed as live |
| Server-owned regular-session admission | Browser clocks/buttons cannot enforce trading rules | HIGH | Stock buy and sell both reject outside the scheduled regular session, on holidays and after early close; decisions account for America/New_York DST |
| Per-symbol availability | An open exchange does not guarantee a stock can trade | HIGH | Known halt, suspended/inactive instrument or unresolved status blocks that stock; unknown status fails closed according to an approved validity policy |
| Whole-share buy/sell | Confirmed order model | MEDIUM | Positive integral quantities only, including direct API requests; fractional quantities and stock dollar-amount orders rejected; crypto fractional and dollar orders keep working |
| Explicit preview and exact fill | Cash changes must be understandable | HIGH | Server preview shows quantity, execution basis, all simulated costs, total debit/credit and quote time; changed inputs or market state cannot silently execute an obsolete preview |
| Shared cash with atomic execution | Stocks and crypto compete for the same money | HIGH | Concurrent cross-asset purchases cannot overspend; repeat idempotency key does not duplicate a fill; sell cannot exceed owned quantity |
| Combined portfolio with per-asset valuation status | Closed stocks are still owned | HIGH | Cash counted once; both asset classes included; market closure retains last-known stock marks with an as-of/closed label; missing marks make totals explicitly incomplete rather than silently zero |
| Immutable combined history | Historical stock trades must remain interpretable | MEDIUM | Existing keyset history includes asset type and exact stock fills/costs/time; old crypto rows retain meaning; corporate actions, if supported, are distinguishable from trades |
| Safe corporate-action boundary | Real share units can change without a trade | HIGH | A documented action/reconciliation policy prevents mixing pre-action quantities with post-action prices; unresolved affected valuations cannot appear complete |
| Safe rollout for existing accounts | Adding stocks must not reset or mutate prior outcomes | MEDIUM | No second starting balance, crypto holdings/trades/basis preserved, normal refresh/logout/relogin persists both asset classes |

**Proposed freshness contract:** target approximately 60-second collection and
consider the existing crypto execution bound of strictly less than 120 seconds
as the starting stock acceptance rule, subject to provider evidence and explicit
requirements approval. Separate source event age from fetch age. At reopening,
an old previous-session quote cannot be admitted merely because the clock says
open. Recheck session, availability and quote validity after database-lock waits
and immediately before a fill. A valid same-session quote must be available
before trading resumes. These are design recommendations; the user has not
chosen an exact stock age bound.

**Halt feasibility:** Nasdaq publishes a free halt RSS feed for Nasdaq-listed and
other exchange-listed securities and asks consumers to query no more than once
per minute. It is a candidate input, not proof of complete instantaneous halt
detection. Its terms and actual coverage/status history must be validated before
selection; a fresh empty response must not automatically clear a previously
known halt. Define an outage/recovery policy and a way to suspend all stock
admission for emergency exchange closures. [Feed documentation](https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS),
[feed terms](https://www.nasdaqtrader.com/content/administrationsupport/agreementstrading/THRSSFeedTermsCond.pdf).

### Differentiators

| Feature | Value | Complexity | Disposition |
|---|---|---|---|
| One virtual account across stock and crypto | Teaches trade-offs using the same finite cash | MEDIUM | Confirmed core value; include now |
| Explain why a stock cannot trade, with next session when known | Helps friends understand US market hours | LOW–MEDIUM | Include a concise reason; do not promise reopening during unknown status |
| Honest feed/mark explanations | Prevents mistaken confidence in exchange-wide or real broker execution | LOW | Include minimal source/as-of and simulated-fill wording |
| Asset-class allocation summary | Makes the combined portfolio easier to read | LOW–MEDIUM | Optional enhancement after required combined holdings work |
| Watchlists, charts, company fundamentals | Richer exploration | MEDIUM–HIGH | Defer; unrelated to the confirmed trade loop |

### Anti-Features / Explicit Exclusions

| Feature | Why avoid in v1.1 | Alternative |
|---|---|---|
| Real brokerage accounts, funding or order routing | User asked for a simulator extension | Virtual fills only |
| Margin, shorts, options, ETFs, OTC shares, multiple currencies | Adds products/accounting not requested | USD common-stock curation |
| Limit/stop orders or orders queued overnight | Requires order lifecycle/matching and changes closed-market semantics | Refuse closed orders; user retries when open |
| Premarket, after-hours, overnight trading | Owner explicitly wants closure with the regular session | Regular session only even if a provider publishes extended-session ticks |
| Fractional stock orders/dollar buys | Conflicts with confirmed whole-share order scope | Quantity orders; display estimated cost |
| Full consolidated order-book/queue/slippage simulator | No confirmed licensed depth or need at friend scale | Label deterministic fills as simulation |
| A global “market closed” toggle for every asset | Would break crypto's independent availability | Per-asset admission and status |
| Silently reusing crypto's spread/fee as stock reality | Existing costs are a simulation setting, not a stock-market rule | Obtain explicit stock-cost policy and show it in preview |
| Ignoring splits while claiming correct holdings/P&L | Can manufacture catastrophic fictitious losses/gains | Reconcile or quarantine affected marks and trading |
| Selecting a paid feed or silently relaxing freshness | No such authorization | Resolve feasibility with the owner before locking requirements |

## Stock Accounting: Mandatory Decisions, Bounded Implementation

Corporate-action handling is not implied consent to a full brokerage system.
Its *safety boundary* is a launch requirement; the automation level and income
simulation are scope choices that need approval.

### Splits and reverse splits

A forward split changes share count and per-share basis while preserving total
basis, absent other consideration. Reverse splits may create fractional
entitlements even when every purchase was a whole-share order, and some issuers
pay cash instead. Real event terms govern treatment. [IRS split/basis FAQ](https://www.irs.gov/faqs/capital-gains-losses-and-sale-of-home/stocks-options-splits-traders/stocks-options-splits-traders-7),
[SEC reverse-split explanation](https://www.investor.gov/introduction-investing/investing-basics/glossary/reverse-stock-splits).

**Recommended minimal safe option:** verified operational monitoring of the 20
instruments plus an explicit instrument quarantine/reconciliation workflow.
Disable affected fills and suppress completeness of affected marks before the
event becomes effective; reconcile units and basis exactly once before reopening.
Document evidence, effective time and reconciliation outcome. This can avoid
building a fully automated corporate-action service, but only if an enforceable
monitoring/reconciliation owner and procedure exist. A vague promise to “handle
splits later” is insufficient for ongoing held positions.

For example, after a verified 2:1 split, 3 shares with $300 aggregate basis become
6 with the same $300 aggregate basis; original executed trades stay unchanged.
A reverse split yielding a nonintegral quantity must remain quarantined until
an approved entitlement/cash-in-lieu policy resolves it. Do not round away value
or assume it grants fractional order permission. Cash-in-lieu valuation and
associated basis allocation require authoritative event terms and an audit
record; unsupported mergers, spin-offs, delistings and ticker changes use the
same safe quarantine boundary rather than invented conversions.

### Dividends and return semantics

Dividend entitlement depends on ownership before the ex-date; receiving shares
after the ex-date does not create entitlement. Cash payment has a separate
payable date, and an ex-dividend price adjustment can affect measured
performance. [SEC ex-dividend explanation](https://www.investor.gov/introduction-investing/investing-basics/glossary/ex-dividend-dates-when-are-you-entitled-stock-and).

Choose explicitly between:

1. **Price-return-only first version (recommended for smallest scope):** no
   dividend credits; disclose prominently that simulated stock performance
   excludes dividends and is not total return. Do not change existing “total
   account value” meaning, but clarify the return limitation. Ordinary dividends
   are not automatically additions to the holding's acquisition basis.
2. **Ordinary cash dividends now:** snapshot qualifying holdings at the approved
   entitlement boundary, persist each entitlement, and credit shared cash once
   on the payable date even if the shares were subsequently sold. Add separate
   income records and include that cash in account performance. Corporate event
   corrections must not double-credit. Defer reinvestment, tax lots, withholding
   and return-of-capital cases unless specifically scoped.

Option 1 changes educational realism and therefore needs owner acceptance.
Neither option permits ignoring a share-unit-changing action.

### Execution costs and settlement

The existing defaults in `backend/app/core/config.py` are a 0.25% simulated
spread each side and a 0.25% fee with a one-cent minimum. Current
`backend/app/services/trading.py` passes them into shared trade math. Do not
apply these to stocks by accident when adding an asset type.

Recommend retaining transparent *configurable simulated stock costs* rather than
claiming real broker fees. Ask whether to retain the crypto-like settings or
use a different/zero-commission stock policy; a zero commission does not by
itself establish a zero market spread. Quote source selection must define
whether the reference is a bid/ask midpoint, last eligible trade, or bar close.
Never call a last trade “mid” without supporting bid/ask data.

Real market orders do not guarantee the displayed price. Birja's server preview
and atomic fill remain a disclosed simulation rather than an exchange execution
promise. [SEC order-execution guidance](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/executing-order).

**Proposed deferral requiring clear disclosure:** retain immediate simulated cash
availability after a sell; do not add settled/unsettled cash restrictions in
this milestone. This is a simulator simplification, not a statement that real
brokerage settlement is immediate.

## Dependencies and Vertical Workflows

```text
Licensed feed + coverage/timestamp decision + 20 instrument mappings
    -> calendar/availability + quote validation
    -> whole-share preview/fill using shared locked cash
    -> combined valuation and stored history
    -> live acceptance + ongoing corporate-action operations

Corporate-action and stock-cost scope decisions
    -> execution and performance semantics
    -> money invariants, action boundary and acceptance cases
```

| Workflow | Minimum testable outcome |
|---|---|
| First stock trade | Existing account buys one share while open using unchanged USD balance; exact cash, quantity, costs and basis match history and portfolio after refresh |
| Cross-asset contention | Concurrent crypto/stock orders serialize on the shared account; no overspend or duplicate fill |
| Closed market | Existing stock holdings and historical marks remain visible, stock orders fail server-side, crypto still trades using its own freshness rules |
| Open/close race | Preview before close, execution after close or after a lock wait cannot fill; holiday/early-close/DST boundary cases covered |
| Bad or unavailable data | Provider outage, stale/future tick, unknown trading status or halt blocks affected stock fills without falsifying healthy crypto/other holdings |
| Split safety | Event quarantine prevents inconsistent marks; approved reconciliation preserves aggregate basis and cannot apply twice; fractional reverse-split residual stays blocked pending decision |
| Account persistence | No second $10k grant; existing crypto and stock history remain correctly paginated across relogin and migration |

## MVP Definition and Prioritization

**P1 for v1.1:** free-feed/public-display feasibility gate; approved stock-cost,
corporate-action and return semantics; 20 mapped common stocks; timestamped
prices; calendar/status admission; integral quantity preview/fill; shared-cash
concurrency; combined portfolio/history with honest closed/incomplete marks;
focused cross-asset regression and real-session acceptance.

**P2 after validation:** additional catalogue filters, class allocation summaries,
automated reconciliation for a narrow supported event set if manual operations
prove burdensome.

**Defer:** extended hours, fractionals, advanced orders, broker-grade routing,
settlement restrictions, dividend reinvestment, tax reporting and broad product
expansion. The owner must accept any omitted-income/settlement simplifications.

**Curation policy:** select 20 active, widely traded USD common stocks with
provider coverage and both requested primary listing venues represented; verify
listing/security type using authoritative metadata at implementation time.
Avoid one-time hardcoded claims about liquidity or current venue. This research
does not prescribe an investment list; the owner's list or a separately verified
candidate list can be chosen during catalogue planning.

## Decisions Needed Before Requirements Approval

1. Can a free feed legally support this public multi-user app at the requested
   freshness and coverage? If not, ask the owner which constraint changes; do
   not quietly choose fifteen-minute data or pay for access.
2. Approve an exact quote-age/reference-price contract after provider research.
3. Choose simulated stock fee/spread settings; do not inherit crypto defaults
   by accident.
4. Approve minimal monitored corporate-action quarantine/reconciliation, or
   scope automated supported actions. Who performs monitoring and correction?
5. Accept price-return-only without dividend credits, or include ordinary cash
   dividends with entitlement/payment accounting now?
6. Accept immediate simulated sale-proceeds availability while deferring real
   settlement restrictions?

## Confidence and Gaps

Exchange session/calendar, broker fractional-share variability, split/basis and
dividend mechanics above are HIGH confidence primary-source findings. Proposed
simulator boundaries and prioritization are MEDIUM confidence product judgments
subject to owner approval. Free quote entitlements, commercial/public display
permissions, halt-feed reuse and complete corporate-action data are open
feasibility checks, not verified capabilities. Sources were accessed 2026-11-10;
exchange calendars, listing metadata and feed terms require rechecking before
release. No dependencies were installed and no private services were queried.
