---
phase: 08-corporate-action-safe-ownership
reviewed: 2026-11-11T13:21:58Z
depth: deep
monitor_source_sha256: 465be3c19d01be2254f3fbd073c2a9b4aeb3e2dbe2986fa261e7c7acf5813399
quote_scheduler_source_sha256: 98878dd757b32b34a960ebf5a7a3813be1b1fb1812720de2893276a041290f56
scheduler_source_sha256: b9f6be7cf4834aeb2627d35efc3ad64cbaa3be76a0600091803e871c2e3fba31
config_source_sha256: 862c8a8886ed4c9167ce69c40a1db2621a5e4dc47d1fe8b1047a881fad1e98d8
adapter_source_sha256: e8cb2eb9c5b79eb35918b02327107662f0a9e7a9a52b7eb128082e6caecf3a16
accounting_source_sha256: 804be2019da553662f46afa3f8071807c052c6f7e894e2b3a27dfc8a6fe82e60
files_reviewed: 12
files_reviewed_list:
  - backend/app/tasks/stock_actions.py
  - backend/app/tasks/stock_scheduler.py
  - backend/tests/test_stock_action_monitoring.py
  - backend/app/tasks/scheduler.py
  - backend/app/core/config.py
  - backend/app/services/alpaca_actions.py
  - backend/app/services/corporate_actions.py
  - backend/tests/test_scheduler.py
  - backend/tests/test_config.py
  - .env.example
  - docker-compose.yml
  - docker-compose.prod.yml
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan 08-07: Early Monitoring Review

Reviewed the core monitor, shared account-attempt hook and related source tests
against Plan 07 and stable accounting/adapter contracts. Task 2 wiring and its
configuration tests were still in progress and are not treated as completed
implementation. No tests, database/provider calls, credentials, process changes,
source edits or commits were performed.

## Narrative Findings (AI reviewer)

Formatting receipt: re-read the final shared quota helper at the quote-scheduler
hash above after Ruff signature formatting. Validated scoped quote/action quota
selection and the atomic account reservation are unchanged; no finding added.
No tests or runtime operations were performed for this identity-only follow-up.

### Final targeted CR-05 re-review

**Zero active BLOCKER/WARNING findings.** Verified corrected accounting source
SHA256 `804be2019da553662f46afa3f8071807c052c6f7e894e2b3a27dfc8a6fe82e60`.
The existing source/mutation observation is now consulted before revision/pointer/
epoch changes. Identical normalized facts return that original immutable revision;
changed economic/cancellation/verification facts retain `mutation_conflict`.
Local ingest-hold annotations are excluded from source-fact comparison without
rewriting the recorded classification or weakening final authority checks.
The A/B/replay-A regression source asserts the original result, newer current
pointer and unchanged revision count, plus divergent-A refusal. No tests or
runtime operations were performed in this re-review; reported 77-case database
proof and final combined validation remain executor evidence.

### Full scoped re-review

The four original findings below are resolved in their direct implementation:
only current cash-dividend events reach derivation; shared quota selection ignores
unrelated denied rows; REST tokens and fixed-target replay interval bisection are
persisted with policy/mapping/scope evidence; and published health is capped by
the calendar review deadline. The replay frontier advances only after a complete
inclusive interval. An interval too dense at the representable minimum remains
explicitly incomplete.

Task 2 source inspection confirms separately created quote/action clients and
independent concurrent loops, default-off action configuration, selected scheduler
credentials, bounded settings, finally cleanup and scheduler-only Compose
passthrough. Tests were inspected as source, not rerun. Runtime/coverage tests
were still running or being added by the executor. One cross-plan blocker was
identified at that review and is now resolved:

### CR-05 — BLOCKER, RESOLVED: Inclusive replay of an older observed mutation conflicts with newer state

**File:** `/home/YokaiExchange/backend/app/services/corporate_actions.py:379`

**Also affected:** duplicate-cursor lookup near line 474 and the monitor's durable
inclusive replay resumption.

**Issue:** A partial prior batch may validly persist mutation A for event X and
then a later update B for X. A resumed/bisected interval includes A again, as the
protocol is inclusive. Persistence compares A's terms to the current revision B
before checking its already stored cursor. It creates a held historical-revision
candidate, then finds the existing observation A references its original revision
and raises `mutation_conflict`. The whole instrument transaction rolls back, so
resumption cannot advance past an ordinary duplicate prefix. Adapter-local
deduplication cannot prevent this cross-cycle case.

**Fix:** Check the immutable source/mutation identity before revision or current
pointer changes. Validate incoming normalized facts against the originally
observed immutable revision, return the original result for an identical replay,
and retain conflict rejection for changed facts reusing the same cursor. Never
rewind the current pointer or invent a historical hold for an already recorded
identical mutation. Add actual PostgreSQL A/B/replay-A and resumed-monitor
regressions with immutable pointer/revision/count assertions plus divergent-A
refusal.

## Historical Findings

### CR-01 — BLOCKER, RESOLVED: Every split/unsupported event is sent to dividend derivation

**File:** `/home/YokaiExchange/backend/app/tasks/stock_actions.py:345`

**Issue:** The post-publication loop selects every event for an instrument and
calls `derive_dividend_entitlements`. That service explicitly raises
`ActionHeld('not_dividend')` for a forward split, merger or other non-cash-dividend
event. Thus any such persisted event makes otherwise complete monitoring cycles
fail after global health publication; later instruments are not processed. A
normal stock split is sufficient to reproduce the failure.

**Fix:** Select only current revisions whose normalized event type is cash
dividend for entitlement derivation, preserving held/cancelled dividend handling.
Continue processing split/unsupported safety through its proper path. Add a
mixed split/dividend/unsupported-event cycle regression covering all instruments.

### CR-02 — BLOCKER, RESOLVED: Unrelated denied quota rows can break quote-only collection

**File:** `/home/YokaiExchange/backend/app/tasks/stock_scheduler.py:52`

**Issue:** Shared account reservation reads `requests_per_minute` from every
admission row, even unrelated denied actions/status rows with the schema-valid
default `quota={}`. The quote path's own admission checks only require valid
quote/reference/calendar evidence, so previously working quote-only collection
now raises KeyError when an unused denied action row exists. Malformed or
wrong-account unrelated rows can similarly distort the account reservation.
Disabled action collection must not break the independent quote loop.

**Fix:** Derive the account limit from validated applicable same-account/server
quota authorities and the configured account cap, without interpreting denied
unrelated products as an active quota. Preserve accounting of every actual
quote/action attempt and retries. Add quote-only regression coverage with denied
empty-quota action/status rows and separately verify the combined active limit.

### CR-03 — BLOCKER, RESOLVED: Stored bounded continuations are never resumed

**File:** `/home/YokaiExchange/backend/app/tasks/stock_actions.py:216`

**Also affected:** snapshot invocation near line 204 and staged continuation
storage near line 256.

**Issue:** Replay always starts from `covered_until` or the original baseline;
that watermark advances only after complete batches. A replay that reaches its
mutation/response/time bound returns a usable partial continuation, but this
monitor neither stores nor consumes it. The next cycle therefore repeats the
same prefix forever. REST similarly stores `batch.continuation` but restarts the
same date window without supplying the token. An otherwise valid segment needing
more than the cycle's eight attempts cannot complete. These are normal bounded
catch-up cases, not evidence that source history is unavailable.

**Fix:** Persist and consume reviewed bounded progress for both REST pages and
mutation replay, or durably subdivide segments so each completed subsegment
advances a verified frontier. Keep partial observations/cursors atomic under the
instrument gate, retain incomplete health, bind continuations to scope/generation
and the fixed terminal target, and never skip unverified history. Add two-cycle
regressions where the first cycle hits a bound and the second makes forward
progress without restarting/omitting the prefix.

### CR-04 — BLOCKER, RESOLVED: Published health deadline can outlive reviewed calendar authority

**File:** `/home/YokaiExchange/backend/app/tasks/stock_actions.py:311`

**Issue:** Published `valid_until` is capped by product admission deadlines, but
omits `calendar.calendar['review_valid_until']`. If calendar review expires ten
seconds after publication while its admission remains valid for hours, states
advertise current monitoring for up to 120 seconds. The final guard verifies
calendar review only at publication time; it does not shorten the persisted
lease. This breaks the requirement that output validity cannot exceed any
underlying authority deadline.

**Fix:** Include the evaluated calendar decision's reviewed deadline in the
published minimum, together with applicable action/reference deadlines and the
health-age cap. Add a near-review-expiry test that asserts all 20 deadlines equal
the earlier reviewed limit and become unusable at that exact boundary.
