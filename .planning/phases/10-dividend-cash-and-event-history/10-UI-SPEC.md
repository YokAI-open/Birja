---
phase: 10
slug: dividend-cash-and-event-history
status: approved
reviewed_at: 2026-11-12T18:30:41.782036+00:00
shadcn_initialized: true
preset: radix-vega (existing customized source)
created: 2026-11-12
---

# Phase 10 — UI Design Contract

> A private, readable mixed-event History with truthful dividend cash and correction lineage. This is a planning contract, not implemented UI or owner acceptance. Live provider/data/action activation remains deferred.

## Design System

| Property | Value |
|----------|-------|
| Tool | Existing shadcn/ui copied source and Tailwind v4; no initialization |
| Preset | `frontend/components.json`: radix-vega, neutral, CSS variables, subtle menu accent |
| Component library | Existing Button, Card, Badge; semantic table, ordered list, definition list and native disclosure |
| Icon library | Existing Lucide: 20px controls, 16px inline; decorative icons `aria-hidden` |
| Font | Existing self-hosted Inter Variable; tabular financial figures |
| Canonical sources | `design-system/birja/MASTER.md`, `frontend/src/index.css`, existing History source, `09-UI-SPEC.md`, approved requirements and `10-RESEARCH.md` / `10-PATTERNS.md` |

The initialized design system was detected in the checked-in config/components/CSS. No History page override exists. Preserve its actual styling and surrounding shell. No shadcn initialization, registry command, dependency installation, preset reset, additional icon/font library or new design system is needed. No Phase10 CONTEXT exists; the owner authorized deriving this contract from approved requirements and existing design. Specific copy/layout below are implementation defaults, not invented discussion decisions.

Local ui-ux-pro-max lookup: `python3 .codex/skills/ui-ux-pro-max/scripts/search.py 'keyboard focus pagination' --domain ux` returned Focus States and Focus Not Obscured guidance on2026-11-12. Applied here: visible focus and protection from fixed navigation; no blanket AAA compliance claim. No new framework API is required by this visual contract; implementation follows existing local components and the official TanStack infinite-query guidance already documented in10-RESEARCH.

## Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Inline label/icon gaps |
| sm | 8px | Control clearance and wrapping field gaps |
| md | 16px | Event detail rows/mobile groups, card padding, gutters and gaps |
| lg | 24px | Desktop card padding and event group separation |
| xl | 32px | Desktop gutters and page spacing |
| 2xl | 48px | Inherited major section breaks only |
| 3xl | 64px | Reserved existing large separation; no new layout requirement |

New Phase10 spacing uses this standard subset of the existing master system. Existing button20px padding and header40px geometry remain unchanged inherited component styling, outside the new spacing-token declaration; MASTER remains authoritative. Preserve24px card radius,14px controls, pill badges/buttons and existing shadows. Minimum table row height52px; rows grow with wrapped details. Touch targets≥44×44px and8px clearance. Do not truncate a held reason, financial string or stock name to preserve fixed height. No new spacing scale or non-multiple exception.

## Typography

Four content sizes and exactly two content weights on changed surfaces, consistent with Phase9:

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body, event titles, amounts, buttons | 15px | 400 body;500 titles/values | 22px |
| Labels, metadata, timestamps, references | 13px | 400 detail;500 labels | 18px |
| Mobile page heading | 32px | 500 | 36px |
| Page heading at≥768px | 40px | 500 | 44px |

Keep existing shell typography. No extra large dividend KPI, weight600, smaller metadata or typography reset. H1 retains−0.02em tracking. Names and references wrap; amounts align right and use tabular figures. Status/reason text retains normal contrast and size.

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `--background` #F2F2F2 | App canvas |
| Secondary (30%) | `--card` #FAFAFA; `--secondary` #FFFFFF | History card and secondary controls |
| Accent (up to10%) | `--accent` #EEF1FE; `--data-blue-text` #3451D1 | Row hover, original-event navigation/disclosure and focus |
| Primary | `--primary` #18181B / white | Load more or initial error recovery |
| Warning | `--warn-soft` #FEF4E2 / `--warn-text` #8F5200 | Held/correction uncertainty and stale retained-page notice |
| Gain/loss | Existing gain/loss text and soft tokens | Applied positive/negative cash effects only; sign and text accompany color |
| Neutral | `--muted`, `--muted-foreground` | Noncash split metadata, zero changes and skeletons |
| Destructive | `--destructive` #B83270 | Error emphasis only; no destructive UI action |

Accent is reserved for the listed focus/link/hover elements. Use token classes in code, never raw hex. No new palette, gradient, chart or stock-specific color. Held proposed debits are neutral/warning, never styled as already deducted. Readability must not depend on color, tooltip or hover.

## Scope and Component Inventory

Primary focal anchor: each event's **actual cash change or explicit no-cash state**, followed by its identity and recorded time. Original-event lineage and event-specific detail sit immediately beneath that summary.

- Keep the existing History route, Markets / Portfolio / History navigation, top cash chip, fixed mobile navigation and one12-column card. Page header: `History` plus secondary `Refresh history`.
- Reuse existing Card/Button/Badge, exact string-safe money helpers, local timestamp helper and existing append/focus patterns. Extend HistoryPage with a small discriminated event renderer; no separate admin, payout, correction-approval or event-detail route.
- Use the typed mixed endpoint from the Phase10 contract; legacy crypto `/trades` remains compatible. UI must show pre-existing crypto fills and new stock/corporate events together without relabelling old fills as dividends or rebuilding their economics.
- No new filters, date picker, search, charts, downloads, earnings totals, manual payment/retry button, notifications panel or speculative tax/reinvestment controls.
- Do not show announcement-only entitlements as paid money. Only owner-scoped published financial/held records are History events. Their presence never enables live activation or reveals another owner's event.

## Responsive Mixed History Layout

At≥1024px render a semantic table with five columns: **Recorded**, **Event**, **Asset**, **Details**, **Cash change**. Below1024px render an ordered list of stacked event cards with the same information in labelled definition lists. This narrower table deliberately replaces irrelevant trade-only columns; it does not drop their values. CSS must expose one accessible layout at a time.

1. `Event` displays the exact user-facing type: `Buy`, `Sell`, `Dividend`, `Forward split`, `Dividend correction` or `Dividend correction held`. Include a distinct visible `Stock` / `Crypto` label in Asset and the saved symbol/name. Do not infer type from ticker, prepend a misleading Buy badge to a dividend, or use a global split event unrelated to this owner.
2. Each summary shows its actual signed cash amount or explicit `No cash changed`. Show the reason and original-payment reference for held corrections without requiring expansion. Essential dates, dividend quantity/rate and cash are directly visible. Optional lineage detail may use native `<details>` with a descriptive summary; no essential explanation belongs only in a tooltip.
3. Desktop headers use scope=col, Asset uses a row header; number columns align right. Table/card rows have stable public kind+ID keys. Do not use the timestamp or array index as identity. Long saved names, references and timezone text wrap with `min-width:0` and safe word wrapping. No horizontal page overflow at320/375px or zoom; no financial values hidden by ellipsis.
4. Card order is Recorded → Event/Asset → event-specific details → Cash change → linked original/status. Reading order matches visual order. Details use descriptive labels, not visual-only indentation. Preserve card dividers and restrained hover tint, without zebra stripes or clickable whole-row ambiguity.
5. Keep page bottom padding and scroll margin sufficient for the56px fixed navigation plus safe area so Load more, original-event controls and error recovery remain reachable and focused controls fully visible.

## Event-Specific Contract

| Event | Visible details | Cash meaning |
|-------|-----------------|--------------|
| Crypto buy/sell | Original side, symbol/name, quantity, execution price, fee and fill time; preserve established fill values | Original exact signed total including existing fee; no fee recalculation |
| Stock buy/sell | Saved company/symbol, whole shares, `IEX execution price`, actual source quote time, zero commission and fill time | Original exact signed cash total; visible `IEX prices` and simulated-execution explanation; never a current quote |
| Dividend | `Gross ordinary USD dividend`, eligible shares at cutoff, exact USD rate per share, ex-dividend date, record date, payable date, verified eligibility cutoff, credited/recorded time and saved stock identity | Positive actual credited amount; `No tax withholding or automatic reinvestment.` No entitlement forecast added to current cash |
| Forward split | Verified ratio expressed as new:old (`4:1`), effective date/time, saved shares before→after, verified total basis unchanged; original fills remain original | `No cash changed`; not a zero-priced trade or cash-in-lieu |
| Applied correction | Saved stock/event identity, original payment reference, verified revised eligible shares/rate/relevant dates, total now owed and previous cumulative applied amount; recorded time | Exact signed **adjustment applied**, not the new total entitlement; label `Cash change` |
| Held correction | Original reference, `Held for review`, fixed reason; proposed change only if verified and supplied; recorded time | `No cash changed` and `Applied change: $0.00`; proposed debit labelled separately, never the cash headline |

Field names are semantic requirements; exact wire names/discriminator values belong to10-CONTRACTS. Do not fabricate absent old-row facts, unsupported source terms, quote timestamps or exact dates. Display a nullable source date explicitly as `Not provided` when the API permits it; an invalid mandatory field fails parsing rather than displaying zero. Stock fills show retained IEX attribution; dividends are structured corporate actions, so never label a dividend rate or split ratio an IEX quote.

### Correction lineage and held resolution

- Preserve the original payment as a separate immutable event. An applied correction links with `View original dividend`; reference text includes its stable user-visible payment reference. A held decision remains distinct from a later applied correction or superseding decision.
- Links must work even when the original is outside loaded pages: use the owner-scoped original summary/lineage included by the typed response, rendered in an inline anchored detail area. Never guess a page number, scan every page automatically or claim the original is missing merely because it is not loaded. Opening the original detail moves focus to its heading; provide `Back to correction` returning focus to the initiating control. If an original row is already loaded, navigate to its stable anchor instead.
- Original detail repeats retained amount/stock/relevant dates, original credited time and reference. It does not replace the original credit with its corrected total. Any missing/unavailable reference gets fixed copy `Original dividend details are unavailable. Refresh history to try again.`; no foreign-user fallback or raw server error.
- A held reason uses fixed domain copy: `Not enough available cash for this correction. No cash changed.` or `The corrected dividend terms need verification. No cash changed.` Do not promise an automatic date, reserve cash in the UI, add a Pay now button or expose internal provider messages.
- If the backend publishes a later resolution, show a separate linked record with actual recorded time and the applied delta or `No cash changed`, as applicable. Keep the earlier record labelled `Held when recorded`; the latest projection may say `Resolved by correction {reference}` only from verified response lineage. No frontend derivation of current debt or mutable rewriting of the held event.
- A verified zero-delta checkpoint, if exposed, says `Dividend correction — no cash adjustment` and `$0.00`; it is never displayed as a new Dividend credit. This contract does not require exposing internal no-op processing runs.

## Money, Metadata and Date Semantics

- All cash, prices, quantities, rates, basis and ratios originate from validated exact server strings. Use established string/BigInt-safe formatters; no Number/parseFloat arithmetic, client midpoint, local dividend multiplication or sum of History into Account.cash.
- Cash displays USD to two decimals. Positive cash uses `+`, negative uses U+2212 `−`; zero is `$0.00` without a gain arrow. Include signs/text alongside state colors. Dividends are gross virtual income, never after-tax brokerage income.
- Whole-share stock counts have no crypto fractional padding; preserve crypto formatting. Dividend rate displays `USD {exact rate} per share` with all supplied significant decimal precision after safe canonical trimming, so a low rate never appears as zero. If a formatter uses a shorter friendly value elsewhere, retain the exact string in visible detail, not tooltip alone.
- `Recorded` is the immutable History publication timestamp and controls newest-first order. Distinguish `Filled`, `Credited`, `Effective`, `Eligibility cutoff` and `Payable date` explicitly. A late correction appears when recorded and does not backdate the original credit. UI preserves server order including ties across event types; no client resort by economic date.
- UTC instants convert to the viewer's local timezone with date, seconds and zone, using semantic `<time dateTime>` and exact UTC value in title/accessible text. Date-only ex/record/payable fields stay calendar dates without UTC-midnight conversion; avoid previous-day shifts. Payment-day convention is the server's America/New_York date and on/after payable rule, not a promise of a particular brokerage posting hour. The date labels explain calendar dates when needed.
- Historical saved metadata is authoritative. A later company rename, delisting, closed market or current action hold must not rewrite a fill or make the original credit disappear. Current denied data must not be newly fetched from a provider; retained-data display authority is enforced by the server, not invented by a browser join.
- Portfolio and shared cash remain server-authoritative. Refresh/invalidate relevant queries after observed new events; no optimistic credit, duplicate income summation, new starting grant or reset. `Cash after this event`, if supplied, is historical and must be labelled that way, never `Current cash`.

## Loading, Paging, Errors and Auth Lifecycle

- First load: existing fixed-shape card skeletons and `Loading history`, `aria-busy`; no empty-state flash or sample financial amounts. Empty list: neutral copy and Browse markets action below.
- Preserve deterministic server keyset order and stable kind+ID identity; default load size follows the frozen API contract. No infinite-scroll-only interaction. `Load more` makes one bounded request, is guarded during any active fetch and never changes current cash.
- Successful append preserves all loaded rows and keyboard position; polite live region says `{N} more events loaded. {M} events shown.` At end replace the focused Load more with a focusable `All events loaded.` message, using existing focus-return pattern. Background refresh must not steal focus.
- Append error retains loaded events and offers `Try loading more`. Refresh error retains the last successful owner-matching pages and explicitly says the update failed. Initial failure shows no rows plus `Try again`. Malformed discriminator/Decimal/date/lineage/cursor responses are failures, never partially trusted cash events.
- A stale/malformed page must not remove existing safe pages or count missing events as zero. An auth/session change is different: immediately clear/hide prior-owner financial rows, references and cash; abort/drop late responses; scope query keys to owner/session epoch using existing Phase9 patterns. On401 follow existing login/session flow rather than showing somebody else's cached History.
- Announce loading/error/status transitions once with polite status/appropriate alert; do not read the entire list on every refetch. Use native button/disclosure keyboard behavior and visible focus rings. No retry of a financial mutation is offered by History: Refresh/Load more are read-only.

## Copywriting Contract

| Element | Copy |
|---------|------|
| Page / card heading | History / Account activity |
| Chronology helper | Newest recorded first. Times are shown in your local timezone. |
| Cash helper | Cash change is the amount actually added to or taken from your shared USD balance. |
| Primary list CTA | Load more |
| Refresh CTA | Refresh history |
| Empty heading | No activity yet |
| Empty body | Your trades, dividends, splits and corrections will appear here. Browse markets to make your first trade. |
| Empty CTA | Browse markets |
| Initial error | Can't load your history right now. Try again. |
| Initial retry | Try again |
| Refresh error | Couldn't refresh your history. Showing the last successful update. |
| Refresh retry | Retry refresh |
| Append error | Couldn't load more events. Your loaded events are still here. |
| Append retry | Try loading more |
| Loading / append | Loading history / Loading more events… |
| Completion | All events loaded. |
| Dividend explanation | Gross ordinary USD dividend. No tax withholding or automatic reinvestment. |
| Held badge / cash line | Held for review / No cash changed |
| Held insufficient cash | Not enough available cash for this correction. No cash changed. |
| Held uncertain terms | The corrected dividend terms need verification. No cash changed. |
| Link to original / return | View original dividend / Back to correction |
| Original missing | Original dividend details are unavailable. Refresh history to try again. |
| Zero correction | Dividend correction — no cash adjustment |
| Destructive confirmation | Not applicable: History has no destructive, payment-approval or reset control |

## Acceptance and Evidence Contract

Implementation must capture actual authenticated synthetic browser journeys using real isolated financial services/SQL: existing crypto + stock fills, credited dividend spent through the shared balance, per-owner split, applied positive/negative correction, held unaffordable/uncertain correction with unchanged cash, original outside current page, identical-time mixed paging and account switch during delayed response. Do not mock successful financial effects in the browser to manufacture acceptance.

Required visual states: mixed desktop table, mobile cards, expanded original lineage, held correction with visible no-cash reason, empty, initial error, retained-page refresh/append error, final-page focus and loading. Include long company names, references and exact small rates. Check320/375/768/1024/1440px, keyboard-only, touch target44px, visible focus above fixed navigation and reduced-motion settings. No page overflow, clipped cash, color-only status or inaccessible duplicate layouts.

Owner must explicitly accept the new mixed History and correction/held UI. Record a genuine desktop browser **native200% zoom** readability/reachability/nooverlap/nohorizontal-page-overflow check. Headless CSS zoom, smaller viewports, device scale and unverified Ctrl+ shortcuts are supplementary only; when automation cannot prove native zoom, keep that outcome pending until the owner checks it. Phase9 acceptance does not accept new Phase10 UI. Screenshots and source-hash manifests must identify the actual reviewed build; no native-zoom or owner-acceptance claim is made during planning.

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| Existing shadcn official copied source | Current Button/Card/Badge only; no newly fetched blocks | Existing checked-in sources/config inspected2026-11-12; no new registry acquisition |
| Third-party registries | None | Not applicable; `frontend/components.json` registries is empty |

## Checker Sign-Off

- [x] Dimension1 Copywriting: PASS
- [x] Dimension2 Visuals: PASS
- [x] Dimension3 Color: PASS
- [x] Dimension4 Typography: PASS
- [x] Dimension5 Spacing: PASS
- [x] Dimension6 Registry Safety: PASS

**Approval:** independent UI contract checker approved all6dimensions on2026-11-12 after one spacing clarification. No implementation/UAT acceptance inferred.
