"""Metadata mutation never changes the original journal, finances or history."""

from uuid import uuid4

from sqlalchemy import text

from tests.test_portfolio_creation import authority, management_api, patch, post
from tests.test_portfolio_management_authority import close
from tests.test_portfolio_strategy_lifecycle import ledger, strategy_books, trade

__all__ = ["authority", "management_api", "strategy_books"]


async def test_private_detail_edit_clear_and_legacy_summary_remain_exact(management_api):
    api = management_api
    response = await post(api, "Long term")
    assert response.status_code == 201
    root = response.json()["id"]
    # Persist nonempty real financial/history evidence, then compare every byte
    # outside the only three editable account columns after all metadata edits.
    async with api.migrator.begin() as conn:
        params = {"p": int(root), "u": api.uid, "k": uuid4()}
        await conn.execute(text("UPDATE accounts SET cash=9949.75 WHERE id=:p"), params)
        await conn.execute(
            text(
                "INSERT INTO holdings(portfolio_id,user_id,coin_id,quantity,cost_basis) "
                "SELECT :p,:u,id,.001,50.25 FROM coins WHERE symbol='BTC'"
            ),
            params,
        )
        await conn.execute(
            text(
                "INSERT INTO trades(portfolio_id,user_id,coin_id,side,input_kind,input_value,"
                "quantity,mid_price,price_as_of,exec_price,fee,cash_delta,cash_after,"
                "idempotency_key) "
                "SELECT :p,:u,id,'buy','quantity',.001,.001,50000,clock_timestamp(),"
                "50000,.25,-50.25,9949.75,:k FROM coins WHERE symbol='BTC'"
            ),
            params,
        )
    before = await economic_evidence(api)
    assert (await api.client.get(f"/api/v2/portfolios/{root}/metadata")).json() == {
        "id": root,
        "name": "Long term",
        "description": "",
    }
    for value, expected in [
        (
            "<script>alert(1)</script>\t\r\n" + "😀" * 900,
            "<script>alert(1)</script>\t\n" + "😀" * 900,
        ),
        ("😀" * 1000, "😀" * 1000),
        ("", ""),
    ]:
        changed = await patch(api, root, {"description": value})
        assert changed.status_code == 200 and changed.json() == {
            "id": root,
            "name": "Long term",
            "description": expected,
        }
        assert changed.headers["cache-control"] == "no-store"
    assert (await patch(api, root, {"name": "  Renamed  "})).json() == {
        "id": root,
        "name": "Renamed",
        "description": "",
    }
    assert (await api.client.get("/api/v2/portfolios")).json() == [{"id": root, "name": "Renamed"}]
    assert await economic_evidence(api) == before


async def economic_evidence(api):
    tables = (
        "accounts",
        "portfolio_creations",
        "portfolio_initializations",
        "holdings",
        "trades",
        "stock_fill_facts",
        "stock_ownership_movements",
        "stock_dividend_payments",
        "stock_dividend_decisions",
    )
    async with api.migrator.connect() as conn:
        return tuple(
            [
                tuple(
                    (
                        await conn.execute(
                            text(
                                "SELECT (to_jsonb(t)-'name'-'name_key'-'description')::text "  # noqa: S608
                                f"FROM {table} t ORDER BY "
                                + ("trade_id" if table == "stock_fill_facts" else "id")
                            )
                        )
                    ).scalars()
                )
                for table in tables
            ]
        )


async def test_owner_closed_unknown_privacy_and_no_public_delete(management_api):
    api = management_api
    root = (await post(api)).json()["id"]
    for target, client in [(root, api.other), ("9223372036854775807", api.client)]:
        for response in [
            await client.get(f"/api/v2/portfolios/{target}/metadata"),
            await patch(api, target, {"name": "Stolen"}, client=client),
        ]:
            assert response.status_code == 404 and response.json()["detail"] == {
                "code": "portfolio_unavailable"
            }
            assert response.headers["cache-control"] == "no-store"
    await close(api.migrator, int(root))
    assert (await api.client.get(f"/api/v2/portfolios/{root}/metadata")).status_code == 404
    assert (await patch(api, root, {"description": "closed"})).status_code == 404
    assert (await api.client.get("/api/v2/portfolios")).json() == []
    assert (
        await api.client.delete(f"/api/v2/portfolios/{root}", headers={"X-CSRF-Token": "test-csrf"})
    ).status_code == 405


async def test_patch_shape_scalar_boundaries_csrf_and_name_conflict_leave_evidence(management_api):
    api = management_api
    root = (await post(api)).json()["id"]
    assert (await post(api, "Other")).status_code == 201
    before = await economic_evidence(api)
    for payload in (
        {},
        {"name": None},
        {"description": None},
        {"cash": "1"},
        {"name": "\x00"},
        {"name": "😀" * 61},
        {"description": "😀" * 1001},
        {"description": "\x1f"},
    ):
        response = await patch(api, root, payload)
        assert response.status_code == 422 and response.headers["cache-control"] == "no-store"
    conflict = await patch(api, root, {"name": "OTHER"})
    assert conflict.status_code == 409 and conflict.json()["detail"] == {"code": "name_taken"}
    assert (
        await api.client.patch(f"/api/v2/portfolios/{root}", json={"description": "wrong"})
    ).status_code == 403
    for malformed in ("0", "-1", "01", "+1", "9223372036854775808", "abc"):
        response = await api.client.get(f"/api/v2/portfolios/{malformed}/metadata")
        assert response.status_code == 422
    assert await economic_evidence(api) == before


async def test_metadata_after_real_stock_crypto_fills_preserves_every_original(strategy_books):
    api, (root, sibling), _, _ = strategy_books
    for stock in (False, True):
        filled = await trade(api, root, stock=stock, quantity="2")
        assert filled.status_code == 201, filled.text
    before = await economic_evidence(api)
    sibling_before = await ledger(api, sibling)
    history_before = (await api.client.get(f"/api/v2/portfolios/{root}/event-history")).json()
    changed = await patch(api, root, {"name": "Edited invested root", "description": "notes"})
    assert changed.status_code == 200
    assert await economic_evidence(api) == before
    assert await ledger(api, sibling) == sibling_before
    assert (
        await api.client.get(f"/api/v2/portfolios/{root}/event-history")
    ).json() == history_before
