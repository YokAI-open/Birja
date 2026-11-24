# Phase 20 stock trade and valuation contract

Use the existing [Birja design system](../../../design-system/birja/MASTER.md)
and [Markets layout](../../../design-system/birja/pages/markets.md). Keep the
single stock search, shared header and one portfolio selector. Extend the
existing stock order and receipt components to the stable catalog route.

## Trade through Markets

- Use a single **Trade** action for an eligible result and **View details** for
  a read-only result. Carry the catalog ID through portfolio choice and switching.
  Keep distinct share class and exchange visible for ambiguous ticker text.
- Use the current Buy/Sell toggle, whole-share input, Buy max and Sell all.
  Show available cash once. Highlight the relevant IEX side and show the exact
  executable price, quantity, signed cash change and source time in preview.
  Keep price source and fee disclosure short within the existing preview.
- Price changes show the prior and new price and cash change and require a new
  confirmation. Leave the user on the original receipt after a fill or retry.
  Offer the existing Portfolio and Trade again actions. Switching owner or
  portfolio invalidates pending review and clears any mismatched display.
- Keep the edited quantity on closure or a hold and provide the relevant reason.
  A closed panel shows **Market closed** and **Opens in X hr Y min** when the
  reopening time is verified. Keep the permitted last mark and its timestamp
  in the existing accessible price detail without adding a timestamp line to
  the closed panel. Prevent preview/confirmation until eligibility is current.
  For a reported halt, use concise reason copy and the existing coverage note.
- Place a specific quantity error beside its field and connect it via
  `aria-describedby`. Announce settled preview replacements or refusals once.
  Keep visible focus and the mobile Back-to-results focus return. Use Birja's
  existing tap targets, tokens, type, and reduced-motion handling.

## Portfolio and History

- Keep existing holding cards, filters and sorting. Show the authorised human
  ticker and name for the current issue, with the same quote/as-of and P/L
  semantics. Keep known cash and priced values when any holding lacks a mark.
  Use **Known value** with the unpriced count, and suppress whole-portfolio
  return and allocation percentages while their denominator is incomplete.
- Keep History date, original market label, share quantity, cash delta and
  original-event link. Show dividend, split and correction on their existing
  cards. A new ticker occupant cannot replace a historical label or open the
  other issue's trade ticket.

Use focused component tests plus the actual disposable browser stack for the
out-of-list round trip, repricing, read-only conditions, incomplete valuation,
wide and narrow screens, keyboard and 200% equivalent reflow. Report native
zoom only when it is actually exercised. Local UX guidance confirmed connected
inline errors and focus management. Existing visual approvals carry forward.
