# Phase 24 — Compare portfolio performance

Phase scope comes from the approved v1.5 prototype, requirements and roadmap.
The user asked to bring the approved redesign and its charts into the running
app. The prototype's `portfolios.html` and `portfolio.html` are the reference.

<decisions>

- **D-01:** Use fully clickable portfolio cards with name, optional
  description, cash, total and return. The last card creates a portfolio.
  Preserve creation, editing, switching and closure and their empty and
  maximum-portfolio states.
- **D-02:** Show a 30-day sparkline and a readable summary from each active
  portfolio's own recorded daily values. Keep current figures visible through
  empty, partial and failed history. Leave gaps for missing observations.
- **D-03:** Collect one immutable observation per active portfolio per UTC day
  from capture enablement forward. Reuse current valuation and original
  starting cash. Use the 22:00–24:00 UTC collection window and the actual
  capture time. Validate ownership, retry, closure and encrypted recovery.
- **D-04:** Put the portfolio chooser and Edit, Update with age, and Remove
  above value, profit and Cash, Stocks and Crypto allocation. Place holding
  cards with asset filters and Highest value, Ticker A–Z and Highest return
  sorting below. Use Highest value by default and rank returns by percentage.
  Preserve current trade destinations and incomplete valuation messages.
- **D-05:** Compare the running overview and selected portfolio with the
  approved ZIP on desktop and mobile. Keep typography, controls and real
  financial states consistent with the rest of Birja.

</decisions>

The 30-day display window and UTC capture window are planning defaults.
Phase 24 can run with Phase 23's historical market-bar source disabled.
Broader redesign and release acceptance belong to Phase 25.

## References

- [Approved prototype](../../ui-reviews/v1.5/README.md)
- [Requirements](../../REQUIREMENTS.md)
- [Roadmap](../../ROADMAP.md)
- [Technical research](24-RESEARCH.md)
- [Phase 22 verification](../22-adopt-the-market-workspace/22-VERIFICATION.md)
- [Design system](../../../design-system/birja/MASTER.md)
