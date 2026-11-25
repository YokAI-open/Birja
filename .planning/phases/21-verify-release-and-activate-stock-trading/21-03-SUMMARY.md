---
phase: 21-verify-release-and-activate-stock-trading
plan: "03"
subsystem: recovery
tags: [postgres, tls, restic, catalog, rollback]
requires:
  - phase: 21-01
    provides: Exact v7 archive, current image and seven-stage contract
  - phase: 21-02
    provides: Scoped catalog authority and volatile quote cache
provides:
  - Encrypted recovery of the populated 0023 predecessor and 0026 successor
  - Verified TLS authority parity across cold, upgraded and fresh 0026
  - Proved pre-write predecessor reversal and post-write successor recovery
affects: [21-04, 21-05, 21-07, 21-08]
tech-stack:
  added: []
  patterns: [fixed source and image binding, measured volume identity]
key-files:
  modified: [deploy/RUNBOOK.md, deploy/tests/run-portfolio-validation.py, deploy/tests/portfolio-smoke.py, deploy/tests/test-stock-catalog-finance-recovery.sh, deploy/tests/test-portfolio-recovery-contracts.py, deploy/tests/test-deploy-compatibility.sh, deploy/tests/test-rollback-db-security.sh]
requirements-addressed: [SV-02, SV-03]
requirements-completed: []
duration: 18 minutes
started: 2026-11-25T08:06:31Z
completed: 2026-11-25
tasks: 2
---

# Phase 21 Plan 03 summary

The isolated rehearsal encrypted a populated book from the exact 0023
predecessor, restored it to a distinct candidate and upgraded the candidate
to 0026. Historical cash, holdings, actions, receipts, closures and sequence
state matched. A fresh PostgreSQL server restored the exact 0026 books from
the installed v7 consumer and archived restic. The exact backend image
replayed catalog buys, sells, dividends, corrections and splits through
direct verified-TLS roles. A separate retained 0025 restore used its
authenticated historical sources.

| Task | Commit | Evidence |
|---|---|---|
| Wire live-shaped successor stages | `e618c2c` | Real owned cold, upgraded, fresh, current role and retained 0025 runs. Exact stock receipt replay and measured TLS authority agreement. |
| Prove both write boundaries | `3aac7d6` | The original 0023 volume and old image reopened before new writes with the same full projection. After actual 0026 writes, the same candidate volume and tested image reopened with stocks disabled, keeping exact receipts and original crypto available. The old image refused 0026 before loading its app, and populated downgrade refused. |

## Evidence

- Local archive SHA-256 `afd678d4199e4ec7eaaa8870a63238209acf81f477ee070b6e5ffb2631ae1ed6`.
  The exact baseline source is `07d3aa5c627b5ba550aa2d11baa13e2becaf3aa9`.
  The local 0026 application image was built from `522e171`. The task commits
  change only recovery tests and the runbook, leaving those backend bytes intact.
- The cold, upgraded, fresh and role runs measured the same 0026 catalogue
  `0c855fb80619ed1cd46183b87c3357a9183b3592d4504ebce8c722fb61085cc6`,
  runtime ACL `6995ecd9a65d5bf659480b524e37e236c31a293cb2ab9f1648ea657c15842994`,
  and defaults `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.
- The 19 recovery, 44 validation runner, 113 CI and 11 deployment evidence
  contracts passed. The deploy-compatibility tests checked the 0023/0026
  refusal and both supported revision cases. Rollback input, shell syntax,
  dry-run, diff and owned resource cleanup checks passed.

## Deviations and handoff

The workstation has Compose 5.0.0. Hosted qualification pins Compose 5.7.0
and Docker 29.2.1. The local preflight verified the disposable stack and
then failed to launch pytest through the worktree's partial venv under
`uv run --locked --no-sync`. The guarded successor rehearsals used the
existing installed Python environment and pinned Docker inputs. The full
serial graph and artifact receipt remain mandatory on the supported hosted
runner before merge or rollout.

The successor runner retains image transition, historical restores,
restricted-role checks, TLS controls and selected rollback in its full
graph. The cold, fresh and upgraded stages return measured 0026 authority
triples and the runner requires them to agree. Backups carry the exact
archive through recovery. Plan 04 can start integrated qualification using
these scoped outcomes.

## Self-Check: PASSED

Verified both task commits, expected files, stage outputs, authority parity
and absence of the owned database containers, volumes and network.
