# Phase9 — Multi-source Coverage Audit

Status: planned coverage, not executed proof. All9 assigned requirements and16 locked decisions have concrete tasks. No new provider calls, dependencies, production changes, publication, Phase10 payment/public event History or Phase11 final rollout are scheduled. Existing live deferrals remain.

## Four-source coverage

| Source | ID / constraint | Owning plans/tasks | Status |
| --- | --- | --- | --- |
| GOAL | G1 Whole-share side-price preview, persisted fill, reconfirmation and disclosure | 01–02,06,08,10–11,13–15 | COVERED |
| GOAL | G2 Original shared cash, mixed concurrency, immediate proceeds and action-order capture | 06–08,13–14 | COVERED |
| GOAL | G3 Independent session/status/action/freshness refusal after all waits; crypto independent | 01,03,05–08,10–11,13–14 | COVERED |
| GOAL | G4 Exact once-only original replay after close; changed payload conflict | 03–04,06–08,10–11,13–14 | COVERED |
| GOAL | G5 Mixed midpoint portfolio, original-start returns, dated/incomplete marks and once-only future cash | 09,12–15 | COVERED |
| REQ | MKT-02 | 01,03–08,10–11,13–15 | COVERED |
| REQ | STKTR-01 | 01–03,06,08,10–11,13–15 | COVERED |
| REQ | STKTR-02 | 02–03,06,08,11,13–15 | COVERED |
| REQ | STKTR-03 | 01–06,08,10–11,13–15 | COVERED |
| REQ | STKTR-04 | 06–07,13–15 | COVERED |
| REQ | STKTR-05 | 01,03–04,06–08,10–11,13–15 | COVERED |
| REQ | STKTR-06 | 02,06–08,11,13–15 | COVERED |
| REQ | PORT-06 | 01,04,09,12–15 | COVERED |
| REQ | PORT-07 | 01,05,09,12–15 | COVERED |
| RESEARCH | R01 Separate API/service/math tiers and fixed request/receipt contracts | 01–02,06,08 | COVERED |
| RESEARCH | R02 Exact positive lexical whole-share and numeric capacity bounds | 01.1,02.1 | COVERED |
| RESEARCH | R03 Half-even cent notional, zero-free-share rejection and cost basis policy | 02.1 | COVERED |
| RESEARCH | R04 Conservative bounded Buy max and verified Sell all | 02.2,08.1,11.1 | COVERED |
| RESEARCH | R05 Actual independent status event vs continuity; default unknown | 01.2,05.1 | COVERED |
| RESEARCH | R06 Explicit baseline/generation/loss/reconnect/out-of-order halt safety | 05.1–2,10.2 | COVERED |
| RESEARCH | R07 Reachable finite offline scheduler source and no invented live endpoint | 05.2 | COVERED |
| RESEARCH | R08 Separate access/display/derived/durable rights and actual quota gates | 01.2,05.1–2,06.2,09.2,14.2 | COVERED |
| RESEARCH | R09 Same stable instrument gate, one instrument per transaction | 06.2,07.1–2 | COVERED |
| RESEARCH | R10 Shared account then all instrument holdings in deterministic order | 06.2,07.1 | COVERED |
| RESEARCH | R11 No account→stock reverse edge or own-holding-first all-holder deadlock | 06.2,07.1 | COVERED |
| RESEARCH | R12 Post-helper/read/write/constraint wait final current committed guard | 03.2,06.2,07.2 | COVERED |
| RESEARCH | R13 Advancing DB wall clock and documented statement-snapshot linearization | 01.2,03.2,07.2 | COVERED |
| RESEARCH | R14 Atomic Trade/facts/cash/movement/basis and cancellation rollback | 03,06.2,07.2 | COVERED |
| RESEARCH | R15 Cross-asset global idempotency helper both endpoints and uniqueness race | 06.1–2,07.1,08.2 | COVERED |
| RESEARCH | R16 Immutable symbol/name/source/balances/units receipt and after-close replay | 01.1,03.1,06,08,10–11 | COVERED |
| RESEARCH | R17 Selected-side repricing only and second confirmation | 02.1,06.2,08.2,10–11 | COVERED |
| RESEARCH | R18 Successor-only0013 actual guards, safe downgrade and no prior-row rewrite | 03.1 | COVERED |
| RESEARCH | R19 Fixed invoker bodies/search_path/owner/ACL plus actual42501 tests | 03.2,04,14 | COVERED |
| RESEARCH | R20 Fresh/populated upgrade parity without grant repair before runtime | 04.2 | COVERED |
| RESEARCH | R21 Exact0007–0013 same encrypted archive/identities/corruption rejection | 04,14.1–2 | COVERED |
| RESEARCH | R22 Actual restricted service consumer/receipt replay after restore | 14.1–2 | COVERED |
| RESEARCH | R23 One coherent mixed financial snapshot and current-authority-only suppression | 09.2 | COVERED |
| RESEARCH | R24 Exact unrounded midpoint, cost basis and original starting-cash returns | 09.1–2 | COVERED |
| RESEARCH | R25 Historical closed/halt mark independent of execution120s freshness | 01.2,09.2,12.1 | COVERED |
| RESEARCH | R26 Retention/generation/unit/action override; no weekend rights extension | 09.2,12.1 | COVERED |
| RESEARCH | R27 Known subtotal/count and null global returns/allocation, no normalization | 09.1,12 | COVERED |
| RESEARCH | R28 Cash from Account once, no entitlement re-add/payment implementation | 09.1,12.2 | COVERED |
| RESEARCH | R29 Guarded identity/fullRTT/deadline/epoch high-waters in cache and view | 10,12.1,13 | COVERED |
| RESEARCH | R30 Unknown-outcome frozen body/key, after-close result resolution | 10.1–2,11,13.1 | COVERED |
| RESEARCH | R31 Distinct reachable stock route, memory draft and explicit reopen confirm | 11.2,10.2,13 | COVERED |
| RESEARCH | R32 Real PG races, first fill/split/cutoff/XID limitation, no DB mocks | 07 | COVERED |
| RESEARCH | R33 100%critical/80%overall mirrors, audits, five strict image scans | 14 | COVERED |
| RESEARCH | R34 Actual browser/accessibility/owner acceptance/independent reviews | 13–15 | COVERED |
| RESEARCH | R35 No packages/install/downloads, no assumed provenance certification | All threat registers T-09-SC | COVERED |
| RESEARCH | R36 ASVS5 L1 trust boundaries; all unresolved high severity blocking | All threat registers;14.2 | COVERED |
| RESEARCH | R37 Live status suitability and Phase7/8 evidence deferred and disabled | 05,14–15 | COVERED |
| CONTEXT | D-01: User edits only positive whole-share stock quantity; Buy max/Sell all populate drafts requiring preview and confirmation. | 01,02,06,08,10,11,13,14,15; cited in task actions and truths | COVERED |
| CONTEXT | D-02: User sees IEX bid/ask, buys at ask or sells at bid with zero stock fee/spread; crypto inputs/fees remain unchanged. | 02,03,06,08,11,13,14,15; cited in task actions and truths | COVERED |
| CONTEXT | D-03: Relevant stock price changes show old-to-new execution price and cash-total difference and require renewed confirmation. | 01,02,06,07,08,10,11,13,14,15; cited in task actions and truths | COVERED |
| CONTEXT | D-04: User remains on original persisted receipt with historical cash/share-after and Portfolio/Trade again actions. | 01,03,04,06,08,10,11,13,14,15; cited in task actions and truths | COVERED |
| CONTEXT | D-05: User sees one shared cash balance and combined labelled Stock/Crypto holdings list. | 09,12,13,14,15; cited in task actions and truths | COVERED |
| CONTEXT | D-06: Holdings remain alphabetical by ticker with stable identity tie-break as prices refresh. | 09,12,13,14,15; cited in task actions and truths | COVERED |
| CONTEXT | D-07: Quantity, average cost, basis, value, gain/loss and allocation appear directly in desktop table/mobile cards. | 09,12,13,14,15; cited in task actions and truths | COVERED |
| CONTEXT | D-08: Allocation displays Cash/Stocks/Crypto class bars and individual holding percentages only when complete. | 09,12,13,14,15; cited in task actions and truths | COVERED |
| CONTEXT | D-09: Incomplete portfolio shows Known value and unvalued count, with unavailable total returns and all allocation percentages. | 01,09,12,13,14,15; cited in task actions and truths | COVERED |
| CONTEXT | D-10: Verified halt retains permitted compatible dated last midpoint with Halted label; action uncertainty suppresses it. | 05,09,12,13,14,15; cited in task actions and truths | COVERED |
| CONTEXT | D-11: Unavailable stock ticket allows quantity drafting but disables confirmation and unsafe estimates; no order is queued. | 05,10,11,13,14,15; cited in task actions and truths | COVERED |
| CONTEXT | D-12: Interrupted review retains quantity, invalidates preview and requires fresh preview plus confirmation without autoexecution. | 05,10,11,13,14,15; cited in task actions and truths | COVERED |
| CONTEXT | D-13: Stock journey discloses IEX single venue, simulated execution, omitted regulatory fees and immediately reusable virtual proceeds. | 02,08,11,12,13,14,15; cited in task actions and truths | COVERED |
| CONTEXT | D-14: New fills require current regular session, normal independent status and action/permission safety plus quote age strictly below120seconds after all waits. | 01,03,04,05,06,07,08,10,11,13,14,15; cited in task actions and truths | COVERED |
| CONTEXT | D-15: Mixed orders share original cash without new grant/overspend; same-key original receipt replays even after close and payload changes conflict. | 01,03,04,06,07,08,10,11,13,14,15; cited in task actions and truths | COVERED |
| CONTEXT | D-16: Stocks use midpoint/dated closed marks; unknown actions make valuation unavailable, and future dividend cash is counted once from Account.cash. | 01,07,09,12,13,14,15; cited in task actions and truths | COVERED |

## Dependency/ownership graph

| Plan | Wave | Needs | Creates | Checkpoint |
| --- | --- | --- | --- | --- |
| 09-01 | 1 | Saved context/research/UI | Freeze stock financial and authority contracts | No |
| 09-02 | 2 | 09-01 | Implement exact whole-share plans and conservative shortcuts | No |
| 09-03 | 3 | 09-01, 09-02 | Add successor stock facts and independent status integrity | No |
| 09-04 | 4 | 09-03 | Prove exact0013 recovery and least-privilege TLS parity | No |
| 09-05 | 5 | 09-04 | Implement bounded independent status and stock eligibility | No |
| 09-06 | 6 | 09-02, 09-04, 09-05 | Implement atomic stock execution and global idempotency | No |
| 09-07 | 7 | 09-06 | Prove shared-cash, action-order and final-wait concurrency | No |
| 09-08 | 8 | 09-07 | Expose authenticated stock preview, context and fill APIs | No |
| 09-09 | 8 | 09-07 | Compute honest mixed portfolio from one financial snapshot | No |
| 09-10 | 9 | 09-08 | Implement strict stock client and protected order-attempt lifecycle | No |
| 09-11 | 10 | 09-10 | Deliver the reachable whole-share ticket and immutable receipt | No |
| 09-12 | 9 | 09-09 | Present protected combined portfolio and three allocation classes | No |
| 09-13 | 11 | 09-11, 09-12 | Exercise actual isolated browser journeys and accessibility | No |
| 09-14 | 12 | 09-13 | Close strict local financial, recovery and independent review gates | No |
| 09-15 | 13 | 09-14 | Obtain owner acceptance of the new Phase9 interface | Owner actual UI acceptance |

All same-wave file sets are disjoint. Shared files serialize through explicit dependencies. Each plan has2tasks; separate15 owns only genuine UI acceptance, after automation. Long operations are serial, not parallel fixed-project fixtures. Missing tests are created by their own task before implementation; no speculative scaffold-only plan. Critical constraint (schema/current authority/cross-row financial integrity) is fixed in01/03 and proven in04 before runtime06.

## Threat and schema obligations

Each plan registers T-09-NN-{V,A,I,D,R}, with concrete task behaviors; T-09-SC forbids unreviewed packages.03/04 specifically own cross-row triggers, invoker final guard, qualified static SQL, no elevated membership, immutable facts, safe downgrade, restored function identity/ACLs and both TLS lanes.06/07 own post-helper last-business-statement authorization and rollback.10/12 own auth identity/epoch/deadline cache guards.14 independently audits all mitigations; unresolved ASVS L1/HIGH/CRITICAL blocks. Live provider rights/status history/quotas/latency cannot be established by these isolated tests.

## Planning reasoning

Irreversible choices are additive0013 immutable receipt/cause integrity and status authority provenance; they receive migration/grants/recovery proof first. Reversible UI composition stays within accepted design contract. Pre-mortem failures: stale authority after journal waits (03/06/07 last guard), cross-asset key/deadlock races (06/07 real PG), old-unit historical marks or incomplete totals overstated (09/12/13 exact snapshot/cache tests). No source item is missing. Local recovery of new schema is required now; Phase11 remains final milestone rollout acceptance. Existing explicit external deferral is recorded, not reapproved.
