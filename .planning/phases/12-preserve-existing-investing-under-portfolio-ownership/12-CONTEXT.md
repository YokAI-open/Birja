# Phase 12: Preserve Existing Investing Under Portfolio Ownership — Context

**Recorded:** 2026-11-14
**Source:** Approved v1.2 requirements/roadmap and the owner's explicit instruction
to research, create the UI contract from the existing design system, then plan.
This compiles existing decisions; it is not a newly conducted discuss-phase.

## Phase Boundary

Preserve the existing investing journey in a first named portfolio while making
financial identity explicit across authentication consumers, trading, retries,
holdings, stock journals, dividends/splits/corrections, valuation and History.
Existing actual cash, stored baseline and immutable financial evidence survive
without a reset or additional grant. Primary requirements: PFUND-03, PFIN-02,
PFIN-03, PCTX-01, PVIEW-03, PSAFE-02 and PSAFE-03.

All financial writers/readers, SQL authority, grants and per-revision recovery
support must be coherent before multiple funded portfolios are enabled. This
phase remains a runnable preservation slice, not a separate database-only layer.

## Decisions

- Use the approved requirements and existing Birja design system; research
  technical approaches, create and verify the required UI contract, then write
  and check executable plans. The owner approved this sequence explicitly.
- Keep actual existing balances, stored starting cash, quantities/basis, fills,
  ownership/event lineage and retry identities intact in the first portfolio.
  Its initial label is “My portfolio.” Migration grants no new money.
- Bind every financial request and UI action to an explicit owned active
  portfolio. Show its name on the existing trading/confirmation/receipt,
  holdings and History surfaces; do not silently select an alternative target.
- Preserve existing crypto and stock execution, fees, freshness, eligibility,
  valuation/incomplete-value and private event-history behavior. Stock
  collection/execution admissions stay gated by the existing prerequisites.
- Authentication/session identity must work with zero, one or many financial
  portfolios in isolated fixtures; ordinary reads or sign-in cannot regrant
  money or recreate an intentionally empty portfolio set.
- Preserve restricted PostgreSQL roles, verified TLS, SQL ownership constraints,
  immutable economic evidence and exact-money rules. Do not broaden ordinary
  mutation privileges to make the transition pass.
- Qualify grants, revision-specific exact recovery and supported rollback or
  explicit refusal with each runnable schema transition; Phase 15 is not a
  reason to postpone those safety proofs.
- Future v1.2 lifecycle is already fixed: ten active portfolios, independent
  once-only $10,000 grants, terminal deletion including holdings or last
  portfolio, and freezing cash/holdings/financial History at deletion with no
  later dividends/splits/corrections (including earned unpaid effects), fake
  liquidation or transfers. The foundation must accommodate it coherently.
- Names/rename, creation/overview and optional descriptions (which may be empty)
  are Phase 13 user features. Delete/empty-state management is Phase 14. Do not
  expose unfinished management features in Phase 12; use isolated fixtures to
  prove future ownership/lifecycle states.
- Keep planning local on feature/milestone-v1.2. No push, merge, provider call,
  live verification, production inspection/change, dependency installation or
  implementation is authorized by this planning workflow.

## Agent Discretion

- Research the smallest coherent portfolio-root and immutable-association design
  against actual code; the milestone account-root recommendation is not a
  substitute for verifying every financial consumer and migration invariant.
- Select explicit API/route, cursor, retry and browser-state compatibility
  contracts that preserve the locked outcomes without guessing a portfolio.
- Design phased migration, lock ordering, SQL authority and exact recovery
  revisions using existing packages and isolated test infrastructure.
- Reuse accepted components, tokens, layouts and state patterns for portfolio
  identity labels and unavailable-target handling. Record all concrete UI
  choices in UI-SPEC.md rather than inventing a new visual design.
- Split executable plans into bounded tasks with concrete files, dependencies,
  verification, threat mitigations and human UI review; preserve the coordinated
  final delivery boundary and keep future management activation disabled.

## Deferred Ideas and External Gates

- Phase 7 STOCK-01/02/03, DATA-01, MKT-01 and SAFE-01 remain separately deferred
  and unverified. Do not rewrite their records, generate a false Plan 07-14
  completion summary or invoke its approved bounded manual campaign here.
- Historical charts, transfers, resets, cloning, configurable capital, shared
  portfolios, trash/restore UI and additional asset/provider features are outside
  this phase. Optional descriptions remain in Phase 13, not forgotten.
- Do not introduce new dependencies, activate live stock data, publish changes
  or deploy production under plan-phase authority.

## Canonical References

- /home/YokaiExchange/CLAUDE.md
- /home/YokaiExchange/AGENTS.md
- /home/YokaiExchange/.planning/PROJECT.md
- /home/YokaiExchange/.planning/REQUIREMENTS.md
- /home/YokaiExchange/.planning/ROADMAP.md — Phase 12 and continuing obligations
- /home/YokaiExchange/.planning/STATE.md
- /home/YokaiExchange/.planning/DEFERRED.md
- /home/YokaiExchange/.planning/research/v1.2/SUMMARY.md
- /home/YokaiExchange/.planning/research/v1.2/ARCHITECTURE.md
- /home/YokaiExchange/.planning/research/v1.2/PITFALLS.md
- /home/YokaiExchange/design-system/birja/MASTER.md
- /home/YokaiExchange/.planning/milestones/v1.1-RELEASE-RECEIPT.md
