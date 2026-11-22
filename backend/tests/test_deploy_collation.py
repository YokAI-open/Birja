"""Execute the exact deployment collation probe on disposable PostgreSQL."""

import ast
import asyncio
import json
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from tests.portfolio_fixtures import economic_snapshot
from tests.test_migrations import test_migration_url


def collation_preflight():
    source = (Path(__file__).parents[2] / "deploy/configure-db.sh").read_text()
    python_source = source.split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    assignments = [
        node.value
        for node in ast.parse(python_source).body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "COLLATION_PREFLIGHT"
            for target in node.targets
        )
    ]
    assert len(assignments) == 1
    sql = ast.literal_eval(assignments[0])
    assert sql.startswith("BEGIN READ ONLY;") and sql.endswith("ROLLBACK;\n")
    return sql


async def probe():
    test_migration_url()  # Refuse alternate application/test connection routes.
    result = await asyncio.to_thread(
        subprocess.run,
        [
            "/usr/bin/docker",
            "exec",
            "-i",
            "birja-test-postgres-1",
            "psql",
            "-XqAt",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            "birja_test",
            "-d",
            "birja_test",
        ],
        input=collation_preflight(),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


async def metadata(conn):
    assert (await conn.execute(text("SELECT current_database(),current_user"))).one() == (
        "birja_test",
        "birja_test",
    )
    return {
        "database": list(
            (
                await conn.execute(
                    text(
                        "SELECT datcollversion,pg_database_collation_actual_version(oid) "
                        "FROM pg_database WHERE datname=current_database()"
                    )
                )
            ).one()
        ),
        "collations": [
            list(row)
            for row in (
                await conn.execute(
                    text("""
            SELECT DISTINCT n.nspname,c.collname,c.collprovider::text,c.collversion,
                pg_collation_actual_version(c.oid)
            FROM pg_index i JOIN pg_class t ON t.oid=i.indrelid
            CROSS JOIN LATERAL unnest(i.indcollation) used(oid)
            JOIN pg_collation c ON c.oid=used.oid
            JOIN pg_namespace n ON n.oid=c.collnamespace
            WHERE t.relnamespace='public'::regnamespace ORDER BY 1,2
        """)
                )
            ).all()
        ],
        "indexes": [
            list(row)
            for row in (
                await conn.execute(
                    text("""
            SELECT i.indexrelid::regclass::text,i.indisvalid,i.indisready
            FROM pg_index i JOIN pg_class t ON t.oid=i.indrelid
            WHERE t.relnamespace='public'::regnamespace ORDER BY 1
        """)
                )
            ).all()
        ],
    }


async def test_current0023_builtin_c_collation_is_healthy(engine, migrated):
    async with engine.connect() as conn:
        before = await metadata(conn)
        assert ["pg_catalog", "C", "c", None, None] in before["collations"]
        assert before["database"][0] == before["database"][1]
        assert before["database"][0] is not None
        assert all(valid and ready for _, valid, ready in before["indexes"])
        print(
            "current0023_collation_metadata="
            + json.dumps(
                {
                    "database": before["database"],
                    "collations": before["collations"],
                    "invalid_indexes": sum(
                        not valid or not ready for _, valid, ready in before["indexes"]
                    ),
                }
            )
        )
    outcome = await probe()
    async with engine.connect() as conn:
        assert await metadata(conn) == before
    assert outcome == "collation_ok"


@pytest.mark.parametrize(
    "case,expected",
    [
        ("POSIX", "collation_ok"),
        ("versioned", "collation_ok"),
        ("version-mismatch", "collation_blocked"),
        ("unknown-unversioned", "collation_blocked"),
        ("invalid-index", "collation_blocked"),
    ],
)
async def test_exact_collation_probe_preserves_benign_states(engine, migrated, case, expected):
    test_migration_url()
    custom = case in {"version-mismatch", "unknown-unversioned"}
    try:
        async with engine.begin() as conn:
            assert await conn.scalar(text("SELECT current_database()")) == "birja_test"
            assert (
                await conn.scalar(text("SELECT to_regclass('public.deploy_collation_probe')"))
                is None
            )
            assert (
                await conn.scalar(text("SELECT to_regcollation('public.deploy_collation_custom')"))
                is None
            )
            if case == "version-mismatch":
                # Supported DDL creates stale metadata without catalogue tampering.
                await conn.execute(
                    text(
                        "CREATE COLLATION public.deploy_collation_custom "
                        "(provider=libc,locale='en_AU.utf8',version='test-stale-version')"
                    )
                )
            elif case == "unknown-unversioned":
                await conn.execute(
                    text('CREATE COLLATION public.deploy_collation_custom FROM pg_catalog."C"')
                )
            await conn.execute(
                text("CREATE TABLE public.deploy_collation_probe(value text NOT NULL)")
            )
            await conn.execute(
                text("INSERT INTO public.deploy_collation_probe VALUES ('sample'),('sample')")
            )
            if case != "invalid-index":
                collation = {
                    "POSIX": 'pg_catalog."POSIX"',
                    "versioned": 'pg_catalog."en_AU.utf8"',
                    "version-mismatch": "public.deploy_collation_custom",
                    "unknown-unversioned": "public.deploy_collation_custom",
                }[case]
                await conn.execute(
                    text(
                        "CREATE INDEX deploy_collation_probe_idx "
                        "ON public.deploy_collation_probe(value COLLATE " + collation + ")"
                    )
                )
        if case == "invalid-index":
            # Failed concurrent unique build leaves a real invalid index.
            autocommit = create_async_engine(engine.url, isolation_level="AUTOCOMMIT")
            try:
                async with autocommit.connect() as conn:
                    with pytest.raises(DBAPIError, match="duplicate"):
                        await conn.execute(
                            text(
                                "CREATE UNIQUE INDEX CONCURRENTLY "
                                "deploy_collation_probe_idx ON public.deploy_collation_probe(value)"
                            )
                        )
            finally:
                await autocommit.dispose()
        async with engine.connect() as conn:
            before = await metadata(conn)
            books = await economic_snapshot(conn)
            if case == "versioned":
                row = next(row for row in before["collations"] if row[1] == "en_AU.utf8")
                assert row[3] is not None and row[3] == row[4]
            if case == "version-mismatch":
                row = next(
                    row for row in before["collations"] if row[1] == "deploy_collation_custom"
                )
                assert row[3] == "test-stale-version" and row[4] is not None and row[3] != row[4]
            if case == "unknown-unversioned":
                assert ["public", "deploy_collation_custom", "c", None, None] in before[
                    "collations"
                ]
            if case == "invalid-index":
                assert any(
                    name == "deploy_collation_probe_idx" and not valid
                    for name, valid, _ in before["indexes"]
                )
        assert await probe() == expected
        async with engine.connect() as conn:
            assert await metadata(conn) == before
            assert await economic_snapshot(conn) == books
            assert (
                await conn.execute(text("SELECT value FROM deploy_collation_probe"))
            ).scalars().all() == ["sample", "sample"]
    finally:
        async with engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS public.deploy_collation_probe"))
            if custom:
                await conn.execute(text("DROP COLLATION IF EXISTS public.deploy_collation_custom"))
