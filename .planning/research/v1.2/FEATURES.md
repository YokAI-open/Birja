# Feature Research

**Domain:** Private strategy portfolios in Birja's virtual-money investing simulator
**Milestone:** v1.2 — Multiple Strategy Portfolios
**Researched:** 2026-11-14
**Confidence:** HIGH for confirmed scope and current-code findings; MEDIUM for proposed product refinements pending requirements approval.

## Scope and Evidence Boundary

The owner explicitly confirmed ten active named portfolios per user, an
independent once-only $10,000 grant for each new portfolio, isolated activity,
an overview showing cash/value/return, and confirmed deletion even with holdings
or when deleting the last portfolio. The existing user's actual financial state
must become their first portfolio without another grant. Deleted portfolios
leave normal screens while their financial records are retained. These are
approved goals; this research does not constitute implementation approval.

The owner chose the simple overview rather than performance-over-time charts.
Transfers, resetting an existing portfolio, social features, real brokerage
orders and additional asset classes are outside this milestone. The original
single-account grant/no-reset policy is intentionally refined: each new
portfolio gets a grant once, and deletion followed by creating a new strategy is
allowed. Neither deletion nor renaming resets a retained portfolio's ledger.

Stocks and crypto share cash **within** each portfolio. Across portfolios, cash,
holdings, History and performance are independent. Six Phase 7 requirements stay
deferred/unverified in [DEFERRED.md](../../DEFERRED.md); live stock activation
and any production rollout remain separate. Local stock feature verification
can use the existing isolated synthetic fixtures.

## Feature Landscape

### Table Stakes (Required to Deliver the Confirmed Goal)

| Feature | Why Expected | Complexity | Notes / acceptance implication |
|---|---|---|---|
| Private named portfolio list and creation, up to ten active | Users must distinguish the strategies they are trying | MEDIUM | Names are labels; immutable portfolio identity remains separate. Creation retry/concurrency cannot duplicate the intended starting grant or exceed the active limit. |
| Independent $10,000 starting cash | Experiments must begin independently without splitting old money | HIGH | Store each portfolio's own initial baseline; opening, refreshing, renaming, logging in or retrying creation must not grant another $10,000. |
| Explicit selected-portfolio context throughout trading | Users must know which strategy an order affects | HIGH | Identify the target portfolio on the ticket, preview and receipt; bind confirmation to that target. Switching context cannot submit an old preview against a new portfolio. |
| Independent mixed-asset holdings, cash, fills and History | Strategies must not share financial effects | HIGH | Existing crypto behavior, stock whole-share/ask-bid rules and activation gates continue inside each portfolio. Reusing a ticker across portfolios does not combine quantities or cost basis. |
| Per-portfolio dividends, splits and correction effects | Cash and performance must remain attributable to the strategy that earned them | HIGH | One instrument event may affect several portfolios; each gets only its own entitlement/effect once. Historical ownership must not be rebuilt from another portfolio's positions. |
| Overview showing each active portfolio's cash, value and return | The owner explicitly wants to compare strategies | MEDIUM | Use the same server-authoritative valuation semantics as the detail page. A row with an unvalued holding remains incomplete, rather than looking like a loss or a zero-valued strategy. |
| Open a portfolio for detail, trading and History | The overview must lead into the existing investing loop | MEDIUM | The selected name stays visible. Portfolio-specific links and browser navigation must preserve the target, rather than depend only on a mutable global selection. |
| Confirmed deletion with holdings allowed | The owner explicitly approved ending an experiment without liquidating it | HIGH | Hide/deactivate the strategy, retain financial rows, block further ordinary access/trades; do not manufacture sales, move cash to another portfolio or rewrite past fills. |
| Zero active portfolios is a valid signed-in state | Deleting the last portfolio is approved | MEDIUM | Show an empty overview with Create portfolio; account sign-in/sign-out and market browsing must still work. Viewing or signing in must not silently recreate/grant a portfolio. |
| Migration into one first portfolio | Existing users must keep their current experience and data | HIGH | Preserve actual cash, stored starting_cash, quantities/basis, event ownership, receipts and immutable history. No reset to $10,000 and no extra grant. |
| Owner and active-state checks for every portfolio operation | Users expect privacy and deletion to be effective | HIGH | A guessed ID, stale tab, old History cursor or direct event-reference link must not reveal another owner's or deleted portfolio's financial data. |

### Proposed Minimal Refinements (For Requirements Approval)

These are recommended defaults, not additional owner decisions already made.
They make the agreed lifecycle understandable without adding another product.

| Refinement | Recommendation | Reason / validation |
|---|---|---|
| Rename | Let the owner rename an active portfolio without changing its cash, baseline, identity or History | Strategy names naturally evolve; this is a small management action, not a reset. |
| Name validation | Require a trimmed, nonblank Unicode label of 1–60 characters; reject control characters; show inline errors | Names must wrap safely in overview, selector, ticket and delete confirmation. Exact length can be settled in phase UI/API contracts. |
| Duplicate names | Reject duplicate active names for the same owner using a documented normalization rule; allow reuse after deletion and the same label for different users | Identical strategy names make target confirmation ambiguous. Identity/authorization must still use IDs, never the name. This is a proposed policy, not a finding about an existing constraint. |
| First-portfolio label | Name the migrated portfolio “My portfolio” and allow renaming | A plain label identifies existing data without inferring a strategy. |
| New-user onboarding | Preserve today's immediate first-portfolio experience for a newly created user; its initial grant belongs to that first portfolio | Distinguish brand-new onboarding from an existing user who intentionally deleted every portfolio. Never auto-create on every login. |
| Stable overview order | Default to creation order with a unique tie-breaker, rather than automatically sorting by changing value | Ten strategies are easy to scan; stable positions avoid accidental target selection and do not imply a fair ranking across different start dates. |
| Overview refresh | Value the rows using a coherent server valuation point and expose time/completeness | Detail and overview should agree under the same inputs. Do not calculate financial totals or returns from rounded UI numbers. |
| Successful deletion destination | Return to overview, explicitly clear the deleted selection and announce success | A stale selected ID must not remain usable; zero active portfolios naturally uses the same destination. |
| Cancel / delete failure | Cancel leaves the strategy untouched; failure keeps the target visible with retry feedback | Do not pretend deletion succeeded or silently select another strategy while a destructive request is unresolved. |
| Deleted tab / old link | Show that the portfolio is unavailable and offer the overview/create action; do not silently redirect an order to a survivor | A stale tab must never spend another strategy's money. Cancel/ignore late data for the old target. |
| Repeated delete | Make a retry safely converge on unavailable/deleted without touching other portfolios | This is the observable consequence of safe deletion, not an instruction to disclose private tombstones. |

No major new owner decision is necessary before drafting requirements: the
defaults above can be presented as part of the full requirement list. If the
owner does not want renaming, the naming restriction or automatic first-portfolio
onboarding for brand-new users, revise those small refinements during that gate.

### Differentiators (Already Within the Confirmed Scope)

| Feature | Value Proposition | Complexity | Boundary |
|---|---|---|---|
| Equal fresh funding for independent experiments | Users can test a new approach without consuming another strategy's capital | HIGH | $10,000 per new strategy is fixed; no configurable deposits or leverage. |
| Mixed crypto/stock strategies under the same semantics | Compare strategies using existing assets, costs and exact History | HIGH | Live stock prerequisites are unchanged; a new portfolio is not a bypass. |
| Honest incomplete comparison values | Users can distinguish unavailable prices from poor performance | MEDIUM | Show known value/incompleteness and withhold overall return when it cannot be calculated. |
| Deletion without fake liquidation | Users can end an experiment without altering their recorded fills | HIGH | Retained bookkeeping is private and excluded from ordinary screens/active totals; no in-app restoration promised. |

### Anti-Features (Scope and Safety Boundaries)

| Feature | Why Requested | Why Problematic Here | Alternative |
|---|---|---|---|
| Cross-portfolio cash or asset transfers | Rebalance capital between strategies | Adds flows and complicates return baselines beyond approved independent funding | Create an independently funded strategy; keep each strategy's cash closed. |
| Reset an existing portfolio | Retry a failed approach | Rewrites the same strategy's baseline/history and conflicts with retained records | Delete and create a new portfolio with a new identity. |
| Forced sale on deletion | Clear holdings before removal | Introduces artificial fills, market-closed dependencies and potentially unavailable prices | Delete with holdings; keep retained financial rows. |
| Automatic fallback portfolio for an in-flight order | Keep an order working after switch/delete | Can execute the user's intended experiment in another strategy | Preserve/reject the original target; require a fresh target-specific preview. |
| Destructive physical ledger deletion | Make the database look like the normal UI | Loses financial provenance, entitlement/correction links and retry protections | Remove ordinary access while preserving immutable financial records. |
| Historical charts, annualized returns or strategy leaderboard | Richer comparisons | Requires extra snapshots and comparison policy; owner chose a simple overview | Current cash/value and dollar/percent return against each stored baseline. |
| Automatic restore/trash browser/export features | Recover deleted experiments | Adds new access and lifecycle promises outside the confirmed scope | Clear confirmation; retain internal records for integrity/recovery without a normal deleted-portfolio screen. |
| Treat all portfolios as account-wide wealth | A larger account total appears convenient | Repeated independent virtual grants and hidden deleted books are not a single capital pool | Show each active strategy separately; do not introduce a cross-portfolio money total. |

## Feature Dependencies

```text
Owner + persistent portfolio identity + active/deleted lifecycle
    -> per-portfolio starting grant + limit + migration
    -> scoped cash/holdings/trades + target-specific retry behavior
    -> scoped historical ownership/dividends/splits/corrections/History
    -> coherent detail valuation and multi-portfolio overview
    -> create/open/rename/delete/empty-state UI
    -> migration, deletion-race, browser-isolation and exact recovery acceptance
```

Deletion and UI context cannot be treated as a cosmetic final step: trading,
corporate-action accounting and read paths all need the same lifecycle semantics.
The old ownership/event data must be assigned to its first portfolio before new
strategies coexist. Restore proof must retain both active and deleted portfolio
identities; otherwise a restored database can resurrect hidden strategies or
grant their starting cash again.

## Product Semantics to Preserve

1. **Actual baseline, not hard-coded comparison money.** New portfolios begin at
   $10,000, but migration preserves each original stored `starting_cash`. Display
   total value and dollar/percent return against that portfolio's own baseline.
   Label it as return since that strategy began, not a time-normalized ranking.
2. **Cash shared across assets, isolated across strategies.** Dividend proceeds,
   a crypto sale or a stock sale become spendable only within the portfolio that
   received them. A duplicate event/retry cannot credit its siblings.
3. **Truthful valuation.** Existing fresh/closed/halted/unavailable stock marks,
   IEX attribution, timestamps, incomplete totals and crypto behavior carry into
   both detail and overview. One incomplete strategy need not hide another's
   complete numbers, but it must not be ranked or summarized as zero.
4. **Deleted means unavailable in normal investing flows.** No new fill may
   execute against a deleted portfolio. A delete-versus-fill race must have a
   clear ordering: a fill that won is retained in that portfolio; deletion never
   redirects it. Retained background reconciliation must remain associated with
   that same hidden book and cannot change another active portfolio's cash.
   Whether particular post-deletion internal events are frozen or reconciled
   needs a precise accounting design; it does not require a new visible feature.
5. **Selection is user context, not authority.** Every object operation is checked
   server-side. Clear/reset portfolio-bound forms, previews and paginated data
   when the target changes; keep any unresolved original attempt attached to its
   original target and never turn it into a new portfolio's order.
6. **The ten-portfolio cap is active-only.** Deleted retained books do not occupy
   active slots, but deletion/recreation does not imply unbounded background job
   cost is harmless. Preserve ordinary rate-limit/resource controls; do not add
   an unapproved lifetime creation limit that defeats the confirmed strategy loop.

## MVP Definition and Prioritization

| Priority | Feature category | User Value | Implementation Cost | Scope |
|---|---|---|---|---|
| P1 | Existing-data migration and independent funding/lifecycle | HIGH | HIGH | Confirmed; prerequisite for all other flows |
| P1 | Isolated trading, ownership/event accounting and private History | HIGH | HIGH | Confirmed; preserve existing financial guarantees |
| P1 | Portfolio list, create/open, overview, clear selected context | HIGH | MEDIUM | Confirmed; name validation/rename are proposed refinements |
| P1 | Delete including holdings/last portfolio, empty and stale-target states | HIGH | HIGH | Confirmed; privacy and race behavior necessary |
| P1 | Exact active/deleted recovery and local acceptance | HIGH | HIGH | Required preservation of existing operational guarantees |
| P3 | Historical comparisons, transfers, configurable funding, cloning strategies, restore UI | MEDIUM | HIGH | Deferred / outside confirmed milestone |

Launch v1.2 with the confirmed management and isolated investing loop. Do not
introduce a charts phase, transfer ledger, new market feed or a provider campaign.
New roadmap numbering starts at Phase 12; Phase 7 remains separately deferred.

## Product Reference Check

TradingView's official Paper Trading account manager describes account-specific
positions/orders/History and a summary of account metrics. This supports the
familiar pattern of choosing an investing context and seeing its own activity.
It does **not** establish a ten-account quota, a name/deletion rule or Birja's
funding policy; those are owner decisions and recommendations documented above.
[Official account-manager documentation](https://www.tradingview.com/support/solutions/43000786138-what-is-the-account-manager/).

No competitor quota or deletion behavior was needed to justify the confirmed
scope, and no unsourced competitor behavior is claimed.

## Existing Repository Evidence

Read-only source evidence at the v1.2 planning base:

- `backend/app/services/accounts.py:10–38`: one account grant currently occurs
  during new-user insertion; `get_me` currently joins the account and exposes
  account cash. Deleting the last strategy must not break authenticated identity
  or trigger a replacement grant.
- `backend/app/models/user.py:33–46`: account cash and starting cash are currently
  one-to-one with user. `backend/app/models/trade.py:27–51`: holding uniqueness
  and trade idempotency/history indexes are currently user-scoped. These are real
  financial boundaries, not merely a list of UI cards.
- `backend/app/api/v1/portfolio.py`: today's single `/portfolio` response is
  authenticated and uses server valuation. `backend/app/services/portfolio.py`
  selects account cash/holdings by user; the overview needs scoped equivalents.
- `backend/app/services/portfolio_math.py:70–136`: performance uses stored starting
  cash, nullable complete totals and known value. Preserve these semantics.
- `frontend/src/App.tsx`: current navigation and routes expose one Portfolio and
  History; trade routes identify the symbol without a portfolio target.
- `frontend/src/pages/PortfolioPage.tsx`: existing UI already explains incomplete
  known value and unavailable overall P/L, displays starting cash and IEX labels.
- `frontend/src/hooks/usePortfolio.ts`, `useHistory.ts`, `useEventHistory.ts`:
  current caches are single-portfolio/user scoped; `useStockTrade.ts` also holds
  unresolved attempt/recovery state. Portfolio changes must isolate these views
  and attempts rather than simply replacing one cash label.
- `design-system/birja/MASTER.md`: existing card/table/mobile, visible-label,
  focus, money-formatting, empty-state and single-primary-action patterns apply.

## Standards and Documentation Sources

All external sources below were accessed on 2026-11-14. Official documentation
is used because no Context7 tool is available; no fallback package was installed.
These sources establish mechanics and accessibility/security expectations;
recommendations applying them to Birja are explicitly inferences.

- **W3C WCAG 2.2 SC3.3.4 understanding:** important data-changing/deleting flows
  need an appropriate error-prevention mechanism. Birja's approved confirmation
  is the fitting mechanism here; it should identify the named portfolio and
  consequence, with a clear cancellation path.
  [Error prevention](https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-legal-financial-data.html).
- **W3C ARIA APG alert dialog:** action confirmation can use an accessible modal
  with a programmatic name/description and genuine modal behavior. Use the
  existing component system and verify keyboard/focus behavior in phase UI work.
  [Alert dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/alertdialog/).
- **OWASP API Security Top10 API1:** each ID-addressed object operation needs
  authorization for the requested object. Apply ownership and active-state
  checks to detail, rename, delete, trade, History/cursor and original-event reads.
  [Broken object-level authorization](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/).
- **TanStack Query v5 query keys:** cache identity must distinguish the data
  requested. Infer that both session/owner and portfolio identity belong in
  financial query keys; a selector label is insufficient isolation.
  [Query keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys).
- **Local UI skill search:** `destructive action confirmation --domain ux`
  returned confirmation-dialog and success-feedback matches; `empty state create
  action --domain ux` returned empty-state, active-context and deep-linking
  guidance. Results fit this existing React dashboard. They are local guidance,
  not an external conformance proof or replacement design system.

## Confidence and Remaining Questions

| Area | Confidence | Reason |
|---|---|---|
| Approved goals and exclusions | HIGH | Explicit owner scope confirmation recorded in PROJECT.md |
| Current single-portfolio assumptions | HIGH | Direct source inspection; no live data or services read |
| Context, confirmation and privacy behavior | HIGH | Existing code/design evidence plus official W3C/OWASP/TanStack sources |
| Name/rename/duplicate/default-order/onboarding refinements | MEDIUM | Reasoned recommendations for requirements approval, not prior decisions |
| Detailed deletion versus late corporate-action accounting | MEDIUM | Required invariant is clear; precise retained-book lifecycle belongs in architecture/phase research |

No new external provider capability is required by the portfolio-management
feature itself. This does not resolve or weaken any existing stock activation
condition. No application files, packages, deployment, provider accounts or
historical research files were changed for this research.

---
*Feature research for Birja v1.2; scoped to the confirmed multiple-strategy milestone.*
