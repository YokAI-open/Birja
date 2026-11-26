# Phase 23 browser receipt

## Isolated app verification

The local Compose stack used disposable Postgres and Redis, console OTPs,
fake ticker prices, and the guarded stock and catalog test fixtures. The
browser drove the built React application through authentication, discovery,
and trade. Historical series came from deterministic responses at the chart
request boundary. The Oracle panel used a separate display fixture for the
matching mobile view. The FQZT test used the exact catalog identity from
the real isolated search, quote and preview APIs.

```text
python3 deploy/tests/run-stock-browser.py --suite all --grep 'Phase 23|Markets workspace|Markets displays|catalog search|catalog preserves|actual ask buy|a signed-in user buys'
```

The filter discovered 11 cases in four browser specs. The names record the
retained Markets layout, verified holiday and early closure, three chart
range journeys, exact catalog selection and closed marks, AAPL ask and bid
fills, and BTC buy and sell. [Discovered cases](/tmp/birja-phase23-browser-tests.txt)

All 11 cases passed on `775c435c70484afa02705f48fb20f36d19b8183b` in the
final rebuilt stack. The AAPL and FQZT previews used their current fixture
asks, $102 and $103. The retained stock and crypto cases completed both
directions through the real execution endpoints. The history cases verified
all three ranges, exact catalog selectors, readable rows and source labels,
closed and missing gaps, delayed requests, a failed chart read and retry.
Chromium kept the single header row at 320px. At 640px with 200% root font,
the heading, range controls, expanded table, navigation and action remained
visible without horizontal overflow. The global header wrapped naturally.
This enlarged-text check used CSS font scaling.
[Sanitized final browser log](/tmp/birja-phase09-browser-lyifniv5/browser-all.log)

All 1,409 Vitest tests in 63 files passed. ESLint, TypeScript, scoped
Prettier and the production build passed. Vite reported its bundle-size
warning. The reviewed backend evidence covers 335 scoped regression cases,
130 scheduler coverage cases and 85 affected review replay cases.
[Frontend check log](/tmp/birja-phase23-frontend-final.log) · [Backend and frontend code review](23-REVIEW.md)

## Compared views

The four Chromium pairs use default zoom and equal viewports in the app and
the approved prototype. The images use synthetic prices. The full-page phone
renders extend below the viewport so the bottom actions are visible.

| View | Viewport | Comparison |
|---|---|---|
| AAPL open | 1440 × 1000 | Tabs, search and price columns align. The heading and price precede the three range controls and 278px plot. Trade aligns with the inner right edge. |
| AAPL closed | 1440 × 1000 | Same chart frame, paired with the preserved last mark and verified countdown. View details aligns with the same right edge. |
| ORCL catalog | 390 × 1000 | The selected Oracle result has a stacked card, 38px ticker tile, 234px plot and right-aligned action. The app preserves Back to results and visible keyboard focus. |
| BTC | 1440 × 1000 | The Crypto tab uses the same quote-led hierarchy, 278px plot and right-aligned Trade. The source caption identifies UTC intervals. |

All wide views use the 1,360px workspace, 546px list, 28px gap, 786px
detail card, 33px inner inset and approximately 720px plot width from the
reference. The phone uses a 16px outer gutter, 358px card, 17px inner inset
and 324px plot width. The desktop toolbar begins at (40,127) and the cards
at (40,193) and (614,193) in both. The mobile search starts 51px earlier
with the demo selector omitted. The plot starts about 25px later and the
action about 115px later on that screen. The Back to results control, quote
freshness, source/time caption, 44px range buttons and Price data disclosure
account for the vertical differences.

The app uses the production brand shell, a single portfolio selector,
qualified current-price copy, source attribution and only the supported
day changes. The source, exact timestamps, neutral chart ink, true time
spacing and line breaks across closed sessions reflect the running chart.
The reference uses a demo control, continuous simulated lines, and mock
holdings and cash text. [Approved prototype and checksum](../../ui-reviews/v1.5/README.md)

The wide layout now ends at the visible workspace. Positioning the Markets
list keeps its offscreen screen-reader text from expanding the document.
The final full-page desktop app and ZIP images are all 1440 × 1000. The
mobile full-page images are 390 × 1156 and 390 × 1055 at the shared
390 × 1000 viewport. The runner's source hashes matched before and after
execution. The fixture commits are `a66bcb0` and `775c435`.

- [Side-by-side gallery](/tmp/birja-phase23-visual-proof/index.html)
- [Visual comparison ZIP](/tmp/birja-phase23-visual-proof.zip)
- [Capture dimensions, layout coordinates and image hashes](/tmp/birja-phase23-visual-proof/manifest.json)
- [Browser input source hashes](/tmp/birja-phase23-visual-proof/source-sha256.json)

The visual ZIP SHA-256 is
`ad8ce5b9880f1d868cd7f4ac87c7e20bef59cb9eea8162397351142733577f20`.

## Live source qualification

IEX and Kraken history remain disabled outside qualified scopes. Each
provider has zero live attempts in Phase 23. The actual history collection,
display and derived-use rights, permitted storage, representative coverage
and measured account or IP headroom remain open under CHART-04.
[Source qualification evidence](23-SOURCE-QUALIFICATION.md)

