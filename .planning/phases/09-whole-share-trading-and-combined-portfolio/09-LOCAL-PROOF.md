# Phase 9 — Local Execution Proof

This records actual local results, not provider/live activation or production
readiness. Phase7 live evidence and Phase8 action activation remain deferred.
All nine Phase9 requirements stay pending until end-to-end verification.

## Waves 1–3

| Plan | Actual proof | Source / summary |
| --- | --- | --- |
| 09-01 |137schema/rule/quote-rule tests pass0.67s; scoped Ruff/format/Mypy pass |3c765db /fddebba |
| 09-02 |186affected stock/crypto math/schema tests pass1.78s; stock math72statements/24branches100%; scoped static pass |16b6c55 /b218105 |
| 09-03 |124real isolated migration/authority/ownership tests pass14.19s; scoped Ruff7files/Mypy2sources pass |c408be8 /5134cbc |

01/02 are pure contracts/math, not routes or financial writers.03 adds reviewed
Alembic0013 and narrow database authority. Actual retained encrypted recovery,
fresh/populated verifiedTLS and consumer replay remain09-04/later final gates.
The existing guarded birja-test stack uses approved pinned images and tmpfs;
no dev/production data, secrets or provider calls were used.

## Independent early source review

Review of14explicit files found0blockers and1warning: unexpected session strings
were treated as open by the pure rule, although the final SQL guard independently
required exact open. Actual RED e0f1802 reproduces allowed=True for garbage;
GREEN e5f122a explicitly whitelists open/closed in execution and valuation.
All12 malformed-state regressions and193affectedtests pass0.86s; scoped
Ruff/format/Mypy pass. Focused independent recheck closes WR-01 with no active
findings. See09-03-REVIEW.md for precise scope, hashes and finding history.

An off-hours historical-mark candidate was discarded as an unsupported policy
assumption; this work did not silently add a new market-data requirement.

## Current gate

Full backend initial regression failed7/1777passed165.64s,99.67%overall.
Tests-only correctionsb2d9f80/96e780b preserve original financial assertions and
add complete0013isolation facts; see09-03-INTEGRATION.md.
Subsequent full backend gate passes1793tests/73warnings168.97s,99.83%overall.
All31critical modules3217statements/1052branches100%, with no partial branches.
Exact existingCLAUDEcritical list plus newstock math/rules was measured from
the actual full-run coverage data. CI/CLAUDElist expansion remains09-14.
Runtime stock consumers remain behind09-04 recovery/role/TLS proof. No packages,
private calls, installed production-tool changes, activation or publication.
