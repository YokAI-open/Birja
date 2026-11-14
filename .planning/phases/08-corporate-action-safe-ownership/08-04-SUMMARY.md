---
phase: 08-corporate-action-safe-ownership
plan: "04"
subsystem: api
tags: [httpx, corporate-actions, decimal, sse, bounded-io]
requires:
  - phase: 08-03
    provides: Independent action admission and frozen normalized economic contracts
provides:
  - Current inclusive REST discovery and separate known-ID rechecks
  - Finite historical mutation replay with immutable observations and explicit gaps
  - Shared actual-attempt, byte, page, mutation, frame and elapsed-time budgets
affects: [08-06, 08-07, 08-12, 08-13]
tech-stack:
  added: []
  patterns: [HTTP-boundary mocks, frozen observation batches, serial shared cycle budget]
key-files:
  created: [backend/app/services/alpaca_actions.py, backend/tests/test_alpaca_actions.py]
  modified: []
key-decisions:
  - REST and replay use distinct current officially documented fixed HTTPS hosts.
  - Known-ID requests omit every mutually exclusive filter, including data_quality.
  - Source completeness is not financial health; absent economic verification remains unknown.
  - Terminal-ID replay requires an actual witness; historical timestamp replay requires normal protocol EOF and fully terminated frames.
patterns-established:
  - One caller-owned budget counts all actual HTTP attempts across REST, known-ID and replay work.
requirements-completed: []
requirements-addressed: [DIV-01, ACT-02, ACT-03]
duration: 18min
completed: 2026-11-11
---

# Phase 8 Plan 04: Bounded Corporate Action Observations Summary

**Current REST discovery, known-ID uncertainty and finite mutation replay return immutable source observations under one bounded action budget.**

## Performance

- Duration: approximately18minutes, completed2026-11-11T11:51UTC.
- Tasks:2/2, both with meaningful behavioral RED and GREEN commits.
- Source/test files:2; no new dependency, lockfile, service or configuration change.

## Accomplishments

`fetch_action_snapshot` uses inclusive `start`/`end` process-date filtering,
`data_quality=all`, region US, response-wide1000limit and bounded opaque pagination.
`recheck_action_ids` uses only IDs/limit/page token, since IDs are mutually
exclusive with **all** filters, including data_quality. Missing known IDs produce
`missing_or_uncertain`, never a fabricated cancellation.

`replay_action_mutations` uses the distinct official stream host, finite historical
`since`/`until` or inclusive `since_id`/`until_id`, and current array-shaped SSE
envelopes. Insert/update/delete observations remain distinct. Inclusive duplicate
emissions are deduplicated; conflicting/reordered cursors fail closed. An exact
terminal-ID witness may come from an unrelated stock, but unrelated observations
are validated and discarded before the batch leaves the adapter. Timestamp mode
accepts normal HTTP completion only under the documented historical-until close
contract, with fully terminated SSE frames. Idle timeouts, incomplete frames,
transport disconnects, unavailable products and missing terminal IDs remain gaps.

All requests share hard ceilings:8actual attempts (including retries),20pages,
256KiB/response,1MiB/cycle,30seconds/cycle,5seconds/attempt,1024mutations and
64KiB/frame. Approved quotas lower applicable limits. REST has at most one retry
per request, bounded Retry-After, cadence and jitter; replay never reconnects
automatically. Callback waits, sleep, headers and bodies stay under the cycle
deadline. Current scoped collection/derived/retention authority and lease are
reloaded around I/O. Revocation discards previously accumulated output.

The strict parser preserves Decimal precision and rejects duplicate keys,
excessive nesting/coefficient/exponent, invalid identities/dates, unknown groups,
unexpected symbols, oversized bodies and cursor loops. Currency absence/blank,
ordinary subtype, absent due-bill evidence and verified economic time are not
invented. Normalized terms require downstream reconciliation before automatic
economic effects. No stock execution, cash mutation or health renewal occurs.

## Public Protocol Evidence

Reviewed primary sources before implementation:

- https://docs.alpaca.markets/us/reference/corporateactions-1
- https://docs.alpaca.markets/us/reference/subscribetocorporateactionseventssse
- https://raw.githubusercontent.com/alpacahq/cli/main/api/specs/market-data-api.json
- https://www.python-httpx.org/async/

Public raw schema SHA256:
`2856fc7ed4dc6aa55a7b5db453a3cb8c5e9270b56e0679ded695bd926ec4e7dc`.
Bounded actual-shape public fixtures/source identity are pinned in the test file
before implementation. REST is `https://data.alpaca.markets/v1/corporate-actions`;
replay is `https://stream.data.alpaca.markets/v1beta1/events/corporate-actions`.
No private API request, secret read or provider account inspection was performed.

## Task Commits

1. Task08-04-01 RED: `5cc7e4b` — batch completeness assertion failed before implementation.
2. Task08-04-01 GREEN: `a2f7c82` —53mocked REST tests passed, scoped static checks passed.
3. Task08-04-02 RED: `6786bf3` — inclusive terminal mutation assertion failed before replay implementation.
4. Task08-04-02 GREEN: `4d1b327` — finite replay, required adversarial cases and strict critical coverage passed.

An initial import typo and mock unused-route assertion were corrected before
recording Task1's meaningful behavioral RED; neither was claimed as RED evidence.

## Verification

Final executed command:

```text
cd backend
uv run ruff format --check app/services/alpaca_actions.py tests/test_alpaca_actions.py
uv run ruff check app/services/alpaca_actions.py tests/test_alpaca_actions.py
uv run mypy app/services/alpaca_actions.py
uv run pytest tests/test_alpaca_actions.py tests/test_corporate_action_rules.py tests/test_stock_admission.py --cov=app.services.alpaca_actions --cov-fail-under=100 -q -x
```

- Final combined suite:298passed in3.91seconds;123adapter tests plus175rules/admission regressions.
- Adapter:504statements/220branches,100% each, no missing lines or partial branches.
- Ruff/format and source mypy pass.
- Existing16calendar/pandas deprecation warnings remain unchanged and out of scope.
- Pure adapter tests use mocked HTTP and existing isolated-stack guard. No database
  mutation, full-suite duplicate run, provider request or production access.
- Parent owns the subsequent independent review and full serial Wave2 gate;
  neither is claimed here as already passed.

## Deviations from Plan

**[Rule2 — Missing critical defense] Reject unexpected content encoding before
HTTPX decompression.** Even with identity requested, a hostile compressed response
could allocate before the decoded-byte limit. Both REST/replay reject nonidentity
encoding before body iteration; tests fail if the compressed body is touched.
Included in `4d1b327`, within the assigned adapter/test files.

Current official host and IDs-filter semantics clarify the planned protocol;
they are not a new provider, service or architectural change.

## Remaining Gates and Integration Contract

- Phase7 live identity/freshness acceptance remains owner-deferred. Its scheduled
  source manifest is stale after Plan03; no hashes/process were changed here.
- Actual action REST/replay access, quotas, latency, all-US transient ingress,
  display/derived rights and durable accounting/backup retention remain activation
  prerequisites. Mocked success does not establish account coverage or SLA.
- Caller must provide verified-TLS client, zero transport retries, no redirecting
  hooks, private headers and `trust_env=False`; Last-Event-Id is rejected so client
  defaults cannot override the reviewed finite replay range.
- Callers supply current evidence/lease callbacks (sync or awaitable), UTC clock,
  reviewed `StockMapping` values and one serial shared `ActionBudget`. Returned
  `ActionBatch` contains records, observations, coverage, continuation, complete,
  actual cumulative attempt_count and a fixed safe reason. Completeness describes
  transport/page coverage only. Current financial health belongs to Plan07.
- Multi-security identity-changing events may emit one held observation per
  affected curated mapping; they do not authorize economic identity changes.
- No known stubs prevent this plan's observation contract. Deliberately unknown
  economic verification fields are safety facts, not mocked live acceptance.
- Whole-phase requirements remain unchecked pending final phase verification.

## Self-Check: PASSED

Both created source/test files exist. All four RED/GREEN commits were verified
in the current branch log. No tracked files were deleted; unrelated `.claude/`
was preserved. Source freezes at `4d1b327` for parent review.
