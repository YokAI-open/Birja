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


## Plan09-04 final recovery proof —2026-11-12

Source/test commits through e8d3bb2. Final canonical serial --all exits0;
log /tmp/birja-phase09-04-all-consistent.log. One retained archive
08131798ce5d3893bde0da4cf566d46de5e77654f47b87dbd3f912898e14278c
(152197120bytes) covers exact0007–0013 rows/schema/identities with unchanged
source and denied feature checkout. Retained recovery395.688s, restricted
roles181.408s (63 denied operations), populated0012→0013 TLS126.301s and
fresh0013 TLS122.868s. Both TLS lanes pass certificate/hostname/plaintext
negatives, exact runtime ACL parity and actual invoker/ownership consumers.

Actual new stock source/restored history has two same-stock receipts, complete
baseline and contiguous journal; duplicate rejection adds no effect/counter.
Ten new execution corruptions, nine accounting, seventeen identity and thirteen
operator-authority corruptions are rejected. Offline10passed/3explicit SQL-only
skips0.044s; restore-safety6passed1.402s; compile/shell/whitespace pass.

Inline review found and fixed nonunique receipt hash ordering (5a59aa0/603e43a)
and synthetic missing history (e17ef25/e8d3bb2). Both real RED/GREEN proofs are
recorded in09-04-SUMMARY/REVIEW. Agents lacked filesystem/shell tools; review
was a distinct inline pass, not independent. Actual stock execution service
replay/concurrency and its restored TLS consumers remain06/07/14 obligations.
No provider, production, B2, timer, push, merge or deployment change.


## Plan09-05 verified status and eligibility —2026-11-12

Source732af2c; summary/review89f4245. Finite normalized status batches,
post-wait persistence guards, no-source startup invalidation and current
execution snapshots pass actual isolated PostgreSQL tests. Durable financial
facts require explicit accounting/backup scope; data retention deadlines cap
final authority without changing0013 identities. No live transport is enabled.
Full backend1889passed202.08s,99.85%overall; all35critical modules
3534statements/1154branches100%. Ruff, format and Mypy pass. Logs:
/tmp/birja-phase09-05-backend-final.log and
/tmp/birja-phase09-05-critical-all.log. Separate inline review has no open
blocker; agents lacked tools, so independence is not claimed. Actual execution,
API/client integration and production/provider acceptance remain later plans.


## Plan09-06 atomic execution —2026-11-12

Sourcee7e3a47; summaryce025f9. Final153 service/key/crypto/ownership tests
pass20.76s; new services174statements/40branches100%. Scoped Ruff/format/Mypy
pass. Actual key/filter REDf04b90a and preview REDd26c35c preceded implementation.
Review REDc0037e4 fixes halted future-quote disclosure using historical mark
validation. Original receipt replay survives sale/rename/revocation; changed
payload conflicts; late authority, integrity, DB, ownership and cancellation
failures leave exact pre-state. Actual multi-session races and opposite-side
metadata refinement remain07. No live/provider/production/publication change.


## Plan09-07 actual contention and waits —2026-11-12

Sourcea185fba; summaryf8de7cf. Final248tests pass63.39s;185statements/42branches
100%. /tmp/birja-phase09-07-services.log records the serial gate. Actual PG
instrument/account/holder/helper/final-boundary waits, current authority changes,
real clock expiry, original replay and causal action processing are verified.
No relation wait INSIDE the final function is claimed by boundary instrumentation.
One full rollback quote-metadata rebuild resolves actual RED050bfa0 without
rewriting immutable rows or retrying lock/constraint/permission failures.
Distinct inline review is clear. API/portfolio/UI/recovered runtime/full gates
remain08–15; no live/provider/production/publication change.


## Plan09-08 private HTTP —2026-11-12

Source77a4001/ea2472b. Actual HTTP RED04067a0 precedes wiring. Final224tests
pass58.92s plus matched split1test2.08s;253statements/50branches100%.
/tmp/birja-phase09-08-final.log. No-store validation/auth/refusal and uncertain
post-commit outcome recovery are tested; deep receipt JSON uses actual persisted
Decimal scales before final guard. Shared sale cash funds crypto then stock
without a new grant. Owner-scoped same keys never expose another receipt.
Separate inline review is clear; portfolio/UI/recovered runtime/full gates
remain09–15. No provider, production, B2, timer or publication change.


## Plan09-09 coherent mixed valuation —2026-11-12

Source64c8611; puremath844f957. ActualRED9c72830/72dbda3 and reviewRED689567b
precede fixes. Final66tests14.45s,171statements/42branches100%, scoped static
checks pass. /tmp/birja-phase09-09-final.log. One financial statement plus
suppress-only current authority; actual mixed commits, old/new units, original
rights, strict deadlines and HTTP plain values are proved. No mark is minted
without original quote-generation permission proof. No new schema/grant or
retained recovery identity. Client/UI/full gates and owner acceptance remain.
No provider/production/B2/timer/publication change.
