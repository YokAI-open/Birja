---
phase: 18
reviewed: 2026-11-24
status: reviewed
---

# Phase 18 code review

An independent review and recheck covered the quote refresh lane, reported
halt parsing and publication, stock routes, Markets and the trade ticket.

The review found a publication/fill race, a potential minute skipped by the
collector, a response size limit mismatch, a Markets status serialization
mismatch, and a repricing interruption when a report renewed. The changes
serialize status publication with the final stock check, probe for the next
due report independently of source cadence, enforce the admitted response
limit, expose the publication time to Markets, and permit a newer matching
report in a repriced preview. Tests cover the final shared lock, the Markets
payload, and another explicit confirmation after repricing.

Closed-market marks retain their existing admission and action checks and
can stay visible after a report expires. Stock fills still require a current
report during the regular session. The operator dry-run validates the feed
in the submitted admission packet. A separate recovery review checked
the successor archive profile, application startup and retained fixtures. The
recovery harness now checks schema 0024 explicitly and handles the UTC-date
boundary in its synthetic session.

After a forward split, the first usable post-split quote may arrive on the
regular refresh cycle. Unit and price checks pause execution in the meantime.
This affects refresh latency only in that transition.
