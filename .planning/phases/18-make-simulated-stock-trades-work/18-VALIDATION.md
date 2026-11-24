---
phase: 18
slug: make-simulated-stock-trades-work
status: approved-for-planning
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-24
---

# Phase 18 validation

Use current pytest, Vitest and Playwright infrastructure. Use the project test
stack and retained release harness for checks that involve PostgreSQL, Redis,
restricted roles and recovery. The new tests below ship with their tasks.

| Plan | Requirements | Checks |
|---|---|---|
| 18-01 | SX-02, SX-04 | Check primary protocol and terms, sample live IEX quotes and official halt inputs within documented quotas, cross-check a known individual carryover and a confirmed historical market-wide halt or official sample. Validate decision receipt shape and evidence references. |
| 18-02 | SX-02, SX-03 | Test snapshot freshness, partial/stale/empty evidence, halt and resumption, per-symbol and global holds, deleted or changed evidence and expiry after lock waits. Run migration, exact historical replay, least-privilege, restore and rollback checks for affected schema paths. |
| 18-03 | SX-01 | Test quote source age 119.999/120 seconds, previous session, missing/invalid sides, concurrent refresh coalescing, quota, timeout, Redis loss, worker restart and unchanged crypto scheduling. |
| 18-04 | SX-01–SX-03 | Test real app preview/confirm, repricing, quote/halt/session races and unchanged cross-portfolio/idempotency protection. Run the affected browser flow. |
| 18-05 | SX-02–SX-04 | Verify the affected upgrade, restore, role and rollback paths. Run the regular-session live-price buy/sell plus crypto control in an isolated stack and require a qualified source and explicit passing receipt. |

After each plan run the tests named in its verify commands. Run targeted
Python/frontend lint, types and tests at integration. Run the affected
PostgreSQL recovery suite sequentially when a schema change invalidates prior
evidence. Never mark live qualification passed from a mocked source or count
a prior quote-only receipt as a stock fill.

The live check depends on an open regular session, a qualified source decision,
valid crawl budget and permitted test-feed use. Record the exact app revision,
request counts, redacted source timing and fill, cash, holdings and History
assertions. Public snapshots or historical examples may cover rare halt events.
Actual production activation belongs to Phase 21.
