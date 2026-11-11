# Phase 8 local execution proof

Incremental actual evidence, not phase completion or live activation.

## Wave 1: Plans 01 and 03

Plan 01 adds constrained accounting schema 0011 and restricted grants; Plan 03
adds product-specific action admission and exact economic/safety rules.
Individual RED/GREEN commits and scoped results are in their summaries.

Independent early review found and resolved three schema blockers: alias
observations could not share an economic revision; movement causes lacked
user/instrument/unit correspondence; interrupted concurrent index creation broke
migration retries. Actual failing regressions and corrective commits are
recorded in 08-01-SUMMARY.md. Final independent schema review is clean.

The first full integration run exposed 22 failures (1089 passed): 20 stock API
constructor failures after the new local unit column, plus two historical test
expectations for the predecessor downgrade guard. The API now explicitly maps
provider-contract fields and suppresses nonzero-unit amounts until the full
unit-aware path is implemented. Seed downgrade tests exercise actual 0010.
Independent affected-scope review is clean. No earlier failure was ignored.

Final Wave 1 gate:

- Backend compileall: pass.
- Full guarded isolated backend suite: **1115 passed, 77 warnings, 54.26s**.
- Overall coverage: **99.71%**, existing 80% threshold unchanged.
- Expanded 23 critical modules: **1388 statements / 374 branches, 100%**.
- Saved full output: `/tmp/birja-phase08-wave1-backend-fixed.log`.
- Earlier failed output: `/tmp/birja-phase08-wave1-backend.log`.
- No source change followed this successful gate before the next plan.

The isolated birja-test PostgreSQL/Redis services remain healthy for subsequent
execution. No production services, provider requests or installed tools were
changed. Phase 7's live review remains owner-deferred; its frozen source hashes
are stale after authorized Plan 03 changes and must not be silently refreshed.
The scheduled check retains its fail-closed hash guard and has not been modified.

## Next gate

Plan 02 must extend exact revision-selected recovery and prove actual restricted
TLS populated upgrade/fresh parity for 0011 before new runtime consumers start.
Its canonical contract must include observations.event_id,
split_applications.coin_id, causal composite keys and the concurrent trade index.
Privileged bootstrap preprovisions the NOLOGIN operator role; restricted migrator
privileges must not be expanded to CREATEROLE. No requirement or entire phase is
marked complete by the infrastructure/rules evidence above.
