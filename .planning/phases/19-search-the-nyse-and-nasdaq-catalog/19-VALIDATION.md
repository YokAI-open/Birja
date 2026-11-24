---
phase: 19
slug: search-the-nyse-and-nasdaq-catalog
status: ready_for_execution
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-24
---

# Phase 19 validation

Use the installed test infrastructure. Each plan adds tests with its
behavior. Mock vendor HTTP at the transport boundary and exercise persistence
and API contracts against disposable PostgreSQL and Redis. Use Vitest and
the existing isolated Playwright harness for Markets.

| Requirement | Evidence required |
| --- | --- |
| SC-01 | Reconcile both directories by row totals, included common shares, typed exclusions and unresolved rows. Cover exact/prefix/name ranking, one-letter and punctuated tickers, deterministic ties, bounds and empty results. |
| SC-02 | Reimport, failed refresh, real rename, delisting, share classes, ambiguous match and ticker reuse. Assert immutable identity, preserved historic links, concurrent publish and refused inactive or unresolved trade entry. |
| SC-03 | Select a verified fixture beyond the original 20, request only its quote, compare active identity, price and source time, then open its selected portfolio ticket. Exercise refused missing or stale data, permission gaps, unresolved units and identity mismatch. |
| SC-04 | Prove zero provider calls for search and result rendering. Coalesce matching selections, limit selected work and share the quote budget. Simulate timeout, rate limit, cache loss and malformed refresh. Verify last admitted catalog and crypto still work. |

Test fresh install, 0024 upgrade and relevant backup and restore if catalog
persistence changes schema. Preserve receipts, permissions and expiry.
Check keyboard and narrow-screen operation with fixture results, including
late responses and portfolio targeting. A bounded public inventory
assessment can qualify coverage during execution. Record unresolved rights
or rows in the coverage receipt. Full release CI and production acceptance
remain Phase 21.


## Phase 21 release handoff

Before enabling expanded production quotes, qualify the Redis cache for
the approved data-use scope. Production currently uses a persistent
append-only log. Verify permission for disk retention through log rewrite,
or use a volatile cache for these marks.

When qualifying the 0025 release archive, update the current-source profile
checks in `deploy/tests/run-portfolio-validation.py` and the accepted archive
inventory in `deploy/tests/ops-fixtures.py`. Their current checks name the
0024 profile. Preserve that profile for explicit retained 0024 lanes and
run the full release checks against the appropriate archive.
