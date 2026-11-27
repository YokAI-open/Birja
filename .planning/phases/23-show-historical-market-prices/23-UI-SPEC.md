---
phase: 23
slug: show-historical-market-prices
status: approved-direction
created: 2026-11-26
---

# Phase 23 — Markets UI contract

The approved [prototype ZIP](../../ui-reviews/v1.5/PROTOTYPE.zip) supplies the
visual reference. Keep existing React, Tailwind, Inter and scheme tokens.
Use existing assets, decorative letter tiles and Canvas for the plotted data.
Keep real API copy and provider-mandated attribution where needed.

| Area | Target |
|---|---|
| Header and tabs | Preserve the Phase 22 account control, active navigation, 44px targets and single portfolio selector. US stocks and Crypto stay in the same order as the ZIP. |
| Asset list | Restore 36–40px decorative ticker tiles and ticker-first rows. Use restrained neutral tiles with readable symbols and quiet dividers. Keep the current venue and class where they distinguish a listing. Price and valid Day change align to the right. Leave absent changes empty with accessible availability text where needed. |
| Layout | At wide widths use the prototype's approximately 42:58 split, 28–32px column gap and aligned search/list and detail. Use a 16px mobile gutter and 16–20px panel padding with a stacked result panel. Keep Back to results and focus restoration. Keep long names and narrow/large-text layouts free of overlap and horizontal page scrolling. |
| Detail | Align the asset tile, name, symbol and concise open/closed state at the top. Put the current price and any comparable daily change immediately below. The chart follows, then the bottom action row, with Trade or View details aligned right when space allows. |
| Closed stocks | Keep the permitted mark, Market closed and the verified countdown from Phase 22. The historic series can still render. Keep entry to the existing read-only ticket and leave order authority to the existing ticket/backend. |
| Chart | Use a roughly 278px plot on desktop and 232–240px on phones. Labels, axis values and the plotted line share the same normalized series. Default 1W. Place 1D/1W/1M buttons above the plot in an accessible group with pressed state. Use tabular prices and existing semantic gain/loss tokens. Break the line across missing intervals and closed sessions. |
| Accessible data | Give the chart a readable caption, source and window, and an expandable Price data control listing actual times and closes in a simple table. Use browser-local dates with explicit exchange-session or crypto time basis. Keyboard access, status text and readable tables work without hover or color alone. |
| Incomplete or unavailable | State `Some price intervals are missing`, `No history for this range` or `Couldn’t load price history` as appropriate. Keep the period controls and any authorized ask/bid trade path usable. An unavailable or unqualified source gets a concise history-only state. For delayed series show `History behind · As of …` with the actual latest completed bar time and preserve any partial coverage message. |

Compare four like-for-like pairs against fresh ZIP renders at the same
viewport and zoom. Capture an open and a closed stock at 1440px, a 390px
selected catalog result using a matching search in the ZIP, and a 1440px
crypto selection. Keep a separate functional check for every range. Verify 320px and enlarged-text reflow. For matched fixture colors and
geometry verify position of tabs, tiles, quote, period controls, plot and
action in both views. Use semantic heading and normal contrast, and record
real-data copy differences such as attribution, partial coverage and the
prototype's demo switch. The screenshots come from the running app. Resolve material mismatches
in named visual elements before passing the design check.

## Contract check

Specific button and failure copy, quote-led visual hierarchy, restricted
brand accent, existing Inter roles, four-pixel spacing and current local
component assets satisfy the six GSD UI contract dimensions.
