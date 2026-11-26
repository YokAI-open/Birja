# Markets

Use Inter, warm paper, dark ink and a restrained fox-red accent for the
selected market and keyboard focus. Put the supplied fox artwork in the
shared header. Store the originals and web-ready assets in
`frontend/public/brand/`.

- Start with US stocks and Crypto controls, a name or ticker search and a
  roomy list. The header navigation provides the visible page name. Retain a
  visually hidden page heading for assistive technology. Align available prices
  to the right. Flag delayed or stale
  crypto prices where they appear.
- Show the original 20 stocks by default. Searching uses the eligible listing
  catalog and Crypto has its own list and query.
- Keep the list and selected asset side by side from 768px. Below that width,
  stack the detail below the list. A selected row brings focus to the detail
  heading. Use Back to results to return focus to the row or the search field.
  Keep the asset, price, update time and next action together.
- Show one action for the selected asset. Use **Trade** when trading is
  available, **Check price** for older crypto quotes and **View details**
  for read-only stocks. Carry the symbol forward when choosing a portfolio.
- Label IEX midpoint prices and show why trading is restricted in the
  selected stock pane. Open the stock ticket for bid and ask prices.
- While the market is closed, keep the last verified price while display
  permission is current. Keep the price panel to **Market closed** and a
  reopening countdown when the next session is verified.
- Keep required provider attribution with the stock rows and detail price
  where their data contract requires it.
