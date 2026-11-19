---
phase: 14
slug: end-strategies-safely
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-19
---

# Phase 14 — Validation Strategy

Planning contract only. No Phase14 implementation, test result or human
acceptance is claimed. Planner must replace creation-owner labels below with
actual plan/task/wave IDs and threat references before plan checking.

## Test Infrastructure

Existing pytest/pytest-asyncio and isolated real PostgreSQL/Redis;
Vitest/React Testing Library and Playwright. Configuration remains
`backend/pyproject.toml`, `frontend/vite.config.ts`,
`frontend/playwright.config.ts`. No framework/dependency installation.

After each task use its bounded selector, source static checks and relevant
retained regressions. After each wave run affected integrations, not a repeat
of the hour-long final campaign. Before verification run complete:

```
python3 deploy/tests/run-portfolio-validation.py --suite all-security
python3 deploy/tests/run-portfolio-validation.py --suite recovery
```

These are final qualification commands, run sequentially at one frozen source.
Current runner requires planned successor adaptation before execution. Prior
actual Phase13 times were3373s security and2792s recovery; new scope may exceed
these. Routine target feedback aims under60s where feasible; real DB startup,
transactions/races and integration groups are measured latency exceptions.
Never substitute DB mocks or report an unmeasured short latency promise.

## Sampling and Resource Discipline

- Every task has automated verification or an explicit earlier test-creation
  dependency; never three consecutive tasks without automated feedback.
- All backend pytest (including nominal pure tests), DB operations, browser
  runners and recovery use one exclusive serial disposable lane. No dev/prod
  stack, secrets or provider calls. Frontend pure units/offline contracts can
  overlap only with explicitly disjoint files/resources.
- Use actual blocked-PID/lock barriers, not sleeps as evidence of concurrency.
  Historical migrations use separate databases and explicit revision targets;
  never downgrade a shared current database or blindly upgrade history to head.
- Before long campaigns run bounded current fixture/admission/compatibility
  diagnostics in the exact stripped child environment. PATH includes
  `/usr/sbin`; preflight existing Node24/uv/Python/restic/nginx and owned
  resources, authenticated immutable image IDs and archive/source bindings.
- Durable one-shot PID/start/log/status/exit receipts survive status questions;
  do not restart or assemble partial diagnostics into a whole-gate pass.
  A source repair requires fresh whole qualification.
- One new Phase14-specific exclusive archive path; preserve qualified
  `/tmp/birja-phase13-proof/recovery.tar.gz` and prior Phase12/13 archives.
  Recovery proves all seven stage families using the same pinned archive,
  successor current plus fixed0020/0017/older profiles, exact roles/TLS,
  source-destroyed independent oracles and safe rollback/refusal.
- Preserve all61 existing critical modules; include every new critical
  closure/authorization module at100%. Existing issue35 disposition is neither
  expanded nor remediated by this planning contract.

## Per-Task Verification Map

Proposed new files are MISSING until the named feature owner creates them.
Planner must allocate concrete IDs and ensure each command runs only after its
file and fixtures exist. Threat IDs below are planning placeholders, not audit
dispositions or passing evidence.

| Task/creation owner | Requirement | Threat / secure behavior | Test type | Automated command after creation | File exists / status |
|---|---|---|---|---|---|
| Closure authority/API | PMGT-03 | T-API: owner+CSRF, exact named intent, minimal replay, no retarget | real API | `cd backend && uv run pytest tests/test_portfolio_closure_api.py -k 'repeat or confirmation' -x` | MISSING / pending |
| Financial terminal boundary | PMGT-04 | T-FREEZE: immutable before/after oracle, unpaid/future effects excluded, no financial History append | real DB/jobs | `cd backend && uv run pytest tests/test_portfolio_closure_events.py -k 'unpaid or negative' -x` | MISSING / pending |
| Zero/replacement identity | PMGT-05 | T-IDENTITY: reads/login never grant, new ID only on explicit create | real API | `cd backend && uv run pytest tests/test_portfolio_closure_identity.py -k 'last or replacement' -x` | MISSING / pending |
| Stock continuity | PFIN-05 | T-STOCK: all historical instruments incl sold-out, global tails/units and sibling continuity | real DB | `cd backend && uv run pytest tests/test_portfolio_closure_stocks.py -k 'sold_out or successive' -x` | MISSING / pending |
| Commit/clock/management races | PFIN-06 | T-RACE: sorted gates before account, first-buy rediscovery, no grant/cap/effect duplication | real concurrency | `cd backend && uv run pytest tests/test_portfolio_closure_races.py -k 'first_buy or management' -x` | MISSING / pending |
| Privacy/final response fence | PSAFE-01 | T-PRIVACY: all normal reads/replays/cursors/originals reject closed/foreign; restricted TLS | real API/DB | `cd backend && uv run pytest tests/test_portfolio_closure_privacy.py -k 'cursor or original' -x` | MISSING / pending |
| Browser deletion/target lifetime | PCTX-03, PMGT-03/05, PSAFE-01 | T-UI: before-send persistence, same-ID unknown recovery, late/session/cross-tab privacy | unit | `cd frontend && npm run test -- src/hooks/usePortfolioDeletion.test.tsx src/components/PortfolioDeleteForm.test.tsx` | MISSING / pending |
| Full-stack deletion journeys | All seven | T-E2E: public DELETE, siblings, stale routes, replacement and zero-book state | real browser | `python3 deploy/tests/run-stock-browser.py` after runner includes `frontend/e2e/portfolio-deletion.spec.ts` | runner exists; new spec MISSING / pending |
| Recovery contracts | PMGT-04, PFIN-05/06, PSAFE-01 | T-RECOVERY: complete immutable lifecycle evidence, exact authority, no downgrade loss | offline+real restore | `python3 deploy/tests/test-portfolio-recovery-contracts.py` and `python3 deploy/tests/test-portfolio-validation-contracts.py`, then whole recovery above | files exist; successor cases pending |

## Wave 0 Requirements and Creation Dependencies

- [ ] Lifecycle schema/authority plan creates the independent frozen-finance
  oracle, multi-instrument/sold-out/clock fixtures and migration/SQL negatives.
  Lock exact lifecycle/stock interfaces before API/jobs consume them.
- [ ] API owner creates confirmation/status schemas and strict endpoint tests
  before frontend transport consumers; dedicated DELETE body parser, no PATCH
  validation flag workaround.
- [ ] Job/race owners create real before/after closure, unpaid/held correction,
  two-owner/sibling, first-buy and equal/backward-clock tests without weakening
  the existing one-instrument financial guard.
- [ ] UI owners create the hook/component tests named above and real e2e spec;
  existing suites are extended for owner/session, receipts, cursors and stale
  financial target boundaries. No command references an uncreated test owner.
- [ ] Recovery owner supplies successor inventories, immutable qualified0020
  source9527e35, complete0017source4b4320b and earlier profiles; explicit
  closed-fixture provenance, quarantine/ACL/catalogue parity, final runner
  preflight/image/archive and durable receipt contracts before long campaigns.

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Instructions |
|---|---|---|---|
| New deletion UI acceptance | PMGT-03/04/05, PCTX-03 | Owner assessment of actual reviewed screens | Download source-bound synthetic review packet; inspect named effects/Cancel, pending/unknown/recovery, rename refusal, stale/private boundary and empty/Create. Record actual answer. |
| Genuine native200% zoom | PCTX-03, PSAFE-01 | Viewport emulation is not native browser zoom | In desktop browser menu select200%; new screens remain readable/reachable without overlap or horizontal page scroll. Record actual owner outcome separately. |

## Validation Sign-Off

- [ ] Concrete task/wave/threat map filled and every task automated or dependent
- [ ] No three consecutive tasks without meaningful automated feedback
- [ ] All MISSING tests have explicit earlier creation owners
- [ ] No watch-mode flags, provider calls or production operations
- [ ] Bounded feedback measured; long exceptions and resource ownership recorded
- [ ] Independent security/code/UI review and whole final qualification pass
- [ ] New owner UI and native200 outcomes actually recorded
- [ ] `nyquist_compliant: true` set only after actual validation

**Approval:** Pending execution; this draft does not complete any requirement.
