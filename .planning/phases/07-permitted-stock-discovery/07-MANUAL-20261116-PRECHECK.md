# November16 manual campaign precheck

Prepared2026-11-16 during the regular session. Existing owner approval is
07-LIVE-VERIFICATION-PROPOSAL.md; this is not a new grant or activation.
Phase12 remains25/28 at its independent Plan26 repair checkpoint.

## Reviewed scope

One manual campaign, fixed20symbols, maximum20 Paper reference GETs and10 IEX
latest-quote batches, at most30 actual attempts including failures,900seconds.
No retries, fallback feed, background waiter, database import or activation.
Requests stop on unexpected endpoint/response,401/403/429 or exhausted evidence.
Credentials may be read only from the existing two literal Alpaca assignments
after all prechecks; no values, headers, raw responses or private account IDs
are emitted. Existing owner-attested rights remain attested, not independently
verified. Action/status/durable-accounting rights remain outside this check.

## Fresh public review

- NYSE: https://www.nyse.com/trade/hours-calendars
- Nasdaq: https://www.nasdaq.com/market-activity/stock-market-holiday-schedule
- Paper reference: https://docs.alpaca.markets/us/reference/get-v2-assets-symbol_or_asset_id
- IEX quotes: https://docs.alpaca.markets/us/reference/stocklatestquotes-1

Reviewed2026-11-16: November16 is not a listed holiday; regular sessions are
09:30–16:00America/New_York,17:30–00:00Moscow (closeNovember17). This schedule
does not establish halt-free trading. Current installed calendar and actual
guard independently report both exchanges open. Assets expose class/listing/
active/tradable/UUID; common-stock subtype and USD are separately attributed
catalogue/product bases, not absent response fields falsely verified.

## Source and helper review

Current adapter, quote rules and calendar hashes match07-VERIFICATION.md.
Admission ec5ddce4ca362e28547dc42a698b43d90349f23436ec0c6572905c9f6c4fb315
matches the November14 review. The delta from the old runner pin concerns
action fields/feed/capabilities/retention, not quote/reference scope; no code
change was required for this check.

The old November11 runner/claim/result absence remain untouched. A separate
private0700 directory holds the manual helper and its exclusive result claim:
`/tmp/birja-phase07-manual-20261116/`. It cannot wait for another session/day.
Latest allowed start20:45UTC leaves the full900seconds before21:00UTC close.

| File | SHA256 |
|---|---|
| runner.py | eadfce17e11a25e997e37bd86c5fc0b5120f8be07fc0ceda66811357f4ce4feb |
| measurement.py (unchanged original) | 4e1553847f0d1d776f290e6ef48d290a74f1edf2b2363ed4f09fa701078b0745 |
| test_manual.py | 2d80176ded8901d096ea24b6ca78df50cfc225d7b321a249b57a54790bdeeaa7 |
| preserved old runner.py | e972fd5392bece2aac5fcc645b46f8ef356f5bdeb7733a2e866195a4609be911 |

Separate coordinator review compared transport allowlists, fixedattempt/cadence/
timeout/byte limits, safe error output, credential lifetime and exclusive claim
behavior. This is not an independent agent audit. Fifty-two offline checks pass
(eight existing pandas deprecation warnings); no package installation/update.
One initial test exposed a final diagnostic label overwriting wrong-day refusal;
the runner now applies session-close relabeling only to a measured result.
No credential read/provider request occurred during these tests or dry run.

## Result boundary

Actual receipt, once created, is private:
`/tmp/birja-phase07-manual-20261116/result-20261116/receipt.json`.
This precheck does not claim measurement success or phase completion. Preserve
all six unchecked Phase7 requirements until their real outcomes are verified.
