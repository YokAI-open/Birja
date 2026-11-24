# Phase 18 research — On-demand stock quotes and reported halts

## What is supported by evidence

Birja's existing Alpaca adapters accepted all 20 IEX quotes in one live batch.
A disposable scheduler and PostgreSQL run persisted and showed 19 live quotes.
The status WebSocket supplied no initial statuses during a 25-second sample.
None of those checks executed a stock trade. Alpaca's REST bid/ask path is the
first choice. Use the existing quote validator and timestamps, keep credentials
with the scheduler, read actual quota headers and avoid counting request time
as event time. [Existing evidence](../../quick/20261124-stock-activation/SUMMARY.md) ·
[Latest quotes](https://docs.alpaca.markets/us/reference/stocklatestquotes-1)

The Nasdaq current RSS is documented for Nasdaq and other exchange listings,
with reads at most once per minute. A current sample returned 45 records and
included older halts. A research probe on November 24 queried the documented
historical endpoint for March 16, 2020. It returned 820 records with codes
`LUDP`, `M` and `T3`, zero `MWC0`–`MWC3`/`MWCQ` and a channel `pubDate` dated
November 24, 2026. The exchange working group records a Level 1 market-wide
halt on March 16. This sample rules out treating RSS code enumeration or a
fresh channel `pubDate` as proof of underlying market-wide scope or freshness.
It does not determine the current RSS's live market-wide behavior.
[Nasdaq RSS](https://beta.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS) ·
[History query semantics](https://www.nasdaqtrader.com/snippets/tradehaltaccordion.html) ·
[Exchange working group report](https://www.nyse.com/publicdocs/nyse/markets/nyse/Report_of_the_Market-Wide_Circuit_Breaker_Working_Group.pdf)

NYSE's current halt page links a machine-readable CSV. It is a useful
individual-halt comparator. The working group identifies CTA/UTP status
messages and NYSE/Cboe notices for market-wide breach and resumption. Check
whether a documented, current, machine-readable exchange source or combination
provides the needed coverage and freshness within the existing budget.
Check same-session recovery, carryover, genuine trading resumption versus
quote-only or scheduled times, cached/partial responses and conflicting sources.
Use report examples for historical market-wide cases. Measure the actual
publication markers and validate the API contract. HTTP receipt timestamps only
bound local receipt. Document what makes a current empty result authoritative.
A snapshot may contain zero active halts and still be valid if its coverage and
freshness are established. [NYSE current halts](https://www.nyse.com/trade/trading-halts) ·
[Nasdaq RSS terms](https://beta.nasdaqtrader.com/content/administrationsupport/agreementstrading/THRSSFeedTermsCond.pdf)

Complete free market-wide coverage and authoritative source age remain
unproven. The owner accepted a reported-halt simulator rule on November 24.
See the [source decision](18-SOURCE-DECISION.md) for the measured freshness,
active halt handling and explicit coverage limitation.

## Runtime design and patterns

1. **One status snapshot for the existing scope.** Persist a normalized,
   source-specific observation in the existing status table with separate
   constraints for Nasdaq reports and legacy stream evidence.
   Bind scope, source, session, publication/observation timestamps, expiry,
   authority generation, bounded halt states and digest. The scheduler owns
   writes. Reuse existing `status` admissions with a distinct source scope
   after checking actual use. Keep raw source payloads out of durable receipts.
2. **One quote request lane.** Reuse `fetch_iex_quotes`, `upsert_stock_quotes`
   and the existing shared attempt quota. Keep normal periodic refresh for the
   curated catalog. For a stale or missing selected quote, add a bounded,
   expiring, per-symbol coalesced request in Redis for the single scheduler.
   Treat Redis only as a request signal. The app reads trusted quotes from
   PostgreSQL. The scheduler and the app both bound waits and request volume.
3. **One financial path.** Preserve v2 preview, confirm and context routes.
   Finish any provider wait outside account/instrument locks and DB transactions.
   Return an exact prior receipt without waiting for a new quote or halt check.
   Reauthorize ownership and recalculate evidence after waits. The SQL function
   defined via `0017_stock_portfolio.sql` currently binds a legacy status row.
   A new Alembic revision must update the function and Python snapshot together.
   Preserve old receipt replay, existing money/action/session checks and role
   boundaries. Capture the new authority digest in the immutable fill facts.
4. **Small UI change.** Keep the existing trade ticket and portfolio selector.
   Map waiting, stale/failed check, reported halt and repricing to their current
   message areas. Keep the existing closed countdown. Search and broader
   corporate-action coverage belong to later phases.

## Validation Architecture

Use hermetic provider-shaped data for parser and timing tests, real disposable
PostgreSQL and Redis for locking and evidence checks, and existing browser
fixtures for the ticket. Require a separate regular-session live-data receipt
with both fills through v2, the actual measured source decision and a crypto
control. Isolated test identities and funds only. Use the unchanged qualified
recovery inputs where applicable and rerun schema/ACL/restore checks affected
by the new revision. See [validation](18-VALIDATION.md).
