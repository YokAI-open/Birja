---
status: partial
phase: 12-preserve-existing-investing-under-portfolio-ownership
source: [12-LOCAL-VERIFICATION.md, 12-RECOVERY-PROOF.md, 12-28-PLAN.md]
started: 2026-11-17
updated: 2026-11-17
qualified_source: 1f8d5a4eb500dad879440c2f2ebba892b8b5f65c
owner_ui_accepted: true
native_200_percent_verified: false
---

# Phase 12 Owner Acceptance

## Current Test

Plan28's changed-UI review is accepted. The owner's exact response to this
current packet was “approved” on2026-11-17. Native200% is recorded separately
below; no acceptance is inferred from a prior phase or an automated screenshot.

Download `/tmp/birja-phase12-ui-review-owner-1f8d5a4.zip`, extract it and open
the top-level index.html. These are inert, read-only actual synthetic pages;
buttons place no orders. Combined ZIP SHA256:
c87cb4a3eb3feb52c42a37aa60ff69cce66d2ac8e2637847e6a977af1714d55f.

Use the same SSH destination used to access this VDS, from the owner's PC:

```bash
scp YOUR_EXISTING_SSH_DESTINATION:/tmp/birja-phase12-ui-review-owner-1f8d5a4.zip .
```

The placeholder deliberately avoids inventing a login, hostname or IP.
No credential or secret value is required in chat.

## Tests

### 1. Accept the changed portfolio identity and safety UI — 12-28-01

expected: Review named crypto/stock draft, preview/confirmation, repricing and
original receipt, holdings, mixed History and original/held details; Account's
identity-only view, incomplete/unavailable states and the zero/multiple
supplement. The correct portfolio name stays visible and wraps; no previous
target's finances appear in unavailable/zero/ambiguous states. Zero/multiple
states offer Markets without selecting or creating a portfolio. Creation,
rename, descriptions, overview management and deletion are later-phase work.
Use main/index.html for all widths, or the top-level representative links.
Report explicit acceptance or actionable issues for this packet.

result: pass
owner_response: "approved"
accepted_on: 2026-11-17
accepted_packet_sha256: c87cb4a3eb3feb52c42a37aa60ff69cce66d2ac8e2637847e6a977af1714d55f

### 2. Genuine desktop native 200% zoom — 12-28-02

expected: In the extracted HTML pages, set the desktop browser's own Zoom menu
to200%. Check trade/receipt, named holdings, mixed History/original details and
unavailable/zero/multiple pages. Text and controls remain readable/reachable,
without obscuring overlap or horizontal page overflow. Report browser and
pass/fail separately from UI acceptance. Automated reflow screenshots do not
satisfy this native-browser check.

result: pending
owner_response: none

## Source and Automated Evidence

Actual complete all-security passes at1f8d5a4:3108backend cases, exact60critical
modules100%,958frontend tests, full59browser/1originalCSPskip, audits and five
strict image scans. The complete same-archive seven-stage recovery passes at
10121b0; its exact executable/packaged inputs remain unchanged. The only broad
recovery-inventory difference is an unused backend test fixture, documented
without relabelling the original run as a different HEAD.

Main render commitfacfa1e and supplementary render1f8d5a4 share all249current
covered source hashes. The main102 and supplementary12 artifacts, original
ZIPs, private capture/renderer hashes and combined file hashes are preserved
in PROVENANCE.json and the nested manifests. Native200% remains false in every
manifest. See12-LOCAL-VERIFICATION.md for hashes and actual-source scope.

## Summary

total: 2
passed: 1
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps

No owner issue has been reported. UI acceptance is recorded; the separate
native200% result remains the second checkpoint until explicitly recorded.
Final phase code/security/UI reviews and goal verification still follow
execution; this packet does not complete Phase12, any whole requirement,
Phase7 live work, publication or deployment.
