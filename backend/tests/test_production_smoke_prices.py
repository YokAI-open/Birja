"""Actual smoke query preserves crypto freshness across retained/current rows."""

import re
from pathlib import Path

import pytest
from sqlalchemy import text


@pytest.mark.parametrize("mixed", [False, True], ids=["retained0008", "mixed-assets"])
@pytest.mark.parametrize("missing_crypto", [False, True], ids=["priced", "missing-price"])
async def test_production_smoke_crypto_query(engine, mixed, missing_crypto):
    source = (Path(__file__).parents[2] / "deploy/smoke-prod.sh").read_text()
    match = re.search(r'^PRICES_SQL="([^"]+)"$', source, re.M)
    assert match is not None
    async with engine.begin() as conn:
        # Connection-local tables only; no production or public financial rows.
        columns = ",asset_class text" if mixed else ""
        await conn.execute(
            text(f"CREATE TEMP TABLE coins(id bigint,is_active boolean{columns}) ON COMMIT DROP")
        )
        await conn.execute(
            text("CREATE TEMP TABLE prices(coin_id bigint,as_of timestamptz) ON COMMIT DROP")
        )
        if mixed:
            await conn.execute(
                text("""INSERT INTO coins VALUES
                (1,true,'crypto'),(2,true,'crypto'),(3,false,'crypto'),
                (4,true,'stock'),(5,true,'stock')""")
            )
            # A dated stock mark and an unpriced stock must not affect crypto.
            await conn.execute(text("INSERT INTO prices VALUES (4,now()-interval '1 day')"))
        else:
            await conn.execute(text("INSERT INTO coins VALUES (1,true),(2,true),(3,false)"))
        await conn.execute(
            text("""INSERT INTO prices VALUES
            (1,now()-interval '60 seconds'),(3,now()-interval '1 day')""")
        )
        if not missing_crypto:
            await conn.execute(text("INSERT INTO prices VALUES (2,now()-interval '30 seconds')"))
        assert (await conn.execute(text(match.group(1)))).one() == (
            2,
            1 if missing_crypto else 2,
            60,
        )
