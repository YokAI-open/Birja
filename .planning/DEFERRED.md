# Deferred work across milestones

This register survives milestone switches. Items remain unverified until their
actual acceptance evidence is obtained. Starting v1.2 does not complete them.

## v1.1 Phase 7: live stock acceptance

| Requirement | Outstanding outcome | Status |
|---|---|---|
| STOCK-01 | Actual permitted live mappings for the twenty curated identities | Deferred; unverified |
| STOCK-02 | Final live acceptance of IEX attribution across stock screens | Deferred; unverified |
| STOCK-03 | Actual live source freshness, collection behavior and acceptance | Deferred; unverified |
| DATA-01 | Applicable quote/action/status access, display/retention rights and operational suitability | Deferred; unverified |
| MKT-01 | Complete live regular-session acceptance | Deferred; unverified |
| SAFE-01 | Whole-phase compatibility and live acceptance, beyond substantial local proof | Deferred; unverified |

The full original requirement definitions and partial local evidence remain in
[v1.1 requirements](milestones/v1.1-REQUIREMENTS.md),
[audit](milestones/v1.1-MILESTONE-AUDIT.md), and
[Phase 7 verification](phases/07-permitted-stock-discovery/07-VERIFICATION.md).
The milestone was closed with owner-accepted gaps, not six verified outcomes.
Plan 07-14 tasks 02/03 remain unexecuted; no completion summary is fabricated.

Live stock activation stays gated. v1.2 portfolio work may proceed locally,
but neither portfolio creation nor milestone initialization enables live data.
This work is tracked separately from v1.2's committed feature requirements.

### Existing bounded manual campaign

The owner approved one manual campaign during Monday, November 16's regular
session at or after 17:30 Moscow: at most twenty reference GETs and ten IEX
quote batches, thirty private attempts and 900 seconds. Fresh calendar/source/
helper review is required first. No automatic waiter, background schedule or
retry authorization is added here. Preserve the original
[proposal](phases/07-permitted-stock-discovery/07-LIVE-VERIFICATION-PROPOSAL.md).
The old November 11 run's outcome and request count remain unknown.

## Other accepted debt

- v1.0 W01–W08 and four historical validation-record gaps remain in the
  [v1.0 audit](milestones/v1.0-MILESTONE-AUDIT.md).
- v1.1 W09 summary metadata discipline remains in the
  [v1.1 audit](milestones/v1.1-MILESTONE-AUDIT.md); no product fix is inferred.
- Production v0.5.0 rollout remains separate from source publication and needs
  its own concrete preflight/proposal and approval. Last confirmed production:
  v0.4.0/schema0008; no live system inspection occurred during milestone setup.

Updated: 2026-11-14 when v1.2 scope was confirmed.
