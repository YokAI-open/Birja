import asyncio

from app.services import stock_quote_demand


async def test_same_stock_requests_coalesce_and_completion_is_token_bound(
    redis_client, monkeypatch
):
    scope = {"account": "coalesced-test", "server": "birja"}
    other = {"account": "another-test", "server": "birja"}
    monkeypatch.setattr(stock_quote_demand, "_WAIT_POLL_SECONDS", 0.01)

    queued = asyncio.Event()
    count = 0
    original_set = redis_client.set

    async def track_request(*args, **kwargs):
        nonlocal count
        value = await original_set(*args, **kwargs)
        count += 1
        if count == 2:
            queued.set()
        return value

    monkeypatch.setattr(redis_client, "set", track_request)

    async def request() -> bool:
        return await stock_quote_demand.request_stock_quote(redis_client, "AAPL", **scope)

    async with asyncio.TaskGroup() as group:
        first = group.create_task(request())
        second = group.create_task(request())
        await asyncio.wait_for(queued.wait(), timeout=2)
        pending = await stock_quote_demand.pending_stock_quotes(redis_client, **scope)
        assert set(pending) == {"AAPL"}
        assert await stock_quote_demand.pending_stock_quotes(redis_client, **other) == {}
        await stock_quote_demand.complete_stock_quotes(redis_client, {"AAPL": "earlier"}, **scope)
        assert await stock_quote_demand.pending_stock_quotes(redis_client, **scope) == pending
        await stock_quote_demand.complete_stock_quotes(redis_client, pending, **scope)
    assert first.result() and second.result()
    assert await stock_quote_demand.pending_stock_quotes(redis_client, **scope) == {}


async def test_no_consumer_returns_within_bound_and_unlisted_symbol_is_ignored(
    redis_client, monkeypatch
):
    scope = {"account": "expiry-test", "server": "birja"}
    monkeypatch.setattr(stock_quote_demand, "_WAIT_SECONDS", 0.05)
    assert not await stock_quote_demand.request_stock_quote(redis_client, "UNLISTED", **scope)
    assert await stock_quote_demand.pending_stock_quotes(redis_client, **scope) == {}
    assert not await stock_quote_demand.request_stock_quote(redis_client, "AAPL", **scope)
    pending = await stock_quote_demand.pending_stock_quotes(redis_client, **scope)
    assert set(pending) == {"AAPL"}
    await stock_quote_demand.complete_stock_quotes(redis_client, pending, **scope)
