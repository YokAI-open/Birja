# Phase 19 stock search contract

Use the [Birja design system](../../../design-system/birja/MASTER.md)
and its [Markets rules](../../../design-system/birja/pages/markets.md). Keep
the US stocks section, ruled rows, desktop detail pane, mobile detail view,
and shared portfolio selector.

- Use one visible “Search stocks” label and a “Name or ticker” placeholder.
  Keep the input editable during loading. Support one-letter tickers,
  pasted names and IME composition. Use TanStack Query with a short debounce,
  cancellation and results keyed to the submitted search text.
- Show ticker, company, listing exchange and any distinguishing share
  class. Keep one focusable control per result. Exact ticker matches come
  first. If more than the bounded page matches, prompt the user to refine.
- Keep the original stocks available in the initial browse view. Show
  “No matching stocks” with a short suggestion to try a ticker or company
  name. Announce settled results politely once.
- On desktop, keep search and results visible when a detail opens. On
  mobile, move focus to the detail heading and restore it to the result
  on return. Retain query and selection across data refreshes.

Show the company, ticker and exchange first in the detail. A selected
eligible listing can request one price. Show its source time and required
attribution using existing formatting. A late response for a previous
selection cannot change the visible detail.

| State | Visible behavior |
| --- | --- |
| Price received | Show price and source time. Offer the trade ticket for the same listing and portfolio. |
| Price missing or rate limited | Show one concise reason. Offer one retry where supported. |
| Market closed | Keep an eligible cached mark if present. Show “Market closed” and “Opens in X hr Y min” when the reopening time is verified. Use the viewer's clock. |
| Listing or price needs review | Explain the reason next to the action. Keep confirmation disabled. |
| Catalog temporarily unavailable | Keep the last verified permitted results. Show one retryable message if none exist. |

Phase 19 opens a read-only catalog ticket with the listing identity and
portfolio fixed. Confirmation for newly found stocks becomes available in
Phase 20 after execution checks are in place. An inactive or ambiguous listing
cannot expose an actionable order form. Keep the original curated stock trade
entry available from the existing browse view, and preserve crypto trading.

Check keyboard operation, visible focus, long issuer names, touch targets,
mobile reflow and desktop at 200% zoom. Reuse existing tokens and native
controls. The UI/UX Pro Max search centered on focus, empty results and
settled status updates.
