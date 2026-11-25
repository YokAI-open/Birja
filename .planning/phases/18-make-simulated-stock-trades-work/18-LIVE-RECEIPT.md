# Phase 18 isolated live-data receipt

Result: passed

On November 24, 2026 at 18:15 Amsterdam time, the actual v2 application
previewed and confirmed a one-share AAPL buy and sell while the regular NYSE
and Nasdaq sessions were open. A disposable PostgreSQL and Redis stack ran
migration 0024 and the actual quote and halt collection code. Provider identity,
corporate-action admission and portfolio data used isolated fixtures. The IEX
quote and Nasdaq report were live. This receipt applies to the original
curated universe and the owner-approved reported-halt rule.
[Source decision](18-SOURCE-DECISION.md)

| Check | Result |
| --- | --- |
| Selected IEX quote | One read-only request. Source timestamp 17:15:35.737 UTC, within the 120-second execution window. |
| Reported halts | One official Nasdaq Trader request. HTTP publication 17:15:23 UTC. No active applicable halt was reported. |
| AAPL buy and sell | Bought one share at the $352.25 ask and sold it at the $351.94 bid. Each fee was $0. |
| Cash and position | $1,000.00 → $647.75 → $999.69. AAPL position returned to zero. |
| History and retries | History listed both fills in order. Reconfirming each idempotency key returned its original receipt and created no duplicate. |
| Crypto control | A BTC buy with a synthetic quote succeeded in the same virtual portfolio, reduced the shared cash by its exact receipt delta and appeared in mixed History. |

A first live run at 18:05 Amsterdam time also passed, buying at $351.63 and
selling at $351.30. This final run followed the report publication and order
serialization fix. Each run used one IEX request and one Nasdaq request.

Tested base commit `f00b543a5b1de2fb946f8ec41af0c61bc1a3e776` with the Phase 18
implementation. SHA-256 pins of the measured path:

| File | SHA-256 |
| --- | --- |
| `backend/app/tasks/stock_halts.py` | `bae33961e94bf913ef0b30130478b8a852872b9aeacda9fc72d4abdda3f3fd38` |
| `backend/app/tasks/stock_scheduler.py` | `5a5235340b33a912b40e839ef5a6594935ffc87c4c07041c46497b70f8f94d4c` |
| `backend/app/services/stock_trading.py` | `f5df0d756bbf773720874a9c190d077a6c58092a2fc8a2b55a8da5b8c0b1d57c` |
| `backend/app/api/v2/stock_trades.py` | `7ce28066ef8edc4a0aa3f4288473bde51b5026ce1b1f8c31c2040a7be42a655a` |
| `backend/alembic/sql/0024_stock_halt_snapshot.sql` | `fa19099943dd885cfa3548cd45f25fb5d5150307524ea41d0cae0aa4b2c6e986` |
| Disposable test harness | `ab65dd52890eb313093f7b4fa7f2264d8139c132293d4b8fad33ceb6a95bf057` |

The live result proves the simulator path with available quotes and reports.
The report can lag or miss halts. The scope does not include broader stock
search or production activation.
