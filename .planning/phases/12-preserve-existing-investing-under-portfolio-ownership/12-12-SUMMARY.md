---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "12"
subsystem: accounting
tags: [portfolio, stock-journal, splits, immutable-evidence, concurrency, terminal-state]
requires:
  - phase: 12-07
    provides: final0017 paired causes, global digest marker and terminal records
  - phase: 12-08
    provides: explicit owned root identity
provides:
  - Portfolio-keyed complete stock journal reconstruction and terminal cutoff validation
  - Persisted legacy NULL/user and new2/portfolio digest interpretation without rewriting old evidence
  - Once-only global splits with independent active-root effects and frozen siblings
  - Narrow scheduler-only instrument-first root-lock authority without account UPDATE grants
affects: [12-11, 12-13, 12-16, 12-17, 12-18, 12-27]
tech-stack:
  added: []
  patterns: [versioned digest reader, terminal journal boundary, instrument-first lock-only definer]
key-files:
  created:
    - backend/tests/test_portfolio_stock_ownership.py
    - backend/tests/test_portfolio_splits.py
  modified:
    - backend/app/services/stock_ownership.py
    - backend/app/services/corporate_actions.py
    - backend/alembic/versions/0017_portfolio_ownership.py
    - backend/tests/test_migrations.py
    - backend/tests/test_portfolio_migrations.py
key-decisions:
  - Global sequence and application identity stay instrument-wide; ownership totals and split movement uniqueness use portfolio_id
  - Legacy NULL dispatches original user tuples and integer split-result formatting; explicit2 uses fixed-eight-decimal owned tuples
  - Validate every frozen journal against exact closure time, tail and epoch instead of excluding closed records from integrity checks
  - Scheduler locks roots through a fixed-path lock-only definer, not account UPDATE permission
requirements-completed: []
requirements-addressed: [PFUND-03, PFIN-02, PSAFE-03]
duration: 20 min
completed: 2026-11-16
---

# Phase 12 Plan 12: Root-Specific Stock Journals and Terminal Split Reconstruction

**Portfolio-keyed journals retain legacy global split bytes while active sibling strategies split independently and terminal portfolios remain exact.**

## Accomplishments

- StockMovementInput requires an explicit portfolio_id; omitted, foreign or
  closed roots fail before replay. Fill causes match portfolio/user/coin; global
  application causes remain global with one movement per eligible root. New
  holdings include their exact root. Sequence allocation remains instrument-wide.
- Complete reconstruction indexes quantities/basis by portfolio, not user. It
  validates paired causes, all departed/zero owners, global sequence and units,
  actual holdings, and each immutable terminal record. Missing/contradictory,
  future or too-early closure boundaries fail closed; frozen rows cannot advance
  past their closing sequence/epoch/time or disappear from integrity checks.
- Persisted StockSplitApplication.owner_digest_version selects the reader after
  reload. NULL uses original sorted user/quantity/basis tuples, including the
  old integer formatting of split results; explicit2 uses sorted
  (portfolio_id,user_id,coin_id,quantity,basis,last_sequence,unit_epoch), with
  fixed-eight-decimal monetary strings. Unknown versions fail closed. Original
  event IDs, application IDs and before/after digest bytes are never rewritten.
- Split application locks the instrument, then affected roots in ascending ID,
  then holdings. Active roots alone receive effects, but full validation still
  checks frozen siblings at their terminal epoch. One global application is
  inserted with explicit2 and retained global cause keys; same-owner portfolios
  no longer collide in split arithmetic or movement lookup.
- A genuine two-user0014 global split migrates to0017 with unchanged NULL/digest
  evidence. The same fixture adds a later same-owner sibling and freezes the
  other original owner, then two independent restricted scheduler transactions
  race to apply one new global2 split. Both return the same application set;
  exactly the two active roots receive effects. Additional checks cover two
  later epochs, reverse/cancelled holds and injected partial-effect rollback.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| 12-12-01 | 08225c1 | Owned complete journals, terminal validation and actual legacy digest migration/reload |
| 12-12-02 | 713915f | Root-aware split writer, independent scheduler race, freeze/rollback proofs and narrow lock authority |

## Verification

Existing locked environment only (uv run --no-sync, temporary UV cache).
All databases are guarded disposable birja_test; no provider, production,
installation, live admission or publication operation occurred.

| Check | Result |
|---|---|
| Plan12 journal/closure/digest and split suites, final source | 29 passed in15.07s |
| Actual retained0007–0014→0017 preservation plus final inventory | 9 passed in55.49s |
| Four restricted ownership/authority families test_final_sql_* | 66 passed in4.84s |
| Focused mypy, stock_ownership.py and corporate_actions.py | PASS, two source files |
| Ruff check/format, seven touched files | PASS |
| git diff --check | PASS |

Initial failures exposed two synthetic source mistakes (the reused split helper
defaults to4:1; same-date distinct source IDs correctly trigger alias uncertainty)
and an expired ORM identity in the concurrency fixture. Corrected the fixtures,
preserving the source uncertainty policy. Actual scheduler execution exposed the
permission defect below; it is fixed and tested rather than masked by admin-only
success. No skipped/xfail/manual-schema substitute is used.

## Deviations from Plan

**[Rules2/3 — Necessary restricted scheduler lock authority]** Actual scheduler
split execution failed42501 when SELECT accounts FOR UPDATE required UPDATE
permission. Retaining no scheduler account/cash UPDATE and deterministic root
serialization requires the narrow private
public.lock_stock_portfolio_roots(bigint) RETURNS void helper in unmerged0017.
The orchestrator confirmed this local correctness repair within approved scope.
It validates an existing stock, obtains the identical instrument advisory gate,
then locks affected account roots in ascending ID. It takes no owner/cash
argument and performs no economic mutation. SECURITY DEFINER owner is exactly
birja_migrator; search_path=pg_catalog,public,pg_temp; PUBLIC EXECUTE revoked;
only birja_scheduler receives EXECUTE. App calls and invalid instruments are
denied; scheduler cash UPDATE remains denied. The fixed migrator inventory and
final helper owner/path/ACL assertions include it. No merged migration or SQL
companion bytes were edited and no broad grant was added.

## Threat Flags

| Flag | File | Description |
|---|---|---|
| threat_flag: lock_definer | backend/alembic/versions/0017_portfolio_ownership.py | Lock-only scheduler definer; exact function body, owner, fixed search_path, scheduler-only EXECUTE and no account UPDATE must enter16/17 bootstrap/recovery inventories and27 qualification |

## Known Stubs

None in this plan's journal/split path. Remaining consumers are explicit
cross-plan obligations, not final financial integration claims.

## Carry Forward

- Plan11 must supply portfolio_id on every StockMovementInput and scope stock
  retry causes. No user-only root fallback is retained.
- Plan13 must call reconstruct_stock_quantity with portfolio_id, not user_id,
  and scope entitlement supersession/payments/corrections accordingly. Current
  dividend derivation is deliberately still its later plan's ownership.
- Plans16/17 must authenticate lock_stock_portfolio_roots(bigint), its exact
  migration-owned body/config/ACL, and the existing trigger helper in role and
  recovery inventories. Current0017 includes the lock-only routine; retained
  sources remain byte-identical. SQL companion checksums are unchanged.
- Prior retained ownership/action fixtures and callers use old user-only
  arguments and omit required root columns; full regression adaptation belongs
  to their domain plans/Plan27. No whole-suite success is claimed here.
- Verified TLS/cold recovery, complete service/browser integration, coverage,
  strict dependency/image gates and both owner UI checkpoints remain pending.
  All milestone requirements remain unchecked. Phase7 live work remains
  separately deferred and admissions disabled; no phase completion claimed.

## Self-Check: PASSED

Both task commits exist; all seven created/modified files exist, assigned
focused suites pass, and no unexpected deletion occurred. Unrelated .claude/
remains untouched. Changes are local on feature/milestone-v1.2.
