---
phase: 22
slug: adopt-the-market-workspace
status: approved-direction
shadcn_initialized: true
preset: existing
created: 2026-11-26
---

# Phase 22 — Markets UI design contract

The approved prototype and `design-system/birja/MASTER.md` govern the
design. Update `design-system/birja/pages/markets.md` where its earlier
mobile-only detail pattern differs. Existing React, Tailwind, local Inter,
brand image assets and Lucide are sufficient. Registry additions are empty.

## Layout and hierarchy

- At normal text size the header is one row at 320px, 390px, 768px and 1440px. Allow wrapping when enlarged text needs more room. Fox and Birja sit
  with Markets, Portfolios and History. The active destination uses the
  dark pill. A 44px account door target uses the existing Sign in or Sign
  out accessible name. The Markets h1 remains available to screen readers.
- Put US stocks, Crypto and the owned portfolio chooser at the top. On
  wide screens the tabs are at left and the selector at right. On narrow
  screens the toolbar can wrap below the single-row header.
- At 768px and up use a two-column grid with a roughly 42:58 list-to-detail
  ratio. The left side is a search box and ruled list. Each row shows
  ticker, name and available price, with exchange and class where needed
  to distinguish results. There is one focusable control per row. The
  detail panel anchors the page with the selected name and large price,
  a concise state and one primary action. Keep the no-selection surface
  compact when search results await explicit selection.
- Under 768px stack search, list and selected detail in DOM order. A
  selection puts focus on the detail heading and scrolls it into view.
  A visible `Back to results` control returns focus to the invoking row,
  or search when the row is gone. The list preserves input and selection.
  A bounded list may scroll vertically. No keyboard trap, covered focus
  or page-wide horizontal overflow.
- Reuse the existing owned portfolio combobox. In Markets, its accessible
  name is `Trading portfolio` and the description explains that selection
  changes the portfolio for the next trade. Keep the selected quote and
  search when it changes.

## Spacing, typography and color

Use 4/8px for small alignment, 12/16px around row content, and 20/28/32px
for panel padding, group spacing and desktop gaps. Preserve a 44px minimum
for controls and a 52px search field. Use a 16px minimum mobile page gutter.

| Role | Size | Use |
|---|---|---|
| Supporting | 13–14px | Secondary metadata, status and column labels |
| Body | 16px | List text and controls |
| Heading | 24px | Selected instrument |
| Display | 32–52px | Current price with tabular numerals |

The warm UI is mostly canvas `--background`, with `--card` for the detail
surface, `--foreground` for text and the primary action, and `--border`
between rows. Fox `--brand` emphasizes the selected market and keyboard
focus. Outcome colors continue to pair with readable text. Draw no
decorative chart, percentage placeholder or status badge.

## State copy

| State | Visible behavior |
|---|---|
| Awaiting catalog selection | `Select a stock to see its price.` Selecting a result requests that listing. |
| Search returned nothing | `No matching stocks. Try another name or ticker.` Crypto keeps its existing empty copy. |
| Catalog or current quote failure | Use the existing specific error and retry when it can recover. Default browse and the other asset tab stay reachable. |
| Ready | `Trade AAPL` or `Trade BTC` using the actual symbol and chosen portfolio. |
| Read-only or old crypto price | `View details` or `Check price` as appropriate, with the symbol in the accessible name. Explain the actual restriction. |
| Confirmed market closure | Show the permitted last price, `Market closed` and `Opens in 2 hr 30 min` using the real interval. Keep source time and local opening time accessible without a repeated visible date line. Show `Market closed` alone if the opening is unverified. |
| Explicit portfolio awaiting access | Keep market data visible and suspend the trade link while access resolves. If unavailable, show `Choose an available portfolio` and point to the existing chooser. |

Provider attribution stays where the current data contract requires it.
Compact required attribution is separate from closure instructions.
Use one polite announcement for settled state changes. The visual minute
countdown updates without repeated live-region announcements. Browser
verification uses deterministic complete and missing-mark states and
captures 1440px and 390px real-app views.

## Contract review

Review copy specificity, quote-led hierarchy, token reuse, the four
typographic roles, the spacing scale and empty registry additions before
implementation. Confirm actual viewports and keyboard paths during execution.

Planning check on 2026-11-26 passed all six design-contract dimensions.
The copy names the action or recovery. The current price leads the
hierarchy. Fox red is limited to selection and focus. Four Inter roles
and the project spacing scale cover the layout. The design uses the
existing component and icon sources.
