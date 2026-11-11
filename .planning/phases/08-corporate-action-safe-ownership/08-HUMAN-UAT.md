---
phase: 08-corporate-action-safe-ownership
status: awaiting-owner-review
owner_acceptance: pending
source: [08-LOCAL-PROOF.md, 08-UI-REVIEW.md, 08-11-BROWSER.md]
prepared: 2026-11-11
---

# Phase8 presentation acceptance

This packet concerns the new corporate-action safety presentation only. Phase7
UI acceptance is retained; its deferred live-data evidence is a separate gate.
These are actual authenticated synthetic browser captures, not production or
provider acceptance. No services, builds or tests are requested from the owner.
Final local validation passed; no owner acceptance has been inferred. Full
frontend429tests, backend1551tests,31browser passes plus1expected production-CSP
skip, exact six-revision recovery and all five strict image scans are recorded
in08-LOCAL-PROOF.md. Independent UI24/24 and source/security reviews are clear.

## Actual examples

- [Mobile375px held stock](/tmp/birja-phase08-ui-mqq4ss1g/screenshots/actions-375-first-stock.png)
- [Desktop1280px held stock](/tmp/birja-phase08-ui-mqq4ss1g/screenshots/actions-1280-first-stock.png)
- [Full mobile catalogue and crypto](/tmp/birja-phase08-ui-mqq4ss1g/screenshots/actions-375.png)
- [Full desktop catalogue and crypto](/tmp/birja-phase08-ui-mqq4ss1g/screenshots/actions-1280.png)
- [Actual200%CSS zoom](/tmp/birja-phase08-ui-mqq4ss1g/screenshots/actions-css-zoom-200pct-first-stock.png)

CSS zoom preserves desktop media queries; the separate640CSS-pixel reflow
case at2x density complements it. Neither is described as native toolbar zoom.
The screenshot source is0cea8b5, StockSection SHA256
`aee6a806a4588c1af653fe84f2e40cecae286a2fa59101369f3c4cb98ef2516d`.
See08-11-BROWSER.md for complete receipts and capture inventories.

## Focused review

### 1. Held stock remains clear and readable

Expected: the affected stock shows its fixed review reason and “Valuation
unavailable”, with no bid/ask or quote timestamp. Reasons and dated check times
wrap without clipping or adjacent-cell overlap. Corporate actions, Stock status
and Trading are separate facts; no stock Buy/Sell/Resolve control appears.

Result: pending owner review.

### 2. Other instruments and notices remain independent

Expected: unaffected stocks retain their own current information; all20 stock
identities and15 crypto instruments remain discoverable. Crypto keeps Trade
controls. “IEX prices”, single-venue explanation and the stock-trading-coming-later
notice remain visible. A healthy quote does not override a corporate-action hold.

Result: pending owner review.

### 3. Monitoring and recovery behavior is honest

Expected: unavailable checks show a fixed reason instead of guessed valuation;
post-split waiting shows no price until a compatible verified quote arrives.
Known expiry removes values before the next poll. Request failure retains retry;
failed manual retry returns focus to its button, successful retry to the section
heading. Background polling/expiry never moves keyboard focus. Automated RTL,
real browser assertions and independent source/visual review cover these changes;
the owner is asked for presentation approval, not to reproduce the tests.

Result: pending owner review.

## Disposition

Owner response: pending. A generic instruction to continue is not new UI approval.
No whole-phase completion or external permission is established by this packet.
