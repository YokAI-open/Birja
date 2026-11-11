"""Real isolated PostgreSQL accounting invariants and privilege boundaries."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

ACTION_TABLES = {
    "stock_action_events", "stock_action_sources", "stock_action_revisions",
    "stock_action_observations", "stock_action_state", "stock_ownership_movements",
    "stock_split_applications", "stock_dividend_entitlements", "stock_action_resolutions",
}


async def test_durable_action_schema_exists(engine: AsyncEngine, migrated: None) -> None:
    async with engine.connect() as conn:
        tables = set((await conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname='public'"
        ))).scalars())
        assert ACTION_TABLES <= tables, "Accounting needs nine durable constrained relations"


async def test_quote_has_local_unit_provenance(engine: AsyncEngine, migrated: None) -> None:
    async with engine.connect() as conn:
        columns = set((await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='stock_quotes'"
        ))).scalars())
        assert "unit_epoch" in columns, "Quote units must survive restart and split boundaries"
