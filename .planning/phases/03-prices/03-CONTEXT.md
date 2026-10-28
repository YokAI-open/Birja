# Phase 3: Prices - Context

**Gathered:** 2026-10-28
**Status:** Ready for planning
**Source:** plan-phase questions (no discuss-phase run, no UI-SPEC)

<domain>
## Phase Boundary

Signed-in users see a markets page listing a curated set of about 15 cryptocurrencies with current USD prices. Each price shows how old it is and whether it is fresh, aging or stale. Prices refresh about every 60 seconds from Kraken's public Ticker, without the user reloading the page. Invalid prices are rejected and the last good one is kept. Requirements: PRICE-01 to PRICE-04.

Trading (Phase 4) consumes these prices later. This phase only shows them.

</domain>

<decisions>
## Implementation Decisions

### Coin list
- **D-01:** The list is the **top ~15 coins by market cap, excluding stablecoins**. Starting candidates: BTC, ETH, SOL, XRP, BNB, ADA, DOGE, TRX, AVAX, LINK, DOT, LTC, BCH, XLM, ATOM. The final list is pinned to coins that Kraken actually quotes against USD (research confirms each pair and its response key; for example, BNB may not be listed). If a candidate is unavailable, drop it or replace it with the next coin by market cap that is not a stablecoin. Keep the list as data (e.g. a seed migration or config), not hard-coded in the UI.

### Access
- **D-02:** The markets page is for **signed-in users only**. Signed-out visitors keep seeing the sign-in card. The prices API sits behind the existing `CurrentUserDep`.

### Freshness
- **D-03:** A price is **fresh under 2 minutes**, **aging from 2 to 5 minutes**, and **stale after 5 minutes**. Age is measured from the price's "as of" timestamp, meaning when the price was fetched or observed, not when the page loaded. The thresholds live in one place, shared by the backend and the UI or sent by the API, so Phase 4 can refuse trades on stale prices with the same definition. Per CLAUDE.md: "Staleness is visible".

### Spike rejection
- **D-04:** A new price that is **more than 25% away from the last good price** is rejected. The last good price stays and keeps aging toward stale. Zero, negative and non-numeric prices are always rejected (PRICE-04).
  - Claude's discretion: a confirmation rule, so that a genuine move of more than 25% is not rejected forever. For example, accept the new level after N consecutive polls agree within a small tolerance. Research proposes it; it must be tested.

### Decided after research (2026-10-28)
- **D-05:** **Store the mid price only.** Kraken's bid and ask are used to compute mid, then dropped. No bid/ask columns: trading uses a fixed simulated spread around mid (PROJECT.md), and CLAUDE.md forbids speculative columns.
- **D-06:** **Keep the MASTER.md display rule.** At $1 or more, show 2 decimals (XRP, DOT and ATOM show like `$1.04`). Below $1, show 4 significant digits. No MASTER.md change.
- **D-07:** **Production egress to Kraken is confirmed.** From the `birja-prod_app` network, `GET https://api.kraken.com/0/public/Ticker?pair=XXBTZUSD` returned HTTP 200 in 0.05 s.
- **Defaults accepted by the user** (proposed by RESEARCH):
  - Spike confirmation: N=3 consecutive polls within 5% of each other.
  - Kraken is polled every 60 s. The UI refetches every 30 s.
  - Routes: `/` is Markets and `/account` is Account. The health card moves to Account.
  - D-01 needs no substitutions: all 15 candidates, including BNB, are quoted in USD on Kraken.

### Claude's Discretion
- **Scheduler:** a single scheduler-loop container that polls Kraken about every 60 s. It runs exactly once regardless of how many backend workers there are, with no Celery or arq (PROJECT.md decision, CLAUDE.md "Background jobs").
- **Storage:** Postgres is the source of truth (the latest good price per coin, with its as-of time and source), and Redis is optional as a cache (CLAUDE.md "Data, caching"). History tables only if Phase 4 or 5 needs them; no speculative tables.
- **Retries:** backoff with jitter and Kraken's rate limits (CLAUDE.md "Retries and back pressure").
- **Money:** prices are `Decimal`/`NUMERIC(20,8)` and sent as JSON strings. They are formatted only in the UI (MASTER.md has the number-formatting rules, including sub-dollar prices with 4 significant digits).
- **Frontend:** react-router arrives now (deferred here by Phase 2 D-03), giving a markets route plus the existing account view. TanStack Query refetches about every 60 s.
- **Production:** the new scheduler container is added to `docker-compose.prod.yml` and covered by `deploy.sh` and the smoke checks. Deploying to birja.nist.one follows the Phase 02.1 runbook (release/hotfix flow); whether this phase ends with a release is decided at its push gate.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `CLAUDE.md`: Data, caching and background jobs (scheduler, staleness, retries, Redis); Money and numbers; API; Test culture (mock Kraken at the HTTP boundary with respx)
- `.planning/STATE.md`: open blocker "confirm the Kraken pair/response-key map and rate limit live when freezing the coin list"
- `.planning/phases/03-prices/03-RESEARCH.md`
- `design-system/birja/MASTER.md`: number formatting, gain/loss/warn tokens
- `deploy/RUNBOOK.md`, `docker-compose.prod.yml`, `deploy/deploy.sh`: the production stack the new scheduler joins

</canonical_refs>

<deferred>
## Deferred Ideas

- Price charts and history graphs: v2
- Stablecoins in the list: excluded (D-01)
- Public markets page: not now (D-02)
- UI-SPEC: skipped by the user

</deferred>

---

*Phase: 03-prices*
