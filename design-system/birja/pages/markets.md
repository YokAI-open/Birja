# Markets

Use Inter, warm paper, dark ink and a restrained fox-red accent for the
selected market and keyboard focus. Put the supplied fox artwork in the
shared header. Store the originals and web-ready assets in
`frontend/public/brand/`.

- Start with US stocks and Crypto controls, one portfolio selector and a
  name or ticker search. The header navigation provides the visible page name.
  Retain a visually hidden page heading and search label. Use 38px decorative
  ticker tiles, quiet row dividers, and right-aligned price and Day columns.
  Flag delayed or stale crypto prices where they appear.
- Show the original 20 stocks by default. Searching uses the eligible listing
  catalog and Crypto has its own list and query.
- Fit the approved 1360px desktop workspace with a 41:59 split and 28px gap.
  Stack the list and detail below 768px with 16px gutters at phone widths.
  A selected row on a phone brings focus to the detail heading. Back to results
  returns focus to the row or search field. Set the identity and session state
  above the current price. Put the chart below the quote and the action at the
  right edge of the panel footer.
- Show one action for the selected asset. Use **Trade** when trading is
  available, **Check price** for older crypto quotes and **View details**
  for read-only stocks. Carry the symbol forward when choosing a portfolio.
- Label IEX midpoint prices and show why trading is restricted in the
  selected stock pane. Open the stock ticket for bid and ask prices.
- While the market is closed, keep the last verified price while display
  permission is current. Show **Market closed** and a reopening countdown when
  the next session is verified. The chart can still show prior sessions.
- Keep required provider attribution with the stock rows and detail price
  where their data contract requires it.

## Price history

- Start with one week. Keep the 1D, 1W and 1M buttons keyboard-accessible
  with a pressed state and 44px targets.
- Use a 278px desktop plot and a 234px phone plot with the neutral data-fill
  token. Connect consecutive bar closes, drawing breaks for missing intervals
  and closed sessions. Show the source, time basis and split treatment below
  the plot. Price data expands to the same dates and decimal closes in a table.
- Fill Day for the selected row only when the series supplies a comparable
  change. Render a reported period change with its selected range. Leave absent
  changes blank and announce delayed or partial history in the chart region.
- Current quotes, reopening times and eligible trade actions use their own
  inputs. The history region can show a loading, empty, partial or unavailable
  state while those controls remain usable.
