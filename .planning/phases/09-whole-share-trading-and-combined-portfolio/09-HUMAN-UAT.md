---
status: passed
phase: 09-whole-share-trading-and-combined-portfolio
source: [09-UI-SPEC.md, 09-LOCAL-PROOF.md, 09-UI-SOURCE-HASHES.json, 09-VERIFICATION.md]
---

# Phase 9 interface acceptance

Plans01–14 are complete locally. All required automated, recovery, security and
source-review gates pass. Plan15 requires the actual owner's new-UI answers;
earlier Phase7/8 acceptance does not cover these screens. All three owner checks below passed on 2026-11-12. Live provider activation remains owner-deferred.

## Open the review bundle

[Download the review ZIP](/tmp/birja-phase09-ui-review.zip), extract it on your
computer and open index.html in your desktop browser. The five read-only pages
contain the actual rendered DOM, CSS and fonts from source969c301. Accounts,
prices and session times are deliberately synthetic. Scripts, forms and network
navigation are removed; trade buttons are inactive in these review snapshots.

The pages run offline and support actual desktop browser zoom. Their integrity
check passed at1440/375/640px with zero external HTTP requests. This reflow proof
is separate from the owner's native200% check. The real application passed
45applicable browser stories and the final affected stock14, with no retries;
the expected production-CSP skip remains separate.

The bundle includes25live application screenshots, covering320/375/768/1024/1440,
the actual AAPL+BTC combined portfolio, repricing, receipt, dated closed/halted
marks, uncertain action, keyboard/stale draft and a supplementary640px reflow.
MANIFEST.json records SHA256 and sizes.09-UI-SOURCE-HASHES.json records source.

## Owner checks

1. **Ticket/preview/receipt — passed.** Review stock-preview-review.html,
   stock-reprice-review.html and stock-receipt-review.html. Check whole-share
   quantity and shortcut drafts, bid/ask highlighting, explicit confirmation,
   old/new price and cash delta, original receipt balances and dates, sensible
   focus, and IEX/simulation/zero-added-fee/settlement disclosures. Closed draft
   and committed-loss recovery screenshots show unavailable/result states;
   the actual functional paths passed browser tests.

2. **Combined portfolio — passed.** Review combined-portfolio-review.html and
   incomplete-portfolio-review.html. Check one cash balance, Stock/Crypto labels,
   alphabetic AAPL/BTC rows, direct quantity/cost/basis/value/return/allocation,
   Cash/Stocks/Crypto bars, known subtotal/count and unavailable aggregate
   returns/allocations. Closed/halted screenshots retain dated marks;
   uncertain actions hide unsafe values.

3. **Actual native200% zoom — passed (owner verified).** Use your desktop browser's Zoom menu
   to select200% on these HTML pages. Check readable text/table/cards, reachable
   controls and no overlap or horizontal page overflow. The headless shortcut
   did not apply native zoom; no automated native200% pass is claimed.

## Actual owner responses — 2026-11-12

- Ticket/receipt: “Approve ticket and receipt UI”.
- Combined portfolio: “Approve combined portfolio UI”.
- After downloading the bundle, the owner reported “it works perfect”. Asked
  specifically whether this included **200% browser zoom**, readable text,
  reachable controls and no overlap or horizontal page scrolling, the owner
  answered “yes”. This is owner-observed native zoom, not an automated pass;
  browser/OS details were not reported and are not invented.

Evidence: source969c301; current17source hashes independently rechecked against
09-UI-SOURCE-HASHES.json. Reviewed ZIP SHA256:
0368d66604f8b33ad35294f9c18c7a9837d0f91dd79e3a765c5879d671e816b2.

## Summary

total: 3
passed: 3
issues: 0
pending: 0
skipped: 0
blocked: 0

Result: accepted. Both Plan15 tasks are complete. This closes local interface
acceptance only; existing provider/live-data/publication/deployment deferrals
remain unchanged. Production remains v0.4.0/schema0008.
