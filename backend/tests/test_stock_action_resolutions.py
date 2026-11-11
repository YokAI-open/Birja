"""Real isolated PostgreSQL authority; synthetic evidence is not provider approval."""

from sqlalchemy import text


async def test_authority_has_narrow_operator_entrypoint(engine, migrated):
    async with engine.connect() as conn:
        row = (await conn.execute(text("""SELECT prosecdef,proconfig,
          NOT has_function_privilege('birja_app',p.oid,'EXECUTE'),
          NOT has_function_privilege('birja_scheduler',p.oid,'EXECUTE'),
          has_function_privilege('birja_action_operator',p.oid,'EXECUTE')
          FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
          WHERE n.nspname='public' AND p.proname='apply_stock_action_resolution'"""))).one_or_none()
        assert row is not None, "Reconciliation must have an actual restricted database authority"
        assert row[0] and row[1] == ['search_path=pg_catalog, public']
        assert all(row[2:])
