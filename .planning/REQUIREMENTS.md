# Requirements: Birja v1.3 — Interface Redesign

## v1.3 Requirements

### Approved interface

- [x] **UI-01** — The Birja logo, wordmark, Markets, Portfolios, History and door control fit one header row on supported phones and desktops. The current destination is identifiable.
- [x] **UI-02** — The door focuses the current sign-in field or signs out directly. OTP, session refresh, failed logout recovery and private-data clearing work with the backend. Old Account URLs return to Markets, and signed-in system status remains at `/health`.
- [x] **UI-03** — Users can browse and search crypto and stocks, see the selected asset and start a trade. IEX attribution, stock eligibility and market-hours restrictions remain visible where needed.
- [x] **UI-04** — Users open strategies through whole-card links and create them through the final New portfolio card. Cards show cash, value and return. Users can set a name and optionally add or clear a description.
- [x] **UI-05** — A selected portfolio has one switcher, Edit, Remove and Update toolbar. Its overview shows profit or loss and cash, stock and crypto allocation. Holding cards offer filtering, sorting and trade actions. Unavailable valuations remain explicit.
- [x] **UI-06** — Both order tickets preserve correct portfolio context, preview, confirmation, receipt, rejection and recovery from an uncertain order result. Orders affect only the selected portfolio.
- [x] **UI-07** — History has one switcher and Update control. Expandable cards retain the exact recorded values, order, pagination, and original references for trades, dividends, corrections and splits.

### Verification and delivery

- [x] **QA-01** — Keyboard, phone and desktop workflows, and enlarged-text layouts pass verification. Owner-accepted design decisions and representative release-candidate evidence are recorded.
- [x] **QA-02** — Changed code passes review and the existing frontend, backend and isolated browser checks. Tests cover session, portfolio ownership and deletion, trade economics and History across the redesigned flows.
- [ ] **QA-03** — A milestone audit links requirements to actual verification. The reviewed release candidate has the required PR and CI evidence before merge. Release and production actions follow the established approval workflow.

## Future requirements

See [DEFERRED.md](DEFERRED.md) for live stock status transport and other separately tracked work. Phase 7 owner acceptance is closed.

## Out of scope

New trading behavior, provider activation, speculative API or schema changes, production data in local tests, and unrelated repository tooling. Backend changes address demonstrated problems in the approved flows.

## Traceability

| Requirement | Phase | Status |
|---|---|---|
| UI-01 | Phase 16 | Complete |
| UI-02 | Phase 16 | Complete |
| UI-03 | Phase 16 | Complete |
| UI-04 | Phase 16 | Complete |
| UI-05 | Phase 16 | Complete |
| UI-06 | Phase 16 | Complete |
| UI-07 | Phase 16 | Complete |
| QA-01 | Phase 16 | Complete |
| QA-02 | Phase 17 | Complete |
| QA-03 | Phase 17 | Pending |
