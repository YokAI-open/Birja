---
phase: 06-deploy
plan: "13"
status: complete
evidence_type: owner-confirmed-pass
release: v0.4.0
source: 46d24c8591de2207cf219429aac0768962bed4c3
---

# Live friend acceptance

Plan12 deployment, smoke and exact recovery pass; this human checkpoint is
now explicitly confirmed by the owner. Evidence is the owner’s explicit report, not an inference from smoke or CI.
Owner invites consenting Gmail and Outlook friends; assistant sends no messages,
requests no addresses/codes and performs no live trade.

For EACH provider at https://birja.nist.one:

1. Request/receive email code in their own inbox and enter it privately.
2. New account starts with$10,000 once; returning accounts keep existing value.
3. Preview and confirm a market buy; fee/fill/cash agree, then Portfolio and
   stored History match the fill.
4. Refresh/reopen and confirm session/account persists, then sign out.

| Provider | Release | Signup/code | Buy/portfolio/history | Persistence/signout |
|---|---|---|---|---|
| Gmail | v0.4.0/46d24c8 | Owner-confirmed PASS | Owner-confirmed PASS | Owner-confirmed PASS |
| Outlook | v0.4.0/46d24c8 | Owner-confirmed PASS | Owner-confirmed PASS | Owner-confirmed PASS |

Record only provider class, release/ref, time and pass/fail/nonprivate issue.
No email address, OTP, screenshot, balance or private trade data is needed.
Optional whole-position sell may be tested privately; no assistant authorization
for money/account mutation follows from requesting this human verification.

Nightly criterion separately passed the resumed actual observation in LIVE-RECOVERY.
Final06-VERIFICATION accepts both requirement mappings after source/evidence review.

## Actual human response —2026-11-10

Owner answered “Both provider flows passed” to the complete current-release
Gmail AND Outlook checklist (code delivery, private signup, new-account$10,000,
buy/fill/Portfolio/History, persistence after refresh/reopen, signout). No inbox
address, code, account screenshot or trade details collected. Assistant sent no
message or email and performed no live trade. RequirementDEPL-01/SC1 human
evidence is satisfied; separate final goal verification still required.
Owner also explicitly resumed the read-only nightly observation; that criterion
is now checked in updated LIVE-RECOVERY, not inferred from this human result.
