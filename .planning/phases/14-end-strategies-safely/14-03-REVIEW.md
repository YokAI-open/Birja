---
phase: 14-end-strategies-safely
plan: "03"
reviewed: 2026-11-19
depth: standard
source_commit: 328b1e3
initial_source_commit: 2b08c42
diff_base: 0e8e408
files_reviewed: 8
files_reviewed_list:
  - backend/app/services/portfolio_closure.py
  - backend/app/services/stock_ownership.py
  - backend/app/services/corporate_actions.py
  - backend/alembic/sql/0023_portfolio_closure.sql
  - backend/alembic/versions/0023_portfolio_closure_authority.py
  - backend/tests/test_portfolio_closure_stocks.py
  - backend/tests/test_portfolio_closure_clocks.py
  - backend/tests/test_migrations.py
initial_findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 14 Plan 03 — Independent Code Review

## Current Recheck Result

CR-01 is resolved at328b1e3 by code fix322e5d9, following real RED3e30b5e.
Current remaining BLOCKER:0; WARNING:0. The original finding and initial count
are retained below; this was not an initially clean implementation.

The repair adds exactly `lifecycle.confirmation_name != account.name` refusal
inside the owner_confirmation branch before the existing linked-intent proof.
It rechecks the frozen evidence invariant without comparing the fresh incoming
request's reviewed name against that evidence. Thus a valid fresh-key closed
acknowledgement can still use a different incoming name, while jointly corrupted
retained names are refused.

Reviewed the complete source change and both real PostgreSQL regression
variants: empty and multi-stock. Each proves a valid different-name fresh-key
acknowledgement first, then jointly corrupts only lifecycle/intent names through
a declared privileged fixture, requires OwnershipHeld invalid_closure with no
open transaction, and compares all retained financial/evidence rows and old/new
sequence states before and after refusal. No source or test weakening was found.

Executor evidence:4focused cases30.62s;31affected stock/clock/backfill cases
240.60s; scoped Ruff/format and ownership mypy pass, with owned repair resources
removed. Repair receipt is `/tmp/birja-phase14-plan03-repair/receipt.json`.
These are new repair results, not relabelled original53-case qualification.
This reviewer did not rerun them. No introduced blocker or warning identified;
Plan04 may proceed with the existing exact-admission handoff.

## Original Narrative Findings (AI reviewer)

One BLOCKER identified in the complete closed-acknowledgement proof. No other
proven blocker or warning found in the reviewed changes. This is a source
review; the reproduction below was traced through the exact control flow and
was not executed by this read-only reviewer.

### CR-01 — BLOCKER: closed acknowledgement omits frozen confirmation-name integrity

**File:** `backend/app/services/stock_ownership.py:632` (owner-confirmation
branch through649).

**Issue:** The proof checks that the immutable intent's confirmation name
matches the lifecycle confirmation name, but never checks that this name also
matches the frozen account's name. The original0021 integrity trigger explicitly
requires that equality (`0021_portfolio_closure_schema.py:48`). A closed book
whose lifecycle and original intent names were jointly corrupted to another
valid canonical name therefore passes this supposedly complete proof when
acknowledged using a fresh key.

This is the same privileged retained-corruption threat model exercised by the
new fill-history/replay tests, not a claim that ordinary app roles can update
these immutable rows. The requirement is to refuse corrupt retained closure
evidence, including an owned already-closed acknowledgement. SQL's closed
branch checks owner/time, stock membership and per-stock bounds but does not
recheck this name invariant; a fresh incoming key has no prior journal entry.
The Python branch then sees mutually matching corrupted intent/lifecycle names,
and its request lookup is absent, so it commits and returns closed. Every stock
check can remain valid, and a crypto-only/empty book has no later stock proof
that could detect the inconsistency.

**Reproduction to add:**

1. Close an owned book normally using the new service and retain its account
   name, e.g. Strategy.
2. In a declared privileged corruption fixture, disable USER triggers only on
   `portfolio_lifecycle_closures` and `portfolio_closure_intents`, change the
   lifecycle and its linked closed intent's `confirmation_name` to a different
   valid canonical name, and re-enable triggers. Leave account.name unchanged;
   other lifecycle/financial data and constraints remain intact.
3. Call `close_portfolio` with a new UUIDv4 key for that owned closed root.
   Current code returns closed; expected outcome is OwnershipHeld invalid_closure
   with no new outcome or financial/lifecycle mutation.

**Fix:** In the owner_confirmation proof require
`lifecycle.confirmation_name == account.name`, in addition to the existing full
intent/lifecycle equality. Preserve fresh-key acknowledgements of valid closed
books (the fresh request's reviewed name need not equal the original frozen
name). Add the real PostgreSQL corruption/replay regression above, ideally
covering both crypto/empty and stock-bearing books, then rerun affected proof
and retained migration compatibility cases. No historical migration rewrite is
needed; this is a missing application verification check.

## Other assessed boundaries

- Existing financial one-instrument entry still acquires its unchanged guard;
  complete verification moved into a private core without removing its
  accounting, closure/unit/digest or pending financial assembly checks.
- The closure service binds immutable originals to its SQL result and current
  transaction, verifies every historical member, commits only after proof,
  removes private context in finally and rolls back whole40001attempts with
  a three-attempt bound. Durable refusal commits only its nonfinancial outcome.
- Advisory-lock evidence is backend/database-scoped and requires granted
  ExclusiveLock in the correct bigint namespace. It does not accept merely a
  shared lock, another backend's lock or a guessed financial marker.
- Service and new successor trigger fences inspect already-held gates rather
  than acquiring behind account locks. They compare movement recorded_at and
  application processed_at strictly against the latest instrument closure.
  No later timestamp is synthesized. Normal pending multi-owner split assembly
  remains on the financial wrapper's explicit exemption path.
- New guard ownership/signature/trigger additions are explicit; only the
  still-developed0023 checksum and its finite test inventory were extended.
  No old profile or historical0015–0022 migration change appears in scope.

## Verification evidence and limits

Reviewed the three service modules and their changed call paths, both new test
modules, new SQL trigger and migration checksum, finite prerequisite extension,
03PLAN/SUMMARY, interface contract and relevant existing0021/0022 guards.
The executor's53-case352.85s plus two strengthened18.95s cases are recorded
evidence, not tests independently rerun here. Existing tests cover damaged
financial history, stale transaction context, actual first-buy retry and clock
refusal/continuation, but not CR-01's joint confirmation-name corruption.

Runtime admission, critical-list expansion, API transport and whole-phase
qualification remain explicit downstream plans and are not findings against
this step. No source edits, tests, packages, runtime/provider/production
operations or commits were performed. Only this review document was created.
