---
phase: 9
slug: whole-share-trading-and-combined-portfolio
status: approved
reviewed_at: 2026-11-11
shadcn_initialized: true
preset: radix-vega (existing customized source)
created: 2026-11-11
---

# Phase 9 — UI Design Contract

> Whole-share stock tickets and truthful combined holdings, using Birja's existing design system. This contract authorizes no live activation. Phase 7 live evidence and Phase 8 action activation remain owner-deferred; isolated fixtures establish mechanics only.

## Design System

| Property | Value |
|----------|-------|
| Tool | Existing shadcn/ui copied source with Tailwind v4; no initialization |
| Preset | `frontend/components.json`: radix-vega, neutral, CSS variables, subtle menu accent |
| Component library | Existing Button, Input, Card, Badge; native forms, table, list and definition-list semantics |
| Icon library | Existing Lucide only: 20px controls, 16px inline, decorative icons hidden from accessibility tree |
| Font | Self-hosted Inter Variable; tabular figures on every financial number |
| Canonical sources | `design-system/birja/MASTER.md`, `09-CONTEXT.md`, `09-RESEARCH.md`, `08-UI-SPEC.md`, actual checked-in components and CSS |

No page overrides exist under `design-system/birja/pages/`. The existing initialized design system remains authoritative. No registry CLI, new package, font, chart, preset reset or new visual system is needed. Owner authorized deriving this contract from saved decisions without another design interview. Exact copy/layout details below are planning defaults where D-01–16 did not already specify them.

## Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Inline icon gaps, compact metadata |
| sm | 8px | Control clearance, label/input spacing |
| stack | 12px | Definition-list rows, mobile holding groups |
| md | 16px | Mobile card padding/gutters, card grid gaps |
| control | 20px | Existing button horizontal padding |
| lg | 24px | Desktop card padding, ticket section gaps |
| xl | 32px | Desktop gutters and page spacing |
| 2xl | 40px | Inherited header spacing only |
| 3xl | 48px | Existing major section breaks only |

All are master-system multiples of four; 12/20/40px intentionally retain the project scale rather than the generic template scale. Keep 24px card radius, 14px controls, pill buttons/badges and existing shadows. Table rows have minimum 52px height and grow to fit status reasons. Inputs remain 48px tall; interactive targets at least 44×44px with 8px clearance. Never clip warning text or long stock names in a fixed-height box.

## Typography

Four content sizes and two content weights, 400 and 500, on the changed surfaces:

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body, card headings, financial rows, buttons | 15px | 400 body; 500 headings/values | 22px |
| Labels, status reasons, attribution, timestamps | 13px | 400 detail; 500 labels | 18px |
| Mobile page heading and headline value | 32px | 500 | 36px |
| Page heading and headline value at ≥768px | 40px | 500 | 44px |

Inherited input text stays 16px to preserve the existing control's mobile behavior; this is a control exception, not a new text hierarchy. Preserve surrounding shell and unchanged crypto typography. Headings use inherited −0.02em tracking; values/tabular columns remain right aligned. Use sentence case and canonical uppercase tickers. Do not introduce smaller timestamps, extra weight 600, or shrink text to fit totals.

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `--background` #F2F2F2 | Canvas and neutral surrounding space |
| Secondary (30%) | `--card` #FAFAFA; `--secondary` #FFFFFF | Cards, secondary controls and input surfaces |
| Accent (up to 10%) | `--accent` #EEF1FE; `--data-blue-text` #3451D1; `--data-blue` #4A6BF0 | Selected bid/ask emphasis, links, focus, allocation fills, row hover |
| Primary action | `--primary` #18181B / white foreground | One Confirm buy/sell or outcome-resolution primary action |
| Warning | `--warn-soft` #FEF4E2 / `--warn-text` #8F5200 | Repricing, incomplete value and unavailable-trading explanations |
| Neutral | `--muted` #EDEDED / `--muted-foreground` #6B6B70 | Closed/halted metadata, unavailable values and skeletons |
| Gain/loss | Existing gain/loss text and soft variants | Signed financial outcomes only; include text/sign/arrow |
| Destructive | `--destructive` #B83270 | Validation/refusal emphasis; no destructive account operation |

Accent is reserved for the explicitly listed elements. Never green Buy/red Sell buttons; use neutral segmented controls. Use tokens rather than raw hex in components. One existing portfolio highlight gradient maximum; keep white text over its navy region. Status labels and disabled reasons retain full contrast independently of button opacity. Class allocation bars may all use data-blue: their explicit labels carry meaning, with no new asset-class colors.

## Scope and Component Inventory

Primary focal anchors: the ticket's preview cash change and confirmation action;
the portfolio's complete value or explicitly incomplete known-value headline.
Independent checker approval covers all six dimensions. The inherited 16px input
is an accepted control accessibility exception to the four-size content scale.

- Preserve Markets / Portfolio / History navigation and the shared cash chip. Add a distinct stock ticket route, default `/trade/stocks/:symbol`, leaving existing crypto `/trade/:symbol` semantics untouched. Use approved stock identity routing; never infer asset type solely from a symbol match.
- Reuse `StockAttribution`, `StockActionState`/fixed reason copy, existing money-formatting helpers, Button/Input/Card/Badge, and TanStack Query/auth lifecycle patterns. A focused StockTradePage and typed stock-specific hook/parser are appropriate. Do not route stocks through crypto USD/fractional/fee calculations.
- Stock discovery entries may link to the ticket even when trading is unavailable so the user can inspect the reason and prepare a draft. The entry control is `View stock`; eligible entries may say `Trade`. A link never advertises execution when the server denies it. Replace the Phase 8 coming-later notice only where the new local contract is actually integrated; absent activation remains disabled.
- Stock ticket desktop: 7-column identity/bid-ask/draft card and 5-column preview/receipt card at ≥1024px, within existing max-width layout. Below 1024px stack draft then preview/receipt. Keep attribution/disclosures visible in normal flow, not hidden in a tooltip.
- Portfolio preserves its existing summary/cash 8/4 layout at ≥1024px and one combined holdings section below. No separate stock account, starting grant, reset, watchlist, charts, order queue, event-detail page or dividend payment UI.

## Stock Ticket Contract

### Draft and preview — D-01, D-02, D-11, D-12, D-14

1. Show company, ticker, `Stock` asset label, listing exchange, session/status/action facts, and both labelled `IEX bid` / `IEX ask` when independently authorized for disclosure. Highlight Ask for Buy and Bid for Sell with text `Buy price` / `Sell price`, plus subtle accent; never indicate execution at midpoint.
2. Buy/Sell uses neutral segmented buttons. Visible label `Whole-share quantity`; input is a string with numeric keyboard hint. Reject zero, negatives, fractions, exponents and invalid/overflow strings. No USD mode, stepper rounding or silent truncation. Errors appear under the field. Stocks display whole counts without crypto decimal padding.
3. `Buy max` appears on Buy; `Sell all` on Sell. Both only fill the draft. Server-computed exact bounded whole-share maximum and current holding are authoritative. No JS Number/parseFloat money math or cent-rounding approximation; safe integer/string arithmetic is allowed only under the frozen API contract. Disable Buy max without a valid executable ask/current cash; Sell all requires verified current quantity. A zero shortcut result gives an explicit reason rather than submitting zero.
4. Render a server preview only for the currently matching symbol, side, quantity, authenticated user and still-valid authority. Rows: `Quantity`, `Execution price`, `Commission` ($0.00), `Added spread` (0%), `Total cash change`; show source quote date/time and IEX attribution. Show cash available / shares owned separately. No speculative client total.
5. Only current eligible regular-session quotes strictly younger than 120 seconds can support confirmation. At equality or authority expiry, remove confirmation eligibility immediately. Do not relabel historical marks as fresh previews. Awaiting preview uses fixed-shape skeletons with `Loading preview`; no old preview remains executable while a new quantity loads.
6. Closed/temporarily unavailable stock retains editable draft quantity and explicit reason, but preview/confirmation is disabled and unsafe quote-dependent estimates disappear. Quantity-only `Sell all` may still populate when holding data is verified. No queued order, auto-submit, persistent draft or pre-approved confirmation. Keep draft only in the current authenticated page lifecycle; clear on logout/account change.
7. A close/hold/source deadline during review invalidates the preview, retains typed quantity and announces why. Availability recovery requires a fresh preview and a later explicit user confirmation. No enablement from the browser clock alone.

### Repricing — D-03

The selected executable side changing requires a renewed server preview. Show `Price updated. Review the changes before confirming again.`, followed by labelled old → new execution price, old → new total cash change, and signed total difference. Differences come from server exact strings or existing exact arithmetic, never floating-point subtraction. A change only to the opposite quote side does not invent a price-change refusal. The stale preview is never submitted again; the renewed preview must match the current draft and authority before another click can confirm.

### Submission, uncertain outcome and receipt — D-04, D-15

- During submission, disable edits, shortcuts and duplicate confirmation, show `Confirming buy…` / `Confirming sell…`. Do not optimistically change cash, holdings or show a fill.
- A network timeout, malformed success response or otherwise unknown execution outcome enters a distinct unresolved-attempt state: `We couldn't confirm the result. Check this order before placing another.` Freeze the attempt's symbol/side/quantity/key. The primary `Check order result` retries the same economic payload and idempotency key; do not generate a new key, present Trade again, or permit edits that silently abandon the attempt.
- Result resolution must remain possible after market closure, a hold or quote expiry: it retrieves/replays the original receipt, never requires a fresh executable quote. It may receive a definitive no-fill refusal or payload conflict. Preserve user-scoped replay and auth isolation. An unresolved attempt is not a queued order. New submission becomes available only after the current outcome is resolved; never falsely promise that a timeout means no trade occurred.
- For a known no-fill refusal, retain editable quantity, display the fixed refusal reason and require a fresh eligible preview before another new order. A payload conflict says `This order reference belongs to a different request. Refresh before trying again.` Do not expose another user's receipt or raw server/provider errors.
- On persisted success, remain on `Order filled` receipt: original symbol/company/side, quantity, IEX execution price/source time, zero commission/spread, signed cash change, `Cash after this trade`, `Shares after this trade`, fill date/time and transaction reference. Receipt facts remain those saved at execution even on replay after a split, rename or later trade. Mark them as historical after-trade balances; separately refreshed current cash must not rewrite them.
- Offer `Portfolio` and secondary `Trade again`. Trade again clears prior outcome and quantity and begins a fresh preview flow; it never executes or resubmits. Receipt success moves focus to its heading, while background refetch never moves focus. Invalidate/refetch relevant shared cash, holdings and portfolio queries after confirmed success without computing balances locally.

## Independent Status and Valuation Contract

Status, session, action monitoring, display rights and executable quote validity remain independent. Backend authorization owns the decision; a green price badge, HTTP success or recent source time alone never means tradable. Show all applicable facts, with one primary refusal explanation chosen conservatively:

| Condition | Ticket and controls | Portfolio mark/value |
|-----------|---------------------|----------------------|
| Display permission absent/expired | No denied numeric quote/time; fixed access-unavailable copy; draft only | Suppress denied source-derived values; incomplete if held |
| Corporate-action hold, uncertain monitoring/units, or incompatible post-action quote | Persistent Phase 8 hold/reason; no numeric unsafe bid/ask or executable preview | `Valuation unavailable`; no old-unit mark, average-cost inference or guessed adjustment |
| Frozen/halted/unverified or stale status evidence | Clear independent refusal; no confirmation | A verified halt without action uncertainty may retain compatible permitted historical midpoint; unknown/frozen state alone cannot authorize a retained mark |
| Regular session closed, otherwise safe | `Market closed`; draft allowed; no executable preview | Permitted last compatible midpoint with actual date/time and `Market closed` |
| Session open, execution quote missing/stale/prior-session | No confirmation; source-time refusal | No assumption of a valid mark from quote recency alone; follow explicit server valuation projection |
| Eligible quote/status/session/actions/rights | Fresh server preview; explicit confirmation | Eligible IEX midpoint and actual source date/time |
| Any authority/action deadline reached or newer restriction observed | Invalidate preview immediately, retain draft | Clear values no longer authorized; recompute honest incomplete projection |

Permission and action/unit restrictions override all historical display preferences. An unresolved submitted attempt retains its result-resolution action across these states; result resolution is separate from new-order eligibility. Show `Halted` prominently on a verified historical halt mark with `Last verified midpoint · {dated time and zone}`. It is never `Live` or an execution quote. If no trustworthy permitted mark remains, show `Unavailable`.

Retained marks expire at actual retention/display rights and current action/unit deadlines; do not extend retention to span a weekend or promise every closure always has a mark. Preserve conservative monotonic transport/time guards, admission generation, action epochs and later-restriction ordering. Older/equal delayed responses must not restore removed values or restart deadlines. Separate executable quote expiry from historical valuation permission so an expired 120-second execution quote does not automatically erase a separately authorized closed/halted mark. No direct provider calls or raw privileged event details in the browser.

## Combined Portfolio — D-05 through D-10, D-16

- One alphabetically ticker-sorted list with stable instrument identity as tie-break/key. No price-driven row reordering. Every holding shows `Stock` or `Crypto`, symbol and name; stock rows also show IEX valuation attribution. Preserve one actual cash balance and original stored starting-cash comparison.
- At ≥1024px use a semantic table: `Asset`, `Quantity`, `Average cost`, `Cost basis`, `Current value`, `Gain/loss`, `Allocation`. The Asset cell includes mark price/source time/session/hold reason in a wrapping detail group. At smaller widths use stacked holding cards with exactly the same labelled figures in a definition list; no expandable cost details and no duplicated accessible layouts.
- Stock quantity is whole-share count; crypto keeps its established up-to-eight-decimal display. Use server exact monetary strings and existing string-safe formatters. Cash/basis/value/P&L are formatted USD to two decimals; retain extra nonzero unit-price precision under the established price formatter. No client recalculation of average cost, midpoint, basis or P/L.
- Current stock value uses the backend IEX midpoint, never bid-only liquidation value or an execution receipt price. Preserve exact source date/time. Closed/halted marks remain dated historical marks, not rolling ages called live. Corporate-action uncertainty suppresses unsafe derived average-cost/unit figures as well as value where the server marks them unavailable; verified total basis/quantity remain only when independently trustworthy.
- With complete valuation, headline `Total portfolio value`, total gain/loss and return versus original stored starting cash remain available. Per-holding P/L includes sign/arrow/text and percentage where defined. Complete zero-denominator percentages use `Not applicable`, never NaN or invented 0%.
- If any holding lacks value, headline must read `Known value: {USD} — incomplete` plus `{N} holding cannot be valued` / `{N} holdings cannot be valued`. This is the server known subtotal including known cash and known holdings. Do not sum in JavaScript. Overall gain/loss and all allocation percentages are `Unavailable`; no zero fills, hidden positions, residual allocation or subtotals labelled total. Individually known holding value/P&L may remain visible; unknown row values show `Unavailable` and the reason.
- Allocation has exactly three summary rows/bars: `Cash`, `Stocks`, `Crypto`. Holding-specific percentages remain in the holdings list only when total valuation is complete and a nonzero denominator exists. Use server percentages lexically validated for 0–100 CSS widths, no Number arithmetic/rebalancing to force 100%. In incomplete state suppress filled bars, keep labelled rows with `Unavailable` and the reason. Do not renormalize against known value. Independently valid class monetary amounts may appear, explicitly labelled known/incomplete where needed.
- Dividend entitlements are not cash. Phase 9 reads the one Account cash balance, so future Phase 10 credits appear once through that balance, not by adding entitlement/payment histories again. Do not add dividend payout/history UI in this phase.

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary ticket CTA | Confirm buy / Confirm sell |
| Quantity label/help | Whole-share quantity / Enter a whole number of shares. |
| Quantity validation | Enter a whole number greater than 0. |
| Quantity range | This quantity is too large. Enter a smaller whole number. |
| Shortcuts | Buy max / Sell all |
| No affordable whole share | Not enough cash to buy one share at the current ask. |
| No holding to sell | You do not hold shares of this stock. |
| Initial preview hint | Enter a quantity to preview this trade. |
| Loading preview | Loading preview |
| Repricing | Price updated. Review the changes before confirming again. |
| Old/new labels | Previous execution price / New execution price / Previous cash change / New cash change / Difference |
| Closed | Market closed. You can edit a draft; no order is queued. |
| Interrupted preview | Trading became unavailable. Your quantity is saved here; get a fresh preview before confirming. |
| Halted/frozen | Trading halted. New orders are unavailable. / Trading frozen. New orders are unavailable. |
| Unknown status | Stock status is unverified. New orders are unavailable. |
| Stale quote | This quote is out of date. A fresh eligible quote is required before trading. |
| Permission unavailable | Stock data access is unavailable. Crypto remains available. |
| Action uncertainty | Preserve Phase 8 fixed reason copy, including Suspended for corporate-action review. |
| Preview unavailable | Preview unavailable while trading is paused. Your quantity is only a draft. |
| Unknown outcome | We couldn't confirm the result. Check this order before placing another. |
| Unknown-outcome CTA | Check order result / Checking order result… |
| Known insufficient cash | Not enough cash for this order. Review your quantity and try again. |
| Known insufficient holding | Not enough shares for this sale. Review your quantity and try again. |
| Receipt heading/actions | Order filled / Portfolio / Trade again |
| Receipt balance labels | Cash after this trade / Shares after this trade |
| Empty state heading | No holdings yet |
| Empty state body/action | Explore Markets to buy your first stock or crypto. / Explore Markets |
| Portfolio load error | Can't load your portfolio right now. Try again. |
| Portfolio background error | Couldn't refresh your portfolio. Only still-permitted values from the last update are shown. |
| Ticket load error/action | Can't load this stock right now. Retry or return to Markets. / Retry stock |
| Known incomplete headline | Known value: {USD} — incomplete |
| Incomplete explanation | {N} holding(s) cannot be valued. Overall gain/loss and allocation are unavailable. |
| Unavailable value | Unavailable |
| Historical closed/halt mark | Market closed / Halted; Last verified midpoint · {dated time and zone} |
| Valuation explanation | Stock values use the IEX bid/ask midpoint; this may differ from the buy or sell price. |
| Existing attribution | IEX prices. Quotes come from IEX, one US exchange, and may differ from other exchanges. Birja uses virtual money and simulated execution. |
| Stock fee/settlement disclosure | Stock commission and added spread are zero. Regulatory fees are omitted. Virtual sale proceeds are available immediately; real settlement restrictions are not simulated. |
| Destructive confirmation | No destructive account operation. Every simulated buy/sell requires its itemized preview and explicit Confirm action; shortcuts never execute. |

Copy uses fixed validated domain reason mappings, not raw provider/operator strings. Preserve applicable required attribution text without exposing private evidence. Source, simulation, omitted-fee and immediate-proceeds disclosures appear on the stock ticket/preview/receipt journey; IEX midpoint explanation and attribution appear in Portfolio whenever stocks are shown. Never imply exchange-wide consolidated pricing, guaranteed real execution or a live grant from synthetic tests.

## Loading, Feedback and Accessibility

- Initial loading reserves actual card/table shapes, one contextual busy/status label and no full-page spinner. Background refetch retains only independently valid data and never restores expired values. Empty holdings differ from request failure or unpriced holdings. Retry actions only refetch app APIs; they do not clear holds or activate products.
- Native form labels are always visible; quantity helper/error/restriction uses `aria-describedby`, invalid field uses `aria-invalid`. Preserve 2px focus ring/2px offset. Buy/Sell supports keyboard selection with coherent radio semantics and arrow navigation or native controls. All CTA/shortcuts are ≥44px targets.
- Exactly one accessible table/card layout is exposed per breakpoint. Table headers have scope; mobile definition-list labels match columns. Asset/action status text wraps; no tooltip-only timestamp, warning, bid/ask label or disability reason. Show semantic `<time dateTime>` with actual date and local time zone, not merely time-of-day; session boundaries use America/New_York labels.
- One polite atomic contextual status region announces selected-stock availability changes, invalidated/repriced previews, result resolution and portfolio incompleteness. Do not announce each source-age second, price tick, polling cycle or every holding separately. Submission errors can use a focused alert; do not move focus on background updates.
- Successful fill focuses receipt heading; explicit retry success preserves sensible heading/control focus; failed retry retains retry focus. Do not trap focus, require hover, use browser alert dialogs or hide safety explanations in transient toasts.
- At 320/375/768/1024/1440px and actual 200% browser zoom, no document overflow, overlap or hidden confirm button. Narrow screens stack bid/ask, controls and receipt rows; table switches to cards below 1024px. Long company names, huge amounts and date/zone strings wrap without ellipsis. Respect bottom-navigation safe area.
- Existing hover/press ≤150ms remains; no new motion package, pulsating price dot or chart. Reduced-motion disables nonessential transitions. Expired financial values and authority removals happen immediately without a fade that retains forbidden numbers.

## Required Verification Stories

1. Whole-share validation rejects fractions/USD/exponents/zero and supports exact numeric limits. Buy max/Sell all fill quantity only; Buy max half-even/large-value math is server-tested. Stock ask-buy/bid-sell/zero-fee UI and existing crypto amounts/fractions/fees both work independently.
2. Relevant price change shows old/new price/cash delta and requires a second confirmation; opposite-side-only change does not falsely reprice. Pending submission prevents edits/duplicates; confirmed receipt remains with correct saved balances, Portfolio/Trade again actions.
3. Dropped/malformed response retains one key and frozen payload; Check order result after close/hold returns the exact original receipt once. Replay after later split/rename/another trade keeps original receipt facts. Conflict and two-user cache cases reveal no foreign data. Result unknown never becomes failed/no-fill merely because prices expire.
4. Close/hold/120-second boundary during preview immediately disables new confirmation, retains draft and suppresses unsafe estimates. Reopening requires a new eligible server preview and another click. No queued orders or automatic retry/fill. Unknown status is never inferred normal from fresh quotes.
5. Complete mixed portfolio has one cash balance/original start, alphabetic labelled stock/crypto holdings, visible cost basis, midpoint values, class bars and individual allocations. Stock sale then immediate stock/crypto purchase uses refreshed shared cash without a grant or local optimistic accounting.
6. Closed and verified-halt historical marks display actual dates with explicit labels while orders remain blocked. Retention/permission/action expiry removes them; uncertain action overrides recent/dated mark. Source120s execution expiry is distinct from valid historical-mark disclosure.
7. One unknown holding produces exact known subtotal/count, nullable overall P/L/all percentages and unfilled allocation bars, while known individual values/cash remain. No value zeroing, hidden row or normalization. Zero-value complete portfolio uses Not applicable percentages. Future dividend cash fixture is counted once from account cash, not added from entitlements.
8. Delayed/older epoch, admission revocation, authority equality, background error, reconnect and account-switch cannot restore old unit values or execute stale previews. Verify both active view and query cache protection using fake clocks/controlled responses, plus real isolated browser stories.
9. Actual browser mobile/desktop/200% zoom, long synthetic names/large values, keyboard-only Buy/Sell/shortcuts/confirmation/retry, screen-reader labels/live-region assertions and reduced motion pass. Preserve crypto journeys and Phase 8 action safety. Screenshots/owner UI acceptance cover new ticket, receipt, repricing, unavailable draft, full and incomplete combined portfolio; earlier Phase 8 approval does not approve the new UI.
10. All proof remains isolated. Actual provider-status bootstrap/continuity, Phase 7 live quotes and Phase 8 action rights/readiness remain deferred and disabled. No prototype “enabled” state is recorded as live readiness or deployment acceptance.

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| Existing checked-in shadcn source | Button, Input, Card, Badge | 2026-11-11 inspected local components/config; no new download or registry import |
| Third-party registries | None | 2026-11-11 `frontend/components.json` declares empty registries; no external block included |

## Source and Default Provenance

| Source | Decisions used |
|--------|----------------|
| `09-CONTEXT.md` D-01–04 | Whole shares/shortcuts, bid/ask emphasis, repricing comparison, persistent receipt/actions |
| D-05–08 | Combined labelled alphabetical table/cards, direct cost details, three class bars |
| D-09–12 | Known incomplete headline/count, dated halt mark, editable unavailable draft, retained quantity/reconfirmation |
| D-13–16 | Disclosures, strict execution eligibility, shared cash/exact replay, midpoint/dated marks and once-only future dividend cash |
| `09-RESEARCH.md` | Separate execution versus valuation projection, exact server shortcuts, immutable receipt, post-wait authority, deferred status activation |
| Master / actual source / Phase 8 UI | Tokens, spacing, fonts, responsive shell, native components, safe fixed reasons, epoch/deadline/auth guards |
| Local ui-ux-pro-max search | Submit feedback, visible labels and explicit action confirmation; applied within existing system, no style replacement |
| Planning defaults | Distinct stock route, exact CTA/error wording, 1024px card/table switch, unresolved-attempt controls and source-time labelling consistent with locked safety |

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** Independent checker APPROVED, 2026-11-11. All six dimensions reviewed; focal anchors are now explicit and inherited 16px input typography is a documented accessibility exception. This is contract approval, not owner acceptance of implemented UI.
