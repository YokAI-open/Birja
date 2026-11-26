# Phase 25 — Finish the trading flows and verify the integrated app

Use the approved v1.5 prototype, existing Birja design system and FLOW-01
through FLOW-04. These decisions carry forward the approved design and
milestone requirements.

<decisions>

- **D-01:** Match the trade workspace for crypto, curated stocks and catalog
  stocks. Keep one portfolio chooser, cash and holdings, meaningful price and
  market state, the real order preview and receipt. Preserve crypto amount
  and quantity, stock whole shares, fee display, renewed confirmation and
  original-request recovery. Receipts, cash and History must reconcile to
  the same portfolio.
- **D-02:** Match the compact History toolbar and expandable activity list.
  Preserve activity and asset filters, exact cursor ordering, pagination and
  all existing event details, including corrections and held events.
- **D-03:** Match the sign-in panel and header door control. Run the real
  request-code, verify-code and sign-out paths with visible labels, focus and
  feedback. Use the configured console transport on the isolated stack.
- **D-04:** Compare the running app with the approved ZIP on desktop and
  mobile. Verify authenticated and signed-out flows, safe chart fallbacks
  and representative full-stack trades, portfolio and History journeys.
  Preserve existing financial and session checks.
- **D-05:** Qualify the integrated candidate with review and local evidence,
  then require hosted CI on the authorized release candidate. Reuse verified
  Phase 24 recovery evidence for identical relevant local inputs. Account for
  the measured recovery timing during CI planning. Keep Phase 23 CHART-04
  tracked separately as live history qualification.

</decisions>

The prototype's `trade.html`, `history.html` and `sign-in.html` define
layout and interaction. Existing server APIs define cash, holdings, order
state, event details, session state, and ordering. The established
publication approvals govern hosted CI and release operations.

## References

- [Approved v1.5 prototype](../../ui-reviews/v1.5/README.md)
- [Approved requirements](../../REQUIREMENTS.md)
- [Phase 23 source qualification](../23-show-historical-market-prices/23-SOURCE-QUALIFICATION.md)
- [Phase 24 verification](../24-compare-portfolio-performance/24-VERIFICATION.md)
- [Phase 24 recovery receipt](../24-compare-portfolio-performance/24-RECOVERY-RECEIPT.md)
- [Birja design system](../../../design-system/birja/MASTER.md)
