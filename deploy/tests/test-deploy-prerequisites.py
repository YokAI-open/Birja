#!/usr/bin/env python3
"""Fast stdlib contracts; synthetic files and intercepted command boundaries only."""

import argparse
import contextlib
import fcntl
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
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


class Evidence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="birja-backup-test-")
        self.root = Path(self.tmp.name)
        self.state = self.root / "state"
        self.state.mkdir(mode=0o700)
        self.sid = "a" * 64
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

    def run_restore(self, failure=None):
        def verified(*args):
            if failure == "verify":
                raise ValueError("synthetic verification failure")

        with (
            patch.object(r, "backup_module", return_value=b),
            patch.object(b, "load_config", return_value=self.c),
            patch.object(
                b.Job,
                "restic",
                lambda job, *args, **kwargs: self.remote(job, *args, **kwargs),
            ),
            patch.object(b.Job, "quota"),
            patch.object(r, "check_running"),
            patch.object(r, "restored", return_value=contextlib.nullcontext()),
            patch.object(r, "verify", side_effect=verified),
        ):
            r.restore(
                ["--synthetic", str(self.root / "config"), "--snapshot", self.sid]
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
            source_binding=binding, recovery_sha256=success["recovery_sha256"]
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
            "epoch": success["started_epoch"],
        }
        for name in ["last-success.json", "last-attempt.json"]:
            b.atomic(self.state / name, backup)
        for name in ["restore-last-success.json", "restore-last-attempt.json"]:
            b.atomic(self.state / name, success)
        with (
            patch.object(b, "recovery_binding", return_value=binding),
            patch.object(b.Job, "quota"),
            patch.object(
                b.Job,
                "restic",
                lambda job, *args, **kwargs: self.remote(job, *args, **kwargs),
            ),
        ):
            self.assertTrue(
                b.recovery_gate(self.c, self.sid, expected)["recovery_verified"]
            )
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ["locks", "evidence", "fixtures"]:
        parser.add_argument("--" + name, action="store_true")
    options = parser.parse_args()
    selected = [
        c
        for name, c in [("locks", Locks), ("evidence", Evidence)]
        if getattr(options, name) or not any(vars(options).values())
    ]
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in selected
    )
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
