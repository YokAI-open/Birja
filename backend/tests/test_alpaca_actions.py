"""Public protocol fixtures; external network is always mocked.

Reviewed 2026-11-11:
https://docs.alpaca.markets/us/reference/corporateactions-1
https://docs.alpaca.markets/us/reference/subscribetocorporateactionseventssse
https://raw.githubusercontent.com/alpacahq/cli/main/api/specs/market-data-api.json
Source SHA256: 2856fc7ed4dc6aa55a7b5db453a3cb8c5e9270b56e0679ded695bd926ec4e7dc
REST uses corporate_actions.{cash_dividends,forward_splits,...} numeric rates;
SSE data is an ARRAY of envelopes with string rates, action/at/event_id/region/ca.
since_id/until_id are inclusive ULIDs. Replay host is stream.data.alpaca.markets.
"""

from datetime import date
from decimal import Decimal

import httpx
import respx

from app.services.alpaca_actions import ActionBudget, REST_URL, fetch_action_snapshot
from app.services.stock_quote_rules import StockMapping
from tests.test_stock_admission import action_admitted
from tests.test_stock_quote_rules import NOW

EVENT_ID = "1dbc7685-9517-4a77-a236-8527d49cefdc"
BODY = (
    b'{"corporate_actions":{"cash_dividends":[{"id":"' + EVENT_ID.encode()
    + b'","symbol":"AAPL","cusip":"037833100","rate":0.24000001,'
    b'"process_date":"2026-11-10","ex_date":"2026-11-10",'
    b'"record_date":"2026-11-10","payable_date":"2026-11-15",'
    b'"foreign":false,"special":false,"currency":"USD"}]},"next_page_token":null}'
)
MAPPING = StockMapping(16, "AAPL", "asset-aapl", NOW, "NASDAQ")


async def test_rest_exact_decimal_current_schema_and_query() -> None:
    with respx.mock(assert_all_mocked=True, assert_all_called=False) as router:
        route = router.get(REST_URL).respond(200, content=BODY)
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await fetch_action_snapshot(
                http, [MAPPING], lambda: action_admitted(), lambda: NOW,
                ActionBudget(), start=date(2026, 11, 10), end=date(2026, 11, 10),
            )
    assert batch.complete and batch.attempt_count == 1
    assert batch.records[0].rate == Decimal("0.24000001")
    assert batch.records[0].currency == "USD"
    # No inferred ordinary subtype, due-bill absence or verified economic dates.
    assert batch.records[0].subtype is None
    assert batch.records[0].due_bills is None
    assert not batch.records[0].dates_verified
    assert dict(route.calls.last.request.url.params) == {
        "symbols": "AAPL", "start": "2026-11-10", "end": "2026-11-10",
        "region": "us", "data_quality": "all", "limit": "1000", "sort": "asc",
    }
