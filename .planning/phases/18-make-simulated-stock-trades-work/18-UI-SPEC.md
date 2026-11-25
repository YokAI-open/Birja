# Phase 18 trade ticket contract

Use the established [Birja design system](../../../design-system/birja/MASTER.md)
and `StockTradePage` with its existing order form, portfolio selector, cash
amount, preview and receipt. Keep the current layout, type, spacing and palette.

| State | Behavior |
|---|---|
| Fetching an eligible price | Show the existing inline preview loading treatment. Keep the typed whole-share quantity. |
| Reported halt | Explain that trading is paused in the existing message area. Disable confirmation. When using the reported-halt feed, show that halt reports can be delayed or incomplete. |
| Closed | Preserve Market closed and the opening countdown. If a permitted last mark is present, keep it visible. |
| Price stale or check unavailable | Use one concise reason near the existing preview. Allow a fresh preview when data returns. |
| Price changed | Reuse the existing old/new price and total review and require confirmation again. |
| Fill or recovered result | Reuse the receipt and exact cash and quantity. Preserve its portfolio context in the existing selector and server intent. |

Keep keyboard focus visible, existing controls accessible on phones and at 200%
zoom, and announce state changes without a repeating countdown announcement.
Avoid duplicate status text, labels, and additional retry buttons. Verify
representative normal, halted, stale, repriced and recovered results. UI/UX Pro
Max's inline error and announcement guidance applies where the copy changes.
