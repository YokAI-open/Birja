"""Explicit operator publication for prepared stock catalogs and selected mappings."""

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, create_async_engine

from app.db.connection import database_connect_args
from app.db.portfolio_migrate import require_migrator
from app.models.stock_catalog import StockCatalogAdmission
from app.services.stock_catalog_provider import CatalogAssetError, stage_reviewed_assets
from app.services.stock_catalog_publish import (
    CatalogPublishError,
    current_mapping_targets,
    promote_catalog_mappings,
    publish_catalog,
    reviewed_mapping_scope,
)
from app.tasks.stock_catalog_inventory import MAX_STAGE_BYTES, CatalogManifest


@dataclass(frozen=True, slots=True, repr=False)
class _OperatorConnection:
    env: str
    database_url: str
    database_ssl_ca_file: str | None


def _database_settings(fixture: bool) -> _OperatorConnection:
    url = os.environ.get("BIRJA_CATALOG_DATABASE_URL", "")
    if fixture:
        parsed = make_url(url)
        if (
            os.environ.get("ENV") not in {"dev", "test"}
            or parsed.drivername != "postgresql+asyncpg"
            or parsed.host not in {"localhost", "127.0.0.1"}
            or parsed.port != 55432
            or not parsed.database
            or not parsed.database.endswith("_test")
            or parsed.query
        ):
            raise CatalogPublishError("Fixtures require the isolated local test database")
        return _OperatorConnection("test", url, None)
    if make_url(url).username != "birja_migrator":
        raise CatalogPublishError("The restricted catalog operator connection is required")
    return _OperatorConnection("prod", url, os.environ.get("DATABASE_SSL_CA_FILE"))


async def _check_connection(conn: AsyncConnection, fixture: bool) -> None:
    if fixture:
        database, session_role, current_role = (
            await conn.execute(text("SELECT current_database(), session_user, current_user"))
        ).one()
        if not database.endswith("_test") or session_role != current_role:
            raise CatalogPublishError("Fixtures require the isolated local test database")
        if (
            await conn.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one() != "0025":
            raise CatalogPublishError("Catalog import requires schema 0025")
    elif await require_migrator(conn) != "0025":
        raise CatalogPublishError("Catalog import requires the admitted catalog migration")


def _read_manifest(path: Path) -> CatalogManifest:
    if path.is_symlink() or not path.is_file():
        raise CatalogPublishError("Expected a reviewed regular manifest file")
    with path.open("rb") as stream:
        payload = stream.read(MAX_STAGE_BYTES + 1)
    if len(payload) > MAX_STAGE_BYTES:
        raise CatalogPublishError("Manifest exceeds its size bound")
    return CatalogManifest.model_validate_json(payload)


def _generation(value: str) -> int | None:
    if value == "empty":
        return None
    return _positive_id(value)


def _positive_id(value: str) -> int:
    try:
        result = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Expected a positive ID") from None
    if not 0 < result < 2**63:
        raise argparse.ArgumentTypeError("Expected a positive ID")
    return result


def _args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True, dest="command")
    publish = commands.add_parser("publish", help="Publish a complete reviewed catalog")
    publish.add_argument("manifest", type=Path)
    publish.add_argument("--expect-generation", type=_generation, required=True)
    publish.add_argument("--fixture", action="store_true")
    publish.add_argument("--fixture-as-of", type=datetime.fromisoformat)
    stage = commands.add_parser("stage-assets", help="Stage and promote the exact reviewed assets")
    stage.add_argument("--admission-id", type=_positive_id, required=True)
    stage.set_defaults(fixture=False)
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> dict[str, object]:
    settings = _database_settings(args.fixture)
    engine = create_async_engine(
        settings.database_url, connect_args=database_connect_args(settings, migration=True)
    )
    try:
        if args.command == "publish":
            manifest = _read_manifest(args.manifest)
            if args.fixture != (manifest.mode == "fixture") or (
                args.fixture_as_of is not None and not args.fixture
            ):
                raise CatalogPublishError("Manifest and operator mode must agree")
            now = args.fixture_as_of
            if now is not None and now.tzinfo is None:
                raise CatalogPublishError("A timezone-aware clock is required")
            async with AsyncSession(engine) as db, db.begin():
                await _check_connection(await db.connection(), args.fixture)
                receipt = await publish_catalog(
                    db, manifest, args.expect_generation, now=now, allow_fixture=args.fixture
                )
            return asdict(receipt)
        return await _stage_assets(engine, args.admission_id)
    finally:
        await engine.dispose()


async def _stage_assets(engine: AsyncEngine, admission_id: int) -> dict[str, object]:
    account = os.environ.get("STOCK_DATA_ACCOUNT", "")
    server = os.environ.get("STOCK_DATA_SERVER", "")
    environment = os.environ.get("ALPACA_ASSET_ENVIRONMENT", "")
    key = SecretStr(os.environ.get("ALPACA_API_KEY", ""))
    secret = SecretStr(os.environ.get("ALPACA_SECRET_KEY", ""))
    if (
        not account
        or not server
        or environment not in {"paper", "live"}
        or not key.get_secret_value().strip()
        or not secret.get_secret_value().strip()
    ):
        raise CatalogPublishError(
            "Explicit operator provider settings and credentials are required"
        )

    async with AsyncSession(engine) as db, db.begin():
        await _check_connection(await db.connection(), False)
        now = datetime.now(UTC)
        scope = await reviewed_mapping_scope(db, admission_id, now, lock=True)
        if (scope.provider.account, scope.provider.server, scope.provider.environment) != (
            account,
            server,
            environment,
        ):
            raise CatalogPublishError("Provider admission does not match the configured account")
        expected_targets = await current_mapping_targets(db, scope, now)
        record = await db.get(StockCatalogAdmission, admission_id)
        if record is None:
            raise CatalogPublishError("Provider admission disappeared")
        if "attempted_at" in record.scope:
            raise CatalogPublishError("This single-use provider admission was already attempted")
        # The claim survives request failure and process interruption, so a
        # restart cannot spend the same bounded reviewed provider allowance.
        claimed_at = now.isoformat()
        record.scope = {**record.scope, "attempted_at": claimed_at}

    async def before_attempt() -> None:
        async with AsyncSession(engine) as db, db.begin():
            await _check_connection(await db.connection(), False)
            checked_at = datetime.now(UTC)
            current = await reviewed_mapping_scope(db, admission_id, checked_at)
            claimed = await db.get(StockCatalogAdmission, admission_id)
            if (
                current != scope
                or claimed is None
                or claimed.scope.get("attempted_at") != claimed_at
                or await current_mapping_targets(db, current, checked_at) != expected_targets
            ):
                raise CatalogPublishError("The provider claim or selected listing has changed")

    staged = await stage_reviewed_assets(
        scope.provider,
        scope.units,
        account=account,
        server=server,
        environment=scope.provider.environment,
        expected_listings=expected_targets,
        key=key,
        secret=secret,
        before_attempt=before_attempt,
    )
    async with AsyncSession(engine) as db, db.begin():
        await _check_connection(await db.connection(), False)
        promoted = await promote_catalog_mappings(db, admission_id, staged, now=datetime.now(UTC))
    return {
        "disposition": "promoted",
        "count": promoted,
        "evidence_digests": [mapping.evidence_digest for mapping in staged],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _args(argv)
    try:
        receipt = asyncio.run(_run(args))
    except CatalogPublishError as exc:
        print(json.dumps({"disposition": "refused", "reason": str(exc)}), file=sys.stderr)
        return 2
    except CatalogAssetError as exc:
        receipt = {"disposition": "refused", "reason": exc.reason}
        print(json.dumps(receipt), file=sys.stderr)
        return 2
    except ValueError, OSError, SQLAlchemyError:
        print(
            json.dumps(
                {"disposition": "refused", "reason": "invalid input or operator connection"}
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
