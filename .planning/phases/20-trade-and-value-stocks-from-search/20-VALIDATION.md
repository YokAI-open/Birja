---
phase: 20
slug: trade-and-value-stocks-from-search
status: ready_for_execution
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-24
---

# Phase 20 validation

Use the existing locked tools, disposable PostgreSQL and Redis, mocked provider
transport, Vitest and the guarded Playwright runner. No Wave 0 setup is needed.
The focused checks in each plan run after the affected task. Run a combined
slice at each integration boundary and the catalog browser suite once the
UI is assembled. Keep expensive exact restore checks at the end of the phase.
Record elapsed time and pin results to the source, schema and fixture inputs.

| Requirement | Focused verification |
|---|---|
| SL-01 | Real DB/API tests for stable promotion, owned preview and buy/sell, ask/bid and zero fee, repricing, idempotency, lock-time refusals, and capped selected and held work. Verify stale, halted and reused issue refusal plus original stock/crypto smoke. |
| SL-02 | Session and expiry checks for open, early-close, closed and reopen. Both browser price views retain a permitted SQL mark and show the local countdown with no cached quote, block submission and remove expired marks. |
| SL-03 | Real action ingestion and finance fixtures for coverage gaps/resume, ordinary dividend duplicate and correction, supported split, rejected fractional split, frozen sibling and targeted holds. Verify operator resolution after a same-issue rename. |
| SL-04 | Check balances, whole quantities, basis, fees, immutable catalog and legacy History and honest incomplete totals before and after rename, ticker reuse, cold Redis, restart and encrypted successor restore. |

Use short commands selecting the changed tests and retain 100% critical
coverage and the project overall gate. The finalized plans carry exact test
commands and sample map. New tests are written in their corresponding tasks.
Full hosted CI, production activation and live acceptance stay Phase 21.

## Per-task sampling

Run the exact <automated> command in the numbered task. Collect the
observable assertions from its acceptance criteria. Keep the fast
task checks separate from the browser and encrypted proof. Use a
fresh owned disposable stack for migration-only 20-01 and 20-02
checks. The shared running-app fixtures begin after 20-03 pins exact
0026. Serialize database suites that use the same Compose ports or
mutate migration roles, even if their source plans can run in parallel.

| Task | Wave | Requirements | Check |
|---|---:|---|---|
| 20-01-01 | 1 | SL-01, SL-03, SL-04 | Define the durable catalog financial contracts |
| 20-01-02 | 1 | SL-01, SL-03, SL-04 | Implement reviewed catalog issue promotion |
| 20-02-01 | 2 | SL-01, SL-03, SL-04 | Implement the catalog final execution statement |
| 20-02-02 | 2 | SL-01, SL-03, SL-04 | Add exact corporate-action posting and operator resolution checks for the bound issue |
| 20-03-01 | 3 | SL-01, SL-03, SL-04 | Pin current and retained runtime admission and the checked operator grant |
| 20-03-02 | 3 | SL-01, SL-03, SL-04 | Verify schema contracts and update current fixture selectors |
| 20-03-03 | 3 | SL-01, SL-03, SL-04 | Align deployment bootstrap fixtures with the exact current revision |
| 20-04-01 | 4 | SL-01, SL-02, SL-04 | Join selected demand with a bounded held-stock candidate set and verify the durable mark reader |
| 20-04-02 | 4 | SL-01, SL-02, SL-04 | Project the latest reported halts onto the exact selected or held issue |
| 20-05-01 | 4 | SL-03, SL-04 | Admit scoped action ingestion and detect incomplete coverage |
| 20-05-02 | 4 | SL-03, SL-04 | Apply corporate actions and verified hold resolution against the original issue and entitlement |
| 20-06-01 | 5 | SL-01, SL-02, SL-04 | Adapt the existing locked execution and replay path |
| 20-06-02 | 5 | SL-01, SL-02, SL-04 | Expose the owned catalog order contract and the closed mark in both price responses |
| 20-07-01 | 6 | SL-02, SL-03, SL-04 | Value only scoped owned holdings and return honest totals |
| 20-07-02 | 6 | SL-02, SL-03, SL-04 | Project original catalog receipts into private History |
| 20-08-01 | 7 | SL-01, SL-02, SL-04 | Connect catalog order and replay to the existing stock ticket |
| 20-08-02 | 7 | SL-01, SL-02, SL-04 | Preserve stable discovery and holding links across the existing surfaces |
| 20-08-03 | 7 | SL-03, SL-04 | Decode catalog History events and keep links bound to the original issue |
| 20-09-01 | 8 | SL-01, SL-02, SL-03, SL-04 | Exercise the owned round trip and both closed price views with a cold display cache |
| 20-09-02 | 8 | SL-01, SL-02, SL-03, SL-04 | Bind deployment and recovery profiles to exact 0026 and immutable retained 0025 |
| 20-09-03 | 8 | SL-01, SL-02, SL-03, SL-04 | Run the paired exact restore, source-tamper checks and replay |

Measure the affected coverage slice on the final integrated candidate.
Retain 100% critical trade, money and ownership coverage and the
existing overall gate. Preserve unaffected broad evidence at its exact
source. The final catalog browser suite and paired encrypted restore
run against the integrated source. Carry Phase 19 unresolved live
coverage and rights into the Phase 21 handoff.

## Plan check

The independent review approved nine plans and 21 tasks across eight waves.
The revision connected both closed-mark routes, the catalog History schema
and decoder, action resolution after a rename, and the retained 0025 fixture
inputs. All four Phase 20 requirements and all five inherited decisions map
to planned behavior and checks.
