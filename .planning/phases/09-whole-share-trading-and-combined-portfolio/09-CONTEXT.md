# Phase 9: Whole-Share Trading and Combined Portfolio - Context

**Gathered:** 2026-11-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Enable safe whole-share stock buys and sells against the existing shared USD
account, and present truthful combined stock/crypto holdings. Cover MKT-02,
STKTR-01 through STKTR-06, PORT-06 and PORT-07. Preserve crypto behavior and
integrate Phase 8 monitoring, suspension, action ordering and historical
eligibility capture before the first stock fill.

This discussion authorizes context capture, not implementation, live activation,
provider calls, production changes or publication. Phase 7 live-data evidence and
Phase 8 live action activation remain owner-deferred. Isolated work may continue;
fixtures do not establish actual product access, rights or live readiness.

</domain>

<decisions>
## Implementation Decisions

### Stock trade ticket

- **D-01:** Use an editable positive whole-share quantity input with Buy max and
  Sell all shortcuts. Shortcuts populate quantity only; preview and explicit
  confirmation remain required. No stock dollar-input or fractional quantities.
- **D-02:** Show both IEX bid and ask; highlight the execution side selected by
  Buy/Sell. Buy uses ask and sell uses bid, with zero stock commission and no
  simulated added spread. Preserve existing crypto spread/fee/input behavior.
- **D-03:** If the relevant executable price changes, show old → new price and
  the change in total in a renewed preview. Require another confirmation.
- **D-04:** After a fill, stay on a receipt showing the persisted result and
  updated cash/share balance. Offer Portfolio and Trade again actions.

### Combined portfolio

- **D-05:** Use one combined holdings list with explicit stock/crypto labels,
  one shared cash balance and one portfolio summary.
- **D-06:** Default to alphabetical ticker order, stable as prices refresh.
- **D-07:** Show quantity, average cost, cost basis, current value, gain/loss
  and allocation directly. Use a desktop table and stacked mobile cards.
- **D-08:** Allocation panel summarizes Cash / Stocks / Crypto. Individual
  holding percentages remain in the holdings list when valuation is complete.

### Closed or unavailable valuations and trade controls

- **D-09:** When any holding cannot be valued, headline reads
  “Known value: $X — incomplete” and shows the unvalued holding count. Known cash
  and individual known values remain visible. Overall gain/loss and allocation
  percentages are unavailable while the total is incomplete; never treat an
  unpriced holding as zero or present a subtotal as a complete portfolio total.
- **D-10:** For a verified trading halt without corporate-action uncertainty,
  retain the last verified price with its actual timestamp and a prominent
  “Halted” label. Orders remain blocked. This is a historical mark, not a fresh
  executable quote. Missing trustworthy marks remain unavailable; uncertain
  corporate actions override retained marks and make valuation unavailable.
- **D-11:** While a stock is closed or temporarily unavailable, allow editing
  whole-share quantity, disable confirmation and explain the reason. The input
  is only a draft; no order is queued. Require a fresh preview once trading is
  available. Unsafe quote-dependent estimates remain suppressed.
- **D-12:** If closure or a hold interrupts review, retain typed quantity but
  invalidate the preview. Require a fresh preview and explicit confirmation;
  nothing executes automatically when availability returns.

### Carry-forward requirements

- **D-13:** Keep visible IEX single-venue attribution and simulation disclosures
  on the stock journey, including omitted regulatory fees and immediately
  reusable virtual sale proceeds rather than real settlement restrictions.
- **D-14:** Regular sessions only, with authoritative holidays/early closes/DST;
  no fills on closed, halted, frozen, unknown or stale eligibility. Source quote
  age must be strictly below 120 seconds. Recheck after blocking database waits.
- **D-15:** Shared-cash concurrency must prevent overspending across assets.
  Preserve original starting cash; no second grant. Exact idempotent replay must
  return the original fill even after close, and changed payloads must conflict.
- **D-16:** Eligible stock marks use midpoint; closed marks retain actual dates.
  Corporate-action uncertainty makes values unavailable. Phase 10 dividend cash
  must enter portfolio cash once when enabled; Phase 9 does not publish payments.

### Agent's Discretion

No explicit “you decide” preferences were given. Research/planning should choose
technical details, exact copy, responsive breakpoints and safe quantity shortcut
calculations within these decisions and the existing design system. A retained
draft is not a pending order and does not weaken auth/cache isolation or preview
expiry. Do not add persistent drafts, new dependencies or unrelated features
merely to implement these preferences.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and shared rules

- `CLAUDE.md` — shared architecture, Decimal precision, migrations, tests and git gates.
- `AGENTS.md` — Codex workflow and UI adaptations.
- `.planning/PROJECT.md` — approved v1.1 scope and policy decisions.
- `.planning/REQUIREMENTS.md` — the nine Phase 9 requirement IDs and boundaries.
- `.planning/ROADMAP.md` — Phase 9 goal, dependencies, five success criteria and activation gates.
- `.planning/STATE.md` — current progress and deferred activation evidence.

### Existing trading, action and design contracts

- `.planning/milestones/v1.0-phases/04-trading/04-CONTEXT.md` — established crypto behavior to preserve.
- `.planning/phases/07-permitted-stock-discovery/07-ACTIVATION.md` — quote permission attestation and deferred actual live evidence; no new campaign inferred.
- `.planning/phases/08-corporate-action-safe-ownership/08-VERIFICATION.md` — verified local action/ownership guarantees and first-fill integration obligations.
- `.planning/phases/08-corporate-action-safe-ownership/08-ACTIVATION.md` — separate unverified action rights and disabled live activation.
- `design-system/birja/MASTER.md` — established visual system; preserve it.

No new external specification was supplied during this discussion. Provider rights
and live coverage must not be inferred from this context.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `frontend/src/pages/TradePage.tsx` — crypto preview/confirm/result flow,
  changed-price handling and uncertain-outcome idempotency behavior.
- `frontend/src/api/trades.ts` — exact monetary-string parsing and API boundaries.
- `frontend/src/pages/PortfolioPage.tsx` and
  `frontend/src/components/PortfolioHoldings.tsx` — portfolio summary and holding
  presentation to extend with the chosen combined table/cards.
- Existing StockSection, StockAttribution, useStocks and stock API modules —
  catalogue-first display, IEX labels and independent session/quote/action facts.
- `backend/app/schemas/portfolio.py` — nullable valuation/P&L/allocation values,
  completeness and source timestamps already express honest unavailable states.

### Established Patterns

- TanStack Query handles server state; preserve auth/generation isolation,
  conservative quote deadlines and Phase 8 epoch protections.
- Server Decimal/NUMERIC calculations, JSON monetary strings, atomic DB changes
  and persisted receipts remain authoritative. UI formatting is not accounting.
- Reuse existing light theme, self-hosted Inter and accessible components.
- Preserve stock instrument → account/holding lock order and existing crypto
  account → holding order; research actual cross-asset concurrency implications.

### Integration Points

- Connect stock execution to Phase 8 ownership journal, monitor health,
  suspension/reconciliation rules and action ordering before any stock fill.
- Extend shared cash/holdings and portfolio valuation without a parallel account
  or independent starting grant. Keep crypto execution independently available.
- Research safe retained-mark semantics and migration/recovery/role compatibility
  with existing schema contracts. Final mixed-asset rollout acceptance is Phase 11.

</code_context>

<specifics>
## Specific Ideas

- Explicit old → new price/total comparison during mandatory re-confirmation.
- Receipt remains visible after execution, with Portfolio / Trade again actions.
- Incomplete headline: “Known value: $X — incomplete”, plus unvalued holding count.
- Allocation summary: Cash / Stocks / Crypto; stable alphabetical holdings.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. Existing future-phase boundaries
remain: dividend cash and public event History in Phase 10; exact mixed-asset
recovery and final acceptance in Phase 11. Live-data review/activation remains
explicitly deferred, not waived or passed.

</deferred>

---

*Phase: 09-whole-share-trading-and-combined-portfolio*
*Context gathered: 2026-11-11*
