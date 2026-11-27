---
phase: 25
slug: finish-the-trading-flows-and-verify-the-integrated-app
status: verified
shadcn_initialized: true
preset: radix-vega
created: 2026-11-26
---

# Phase 25 — UI design contract

Use the approved v1.5 trade, History and sign-in pages for hierarchy and
layout. D-01 through D-03 define the three surfaces. D-04 and D-05 define
the evidence for the integrated candidate. The working app supplies every
price, fill, event and session state. [Phase decisions](25-CONTEXT.md) ·
[Technical research](25-RESEARCH.md) · [Approved prototype](../../ui-reviews/v1.5/README.md)

## Design system

| Property | Value |
|---|---|
| Tool | Existing checked-in shadcn components and Tailwind CSS |
| Preset | `radix-vega`, neutral CSS variables |
| Component library | Radix-based project primitives and existing React components |
| Icon library | Lucide and local Birja brand assets |
| Font | Self-hosted Inter Variable with tabular figures for prices, balances and quantities |

Reuse the shared header, `Button`, `Card`, `Input`, `PortfolioSwitcher`,
native selects and disclosures. Use the existing focus ring, mobile mark and
accessible door. Focused local UI/UX Pro Max searches support paste and autofill
for authentication, unobscured focus and native stateful controls.
[Birja design system](../../../design-system/birja/MASTER.md) ·
[Component configuration](../../../frontend/components.json) ·
[Theme variables](../../../frontend/src/index.css)

## Spacing scale

| Token | Value | Usage |
|---|---:|---|
| Extra small | 4px | Field label to input and paired event metadata |
| Small | 8px | Adjacent controls, form feedback and related figures |
| Medium | 16px | Phone gutters, ticket padding and stack spacing |
| Large | 24px | Mid-width gutters, section separation and toolbar offset |
| Extra large | 32px | Wide trade panels and major groups |
| Wide | 48px | Desktop space below the shared header |
| Page | 64px | Upper range for separation around focused forms |

Use 44px minimum targets and 8px gaps between adjacent controls, 48px minimum
primary actions and 52px money and sign-in fields. Preserve the existing
single-pixel border and radius tokens. Center the 1360px maximum workspace,
which leaves a measured 40px gutter at 1440px. Use 24px at intermediate
widths and 16px from 740px down through 320px. Keep the reference's 220px
maximum chooser and 415px maximum sign-in panel. Use the 16px spacing
increment between trade panels and record the reference's measured 18px
gap in the comparison. Keep
trade panels side by side above 740px, with the ticket at 1.12 and preview
at 0.88 of the available fractional width. Stack ticket before preview at
740px and below. Permit additional vertical space and wrapping for live
labels, long asset names, and validation or recovery messages.

## Typography

| Role | Size | Weight | Line height |
|---|---:|---:|---:|
| Body, fields, controls and supporting text | 16px | 400 | 1.5 |
| Panel and section heading | 24px | 600 | 1.2 |
| Key price | 32px | 600 | 1.15 |
| Trade and sign-in page titles | Responsive 30–46px | 600 | 1.08 |

Use muted ink for supporting text and the responsive title size from phone
to desktop. Keep History's semantic title visually hidden because the active
navigation names the view. Use the existing exact-value formatters for
money, dates and quantities. Use 16px at weight 600 for event emphasis.
Keep sign and unit attached to each result.
Allow long names, addresses and monetary values to wrap at narrow widths.

## Color

| Role | Existing token | Usage |
|---|---|---|
| Dominant surface, about 60% | `--background` | Page canvas and quiet space around the centered sign-in panel |
| Secondary surfaces, about 30% | `--card`, `--muted` | Ticket, History cards, sign-in panel and distinct preview surface |
| Accent, up to 10% | `--ring`, `--brand` | Visible focus and existing Birja brand |
| Text and primary action | `--foreground`, `--primary`, `--muted-foreground` | Shared dark action, readable supporting labels and figures |
| Outcomes | `--gain-text`, `--loss-text`, `--warn-text` | Signed results, field errors and actionable order or market status |
| Destructive | `--destructive` | Existing destructive controls outside these three surfaces |

Use neutral Buy and Sell controls and show the selected side with its text and
pressed or checked state. Restrict accent to the focus treatment and brand.
Use text with signed color outcomes, status text or a meaningful symbol.
Apply the design system's contrast targets to foreground, supporting text,
control borders and focus. Honor reduced motion and keep status feedback
available through the same text in either motion setting.

## Trade workspace

- Use one labelled chooser already owned by the trade route. Put the asset
  heading next, with the symbol and identity visible, then the ticket and
  preview or receipt. Keep the portfolio name in the chooser.
- Order the ticket as current price and market state, Buy or Sell,
  cash and units held, amount or quantity mode when offered, the named
  input and unit, then the available shortcut and explicit preview action.
  Crypto keeps dollar and quantity buys, quantity sells and automatic
  preview. Curated and catalog stocks keep whole shares and explicit
  preview. Use the current cash and held quantity from the chosen portfolio,
  including on Sell. When these are loading or unavailable, use the existing
  state feedback in their place. Place field errors beside the input.
- Show the last permitted display price and next-session countdown when
  closed if the data exist. Use the actual session state and exact listing
  destination. Place the actionable reason by a paused or unavailable
  control and keep the existing read-only history view where applicable.
  A closed or stale quote stops a fresh confirmation while the original
  ambiguous order still offers its existing result check.
- Use a quiet summary panel. Read quantity, execution price, fees or
  commission and total cash change from the server preview. Retain the
  relevant buy/sell context, crypto market price and source time where it
  helps the decision. Include required source labels only where applicable.
  A replacement quote must explicitly require confirmation again and show
  the currently supported old/new comparison. During submission retain one
  pending action, then show either the original-order result check or the
  receipt. A historical chart can fail independently of the trade controls.
- After a fill, bring focus to the receipt heading and show the actual
  quantity, price, fees, signed cash change and resulting balance. Use
  route-scoped access to the portfolio and its History through the existing
  navigation, and an explicit `Trade again` action. The receipt values and
  the same portfolio's History must agree.

## History workspace

- Place a single `History portfolio` chooser and existing `Update history`
  action at the left, then `Filter activity` and `Filter assets` at the
  right. On phones put the filter pair below the chooser and Update. Keep
  this reading and keyboard order when the controls wrap. A compact refresh
  icon retains its accessible name and target.
- Activity choices are `All activity`, `Buy`, `Sell`, `Dividend` and
  `Split`. Dividend includes the original dividend and posted or held
  corrections. Asset choices are `All assets`, `Stocks` and `Crypto`.
  Both filters apply to the same owned server result before ordering and
  pagination. Use the current event catalog as the source of filter options.
- Render the newest-first server sequence as a compact list of real events.
  Label contiguous date groups without sorting the series again. Each
  native disclosure shows the event, symbol, recorded time and signed cash
  change or existing unavailable status. Show the existing company, units,
  price, fees and other event-specific detail on expansion. Preserve stable
  anchors, exact catalog identity and the correction's original dividend
  action. Keep the embedded original detail when the original row falls
  outside the loaded page or the selected filters.
- A filter or target change starts at page one and clears obsolete event
  expansion, pagination and append announcements. Give filters their
  regular loading and error states. Append on `Load more`, retain loaded
  events on an append error, and announce how many arrived after success.
  Preserve focus on the initiating control while it remains useful. When
  the final successful append removes it, move focus to the end-of-list
  status for that same query. Keep focus on the filter during a filter
  change and preserve the existing refresh/error recovery behavior.

## Sign-in workspace

- Center one panel under the shared header. Order the email stage as
  `Sign in`, visible `Email` label and input, any field feedback and
  `Send code`. The code stage uses `Enter your code`, a delivery hint,
  visible `6-digit code` field, any feedback, `Sign in`, then
  `Send a new code` and `Use a different email`. Keep email autofill,
  one-time-code autofill and paste support with numeric input mode.
- Keep the existing real request, verification and sign-out mutations and
  their cookie/session lifecycle. Transfer visible focus to the newly
  mounted field on stage changes. The signed-out door focuses the active
  field. The signed-in door runs sign-out, shows pending and error feedback,
  and returns focus to the signed-out form on success. Use the actual
  session's available navigation. Suppress duplicate pending submissions.
- Associate visible errors with their inputs, keep the established neutral
  delivery wording and honor the existing retry-after behavior. Use the
  guard's generated console code on disposable tests. Capture synthetic
  account data and an empty code field for the code-stage evidence.

## Copywriting contract

| Element | Copy and use |
|---|---|
| Trade actions | `Preview trade` for explicit stock preview, `Confirm buy` / `Confirm sell` for an eligible current preview |
| Empty trade preview | `Enter a quantity to preview this trade.` for stocks. For crypto, use `Enter an amount to see the full cost.` or `Enter a quantity to see the full cost.` according to mode. |
| Market closed | `Market closed` with the existing actual next-session countdown when known |
| Price changed | `Price updated. Please review again.` for crypto and `Price updated. Review the changes before confirming again.` for stocks, with retained comparison details |
| Unknown trade result | `We couldn’t confirm the result. Check this order before placing another.` and `Check order result` |
| Filled order | `Order filled` and `Trade again` with the actual receipt |
| Empty History | `No activity yet` with `Browse markets` |
| Filtered empty History | `No matching activity` and `Clear filters`, which restores both default filters |
| History loading and errors | `Loading history`, `Can’t load your history right now.` with `Try again`, and `Couldn’t load more events. Your loaded events are still here.` with `Try loading more` |
| History append | `Load more`, `Loading more events…` while pending, and `All events loaded.` at the final page |
| Sign-in actions | `Send code`, `Sign in`, `Send a new code`, `Use a different email` and `Sign out` |
| Sign-in validation | `Enter a valid email address.` and `That code is wrong or has expired. Check it or send a new code.` |
| Sign-in feedback | `Sending…`, `Signing in…`, `Signing out…` and the existing sanitized retry-after or service-unavailable message |
| Destructive confirmation | Trade confirmation stays explicit with its fee and total. Sign-out has its existing direct door action. |

## Running-app acceptance

Compare six actual-app captures with the corresponding six approved ZIP
captures at equal 1440 × 1000 and 390 × 1000 viewports. Use the same seeded
visual stage on each pair. Use an initial crypto trade draft, an initial
History list with a real event, and the initial email form. Keep supporting
order, History and session states in the behavior evidence below.

| Geometry anchor | Desktop approved target | Phone approved target |
|---|---|---|
| Workspace and trade chooser | 1360px wide, chooser at `40,127` | 358px wide, chooser at `16,88` |
| Trade ticket and preview | Aligned at y≈289, widths ≈752px and ≈590px | Stacked at x=16, both 358px wide |
| History toolbar and summaries | Chooser and filter row at y≈127, first summary around y=220 | Chooser before filters, first summary around y=233 |
| Email panel and field | Centered, 415px panel and ≈339px inner field | 358px panel and ≈316px inner field |

Record element boxes for the chooser, trade heading and both panels, History
filter row and first disclosure, and sign-in panel and field. Compare position,
order, spacing, visible controls and value hierarchy. Document geometry
differences tied to live content, including working form height, auth-gated
navigation, the existing Update action and server-produced amounts. Bind the comparison
to the tested source, approved ZIP SHA-256, specimen viewports and screenshot
hashes using the Phase 24 pairing pattern. [Measured prototype](25-RESEARCH.md#measured-approved-reference) ·
[Prior paired evidence](../24-compare-portfolio-performance/24-BROWSER-RECEIPT.md)

- Exercise live-app crypto amount and quantity, an actual crypto receipt,
  curated and catalog stock previews, closed or paused state, requote and
  ambiguous-result recovery. Check the resulting same-portfolio cash and
  History, and the existing market- and portfolio-chart fallback states.
- Exercise initial and filtered History, expanded correction with its
  original detail, a matching event beyond the unfiltered first page,
  load-more failure/retry and completion. Exercise request and entry of
  a real isolated email code, form validation or failure, focus transfer
  and sign-out.
- Check keyboard access and focus through each surface. At 320px assert
  the controls and values remain readable and usable with zero horizontal
  page overflow. Repeat with 200% CSS text enlargement and record the method.
  Record native browser zoom separately when actually exercised.

## Registry safety

| Registry | Blocks used | Safety gate |
|---|---|---|
| shadcn official | Checked-in `Button`, `Card`, `Input` | Local source use and neutral preset verified 2026-11-26 |
| Third-party | No imported blocks | Existing component config has an empty registry map, checked 2026-11-26 |

## Checker sign-off

- [x] Dimension 1 Copywriting
- [x] Dimension 2 Visuals
- [x] Dimension 3 Color
- [x] Dimension 4 Typography
- [x] Dimension 5 Spacing
- [x] Dimension 6 Registry safety

The independent UI checker passed all six dimensions on 2026-11-26.
