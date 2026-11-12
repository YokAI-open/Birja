---
status: draft
phase: 09-whole-share-trading-and-combined-portfolio
source: [09-UI-SPEC.md, 09-LOCAL-PROOF.md, 09-UI-SOURCE-HASHES.json]
---

# Phase9 new interface acceptance packet

Final automated/review gates14 must pass before requesting owner acceptance15.
Prior Phase7/8 acceptance does not approve these new screens. No owner result
is inferred; all items below remain pending. Synthetic-only artifacts prove
local UI behavior, not provider rights or public readiness.

## Review screenshots

22current images and SHA256 are in
[/tmp/birja-phase09-ui-proof/screenshots.json](/tmp/birja-phase09-ui-proof/screenshots.json).
Source identities are [09-UI-SOURCE-HASHES.json](09-UI-SOURCE-HASHES.json).
Images include actual authenticated stock previews/receipts and combined
portfolio at320/375/768/1024/1440, old→new repricing, closed editable draft,
committed-loss original receipt, keyboard stale draft and incomplete portfolio.
Names/balances are deliberately synthetic; names use the actual64-character
catalogue bound. Huge decimal display is additionally covered in unit tests and
legacy portfolio browser boundary fixtures, not impossible production balances.

## Pending owner checks

1. Ticket: whole-share input, Buy max/Sell all drafts, bid/ask selected side,
   visible IEX/simulation/zero-fee/omitted-regulatory-fee/immediate-proceeds copy.
2. Preview and repricing: itemized cash, old/new execution price and cash delta;
   explicit second confirmation, closed/held quantity retained without a queue.
3. Receipt: original saved company/source/full dates and historical cash/share
   balances, Portfolio/Trade again and sensible keyboard focus.
4. Portfolio: shared cash, Stock/Crypto labels, direct quantities/costs/basis/
   values/returns, alphabetic rows and exactly3Cash/Stocks/Crypto allocations.
5. Incomplete/historical: Known value and unvalued count, no overall return or
   filled allocation bars; dated closed/halt marks and uncertainty explanations.
6. Actual browser200% zoom on the owner's browser: confirm/retry reachable,
   readable table/cards, no overlap or horizontal page scroll. Headless native
   shortcut attempt did not apply zoom;640px reflow is supplementary only.

Result: pending for all6. Do not activate provider collection or deploy to do
these checks. Plan15 must present the finished concrete packet after14 passes.
