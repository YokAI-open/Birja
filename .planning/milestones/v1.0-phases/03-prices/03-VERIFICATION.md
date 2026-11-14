---
phase: 03-prices
verified: 2026-10-28T11:07:00Z
status: passed
score: 4/4 must-haves verified
---

# Phase 3: Prices Verification Report

**Goal:** Users can see current prices for a curated coin list, always with how old each price is.
**Status:** passed (no human items open; the visual check was approved by the user in 03-09 T2).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Markets page lists ~10-20 coins with USD prices | VERIFIED | MarketsPage.tsx renders a table from GET /api/v1/prices (services/prices.list_prices, Coin join Price). Prod smoke: all 15 active coins priced. |
| 2 | Each price shows as-of age and fresh/aging/stale badge | VERIFIED | API returns age_seconds, status and thresholds; frontend freshnessStatus + FreshnessBadge, age ticks locally via useNow(1000). |
| 3 | ~60 s refresh without reload, single scheduler | VERIFIED | usePrices refetchInterval 30 s; scheduler service in docker-compose.yml is a separate container with Redis NX/PX lock plus whole-cycle timeout (40 s) under the lock TTL (45 s) and heartbeat healthcheck. Prod logs show `price cycle: status=ok accepted=15 rejected=0` at 11:04:29 and 11:05:29 (60 s apart). Smoke confirms exactly one healthy scheduler. |
| 4 | Invalid/spiking price rejected, last good kept, age grows to stale | VERIFIED | price_rules.py rejects non-finite/<=0/bid>ask/overflow and moves >25% unless 3 polls confirm within 5%. Rejected coins are skipped and not upserted, so as_of is untouched; upsert only advances as_of. Frontend keeps last data on refetch failure. |

## Requirements
| ID | Status |
|----|--------|
| PRICE-01 | SATISFIED |
| PRICE-02 | SATISFIED |
| PRICE-03 | SATISFIED |
| PRICE-04 | SATISFIED |

No orphaned requirements. REQUIREMENTS.md still shows these as Pending/unchecked and must be ticked at closeout.

## Behavioral checks (read-only, prod)
- smoke-prod.sh: SMOKE OK (36 checks); --public: SMOKE OK (7 checks), /prices 401 signed out.
- docker compose -p birja-prod ps: backend, postgres, redis, scheduler all healthy, one scheduler.

## Anti-patterns
No TBD/FIXME/XXX markers found in backend/app, frontend/src, deploy. Review CR-01 and WR-01..07 are fixed in code (per-coin try/except, MAX_MID guard, no txn across fetch, cycle timeout, cancel on shutdown, SchedulerSettings without secrets, last data kept).

## Notes (non-blocking)
- Working tree HEAD beb8d17 differs from origin/main 9ddea52; the code matches the v0.2.2 content described.
- Frontend polls at 30 s, the scheduler at 60 s, so prices land within about 90 s worst case. This is consistent with "about every 60 seconds".
- 03-09/03-10 SUMMARY files are missing by design until closeout.
- Candidate (spike-confirm) state is in memory only; a restart resets it. This is documented and acceptable.
