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
            == "91af78e11963a7a8f944e1807b310193e1ea1da676b74beab2e667b5e841c7f0"
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
    require(path.is_absolute() and path == path.resolve())

    def validate(fd):
        current, held = path.lstat(), os.fstat(fd)
        require(stat.S_ISREG(current.st_mode) and stat.S_ISREG(held.st_mode))
        require(
            held.st_uid
            == (0 if path == Path("/var/lock/birja-deploy.lock") else os.geteuid())
        )
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
    with job.lock():
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
        job.quota()  # Revalidate fresh request/download allowances; no full blobs.
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
        return {
            "snapshot_id": snapshot_id,
            "recovery_verified": True,
            "completed_utc": success["completed_utc"],
        }


def status(c):
    try:
        state = private_dir(c["state_dir"])
        s = json.loads(private_file(state / "last-success.json").read_text())
        a = json.loads(private_file(state / "last-attempt.json").read_text())
        require(a["ok"] is True and a["run_id"] == s["run_id"])
        require(ID.fullmatch(s["snapshot_id"]))
        require(0 <= time.time() - s["epoch"] <= c["freshness_seconds"])
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
        self.started = time.monotonic()
        self.calls = 0
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

    def call(self, argv, *, data=None, input_file=None, output=None, cwd=None):
        self.calls += 1
        require(self.calls <= 20)
        left = self.c["timeout_seconds"] - (time.monotonic() - self.started)
        require(left > 0)
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
                preexec_fn=self.limit,
            )
            require(r.returncode == 0)
            if output is None:
                capture.seek(0)
                return capture.read()
        return b""

    def restic(self, *args, cwd=None):
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
                "1024",
                *args,
            ],
            cwd=cwd,
        )

    def quota(self):
        q = self.c["quota"]
        require(
            q["free_controls_verified"] is True and q["dedicated_repository"] is True
        )
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
        require(q["download_remaining_bytes"] >= self.c["max_stage_bytes"])
        require(q["request_remaining"] >= q["request_reserve"] >= 1000)
        require(shutil.disk_usage(self.state).free >= self.c["max_stage_bytes"] * 2)

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
            proc.stdin.write((HERE / "backup-manifest.sql").read_bytes() + b"\n")
            proc.stdin.flush()
            manifest = json.loads(self.line(proc))
            require(
                set(manifest["tables"])
                == {
                    "users",
                    "accounts",
                    "auth_sessions",
                    "refresh_tokens",
                    "coins",
                    "prices",
                    "holdings",
                    "trades",
                    "alembic_version",
                }
            )
            for row in manifest["tables"].values():
                require(type(row["count"]) is int and row["count"] >= 0)
                require(ID.fullmatch(row["sha256"]))
            for key in ["negative_cash", "fractional_cents", "negative_holdings"]:
                require(manifest["financial"][key] == 0)
            for key in [
                "cash",
                "starting_cash",
                "quantity",
                "cost_basis",
                "fees",
                "cash_delta",
            ]:
                require(Decimal(manifest["financial"][key]).is_finite())
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
            self.start_utc = utc()
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


def main(argv):
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
        c = load_config(argv[1:])
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
