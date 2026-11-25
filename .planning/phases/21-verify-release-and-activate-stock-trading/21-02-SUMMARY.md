---
phase: 21-verify-release-and-activate-stock-trading
plan: "02"
subsystem: stock-catalog
tags: [catalog, admission, redis, scheduler]
requires:
  - phase: 20-09
    provides: Catalog 0026 ledger, permission checks and recovery
provides:
  - Restricted catalog packet review, apply and renewal procedure
  - Volatile catalog demand, result and display path with shared provider quota
affects: [21-03, 21-04, 21-06, 21-08]
requirements-addressed: [SV-02, SV-03]
requirements-completed: []
completed: 2026-11-25
duration: 21 minutes
tasks: 3
---

# Phase 21 Plan 02 summary

The restricted 0026 operator can review an exact catalog packet and apply
the approved file digest. Review rolls back. Apply rechecks the current
generation and applicable listing and provider evidence under the catalog
lock. Existing publication and promotion tests cover stable financial
identity through a verified listing change. Replacement admissions retain
earlier evidence with its revocation timestamp.

Production Compose routes catalog selection, completion and display through
a distinct internal Redis service with a tmpfs data directory. The scheduler
uses the original state Redis for the shared provider quota and report timing.
The catalog halt loop reads pending selections from the catalog instance.
An absent or unavailable catalog client leaves refresh unavailable while
independently admitted durable data and existing state services remain usable.

| Task | Commit | Verification |
|---|---|---|
| Review and rehearse the operator packet | `22bbd9f`, `eded7fd` | Expected RED on absent operator command, then passing real restricted-migrator review/apply, stale generation, overlap and expiry refusal, exact replacement and retained revocation tests. Sixteen existing and affected publisher, promotion and migration cases passed, and the final expanded operator case passed on recheck. |
| Wire the catalog cache | `a85c568` | Synthetic Compose render and scoped Ruff and mypy passed. The cached pinned Redis image had no disk files after a synthetic display write, and restart removed the key. Runtime role and live flags retained their default scopes. |
| Preserve atomic completion and shared budget | `63f5720` | The selected 49-case catalog/scheduler/halt run passed 48 and found one stale request fixture. The final 11-case affected rerun passed, including atomic completion, refusal with exhausted shared cap, separated halt selection, cache outage without state fallback, and original scheduler controls. Existing CI and runner contracts passed 113 and 44 respectively. |

The Redis routing tests use distinct logical databases inside the disposable
fixture to detect incorrect client use. The separate daemon rehearsal and
Compose render verify the actual distinct volatile production topology.
The existing pandas deprecation warnings remain visible.

## Deviations

- The reported-halt worker also consumes catalog pending requests when a
  listing first becomes eligible for a report. Updated that caller and its
  narrow test fixture to use the catalog client while keeping report timing
  on state Redis.
- Two existing fixtures needed the current interface. The catalog confirm
  refusal fixture now supplies the schema-required preview token. The
  scheduled-loop fixture accepts the existing optional heartbeat argument
  and counts the health-bearing loops it was written to verify.
- The operator fixture temporarily uses the production-shaped schema owner
  when a preceding disposable migration suite has reset it to the test
  administrator. It restores the previous fixture owner afterward.

## Handoff

Plans 03 and 04 still own deployment rehearsal and full integrated
qualification. Plans 06 and 08 establish the actual field and purpose rights,
approved runtime scope, and exact live admission and release receipts.
This plan uses synthetic evidence and disposable services. The test projects
were removed after verification.

## Self-Check: PASSED

The expected source, test and documentation files exist. Each task commit,
the focused final exit status, the strict lint and type checks, and disposable
cleanup were verified.
