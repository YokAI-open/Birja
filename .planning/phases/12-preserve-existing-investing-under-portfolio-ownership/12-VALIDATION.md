---
phase: 12
slug: preserve-existing-investing-under-portfolio-ownership
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-14
---

# Phase 12 — Validation Strategy

Planning contract only. No implementation tests or runtime campaigns were run
to create this document. Synchronize the per-task map with the generated plans
before independent plan checking; missing tests must have earlier Wave 0 owners.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Existing pytest 9.1.1/asyncio/coverage, Vitest and Playwright |
| Configuration | backend/pyproject.toml; backend/tests/conftest.py; frontend/package.json; existing browser/ops harnesses |
| Existing focused baseline | `cd backend && uv run pytest tests/test_accounts.py tests/test_stock_trading_service.py tests/test_event_history.py -q` |
| Frontend baseline | `cd frontend && npm run test -- --coverage` |
| Full backend gate | `cd backend && uv run pytest --cov=app --cov-branch --cov-fail-under=80`, then the exact critical 100% command in CLAUDE.md, extended to new critical modules |
| Browser gate | `python3 deploy/tests/run-stock-browser.py` after extending its synthetic owned stack for explicit portfolio targets |
| Operations starting points | `python3 deploy/tests/test-stock-recovery-contracts.py`; `python3 deploy/tests/test-ci-ops.py`; guarded real-PostgreSQL/restricted-TLS/recovery lanes |
| Runtime | Not measured by planning; focused feedback target 120 seconds, with longer complete security/recovery gates explicitly scheduled |

Use only owned disposable PostgreSQL/Redis/ops stacks. Existing test isolation
guards remain mandatory. No provider, production, dev financial data, installed
host tooling, private .env or credentials may be used. No dependency change is
required by this contract.

## Sampling Rate

- After each bounded task: run affected automated tests and static checks.
- After each integrated wave: run its complete affected financial/auth/API/UI
  domain plus relevant migration/authority contracts.
- Before phase verification: full backend/frontend/browser gates, exact critical
  coverage, strict dependency/image scans and fresh/upgraded restricted-TLS and
  current/retained recovery/rollback or explicit refusal proofs must pass.
- Do not run expensive full recovery campaigns after every metadata edit; bind
  complete proof to the final reviewed source and retained archive, recording
  any later source qualification explicitly.
- No watch flags. No three consecutive tasks without automated feedback.
- Focused feedback target: 120 seconds where practical, not a measured runtime
  guarantee; complete migrations/recovery/image campaigns are necessary exceptions.

## Per-Task Verification Map

Initial requirement-level map; planner must replace TBD task/plan/wave fields
with actual generated IDs, commands and threat references before checking.

| Requirement | Required assertion | Existing baseline | Missing focused proof / earlier owner required | Status |
|---|---|---|---|---|
| PFUND-03 | Exact populated 0014→final preservation, no grant/reset; bounded association and all original economics/keys/causes unchanged | accounts and dividend/stock migration tests | backend/tests/test_portfolio_migrations.py | Pending; Wave 0 |
| PFIN-02 | Explicit owned active target, unchanged crypto/stock rules, post-lock recheck, same-user sibling isolation | trading and stock trading wait/concurrency tests | backend/tests/test_portfolio_ownership.py | Pending; Wave 0 |
| PFIN-03 | Original active-root receipt and user-global key preserved; changed root conflicts without fill or leakage | stock trading concurrency and retry tests | portfolio ownership/retry extensions | Pending; Wave 0 |
| PCTX-01 | Matching visible name/target on tickets/previews/receipts/holdings/History; stale response cannot retarget | adjacent API/hooks/screens and browser suites | frontend/e2e/portfolio-ownership.spec.ts plus targeted hook tests | Pending; Wave 0 |
| PVIEW-03 | Every History kind/original/union arm/cursor bound to exact root and deterministic tie-breaker | event_history, event_history_cursor and history_api tests | backend/tests/test_portfolio_scoped_history.py | Pending; Wave 0 |
| PSAFE-02 | Identity-only auth with zero/one/many roots, no regrant/recreation, legacy refusal before OTP consumption | auth verify/session/account tests | explicit identity and financial route tests | Pending; Wave 0 |
| PSAFE-03 | Restricted roles/columns/definers/FKs, no residual migrator exception, intermediate refusal and final exact recovery/TLS | authority/schema and ops contracts | backend/tests/test_portfolio_authority.py; deploy/tests/test-portfolio-recovery-contracts.py | Pending; Wave 0 |

## Wave 0 Requirements

- Assign each missing proof above to an actual earlier test/fixture task; naming
  a nonexistent file is not passing verification.
- Seed original non-$10k cash/baselines, original fill JSON/keys, legacy split
  digests, same-time History and entitlement/correction lineage.
- Include one owner with two active portfolios holding the same asset, a foreign
  owner, zero portfolios and a closed stock+crypto portfolio. Closure is fixture
  setup here, not a public deletion feature.
- Add migration-only stage refusal and final runnable authority/grant/recovery
  inventories with real app/scheduler/migrator roles and verified TLS.
- Extend browser identity/auth fixtures and exact portfolio routes consistently.
- Framework installation: none; preserve lockfiles and runtime pins.

## Threat and Regression Obligations

Every PLAN.md requires its own threat model and mapped automated mitigations.
Include: BOLA/cross-root causes, wrong-root retry replay, association bypass,
legacy ambiguous targeting, closed-root worker mutations, stale browser state,
unsafe schema/restore/rollback admission, extra grants and widened role access.
Do not count a grep-only check as financial or concurrency proof.

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Test instructions |
|---|---|---|---|
| New portfolio-context UI acceptance | PCTX-01 | Owner acceptance of changed screens | Review synthetic screenshots/pages for label clarity and unavailable-target states; no account data or deployment |
| Genuine browser native 200% zoom | PCTX-01 | Emulated viewport/reflow is not native zoom evidence | Open synthetic review pages in desktop browser, select native 200%, verify readable/reachable controls and no obscuring overlap or page overflow |

Automate keyboard/focus, responsive reflow, late-response handling, private access
and target isolation as well. Manual acceptance never substitutes for those tests.

## Validation Sign-Off

- [ ] Exact per-task/plan/wave/threat map synchronized with all generated plans.
- [ ] Every task has automated verification or a concrete earlier Wave 0 owner.
- [ ] No three consecutive tasks lack automated feedback.
- [ ] All missing files are marked and mapped to creation tasks, not assumed present.
- [ ] No watch flags, fake passing reports, provider calls or production state.
- [ ] Focused latency targets and necessary long campaign exceptions are explicit.
- [ ] Independent plan checking approves sampling/coverage; only then set nyquist_compliant.

**Approval:** Pending planner synchronization and independent plan check.
**Execution:** Pending; wave_0_complete remains false until implemented evidence exists.
