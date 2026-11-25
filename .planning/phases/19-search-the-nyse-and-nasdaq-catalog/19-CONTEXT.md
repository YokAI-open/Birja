# Phase 19 context

Source: approved v1.4 roadmap, requirements and Phase 18 handoff.

<domain>

Make active common shares on the New York Stock Exchange and Nasdaq searchable
by ticker and company name, including symbols beyond the original 20. Keep
search, result details and the existing portfolio-specific trade entry usable
on desktop and mobile. Phase 20 owns fills and valuation for newly found
stocks. Phase 21 owns release, production activation and live acceptance of
an out-of-list buy and sell.

</domain>

<decisions>

- **D-01:** Search the refreshed local catalog. Return bounded results with exact
  ticker matches first, support verified aliases and keep share classes distinct.
- **D-02:** Preserve identity and historical links across listing changes.
  Hold ambiguous matches for review and block inactive instruments from
  new orders.
- **D-03:** Show company, ticker and listing exchange. A selection can request
  its own quote and open the trade entry for the selected portfolio. Show the
  actual eligibility reason when a price or order is unavailable.
- **D-04:** Search and the last verified catalog survive quote source failure,
  rate limits and failed catalog refreshes. Use the existing free-data approach
  and require applicable rights for display and retention.
- **D-05:** Keep Birja's approved Markets layout, Inter typography and light
  palette. Use one search field and useful result information. Preserve
  previously approved closed-market copy and the viewer-local countdown.
- **D-06:** Preserve Phase 18 execution authority and all existing crypto and
  portfolio behavior. Full release CI and the remaining historical recovery
  diagnostics stay with Phase 21.

</decisions>
