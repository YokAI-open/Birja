#!/usr/bin/env python3
"""Private, stdlib-only isolated recovery tooling."""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
COMPOSE_SHA = "91af78e11963a7a8f944e1807b310193e1ea1da676b74beab2e667b5e841c7f0"
BOOT = "birja_ops_bootstrap"
CLONE = "birja_restore_test"


def require(value):
    if not value:
        raise ValueError("recovery guard")


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def private(path, directory=False):
    p = Path(path)
    require(p.is_absolute() and p == p.resolve())
    for component in [p, *p.parents]:
        require(not component.is_symlink())
    s = p.stat()
    require(s.st_uid == os.geteuid() and s.st_mode & 0o077 == 0)
    require(stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode))
    return p


def backup_module():
    spec = importlib.util.spec_from_file_location("backup_private", HERE / "backup-snapshot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compose(project="birja-ops-test"):
    require(project in {"birja-ops-test", "birja-restore-check"})
    path = HERE.parent / "docker-compose.ops-test.yml"
    require(digest(path) == COMPOSE_SHA)
    return ["/usr/bin/docker", "compose", "--env-file", "/dev/null", "-p", project, "-f", str(path)]


ENV = {"PATH": "/usr/bin:/bin", "HOME": "/tmp", "LANG": "C.UTF-8"}


def call(argv, data=None, timeout=120):
    r = subprocess.run(argv, input=data, capture_output=True, env=ENV, timeout=timeout)
    require(r.returncode == 0)
    return r.stdout


def sql(dc, query, db=CLONE):
    require(db in {CLONE, "birja_source_test", "birja_ops_test"})
    return call(dc + ["exec", "-T", "postgres", "psql", "-XqAt", "-v", "ON_ERROR_STOP=1", "-U", BOOT, "-d", db], query.encode())


def check_running(dc):
    config = json.loads(call(dc + ["config", "--format", "json"]))
    require(set(config["services"]) == {"postgres"} and not config.get("volumes"))
    s = config["services"]["postgres"]
    require(not s.get("ports") and not s.get("volumes") and not s.get("privileged"))
    require(s["image"] == "postgres:18.6-trixie")
    require(len(config["networks"]) == 1 and all(n.get("internal") is True for n in config["networks"].values()))
    ids = call(dc + ["ps", "-q", "postgres"]).decode().split()
    require(len(ids) == 1)
    inspected = json.loads(call(["/usr/bin/docker", "inspect", ids[0]]))[0]
    require(not inspected["HostConfig"]["Privileged"])
    require(not inspected["HostConfig"].get("Binds") and not inspected["HostConfig"].get("PortBindings"))
    mounts = inspected["Mounts"]
    require(not mounts and inspected["HostConfig"]["Tmpfs"] == {"/var/lib/postgresql": "size=268435456"})
    networks = inspected["NetworkSettings"]["Networks"]
    require(len(networks) == 1)
    network = json.loads(call(["/usr/bin/docker", "network", "inspect", next(iter(networks))]))[0]
    require(network["Internal"] is True)


def canonical(dc, db=CLONE):
    return json.loads(sql(dc, "SET TIME ZONE 'UTC';\n" + (HERE / "backup-manifest.sql").read_text(), db))


def verify(dc, manifest):
    actual = canonical(dc)
    require(all(actual[k] == manifest[k] for k in ["tables", "financial", "revision"]))
    require(all(actual["financial"][k] == 0 for k in ["negative_cash", "fractional_cents", "negative_holdings"]))
    # Compare complete constraint/index definitions against the reviewed schema
    # captured independently by fixture tests; additionally require core invariants.
    constraints = sql(dc, "SELECT count(*) FROM pg_constraint WHERE connamespace='public'::regnamespace AND contype='f' AND convalidated;").strip()
    require(constraints == b"9")
    require(sql(dc, "SELECT count(*) FROM pg_index WHERE indrelid IN (SELECT oid FROM pg_class WHERE relnamespace='public'::regnamespace) AND (NOT indisvalid OR NOT indisready);").strip() == b"0")
    expected = "ix_trades_user_id" if manifest["revision"] == "0007" else "ix_trades_user_created_id"
    require(sql(dc, f"SELECT to_regclass('{expected}') IS NOT NULL;").strip() == b"t")
    require(sql(dc, "SELECT count(*) FROM pg_constraint WHERE contype='c' AND connamespace='public'::regnamespace;").strip() == b"25")
    # Check identity progression without consuming sequence values. MVCC sequence
    # state need not equal the source; every future generated id must be safe.
    for table in ["users", "accounts", "auth_sessions", "refresh_tokens", "coins", "holdings", "trades"]:
        sequence = f"{table}_id_seq"
        require(sql(dc, f"SELECT (CASE WHEN is_called THEN last_value+1 ELSE last_value END) > coalesce((SELECT max(id) FROM {table}),0) FROM {sequence};").strip() == b"t")
    print("equality=true invariants=true identities=true")


@contextlib.contextmanager
def restored(dc, dump):
    created = False
    try:
        require(sql(dc, f"SELECT NOT EXISTS(SELECT FROM pg_database WHERE datname='{CLONE}');", "birja_ops_test").strip() == b"t")
        sql(dc, "DO $$BEGIN IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='birja_migrator') THEN CREATE ROLE birja_migrator NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION; END IF; END$$;", "birja_ops_test")
        require(sql(dc, "SELECT NOT (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls) FROM pg_roles WHERE rolname='birja_migrator';", "birja_ops_test").strip() == b"t")
        sql(dc, f"CREATE DATABASE {CLONE} OWNER birja_migrator TEMPLATE template0;", "birja_ops_test")
        created = True
        call(dc + ["exec", "-T", "postgres", "pg_restore", "--list"], dump)
        call(dc + ["exec", "-T", "postgres", "pg_restore", "-U", BOOT, "-d", CLONE, "--no-owner", "--no-acl", "--role=birja_migrator", "--exit-on-error", "--single-transaction"], dump)
        yield
    finally:
        if created:
            sql(dc, f"DROP DATABASE {CLONE} WITH (FORCE);", "birja_ops_test")


def restore(args):
    # No operational env override is accepted, including ambient Compose options.
    require(not any(k in os.environ for k in ["COMPOSE_FILE", "COMPOSE_PROJECT_NAME", "DOCKER_HOST", "DATABASE_URL", "PGUSER", "PGDATABASE", "PGHOST", "APP_DIR"]))
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic")
    parser.add_argument("--approved-clone", action="store_true")
    parser.add_argument("--snapshot", required=True)
    a = parser.parse_args(args)
    require(re.fullmatch(r"[0-9a-f]{64}", a.snapshot))
    require(bool(a.synthetic) != a.approved_clone)
    b = backup_module()
    c = b.load_config(["--synthetic", a.synthetic] if a.synthetic else [])
    if a.synthetic:
        require(c["db_user"] == BOOT and c["db_name"] == "birja_source_test")
    dc = compose("birja-ops-test" if a.synthetic else "birja-restore-check")
    job = b.Job(c)
    job.state.mkdir(mode=0o700, parents=True, exist_ok=True)
    b.private_dir(job.state)
    with job.lock():
        check_running(dc)
        snapshots = json.loads(job.restic("snapshots", a.snapshot))
        require(job.check_scope(snapshots) == [a.snapshot])
        with tempfile.TemporaryDirectory(prefix="restore-", dir=job.state) as tmp:
            target = Path(tmp)
            job.restic("restore", a.snapshot, "--target", str(target), "--verify")
            require({p.name for p in target.iterdir()} == {"database.dump", "manifest.json", "recovery.tar"})
            for p in target.iterdir():
                require(p.is_file() and not p.is_symlink() and p.stat().st_size <= c["max_stage_bytes"])
            manifest = json.loads((target / "manifest.json").read_text())
            require(digest(target / "database.dump") == manifest["archive_sha256"])
            with restored(dc, (target / "database.dump").read_bytes()):
                verify(dc, manifest)


def main():
    os.umask(0o077)
    try:
        require(len(sys.argv) > 1)
        if sys.argv[1] == "restore":
            restore(sys.argv[2:])
        elif sys.argv[1] == "bundle":
            return 0
        else:
            raise ValueError("mode")
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError):
        print("recovery=false step=guard-or-verification", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
