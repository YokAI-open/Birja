# Markets

Use Inter, warm paper, dark ink and a restrained fox-red accent for the
selected market and keyboard focus. Put the supplied fox artwork in the
shared header. Store the originals and web-ready assets in
`frontend/public/brand/`.

- Start with Crypto and US stocks controls, a name or symbol search and a
  roomy list. The header navigation provides the visible page name. Retain a
  visually hidden page heading for assistive technology. Align available prices
  to the right. Flag delayed or stale
  crypto prices where they appear.
- Show the selected asset in a detail pane on desktop and a dedicated view
  on phones. Keep the asset, price, update time and next action together.
  Return focus to the selected row when going back on a phone.
- Show one action for the selected asset. Use **Trade** when trading is
  available, **Check price** for older crypto quotes and **View details**
  for read-only stocks. Carry the symbol forward when choosing a portfolio.
- Label IEX midpoint prices and show why trading is restricted in the
  selected stock pane. Open the stock ticket for bid, ask and
  regular-session details.
- While the market is closed, keep the last verified price while display
  permission is current. Keep the price panel to **Market closed** and a
  reopening countdown when the next session is verified.
- Show required provider attribution with the stock list and below the
  action on the mobile detail view when a price is shown.
