# Phase10 actual browser evidence

Verified locally2026-11-13. Final source includes focus fixes944cb7f/7aa29fe
and financial browser fixture/spec commitababfd5. Parent owns phase state.

## Actual gates

| Gate | Result |
|---|---|
| New dividends suite before final retry refinement |4passed/1.5m |
| Final retry/original/responsive actual Chromium selector |1passed/31.3s; runner32.1s |
| Existing stock retry synchronization selector |1passed/3.8s; runner4.6s |
| Complete frozen-source browser suite |49passed/1expectedCSPskip/5.2m; runner314.1s |
| Final frontend unit/coverage |697passed/36files/18.04s |
| Final frontend coverage |98.37%statements,94.82%branches,98.95%functions,99.10%lines |
| Focus component/page regressions |29passed/3.67s |
| Full ESLint/TypeScript/Prettier |Pass |
| Python compile, scoped RuffF/format |Pass |

Final actual command: `python3 deploy/tests/run-stock-browser.py --suite all`.
Log `/tmp/birja-phase10-15-browser-all-final2.log`; detailed isolated evidence
`/tmp/birja-phase09-browser-b1d258g4/browser-all.log`. The runner verifies no
preexisting owned resources, synthetic credentials/console email/fake prices,
internal datastores and loopback-only frontend, then cleans its own project.
Final cleanup: zero containers/networks/volumes for birja-phase09-e2e-test.
Unrelated running services and the parent's birja-test stack are untouched.
All112 UI/test/fixture source hashes stayed unchanged during the final run;
pre-run inventory `/tmp/birja-phase10-15-final-frozen-sources.json`.

## Real financial journey

Real OTP sign-in creates Account.cash=starting_cash10000. Explicit historical
opening shares/journal are synthetic retained input, not a claimed historical
fill or cash credit. Structured action/admission/calendar inputs are synthetic.
Published payouts, corrections and stock/crypto trades use actual services and
PostgreSQL; the worker connects as restricted birja_scheduler, which cannot
directly UPDATE Account.cash. No financial mutation success is route-mocked.

- Original dividend10000 credits cash20000 once; repeat worker adds no row/cash.
- Actual50AAPL shares cost5100; actual crypto purchase costs10000 including fee.
  Cash4900 proves these combined purchases need the dividend, exceeding the
  original grant. Starting cash remains10000; no handcrafted cash UPDATE.
- Verified revision adds2. A proposed10001debit is unaffordable: no cash change,
  held decision deduplicates. An actual crypto sale supplies funds; one later
  worker applies−10001, leaving precisely server sale cash_after minus10001.
- Uncertain replacement has empty eligible work but the independent paid-anchor
  path appends one owner-visible no-cash hold. Repeat does not grow History.
  Explicit reviewed reconciliation then applies+10003 once; original unchanged.
- Separate28zero-rounded originals from a positive0.00000001rate exercise exact
  visible tiny terms and paging. Real correction, crypto fill and1.5:1 forward
  split produce all four event kinds; split becomes exact3:2, shares2→3 and basis
  unchanged. Actual31-record pages and offpage immutable original are checked.
- Pre-anchor uncertain evidence yields no original, decision or Dividend row.
  An actual1USD old-owner crypto trade makes delayed-read account-switch checks
  nonvacuous; the replacement owner has an empty private History.

No provider activation/rights verification is implied by these synthetic inputs.
The earlier operations PROGRAM embedded in dividend-execution-fixture.py remains
byte-identical to8bf8439; the guarded browser CLI is a separate extension.

## Responsive, keyboard and visual evidence

Actual Chromium checks320/375/768/1024/1440, one accessible table/cards layout,
long saved names, tiny rates, original-heading/Back focus,44px Back target,
fixed-nav clearance, no horizontal page overflow and reduced motion. Loading,
empty, initial failure/retry, retained append/refresh errors and end-focus states
are captured. Existing full stock/action/auth/crypto/Portfolio journeys pass.
Final375/1024/1440 viewport images and held proposals were visually inspected:
wrapped metadata remains readable and the no-cash headline is distinct from
the proposed debit. The deliberately long synthetic MSFT label comes from the
existing long-name helper; it is not a provider-identity claim.

The tied-read-only browser page is **separate presentation evidence**: real
retained economics with an explicitly synthetic common publication timestamp.
It tests four-kind client order and two-page append, not a financial mutation
or a database timestamp rewrite. Actual owner-first tied SQL paging is Plan10.
No immutable guard or cash/timestamp row was disabled/updated for this case.

Native200% browser zoom remains **pending owner verification**. Root font-size
200% is supplementary only, not native browser zoom or owner acceptance.

## Review package

- ZIP `/tmp/birja-phase10-ui-review.zip`,15536733bytes.
- SHA256 `4f5d316ae29a6a2d9f9b7173b58715f6bee996191c5387effa7d51193ea49c7d`.
- Extracted index `/tmp/birja-phase10-ui-review/index.html`.
-16 actual DOM/CSS/font HTML pages and32 full/viewport screenshots; no scripts,
  forms, HTTP URL references or CSS network URLs. Index links stay local.
- ZIP CRC and source/artifact SHA256 values verified; no traces, .env, OTP,
  cookie/session material or real user input is included. Only synthetic data.
- Tracked manifest `10-UI-SOURCE-HASHES.json` pins106 source files, each review
  file and ZIP. Its source head isababfd5; later documentation commits do not
  alter the reviewed source. Controls in the offline package do not execute.

## Observed failures and bounded corrections

Fresh startup genuinely failed0014's required safe migrator owner. The isolated
runner now preprovisions explicit safe canonical roles before migrations;
authority/migration unchanged. Failed startup evidence remains
`/tmp/birja-phase10-15-startup.log`, `/tmp/birja-phase09-browser-4d7uwjz_`.
Ordinary docker-compose.yml still starts `alembic upgrade head` without this
preprovisioning: fresh-dev startup is a required Plan16 follow-up, not fixed here.

Own fixture construction corrections: explicit/app import path, complete split
dates (missing payable_date caused an uncertain classification), and consistent
synthetic retained-opening recorded/economic time. These are not product defects.
Earlier failed logs remain `/tmp/birja-phase10-15-dividends-first.log`,
`...-dividends-responsive.log` and `...-dividends-reflow.log`.

Actual native-disabled blur lost final-append focus, then retry focus. Parent
approved only HistoryPage and its tests. Fixes944cb7f/7aa29fe capture owner/epoch
intent before fetch and restore only after the enabled control renders, provided
focus remains body/original control. Other-control/background/auth-change guards
remain. Real browser and native-blur model regressions pass; prior696-test gate
was superseded by final697. An intermediate full run was interrupted after known
failures and cleanup, and is diagnostic only, never a passing gate.

The first complete frozen run had48passed/1expectedskip/1failure317.5s: existing
stock retry test issued its next Enter before the previous503 request completed.
Trace had no successful retry request. Parent-approved test-only synchronization
awaits the failed response and re-enabled button; original focus assertions stay.
StockSection source unchanged. Log `/tmp/birja-phase10-15-browser-all-final.log`,
evidence `/tmp/birja-phase09-browser-zsafs90f`. The final49-pass gate above supersedes it.

Context7/ctx7 unavailable; no install. Official Playwright
[network interception](https://playwright.dev/docs/network) and
[page emulation](https://playwright.dev/docs/api/class-page#page-emulate-media)
guided read delays and reduced motion. Existing design tokens/UI contract and
local skill focus-not-obscured guidance were retained, without blanket AA/AAA claims.
