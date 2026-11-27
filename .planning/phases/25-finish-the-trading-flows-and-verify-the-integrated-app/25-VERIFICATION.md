---
phase: 25-finish-the-trading-flows-and-verify-the-integrated-app
verified: 2026-11-26T22:50:22Z
status: passed
score: 13/13
requirements_satisfied: [FLOW-01, FLOW-02, FLOW-03, FLOW-04]
overrides_applied: 0
source: a3b84647735803cdcc392d2bcaf8141b5a83e64f
hosted_checkout: da8ded9f08afd6e17cf46260ac7a036383dcc3f1
---

# Phase 25 verification

The approved trade, History and sign-in layouts are wired into the
application. The corrected PR candidate passed all six hosted jobs and
authenticated recovery. [PR #55](https://github.com/YokAI-open/Birja/pull/55) ·
[Hosted run](https://github.com/YokAI-open/Birja/actions/runs/45900726488)

## Observable truths

| Truth | Result | Evidence |
|---|---|---|
| Stock and crypto show the actual order preview and cash. A reprice requires renewed confirmation. An uncertain attempt recovers the original result and reconciles with the chosen portfolio and History. | Verified | The three route pages render accepted preview or fill fields from their API hooks. The crypto page uses stored request values and the same key on an unknown outcome. The stock hooks retain the original attempt and the server replacement preview. Hosted Chromium exercises exact stock and crypto fills, held and closed states, repricing, immutable recovery and same-portfolio cash and ledger assertions. |
| On the selected portfolio, users can filter, expand and page through genuine History and complete email-code sign-in and door sign-out. | Verified | `App.tsx` mounts the owned History route and the actual sign-in and session controls. Chromium asserts a later matching ledger event, an off-page correction original, a recovered append and successful HTTP request, verification and logout responses. |
| Real desktop and mobile journeys, chart states, code review, required candidate CI and snapshot recovery pass. | Verified | The guarded local full replay recorded 113 passes and one expected deployed-site CSP skip. The corrected hosted browser runner passed in 946.5 seconds with empty owned container, network and volume inventories after cleanup. The exact hosted run passed every required job and all seven recovery stages. |
| The three trade paths use their selected portfolio, one chooser and a shared responsive workspace. | Verified | `App.tsx` renders the scoped switcher before the nested trade routes. All three pages consume the outlet portfolio target. Current cash and holdings come from the owned portfolio or stock trade context. The crypto ticket shows both amount and quantity, and stocks retain whole-share inputs. |
| Preview and receipt expose exact economic facts and retain the original target when a quote expires or a market closes. | Verified | Stock prices render through `formatStockPrice` in the preview, receipt and corresponding History detail. Confirmations use the server quote and display side, quantity, fee and signed cash delta. Catalog and curated stock browser journeys check recovery against the same portfolio. |
| Server-side mixed History filters preserve legacy clients and select matching events before paging. | Verified | The private v2 route validates typed activity and asset choices and passes the owned active portfolio to the service. Each source has owner and portfolio predicates before the union, tuple seek, descending order and lookahead. The default mixed cursor remains v3. Filtered v4 carries the normalized pair and target. The former trade-only endpoint still calls its own continuation service. |
| Filter and portfolio changes isolate stale responses and retain accessible pagination. | Verified | The query key contains owner, portfolio, epoch, activity and asset. The hook checks the abort signal, query instance and current scope before accepting a page. The page discards superseded append intent. A focused retry stays visible and the final append transfers focus to the terminal status. |
| The approved History controls and disclosures retain original, correction and held records. | Verified | Native disclosure rows render actual event detail. The API includes owned original payment data with a correction, including when the original falls outside the filtered page. Dividend and split predicates preserve the existing source taxonomy and exact monetary projections. |
| Email request, verification and logout use configured session routes with accessible feedback and focus. | Verified | The form hooks call v1 request-code, v2 verify-code and v1 logout. The session transitions clear private queries and update the identity. Sign-in labels, autocomplete, code input handling, pending guards and route focus remain wired. The browser uses a generated console-delivered code on the isolated stack. |
| Six matching desktop and mobile comparisons bind the real app to the approved reference, and keyboard, width and enlarged text are measured. | Verified | The ZIP carries 12 hash-matched images at 1440 × 1000 and 390 × 1000 from capture source `0087e99`. Visual inspection found the expected workspace placement and control hierarchy. The app uses actual balances, an automatic crypto preview and real email prompts. The 320px checks measured doubled CSS text and keyboard reach. Native browser zoom remains unmeasured. |
| The recovery clock, required policy jobs and source binding remain enforced. | Verified | The workflow checks a 65-minute horizon and waits through the fixture clock boundary within the bounded step. It runs preflight, the seven-stage serial proof and receipt verification against `GITHUB_SHA` before upload. `ci-pass` depends on backend, frontend, image, e2e and ops. The exact hosted recovery ran for 25m 04s. |
| Candidate review findings are resolved and the final six-job result belongs to the tested tree. | Verified | The review and local checks cover scoped browser assertions, holdings and History precision, focus, and wrapping the long company name. The verified hosted merge parents include corrected head `a3b8464`. The downloaded archive digest and receipt agree with the actual merge tree, backend context and all seven authenticated stages. |
| Phase 23 live historical data qualification and release authority remain separate. | Verified | CHART-04 remains open in the requirements and source qualification record. This verification applies to the PR candidate and its isolated tests. |

[Browser and comparison evidence](25-BROWSER-RECEIPT.md) ·
[Review](25-REVIEW.md) · [Exact candidate record](25-CANDIDATE.md)

## Artifacts, wiring and data flow

| Required artifact | Verified connection and data |
|---|---|
| Trade pages and `tradeWorkspace.css` | The nested portfolio routes mount `TradePage.tsx`, `StockTradePage.tsx` and `StockCatalogTradePage.tsx`. Their hooks request owned context and server quotes and render accepted prices, fees, balances and receipts. The corrected stylesheet wraps long company names without changing the transaction paths. |
| `backend/app/api/v2/history.py`, `schemas/event_history.py` and `services/event_history.py` | The route supplies the typed filters and authorized portfolio. PostgreSQL returns real fills, payments, splits and correction decisions through bounded seek and hydration of the selected IDs. The service revalidates the owned read before returning it. |
| `HistoryPage.tsx` and `useEventHistory.ts` | The page sends the selected filter pair through the scoped infinite query to `api/eventHistory.ts`. The client validates each page and cursor against that pair and renders the real event and its embedded original through `HistoryEventDetails.tsx`. |
| `SignInPage.tsx` and `App.tsx` | The page submits through `useAuthMutations.ts` and `api/auth.ts`. Actual backend OTP and session responses drive the signed-out form, signed-in identity and door control. |
| `25-BROWSER-RECEIPT.md` and `frontend/e2e/phase25-review-capture.ts` | The trade, History and sign-in specs use the capture helper in the guarded project. The auth spec uses the generated console code from the test helper, and the no-overflow and focus assertions operate on the real rendered controls. |
| `.github/workflows/ci.yml` and `deploy/tests/test-ci-ops.py` | The timing contract checks the actual workflow clock. The workflow calls `run-portfolio-validation.py` for current 0028 recovery and receipt verification and gates artifact upload on success. |
| `25-CANDIDATE.md` and `25-REVIEW.md` | The local baseline and both hosted attempts have separate identities. The successful run binds the exact authorized head, merge commit, tree, six jobs and recovery digests. The Phase 24 evidence is cited for unchanged local inputs. |

## Verification checks

| Check | Result |
|---|---|
| Exact checked-out source and archive | The saved GitHub run record is a successful pull-request run for head `a3b8464`. Its six job conclusions are success. The receipt identifies merge checkout `da8ded9` and tree `aec41f80d7bfdeebb4a2c08bf497ab685fa77e02`. Git resolves that exact tree and both recorded merge parents. The downloaded archive passed SHA-256 verification. The receipt digest is `fc91f736333a76b23b1fa6192876df14f98f07978e8412dffea532af72629bb8`. Its seven stages, archive digest and backend context match the hosted record. |
| Recovery selector | The read-only `run-portfolio-validation.py --phase 24 --suite recovery-successor --dry-run` returned seven ordered stages ending in `selected-rollback`. The dry run checks selection. The hosted artifact supplies the run evidence. |
| Financial display | A direct Node spot-check preserved `100.00000123` as the exact stock price, displayed the same value as cent-rounded USD for cash, and retained an eight-decimal coin quantity. |
| Visual artifact | ZIP integrity and manifest source passed. All 12 PNGs match their recorded SHA-256 hashes and viewport dimensions. The sole later application change from the visual capture source wraps long company names on trade tickets. The corrected full browser replay covers that change. |
| Phase source scan | `git diff --check` passed. The changed application and workflow files contain no unresolved `TBD`, `FIXME` or `XXX` markers. The checked query placeholders and unmounted view branches have real success paths. |

No additional phase probe scripts were declared in the seven plans.
No blocking verification item remains within Phase 25's measured scope.

## Requirements coverage

| Requirement | Plans | Result |
|---|---|---|
| FLOW-01 | 25-01, 25-05 | Satisfied through all three owned tickets, receipts, exact financial reconciliation and reprice and recovery journeys. |
| FLOW-02 | 25-02, 25-04, 25-05 | Satisfied through private filtered reads, stable continuation, original correction details and scoped browser recovery. |
| FLOW-03 | 25-03, 25-05 | Satisfied through the real request, verify and logout routes and accessible keyboard and pending interactions. |
| FLOW-04 | 25-05, 25-06, 25-07 | Satisfied through the six comparison pairs, chart and financial journeys, reviewed corrections, all six hosted jobs and authenticated snapshot recovery. |

[Phase 23 qualification](../23-show-historical-market-prices/23-SOURCE-QUALIFICATION.md)
