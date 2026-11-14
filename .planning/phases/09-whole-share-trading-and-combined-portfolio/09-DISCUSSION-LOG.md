# Phase 9: Whole-Share Trading and Combined Portfolio - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves alternatives considered.

**Date:** 2026-11-11
**Phase:** 09-whole-share-trading-and-combined-portfolio
**Areas discussed:** Trade ticket; Combined portfolio; Closed or unavailable valuations

The owner selected all three areas. This was the default interactive discussion mode.

## Trade ticket

### 1. Offer Buy max and Sell all alongside the editable whole-share input?

**Options presented:**

- Whole-share input + Buy max / Sell all (Recommended)
- Whole-share input only

**User’s choice / captured clarification:** Whole-share input + Buy max / Sell all; both populate quantity and still require preview and confirmation.

### 2. Show both IEX bid and ask with the selected execution side highlighted, or only the selected price?

**Options presented:**

- Show bid and ask; highlight the selected side (Recommended)
- Show only the selected side's price

**User’s choice / captured clarification:** Show bid and ask; highlight the selected side. Buy uses ask; sell uses bid.

### 3. How should the mandatory changed-price preview present updated figures?

**Options presented:**

- Show old → new price and total change (Recommended)
- Replace figures with a price-updated notice

**User’s choice / captured clarification:** Show old → new price and total change; require confirmation again.

### 4. Stay on the receipt or navigate automatically to Portfolio after a fill?

**Options presented:**

- Stay on the receipt; offer Portfolio / Trade again (Recommended)
- Open Portfolio automatically with confirmation

**User’s choice / captured clarification:** Stay on the receipt; show updated cash/share balance and offer Portfolio / Trade again.

### 5. More trade-ticket details or move to the combined portfolio?

**Options presented:**

- Move to the combined portfolio (Recommended)
- Discuss more trade-ticket details

**User’s choice / captured clarification:** Move to the combined portfolio (Recommended)

## Combined portfolio

### 1. One combined holdings list or separate stock and crypto sections?

**Options presented:**

- One combined holdings list with asset labels (Recommended)
- Separate Stocks and Crypto sections

**User’s choice / captured clarification:** One combined holdings list with asset-type labels, shared cash and portfolio summary.

### 2. Default holdings order?

**Options presented:**

- Alphabetically by ticker (Recommended)
- Largest holding value first

**User’s choice / captured clarification:** Alphabetically by ticker; rows remain stable through price refreshes.

### 3. Show holding figures directly or expand cost details?

**Options presented:**

- Show the figures directly in table/mobile cards (Recommended)
- Compact summary with expandable cost details

**User’s choice / captured clarification:** Show quantity, average cost, cost basis, current value, gain/loss and allocation directly in a desktop table and stacked mobile cards.

### 4. Allocation panel grouping?

**Options presented:**

- Cash / Stocks / Crypto summary bars (Recommended)
- A separate bar for cash and every holding

**User’s choice / captured clarification:** Cash / Stocks / Crypto summary bars; individual holding percentages remain in the list.

### 5. More portfolio details or move to closed/unavailable valuations?

**Options presented:**

- Move to closed/unavailable valuations (Recommended)
- Discuss more portfolio details

**User’s choice / captured clarification:** Move to closed/unavailable valuations (Recommended)

## Closed or unavailable valuations

### 1. What headline should appear when a holding cannot be valued?

**Options presented:**

- Show “Known value: $X — incomplete” and the unvalued holding count (Recommended)
- Show “Portfolio value unavailable”

**User’s choice / captured clarification:** Show Known value: $X — incomplete and the unvalued holding count. Known cash/holdings remain visible; overall gain/loss and allocation percentages are unavailable while the total is incomplete.

### 2. How should a verified trading halt without corporate-action uncertainty affect valuation?

**Options presented:**

- Keep the dated last verified price with “Halted” label (Recommended)
- Show valuation unavailable until trading resumes

**User’s choice / captured clarification:** Keep the dated last verified price with a prominent Halted label; orders stay blocked. Uncertain corporate actions still make valuation unavailable.

### 3. Allow quantity editing while a stock is closed or temporarily unavailable?

**Options presented:**

- Allow quantity editing; disable confirmation and explain why (Recommended)
- Make the ticket read-only until trading is available

**User’s choice / captured clarification:** Allow whole-share quantity editing; disable confirmation and explain why. This is a draft only, never a queued order; require a fresh preview when trading becomes available.

### 4. Retain or clear quantity if a closure or hold interrupts review?

**Options presented:**

- Retain the quantity; require a fresh preview and confirmation (Recommended)
- Clear the quantity when trading becomes unavailable

**User’s choice / captured clarification:** Retain quantity; invalidate the existing preview and require a fresh preview and explicit confirmation. Nothing executes automatically.

## Context creation

**Question:** Write the Phase 9 context document, or discuss more details?
**Options:** Write the Phase 9 context document (Recommended); Discuss more details.
**User’s choice:** Write the Phase 9 context document (Recommended).

## Agent’s Discretion

No explicit delegation of product preferences. Technical implementation and exact visual details remain for research/planning within approved decisions and the existing design system.

## Deferred Ideas

None raised. Existing live-data/activation deferrals and Phase 10/11 boundaries remain unchanged.
