---
phase: 03-prices
plan: 08
subsystem: infra
tags: [prod, compose, deploy, smoke, runbook, scheduler]
requires:
  - phase: 03-prices/07
    provides: scheduler loop, heartbeat healthcheck
provides:
  - prod scheduler service (docker-compose.prod.yml)
  - app_services helper in deploy.sh (deploy + rollback)
  - smoke checks 12 (scheduler, price freshness, prices 401)
  - RUNBOOK "Prices scheduler" section
affects: [03-09, 03-10]
key-files:
  modified:
    - docker-compose.prod.yml
    - deploy/deploy.sh
    - deploy/smoke-prod.sh
    - deploy/RUNBOOK.md
metrics:
  completed: 2026-10-28
---

# Phase 3 Plan 08: Production scheduler, deploy and smoke support Summary

Production now defines one hardened `scheduler` (ENV=prod, PRICE_SOURCE hardcoded kraken, no ports, data+app networks, no-new-privileges, log rotation, heartbeat healthcheck); deploy.sh builds/starts it after migrations (and removes it on rollback to older releases); smoke-prod.sh verifies it and price freshness. Nothing was deployed.

## Commits
- 14f8b5c feat(03-08): add prod scheduler service and deploy support
- bf8cc5d feat(03-08): add scheduler and price freshness smoke checks

## Verification (all offline)
- `docker compose -f docker-compose.prod.yml --env-file <dummy> config` valid; services: postgres, redis, backend, scheduler; JSON assertions passed (no ports, networks data+app, PRICE_SOURCE=kraken, ENV=prod, security_opt set). Dummy env deleted.
- `PRICE_SOURCE: "kraken"` count 1; no `PRICE_SOURCE: ${` in prod compose.
- deploy.sh: `app_services` used in build and start for both deploy and rollback (`--remove-orphans`); hotfix order kept (build/prepare, postgres+redis, migrate at line 251, start app services at 253, swap, nginx, health). `bash -n` ok; `deploy/tests/test-rollback-target.sh` 18/18 passed. on_err also tails 30 redacted scheduler lines.
- smoke-prod.sh: `bash -n` ok. PRICES_SQL against the test stack (migrated to head, then `down -v`): empty `15 0 -1`; after inserting one price with now() `15 1 0`; row removed, back to `15 0 -1`. (Inserted row used source `fake` for the first active coin, not specifically BTC.)
- shellcheck is not installed; not run.
- Production not touched: no deploy/smoke/install-nginx run, /srv/birja, /etc/birja, /var/www/birja untouched.

## Deviations from Plan
None, apart from the note above on the test price row. Smoke section numbered 12 and deploy record renumbered 13.

## Known Stubs
None.

## Self-Check: PASSED
