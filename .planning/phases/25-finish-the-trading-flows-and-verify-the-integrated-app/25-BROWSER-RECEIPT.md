---
phase: 25
plan: "05"
task: "25-05-03"
source: 0087e99b80231e103eb70deceedc830475382b11
date: 2026-11-26
scope: guarded Chromium with synthetic data
---

# Phase 25 integrated browser receipt

The guarded replay passed **18 Chromium journeys in 246.6 seconds**. The exact
plan filter discovered 18 cases in eight spec files, including all 15 retained
journeys. One worker exercised the application and authenticated API against a
disposable PostgreSQL database migrated through `0028`. Quotes, market time,
financial fixtures and console OTP delivery were synthetic. The guard exited
successfully and confirmed empty container, network and volume inventories for
its Compose project.

```bash
python3 deploy/tests/run-stock-browser.py --suite all \
  --grep 'Phase (23|24|25) |a new user signs in|a signed-in user buys|actual (ask buy|changed ask|committed lost response|mixed pages|scoped crypto and stock fills)|catalog (buys and sells|preserves a permitted closed mark)|closed drafts'
```

| Requirement | Observed result |
|---|---|
| FLOW-01 | The owned crypto ticket showed a single portfolio chooser, server cash and held balance. Both buy input modes and the quantity sale worked. Curated and exact catalog stock journeys kept whole shares, the permitted closed price and opening countdown, fresh confirmation after repricing, and the original receipt after an ambiguous result. Receipt focus and exact values were checked against the same portfolio statement and History, including cash, quantity, execution price, fee, and ledger identity. The mixed portfolio retained its independent stock and crypto holdings and trade destinations. |
| FLOW-02 | With a one-event server page, the unfiltered first page held only the BTC purchase while the filtered read returned both stock dividend events. The real filtered cursor appended the original dividend after retrying a synthetic read failure. The correction could open its original outside the loaded rows, and focus returned on Back and moved to the terminal status on completion. Switching to an empty portfolio reset both filters. The retained 31-event case checked balances, the forward split, five responsive widths, append and refresh recovery, and equal-date ordering. |
| FLOW-03 | The sign-in form obtained real validation feedback for malformed email, requested an actual console-delivered code for a synthetic owner, focused the blank code field, verified the generated code and signed out with the keyboard door. The email field regained focus after sign-out. The retained sign-in journey verified persistence and re-entry. |
| FLOW-04 local browser coverage | Retained market chart ranges, intentional data gaps and quote independence passed. Portfolio journeys checked private 30-day results, chart retry and fallback, ownership, and same-portfolio trade controls. The paired captures use the same committed inputs as this replay. |

The trade, History and email views passed 320px no-horizontal-scroll checks
with their normal styles and with visible control and content font sizes
doubled in CSS. The test measured the actual doubled sizes on representative
controls and text and used Tab to reach the next action. Native browser zoom
remains unmeasured.

Frontend lint, TypeScript, formatting and production build passed on the
same commit. Vitest passed 1,441 tests with 94.58% statement and 92.37% branch
coverage. All 108 tests across the five guarded trade, stock trade, catalog
trade, session and market-history API suites passed in 121.10 seconds. The
backend Git tree `a0abf5be7a78b5a5b1a7328199c4d5c4db0f535b` and test Compose
configuration matched the guarded API run from `702249b`.

## Repairs verified in the replay

- The initial 10-pass run identified the curated and crypto chooser labels,
  the obsolete catalog fixture schema pin, and competition for dividend
  fixture rows. The next run reached 16 passes with the schema `0028` pin,
  exact chooser labels and measured enlarged-text behavior.
- The new filter journey uses one COST dividend and its correction. The
  retained batch uses KO for all 28 payments and the forward split. This
  keeps the dividend worker's 50-item page available and preserves MSFT's
  unit state for the later portfolio trade. The mixed-holding check now
  expects ticker headings and preserves the exact economic assertions.
- The third run had 16 passes. It reproduced a clipped focused History retry
  and the MSFT split interference. The normal cleanup was interrupted, so
  the same owned Compose cleanup was replayed and all three resource checks
  were empty. The final run verified the retry stays in view, the full
  dividend and split journey works, and the separate MSFT trade passes.

## Approved reference comparison

The six pairs were visually inspected at matching 1440 × 1000 and
390 × 1000 viewports. The measured boxes are `x, y, width, height` in CSS
pixels.

| View | Target | Approved | Running app |
|---|---|---|---|
| Trade 1440 | Chooser | `40, 127, 220, 44` | `40, 127, 220, 44` |
| Trade 1440 | Heading | `40, 197, 1360, 69.17` | `40, 197, 1360, 69.67` |
| Trade 1440 | Ticket | `40, 289.17, 751.52, 480.5` | `40, 289.67, 752.62, 391.8` |
| Trade 1440 | Preview | `809.52, 289.17, 590.48, 142` | `808.62, 289.67, 591.38, 202.8` |
| Trade 390 | Chooser | `16, 88, 220, 44` | `16, 89, 220, 44` |
| Trade 390 | Heading | `16, 158, 358, 51.89` | `16, 158, 358, 52.39` |
| Trade 390 | Ticket | `16, 232.89, 358, 445.5` | `16, 233.39, 358, 387.8` |
| Trade 390 | Preview | `16, 696.39, 358, 108.5` | `16, 637.19, 358, 170.8` |
| History 1440 | Chooser | `40, 127, 220, 44` | `40, 127, 220, 44` |
| History 1440 | Filters | `1129, 127, 271, 44` | `1128, 127, 272, 44` |
| History 1440 | First event | `40, 219.5, 1360, 70` | `40, 219.5, 1360, 70` |
| History 1440 | Refresh | — | `268, 127, 44, 44` |
| History 390 | Chooser | `16, 88, 220, 44` | `16, 89, 220, 44` |
| History 390 | Filters | `16, 140, 252, 44` | `16, 141, 358, 44` |
| History 390 | First event | `16, 232.5, 358, 70` | `16, 233.5, 358, 70` |
| History 390 | Refresh | — | `244, 89, 44, 44` |
| Sign-in 1440 | Panel | `512.5, 207, 415, 311.67` | `512.5, 209, 415, 295.67` |
| Sign-in 1440 | Heading | `550.5, 245, 339, 49.67` | `549.5, 246, 341, 49.67` |
| Sign-in 1440 | Email field | `550.5, 347.17, 339, 44` | `549.5, 347.67, 341, 52` |
| Sign-in 390 | Panel | `16, 115.3, 358, 258.89` | `16, 116.3, 358, 246.39` |
| Sign-in 390 | Heading | `37, 136.3, 316, 32.39` | `37, 137.3, 316, 32.39` |
| Sign-in 390 | Email field | `37, 219.69, 316, 44` | `37, 221.69, 316, 52` |

The running crypto ticket uses automatic preview, both buy input modes,
current cash and holdings, and a confirmation control in the preview. The
prototype uses demo bid and ask boxes and an explicit preview action in the
ticket. This changes panel heights while retaining their desktop and phone
placement. The captured route heading has its keyboard focus outline.

History's 44px refresh control sits 8px from the chooser on both screens.
The phone filter group takes its own row below the chooser. The application
uses the synthetic owner's three ledger events. The fixture's deliberately
long company name truncates and some time text wraps on the phone.
The prototype uses its example activity, including a funding row.
Sign-in uses signed-out navigation, a 52px email field and a disabled
Send code button for an empty form. The app omits the prototype's demo-code
and simulated-data notes.

[Paired comparison ZIP](/tmp/birja-phase25-comparison-tf82a8ni.zip)

The 20-entry archive passed its ZIP integrity check. It contains the 12
paired images, six geometry records, a manifest with per-image and geometry
digests, and an offline viewer. Captures use synthetic activity and a blank
email field. The code-stage screenshot and private execution traces remain
outside the ZIP.

## Input binding

| Input or evidence | SHA-256 |
|---|---|
| Approved prototype ZIP | `5e361ad60eb0915add082791fd4a8bc2862ec607712b04e00a15d2c53f2b143e` |
| Guarded browser runner | `d5966a3809b1f5c649992e26e814387245f593c9d398a21c439f4e9aaedd0680` |
| Browser capture helper | `c702ef68f62f9d83a5abcd246ec30360897c2e62a36ce9643a58e3b5524277e8` |
| Stock fixture | `67f2b7614d5605de5b89c8d3b1a74d0c7846c2971fc8f8866800384674522522` |
| Dividend fixture | `bb79e45058cc6df1b7dd227bc48835230dd06cfabd7b11f12424b6a4f16b2352` |
| Guarded source SHA-256 map, identical before and after the run | `ed8d804519ac7302ac28495a1776aedf3b02812950d5d12b5fcf9f8fad9cafd4` |
| Browser test declaration | `dc82720ffc5e4f4fd3bfa50df06833be809e6cc308d50e023c5518fa98edd09d` |
| Final browser log | `9acd66cf5a22ef05c83ea2021a61a7bbe7e2e50c05a2acc57494d1a719b7041b` |
| Final guard lifecycle log | `273a4d18db7ab09d964f1ce9f4ca7be6cdbbc046c294e85837e1e9e6b76e675d` |
| Frontend gate log | `c063d8df36731570943d27ce17ab7386fb68f1772d484d506ff6af04a1968406` |
| Guarded API log | `14f189ef065f881041849e4c31ccef440d448529e3be5dae40ae500d3b4270eb` |
| Paired screenshot ZIP | `6e537d6588f7819d85c021912fcc31fa655b54e52e506c38fa49e5485da894f1` |

| Earlier run | Browser log SHA-256 |
|---|---|
| `381d951`, 10 passed | `306ecb857c6bb029251c46bcacc3fe04e66c1166d566776c362f3c470b9f57e8` |
| `9d3c6cb`, 16 passed | `2114491ce1ce2cb6135581df5049566059223d1d5b2d7a6d02070337084369d4` |
| `aec88bc`, 16 passed | `155bd8f5b69c6515b49fc6feb83f5d55f8edef63ca703b73c895a733fb9cac30` |

The owned cleanup replay log from `aec88bc` has SHA-256
`6299a84bd498c24c4b93b9156b975ca0e9984aa098aedfae655d51e5b0f5048c`.
