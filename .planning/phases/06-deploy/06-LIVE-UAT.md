---
phase: 06-deploy
plan: "13"
status: human-needed
release: v0.4.0
source: 46d24c8591de2207cf219429aac0768962bed4c3
---

# Live friend acceptance

Plan12 deployment, smoke and exact recovery pass; this human checkpoint is
pending. No actual friend signup/trade result is inferred from smoke or CI.
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
| Gmail | v0.4.0/46d24c8 | Pending | Pending | Pending |
| Outlook | v0.4.0/46d24c8 | Pending | Pending | Pending |

Record only provider class, release/ref, time and pass/fail/nonprivate issue.
No email address, OTP, screenshot, balance or private trade data is needed.
Optional whole-position sell may be tested privately; no assistant authorization
for money/account mutation follows from requesting this human verification.

Nightly criterion remains separately owner-deferred in LIVE-RECOVERY. No13SUMMARY
or DEPL acceptance until required human/calendar evidence is actually supplied.
