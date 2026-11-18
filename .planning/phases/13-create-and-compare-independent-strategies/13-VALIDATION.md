---
phase: 13
slug: create-and-compare-independent-strategies
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-18
---

# Phase 13 — Validation Strategy

Planning contract only; no Phase13 implementation/test pass or framework installation is claimed.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Existing pytest9.1.1/pytest-asyncio, Vitest5.0.5 and Playwright1.64.1 |
| Config | backend/pyproject.toml; frontend/vite.config.ts; frontend/playwright.config.ts |
| Quick existing baseline | cd backend && uv run pytest tests/test_portfolio_identity.py -x (owned isolated stack required even for metadata pytest) |
| Full local qualification | python3 deploy/tests/run-portfolio-validation.py --suite all-security; then --suite recovery |
| Source baseline | Phase12 tested4b4320b; complete security1479.850s and fresh7stage recovery2694.692s are historical qualification, not Phase13 results |
| Execution isolation | All backend/DB-touching ops suites strictly serial; stripped synthetic env/fake prices/console mail; no .env, production or provider calls |

## Sampling Rate

- Per task: smallest meaningful new or affected backend/frontend/API test group from its plan.
- Per wave: affected integration plus schema/role/recovery admission checks; no three implementation tasks without automated verification.
- Before phase verification: actual complete security, current/retained exact same-archive encrypted recovery, independent code/security/UI reviews and implemented new UI/desktop-native200% owner checks.
- Target feedback latency:60seconds for selected groups; actual DB migration/concurrency, full coverage/browser/image/recovery are explicit longer proof exceptions. Measure selectors, do not invent short runtimes.
- Keep original80% overall and100% critical gates. Add actual new money/grant/authz/normalization/overview modules to the critical command instead of preserving only the prior60-module list.

## Initial Requirement Verification Map

Planner must replace group placeholders with its final plan/task/wave IDs while retaining every row and executable creation dependencies.

| Requirement | Proposed new/affected verification | Secure behavior | Planned command | Exists now |
|---|---|---|---|---|
| PMGT-01 | test_portfolio_creation.py | Serialized active cap10, private ownership, closed slot/name reuse and new identity | cd backend && uv run pytest tests/test_portfolio_creation.py -x | New alongside feature |
| PMGT-02 | test_portfolio_metadata.py | SQL-authoritative Unicode normalization/owner uniqueness, rename/create races, unchanged money | cd backend && uv run pytest tests/test_portfolio_metadata.py -x | New alongside feature |
| PMGT-06 | metadata tests; usePortfolioManagement.test.tsx | Empty/default/view/edit/clear description, strict controls/length, no financial mutation | cd frontend && npm run test -- src/hooks/usePortfolioManagement.test.tsx | New alongside feature |
| PFUND-01 | test_portfolio_funding.py; retained identity tests | Fixed10000grant/baseline once; genuine new onboarding; no legacy/zero-book regrant | cd backend && uv run pytest tests/test_portfolio_funding.py tests/test_portfolio_identity.py -x | New plus existing |
| PFUND-02 | creation tests | Permanent original owner/key/payload identity; lost response/rename/cap/closed replay safety | cd backend && uv run pytest tests/test_portfolio_creation.py -x | New |
| PFIN-01 | test_portfolio_strategy_lifecycle.py | API-created siblings trade same assets with isolated money/quantity/basis and cross-asset races | cd backend && uv run pytest tests/test_portfolio_strategy_lifecycle.py -x | New |
| PFIN-04 | strategy lifecycle plus dividend/entitlement/split tests | Correct per-book historical ownership, once-only credits/corrections and active split effects | cd backend && uv run pytest tests/test_portfolio_strategy_lifecycle.py tests/test_portfolio_dividends.py tests/test_portfolio_entitlements.py tests/test_portfolio_splits.py -x | New plus existing; serial |
| PCTX-02 | management/target hooks; portfolio-strategies.spec.ts | Switch/pending create/unknown original/cursor/late callback/logout/cross-tab rename isolation | cd frontend && npm run test -- src/hooks/usePortfolioManagement.test.tsx src/hooks/usePortfolioTarget.test.tsx | New plus existing |
| PVIEW-01 | test_portfolio_overview.py | Stable0/1/10 active owner-only books, original baseline, no pooled total | cd backend && uv run pytest tests/test_portfolio_overview.py -x | New |
| PVIEW-02 | overview and valuation tests | Same marks/time/math as detail; per-book incomplete isolation, shared bounded query plan | cd backend && uv run pytest tests/test_portfolio_overview.py tests/test_portfolio_valuation.py -x | New plus existing |
| PSAFE-07 | creation/overview resource tests; capacity/polling contracts | Key/body/quota/query bounds, one market poll, existing capacity/stock-admission guards | cd backend && uv run pytest tests/test_portfolio_creation.py tests/test_portfolio_overview.py -x | New plus retained deploy contracts |

## Wave 0 / Feature Test Creation Dependencies

- Existing test frameworks and isolated infrastructure remain; no package installation recommended.
- Create meaningful grant/creation/metadata/overview/strategy-lifecycle test files with the owning feature before implementation assertions can pass.
- Add strict frontend API, management/target hooks, pages and actual browser journeys with their implementation owners.
- Shared DB fixtures/test harness/critical list/recovery profiles must have explicit single ownership and sequencing.
- New revision0018+ schema/SQL grants, immutable create/grant journal and initialization latch require fresh/populated/zero-book migration, restricted-role forged amount/baseline/directINSERT/metadata/journal/privateEXECUTE refusals and exact recovery.
- Preserve immutable Phase12 migrations, catalogue/profile fingerprints and actual0017 archive. New current/retained recovery source inventory must be extended, not silently repinned.
- Include negative source/authority/profile mutations, immutable replay and capacity refusal checks before full campaigns.

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Instructions after implementation |
|---|---|---|---|
| New overview/create/edit/switch visual behavior | PMGT-01/02/06; PVIEW-01/02; PCTX-02 | Owner product acceptance | Review actual new screens/states from source-bound packet; planning UI-SPEC approval is not human UAT |
| Native browser200% zoom | Same UI scope | Automation does not prove desktop browser native zoom | Owner checks actual browser zoom with readable/reachable controls, no overlap or horizontal page overflow |

## Accepted and Deferred Boundaries

Issue35 picomatch exception remains exact/hash/path/expiry bound through2026-12-17UTC; full raw audits and unrelated HIGH/critical blockers remain. Approved Python image pins stay unchanged. No dependency refresh or new waiver in planning. Phase7 six live requirements and consumed campaign stay separate; no provider calls/activation. Public deletion belongs to Phase14 and full lifecycle acceptance to15, but new-revision safety/recovery is required now.

## Validation Sign-Off

- [ ] Final task IDs/waves/threat IDs mapped by planner
- [ ] Every implementation task has automated verification and created-test dependency
- [ ] No three consecutive implementation tasks lack feedback
- [ ] All missing files have concrete creation owners
- [ ] No watch commands or invented test pass
- [ ] Critical100/full security/current-retained recovery/reviews/UI-native200 gates retained

Approval: pending plan check. Wave0 remains incomplete until execution supplies actual tests; final Nyquist status reflects checked sampling coverage, not test execution.
