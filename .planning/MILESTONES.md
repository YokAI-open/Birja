# Project Milestones: Birja

## v1.0 Birja MVP (Shipped: 2026-11-10)

**Delivered:** A public crypto investment simulator for friends, with virtual
money, real recent prices, exact trading, portfolio/history and recoverable data.

**Software release:** v0.4.0 at 46d24c8591de2207cf219429aac0768962bed4c3.
The v1.0 label identifies the completed planning milestone, not a new software
release or deployment.

**Phases completed:** 1–6 including inserted 2.1: 7 phases, 69 plans, 163 declared
tasks (counted from plan task elements; the helper's sparse summary count was 29).

**Key accomplishments:**

- One-command local stack and required lint/type/test/image/browser/operations CI.
- Email OTP sign-in, persistent revocable sessions and exactly-once $10,000 accounts.
- Fifteen curated Kraken crypto prices with automatic refresh and visible age.
- Exact atomic market buy/sell, itemized previews, stale-price refusal and idempotent fills.
- Mid-price portfolio performance/allocation and stored paginated trade history.
- Public HTTPS v0.4.0 with Gmail/Outlook acceptance, restricted DB TLS roles and proven encrypted off-server recovery.

**Stats:** 1,066 changed tracked paths from initial repository commit to final
closeout merge; 500 reachable commits through that merge; 21 calendar days
(2026-10-20 → 2026-11-10). Tracked source line counts across backend/app,
frontend/src, deploy and scripts: Python 12,559,
TypeScript/TSX 6,850, shell 3,306.
These scoped counts include tests/helpers where present and exclude dependencies.

**Git range:** `c2a8e39a678a13a15afd39f24a370ea7f35d13a9` → `0f823612db53b9ae4c959b2d0609da083efced61`.

**Audit:** 31/31 requirements, 7/7 phases, 20/20 integration contracts and 12/12
flows; no blockers. Owner explicitly accepted follow-up debt on 2026-11-10:
W01–W08, four early validation-record gaps, and retained historical accepted-risk
caveats described in the [archived audit](milestones/v1.0-MILESTONE-AUDIT.md).
No finding is silently marked resolved.

**Archives:** [roadmap](milestones/v1.0-ROADMAP.md),
[requirements](milestones/v1.0-REQUIREMENTS.md),
[integration review](milestones/v1.0-INTEGRATION-AUDIT.md).
All phase directories and UI artifacts remain in place as execution history.

**What's next:** No new product scope selected. Continue daily backup freshness
and certificate-expiry checks; use `$gsd-new-milestone` when ready.
