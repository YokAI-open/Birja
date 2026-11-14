---
phase: 08-corporate-action-safe-ownership
status: deferred-by-owner
live_activation: disabled
stock_execution: disabled
phase8_private_requests_made: 0
owner_external_disposition: defer-live-activation-continue-locally-2026-11-11
prepared: 2026-11-11
---

# Phase8 action activation boundary

Phase8 implements and tests isolated corporate-action monitoring, ownership,
splits, entitlement snapshots and visible safety holds. It does not activate a
provider, execute stock orders, pay dividends, deploy software or establish any
new product rights. Existing owner-attested IEX quote permission and Phase7 UI
acceptance are retained; Phase7 live identity/freshness evidence remains deferred.
The existing Phase7 one-shot process/campaign is outside this work and unchanged.

Final local checks passed at source0026053, including final UI0cea8b5. Detailed actual receipts and source hashes
are in08-LOCAL-PROOF.md,08-REVIEW.md,08-SECURITY.md and08-UI-REVIEW.md. Fixtures and
source tests establish implementation behavior, not actual provider suitability.

## Distinct evidence required before action activation

| Boundary | Current status | Required actual evidence |
| --- | --- | --- |
| Current corporate-action REST | Unverified | Applicable account/product access, documented returned fields, symbol/event coverage and allowed collection |
| Historical mutation replay | Unverified | Actual access, permitted transport scope, finite history/cursors, completeness and deletion/revision continuity |
| Durable accounting and derived use | Unverified | Retaining normalized identities, revisions, cutoff/entitlement and split evidence for Birja's users for required duration |
| Database/backup/recovery copies | Unverified | Long-lived storage and encrypted off-server recovery retention, including correction and deletion conditions |
| Display and attribution | Unverified for actions | Applicable audience, fixed derived safety facts and required source/product notices; IEX quote attestation is not an action grant |
| Quotas and operational suitability | Unverified | Account-wide actual requests/retries/pages/bytes/stream limits, retention, history and delivery latency, under the chosen no-payment scope |
| Calendar and event facts | Current activation review required | Current official exceptional closures, verified ex-date/opening/cutoff/unit facts, reviewed authority validity and trustworthy source timestamps |
| Status/halts | Separate Phase9 prerequisite | Applicable timely eligibility/status access and safety evidence; action health alone never enables fills |

Unknown or insufficient evidence retains a safety hold. A healthy HTTP response,
recent quote, source timestamp, approved dependency or owner quote attestation
does not establish these independent permissions or complete history.

## Future bounded verification proposal

No call-ready action campaign is proposed or authorized now: actual selected
product limits and rights have not been established, so inventing a request cap
would not be a reviewed account-specific scope. No keys or private configuration
were read for this packet. Before any future measurement, prepare a concrete
proposal binding all of the following, then obtain authorization for that scope:

- Exact reviewed source commit/hashes and isolated execution tool identity.
- Private account/server scope aliases and verified provider mapping for the
  approved20 curated symbols; no guessed replacement identity.
- Separately applicable REST/replay/derived/database/backup permission references,
  validity, required notices and any broader replay transport scope.
- Exact endpoints, historical/event intervals and symbol scope; total request
  attempts including retry, pages, stream frames/mutations, bytes and duration,
  selected within actual product/account limits and shared with quote usage.
- A single fixed observation window, explicit stop conditions and no automatic
  relaunch, next-day retry, subscription/payment, agreement acceptance, provider
  contact, production change or Phase7 campaign reuse.
- Sanitized actual coverage, revision/deletion continuity, source latency, quotas
  and retained-data findings; unknown completeness remains held.

The implementation's conservative internal budgets are safety ceilings, not
provider entitlements or delivery guarantees. Current public schemas, calendar
facts and applicable terms must be rechecked at that future review. Permission
or product changes invalidate prior readiness; they do not silently renew it.

## Future production prerequisites are separate

Use the exact reviewed compatible recovery tooling and a verified fresh backup
before applying schema0011, then0012, then runtime consuming those contracts.
Provision the narrow operator/TLS credentials and save custody off-server only
under separately approved host/rollout scope. Test exact restricted-role parity,
retained tool/archive identity and a current successful restore before cutover.
Populated financial downgrade refuses; binary rollback must preserve the current
ledger, quantities, units and immutable evidence. No real-data restore, ledger
rewrite, guessed financial repair or cash-in-lieu is included here.

The local retained archive and genuine role/TLS proofs are implementation
evidence only. They were not installed into production by this phase. Existing
production remains outside the authorized local work.

## Plan13 owner decision

On2026-11-11 the owner explicitly selected **“Defer live activation; continue
locally (Recommended)”** after the separate access/retention/continuity/quota/
latency gaps were presented. The Plan13 disposition checkpoint is satisfied;
the underlying live evidence remains unverified and activation remains disabled.
Deferral is not a product-readiness pass. Existing Phase7 live deferral and quote
attestation remain unchanged. No provider call, credential read, agreement,
payment, deployment or stock execution is authorized by this decision.
Future activation still requires the concrete reviewed scope described above.
