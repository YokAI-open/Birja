"""Actual restricted PostgreSQL roles and final execution authority."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.test_stock_action_migrations import runtime_roles as _runtime_roles

runtime_roles = _runtime_roles


async def test_scheduler_can_write_status_but_not_receipts(engine,runtime_roles):
    async with engine.connect() as conn:
        tx=await conn.begin()
        cid=(await conn.execute(text("SELECT min(coin_id) FROM stock_instruments"))).scalar_one()
        await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
        await conn.execute(text("""INSERT INTO public.stock_status_evidence
        (coin_id,provider_asset_id,source_ref) VALUES (:c,'synthetic','fixture')"""),{"c":cid})
        with pytest.raises(DBAPIError) as exc:
            async with conn.begin_nested():
                await conn.execute(text("SELECT * FROM public.stock_fill_facts"))
        assert exc.value.orig.sqlstate=="42501"
        await tx.rollback()
