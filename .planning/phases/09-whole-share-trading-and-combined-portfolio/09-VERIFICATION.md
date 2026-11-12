---
phase: 09-whole-share-trading-and-combined-portfolio
status: human_needed
verified: 2026-11-12
review_mode: sequential-inline
operational_gates: passed
owner_acceptance: pending
score: 16/18 local behavioral and acceptance truths
---

# Phase 9 goal-backward verification

Goal: users safely trade whole stocks with existing cash and inspect truthful
combined holdings without compromising crypto or corporate-action accounting.
This is a distinct inline verifier pass, not independent-agent assurance. Source
and actual assertions, not file existence, support the behavioral matrix. All
Plan14 local automated gates pass. Human acceptance15 and actual native zoom
are pending. No production/live readiness
or final requirement completion is claimed.

## Observable decisions

| Decision | Local behavior | Actual source and assertion path |
| --- | --- | --- |
| D-01 | VERIFIED | schemas/stock_trades exact12-digit positive lexeme → stock_trade_math; ticket shortcut drafts; actual browser buymax98/sellall2 still require preview/confirm. |
| D-02 | VERIFIED | plan_stock_trade ask buy/bid sell,zero fee/spread; actual saved102buy/100sale; crypto100USD/fractional legacy journey unchanged. |
| D-03 | VERIFIED | PriceChanged409 exact replacement → stockTrades strict parser → hook preview → old/new delta and explicit next Confirm in actual browser. |
| D-04 | VERIFIED | _receipt saved Trade+Facts+movement → receipt section stays, original cash/held balances and Trade again/Portfolio focus assertions. |
| D-05 | VERIFIED | Single Account.cash and portfolio financial SELECT; actual mixed AAPL/BTC journey with original10000 start and9794cash. |
| D-06 | VERIFIED | SQL Coin.symbol,Coin.id ordering and stable component identity; browser mixed ticker orderAAPL,BTC, no price-driven sort. |
| D-07 | VERIFIED | Direct seven semantic columns / labelled cards, breakpoint1024; actual320/375/768/1024/1440 no-overflow assertions. |
| D-08 | VERIFIED | Server class/holding percentages → exactly3Cash/Stocks/Crypto bars, no client residual/financial arithmetic. |
| D-09 | VERIFIED | Exact server knownsubtotal/count, null total/return/all allocations; actual action hold shows9796known/incomplete/count1 and zero filled bars. |
| D-10 | VERIFIED | value_stock original-rights/unit checks permit dated compatible halt; browser actual Halted label/last-midpoint, later action uncertainty suppresses. d85a3f7 prevents an independently observed halt leaving a fresh cached mark. |
| D-11 | VERIFIED | Closed/held context refuses execution and suppresses unsafe estimates while input remains editable; actual closed draft2→3, no order queued. |
| D-12 | VERIFIED | Hook invalidates preview/keeps quantity on status/session/epoch deadline; reopening only enables preview, never automatic fill. |
| D-13 | VERIFIED | StockAttribution/StockDisclosure visible on ticket/receipt and midpoint explanation in portfolio; IEXsinglevenue/simulation/no commission/no spread/omittedregfees/immediatevirtualproceeds. |
| D-14 | VERIFIED | One bounded eligibility snapshot and final invoker SQL after every staged wait/constraint, last business statement before commit. Real PG barriers test quote/session/status/rights/action/units, clock equality and cancellation. |
| D-15 | VERIFIED | User-global key before availability, account and holdings locks, no new grant, same-key postclose original receipt; actual HTTP/drop transport/crypto concurrency and immutable split history assertions. |
| D-16 | VERIFIED | Exact midpoint9-place derived values; original dated marks, conservative incompatible-unit suppression and one Account.cash reference. Tests simulate future credited cash once; Phase10 dividends are not implemented here. |
| Owner ticket/receipt | UNCERTAIN — HUMAN | Actual owner response to09-15.1 required; previous Phase7/8 UI approvals do not apply. |
| Owner combined UI/nativezoom | UNCERTAIN — HUMAN | Actual owner response to09-15.2 required; headless zoom was observed false, supplementary640px is not native200%. |

## Requirement evidence

All nine remain pending in canonical REQUIREMENTS until final gates and actual
owner acceptance; the following is implementation evidence, not checkbox closure.

| Requirement | Actual chain and tests |
| --- | --- |
| MKT-02 | stock_status/rules → load_execution_evidence → final guard; test_stock_trading_waits actual blocked-session changes, test_stock_status, stock-trades browser closed/halt/stale. |
| STKTR-01 | QuoteIn/TradeIn → stock_trade_math → quote/execute routes → stockTrades parser/ticket; test_stock_trades_api, test_stock_trade_math and legacy crypto browser. |
| STKTR-02 | Exact bid/ask math and immutable facts; API receipt assertions, actual ask/bid browser fill and disclosure components. |
| STKTR-03 | Preview route/service → strict timed response → hook preview/confirm; persisted receipt and actual price_changed browser second click/delta. |
| STKTR-04 | Global Account row/transaction locks and actual concurrency tests; browser stock sale→crypto buy→stock buy preserves original account. |
| STKTR-05 | Global user-key uniqueness and _replay → saved facts/movement; API byte-compatible replay after split/rename/close and dropped-committed-response browser. |
| STKTR-06 | Immediate Account.cash credit in same transaction; actual mixed browser reuse; settlement disclosure. |
| PORT-06 | One financial statement → calculate_portfolio → exact mixed schema/parser/cache/UI; test_portfolio_snapshot/stock_valuation and actual mixed browser. |
| PORT-07 | value_stock retained source-rights and compatible epochs → dated mark or incomplete result; cached expiry/late response tests, actual closed/halted/hold portfolio. |

## Required wiring

App mounts stock-trades router and distinct /trade/stocks/:symbol page; discovery
links reach real ticket. Context/quote/execute use existing cookie auth and CSRF,
owner-only DB queries, real service transactions and no-store responses. All
financial happy-path browser responses come from actual app and PostgreSQL;
transport interception only changes/drops a response after real commit. The
single scheduler finite status cycle invalidates when no verified source exists;
no production status transport or config-selectable fake source was invented.

The retained recovery child is separately denied feature-checkout access. Current
actual application consumers run after exact restore with read-only source code,
not as a false claim that the retained recovery child contains the application.
Financial clone app and stock scheduler quarantine denials remain expected;
owner-only original receipt/context/portfolio reads must preserve exact manifest.
Both source TLS lanes exercised actual restricted quote/execute/replay/status,
split/cutoff and shared crypto cash; final compatible archive5eb886d1 passes
the entire retained/roles/TLS and real selected-volume old/new rollback proof.

## Gates and boundaries

See09-LOCAL-PROOF and the separate09-REVIEW,09-SECURITY,09-UI-REVIEW. Full backend
2086/critical39modules100%,frontend590/98.41%statements and45applicable real browser
stories have passed. Fresh all-five strict image scans pass on patched18.7.
Final retained replay/TLS/rollback/SQL and full backend rerun on18.7 pass.
Backend2086tests239.75s,99.86%overall; exact39critical modules100%statements and
branches. Frontend590tests and full static/build/audits pass. Full browser45pass
plus1expectedCSPskip; final changed stock file14pass97.5s. Five actual read-only
DOM/CSS/font pages pass separate offline reflow/zero-network verification. The
real owner200%zoom and new-UI answers remain explicitly pending.
No stub/TODO was found in the inspected new runtime paths. Cosmetic UI copy and
timestamp-density observations are recorded in UI-REVIEW, not hidden as4/4.
Provider product rights, status continuity/access, quotas/latency and live data
remain owner-deferred/unverified. They are not established by test evidence.
Phase10 payments, Phase11 activation, publication and deployment are outside
this execution. Nothing in this report authorizes them.
