"""Actual PostgreSQL dividend authority and hostile restricted callers."""

from sqlalchemy import text


async def test_scheduler_boundary_requires_narrow_authority(engine, migrated):
    async with engine.connect() as conn:
        assert (await conn.execute(text(
            "SELECT to_regprocedure('public.apply_stock_dividend(bigint,bigint,text,text)') "
            "IS NOT NULL AND to_regprocedure('public.record_stock_dividend_hold(bigint,text)') "
            "IS NOT NULL"
        ))).scalar_one(), "Scheduler needs both narrow retained-row financial authorities"
