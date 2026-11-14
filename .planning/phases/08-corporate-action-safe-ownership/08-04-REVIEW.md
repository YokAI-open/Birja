---
phase: 08-corporate-action-safe-ownership
reviewed: 2026-11-11T11:52:47Z
depth: deep
review_head: 4d1b327df2115ea99425665d561d15e7c85acf92
files_reviewed: 2
files_reviewed_list:
  - backend/app/services/alpaca_actions.py
  - backend/tests/test_alpaca_actions.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan 08-04: Focused Adapter Review

Reviewed frozen REST/known-ID/replay adapter and adversarial test source at
`4d1b327`, against Plan 04 and stable Plan 03 interfaces. No source edits, tests,
private provider calls, credentials, database or production operations occurred.
Executor-reported coverage/test totals were context, not independent proof.

## Narrative Findings (AI reviewer)

No concrete BLOCKER or WARNING findings in this scoped review.

Traced shared attempt/page/byte/frame/mutation/deadline limits, cadence and bounded
retry paths, awaited lease/admission checks, evidence changes, cancellation cleanup,
strict numeric/duplicate-key/depth decoding, UUID/ULID identity, and immutable
normalized observations. Content-encoding rejection occurs before body decoding;
requests use fixed HTTPS URLs without redirects or environment proxy discovery.
The injected HTTP client remains responsible for verified TLS and zero hidden
transport retries, as the explicit caller contract states.

Known-ID absence remains uncertain. Replay retains only curated observations,
checks broader ingress permission separately, deduplicates inclusive mutations,
rejects divergent/out-of-order cursors, and requires the exact terminal ID when
using ID bounds even if the terminal record is unrelated to retained symbols.
Timestamp completion requires clean EOF on a finite historical-until request and
fully terminated SSE frames. Partial results never establish financial health;
lease/admission failure clears retained partial observations.

Public protocol cross-checks on 2026-11-11 confirmed the fixed endpoints and
inclusive process-date/ID filter semantics in the
[official REST documentation](https://docs.alpaca.markets/us/reference/corporateactions-1).
Historical-until connection closure and inclusive terminal-ID behavior are stated
in the [official SSE documentation](https://docs.alpaca.markets/us/reference/subscribetocorporateactionseventssse).
Envelope/type facts were cross-checked against Alpaca's
[published API schema](https://raw.githubusercontent.com/alpacahq/cli/main/api/specs/market-data-api.json).
These public protocol checks do not establish account entitlements, provider
delivery completeness or production activation acceptance. Durable consumer
transactions, ongoing completeness and current-state decisions remain downstream
plan responsibilities.
