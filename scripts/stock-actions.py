#!/usr/bin/env python3
"""Private operator inspection/reconciliation; no provider calls or cash writes."""

import argparse
import asyncio
import json
import ssl
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.stock_action_reconciliation import (
    ResolutionRequest,
    inspect_actions,
    protected_json,
    reconcile,
)
from pydantic import BaseModel, ConfigDict, SecretStr
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


class Connection(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    database_url: SecretStr
    ca_file: str
    account: str
    server: str


async def run(args: argparse.Namespace) -> None:
    config = Connection.model_validate(protected_json(Path(args.connection_file)))
    url = make_url(config.database_url.get_secret_value())
    if (
        url.drivername != "postgresql+asyncpg"
        or not url.host
        or not url.username
        or not url.password
        or not url.database
        or url.query
    ):
        raise ValueError("verified operator connection required")
    # The CA is private configuration too; read/protect using the same owned
    # file policy, without interpreting it as JSON.
    ca = Path(config.ca_file)
    if not ca.is_absolute() or ca != ca.resolve() or not ca.is_file():
        raise ValueError("verified CA required")
    context = ssl.create_default_context(cafile=str(ca))
    engine = create_async_engine(
        url, connect_args={"ssl": context}, hide_parameters=True
    )
    try:
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory.begin() as db:
            safe = (
                await db.execute(
                    text("""SELECT
              NOT (r.rolsuper OR r.rolcreatedb OR r.rolcreaterole OR r.rolreplication
                   OR r.rolbypassrls OR r.rolinherit),
              (SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()),
              ARRAY(SELECT parent.rolname FROM pg_auth_members m JOIN pg_roles parent
                    ON parent.oid=m.roleid WHERE m.member=r.oid ORDER BY parent.rolname)
              FROM pg_roles r WHERE r.rolname=session_user""")
                )
            ).one()
            if not safe[0] or not safe[1] or safe[2] != ["birja_action_operator"]:
                raise ValueError("dedicated verified operator login required")
            await db.execute(text("SET LOCAL ROLE birja_action_operator"))
            if args.command == "inspect":
                result = await inspect_actions(
                    db,
                    coin_id=args.coin_id,
                    event_id=args.event_id,
                    after=args.after,
                    limit=args.limit,
                )
                print(
                    json.dumps(
                        {
                            "items": result,
                            "next_after": result[-1]["event_id"] if result else None,
                        }
                    )
                )
            else:
                request = ResolutionRequest.model_validate(
                    protected_json(Path(args.evidence_file))
                )
                identity = await reconcile(
                    db, request, account=config.account, server=config.server
                )
                print(
                    json.dumps(
                        {
                            "resolution_id": identity,
                            "event_id": request.event_id,
                            "state": "reconciling",
                        }
                    )
                )
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--connection-file",
        required=True,
        help="protected0600 JSON for the dedicated verified-TLS operator login",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--coin-id", type=int, required=True)
    inspect.add_argument("--event-id", type=int)
    inspect.add_argument("--after", type=int, default=0)
    inspect.add_argument("--limit", type=int, default=20)
    reconcile_parser = commands.add_parser("reconcile")
    reconcile_parser.add_argument("--evidence-file", required=True)
    args = parser.parse_args()
    try:
        asyncio.run(run(args))
    except Exception:  # noqa: BLE001 - private CLI never prints sensitive driver errors
        # Never print driver/Pydantic errors: they can embed credentials,
        # protected paths, evidence content or arbitrary DB strings.
        print("stock action operation refused", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
