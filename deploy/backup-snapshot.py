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
    c = json.loads(private_file(path).read_text())
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
    require(set(c) == expected)
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
    c["_synthetic"] = synthetic
    return c


def utc():
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


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
            else str(HERE.parent / "docker-compose.ops-test.yml"),
        ]
        if not c["_synthetic"]:
            self.dc += ["--env-file", "/etc/birja/prod.env"]
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
        lock = (
            (self.state / "operation.lock")
            if self.c["_synthetic"]
            else Path("/var/lock/birja-deploy.lock")
        )
        inherited = os.environ.get("BIRJA_BACKUP_LOCK_FD")
        if inherited is not None:
            require(inherited.isdigit() and 3 <= int(inherited) <= 1024)
            fd = int(inherited)
            require(os.path.samestat(os.fstat(fd), lock.stat()))
            info = Path(f"/proc/self/fdinfo/{fd}").read_text()
            require(
                any(
                    "FLOCK" in s and "WRITE" in s
                    for s in info.splitlines()
                    if s.startswith("lock:")
                )
            )
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return os.fdopen(os.dup(fd), "a")
        fd = os.open(lock, os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        f = os.fdopen(fd, "a")
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            f.close()
            raise
        return f

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
        require(argv and argv[0] in ["backup", "status"])
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
