---
phase: 18-make-simulated-stock-trades-work
verified: 2026-11-24T17:51:26Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 1
overrides:
  - must_have: "Live eligibility requires complete individual and market-wide halt coverage with usable freshness evidence."
    reason: "The owner chose fresh IEX quotes and blocks on exchange-reported halts, with disclosure that reports can lag or omit a halt. Current report evidence remains mandatory. D-02 and SX-02 record the revised rule."
    accepted_by: "Project owner"
    accepted_at: "2026-11-24"
deferred:
  - truth: "Release-candidate CI, remaining historical recovery and rollback diagnostics, and production acceptance."
    addressed_in: "Phase 21"
    evidence: "SV-01–SV-03 and roadmap success criteria require real-browser release acceptance, CI, applicable restore and rollback checks, and approved production activation."
---

# Phase 18 verification

Phase 18 passed. The actual v2 app previewed, confirmed and recorded a simulated AAPL buy and sell with live IEX pricing during a regular session. The selected portfolio received the exact money and position changes. Birja blocked reported halts in its runtime tests and disclosed the limits of exchange reporting.

## Observable truths

| Truth | Status | Evidence |
| --- | --- | --- |
| Free IEX pricing and official halt reports have a qualified, bounded use for the curated scope. Reported individual and market-wide halts block trading. | Verified | The activation check recorded live two-sided quotes for all 20 symbols. Phase 18's round trip made one IEX and one Nasdaq request. The scheduler shares the admitted Redis attempt budget and limits Nasdaq requests to one per minute. The halt parser tests exercise individual, overlapping and market-wide notices, and the stock ticket displays the coverage warning. [Source decision](18-SOURCE-DECISION.md) |
| Complete underlying exchange halt coverage is required by the original Plan 01 wording. | Passed with approved override | The owner explicitly accepted a reported-halt simulator. The existing fail-closed handling of required stale or failed checks remains in force. [D-02](18-CONTEXT.md) |
| A disposable portfolio buys at the current IEX ask and sells at the bid. Session closure, stale quotes and unavailable or halted reports refuse the order. | Verified | The live run bought one AAPL share at $352.25 and sold it at $351.94. Each fee was zero. Portfolio cash moved from $1,000.00 to $999.69 and position returned to zero. Runtime tests exercise closed, expired and reported-halt refusals. [Live receipt](18-LIVE-RECEIPT.md) |
| Repricing requests fresh confirmation, and retries preserve selected-portfolio cash, holdings and History. | Verified | The v2 routes pin the target through each attempt. The service returns a replacement preview on an executable-price change. Browser scenarios exercise fresh confirmation and failed-response recovery. Both live stock retries returned their original receipts, and History held the two fills. |
| The committed fill uses the current scoped halt report at the final database check. | Verified | The publisher and fill use exclusive and shared sides of the same advisory fence. The fill invokes the 0024 authority function immediately before commit. It rechecks the report identity, expiry and normal state with advancing database time. Integration coverage includes a report that turns into a halt before the final recheck. |
| Existing and new receipts survive migration and recovery with role boundaries intact. | Verified | All 26 PostgreSQL recovery contracts passed. The paired encrypted 0023/0024 fixture exercised verified TLS, exact source/clone comparisons, replay of three original receipts through the retained reader and continued refusal to trade on expired restored evidence. An evidence-bearing downgrade refused. The 0023 cold restore and two retained 0008 rollback lanes passed on the same v5 archive. [Recovery evidence](18-05-SUMMARY.md) |
| The single stock scheduler handles bounded selected-symbol demand and persists accepted prices in PostgreSQL. | Verified | Redis coalesces requests by account, server and curated symbol with a 10-second lifetime and a 7-second caller bound. The scheduler retrieves demand and calls the admitted provider path within its shared attempt budget. Only the stored accepted quotes price the order. |
| Preview and confirmation request freshness when needed and release database transactions before the wait. | Verified | The v2 quote and confirm routes call the order service first. Refresh applies to stale or unavailable quotes, rolls back the transaction, and repeats against the same portfolio target. The initial confirm's receipt lookup returns a success replay before a refresh can be scheduled. |
| A live-data stock round trip preserves the independent crypto path. | Verified | The inspected harness checked both regular exchange sessions, obtained the live Nasdaq report and IEX quote through the scheduler's normal functions, and used real v2 routes with disposable admissions and portfolio state. A BTC control with a synthetic quote spent the same cash and appeared in mixed History. |

## Artifacts and wiring

The GSD artifact check passed all nine declared files. I traced these links through the runtime and documents:

| From | Through | Result |
| --- | --- | --- |
| Source decision | Plan 02 context and the live receipt's relative source-decision link | The qualified scope drives execution and live acceptance. |
| `tasks/stock_halts.py` | Scheduled refresh, normalized report and committed `StockStatusEvidence` read by `services/stock_eligibility.py` | Real source evidence reaches eligibility with its identity and expiry. |
| `services/stock_eligibility.py` | `services/stock_trading.py` and `assert_stock_execution_current` from revision 0024 | The exact report reaches the final SQL check and saved fill authority. |
| `services/stock_quote_demand.py` | Redis request and `tasks/stock_scheduler.py` | The scheduler consumes the request and durably stores the accepted quote. |
| `StockTradePage.tsx` | `useStockTrade`, `api/stockTrades.ts`, and the v2 router | Live quote, refusal, replacement preview and receipt results reach the rendered ticket. |
| v2 `stock_trades.py` | Order service, transaction rollback and demand helper | The existing trade service precedes any freshness wait. |
| `deploy/verify-restore.py` | Revision-specific catalogue and grants aligned with the runtime schema contract | Recovery rejects incompatible inputs and restores the checked revision. |

Several GSD key-link heuristics look for literal filenames. The links above use relative Markdown links, shared PostgreSQL state, HTTP routes and indirect calls. Inspection and exercised flows verified the connections. The runtime paths contain substantive source checks, database reads and order mutations. The changed runtime files had no unresolved `TBD`, `FIXME` or `XXX` markers.

## Verification evidence

- Independently ran the isolated pure halt parser and authority tests, 6 passed. Ran `bash -n deploy/tests/test-stock-halt-recovery.sh` and `git diff --check`.
- Matched the live harness and the five runtime SHA-256 pins to the live receipt. Checked the harness's 201 fill and 200 exact replay assertions against the passed run and verified that crypto used the same portfolio cash and History.
- Checked the retained logs for 485 backend regressions, 17 final targeted regressions, 14 stock browser cases and all 26 PostgreSQL recovery contracts. The browser run used supplementary narrow-viewport reflow when headless Chromium did not apply native 200% zoom.
- The longer historical operations diagnostic reached its limit in the 0014 lane after retained 0013 passed and the 0014 backup and restore launchers completed. The selected rollback diagnostic passed its two 0008 lanes, then reached its limit in the retained 0014 candidate deployment after encrypted restore and TLS startup. The fixtures were cleaned. These runs provide partial historical evidence. The directly affected 0023/0024 encrypted recovery passed. Full release checks remain under Phase 21.
- The plans declare no standalone verification probes or deferred human-check blocks. The live flow and phase-specific browser behavior already have direct evidence. Phase 21 owns release browser acceptance and production activation.

## Requirements coverage

| Requirement | Plans | Result |
| --- | --- | --- |
| SX-01 | 03, 04 | Satisfied by the bounded selected-symbol request, regular-session whole-share quote rule and live fills. |
| SX-02 | 01, 02, 04, 05 | Satisfied by the approved reported-halt rule, final database guard, explicit refusals and disclosure. |
| SX-03 | 02, 04, 05 | Satisfied by selected-portfolio repricing and idempotency, exact cash and History, and restored original receipts. |
| SX-04 | 01, 05 | Satisfied for the original curated scope by the owner-attested account permissions, measured source usage and isolated AAPL/BTC evidence. |

All four Phase 18 requirement IDs trace to an implementing plan and observed evidence. No Phase 18 blocking gap or additional human checkpoint surfaced.
