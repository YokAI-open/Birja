---
phase: 24
slug: compare-portfolio-performance
status: in_progress
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-26
---

# Phase 24 — Validation strategy

Use the locked Python and Node environments, the isolated test PostgreSQL and
Redis, Vitest, the guarded Playwright runner and the existing encrypted
recovery harness. Add focused tests with the plan that implements their
behavior. The infrastructure requires no Wave 0 installation.

## Coverage

| Requirement | Evidence to collect |
|---|---|
| TREND-01 | Overview component and browser tests for the fully clickable cards, optional descriptions, figures, final creation card, empty and capped states, and supported create, edit, switch and remove flows. |
| TREND-02 | Strict private trend read and client tests for exact IDs and decimals, UTC day spacing, missing and incomplete rows, an accessible summary and current data through empty or failed history. Check cache behavior after a session or active portfolio set changes. |
| TREND-03 | Real PostgreSQL tests comparing observations to the existing exact statement, first-write uniqueness, capture window, retries and restart, terminal close ordering, owner and role boundaries, and populated migration from 0027. The successor recovery lane must restore exact complete, incomplete and retained terminal observations from one encrypted archive. |
| TREND-04 | Selected portfolio component and browser checks for chooser and management order, update age, exact value, profit and allocation, stock and crypto filters, stable sorting by value, ticker and percentage return, missing values and scoped trade links. |

## Per-task verification map

The matching `PLAN.md` task contains the complete runnable command. Tests
marked new are authored before their task's verification. Existing tests
retain their substantive assertions when updated for the new behavior.

| Task | Wave | Requirements | Planned automated evidence |
|---|---:|---|---|
| 24-01-01 | 1 | TREND-03 | New `test_portfolio_daily_schema.py -k isolated_schema` in a test-owned PostgreSQL database. Verify schema, complete/null rows, ownership, constrained grants and downgrade. |
| 24-01-02 | 1 | TREND-03 | New `test_portfolio_daily_schema.py -k current_admission` checks actual roles, fresh and populated admissions and separate predecessor path. |
| 24-02-01 | 1 | TREND-04 | `App`, `PortfolioPage`, `PortfolioTargetBoundary` and `PortfolioSwitcher` tests confirm actual detail route toolbar and tab order, live refresh, focus and unaffected trade/History wrappers. |
| 24-02-02 | 1 | TREND-04 | `PortfolioPage`, `PortfolioDeletionPage`, `PortfolioDeleteForm`, `PortfolioSwitcher` tests, lint and types for allocation, exact sorting, management and scoped links. |
| 24-03-01 | 2 | TREND-03 | Guarded daily schema, migration, developer bootstrap, role and current or retained admission replays listed in Plan 03. |
| 24-03-02 | 2 | TREND-03 | Existing guarded exact closure, authority, durable dividends, split and lifecycle tests on the qualified 0028 head. |
| 24-04-01 | 3 | TREND-03 | New `test_portfolio_daily_capture.py -k 'not scheduler_cycle'` and current `test_portfolio_snapshot.py` cover exact valuations, starting cash, applicable current-mark restrictions and both closure race orders. |
| 24-04-02 | 3 | TREND-03 | New `test_portfolio_daily_capture.py` and extended `test_scheduler_loop.py` cover disabled, admitted and predecessor initialization, boundaries, restart and failure fairness. |
| 24-04-03 | 3 | TREND-02, TREND-03 | New `test_portfolio_daily_api.py`, current `test_portfolio_overview.py` and `test_portfolio_authority.py` check independent no-store, schema admission, ownership and exact results. |
| 24-05-01 | 4 | TREND-02 | New decoder and `usePortfolioValueHistory` tests for exact dates, money and IDs, bounded reads, retries and session/closure fencing. Re-run existing overview hook tests. |
| 24-05-02 | 4 | TREND-01, TREND-02 | New sparkline tests and `PortfoliosPage.test.tsx` for dates, gaps, equivalent summaries, card links, cap and independent current data. |
| 24-06-01 | 4 | TREND-03 | Stock and portfolio recovery contracts verify the extended exact archive, manifest and retained-role dispatch. |
| 24-06-02 | 4 | TREND-03 | New 0028 and capture-before-close cases in recovery contracts and `bash -n` validate the implemented campaign before its guarded execution. |
| 24-07-01 | 5 | TREND-03 | Deployment compatibility assertions and rollback script syntax check exact successor and retained pre-write inputs. |
| 24-07-02 | 5 | TREND-03 | `test-ci-ops.py` verifies the existing CI graph and exact measured successor proof selection and artifact staging. |
| 24-08-01 | 6 | TREND-01, TREND-02, TREND-04 | New Phase 24 and retained scenarios discovered by the exact `portfolios` Playwright filter. Source-bound app/ZIP geometry, actual tab order and four paired captures. |
| 24-08-02 | 6 | TREND-01, TREND-02, TREND-03, TREND-04 | Run Phase 24 `recovery-successor` preflight, actual serial proof and receipt verifier. Collect backend branch coverage at the existing 80% overall gate, report exact touched critical modules at 100%, and run frontend lint/types/Vitest/build. |

## Sampling and final verification

Run the planned focused command after each task. Wider rechecks at integration
cover touched existing critical files, financial and lifecycle regressions,
frontend lint, type checking, Vitest and the production build. Record exact
commands, commits, actionable findings and observed outcomes. The unchanged
release CI checks remain required before merge. Plan 24-08 contains the
complete coverage collection and the explicit critical-module report command.

Before the browser run, discover the exact named tests using the phase filter.
Exercise current valuation and ordinary portfolio actions on the guarded
application stack. Use deterministic price and financial fixtures. Compare
the overview and selected portfolio with the approved ZIP at equal desktop
and phone viewports. Include current-only and incomplete cases. Check target
placement, keyboard focus, 320px reflow and enlarged text. Bind each capture
to runtime source and fixture hashes. Record native zoom only if actually
tested with that browser control.

Recovery evidence includes actual stored values and gaps, authority after
restore, reviewed grants and identities, retained 0027 compatibility, and the
same candidate source for backup and verification. Restoring synthetic rows
in isolation verifies the recovery path. Release-source and any applicable
live current-mark conditions are tracked with the release acceptance.

Phase 23's live historical bars are independent of this proof.

The independent plan check passed the revised eight plans and 17 tasks on
2026-11-26. All four TREND requirements and five decisions have planned
evidence. The check confirmed the dependency order, parallel file ownership,
schema admission, actual toolbar and keyboard order, and the single final
encrypted recovery campaign.

## Measured integration evidence

| Requirement | Verified evidence |
|---|---|
| TREND-01 | Real browser cards open independent portfolios. The final creation card works, including the empty state and the ten-active-portfolio limit. The existing lifecycle and interrupted creation journeys passed. |
| TREND-02 | The real owner route supplied separate 30-day histories. Chromium verified missing days, incomplete data, one observation, and a recoverable history error with current figures and navigation available throughout. |
| TREND-03 | The guarded schema, capture and owner API checks passed. The authenticated seven-stage 0028 recovery restored exact rows and identities and verified owner reads and rollback. [Recovery receipt](24-RECOVERY-RECEIPT.md) |
| TREND-04 | Chromium verified toolbar and keyboard order, refresh age, allocation, distinct positions, percentage-return sorting, incomplete valuation and scoped trade links. |

All eight focused Chromium cases passed on the browser source `741c337`.
Frontend lint, TypeScript, all 1,424 Vitest cases and the production build
passed on the same runtime inputs. Vite reported its bundle-size warning.
The app and approved ZIP were compared at 1440 × 1000 and 390 × 1000, with
320px reflow and enlarged-text browser checks.

The recovery preflight passed 148 checks. The serial proof and exact receipt
verifier both passed on `74e852d`. The measured proof inputs remained identical
through `741c337`. This includes backend, deploy tooling, Compose, workflow,
the frontend Dockerfile and package lock. The intervening runtime change is
one CSS declaration. The local serial time was 56m 19s with concurrent
backend testing. Hosted CI timing remains to be measured against 45 minutes.

The full guarded backend coverage collection is in progress. Ruff checks and
format verification passed across 344 files. Mypy passed for 149 app files.
