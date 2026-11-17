# Deferred work across milestones

This register survives milestone switches. Items remain unverified until their
actual acceptance evidence is obtained. Starting v1.2 does not complete them.

## v1.1 Phase 7: live stock acceptance

| Requirement | Outstanding outcome | Status |
|---|---|---|
| STOCK-01 | Actual twenty identity mappings observed Nov16; whole-phase permitted-use/live acceptance remains | Deferred; partially evidenced |
| STOCK-02 | Final live acceptance of IEX attribution across stock screens | Deferred; unverified |
| STOCK-03 | Nov16 measured183/200acceptedquotes,0–41s; intermittent invalids and final acceptance remain | Deferred; partially evidenced |
| DATA-01 | Applicable quote/action/status access, display/retention rights and operational suitability | Deferred; unverified |
| MKT-01 | Complete live regular-session acceptance | Deferred; unverified |
| SAFE-01 | Whole-phase compatibility and live acceptance, beyond substantial local proof | Deferred; unverified |

The full original requirement definitions and partial local evidence remain in
[v1.1 requirements](milestones/v1.1-REQUIREMENTS.md),
[audit](milestones/v1.1-MILESTONE-AUDIT.md), and
[Phase 7 verification](phases/07-permitted-stock-discovery/07-VERIFICATION.md).
The milestone was closed with owner-accepted gaps, not six verified outcomes.
Plan07-14 task02 was executed in the approved Nov16 campaign; task03/final
acceptance remains unresolved. No completion summary is fabricated.

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

## November16 actual measurement

The approved manual campaign completed with30attempts:20distinctidentity mappings
and10IEXsamples,183/200acceptedquotes (reported0–41s),17invalid observations.
See[actual review](phases/07-permitted-stock-discovery/07-LIVE-20261116-REVIEW.md).
This campaign is consumed; no repeat/fallback authorization follows. Allsix
Phase7requirements remain pending; missing broader rights/action/status and
final live acceptance are not established. Stock activation remains gated.

## v1.2 accepted tooling advisory — issue35

The owner explicitly approved continuing without fixing picomatch
GHSA-fc5q-39xc-vjpf/CVE-2026-112366. Follow-up:
https://github.com/YokAI-open/Birja/issues/35. Review expires2026-12-17UTC,
or earlier on a maintained fix, changed dependencies/exposure or new finding.
Exact frontend manifest/lock and Node tooling image identity/path/hash controls
retain raw findings while rejecting unrelated HIGH/critical and invalid audit
evidence. The vulnerability remains unresolved accepted risk. No unsafe fork
was installed. See Phase12's ACCEPTED-RISK and VERIFICATION records.

This accepted item does not block the locally verified Phase12 closure, waive
other findings, complete Phase7live acceptance or authorize publication or
production changes. The separate approved Python image finding was fixed and
qualified rather than added to this exception.
