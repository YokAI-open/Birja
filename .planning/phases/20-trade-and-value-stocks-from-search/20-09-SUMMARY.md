---
phase: 20-trade-and-value-stocks-from-search
plan: "09"
subsystem: integration
tags: [catalog, browser, recovery, postgres, restic]
requires:
  - phase: 20-08
    provides: Owned catalog ticket, Market selection, Portfolio and History
provides:
  - Isolated browser journeys for searchable stock trading and valuation
  - Paired encrypted recovery for retained 0025 and successor 0026
affects: [21]
requirements-addressed: [SL-01, SL-02, SL-03, SL-04]
requirements-completed: [SL-01, SL-02, SL-03, SL-04]
---

# Phase 20 Plan 09 Summary

Chromium exercised a simulated buy and sell for a stock outside the original 20 using the actual application and disposable PostgreSQL and Redis. It reconciled the original receipt, cash and History. It also exercised a verified cold-cache close, mark revocation, a halt, stale evidence, ticker reuse, and private Portfolio and History after a dividend and forward split.

The integrated review added a read-only original-order lookup. A missing receipt becomes definitive only after the signed, server-enforced preview expires under the portfolio lock. Original fills remain retrievable after expiry. A split triggers new-unit quote demand. Early ordinary actions before the ownership journal began leave new positions untouched. Continuing action coverage retains its valid lease while advancing its cursor. Portfolio uses a dated verified mark during a reported halt when display scope permits it. Markets refreshes its selected listing at session boundaries.

## Verification

- All seven guarded catalog browser journeys passed on final source `c842b9f` in 125.2 seconds. The matching before/after browser source inventory SHA-256 was `a84a5bf035211a9ba82ff22dd9ff3adf1acbf8b2873dd9f557ff2fbdf3fbddd2` and the run receipt SHA-256 was `ea88f552288d23635b4841142b8b0b9222c54dd3d4785796cc864032cf42439e`. No disposable browser resources remained. The run exercised keyboard access and 200% equivalent reflow. Native desktop zoom remains unmeasured.
- The earlier combined neighbor regressions passed 207 backend and 233 frontend cases. All 43 local validation contracts passed. These results cover the unchanged paths through `0eaf603`.
- All 63 final affected backend tests passed, including an expiry during a tentative fill that rolled back with no cash or trade changes. The run sampled five order, valuation and action suites. It measured 55.17% across the app and 79% across seven affected modules, and exited nonzero on the inherited 80% whole-app threshold. Full-suite coverage, including the unchanged 100% critical gate, remains a Phase 21 release check. Four pandas deprecation warnings were reported.
- Commit `1d5fb60` introduced the backup producer, restore consumer and successor deployment binding. The final rerun correctly rejected the earlier corporate-action source pin. Commit `b4118e8` synchronized the 0026 pins; the retained 0025 profile uses the original sources. Local recovery contracts passed 19/19. Static stock recovery contracts passed 20 with 10 SQL-only cases conditional on a running database. The guarded paired test uses a real database. The deployment compatibility contract passed.
- The final paired restic proof verified encrypted archive integrity, exact retained 0025 and successor 0026 restoration, restricted TLS roles and exact buy/sell/dividend/correction/split results. Cold replay preserved economic facts and original receipts without reapplying effects. Redis display cache was excluded and the populated 0026 downgrade was refused. The paired receipt SHA-256 was `2f3dd58d8248482aa5367d53e2778ba4243d4bbc24af5ed257a0f4ffa70b54da`. The exact producer SHA-256 was `1c2ecfeac5492bc3b676015f5eadc163b97d8ba2f74ee05e498fd8ec0dd43182` and consumer SHA-256 was `2fb2c9b92b9c81a362728dbc8d75938b8b5b1581bd57102207e0f32c795d00ba`.
- The retained 0025 fixture was reconstructed from `31cba00ca3f0c9d4214b6bb0b66892a4c81779fb`; its unchanged query SHA-256 was `36cdd7e9756936b3e0a79e6b249e833a0b5d11d4fad2d4181ab96ab485e0fb08`. The normalized 0026 schema SHA-256 was `d663c6cf07de20685b83d5f58a8a3381157d0b0afb087aa64dc6c34dd40c0626`. The reviewed 0026 migration SQL and the existing release gates remain in place.
- The final frontend build, full backend mypy and application Ruff checks passed. Vite reported a 584.60 kB minified application chunk. The focused ticket and Markets units passed 39 cases, including the single retry after an early or failed boundary refresh. The independent review closed all seven findings. [Code review](20-REVIEW.md)

## Phase 21 handoff

The Phase 20 findings apply to admitted synthetic fixtures. Phase 19's complete live directory coverage and expanded quote proof are open. Live acceptance also needs the applicable reference, quote, action, halt and durable fill/backup scope, measured expanded source quota, and a decision on the retention of the deciding Redis data in the production AOF or use of a volatile cache. Phase 21 owns whole-release CI, production rollout and the first live out-of-list buy and sell. [Phase 19 verification](../19-search-the-nyse-and-nasdaq-catalog/19-VERIFICATION.md) · [Roadmap](../../ROADMAP.md)
