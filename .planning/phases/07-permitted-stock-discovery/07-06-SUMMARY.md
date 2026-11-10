---
phase: 07-permitted-stock-discovery
plan: "06"
subsystem: api
tags: [iex, alpaca, decimal, postgres, admission, source-time]
requires:
  - phase: 07-05
    provides: Product-specific generation-bound admission and disabled settings
provides:
  - Bounded HTTP-boundary IEX quote collection with exact Decimal parsing
  - Pure strict source-age and regular-session bounds predicate
  - Atomic monotonically newer PostgreSQL quote persistence with current evidence checks
affects: [07-08, 07-09, 07-10, 07-13, 07-14]
tech-stack:
  added: []
  patterns: [raw Decimal decoding, source-time monotonic insert-select, snapshot-bound authority]
key-files:
  created:
    - backend/app/services/alpaca.py
    - backend/app/services/stock_quote_rules.py
    - backend/app/services/stock_quotes.py
    - backend/tests/test_alpaca.py
    - backend/tests/test_stock_quote_rules.py
    - backend/tests/test_stock_quotes.py
  modified: []
key-decisions:
  - "Quote eligibility consumes structural UTC session bounds; real calendar authority remains07-08."
  - "INSERT SELECT rechecks full current evidence and DB expiry without granting admission UPDATE for row locks."
requirements-completed: []
duration: 11min
completed: 2026-11-10
---

# Phase 7 Plan 6: Exact IEX quotes and monotonic persistence Summary

**Validated IEX bid/ask source events retain exact Decimal values and cannot overwrite a newer or equal-time observation; current authority is checked again in the write statement.**

## Performance

- Recorded start: 2026-11-10T15:11:04Z; completed: 2026-11-10T15:21:49Z.
- Tasks: 2/2; files: six owned production/test modules.

## Accomplishments

- `fetch_iex_quotes(http, symbols, admission, now, ...)` accepts at most20
  curated `StockMapping` values with verified provider identity. It fixes the
  official HTTPS batch endpoint, explicitly requests IEX/USD, disables redirects,
  and never substitutes SIP, trades, delayed or last-close prices.
- Raw bytes decode directly to Decimal, with duplicate-key/nonfinite/depth/byte
  limits. Response streaming, HTTP timeouts, at most3 attempts, quota-aware
  retry count, Retry-After/jitter and a maximum10-second outer deadline bound I/O.
  Errors contain classifications/status/classes rather than headers/provider text.
- Only regular R or separate-side RR conditions, IEX V/V venue provenance,
  listing-compatible tape and positive integer sizes are accepted. Invalid/missing
  symbols have separate classifications; accepted partial symbols survive.
- Positive finite NUMERIC(20,8)-representable bid/ask, bid<=ask and exact half-even
  midpoint are checked. UTC source timestamps determine age; receipt stays
  separate. Nanoseconds floor conservatively to microseconds, including a check
  against sub-microsecond future events. Exactly120seconds is refused.
- `quote_eligibility` consumes `RegularSessionBounds` with session_date,
  opens_at/closes_at properties. It requires UTC `[open,close)`, current matching
  session and exact `0<=source_age<120`. This confers no calendar authority,
  halt/action status, permission or stock execution capability.
- `load_stock_catalog` reads ordered active curated stock identities only.
  `upsert_stock_quotes` rereads evidence/catalogue, requires collection/retention/
  derived rights, validates generation and exact row values, then atomically
  rechecks the full evidence/mapping snapshot and database-clock permission
  expiry in INSERT SELECT. Conflict updates require a strictly newer event.
  Equal/older quotes never alter price, event or collected time; failed/missing
  symbols do not erase retained rows. Caller owns the short transaction/commit.

## Task Commits

1. Task07-06-01 RED `5751a84`; GREEN `fb66813`.
2. Task07-06-02 RED `caeb7a2`; GREEN `9d64606`.

Task1 meaningful RED:29 assertion failures/37 refusal passes against deny-only
contracts. Task2 meaningful RED:15 assertion failures/10 refusal passes using
independent populated PostgreSQL fixtures. No import failure counted as RED.

## Verification

- Exact Task1 command:66 passed before Task1 GREEN; final expanded slice68.
- Exact Task2 command:25 passed before final edge assertions; final slice26.
- Combined owned slice:94 passed in4.01seconds against guarded birja-test
  PostgreSQL/Redis and mocked HTTP. Includes actual concurrent reordered writes,
  equal-different event immutability, post-read committed revocation, actual
  DB-clock expiry before INSERT, partial batches and slow HTTP cancellation.
- Coverage of stock_quote_rules.py and stock_quotes.py:100% statements/branches
  (104statements/30branches), with fail-under100. This is scoped evidence, not
  the later full-suite/whole-phase critical gate.
- Ruff check/format and strict mypy passed on all owned production modules;
  six-file formatting/lint passed. `git diff --check` passed; no tracked deletion.
- Fixture teardown restored all provider mappings to unverified: isolated
  database aggregate confirmed zero nonnull/test-owned provider IDs afterward.
  Unrelated `.claude/` remains untouched. No secrets or production data read.

## Source and condition evidence

Public official documentation was checked2026-11-10, without a private API call:

- [Alpaca latest quotes](https://docs.alpaca.markets/us/reference/stocklatestquotes-1)
  documents the batch endpoint, explicit IEX selection and USD currency.
- [Alpaca maintained schema](https://raw.githubusercontent.com/alpacahq/cli/main/api/specs/market-data-api.json)
  defines stock_quote fields and one shared or two side-specific condition flags.
- [NYSE Daily TAQ specification3.3](https://beta.nyse.com/publicdocs/nyse/data/Daily_TAQ_Client_Spec_v3.3.pdf)
  and [Nasdaq UTP quote specification](https://www.nasdaqtrader.com/content/technicalsupport/specifications/utp/uqdfspecification.pdf)
  identify R as the regular two-sided quote. Other conditions are refused.

These source descriptions do not establish Birja's account access, display/
derived/retention permission or actual20-symbol coverage. Those remain07-14.

## Deviations from Plan

No architecture/scope changes. Because genuine sessions are implemented after
the package checkpoint, this plan defines only a structural bounds protocol in
its owned rules file; it does not import a missing calendar module or create a
fake evaluator.07-08 supplies genuine reviewed session bounds. Runtime admission
rows remain SELECT-only: statement-local evidence guards avoid FOR SHARE, which
would require an unauthorized UPDATE grant. No dependency was added.

## Issues Encountered

An initial test fixture depended on the unimplemented loader and had writer/
teardown ordering issues. It was corrected to independently construct catalogue
fixtures and close writers before cleanup; interrupted test processes were stopped
and meaningful RED/final verification ran serially. Final fixture cleanup passed.
Static checking also corrected the SQLAlchemy returning-statement variable type.

## User Setup Required

None for this offline implementation. No provider request/contact/signup,
agreement, payment, private configuration, production service, B2 operation,
publication or deployment occurred. Package review remains next07-07.

## Next Plan Readiness

07-08 genuine session results should implement the read-only structural shape:
`session_date: date`, `opens_at: datetime|None`, `closes_at: datetime|None`.
Only pass bounds after authoritative calendar admission/generation evaluation.
07-09 must configure the injected HTTP client's server-side secret headers,
reload current admissions around awaited collection and persist within a short
transaction.07-10 must apply current committed display/derived evidence and fresh
time at its final response boundary; stored rows do not grant permission.

Actual restricted-role consumer proof, full local gates and permitted live-data
acceptance remain07-13/14. STOCK-03/DATA-01 and whole-phase criteria stay pending.
Stock execution remains disabled throughout Phases7–8.

## Self-Check: PASSED

All six created files and four ordered RED/GREEN commits exist. Both tasks have
passing actual scoped tests. No blocking stubs; refusal returns are deliberate
validated outcomes. The planned HTTP/schema trust boundaries are covered; no
unplanned endpoint, financial mutation, runtime authority write or package exists.
