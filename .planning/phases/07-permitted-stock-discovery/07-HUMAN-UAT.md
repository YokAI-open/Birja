---
phase: 07-permitted-stock-discovery
plan: "14"
status: ui-accepted-live-verification-pending
prepared: 2026-11-11
---

# Phase 7 acceptance record

The owner requested continuing independent preparation and checking the live
measurement later. On 2026-11-11 the owner explicitly stated “i accept ui”.
UI acceptance is recorded; live measurement acceptance remains pending. This
does not finish Plan 14 or enable stock data or execution.

## Evidence already available

The final isolated browser run completed with **20 passed, one expected
production-CSP skip**, without retries. Its receipt is
`/tmp/birja-phase07-e2e-7ypm63gm/all-browser.log`; source identities and the
backend, image, restricted-role TLS and exact-recovery gates are recorded in
[07-LOCAL-PROOF.md](07-LOCAL-PROOF.md). This is local test evidence, not GitHub CI
or live provider acceptance. The isolated stack was cleaned up after the run;
no preview server is currently promised by this record.

Existing captures from that final browser output are available for preliminary
visual review in the IDE:

- [320px mobile](/home/YokaiExchange/frontend/test-results/stocks-read-only-catalogue-68652-e-accessible-representation-chromium/stocks-320.png)
- [375px mobile](/home/YokaiExchange/frontend/test-results/stocks-read-only-catalogue-1ba9e-e-accessible-representation-chromium/stocks-375.png)
- [768px tablet](/home/YokaiExchange/frontend/test-results/stocks-read-only-catalogue-24cd4-e-accessible-representation-chromium/stocks-768.png)
- [1280px desktop](/home/YokaiExchange/frontend/test-results/stocks-read-only-catalogue-d7b44-e-accessible-representation-chromium/stocks-1280.png)

These disposable, ignored test artifacts show synthetic stock responses and
fake crypto prices through the actual UI. They contain fixture company names
and attribution; they do not establish actual provider identities or freshness.
No new capture or test execution is claimed by preparing this record.

## Final review checklist

The owner accepted the UI as a whole. Individual viewport, zoom and interaction
checks were not separately reported by the owner; their automated evidence is
retained below without inventing manual test executions. The per-check pending
entries mean no separate owner test result was supplied, not that another
generic UI approval is required. Live-data acceptance remains pending.

| Review | Existing automated evidence | Owner outcome |
| --- | --- | --- |
| Exactly twenty stocks beside fifteen crypto entries; symbols, companies and NYSE/Nasdaq listings distinguishable | Responsive stock browser journeys | Pending |
| Visible IEX label, single-venue explanation and simulated-execution wording | Attribution assertions and shared component review | Pending |
| No stock Buy/Sell/Trade controls; crypto trading remains available | Browser navigation and actual isolated BTC buy/sell journey | Pending |
| Readable 320/375/768/1280px layout without document overflow | Four viewport journeys and captures | Pending |
| Readable layout at 200% zoom | 640px effective-width reflow at 1280px; actual browser zoom still needs visual review | Pending |
| Keyboard navigation and retry return focus to the stock heading | Actual keyboard retry and focus assertion | Pending |
| Stock loading/failure does not replace or block crypto | Independent error/retry journey | Pending |
| Missing, stale, previous-session, closed and unknown states are distinct; unavailable never means zero | Source-age boundary, calendar and missing-data journeys | Pending |
| Denial/revocation removes provider values while retaining catalogue identities | Permission generation/expiry browser journeys | Pending |
| Live identities and quote ages match the actual bounded campaign, including missing/stale cases | Scheduled measurement; results not yet available | Pending |

## Live measurement handoff

The already-authorized single campaign waits for 2026-11-11 **17:30 Moscow**
(14:30 UTC), with at most thirty read-only provider attempts. See
[07-ACTIVATION.md](07-ACTIVATION.md) for the frozen harness/runner identities,
owner-attested permission provenance and exact limits. Do not start another
campaign while checking it. Read the sanitized receipt at
`/tmp/birja-phase07-one-shot/result-20261111/receipt.json` once available;
absence before opening is expected, not a failed or passed measurement.

After the result is reviewed, record actual coverage/freshness and any issues.
Reuse the owner's UI acceptance; do not request the same approval again.
Owner acceptance does not establish an independently observed manual keyboard
or zoom test, or substitute for live-data evidence. Retain unresolved criteria
honestly; no completed summary or phase completion before remaining gates pass.

## Owner acceptance

- Result: **UI accepted by owner: “i accept ui”. Live data not yet accepted.**
- Review date: 2026-11-11; environment not separately specified by owner.
- Nonprivate issues: None reported with acceptance.
- Stock execution: Disabled through Phase 8.
- Production/publication: No deployment, push or merge performed.
