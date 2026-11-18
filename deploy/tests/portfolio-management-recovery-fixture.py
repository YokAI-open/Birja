#!/usr/bin/env python3
"""Independent0020 synthetic oracle. Transports must supply an owned database.

Full table/sequence bytes are captured before backup, never reconstructed from
restored data. Offline transports do not qualify encryption, TLS or recovery.
"""

import argparse
import hashlib
import inspect
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLE_NAMES = frozenset(
    {
        "users",
        "accounts",
        "auth_sessions",
        "refresh_tokens",
        "coins",
        "prices",
        "holdings",
        "trades",
        "alembic_version",
        "stock_instruments",
        "stock_quotes",
        "stock_sessions",
        "stock_data_admissions",
        "stock_action_events",
        "stock_action_state",
        "stock_action_sources",
        "stock_action_revisions",
        "stock_action_observations",
        "stock_action_resolutions",
        "stock_dividend_entitlements",
        "stock_split_applications",
        "stock_ownership_movements",
        "stock_fill_facts",
        "stock_status_evidence",
        "stock_dividend_payments",
        "stock_dividend_decisions",
        "portfolio_stock_closures",
        "portfolio_creations",
        "portfolio_initializations",
    }
)
IDENTITY_NAMES = TABLE_NAMES - {
    "alembic_version",
    "prices",
    "stock_instruments",
    "stock_quotes",
    "stock_action_state",
    "stock_fill_facts",
    "stock_status_evidence",
}
SOURCE_SHA256 = {
    "app/db/portfolio_bootstrap.py": "2429e45f08d72e7adf0dc816e0d5093642a92d8317bff0ad1c74d0cede7212df",
    "alembic/versions/0018_portfolio_management_expansion.py": "8e63586555c85b6f6495d0da1bad4b8a455e5de71249a0f08e2c758e4b22b0b0",
    "alembic/versions/0019_portfolio_management_backfill.py": "75f40d134e05ebdf06b15bff677d866474aa34ac64bdf66ec412bc8e0615f66d",
    "alembic/versions/0020_portfolio_management_authority.py": "53df31be89835558ef7a3b72d2febdb3e6a6130c26d27b961c282d7f9a0de860",
    "alembic/sql/0019_portfolio_metadata.sql": "a26d4230843f75af9202fce71a771818d0bd7f041777a8a01a0d53a8df7a7c65",
    "alembic/sql/0020_portfolio_management.sql": "ff97c417260fd9ed80f70c3a51ddfe32837b9b41c803bfcce4e7f37bc33be9d2",
}


def require_source(root):
    root = Path(root)
    for name, digest in SOURCE_SHA256.items():
        path = root / name
        if (
            path.is_symlink()
            or not path.is_file()
            or path.resolve() != path
            or hashlib.sha256(path.read_bytes()).hexdigest() != digest
        ):
            raise ValueError("0020 source mismatch before import")


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def require_projection(value):
    if set(value) != {"revision", "tables", "sequences"} or value["revision"] != "0020":
        raise ValueError("0020 projection shape")
    tables = value["tables"]
    if set(tables) != TABLE_NAMES or set(value["sequences"]) != IDENTITY_NAMES:
        raise ValueError("complete table/identity inventory required")
    for last, called in value["sequences"].values():
        if (
            type(last) is not int
            or last < 1
            or last > 9223372036854775807
            or type(called) is not bool
        ):
            raise ValueError("exact identity state required")
    roots = tables["accounts"]
    users = {r["email"]: r["id"] for r in tables["users"]}
    owner = users["management@example.test"]
    legacy = users["legacy@example.test"]
    zero = users["empty@example.test"]
    active = [r for r in roots if r["user_id"] == owner and r["closed_at"] is None]
    if len(active) != 10 or len(roots) != 12 or len(users) != 3:
        raise ValueError("ten active plus closed/custom legacy oracle")
    if any(r["user_id"] == zero for r in roots):
        raise ValueError("empty initialized identity acquired grant")
    if [(r["cash"], r["starting_cash"]) for r in roots if r["user_id"] == legacy] != [
        ("123.45000000", "7777.00000000")
    ]:
        raise ValueError("legacy finances changed")
    owned = [r for r in roots if r["user_id"] == owner]
    if any(
        (r["cash"], r["starting_cash"]) != ("10000.00000000", "10000.00000000")
        for r in owned
    ):
        raise ValueError("fixed grant oracle")
    journal = tables["portfolio_creations"]
    initial = [r for r in journal if r["origin"] == "initial"]
    if (
        len(journal) != 11
        or len(initial) != 1
        or initial[0]["canonical_payload"]
        != {"name": "My portfolio", "description": ""}
    ):
        raise ValueError("original initial grant evidence")
    renamed = next(r for r in owned if r["id"] == initial[0]["portfolio_id"])
    if (renamed["name"], renamed["description"]) != ("Renamed", "changed\nmetadata"):
        raise ValueError("mutable metadata oracle")
    reused = [r for r in owned if r["name"] == "Reusable"]
    if (
        len(reused) != 2
        or len({r["id"] for r in reused}) != 2
        or sum(r["closed_at"] is None for r in reused) != 1
    ):
        raise ValueError("closed original/new identity oracle")
    by_id = {r["id"]: r for r in roots}
    for row in journal:
        if (
            row["user_id"] != owner
            or by_id[row["portfolio_id"]]["user_id"] != owner
            or row["amount"] != "10000.00000000"
            or row["payload_version"] != 1
        ):
            raise ValueError("owner-bound immutable grant oracle")
    initializations = tables["portfolio_initializations"]
    if len(initializations) != 3 or {r["user_id"] for r in initializations} != {
        owner,
        legacy,
        zero,
    }:
        raise ValueError("all-user initialization oracle")
    for row in initializations:
        if row["user_id"] in {legacy, zero}:
            if (row["origin"], row["portfolio_id"], row["creation_id"]) != (
                "legacy",
                None,
                None,
            ):
                raise ValueError("invented historical grant")
        elif (row["origin"], row["portfolio_id"], row["creation_id"]) != (
            "initial",
            initial[0]["portfolio_id"],
            initial[0]["id"],
        ):
            raise ValueError("original initialization lineage")
    if len(value["sequences"]) != 22 or not {
        "portfolio_creations",
        "portfolio_initializations",
    } <= set(value["sequences"]):
        raise ValueError("complete identity tails required")
    return value


async def seed_legacy(conn):
    from sqlalchemy import text

    await conn.execute(
        text(
            "INSERT INTO users(email) VALUES ('legacy@example.test'),('empty@example.test')"
        )
    )
    await conn.execute(
        text(
            "INSERT INTO accounts(user_id,name,cash,starting_cash) SELECT id,'Legacy',123.45,7777 FROM users WHERE email='legacy@example.test'"
        )
    )


async def seed_management(conn):
    """Exercise actual authority; only closure is a retained fixture operation."""
    from uuid import UUID

    from sqlalchemy import text

    owner = (
        await conn.execute(
            text(
                "INSERT INTO users(email) VALUES ('management@example.test') RETURNING id"
            )
        )
    ).scalar_one()
    root = (
        await conn.execute(text("SELECT initialize_portfolio(:u)"), {"u": owner})
    ).scalar_one()
    await conn.execute(
        text("SELECT * FROM update_portfolio_metadata(:u,:p,'Renamed',:d,true,true)"),
        {"u": owner, "p": root, "d": "changed\nmetadata"},
    )
    for n in range(10):
        row = (
            await conn.execute(
                text("SELECT * FROM create_portfolio(:u,:k,:n,:d)"),
                {
                    "u": owner,
                    "k": UUID(int=n + 1, version=4),
                    "n": "Reusable" if n < 2 else "Strategy " + str(n),
                    "d": "original " + str(n),
                },
            )
        ).one()
        if n == 0:
            await conn.execute(
                text("UPDATE accounts SET closed_at=clock_timestamp() WHERE id=:p"),
                {"p": row.portfolio_id},
            )
    # Replay the original payload after mutable metadata changed and at cap.
    original = (
        await conn.execute(
            text(
                "SELECT creation_key FROM portfolio_creations WHERE user_id=:u AND origin='initial'"
            ),
            {"u": owner},
        )
    ).scalar_one()
    replay = (
        await conn.execute(
            text("SELECT * FROM create_portfolio(:u,:k,'My portfolio','')"),
            {"u": owner, "k": original},
        )
    ).one()
    if not replay.replayed or replay.portfolio_id != root:
        raise AssertionError("original creation replay changed grant identity")
    for email in ("legacy@example.test", "empty@example.test"):
        value = (
            await conn.execute(
                text("SELECT initialize_portfolio(id) FROM users WHERE email=:e"),
                {"e": email},
            )
        ).scalar_one()
        if value is not None:
            raise AssertionError("legacy latch returned a manufactured initial grant")


async def project(conn, *, columns=None, identities=None):
    # Fixed source-owned identifiers, never archive/input-selected SQL names.
    import importlib.util

    from sqlalchemy import text

    if columns is None:
        spec = importlib.util.spec_from_file_location(
            "projection_producer", ROOT / "deploy/backup-snapshot.py"
        )
        producer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(producer)
        columns = producer.contract_columns("0020")
        identities = producer.identity_tables("0020")
    revision = (
        await conn.execute(text("SELECT version_num FROM alembic_version"))
    ).scalar_one()
    if revision != "0020":
        raise ValueError("0020 only before projection")
    tables = {}
    for name in sorted(columns):
        # jsonb text keeps exact NUMERIC decimal strings through the transport.
        fields = columns[name]
        key = (
            "id"
            if "id" in fields
            else "trade_id"
            if "trade_id" in fields
            else "coin_id"
            if "coin_id" in fields
            else "version_num"
        )
        raw = (
            await conn.execute(
                text(
                    "SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY "
                    + key
                    + "),'[]'::jsonb)::text FROM public."
                    + name
                    + " t"
                )
            )
        ).scalar_one()
        tables[name] = json.loads(raw, parse_float=str)
        for row in tables[name]:
            for field in ("cash", "starting_cash", "amount"):
                if field in row:
                    # PostgreSQL JSON numbers retain their textual eight-scale
                    # representation; no float passes through this path.
                    row[field] = str(row[field])
    sequences = {}
    for name in identities:
        sequences[name] = list(
            (
                await conn.execute(
                    text("SELECT last_value,is_called FROM public." + name + "_id_seq")
                )
            ).one()
        )
    return {"revision": revision, "tables": tables, "sequences": sequences}


def private_snapshot(path, existing):
    path = Path(path)
    if (
        not path.is_absolute()
        or path.resolve() != path
        or path.is_symlink()
        or not str(path).startswith("/tmp/birja-")
        or path.exists() != existing
    ):
        raise ValueError("owned private snapshot required")
    if existing and (
        not path.is_file()
        or path.stat().st_mode & 0o077
        or path.stat().st_uid != os.getuid()
    ):
        raise ValueError("private immutable snapshot required")
    return path


def save_snapshot(path, value):
    require_projection(value)
    path = private_snapshot(path, False)
    with path.open("xb") as stream:
        os.chmod(path, 0o600)
        stream.write(canonical(value))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_snapshot(path, digest, value):
    path = private_snapshot(path, True)
    if (
        not isinstance(digest, str)
        or not re.fullmatch("[0-9a-f]{64}", digest)
        or hashlib.sha256(path.read_bytes()).hexdigest() != digest
    ):
        raise ValueError("before-backup snapshot hash required")
    require_projection(value)
    expected = require_projection(json.loads(path.read_bytes()))
    if canonical(expected) != canonical(value):
        raise ValueError("restored economic/metadata/retry/sequence bytes changed")
    return digest


def program(*, mode, database=None, expected=None):
    if (
        mode not in {"create", "projection", "verify", "compare"}
        or database not in {None, "birja_restore_test"}
        or (mode == "create" and database)
    ):
        raise ValueError("unsafe management fixture mode/database")
    if mode == "compare" and (
        not isinstance(expected, str) or not re.fullmatch("[0-9a-f]{64}", expected)
    ):
        raise ValueError("before-backup snapshot hash required")
    # Source authentication and declared revision precede application imports.
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "fixture_producer", ROOT / "deploy/backup-snapshot.py"
    )
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    columns = {k: sorted(v) for k, v in producer.contract_columns("0020").items()}
    prelude = (
        "SOURCE_SHA256="
        + repr(SOURCE_SHA256)
        + "\nDATABASE="
        + repr(database)
        + "\nMODE="
        + repr(mode)
        + "\n"
    )
    prelude += (
        "TABLE_COLUMNS="
        + repr(columns)
        + "\nIDENTITY_TABLES="
        + repr(producer.identity_tables("0020"))
        + "\n"
    )
    code = (
        prelude
        + r"""
import asyncio,hashlib,json,os,ssl
from pathlib import Path
for name,digest in SOURCE_SHA256.items():
 p=Path('/app')/name
 if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
  raise ValueError('0020 source mismatch before import')
import asyncpg
async def declared_revision():
 from urllib.parse import urlsplit,urlunsplit
 parts=urlsplit(os.environ['DATABASE_URL'].replace('postgresql+asyncpg://','postgresql://'))
 if parts.hostname!='postgres' or parts.port!=5432 or parts.username!='birja_migrator' or parts.path!='/birja_source_test' or parts.query:
  raise ValueError('owned synthetic source identity required')
 if DATABASE:parts=parts._replace(path='/'+DATABASE)
 ca=os.environ.get('DATABASE_SSL_CA_FILE')
 if not ca:raise ValueError('verified TLS required')
 conn=await asyncpg.connect(urlunsplit(parts),ssl=ssl.create_default_context(cafile=ca))
 try:
  if MODE=='create':
   if await conn.fetchval("SELECT count(*) FROM pg_tables WHERE schemaname='public'"):
    raise ValueError('owned empty schema required before create')
  elif await conn.fetchval('SELECT version_num FROM alembic_version')!='0020':
   raise ValueError('0020 schema required before import')
 finally:await conn.close()
asyncio.run(declared_revision())
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine import make_url
"""
    )
    code += "\n".join(
        inspect.getsource(fn) for fn in (seed_legacy, seed_management, project)
    )
    code += r"""
async def run():
 url=make_url(os.environ['DATABASE_URL'])
 if DATABASE:url=url.set(database=DATABASE)
 engine=create_async_engine(url,connect_args={'ssl':ssl.create_default_context(cafile=os.environ['DATABASE_SSL_CA_FILE'])})
 try:
  if MODE=='create':
   from alembic import command
   from alembic.config import Config
   await asyncio.to_thread(command.upgrade,Config('/app/alembic.ini'),'0017')
   async with engine.begin() as conn:await seed_legacy(conn)
   await asyncio.to_thread(command.upgrade,Config('/app/alembic.ini'),'0020')
   from app.db.portfolio_bootstrap import PREFLIGHT_SQL,GRANTS_SQL
   async with engine.begin() as conn:
    raw=await conn.get_raw_connection()
    await raw.driver_connection.execute(PREFLIGHT_SQL)
    await raw.driver_connection.execute(GRANTS_SQL)
    await seed_management(conn)
  async with engine.connect() as conn:
   value=await project(conn,columns=TABLE_COLUMNS,identities=IDENTITY_TABLES)
   print('portfolio_projection='+json.dumps(value,sort_keys=True,separators=(',',':')))
   print('portfolio_verified_tls=true')
 finally:await engine.dispose()
asyncio.run(run())
"""
    return code


def main(argv=None, *, transport=None):
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("mode", choices=["create", "projection", "verify", "compare"])
    parser.add_argument("--database", choices=["birja_restore_test"])
    parser.add_argument("--snapshot")
    parser.add_argument("--expected-sha256")
    args = parser.parse_args(argv)
    if args.mode == "compare":
        private_snapshot(args.snapshot, True)
    if args.mode == "projection":
        private_snapshot(args.snapshot, False)
    code = program(
        mode=args.mode, database=args.database, expected=args.expected_sha256
    )
    if transport:
        value = transport(code)
    else:
        argv = json.loads(os.environ["BIRJA_PORTFOLIO_FIXTURE_TRANSPORT"])
        if (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(v, str) and v for v in argv)
        ):
            raise ValueError("explicit owned argv required")
        result = subprocess.run(
            argv, input=code.encode(), capture_output=True, timeout=240, check=True
        )
        rows = [
            line.split(b"=", 1)[1]
            for line in result.stdout.splitlines()
            if line.startswith(b"portfolio_projection=")
        ]
        if (
            len(rows) != 1
            or b"portfolio_verified_tls=true" not in result.stdout.splitlines()
        ):
            raise ValueError("exact TLS projection required")
        value = json.loads(rows[0])
    require_projection(value)
    digest = (
        save_snapshot(args.snapshot, value)
        if args.mode == "projection"
        else compare_snapshot(args.snapshot, args.expected_sha256, value)
        if args.mode == "compare"
        else hashlib.sha256(canonical(value)).hexdigest()
    )
    print("portfolio_fixture_sha256=" + digest)
    return digest


if __name__ == "__main__":
    main()
