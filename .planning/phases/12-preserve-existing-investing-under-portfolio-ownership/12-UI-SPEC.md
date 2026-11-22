---
phase: 12
slug: preserve-existing-investing-under-portfolio-ownership
status: approved
reviewed_at: "2026-11-14T15:42:46Z"
shadcn_initialized: true
preset: radix-vega (existing customized source)
created: 2026-11-14
---

# Phase 12 — UI Design Contract

> Preserve the accepted investing screens while making the financial portfolio
> explicit. This is a design contract for implementation, not a claim of built
> UI, owner acceptance, provider suitability or production deployment.

## Design System

| Property | Value |
|---|---|
| Tool | Existing copied shadcn/ui source and Tailwind v4; no initialization |
| Preset | `frontend/components.json`: radix-vega, neutral, CSS variables, subtle menu accent |
| Component library | Existing Button, Input, Card, Badge; native links, forms, table/list and definition-list semantics |
| Icon library | Existing Lucide; 20px controls/16px inline, decorative icons hidden |
| Font | Existing self-hosted Inter Variable; tabular financial numbers |
| Canonical visual sources | `design-system/birja/MASTER.md`, `frontend/src/index.css`, accepted `09-UI-SPEC.md` and `10-UI-SPEC.md` |
| Decision sources | `12-CONTEXT.md`, `12-RESEARCH.md`, active Phase 12 requirements and roadmap |

Inspection on 2026-11-14 found the initialized `frontend/components.json`, empty
`registries`, existing UI component source, CSS tokens and React/TanStack Query
usage. These checked-in values are the evidence; no shadcn/Context7 CLI, preset
reset, registry fetch, font download or package installation was run or required.
The owner authorized deriving this contract from approved scope and existing
design rather than another style interview. No design-system override is added.

## Spacing Scale

| Token | Value | Usage |
|---|---|---|
| xs | 4px | Compact label/value gap and inline icon separation |
| sm | 8px | Portfolio context to supporting metadata; control clearance |
| stack | 12px | Existing card content stacks and mobile event groups |
| md | 16px | Mobile card padding/gutters and existing card gaps |
| control | 20px | Existing button horizontal padding |
| lg | 24px | Desktop card padding and ticket section gaps |
| xl | 32px | Desktop gutters and page-header spacing |
| 2xl | 40px | Existing page-heading separation only |
| 3xl | 48px | Existing major section breaks only |

All values retain the master's four-pixel scale. Keep 24px card radius, 14px
controls, pill buttons and current shadows. Inherited table rows are at least
52px and grow with content; interactive targets are at least 44×44px with 8px
clearance. Keep existing 48px inputs. Portfolio-name rows grow naturally; no
fixed-height chip, clipped name, new floating panel or overlay is introduced.

## Typography

Four content sizes and exactly two content weights on the changed surfaces,
following the accepted Phase 9/10 contracts:

| Role | Size | Weight | Line Height |
|---|---|---|---|
| Body, portfolio-name value, financial rows and buttons | 15px | 400 body; 500 names/values | 22px |
| Visible `Portfolio` label, metadata and timestamps | 13px | 400 detail; 500 labels | 18px |
| Mobile page heading and headline value | 32px | 500 | 36px |
| Page heading and headline value at ≥768px | 40px | 500 | 44px |

Keep inherited 16px input text as the existing mobile-control exception; no new
input is required for the portfolio context. Unchanged shell wordmark/account
heading styles retain their existing master/component rules. Do not restyle
unchanged components or introduce another weight into new context/error content.
Names render as text, preserve Unicode and wrap with `min-width: 0` plus safe
word breaking. Show all allowed 60 characters; no ellipsis, title-only recovery,
font shrinking or fixed single-line badge. Keep financial tabular figures,
existing alignment, signs and exact-money formatters unchanged.

## Color

| Role | Value | Usage |
|---|---|---|
| Dominant (60%) | `--background` #F2F2F2 | Existing canvas and neutral surrounding space |
| Secondary (30%) | `--card` #FAFAFA; `--secondary` #FFFFFF | Existing cards and secondary controls |
| Accent (up to 10%) | `--accent` #EEF1FE; `--data-blue-text` #3451D1; `--data-blue` #4A6BF0 | Existing selected-row tint, links and data fills; focus uses `--ring` |
| Primary | `--primary` #18181B with white text | One current confirmation/recovery CTA per view |
| Neutral context | `--foreground` #111113; `--muted-foreground` #6B6B70 | Portfolio name and its quieter visible label |
| Warning | `--warn-soft` #FEF4E2 / `--warn-text` #8F5200 | Unknown order outcome and temporarily unavailable financial context |
| Error/destructive semantic | `--loss-text` / `--destructive` #B83270 | Refusal/error text only; no deletion action in this phase |
| Financial outcomes | Existing gain/loss text and soft tokens | Existing signed P/L and cash outcomes, never portfolio identity |

Accent is reserved for the listed existing links/focus/data/selection functions.
The portfolio name is neutral text, not a new accent, gain, loss or status badge.
Components use semantic tokens rather than raw hex. Preserve existing price
freshness labels, IEX attribution, semantic reason copy and signed outcomes.
Retain at most the existing one portfolio highlight gradient per page.

## Scope and Component Inventory

The primary focal anchor remains the existing preview cash change/confirmation
on trade pages and the complete value or explicitly incomplete known value on
Portfolio. Portfolio identity is consistently visible supporting context, not
a competing headline or a newly invented account dashboard.

| Existing or proposed surface | Phase 12 contract |
|---|---|
| `App.tsx`, existing navigation/focus pattern | Keep Markets / Portfolio / History and Account. Bind financial links to the explicit portfolio; preserve mobile safe-area spacing and heading focus |
| Proposed small `PortfolioContext` text component | Visible `Portfolio` label followed by the owned-active metadata name, initially `My portfolio`; reuse on all financial surfaces |
| Proposed target boundary/metadata hook | Validate and capture the explicit ID before financial queries/actions; fixed loading/unavailable/selection-required states |
| Existing TradePage / StockTradePage | Add context above the draft and repeat it in preview/confirmation and receipt. Replace user-wide cash dependencies with the same portfolio's validated financial context |
| Existing StockTradeReceipt / crypto fill summary | Keep immutable saved fill facts; add the original target's context and portfolio-specific destination links |
| Existing PortfolioPage / PortfolioHoldings | Keep current summary, cash, allocation and combined holdings layout; label the statement and any holding/trade detail with its portfolio |
| Existing HistoryPage / HistoryEventDetails | Keep table/cards, chronology, exact event copy, paging and original-reference behavior; include portfolio context on the page and original-detail region |
| Existing AccountPage / useMe | Identity-only email/session/sign-out view; remove the user-wide Cash block instead of inventing pooled, null or zero cash |
| Existing Button / Input / Card / Badge / money helpers | Reuse checked-in source. No new component package, third-party block, chart or selector library |

Creation, overview comparison, rename, optional description and description
editing/clearing belong to Phase 13. Public deletion and its management empty
state belong to Phase 14. This contract adds none of those controls. Their
underlying zero/multiple/closed states still need safe isolated fixture behavior.
Shared market browsing remains available without a financial target; a market
price is not permission to create a portfolio, show private cash or place an order.

## Portfolio Identity and Navigation Contract

1. Use a stable explicit resource path for financial pages. Planning defaults:
   `/portfolios/:portfolioId`, `/portfolios/:portfolioId/history`,
   `/portfolios/:portfolioId/trade/:symbol` and
   `/portfolios/:portfolioId/trade/stocks/:symbol`. API scope follows the research's
   `/api/v2/portfolios/{portfolio_id}/...` contract. The planner may finalize wire
   field names together with API tests, but may not remove the explicit target.
2. Portfolio metadata is an owned-active server response, not a label reconstructed
   from the URL, a remembered display name or a cash-bearing identity response.
   Portfolio IDs remain strings in browser contracts. The same captured ID binds
   name, money, holding, preview, receipt, History cursor and original-reference data.
3. Place the visible context row after the existing page heading and before the
   first financial card; use 8px internal separation and 16px to the following
   card. On ticket/preview/receipt regions use the same label/value pair before
   financial rows. A receipt's name is contextual metadata; its saved execution
   values and historical after-trade balances remain immutable.
4. Existing preservation entry routes `/portfolio`, `/history` or old trade links
   may discover exactly one owned active root and navigate with `replace` to its
   explicit URL **before** creating a preview/attempt. Zero or multiple results
   do not choose the first/newest root, pool cash or create a root. No chooser
   or create UI is exposed by this phase. Count/selection handling stays bounded.
5. Once an explicit target or attempt exists, an unavailable target never uses
   that discovery shortcut to find a replacement. A user's deliberate return to
   Markets can begin a new navigation lifecycle; it cannot resubmit, resolve or
   transform the old attempt in another portfolio.
6. Keep Markets at `/` and Account at `/account`. When a financial target is
   known, Portfolio/History/Trade links use its explicit ID; when none is valid,
   financial entry links reach the safe preservation resolver/state. Market rows
   retain their existing public facts; private cash, holdings and executable
   trade controls require the resolved portfolio. Do not add a shell-wide cash
   chip—the current `App.tsx` has none.

## Target States, Copy and Action Safety

The following codes/statuses are concrete planning defaults to align in the API
contract/tests; they are not claims about implemented responses. Normal auth
errors keep the existing session flow. Never display raw exception/provider text.

| Condition | Visible state and allowed action |
|---|---|
| Identity loading | Existing account skeleton, `Loading your account`; no financial identity or sample cash |
| Portfolio metadata loading | `Loading portfolio`; reserve the context/card shapes with skeletons and `aria-busy`; do not show the previous target's figures |
| Discovery succeeds with one active root | Navigate to its explicit ID before financial work, then show `Portfolio` / actual name |
| Discovery succeeds with zero roots | Heading `No portfolio available`; body `You're signed in, but no portfolio is available. You can still browse Markets or sign out.`; primary `Browse markets`. No auto-creation or grant |
| Discovery returns multiple roots without explicit selection | Heading `Portfolio required`; body `Open a portfolio-specific link to continue. No portfolio was selected.`; primary `Return to Markets`; no first-item fallback or new chooser |
| Malformed/missing explicit target | Invalid target is not queried as another root. Scoped API malformed IDs use validation refusal; unscoped legacy financial requests use `409 portfolio_required`. Render `Portfolio required` / `Open a portfolio-specific link to continue.` |
| Unknown, foreign or closed target | Same non-enumerating `404 portfolio_unavailable`; heading `Portfolio unavailable`; body `This portfolio is unavailable. Return to Markets to continue.`; primary `Return to Markets`. Immediately hide its cash, holdings, previews, receipts, History and original details |
| Metadata/network failure | `Can't load this portfolio right now. Try again.` / `Try again`; no executable preview or fallback identity. A retry addresses the same ID only |
| Same-target financial refresh failure | Keep only previously validated owner/target-matching read-only data with the existing refresh-failed notice; invalidate actionable quotes/previews until fresh authority returns. A lifecycle/authorization refusal instead removes the financial data |
| Legacy identity/OTP API version refusal | Proposed `409 api_version_required`, before OTP consumption; `This page needs an update. Refresh Birja to continue.` / `Refresh page`. Never show missing cash as zero; do not sign out solely to repair a version mismatch |
| Auth owner/session changes or expires | Existing sign-in/session handling; immediately hide previous-owner finances and discard its late responses, previews and attempts from the current view |

For a known target with no holdings or no History, preserve current empty-state
meaning: `No holdings yet` and `No activity yet`, with the existing Browse markets
action scoped to the same active strategy. Neither empty state implies a new
starting grant. Preserve all current closed/stale/action-uncertain stock reason
copy and IEX quote-disclosure guards independently of portfolio availability.

### Preview, pending attempt and receipt

- A preview binds owner/session, portfolio ID, instrument identity and economic
  payload. Context changes clear its actionable state; confirmation cannot read
  a mutable global “current portfolio” after the preview was prepared.
- Preserve stock `Preview trade`, `Confirm buy` / `Confirm sell`, repricing and
  receipt behavior; preserve current crypto preview/confirmation flow. Existing
  financial restrictions retain priority over optimistic client appearances.
- During submission keep the captured target visible and disable duplicate
  submission/edits as today. Never optimistically move cash/holdings or show a fill.
- Unknown outcome copy stays `We couldn't confirm the result. Check this order
  before placing another.` The primary `Check order result` repeats only the
  original active target/key/payload. Market closure does not prevent retrieval
  of an existing active-root receipt under the established replay contract.
- A different portfolio with the same retry key is a conflict, never its own
  new fill or another root's receipt. Fixed copy: `This order reference belongs
  to a different portfolio or request. Return to the original portfolio to check it.`
  Do not name or reveal an unauthorized original portfolio.
- If the original target becomes unavailable, remove normal financial access
  and stop result retries. If an attempt was unresolved, state `An earlier order's
  result is unconfirmed for this unavailable portfolio. It won't be retried in
  another portfolio.` Do not say “no trade happened,” expose a hidden receipt,
  generate a replacement key, or turn Return to Markets into a resubmission.
- An active matching receipt preserves saved fill time, source time, price,
  quantity, fee and historical cash/holding-after values. `Portfolio` links to
  that same root; `Trade again` begins a new draft only in that same root and
  requires a fresh preview and explicit confirmation.
- Carry ID into every financial query key, pending-attempt guard, cursor and
  late-response check alongside existing owner/session identity. Market evidence
  may remain globally shared. Cancellation is helpful but cannot replace guards
  against a response that already completed or a captured mutation closure.

## Copywriting Contract

| Element | Copy |
|---|---|
| Persistent financial context | `Portfolio` / server-validated name, initially `My portfolio` |
| Financial primary CTA | Existing `Confirm buy` / `Confirm sell` for a valid preview |
| Stock draft CTA | `Preview trade` |
| Outcome recovery CTA | `Check order result` for the original active target only |
| Metadata loading | `Loading portfolio` |
| Empty state heading | `No portfolio available` |
| Empty state body | `You're signed in, but no portfolio is available. You can still browse Markets or sign out.` |
| Empty CTA | `Browse markets` |
| Ambiguous/missing target heading | `Portfolio required` |
| Ambiguous target body | `Open a portfolio-specific link to continue. No portfolio was selected.` |
| Unavailable heading/body | `Portfolio unavailable` / `This portfolio is unavailable. Return to Markets to continue.` |
| Unavailable CTA | `Return to Markets` |
| Metadata error | `Can't load this portfolio right now. Try again.` |
| Metadata retry | `Try again` |
| Obsolete page/API | `This page needs an update. Refresh Birja to continue.` |
| Obsolete-page CTA | `Refresh page` |
| Receipt heading / destinations | Existing `Order filled`, `Portfolio`, `Trade again` |
| History cash helper | `Cash change is the amount actually added to or taken from this portfolio's USD balance.` |
| Account identity | Existing `Your account`, `Email`, `Sign out`; no user-wide cash value |
| Destructive confirmation | Not applicable: no delete, reset, transfer or portfolio-management action in Phase 12 |

The names themselves are text content, never HTML. No description is rendered
or edited here; Phase 13's optional-description requirement remains preserved.

## Responsive, Focus and State-Announcement Contract

- Preserve the existing 1440px maximum width, 16px mobile/32px desktop gutters,
  three-item mobile navigation, card/table breakpoints and 7/5 ticket layout.
  Below 1024px tickets remain draft then preview/receipt. Do not replace the
  combined holdings layout or mixed History table/card layout.
- Verify 320/375/768/1024/1440px widths and genuine desktop native 200% zoom.
  Portfolio names, exact money, long references and status copy wrap without
  horizontal page overflow or text shrinking. A bounded table may scroll inside
  its existing region; context, primary actions and recovery copy must remain visible.
- Context is a noninteractive labelled text group, not a disabled dropdown or
  fake button. Use one normal reading-order instance per independent financial
  region; do not make every repeated name an `aria-live` region.
- Route changes retain the existing focus-to-h1 behavior. A successful receipt
  moves focus to its heading. Initial target refusal moves focus to the state
  heading when it replaces a page; a background refresh/status change announces
  once without moving focus or rereading the full page. Do not focus hidden or
  absent target data after an asynchronous response.
- Keep 2px `--ring`/2px-offset focus treatment. Existing bottom padding and
  scroll-margin must keep all focused controls fully visible above the fixed
  56px mobile navigation plus safe area; do not downgrade to merely partial
  visibility. Label icons and hide decorative glyphs as in accepted components.
- Loading groups use `role="status"`/`aria-busy`; blocking request errors use a
  concise alert and recovery button. Label updates are contextual status changes,
  not repeated announcements on every polling tick.
- Preserve reduced-motion behavior, full-contrast disabled reasons and all
  existing non-color cues. No new animation or financial number flash is added
  for a context change. Show final guarded state immediately when motion is reduced.

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|---|---|---|
| Existing shadcn official source | Checked-in Button, Input, Card, Badge only | Source/config inspected 2026-11-14; `components.json` has empty `registries`; no download or initialization |
| Third-party registries | None | Not applicable; no new third-party block is declared or authorized |

## Evidence and Validation Handoff

- Source inspected: `frontend/components.json`, `frontend/src/index.css`,
  `App.tsx`, Account/Trade/StockTrade/Portfolio/History pages, StockTradeReceipt,
  identity/financial hooks and existing accepted Phase 9/10 UI contracts.
- Targeted local ui-ux-pro-max searches on 2026-11-14: `badge label wraps`
  matched compact-label overflow guidance. This contract avoids a compact badge
  for an unpredictable portfolio name and instead permits a full wrapping text
  value. `focus not obscured` matched minimum/enhanced visibility guidance; the
  established project contract retains fully visible focus above mobile chrome.
- The detected React stack search `async stale state` returned general Actions/
  optimistic-update guidance, which is not a verified match for financial Query
  guards. It is not adopted. Existing inspected TanStack Query and attempt-guard
  patterns, explicit owner/ID keys and rejection tests govern this phase.
- Automated implementation proof must include long names; first and repeated
  target discovery; zero/multiple/foreign/closed states; original key replay;
  route/session changes during delayed metadata, History and mutation responses;
  unavailable-target retries; original-event links/cursors; keyboard/focus;
  responsive reflow; no missing-cash fallback; and unchanged exact financial values.
- Build synthetic read-only review pages/screenshots showing the new context on
  crypto/stock draft, preview, receipt, holdings, History/original detail, identity
  Account and target-refusal states. Obtain genuine owner UI acceptance and
  desktop browser native 200% zoom confirmation during execution. Emulated
  viewport/zoom/reflow alone is not native-zoom evidence. No such acceptance or
  browser/runtime proof is claimed by writing this contract.
- No actual private portfolio, provider quote, production service, secret or
  historical Phase 7 result was inspected. The six deferred live outcomes and
  stock activation gates remain unchanged.

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** Pending independent UI checker. Owner acceptance of implemented
screens and genuine native 200% zoom remains a later execution checkpoint.
