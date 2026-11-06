#!/usr/bin/env python3
"""Fast stdlib contracts; synthetic files and intercepted command boundaries only."""

import argparse
import contextlib
import fcntl
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HERE / name)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


b = module("backup-snapshot.py")
r = module("verify-restore.py")
CALLERS = ["backup", "configure-db.sh", "provision-db-tls.sh", "restore", "gate"]


class Locks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="birja-backup-test-")
        self.root = Path(self.tmp.name)
        (self.root / "state").mkdir(mode=0o700)
        self.lock = self.root / "operation.lock"
        self.parent = self.lock.open("w")
        self.lock.chmod(0o600)
        self.roles = self.root / "roles.json"
        self.roles.write_text(
            json.dumps(
                {
                    "project": "birja-ops-test",
                    "db_name": "birja_source_test",
                    "bootstrap": r.BOOT,
                    "password_files": {
                        k: str(self.root / k) for k in ["app", "scheduler", "migrator"]
                    },
                }
            )
        )
        self.roles.chmod(0o600)

    def tearDown(self):
        self.parent.close()
        self.tmp.cleanup()

    def caller(self, name, inherited=True):
        code = """import runpy,sys,os
from pathlib import Path
m=runpy.run_path(sys.argv[1],run_name='contract')
t=m['Locks']();t.root=Path(sys.argv[2]);t.roles=t.root/'roles.json'
t.parent=os.fdopen(int(sys.argv[3]),'a')
try:
 t._caller(sys.argv[4],sys.argv[5]=='True')
 print('RESULT:ok')
except BaseException as error:
 print('RESULT:'+type(error).__name__)
"""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                code,
                __file__,
                str(self.root),
                str(self.parent.fileno()),
                name,
                str(inherited),
            ],
            check=False,
            pass_fds=(self.parent.fileno(),),
            capture_output=True,
            timeout=10,
        )
        outcome = result.stdout.decode().rsplit("RESULT:", 1)[-1].strip()
        if outcome != "ok":
            raise {
                "BlockingIOError": BlockingIOError,
                "FileNotFoundError": FileNotFoundError,
            }.get(outcome, ValueError)(outcome)

    def _caller(self, name, inherited=True):
        env = {"BIRJA_BACKUP_LOCK_FD": str(self.parent.fileno())} if inherited else {}
        with patch.dict(os.environ, env, clear=True):
            if name in ["backup", "restore", "gate"]:
                c = {
                    "_synthetic": True,
                    "_config_root": str(self.root),
                    "state_dir": str(self.root / "state"),
                    "password_file": "unused",
                    "repository": "unused",
                    "source_project": "birja-ops-test",
                    "docker_binary": "/usr/bin/docker",
                }
                if name == "backup":
                    with b.Job(c).lock():
                        return
                c.update(db_user=r.BOOT, db_name="birja_source_test")
                with (
                    patch.object(
                        b,
                        "recovery_binding",
                        side_effect=RuntimeError("reached locked boundary"),
                    ),
                    patch.object(b, "load_config", return_value=c),
                    patch.object(r, "backup_module", return_value=b),
                ):
                    try:
                        if name == "restore":
                            r.restore(
                                [
                                    "--synthetic",
                                    str(self.root / "config"),
                                    "--snapshot",
                                    "a" * 64,
                                ]
                            )
                        else:
                            b.recovery_gate(c, "a" * 64, {})
                    except RuntimeError as error:
                        assert str(error) == "reached locked boundary"
                        return
                raise AssertionError("boundary not reached")
            source = (
                (HERE / name).read_text().split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
            )
            source = source.rsplit("\ntry:\n    main()", 1)[0]
            scope = {"__name__": "contract"}
            exec(compile(source, name, "exec"), scope)  # noqa: S102 - execute reviewed embedded Python in child only
            args = (
                ["script", str(HERE), "--synthetic", str(self.roles), "--inspect"]
                if name == "configure-db.sh"
                else ["script", str(HERE), "--synthetic", str(self.root), "--check"]
            )
            scope["check"] = lambda *args: None
            with (
                patch.object(sys, "argv", args),
                patch.object(
                    subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess([], 0, b"", b""),
                ),
            ):
                scope["main"]()

    def test_held_parent_reused_by_actual_callers(self):
        fcntl.flock(self.parent, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for caller in CALLERS:
            with self.subTest(caller=caller):
                self.caller(caller)
                with self.lock.open("w") as other, self.assertRaises(BlockingIOError):
                    fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_unheld_and_shared_descriptor_rejected_before_commands(self):
        for mode in [None, fcntl.LOCK_SH]:
            if mode:
                fcntl.flock(self.parent, mode)
            for caller in CALLERS:
                with (
                    self.subTest(mode=mode, caller=caller),
                    self.assertRaises((ValueError, OSError)),
                ):
                    self.caller(caller)

    def test_independent_callers_contend_on_parent(self):
        fcntl.flock(self.parent, fcntl.LOCK_EX)
        for caller in CALLERS:
            with self.subTest(caller=caller), self.assertRaises(BlockingIOError):
                self.caller(caller, False)

    def test_wrong_inode_symlink_and_unsafe_mode_rejected(self):
        fcntl.flock(self.parent, fcntl.LOCK_EX)
        self.lock.rename(self.root / "original")
        self.lock.touch(mode=0o600)
        for mutation in ["inode", "symlink", "mode"]:
            if mutation == "symlink":
                self.lock.unlink()
                self.lock.symlink_to(self.root / "original")
            elif mutation == "mode":
                self.lock.unlink()
                (self.root / "original").rename(self.lock)
                self.lock.chmod(0o666)
            for caller in CALLERS:
                with (
                    self.subTest(mutation=mutation, caller=caller),
                    self.assertRaises((ValueError, OSError)),
                ):
                    self.caller(caller)

    def test_closed_descriptor_and_foreign_owner_are_rejected(self):
        closed = os.dup(self.parent.fileno())
        os.close(closed)
        with self.assertRaises(OSError):
            b.acquire_operation_lock(self.lock, str(closed))
        fcntl.flock(self.parent, fcntl.LOCK_EX)
        with (
            patch.object(b.os, "geteuid", return_value=os.geteuid() + 1),
            self.assertRaises(ValueError),
        ):
            b.acquire_operation_lock(self.lock, str(self.parent.fileno()))


class Evidence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="birja-backup-test-")
        self.root = Path(self.tmp.name)
        self.state = self.root / "state"
        self.state.mkdir(mode=0o700)
        self.sid = "a" * 64
        self.remote_calls = []
        self.manifest = {
            "archive_sha256": hashlib.sha256(b"PGDMPtest").hexdigest(),
            "release": "1" * 40,
            "revision": "0007",
        }
        self.c = {
            "_synthetic": True,
            "_config_root": str(self.root),
            "state_dir": str(self.state),
            "password_file": str(self.root / "password"),
            "repository": str(self.root / "repository"),
            "source_project": "birja-ops-test",
            "docker_binary": str(self.root / "docker"),
            "restic_binary": str(self.root / "restic"),
            "release": "1" * 40,
            "db_user": r.BOOT,
            "db_name": "birja_source_test",
            "max_stage_bytes": 10000,
            "freshness_seconds": 93600,
            "timeout_seconds": 10,
            "quota": {},
            "recovery_files": [],
        }
        for name in ["password", "docker", "restic"]:
            (self.root / name).write_text("synthetic-only")
            (self.root / name).chmod(0o600)
        self.metadata = [
            {
                "id": self.sid,
                "hostname": b.HOST,
                "tags": [b.TAG],
                "paths": [str(self.state / "stage/backup")],
                "time": b.utc(),
            }
        ]

    def tearDown(self):
        self.tmp.cleanup()

    def remote(self, job, *args, **kwargs):
        self.remote_calls.append(args[0])
        if args[0] == "snapshots":
            return json.dumps(self.metadata).encode()
        if args[0] == "restore":
            target = Path(args[args.index("--target") + 1])
            for name, data in [
                ("database.dump", b"PGDMPtest"),
                ("manifest.json", json.dumps(self.manifest).encode()),
                ("recovery.tar", b"material"),
            ]:
                (target / name).write_bytes(data)
        if args[0] == "dump":
            return json.dumps(self.manifest).encode()
        return b""

    def run_restore(self, failure=None, *, actual_preflight=False, clock=None):
        def verified(*args):
            if failure == "verify":
                raise ValueError("synthetic verification failure")
            if clock is not None:
                clock[0] += 301

        with (
            patch.object(r, "backup_module", return_value=b),
            patch.object(b, "load_config", return_value=self.c),
            patch.object(
                b.Job,
                "restic",
                lambda job, *args, **kwargs: self.remote(job, *args, **kwargs),
            ),
            contextlib.nullcontext()
            if actual_preflight
            else patch.object(b.Job, "quota"),
            contextlib.nullcontext()
            if actual_preflight
            else patch.object(b.Job, "refresh_quota"),
            patch.object(r, "check_running"),
            patch.object(r, "restored", return_value=contextlib.nullcontext()),
            patch.object(r, "verify", side_effect=verified),
        ):
            r.restore(
                ["--synthetic", str(self.root / "config"), "--snapshot", self.sid]
            )

    def test_delayed_gate_and_long_restore_refresh_without_rotating_evidence(self):
        clock = [int(time.time())]
        self.c["timeout_seconds"] = 3600
        self.c["quota"] = {
            "observed_at": clock[0] - 301,
            "storage_limit_bytes": 100000000,
            "visible_bytes": 0,
            "hidden_bytes": 0,
            "unfinished_bytes": 0,
            "other_bytes": 0,
            "upload_reserve_bytes": 1000000,
            "repack_reserve_bytes": 1000000,
            "download_remaining_bytes": 10000000,
            "request_remaining": 1000,
            "request_reserve": 1,
            "free_controls_verified": True,
            "dedicated_repository": True,
        }
        Path(self.c["repository"]).mkdir(mode=0o700)
        b.atomic(
            self.root / "config",
            {k: v for k, v in self.c.items() if not k.startswith("_")},
        )
        binding = {**b.recovery_binding(self.c), "bundle_sha256": "c" * 64}
        self.manifest.update(
            source_binding=binding,
            recovery_sha256=b.sha_bytes(b"material"),
            data_epoch=clock[0],
            data_utc=b.utc(clock[0]),
            started_utc=b.utc(clock[0]),
        )
        backup = {
            "ok": True,
            "run_id": "backup",
            "snapshot_id": self.sid,
            "data_epoch": clock[0],
            "data_utc": b.utc(clock[0]),
            "epoch": clock[0],
            "utc": b.utc(clock[0]),
        }
        for name in ["last-attempt.json", "last-success.json"]:
            b.atomic(self.state / name, backup)
        expected = {
            **binding,
            "source_release": self.manifest["release"],
            "source_revision": "0007",
        }
        with (
            patch.object(b.time, "time", side_effect=lambda: clock[0]),
            patch.object(b, "recovery_binding", return_value=binding),
        ):
            self.run_restore(actual_preflight=True, clock=clock)
            names = [
                "last-attempt.json",
                "last-success.json",
                "restore-last-attempt.json",
                "restore-last-success.json",
            ]
            records = {name: (self.state / name).read_bytes() for name in names}
            clock[0] += 301
            with patch.object(
                b.Job,
                "restic",
                lambda job, *args, **kwargs: self.remote(job, *args, **kwargs),
            ):
                self.assertTrue(
                    b.recovery_gate(self.c, self.sid, expected)["recovery_verified"]
                )
                self.assertEqual(self.c["quota"]["observed_at"], clock[0])
                Path(self.c["repository"]).rmdir()
                with self.assertRaises(ValueError):
                    b.recovery_gate(self.c, self.sid, expected)
            self.assertEqual(
                records, {name: (self.state / name).read_bytes() for name in names}
            )
        self.assertEqual(
            self.remote_calls, ["snapshots", "restore", "snapshots", "dump"]
        )

    def test_restore_publishes_private_attempt_and_success_after_cleanup(self):
        self.run_restore()
        attempt = json.loads((self.state / "restore-last-attempt.json").read_text())
        success = json.loads((self.state / "restore-last-success.json").read_text())
        self.assertTrue(attempt["ok"])
        self.assertEqual(attempt, success)
        self.assertEqual(success["snapshot_id"], self.sid)
        self.assertFalse(list(self.state.glob("restore-*/*")))
        self.assertEqual(
            (self.state / "restore-last-success.json").stat().st_mode & 0o077, 0
        )

    def test_failed_latest_restore_invalidates_previous_success(self):
        self.run_restore()
        with self.assertRaises(ValueError):
            self.run_restore("verify")
        attempt = json.loads((self.state / "restore-last-attempt.json").read_text())
        success = json.loads((self.state / "restore-last-success.json").read_text())
        self.assertFalse(attempt["ok"])
        self.assertNotEqual(attempt["run_id"], success["run_id"])

    def test_gate_rechecks_exact_remote_presence_and_all_bindings(self):
        self.run_restore()
        success = json.loads((self.state / "restore-last-success.json").read_text())
        binding = b.recovery_binding(self.c)
        binding["bundle_sha256"] = "c" * 64
        self.manifest.update(
            data_epoch=success["started_epoch"],
            data_utc=b.utc(success["started_epoch"]),
            started_utc=b.utc(success["started_epoch"]),
            source_binding=binding,
            recovery_sha256=success["recovery_sha256"],
        )
        success.update(
            binding, manifest_sha256=b.sha_bytes(json.dumps(self.manifest).encode())
        )
        expected = {
            **binding,
            "source_release": self.manifest["release"],
            "source_revision": "0007",
        }
        backup = {
            "ok": True,
            "run_id": "backup",
            "snapshot_id": self.sid,
            "data_epoch": success["started_epoch"],
            "data_utc": b.utc(success["started_epoch"]),
            "epoch": success["started_epoch"],
            "utc": b.utc(success["started_epoch"]),
        }
        for name in ["last-success.json", "last-attempt.json"]:
            b.atomic(self.state / name, backup)
        for name in ["restore-last-success.json", "restore-last-attempt.json"]:
            b.atomic(self.state / name, success)
        with (
            patch.object(b, "recovery_binding", return_value=binding),
            patch.object(b.Job, "quota"),
            patch.object(b.Job, "refresh_quota"),
            patch.object(
                b.Job,
                "restic",
                lambda job, *args, **kwargs: self.remote(job, *args, **kwargs),
            ),
        ):
            self.assertTrue(
                b.recovery_gate(self.c, self.sid, expected)["recovery_verified"]
            )
            # The point is fresh on entry and can expire during either native
            # inventory refresh or the final authenticated manifest retrieval.
            entry = int(time.time())
            near = {
                **backup,
                "data_epoch": entry - 93590,
                "data_utc": b.utc(entry - 93590),
            }
            original_manifest = dict(self.manifest)
            self.manifest.update(
                data_epoch=near["data_epoch"],
                data_utc=near["data_utc"],
                started_utc=near["data_utc"],
            )
            near_success = {
                **success,
                "manifest_sha256": b.sha_bytes(json.dumps(self.manifest).encode()),
            }
            for name in ["last-success.json", "last-attempt.json"]:
                b.atomic(self.state / name, near)
            for name in ["restore-last-success.json", "restore-last-attempt.json"]:
                b.atomic(self.state / name, near_success)
            for boundary, delay, allowed in [
                ("refresh", 20, False),
                ("dump", 20, False),
                ("dump", 9, True),
                ("dump", 10, True),
            ]:
                clock = [entry]

                def refresh(job, lock, *, boundary=boundary, clock=clock, delay=delay):
                    if boundary == "refresh":
                        clock[0] += delay

                def remote(
                    job, *args, boundary=boundary, clock=clock, delay=delay, **kwargs
                ):
                    value = self.remote(job, *args, **kwargs)
                    if boundary == args[0] == "dump":
                        clock[0] += delay
                    return value

                with (
                    self.subTest(boundary=boundary, delay=delay),
                    patch.object(
                        b.time, "time", side_effect=lambda clock=clock: clock[0]
                    ),
                    patch.object(b.Job, "refresh_quota", refresh),
                    patch.object(b.Job, "restic", remote),
                ):
                    if allowed:
                        self.assertTrue(
                            b.recovery_gate(self.c, self.sid, expected)[
                                "recovery_verified"
                            ]
                        )
                    else:
                        with self.assertRaises(ValueError):
                            b.recovery_gate(self.c, self.sid, expected)
            self.manifest = original_manifest
            for name in ["last-success.json", "last-attempt.json"]:
                b.atomic(self.state / name, backup)
            for name in ["restore-last-success.json", "restore-last-attempt.json"]:
                b.atomic(self.state / name, success)
            stale_data = {
                **backup,
                "data_epoch": backup["epoch"] - 97000,
                "data_utc": b.utc(backup["epoch"] - 97000),
            }
            for name in ["last-success.json", "last-attempt.json"]:
                b.atomic(self.state / name, stale_data)
            with self.assertRaises(ValueError):
                b.recovery_gate(self.c, self.sid, expected)
            for name in ["last-success.json", "last-attempt.json"]:
                b.atomic(self.state / name, backup)
            self.manifest["data_epoch"] -= 1
            changed = {
                **success,
                "manifest_sha256": b.sha_bytes(json.dumps(self.manifest).encode()),
            }
            for name in ["restore-last-success.json", "restore-last-attempt.json"]:
                b.atomic(self.state / name, changed)
            with self.assertRaises(ValueError):
                b.recovery_gate(self.c, self.sid, expected)
            self.manifest["data_epoch"] += 1
            for name in ["restore-last-success.json", "restore-last-attempt.json"]:
                b.atomic(self.state / name, success)
            for key in expected:
                wrong = {**expected, key: "wrong"}
                with self.subTest(key=key), self.assertRaises(ValueError):
                    b.recovery_gate(self.c, self.sid, wrong)
            for key, value in [
                ("ok", False),
                ("run_id", "failed"),
                ("completed_epoch", int(time.time()) + 100),
                ("started_epoch", int(time.time()) - 93601),
                ("snapshot_id", "b" * 64),
            ]:
                b.atomic(
                    self.state / "restore-last-attempt.json", {**success, key: value}
                )
                with self.subTest(state=key), self.assertRaises(ValueError):
                    b.recovery_gate(self.c, self.sid, expected)
            b.atomic(self.state / "restore-last-attempt.json", success)
            self.metadata = []
            with self.assertRaises(ValueError):
                b.recovery_gate(self.c, self.sid, expected)
            self.metadata = [
                {
                    "id": self.sid,
                    "hostname": b.HOST,
                    "tags": [b.TAG],
                    "paths": [str(self.state / "stage/backup")],
                    "time": "2099-01-01T00:00:00Z",
                }
            ]
            with self.assertRaises(ValueError):
                b.recovery_gate(self.c, self.sid, expected)
        # Noninstalled code cannot turn local successful restore into rollout authority.
        with self.assertRaises(ValueError):
            b.recovery_gate(self.c, self.sid, expected)

    def test_ordinary_nightly_status_does_not_require_full_restore(self):
        now = int(time.time())
        backup = {
            "ok": True,
            "run_id": "nightly",
            "snapshot_id": self.sid,
            "data_epoch": now,
            "data_utc": b.utc(now),
            "epoch": now,
            "utc": b.utc(),
        }
        for name in ["last-success.json", "last-attempt.json"]:
            b.atomic(self.state / name, backup)
        self.assertEqual(b.status(self.c), 0)
        for change in [
            {
                "data_epoch": now - 97000,
                "data_utc": b.utc(now - 97000),
                "epoch": now - 93500,
                "utc": b.utc(now - 93500),
            },
            {"data_epoch": now + 1},
            {"data_utc": "wrong"},
            {"data_epoch": None},
        ]:
            for name in ["last-success.json", "last-attempt.json"]:
                b.atomic(self.state / name, {**backup, **change})
            self.assertEqual(b.status(self.c), 1)
        with self.assertRaises(ValueError):
            b.recovery_gate(self.c, self.sid, {})

    def test_isolated_clone_cleanup_failure_invalidates_attempt(self):
        def call(argv, *args, **kwargs):
            if "down" in argv:
                raise OSError("synthetic server cleanup failure")
            return b""

        with (
            patch.object(r, "backup_module", return_value=b),
            patch.object(b, "load_config", return_value=self.c),
            patch.object(
                b.Job,
                "restic",
                lambda job, *args, **kwargs: self.remote(job, *args, **kwargs),
            ),
            patch.object(b.Job, "quota"),
            patch.object(b.Job, "refresh_quota"),
            patch.object(r, "check_running"),
            patch.object(r, "restored", return_value=contextlib.nullcontext()),
            patch.object(r, "verify"),
            patch.object(r, "call", side_effect=call),
            self.assertRaises(OSError),
        ):
            r.restore(
                [
                    "--synthetic",
                    str(self.root / "config"),
                    "--snapshot",
                    self.sid,
                    "--isolated-clone",
                ]
            )
        self.assertFalse((self.state / "restore-last-success.json").exists())
        self.assertFalse(
            json.loads((self.state / "restore-last-attempt.json").read_text())["ok"]
        )

    def test_config_identity_excludes_quota_observation_but_binds_material(self):
        before = b.config_digest(self.c)
        self.c["quota"].update(observed_at=42, request_remaining=5, visible_bytes=100)
        self.assertEqual(b.config_digest(self.c), before)
        (self.root / "password").write_text("changed")
        self.assertNotEqual(b.config_digest(self.c), before)

    def test_cleanup_failure_and_interrupt_do_not_publish_success(self):
        self.run_restore()

        @contextlib.contextmanager
        def cleanup_failure(*args):
            try:
                yield
            finally:
                raise OSError("synthetic teardown failure")

        for failure in [
            InterruptedError("synthetic interruption"),
            OSError("synthetic cleanup"),
        ]:
            with (
                patch.object(r, "backup_module", return_value=b),
                patch.object(b, "load_config", return_value=self.c),
                patch.object(
                    b.Job,
                    "restic",
                    lambda job, *args, **kwargs: self.remote(job, *args, **kwargs),
                ),
                patch.object(b.Job, "quota"),
                patch.object(b.Job, "refresh_quota"),
                patch.object(r, "check_running"),
                patch.object(
                    r,
                    "restored",
                    side_effect=cleanup_failure
                    if isinstance(failure, OSError)
                    and not isinstance(failure, InterruptedError)
                    else lambda *args: contextlib.nullcontext(),
                ),
                patch.object(
                    r,
                    "verify",
                    side_effect=None if type(failure) is OSError else failure,
                ),
                self.assertRaises(type(failure)),
            ):
                r.restore(
                    [
                        "--synthetic",
                        str(self.root / "config"),
                        "--snapshot",
                        self.sid,
                    ]
                )
            self.assertFalse(
                json.loads((self.state / "restore-last-attempt.json").read_text())["ok"]
            )


class Fixtures(unittest.TestCase):
    def test_authentic_legacy_selection_rejects_before_runtime_or_docker(self):
        spec = importlib.util.spec_from_file_location(
            "fixture", HERE / "tests/ops-fixtures.py"
        )
        ops = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ops)
        with tempfile.TemporaryDirectory(prefix="birja-backup-test-") as tmp:
            root = Path(tmp)
            image_config = b"{}"
            image_id = "sha256:" + hashlib.sha256(image_config).hexdigest()
            image = io.BytesIO()
            with tarfile.open(fileobj=image, mode="w") as tar:
                info = tarfile.TarInfo(image_id[7:] + ".json")
                info.size = len(image_config)
                tar.addfile(info, io.BytesIO(image_config))
            files = {
                name: (HERE.parent / name).read_bytes() for name in r.CORE + r.UNITS
            }
            tools = Path("/tmp/birja-test-tools/restic-0.19.1")
            files["tools/restic"] = (tools / "restic").read_bytes()
            for name in r.PROVENANCE:
                files["provenance/" + name] = (tools / name).read_bytes()
            files["provenance/verified.json"] = json.dumps(
                {
                    "fingerprint": "CF8F18F2844575973F79D4E191A6868BD3F7A907",
                    "binary_sha256": r.RESTIC_SHA,
                    "compressed_sha256": "f415415624dcc452f2a02b8c33641791a8c6d6d3b65bbb3543fcf9a25151585c",
                    "signature": "GOODSIG VALIDSIG; verified 2026-11-02; official restic 0.19.1 linux amd64",
                }
            ).encode()
            files["images/postgres.tar"] = image.getvalue()
            inventory = {
                "format": 1,
                "files": sorted(files),
                "units": r.UNITS,
                "image_id": image_id,
                "restic_sha256": r.RESTIC_SHA,
                "recovery_profile": "legacy-v1",
            }
            archive = root / "legacy.tar"

            def build(profile):
                if profile is None:
                    inventory.pop("recovery_profile", None)
                else:
                    inventory["recovery_profile"] = profile
                files.pop("SHA256SUMS", None)
                files["INVENTORY.json"] = json.dumps(inventory).encode()
                files["SHA256SUMS"] = "".join(
                    hashlib.sha256(data).hexdigest() + "  " + name + "\n"
                    for name, data in sorted(files.items())
                ).encode()
                with tarfile.open(archive, "w") as tar:
                    for name, data in sorted(files.items()):
                        info = tarfile.TarInfo(name)
                        info.mode = 0o600
                        info.size = len(data)
                        tar.addfile(info, io.BytesIO(data))
                archive.chmod(0o600)
                sha = r.digest(archive)
                archive.with_suffix(".tar.sha256").write_text(sha)
                archive.with_suffix(".tar.sha256").chmod(0o600)
                return sha

            sha = build("legacy-v1")
            # Only the synthetic image's trusted identity is substituted. The
            # real approved restic/provenance and every archive checksum pass.
            with (
                patch.object(ops, "r", r),
                patch.object(r, "IMAGE_ID", image_id),
                patch.object(r, "runtime", return_value={}) as runtime,
                patch.object(
                    r, "call", side_effect=AssertionError("Docker reached")
                ) as calls,
                patch.object(
                    r,
                    "bundle_package",
                    side_effect=AssertionError("fallback builder reached"),
                ) as builder,
            ):
                self.assertEqual(
                    r.bundle_verify(archive, sha)["recovery_profile"], "legacy-v1"
                )
                for profile in ["legacy-v1", None, "unknown-v99"]:
                    sha = build(profile)
                    r.bundle_verify(archive, sha)  # Generic legacy compatibility.
                    runtime.reset_mock()
                    with self.assertRaises(ValueError):
                        ops.roundtrip(str(archive))
                    with self.assertRaises(ValueError):
                        r.bundle_install(
                            archive,
                            sha,
                            str(root / "host"),
                            required_profile="deploy-recovery-v2",
                        )
                    runtime.assert_not_called()
                    calls.assert_not_called()
                    builder.assert_not_called()
                sha = build("deploy-recovery-v2")
                self.assertEqual(
                    r.bundle_verify(
                        archive, sha, required_profile="deploy-recovery-v2"
                    )["recovery_profile"],
                    "deploy-recovery-v2",
                )

    def test_repeated_hook_uses_same_installed_launchers_and_separate_clone(self):
        spec = importlib.util.spec_from_file_location(
            "fixture", HERE / "tests/ops-fixtures.py"
        )
        ops = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ops)
        with tempfile.TemporaryDirectory(prefix="birja-backup-test-") as tmp:
            root = Path(tmp)
            (root / "state").mkdir(mode=0o700)
            config = root / "config"
            config.write_text(json.dumps({"release": "1" * 40, "quota": {}}))
            config.chmod(0o600)
            session = __import__("types").SimpleNamespace(
                root=root,
                tools=root / "tools",
                release=root / "release",
                archive_sha="a" * 64,
                config_path=config,
                immutable={config: r.digest(config)},
            )
            # Config is per-attempt state; immutable code/launchers are distinct.
            marker = root / "launcher"
            marker.write_bytes(b"immutable installed launcher")
            session.immutable = {marker: r.digest(marker)}
            calls = []

            def target(root, argv):
                calls.append(argv)
                if Path(argv[0]).name == "birja-backup":
                    b.atomic(
                        root / "state/last-success.json", {"snapshot_id": "b" * 64}
                    )

            with (
                patch.object(ops, "target", side_effect=target),
                patch.object(
                    ops.r,
                    "call",
                    side_effect=AssertionError("source lifecycle reached"),
                ),
            ):
                for revision in ["0007", "0008"]:
                    self.assertEqual(
                        ops.recovery_roundtrip(
                            session, source_revision=revision, source_release="1" * 40
                        ),
                        "b" * 64,
                    )
            self.assertEqual(len(calls), 8)
            self.assertTrue(
                all(
                    "--isolated-clone" in argv
                    for argv in calls
                    if Path(argv[0]).name == "birja-restore-check"
                )
            )
            self.assertTrue(
                all(
                    str(session.release / "deploy/backup-snapshot.py") in argv
                    for argv in calls
                    if "recovery-gate" in argv
                )
            )
            self.assertEqual(r.digest(marker), session.immutable[marker])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ["locks", "evidence", "fixtures"]:
        parser.add_argument("--" + name, action="store_true")
    options = parser.parse_args()
    selected = [
        c
        for name, c in [
            ("locks", Locks),
            ("evidence", Evidence),
            ("fixtures", Fixtures),
        ]
        if getattr(options, name) or not any(vars(options).values())
    ]
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in selected
    )
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
