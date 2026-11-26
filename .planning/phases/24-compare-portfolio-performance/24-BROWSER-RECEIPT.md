---
phase: 24
plan: "08"
task: "24-08-01"
source: 741c33709aacc1c05b46c2d509bb794de3ecfc60
date: 2026-11-26
scope: guarded Chromium with synthetic data
---

# Phase 24 portfolio browser receipt

The guarded Chromium runner used the application backend and a disposable
PostgreSQL database migrated through 0028. It used synthetic market evidence,
local clock data and console OTP delivery. The app obtained daily values and
current statements through its authenticated API.

## Browser evidence

| Requirement | Observed result |
|---|---|
| TREND-01 | Two full-surface portfolio cards opened their own roots by keyboard and by clicking card padding. Both showed their exact independently valued cash, total and signed return. The final card opened creation. Retained tests confirmed editable descriptions, original creation replay at the ten-portfolio cap and a disabled final card with the capacity explanation. Last-portfolio closure opened the empty state with an enabled creation card. |
| TREND-02 | The real no-store history route returned distinct active-owner series over 30 UTC days. The first card rendered the recorded adjacent segment and a blank column on a missing date. Its accessible summary used the first and last recorded values. A null observation remained distinct from the missing day. The second card described its sole observation and displayed `Collecting daily values`. An isolated history error left current cash and card navigation usable. One explicit retry restored the history and keyboard focus. |
| TREND-03 | The synthetic terminal root's previously seeded value was present while it was active. After actual closure the history route returned only the two active roots. A second authenticated owner saw only their own portfolio with an empty series. Database capture, persistence and recovery are verified in the separate recovery and integration evidence. |
| TREND-04 | The actual DOM and keyboard order was chooser, Edit, Update, Remove. Same-root refresh checked its exact source timestamp and retained keyboard focus. Current value, signed return and Cash, Stocks and Crypto percentages used the server statement. AAPL's $40.00 gain ranked below MSFT's $22.00 gain when sorted by their 3.92% and 10.78% returns. Default value order, ticker order and separate asset filters passed. Switching roots kept both AAPL positions and trade destinations separate. An action hold left the incomplete value, unvalued count and unavailable allocation visible, and the scoped stock ticket disabled confirmation. |

At 320px the app overview and selected portfolio had no horizontal page scroll
with normal text or with the CSS root font size set to 200%. The selected
chooser, management actions, asset filters and trade link remained visible and
focusable with enlarged text. This test used CSS text enlargement. Native
browser zoom remains unmeasured.

The focused Playwright discovery found eight Chromium cases in three files.
The runner selected both Phase 24 cases and six retained Phase 13, Phase 14 and
owned trade cases using the plan's exact name filter. All eight passed in
130.4 seconds. The guarded runner cleaned up its containers, network and
volumes.

```bash
python3 deploy/tests/run-stock-browser.py --suite portfolios \
  --grep 'Phase 24|Phase13 create view edit clear|Phase13 committed lost creation response|Phase13 real incomplete strategy|Phase14 deletion named|Phase14 deletion last portfolio|actual scoped crypto and stock fills'
```

Prettier, ESLint and the repository TypeScript build checked the test source.
The final browser expressions use the existing execution pattern for reading
browser globals from the Node test project. Earlier runs identified a return
text locator error and an interrupted document load during concurrent Docker
network changes. The cap assertion uses the application's navigation link
after checking reload recovery.

## Approved reference comparison

The four pairs were captured at equal 1440 × 1000 and 390 × 1000 viewports with
the approved ZIP rendered offline. The measured boxes below are in CSS pixels
and follow `x, y, width, height`. All eight images were visually inspected.

| Target | Approved | Running app | Viewport |
|---|---|---|---|
| First card | `40, 127, 442.7, 245` | `40, 127, 442.7, 245` | Desktop |
| Sparkline slot | `66, 235.5, 390.7, 43` | `66, 234.5, 390.7, 44` | Desktop |
| New portfolio card | `957.3, 127, 442.7, 245` | `957.3, 127, 442.7, 245` | Desktop |
| First card | `16, 88, 358, 200` | `16, 88, 358, 200` | Phone |
| Sparkline slot | `33, 174, 324, 43` | `33, 173, 324, 44` | Phone |
| New portfolio card | `16, 520, 358, 120` | `16, 520, 358, 120` | Phone |
| Selected toolbar | `40, 127, 1360, 44` | `40, 127, 1360, 44` | Desktop |
| Summary | `40, 193, 1360, 188` | `40, 193, 1360, 212` | Desktop |
| Allocation strip | `742, 241.8, 625, 11` | `744, 253, 623, 12` | Desktop |
| Holdings heading and controls | `40, 408, 1360, 44` | `40, 433, 1360, 44` | Desktop |
| Holdings first card | `40, 464, 444.7, 170.8` | `40, 489, 442.7, 245` | Desktop |
| Selected toolbar | `16, 88, 358, 96` | `16, 89, 358, 96` | Phone |
| Summary | `16, 206, 358, 233.4` | `16, 207, 358, 261.2` | Phone |
| Allocation strip | `33, 333.4, 324, 11` | `33, 359.2, 324, 12` | Phone |
| Holdings heading and controls | `16, 466.4, 358, 90.5` | `16, 496.2, 358, 88` | Phone |
| Holdings first card | `16, 568.9, 358, 169.1` | `16, 596.2, 358, 245` | Phone |

The app's signed dollar and percentage labels and neutral chart strokes reflect
its data contract. Portfolio card names measure 23px on desktop and phone,
matching the reference. They reach 46px at the enlarged-text test setting.
The selected panel keeps the portfolio description and uses the actual price
age and a labelled allocation strip.
The separate Trade and Cost and price controls grow holdings cards and keep
their actions reachable. The app's header retains the integrated navigation.
Current values, ordering and trend series come from the synthetic test data.

[Paired portfolio comparison ZIP](/tmp/birja-phase24-portfolio-comparison-71cld5ih.zip)

## Input binding

| Input | SHA-256 |
|---|---|
| Approved v1.5 prototype ZIP | `5e361ad60eb0915add082791fd4a8bc2862ec607712b04e00a15d2c53f2b143e` |
| Guarded browser runner | `d5966a3809b1f5c649992e26e814387245f593c9d398a21c439f4e9aaedd0680` |
| Owned portfolio fixture | `bcaf893acd8cc9cc74b3be3c1913bf4b9cfed6ac17169b4ca98893ecbc64ebdc` |
| Portfolio strategy tests | `ba2558c15ea889f79f2877397d00f4481e0aed4d4d5422b2db7d608d16c189d5` |
| Portfolio deletion tests | `fe181480644f0f15401060ee3e4bb8ed56d6f82b40fad9bfb0a57b30c61361b9` |
| Portfolio ownership tests | `5f6084835400a6d17e21ec8e9e6c56465ae2dfd6e2fc206560396173484ba1ca` |
| Portfolio overview CSS | `07baeb582065d5c8a0ec0df2087d3243fbd21cb42f43ca1bd493463659f7f06e` |
| Exact Chromium run log | `0e803e2b7c9f0ea2f6e85426e8997d0627fd306a62b46416cd79eb51f6c5068d` |
| Paired screenshot ZIP | `c1db58df6dc08fb9fd02eebc1ef4892710995727ef6324c2d0a8002b07872cb8` |

The comparison ZIP's `manifest.json` binds the screenshot run to all inputs
recognized by the guard and lists per-image and geometry SHA-256 values.
The ZIP contains only the paired screenshots, their measured boxes, the
manifest, and an offline viewer.
