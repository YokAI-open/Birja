---
phase: 24-compare-portfolio-performance
verified: 2026-11-26T16:34:05Z
status: passed
score: 10/10
requirements_satisfied: [TREND-01, TREND-02, TREND-03, TREND-04]
overrides_applied: 0
source: 96f3f82
---

# Phase 24 verification

Verified the local phase goal of showing each strategy's current allocation
and actual value trend while preserving its accounting.

## Observable truths

| Truth | Status | Checked evidence |
|---|---|---|
| The entire card opens the chosen strategy and shows its real current figures. Creation, editing, switching and removal preserve the existing financial and lifecycle rules. | Verified | `PortfoliosPage.tsx` maps each current statement to one link using that row's ID and shows its optional description, cash, total and return. The final button uses the existing create form and capacity authority. The isolated Chromium run exercised two distinct cards, real fills, edit and original creation replay at capacity, terminal close with holdings, and last-portfolio closure followed by creation. |
| The selected route orders chooser, Edit, Update with age, and Remove above value, return and allocation. | Verified | The `App.tsx` index route renders `PortfolioPage` inside `PortfolioRoute` and places the Update and Remove slots after Edit. `PortfolioPage.tsx` portals the live refresh into that slot and passes the same statement to the summary and allocation. Chromium asserted actual DOM and keyboard order, same-root refresh, exact source timestamp and restored focus. |
| Holdings filter by asset, sort by exact values and percentage return, and open the selected portfolio's trade context. Incomplete current valuation stays explicit. | Verified | `PortfolioHoldings.tsx` uses exact decimal comparison with stable ties and constructs trades from the owned target ID. Chromium observed distinct same-symbol books, independent current cash and a reversal in ordering between dollar gains and percentage returns. A current mark hold produced the qualified known value, unvalued count and unavailable allocation. |
| One immutable observation per active owner and UTC day is captured from enablement forward, using original cash and the existing exact valuation. | Verified | The 0028 SQL binds the observation to the account's composite owner, enforces UTC capture time, unique day and completeness, and takes a shared active-root lock against closure. `portfolio_daily_values.py` reads original cash and appends with conflict-ignore. `portfolio.py` uses the shared snapshot and checks applicable durable mark rights. The PostgreSQL regressions include complete zero, incomplete null, separate baselines and both close orders. |
| Fresh and populated 0028 have exact restricted authority, and the selected predecessor keeps its qualified recovery path. | Verified | The authenticated 0028 migration loads the checked SQL digest. Admission and bootstrap agree on the 0028 catalogue, grant and default fingerprints while the saved 0027 baseline remains pinned. Scheduler append and identity use are narrowly granted. Guarded migration tests and measured fresh, upgraded and retained recovery lanes exercised these paths. |
| A running scheduler captures within 22:00–24:00 UTC with bounded work, retry, restart and no new observations after closure. | Verified | Both Compose entry points pass the capture switch and the scheduler registers the cycle after 0028 admission. A bounded cursor advances past failed roots and the durable daily key preserves the first successful append on retry. Tests cover window rollover, timeout fairness, restart, repeated capture and terminal close. |
| Each active owner gets a private 30-day exact history independently of current valuation. | Verified | The authenticated `/api/v2/portfolios/value-history` route joins active owner roots to observations within the UTC day range and rechecks active ownership under a shared lock. Exact string amounts and IDs reach the independent frontend query, which scopes cache and response acceptance to the session and current active IDs. API and Chromium evidence check sibling and foreign exclusion, old-revision refusal, and history-only failure and retry. |
| Each card shows the correct sparkline and accessible equivalent, with gaps and readable current-only states. | Verified | `PortfoliosPage.tsx` selects series by exact ID. `PortfolioValueSparkline.tsx` uses UTC spacing, splits segments at unavailable days and describes observed endpoints through the link's `aria-describedby`. Guarded browser assertions distinguish a missing date from a null observation and verify accessible zero/one-value states and continued current valuation. |
| Exact encrypted restore preserves complete, incomplete and terminal history and supports the qualified 0027 pre-write fallback and 0028 post-write restart. | Verified | The backup and restore contract includes the canonical daily rows, identity state and exact restricted grants. The same-archive local run passed all seven authenticated stages and the receipt verifier. After restart, the real owner API returned only owned active series and the stored terminal observation still matched the database proof. The old runtime was refused on the written 0028 state. |
| The actual overview and selected workspace match the approved four desktop and phone comparisons, and CI stages only the source-bound measured recovery. | Verified | Independently inspected all eight paired PNGs. The overview card geometry and 23px titles align, and the selected layout retains the expected controls and responsive allocation. Actual data, neutral strokes, explicit trade controls and extra detail explain recorded geometry differences. The CI recovery step selects Phase 24 and verifies the archive and receipt against `GITHUB_SHA` before staging or upload. |

## Artifacts, wiring and data flow

All 20 must-have artifacts exist and passed the GSD artifact scan. All 15
planned connections were traced to substantive code or executable evidence.

| Connection | Checked data and behavior |
|---|---|
| 0028 revision → migration SQL → exact schema and bootstrap | The same SQL digest is pinned by the migration, guarded migrator, deployment and archive consumers. Authenticated fresh, populated and retained replay exercises the actual schema and role predicates. |
| Selected route → toolbar slots → portfolio statement and holdings | The index route provides the selected owner target. Summary and holdings consume the scoped current statement, and the same ID reaches refresh and trade navigation. |
| Compose scheduler → daily cycle → shared snapshot → daily SQL row | Scheduled capture receives current authority and the stored baseline from PostgreSQL. The active-root lock and day key protect the observation through commit. |
| Owner route → daily read → decoder and fenced query → chart and overview | Real rows flow to the owner-batched read and string-decimal decoder. The chart renders that series only for the active identity. The comparison still obtains current amounts from its separate statement. |
| Browser strategy spec → disposable fixture and actual API | `run-stock-browser.py` mounts the host's `frontend/e2e` at read-only `/e2e`. The spec invokes `/e2e/portfolio-browser-fixture.py` in that container and verifies scoped HTTP values. |
| Backup snapshot → restore verifier → campaign and CI | The versioned archive authenticates canonical payload, retained source and successor image. The finite campaign invokes the guarded finance recovery script. CI accepts the exact stage receipt and rechecks the two staged digests before upload. |

Static link checks directly recognized four links. The other eleven resolve
through imports, aliases, the container fixture mount or basename-relative
paths and were verified from call sites and the guarded execution.

## Executed evidence

| Check | Result |
|---|---|
| Guarded backend collection and affected replay | The full collection ran 4,172 cases. It recorded 4,171 passes and one stale assertion in the exact expected route inventory. The failure listed the approved market and portfolio history routes. Commit `7025837` changes that expected set only. The guarded route and daily API replay then passed 57 cases on identical application code. |
| Backend coverage | 93.19% overall. The eight phase critical modules reached 100% line and branch coverage, with 1,015 statements and 296 branches. The complete required CI critical roster also reached 100%, with 6,437 statements and 2,100 branches. |
| Frontend and browser | Frontend lint, TypeScript, 1,424 Vitest cases across 66 files and the production build passed. The build emitted a bundle-size warning. All eight selected Chromium journeys passed. Browser tests exercised 320px reflow and CSS 200% text enlargement. |
| Browser comparison binding | The final comparison ZIP passed integrity and all 13 manifest artifact hashes matched. The approved prototype and child Playwright log matched their manifest digests, all 376 bound input files matched the checkout, and each PNG had its declared 1440 × 1000 or 390 × 1000 dimensions. The evidence is bound to `741c337`. [Browser receipt](24-BROWSER-RECEIPT.md) |
| Encrypted recovery binding | The actual archive and private status digests matched the serial run and verifier output. All seven stage statuses were authenticated on `74e852d`. Backend application, migrations, dependencies, archive tooling, Compose and workflow inputs match the verified branch. Later edits affected documents, the browser strategy spec, one CSS declaration and the backend route test inventory. [Recovery receipt](24-RECOVERY-RECEIPT.md) |
| Independent spot checks | The recovery selector's dry run listed the exact seven stages ending in selected rollback. The 0028 SQL digest matched its four consumers. Deployment and rollback shell syntax and Git diff checks passed. |

## Requirements coverage

| Requirement | Plans | Status |
|---|---|---|
| TREND-01 | 24-05, 24-08 | Satisfied by the integrated card, current statement and creation lifecycle evidence. |
| TREND-02 | 24-04, 24-05, 24-08 | Satisfied by the session-fenced owner read, exact decoder, independent retry and gap-aware rendering. |
| TREND-03 | 24-01, 24-03, 24-04, 24-06, 24-07, 24-08 | Satisfied by exact database admission, immutable capture, privacy, restricted authority and measured encrypted recovery. |
| TREND-04 | 24-02, 24-08 | Satisfied by actual toolbar and held-portfolio behavior in the guarded browser. |

All four Phase 24 requirements are mapped to shipped local behavior. The
change scan found no unresolved debt markers, stubs or disconnected financial
data. The approved visual contract and measured browser comparison satisfy the
phase's visual verification. The recorded text enlargement uses CSS. Native
browser zoom was unmeasured.

## Release evidence still open

The local serial proof took 56m 19s while backend tests were running. The
hosted serial step allows 45 minutes and has no measured hosted outcome for
this candidate. Required hosted CI and release acceptance still apply.
Phase 23's separate CHART-04 live provider qualification remains open.
