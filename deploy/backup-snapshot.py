#!/usr/bin/env python3
"""Private logical-backup producer (stdlib only).

No arguments selects root-owned JSON /etc/birja/backup.env (NEVER sourced).
Synthetic mode accepts only /tmp/birja-backup-test-*/config and local storage.
Required keys: CONFIG_KEYS; production additionally requires approved_host,
production_enabled, access_key_file, secret_key_file. Quota is fresh measured
account evidence, including hidden versions (B2 lifecycle cleanup lags one
day), unfinished uploads and other use. Reserves include HTTP retries,
metadata, old/new coexistence and repacking. No billing guarantee is inferred.

Routine assurance: default restic pre-upload extra verification, exact ID and
file sizes, byte-equal retrieved manifest, structural check. This does NOT
read all remote data blobs or replace initial full retrieval/restore proof.
There is no automatic repository initialization, provider setup or unlock.
"""

import argparse
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import resource
import selectors
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESTINATION = "s3:https://s3.eu-central-003.backblazeb2.com/Birja-backup/prod"
TAG = "birja-db-v1"
HOST = "birja-prod"
ID = re.compile(r"^[0-9a-f]{64}$")
CONFIG_KEYS = {
    "source_project",
    "state_dir",
    "restic_binary",
    "docker_binary",
    "repository",
    "password_file",
    "recovery_files",
    "release",
    "db_user",
    "db_name",
    "max_stage_bytes",
    "timeout_seconds",
    "freshness_seconds",
    "quota",
}
QUOTA_KEYS = {
    "observed_at",
    "storage_limit_bytes",
    "visible_bytes",
    "hidden_bytes",
    "unfinished_bytes",
    "other_bytes",
    "upload_reserve_bytes",
    "repack_reserve_bytes",
    "download_remaining_bytes",
    "request_remaining",
    "request_reserve",
    "free_controls_verified",
    "dedicated_repository",
}


def require(value):
    if not value:
        raise ValueError("guard")


SUPPORTED_REVISIONS = ("0007", "0008", "0009", "0010", "0011")
BASE_COLUMNS = {
    "users": "id email created_at",
    "accounts": "id user_id cash starting_cash created_at",
    "auth_sessions": "id user_id created_at revoked_at",
    "refresh_tokens": "id session_id token_hash expires_at used_at created_at",
    "coins": "id symbol name kraken_pair sort_order is_active",
    "prices": "coin_id mid as_of source",
    "holdings": "id user_id coin_id quantity cost_basis",
    "trades": "id user_id coin_id side input_kind input_value quantity mid_price price_as_of exec_price fee cash_delta cash_after idempotency_key created_at",
    "alembic_version": "version_num",
}
STOCK_COLUMNS = {
    "stock_instruments": "coin_id provider_asset_id provider_verified_at listing_exchange currency security_type source source_ref",
    "stock_quotes": "coin_id bid ask mid source feed event_at collected_at session_date admission_generation",
    "stock_sessions": "id exchange session_date opens_at closes_at coverage_start coverage_end calendar_admission_generation",
    "stock_data_admissions": "id product state generation reviewed_at valid_from valid_until evidence_ref terms_version collection_allowed display_allowed derived_allowed retention_allowed scope quota allowed_fields attribution calendar",
}
ACTION_COLUMNS = {
    "stock_action_events": "id coin_id economic_key current_revision_id first_observed_at",
    "stock_action_state": "coin_id epoch unit_epoch sequence health checked_at valid_until admission_generation coverage_start covered_until cursor staged_continuation journal_start_at complete_from quote_not_before next_blocking_at",
    "stock_action_sources": "id event_id provider product provider_event_id",
    "stock_action_revisions": "id event_id source_id ordinal fingerprint mutation_kind source_mutation_id source_event_at observed_at admission_generation normalized_terms classification reason verified_cutoff units calendar_provenance",
    "stock_action_observations": "id event_id source_id revision_id mutation_id observed_at admission_generation source_kind cycle_id",
    "stock_action_resolutions": "id event_id coin_id expected_revision admission_generation epoch decision decision_key evidence evidence_hash before_digest after_digest actor_ref created_at",
    "stock_dividend_entitlements": "id event_id user_id revision_id cutoff cutoff_rule version units_basis unit_epoch last_movement_sequence eligible_quantity state supersedes_id fingerprint",
    "stock_split_applications": "id coin_id economic_event_id revision_id new_rate old_rate cutoff prior_unit_epoch new_unit_epoch sequence_boundary before_digest after_digest processed_at",
    "stock_ownership_movements": "id coin_id user_id sequence economic_at recorded_at quantity before_quantity after_quantity before_basis after_basis unit_epoch cause_kind trade_id application_id causal_key",
}
# Independent migrated0011 catalogue, frozen only after Plan01 review. This
# includes exact types/defaults, causal FKs, checks and complete index definitions.
ACCOUNTING_SCHEMA_SHA256 = "93cbd850d4f13148515af53f6693937886d0716d52191ac04362a974c75f0a58"


def identity_tables(revision):
    names = ["users", "accounts", "auth_sessions", "refresh_tokens", "coins", "holdings", "trades"]
    if revision in ("0009", "0010", "0011"):
        names += ["stock_sessions", "stock_data_admissions"]
    if revision == "0011":
        names += [table for table, columns in ACTION_COLUMNS.items() if columns.startswith("id ")]
    return sorted(names)


def dump_identity_state(raw):
    """Parse only the allowlisted SEQUENCE SET output; never execute dump SQL.

    Sequences are not MVCC. Their actual archived values, rather than values
    read before pg_dump, are the authoritative retained identity contract.
    """
    require(isinstance(raw, bytes) and len(raw) <= 65536)
    states = {}
    for line in raw.decode("utf-8").splitlines():
        if "pg_catalog.setval(" not in line:
            continue
        match = re.fullmatch(r"SELECT pg_catalog\.setval\('public\.([a-z_]+)_id_seq', ([0-9]{1,19}), (true|false)\);", line)
        require(match is not None)
        table, value, called = match.groups()
        require(table in identity_tables("0011") and table not in states)
        require(1 <= int(value) <= 9223372036854775807)
        states[table] = [table, int(value), called == "true"]
    require(set(states) == set(identity_tables("0011")))
    return [states[table] for table in sorted(states)]


def contract_columns(revision):
    require(revision in SUPPORTED_REVISIONS)
    columns = dict(BASE_COLUMNS)
    if revision in ("0009", "0010", "0011"):
        columns["coins"] += " asset_class"
        columns.update(STOCK_COLUMNS)
    if revision == "0011":
        columns["stock_quotes"] += " unit_epoch"
        columns.update(ACTION_COLUMNS)
    return {table: set(value.split()) for table, value in columns.items()}


def manifest_sql(revision):
    """Select only reviewed static SQL before PostgreSQL parses absent objects.

    The standalone SQL remains the byte-identical legacy query plus comments.
    All substitutions are fixed repository fragments, never operator input.
    """
    contract_columns(revision)
    source = (HERE / "backup-manifest.sql").read_text()
    legacy = source.split("\n/* STOCK_COINS\n", 1)[0]
    if revision in ("0007", "0008"):
        return legacy

    def fragment(name):
        return source.split("/* " + name + "\n", 1)[1].split("\n" + name + " */", 1)[0]

    old = next(line for line in legacy.splitlines() if "SELECT 'coins'," in line)
    result = legacy.replace(old, " UNION ALL" + fragment("STOCK_COINS"))
    result = result.replace(
        "), names(name) AS (", fragment("STOCK_ROWS") + "\n), names(name) AS ("
    )
    result = result.replace(
        "('alembic_version')\n",
        "('alembic_version'),"
        + ",".join("('" + t + "')" for t in STOCK_COLUMNS)
        + "\n",
    )
    result = result.replace(
        " 'schema',json_build_object(",
        " 'stock_invalid',("
        + fragment("STOCK_INVALID")
        + "),\n 'schema',json_build_object(",
    )
    result = result.replace(
        "  'constraints',",
        "  'relations',(SELECT json_agg(json_build_array(relname,relkind) ORDER BY relname) FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind IN ('r','p','v','m','f')),\n"
        "  'columns',(SELECT json_agg(json_build_array(table_name,column_name,data_type,is_nullable,column_default,numeric_precision,numeric_scale) ORDER BY table_name,ordinal_position) FROM information_schema.columns WHERE table_schema='public'),\n"
        "  'sequences',(SELECT json_agg(json_build_array(s.relname,t.relname,a.attname,q.seqtypid::regtype::text,q.seqincrement,q.seqmin,q.seqmax,q.seqcache,q.seqcycle) ORDER BY s.relname) FROM pg_class s JOIN pg_sequence q ON q.seqrelid=s.oid LEFT JOIN pg_depend d ON d.objid=s.oid AND d.deptype='i' LEFT JOIN pg_class t ON t.oid=d.refobjid LEFT JOIN pg_attribute a ON a.attrelid=t.oid AND a.attnum=d.refobjsubid WHERE s.relnamespace='public'::regnamespace),\n"
        "  'constraints',",
    )
    if revision == "0011":
        quote = fragment("STOCK_ROWS").splitlines()[1]
        result = result.replace(quote, quote.replace("admission_generation)::text", "admission_generation,unit_epoch)::text"))
        rows = []
        timestamps = {"cutoff", "verified_cutoff", "coverage_start", "covered_until", "complete_from", "quote_not_before", "next_blocking_at"}
        for table, columns in ACTION_COLUMNS.items():
            expressions = []
            for column in columns.split():
                if column.endswith("_at") or column == "valid_until" or column in timestamps:
                    expressions.append("to_char(" + column + ",'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"')")
                else:
                    expressions.append(column + "::text")
            key = "id" if columns.startswith("id ") else "coin_id"
            rows.append(" UNION ALL SELECT '" + table + "'," + key + ",json_build_array(" + ",".join(expressions) + ")::text FROM " + table)
        result = result.replace("\n), names(name) AS (", "\n" + "\n".join(rows) + "\n), names(name) AS (")
        result = result.replace("('stock_data_admissions')\n", "('stock_data_admissions')," + ",".join("('" + t + "')" for t in ACTION_COLUMNS) + "\n")
        sequences = " UNION ALL ".join("SELECT '" + t + "',last_value,is_called FROM " + t + "_id_seq" for t in identity_tables(revision))
        result = result.replace(" 'schema',json_build_object(", " 'identity_state',(SELECT json_agg(json_build_array(name,last_value,is_called) ORDER BY name) FROM (" + sequences + ") AS s(name,last_value,is_called)),\n 'schema',json_build_object(")
    return result


def schema_guard_sql(revision):
    """Bound all public tables/sequences without changing legacy hash bytes.

    SQL identifiers derive only from reviewed constants, never operator input.
    """
    tables = contract_columns(revision)
    identities = identity_tables(revision)
    table_names = ",".join("'" + t + "'" for t in sorted(tables))
    sequence_names = ",".join("'" + t + "_id_seq'" for t in sorted(identities))
    return (
        "DO $contract$ BEGIN IF ARRAY(SELECT relname::text FROM pg_class WHERE "
        "relnamespace='public'::regnamespace AND relkind IN ('r','p','v','m','f') "
        "ORDER BY relname) IS DISTINCT FROM ARRAY[" + table_names + "]::text[] OR "
        "ARRAY(SELECT relname::text FROM pg_class WHERE relnamespace='public'::regnamespace "
        "AND relkind='S' ORDER BY relname) IS DISTINCT FROM ARRAY["
        + sequence_names
        + "]::text[] "
        "THEN RAISE EXCEPTION 'unsupported recovery catalog'; END IF; END $contract$;\n"
    )


def validate_manifest(manifest):
    """Refuse unknown/omitted shape and invalid persisted discovery state."""
    expected = contract_columns(manifest["revision"])
    require(set(manifest["tables"]) == set(expected))
    for row in manifest["tables"].values():
        require(set(row) == {"count", "sha256"})
        require(type(row["count"]) is int and row["count"] >= 0)
        require(isinstance(row["sha256"], str) and ID.fullmatch(row["sha256"]))
    actual = {}
    for table, column, identity, data_type in manifest["schema"]["identities"]:
        require(table in expected and column not in actual.setdefault(table, set()))
        actual[table].add(column)
        require(isinstance(data_type, str) and identity in ("", "a"))
    require(actual == expected)
    for key in ("negative_cash", "fractional_cents", "negative_holdings"):
        require(
            type(manifest["financial"][key]) is int and manifest["financial"][key] == 0
        )
    for key in (
        "cash",
        "starting_cash",
        "quantity",
        "cost_basis",
        "fees",
        "cash_delta",
    ):
        require(
            isinstance(manifest["financial"][key], str)
            and Decimal(manifest["financial"][key]).is_finite()
        )
    if manifest["revision"] == "0011":
        require(type(manifest["stock_invalid"]) is int and manifest["stock_invalid"] == 0)
        require(hashlib.sha256(json.dumps(manifest["schema"], sort_keys=True, separators=(",", ":")).encode()).hexdigest() == ACCOUNTING_SCHEMA_SHA256)
        states = manifest["identity_state"]
        require(isinstance(states, list) and len(states) == len(identity_tables("0011")))
        require([row[0] for row in states] == identity_tables("0011"))
        for name, value, called in states:
            require(type(value) is int and 1 <= value <= 9223372036854775807)
            require(type(called) is bool)
    if manifest["revision"] in ("0009", "0010"):
        require(
            type(manifest["stock_invalid"]) is int and manifest["stock_invalid"] == 0
        )
        require(
            manifest["schema"]["relations"]
            == [[table, "r"] for table in sorted(expected)]
        )
        identities = {
            "users",
            "accounts",
            "auth_sessions",
            "refresh_tokens",
            "coins",
            "holdings",
            "trades",
            "stock_sessions",
            "stock_data_admissions",
        }
        found = {
            table
            for table, column, identity, kind in manifest["schema"]["identities"]
            if identity == "a" and column == "id" and kind == "bigint"
        }
        require(found == identities)
        sequences = manifest["schema"]["sequences"]
        require(len(sequences) == len(identities))
        require(
            {tuple(row) for row in sequences}
            == {
                (t + "_id_seq", t, "id", "bigint", 1, 1, 9223372036854775807, 1, False)
                for t in identities
            }
        )
        columns = manifest["schema"]["columns"]
        require(len(columns) == sum(len(value) for value in expected.values()))
        for table, column, kind, nullable, default, precision, scale in columns:
            require(table in expected and column in expected[table])
            if table in STOCK_COLUMNS or (table == "coins" and column == "asset_class"):
                optional = {
                    ("stock_instruments", "provider_asset_id"),
                    ("stock_instruments", "provider_verified_at"),
                    ("stock_sessions", "opens_at"),
                    ("stock_sessions", "closes_at"),
                    *(
                        ("stock_data_admissions", c)
                        for c in (
                            "reviewed_at",
                            "valid_from",
                            "valid_until",
                            "evidence_ref",
                            "terms_version",
                        )
                    ),
                }
                require(nullable == ("YES" if (table, column) in optional else "NO"))
                expected_type = "text"
                if column in (
                    "id",
                    "coin_id",
                    "generation",
                    "admission_generation",
                    "calendar_admission_generation",
                ):
                    expected_type = "bigint"
                elif column in ("bid", "ask", "mid"):
                    expected_type = "numeric"
                    require((precision, scale) == (20, 8))
                elif column.endswith("_at") or column in ("valid_from", "valid_until"):
                    expected_type = "timestamp with time zone"
                elif column in ("session_date", "coverage_start", "coverage_end"):
                    expected_type = "date"
                elif column.endswith("_allowed"):
                    expected_type = "boolean"
                elif column in ("scope", "quota", "allowed_fields", "calendar"):
                    expected_type = "jsonb"
                require(kind == expected_type)
        constraints = manifest["schema"]["constraints"]
        require(all(row[3] is True for row in constraints))
        require(sum(row[2] == "f" for row in constraints) == 10)
        required = {
            "ck_coins_asset_class_known",
            "ck_coins_asset_kraken_mapping",
            "uq_coins_asset_class_symbol",
            "fk_stock_instruments_coin_id_coins",
            "fk_stock_quotes_coin_id_stock_instruments",
            "uq_stock_sessions_exchange_date",
            "uq_stock_data_admissions_product",
        }
        require(required <= {row[1] for row in constraints})
        checks = {
            "stock_instruments": "usd_only exchange_known common_stock_only source_length source_ref_length provider_id_length verification_identity",
            "stock_quotes": "finite_positive source_feed generation_positive spread_mid event_not_future",
            "stock_sessions": "boundaries exchange_known generation_positive coverage",
            "stock_data_admissions": "fields_bounded calendar_bounded quota_bounded scope_bounded calendar_product_only product_known approved_evidence state_known evidence_ref_length generation_positive attribution_length terms_version_length validity",
        }
        for table, suffixes in checks.items():
            require(
                {row[1] for row in constraints if row[0] == table and row[2] == "c"}
                == {"ck_" + table + "_" + suffix for suffix in suffixes.split()}
            )
        indexes = manifest["schema"]["indexes"]
        require(all(row[1] is True and row[2] is True for row in indexes))
        require(
            {row[0] for row in indexes if row[0].startswith(("pk_stock_", "uq_stock_"))}
            == {
                "pk_stock_instruments",
                "uq_stock_instruments_provider_asset_id",
                "pk_stock_quotes",
                "pk_stock_sessions",
                "uq_stock_sessions_exchange_date",
                "pk_stock_data_admissions",
                "uq_stock_data_admissions_product",
            }
        )


def strict_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result)
            result[key] = value
        return result

    return json.loads(data, object_pairs_hook=unique)


def private_file(path):
    p = Path(path)
    s = p.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_uid == os.geteuid())
    require(s.st_mode & 0o077 == 0)
    return p


def private_dir(path):
    p = Path(path)
    s = p.lstat()
    require(stat.S_ISDIR(s.st_mode) and s.st_uid == os.geteuid())
    require(s.st_mode & 0o077 == 0)
    return p


def contained(path, root):
    p = Path(path)
    require(p.is_absolute() and not p.is_symlink())
    require(p.resolve().is_relative_to(root.resolve()))
    return p


def load_config(args):
    synthetic = len(args) == 2 and args[0] == "--synthetic"
    require(synthetic or not args)
    path = Path(args[1]) if synthetic else Path("/etc/birja/backup.env")
    if synthetic:
        require(path.parent.parent == Path("/tmp"))
        require(path.parent.name.startswith("birja-backup-test-"))
        root = private_dir(path.parent)
    else:
        require(os.geteuid() == 0)
        root = Path("/etc/birja")
    c = strict_json(private_file(path).read_text())
    expected = CONFIG_KEYS | (
        set()
        if synthetic
        else {
            "approved_host",
            "production_enabled",
            "access_key_file",
            "secret_key_file",
        }
    )
    # Recovery bundle may retain the approved fixed synthetic source definition
    # beside an archived old checkout. Never accept an arbitrary Compose target.
    require(set(c) in [expected, expected | {"source_compose"}])
    if "source_compose" in c:
        require(synthetic)
        source = Path(c["source_compose"])
        require(source == root / "old" / "docker-compose.ops-test.yml")
        require(source == source.resolve() and source.is_file())
        require(
            hashlib.sha256(source.read_bytes()).hexdigest()
            == "6e3a5c1b02d07c785cc69327c0656424af307da7719ed51781ab0d6c5fe3bc9c"
        )
    require(c["source_project"] == ("birja-ops-test" if synthetic else "birja-prod"))
    require(re.fullmatch(r"[0-9a-f]{40}", c["release"]))
    for key in ["db_user", "db_name"]:
        require(re.fullmatch(r"[a-z][a-z0-9_]{0,62}", c[key]))
    for key, low, high in [
        ("max_stage_bytes", 1, 2_000_000_000),
        ("timeout_seconds", 1, 3600),
        ("freshness_seconds", 1, 93600),
    ]:
        require(type(c[key]) is int and low <= c[key] <= high)
    require(set(c["quota"]) == QUOTA_KEYS)
    for key in QUOTA_KEYS - {"free_controls_verified", "dedicated_repository"}:
        require(type(c["quota"][key]) is int and c["quota"][key] >= 0)
    require(type(c["recovery_files"]) is list and 1 <= len(c["recovery_files"]) <= 20)
    if synthetic:
        for key in [
            "state_dir",
            "restic_binary",
            "docker_binary",
            "repository",
            "password_file",
        ]:
            contained(c[key], root)
        for p in c["recovery_files"]:
            contained(p, root)
    else:
        require(
            c["production_enabled"] is True
            and c["approved_host"] == socket.gethostname()
        )
        require(c["state_dir"] == "/var/lib/birja/backup")
        require(c["repository"] == DESTINATION)
        require(c["docker_binary"] == "/usr/bin/docker")
        require(c["restic_binary"] == "/usr/local/bin/restic")
        for key in ["password_file", "access_key_file", "secret_key_file"]:
            contained(c[key], root)
        for p in c["recovery_files"]:
            require(
                Path(p).resolve().is_relative_to(root)
                or Path(p).resolve().is_relative_to(Path("/var/lib/birja/ops"))
            )
    private_file(c["password_file"])
    for p in c["recovery_files"]:
        private_file(p)
    require(path == path.resolve())
    c["_config_root"] = str(root)
    c["_synthetic"] = synthetic
    return c


def acquire_operation_lock(path, inherited_fd=None):
    """Return an owned handle; never unlock a parent's open-file description."""
    path = Path(path)
    production = path == Path("/var/lock/birja-deploy.lock")
    require(path.is_absolute())
    resolved = path.resolve()
    if path != resolved:
        # Ubuntu's system alias is the sole exception to canonical lock paths.
        # Its ancestors cannot be writable by other users. A shared /run/lock
        # is safe only with sticky deletion protection for the root-owned file.
        require(production and resolved == Path("/run/lock/birja-deploy.lock"))
        alias = Path("/var/lock")
        info = alias.lstat()
        require(stat.S_ISLNK(info.st_mode) and info.st_uid == 0)
        require(alias.readlink() in [Path("/run/lock"), Path("../run/lock")])
        for parent in [Path("/"), Path("/var"), Path("/run"), Path("/run/lock")]:
            info = parent.lstat()
            require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0)
            require(
                info.st_mode & 0o022 == 0
                or (parent == Path("/run/lock") and info.st_mode & stat.S_ISVTX)
            )
        path = resolved

    def validate(fd):
        current, held = path.lstat(), os.fstat(fd)
        require(stat.S_ISREG(current.st_mode) and stat.S_ISREG(held.st_mode))
        require(held.st_uid == (0 if production else os.geteuid()))
        require(held.st_mode & 0o022 == 0 and os.path.samestat(current, held))

    inherited = (
        os.environ.get("BIRJA_BACKUP_LOCK_FD") if inherited_fd is None else inherited_fd
    )
    if inherited is not None:
        require(
            type(inherited) is str
            and inherited.isascii()
            and inherited.isdigit()
            and 3 <= int(inherited) <= 1024
        )
        fd = int(inherited)
        validate(fd)
        lines = Path(f"/proc/self/fdinfo/{fd}").read_text().splitlines()
        require(
            any(re.search(r"^lock:.* FLOCK +ADVISORY +WRITE ", line) for line in lines)
        )
        owned = os.dup(fd)
    else:
        owned = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        validate(owned)
        if inherited is None:
            fcntl.flock(owned, fcntl.LOCK_EX | fcntl.LOCK_NB)
        validate(owned)
        return os.fdopen(owned, "a")
    except BaseException:
        os.close(owned)
        raise


def utc(epoch=None):
    return dt.datetime.fromtimestamp(
        time.time() if epoch is None else epoch, dt.UTC
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


def atomic(path, obj):
    fd, name = tempfile.mkstemp(prefix=".status-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
        d = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(d)
        finally:
            os.close(d)
    finally:
        Path(name).unlink(missing_ok=True)


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def config_digest(c):
    stable = {k: v for k, v in c.items() if not k.startswith("_") and k != "quota"}
    stable["quota_policy"] = {
        k: c["quota"].get(k)
        for k in [
            "storage_limit_bytes",
            "upload_reserve_bytes",
            "repack_reserve_bytes",
            "request_reserve",
            "free_controls_verified",
            "dedicated_repository",
        ]
    }
    stable["material"] = {
        str(p): file_sha(private_file(p)) for p in c["recovery_files"]
    }
    for k in ["password_file", "access_key_file", "secret_key_file"]:
        if k in c:
            stable[k] = {"path": c[k], "sha256": file_sha(private_file(c[k]))}
    if "source_compose" in c:
        stable["source_compose_sha256"] = file_sha(c["source_compose"])
    return sha_bytes(json.dumps(stable, sort_keys=True).encode())


def recovery_binding(c):
    # Installed identity comes from the immutable release and its authenticated
    # inventory, never from an argument claiming that a restore was successful.
    release = HERE.parent
    bundle_sha = None
    inventory_hashes = {}
    if release.parent.name == "releases" and release.parent.parent.name == "recovery":
        require(ID.fullmatch(release.name) and release == release.resolve())
        private_dir(release)
        inventory = json.loads(private_file(release / "INVENTORY.json").read_text())
        for line in private_file(release / "SHA256SUMS").read_text().splitlines():
            value, name = line.split("  ")
            require(ID.fullmatch(value) and name not in inventory_hashes)
            path = release / name
            require(path == path.resolve() and path.is_relative_to(release))
            require(file_sha(path) == value)
            inventory_hashes[name] = value
        require(set(inventory_hashes) == set(inventory["files"]) | {"INVENTORY.json"})
        bundle_sha = release.name
    toolchain = {
        "inventory": inventory_hashes,
        "python": file_sha(sys.executable),
        "docker_host": file_sha("/usr/bin/docker"),
        "bash": file_sha("/bin/bash"),
    }
    for key in ["restic_binary", "docker_binary"]:
        toolchain[key] = file_sha(c[key])
    # Include actual adjacent helpers even outside an installed release.
    toolchain["helpers"] = {
        p.name: file_sha(p)
        for p in HERE.iterdir()
        if p.is_file()
        and p.name
        in {
            "backup-snapshot.py",
            "verify-restore.py",
            "backup-manifest.sql",
            "backup.sh",
            "restore-check.sh",
        }
    }
    return {
        "source_project": c["source_project"],
        "db_name": c["db_name"],
        "db_user": c["db_user"],
        "repository_sha256": sha_bytes(c["repository"].encode()),
        "config_sha256": config_digest(c),
        "toolchain_sha256": sha_bytes(json.dumps(toolchain, sort_keys=True).encode()),
        "bundle_sha256": bundle_sha,
    }


def read_state(state, name):
    return strict_json(private_file(private_dir(state) / name).read_text())


def recovery_gate(c, snapshot_id, expected):
    require(type(snapshot_id) is str and ID.fullmatch(snapshot_id))
    job = Job(c)
    with job.lock() as lock:
        binding = recovery_binding(c)
        require(set(expected) == set(binding) | {"source_release", "source_revision"})
        require(binding["bundle_sha256"] is not None)
        require(expected["source_release"] == c["release"])
        require(all(expected[k] == v for k, v in binding.items()))
        require(
            re.fullmatch(r"[0-9a-f]{40}", expected["source_release"])
            and re.fullmatch(r"[A-Za-z0-9_]{1,64}", expected["source_revision"])
        )
        backup = read_state(job.state, "last-success.json")
        backup_attempt = read_state(job.state, "last-attempt.json")
        success = read_state(job.state, "restore-last-success.json")
        attempt = read_state(job.state, "restore-last-attempt.json")
        require(
            backup["ok"] is True
            and backup_attempt["ok"] is True
            and backup["run_id"] == backup_attempt["run_id"]
        )
        require(
            set(success)
            == set(binding)
            | {
                "format",
                "run_id",
                "snapshot_id",
                "ok",
                "started_epoch",
                "started_utc",
                "completed_epoch",
                "completed_utc",
                "source_release",
                "source_revision",
                "manifest_sha256",
                "dump_sha256",
                "recovery_sha256",
            }
        )
        require(success == attempt and success["ok"] is True and success["format"] == 1)
        require(backup_attempt == backup)
        data_time(backup, c)
        require(backup["utc"] == utc(backup["epoch"]))
        require(
            type(success["format"]) is int
            and re.fullmatch(r"[0-9a-f]{32}", success["run_id"])
        )
        require(backup["snapshot_id"] == success["snapshot_id"] == snapshot_id)
        require(all(success[k] == value for k, value in expected.items()))
        now = time.time()
        for epoch in [
            backup["epoch"],
            success["started_epoch"],
            success["completed_epoch"],
        ]:
            require(
                type(epoch) is int
                and 0 <= now - epoch <= c["freshness_seconds"] <= 93600
            )
        require(
            backup["epoch"] <= success["started_epoch"] <= success["completed_epoch"]
        )
        for prefix in ["started", "completed"]:
            require(
                success[prefix + "_utc"]
                == dt.datetime.fromtimestamp(
                    success[prefix + "_epoch"], dt.UTC
                ).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        job.refresh_quota(lock)  # Fresh inventory, without changing recovery evidence.
        rows = strict_json(job.restic("snapshots", snapshot_id))
        require(job.check_scope(rows) == [snapshot_id])
        remote_time = dt.datetime.fromisoformat(rows[0]["time"])
        require(remote_time.tzinfo is not None)
        epoch = remote_time.timestamp()
        require(
            0 <= now - epoch <= c["freshness_seconds"] and epoch <= backup["epoch"] + 1
        )
        raw = job.restic("dump", snapshot_id, "/manifest.json")
        require(sha_bytes(raw) == success["manifest_sha256"])
        manifest = strict_json(raw)
        require(
            manifest["release"] == expected["source_release"]
            and manifest["revision"] == expected["source_revision"]
        )
        require(
            manifest["archive_sha256"] == success["dump_sha256"]
            and manifest["recovery_sha256"] == success["recovery_sha256"]
        )
        require(manifest["source_binding"] == binding)
        require(
            manifest["data_epoch"] == backup["data_epoch"]
            and manifest["started_utc"] == backup["data_utc"]
            and manifest["data_utc"] == backup["data_utc"]
        )
        # Inventory and remote reads can consume the last seconds of the RPO.
        # Recheck every freshness predicate at authorization, after all I/O.
        authorized_at = time.time()
        data_time(backup, c, authorized_at)
        require(
            all(
                0 <= authorized_at - value <= c["freshness_seconds"]
                for value in [
                    backup["epoch"],
                    success["started_epoch"],
                    success["completed_epoch"],
                    epoch,
                ]
            )
        )
        return {
            "snapshot_id": snapshot_id,
            "recovery_verified": True,
            "completed_utc": success["completed_utc"],
        }


def data_time(record, c, now=None):
    now = time.time() if now is None else now
    for epoch, stamp in [("data_epoch", "data_utc"), ("epoch", "utc")]:
        require(type(record[epoch]) is int and record[stamp] == utc(record[epoch]))
    require(0 <= now - record["data_epoch"] <= c["freshness_seconds"])
    require(record["data_epoch"] <= record["epoch"] <= now)
    return record["data_epoch"]


def status(c):
    try:
        state = private_dir(c["state_dir"])
        s = json.loads(private_file(state / "last-success.json").read_text())
        a = json.loads(private_file(state / "last-attempt.json").read_text())
        require(a == s and a["ok"] is True)
        require(ID.fullmatch(s["snapshot_id"]))
        data_time(s, c)
        require(
            s["utc"]
            == dt.datetime.fromtimestamp(s["epoch"], dt.UTC).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        )
        print(f"utc={s['utc']} id={s['snapshot_id']} step=complete")
        return 0
    except (OSError, ValueError, KeyError, TypeError):
        print("step=missing-stale-or-failed")
        return 1


class Job:
    def __init__(self, c):
        self.c = c
        self.state = Path(c["state_dir"])
        self.step = "startup"
        self.started = c.setdefault("_operation_started", time.monotonic())
        self.calls = 0
        self.download_rate = None
        self.run_id = os.urandom(16).hex()
        self.env = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(self.state),
            "TMPDIR": str(self.state),
            "LANG": "C.UTF-8",
            "GOMAXPROCS": "2",
            "GOMEMLIMIT": "256MiB",
        }
        if c["_synthetic"]:
            for key in ["MOCK_ROOT", "FAIL"]:
                if key in os.environ:
                    self.env[key] = os.environ[key]
        else:
            for key, target in [
                ("access_key_file", "AWS_ACCESS_KEY_ID"),
                ("secret_key_file", "AWS_SECRET_ACCESS_KEY"),
            ]:
                value = private_file(c[key]).read_text().strip()
                require(value and "\n" not in value)
                self.env[target] = value
        self.env["RESTIC_PASSWORD_FILE"] = c["password_file"]
        self.env["RESTIC_REPOSITORY"] = c["repository"]
        self.bundle = self.state / "stage" / "backup"
        self.dc = [
            c["docker_binary"],
            "compose",
            "-p",
            c["source_project"],
            "-f",
            "/srv/birja/docker-compose.prod.yml"
            if not c["_synthetic"]
            else c.get(
                "source_compose", str(HERE.parent / "docker-compose.ops-test.yml")
            ),
        ]
        if not c["_synthetic"]:
            self.dc += ["--env-file", "/etc/birja/prod.env"]
        else:
            self.dc += ["--env-file", "/dev/null"]
        self.dc += ["exec", "-T", "postgres"]

    def limit(self):
        resource.setrlimit(
            resource.RLIMIT_FSIZE,
            (self.c["max_stage_bytes"], self.c["max_stage_bytes"]),
        )

    def call(self, argv, *, data=None, input_file=None, output=None, cwd=None, capture_limit=None):
        self.calls += 1
        require(self.calls <= 20)
        left = self.c["timeout_seconds"] - (time.monotonic() - self.started)
        require(left > 0)
        def limits():
            self.limit()
            if capture_limit is not None:
                require(type(capture_limit) is int and 1 <= capture_limit <= self.c["max_stage_bytes"])
                resource.setrlimit(resource.RLIMIT_FSIZE, (capture_limit, capture_limit))
        with tempfile.TemporaryFile(dir=self.state) as capture:
            r = subprocess.run(
                argv,
                check=False,
                input=data,
                stdin=input_file,
                stdout=output or capture,
                stderr=subprocess.DEVNULL,
                env=self.env,
                cwd=cwd,
                timeout=left,
                preexec_fn=self.limit if capture_limit is None else limits,
            )
            require(r.returncode == 0)
            if output is None:
                capture.seek(0)
                return capture.read()
        return b""

    def restic(self, *args, cwd=None):
        self.quota(fresh=self.download_rate is None)
        return self.call(
            [
                self.c["restic_binary"],
                "--json",
                "--no-cache",
                "--compression",
                "auto",
                "-o",
                "s3.connections=2",
                "-o",
                "s3.retries=2",
                "--stuck-request-timeout",
                "30s",
                "--limit-upload",
                "1024",
                "--limit-download",
                str(self.download_rate),
                *args,
            ],
            cwd=cwd,
        )

    def quota(self, *, fresh=True):
        q = self.c["quota"]
        require(
            q["free_controls_verified"] is True and q["dedicated_repository"] is True
        )
        if fresh:
            require(0 <= time.time() - q["observed_at"] <= 300)
        used = sum(
            q[k]
            for k in [
                "visible_bytes",
                "hidden_bytes",
                "unfinished_bytes",
                "other_bytes",
            ]
        )
        require(
            used + q["upload_reserve_bytes"] + q["repack_reserve_bytes"]
            <= q["storage_limit_bytes"]
        )
        require(q["upload_reserve_bytes"] >= self.c["max_stage_bytes"])
        api = self.c.get("_inventory_api")
        native_bytes = api.bytes if api is not None else 0
        require(q["request_remaining"] >= q["request_reserve"] >= 1)
        # Restic has no HTTP counter. Its work is separately bounded by tool
        # calls, retries, connections and this shared whole-operation deadline.
        # Reserve 64 KiB per possible process for limiter bursts/metadata,
        # then double rate*time for protocol/retry overhead. Keep the rate
        # fixed across commands; never grant each subprocess a fresh budget.
        if self.download_rate is None:
            allowance = q["download_remaining_bytes"] - native_bytes - 20 * 65536
            self.download_rate = min(
                1024, allowance // (2 * 1024 * (self.c["timeout_seconds"] + 20))
            )
        require(self.download_rate >= 1)
        require(
            native_bytes
            + 20 * 65536
            + 2 * self.download_rate * 1024 * (self.c["timeout_seconds"] + 20)
            <= q["download_remaining_bytes"]
        )
        require(shutil.disk_usage(self.state).free >= self.c["max_stage_bytes"] * 2)

    def refresh_quota(self, lock):
        """Refresh only inventory under a validated already-held operation lock."""
        path = (
            Path(self.c["_config_root"]) / "operation.lock"
            if self.c["_synthetic"]
            else Path("/var/lock/birja-deploy.lock")
        )
        with acquire_operation_lock(path, str(lock.fileno())):
            spec = importlib.util.spec_from_file_location(
                "quota_preflight", HERE / "backup-quota.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.c["quota"] = module.refresh(self.c)
            self.quota()
            config = Path(self.c["_config_root"]) / (
                "config" if self.c["_synthetic"] else "backup.env"
            )
            private_file(config)
            atomic(config, {k: v for k, v in self.c.items() if not k.startswith("_")})

    def lock(self):
        return acquire_operation_lock(
            Path(self.c["_config_root"]) / "operation.lock"
            if self.c["_synthetic"]
            else Path("/var/lock/birja-deploy.lock")
        )

    def line(self, proc):
        with selectors.DefaultSelector() as selector:
            selector.register(proc.stdout, selectors.EVENT_READ)
            value = bytearray()
            while len(value) < self.c["max_stage_bytes"]:
                left = self.c["timeout_seconds"] - (time.monotonic() - self.started)
                require(left > 0 and selector.select(left))
                b = os.read(proc.stdout.fileno(), 1)
                require(b)
                if b == b"\n":
                    return value.decode()
                value.extend(b)
            raise ValueError("manifest-bound")

    def snapshot(self):
        self.step = "snapshot"
        version = self.call(self.dc + ["pg_dump", "--version"]).decode().strip()
        require(version.startswith("pg_dump (PostgreSQL) 18.6"))
        psql = self.dc + [
            "psql",
            "-X",
            "-qAt",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            self.c["db_user"],
            "-d",
            self.c["db_name"],
        ]
        proc = subprocess.Popen(
            psql,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=self.env,
        )
        try:
            proc.stdin.write(
                b"BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;\nSET LOCAL idle_in_transaction_session_timeout='1h';\nSET LOCAL statement_timeout='60s';\nSET LOCAL TIME ZONE 'UTC';\nSELECT pg_export_snapshot();\n"
            )
            proc.stdin.flush()
            snapshot = self.line(proc)
            require(re.fullmatch(r"[0-9A-Fa-f]+-[0-9A-Fa-f]+-[0-9]+", snapshot))
            proc.stdin.write(
                b"SELECT version_num FROM alembic_version ORDER BY version_num;\n"
            )
            proc.stdin.flush()
            revision = self.line(proc)
            proc.stdin.write(
                (schema_guard_sql(revision) + manifest_sql(revision)).encode() + b"\n"
            )
            proc.stdin.flush()
            manifest = json.loads(self.line(proc))
            require(manifest["revision"] == revision)
            validate_manifest(manifest)
            archive = self.bundle / "database.dump"
            dump = self.dc + [
                "pg_dump",
                "-U",
                self.c["db_user"],
                "-d",
                self.c["db_name"],
                "-Fc",
                "--compress=none",
                "--snapshot=" + snapshot,
            ]
            with archive.open("wb") as f:
                self.call(dump, output=f)
            with archive.open("rb") as f:
                require(archive.stat().st_size > 5 and f.read(5) == b"PGDMP")
            with archive.open("rb") as f:
                require(
                    self.call(self.dc + ["pg_restore", "--list"], input_file=f).strip()
                )
            if revision == "0011":
                selection = ["--table=" + table + "_id_seq" for table in identity_tables(revision)]
                with archive.open("rb") as f:
                    raw_states = self.call(self.dc + ["pg_restore", "--data-only", "--file=-", *selection], input_file=f, capture_limit=65536)
                manifest["identity_state"] = dump_identity_state(raw_states)
                validate_manifest(manifest)
            proc.stdin.write(b"ROLLBACK;\n")
            proc.stdin.close()
            require(proc.wait(timeout=5) == 0)
            require(
                manifest["revision"] and manifest["server_version"].startswith("18.")
            )
            with archive.open("rb") as f:
                digest = hashlib.file_digest(f, "sha256").hexdigest()
            manifest.update(
                {
                    "format": 1,
                    "snapshot": snapshot,
                    "release": self.c["release"],
                    "started_utc": self.start_utc,
                    "data_epoch": self.data_epoch,
                    "data_utc": self.start_utc,
                    "finished_utc": utc(),
                    "archive_sha256": digest,
                    "restic_version": "0.19.1",
                    "pg_dump_version": version,
                }
            )
            (self.bundle / "manifest.json").write_text(
                json.dumps(manifest, sort_keys=True, separators=(",", ":"))
            )
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()
            proc.stdout.close()

    def check_scope(self, snapshots):
        require(type(snapshots) is list)
        ids = []
        for item in snapshots:
            require(ID.fullmatch(item["id"]))
            require(item["hostname"] == HOST and item["tags"] == [TAG])
            require(item["paths"] == [str(self.bundle)])
            ids.append(item["id"])
        require(len(ids) == len(set(ids)))
        return ids

    def perform(self):
        self.state.mkdir(mode=0o700, parents=True, exist_ok=True)
        private_dir(self.state)
        with self.lock():
            self.data_epoch = int(time.time())
            self.start_utc = utc(self.data_epoch)
            attempt = {
                "run_id": self.run_id,
                "ok": False,
                "step": "running",
                "utc": self.start_utc,
            }
            atomic(self.state / "last-attempt.json", attempt)
            stage = self.state / "stage"
            created = False
            try:
                self.step = "quota"
                self.quota()
                self.step = "tools"
                require(
                    self.call([self.c["restic_binary"], "version"]).startswith(
                        b"restic 0.19.1 "
                    )
                )
                self.step = "repository-scope"
                previous = self.check_scope(json.loads(self.restic("snapshots")))
                stage.mkdir(mode=0o700)
                created = True
                self.bundle.mkdir(mode=0o700)
                self.snapshot()
                self.step = "recovery-config"
                # Tar padding/header allowance; refuse before writing config data.
                required = sum(p.stat().st_size for p in self.bundle.iterdir())
                required += sum(
                    private_file(p).stat().st_size for p in self.c["recovery_files"]
                )
                required += 20480 + len(self.c["recovery_files"]) * 2048
                require(required <= self.c["max_stage_bytes"])
                with tarfile.open(self.bundle / "recovery.tar", "w") as tar:
                    for index, name in enumerate(self.c["recovery_files"]):
                        private_file(name)
                        tar.add(
                            name,
                            arcname=f"{index:02d}-{Path(name).name}",
                            recursive=False,
                        )
                manifest_path = self.bundle / "manifest.json"
                manifest = json.loads(manifest_path.read_text())
                manifest.update(
                    source_binding=recovery_binding(self.c),
                    recovery_sha256=file_sha(self.bundle / "recovery.tar"),
                )
                manifest_path.write_text(
                    json.dumps(manifest, sort_keys=True, separators=(",", ":"))
                )
                size = sum(p.stat().st_size for p in self.bundle.iterdir())
                require(size <= self.c["max_stage_bytes"])
                self.quota()
                self.step = "upload"
                lines = self.restic(
                    "backup", "--host", HOST, "--tag", TAG, ".", cwd=self.bundle
                ).splitlines()
                summaries = [
                    j
                    for line in lines
                    if (j := json.loads(line)).get("message_type") == "summary"
                ]
                require(len(summaries) == 1)
                sid = summaries[0]["snapshot_id"]
                require(ID.fullmatch(sid))
                self.step = "verify"
                exact = self.check_scope(json.loads(self.restic("snapshots", sid)))
                require(exact == [sid])
                nodes = [
                    json.loads(line) for line in self.restic("ls", sid).splitlines()
                ]
                files = {n["path"]: n["size"] for n in nodes if n.get("type") == "file"}
                # Backing up '.' gives rooted relative snapshot contents (/name).
                expected = {
                    "/" + p.name: p.stat().st_size for p in self.bundle.iterdir()
                }
                require(files == expected)
                require(
                    self.restic("dump", sid, "/manifest.json")
                    == (self.bundle / "manifest.json").read_bytes()
                )
                self.restic("check")
                self.step = "rotation"
                current = self.check_scope(json.loads(self.restic("snapshots")))
                require(set(current) == set(previous) | {sid})
                old = [x for x in previous if x != sid]
                if old:
                    self.restic("forget", *old)
                    self.restic("prune", "--max-repack-size", "0", "--max-unused", "0")
                    self.restic("check")
                self.step = "cleanup"
                shutil.rmtree(stage)
                created = False
                self.step = "publish"
                now = int(time.time())
                result = {
                    "run_id": self.run_id,
                    "ok": True,
                    "step": "complete",
                    "utc": dt.datetime.fromtimestamp(now, dt.UTC).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "epoch": now,
                    "data_epoch": self.data_epoch,
                    "data_utc": self.start_utc,
                    "snapshot_id": sid,
                    "archive_bytes": size,
                    "tool_invocations": self.calls,
                    "elapsed_ms": int((time.monotonic() - self.started) * 1000),
                    "data_added_packed": summaries[0].get("data_added_packed"),
                    "cpu_milliseconds": int(
                        (
                            resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime
                            + resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime
                        )
                        * 1000
                    ),
                    "peak_child_rss_kib": resource.getrusage(
                        resource.RUSAGE_CHILDREN
                    ).ru_maxrss,
                    "network_requests_measured": False,
                    "network_bytes_measured": False,
                    "assurance": "upload-verified+metadata+manifest+structural;restore-not-proven",
                }
                atomic(self.state / "last-success.json", result)
                atomic(self.state / "last-attempt.json", result)
                print(f"utc={result['utc']} id={sid} step=complete")
                return 0
            except BaseException:  # noqa: BLE001 - publish failure for signals and all producer errors
                original_step = self.step
                cleanup_ok = True
                if created:
                    try:
                        shutil.rmtree(stage)
                    except OSError:
                        cleanup_ok = False
                attempt.update(step=original_step, utc=utc(), cleanup_ok=cleanup_ok)
                atomic(self.state / "last-attempt.json", attempt)
                print(
                    f"utc={attempt['utc']} step={original_step} failed=1 cleanup_ok={int(cleanup_ok)}"
                )
                return 1


def main(argv, *, config=None):
    os.umask(0o077)
    try:
        require(argv and argv[0] in ["backup", "status", "recovery-gate"])
        if argv[0] == "recovery-gate":
            require(
                len([x.split("=", 1)[0] for x in argv if x.startswith("--")])
                == len({x.split("=", 1)[0] for x in argv if x.startswith("--")})
            )
            parser = argparse.ArgumentParser(allow_abbrev=False)
            for name in ["snapshot", "source-release", "source-revision", "bundle-sha"]:
                parser.add_argument("--" + name, required=True)
            parser.add_argument("--synthetic")
            args = parser.parse_args(argv[1:])
            c = load_config(["--synthetic", args.synthetic] if args.synthetic else [])
            expected = recovery_binding(c)
            require(expected["bundle_sha256"] == args.bundle_sha)
            expected.update(
                source_release=args.source_release, source_revision=args.source_revision
            )
            result = recovery_gate(c, args.snapshot, expected)
            print("recovery_verified=true id=" + result["snapshot_id"])
            return 0
        c = load_config(argv[1:]) if config is None else config
    except (OSError, ValueError, KeyError, TypeError):
        print("step=config invalid=1")
        return 2
    if argv[0] == "status":
        return status(c)

    def interrupted(signum, frame):
        raise InterruptedError("interrupted")

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        return Job(c).perform()
    except (OSError, ValueError, KeyError, TypeError):
        print("step=lock-or-startup failed=1")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
