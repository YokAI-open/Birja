# Phase 21 browser acceptance contract

Use the current [Birja design system](../../../design-system/birja/MASTER.md),
[Markets layout](../../../design-system/birja/pages/markets.md), and
[Phase 20 stock interface contract](../20-trade-and-value-stocks-from-search/20-UI-SPEC.md).
Phase 21 verifies the release UI. A confirmed release-blocking defect may
require a targeted repair.

| Journey | Observable outcome |
|---|---|
| Search and select | Search by ticker and company name, select an eligible issue outside the original 20 with the keyboard and verify the exact ticker, share class and exchange. Visible focus reaches the selected result and returns on mobile back. |
| Review and trade | Select the intended portfolio in the existing selector. Cash is visible. A whole-share buy uses the eligible ask and sell uses the bid. A changed price requires fresh confirmation. The original receipt and corresponding private History reconcile to cash and holdings. |
| Closed, halted and stale | Closed Markets and trade show the last permitted mark and the reopening countdown. A reported halt or stale quote gives a specific reason. Orders stay blocked in all three states. |
| Mixed portfolio | Cash and eligible holdings stay visible when a stock is unpriced, and Portfolio shows the incomplete total. Crypto remains accessible. |
| Reflow | Verify the affected keyboard path on desktop and equivalent reflow at narrow widths. No obscured focus, overlapping controls or horizontal page scroll. Record native desktop zoom only if actually measured. |

Use the guarded catalog browser suite for replayable candidate evidence. Use
the authorized live production browser lane for the one-portfolio round trip.
Keep identities, codes and account details out of screenshots and reports.
