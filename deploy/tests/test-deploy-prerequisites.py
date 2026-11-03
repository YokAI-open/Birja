#!/usr/bin/env python3
"""Fast stdlib contracts; synthetic files and intercepted command boundaries only."""

import argparse
import contextlib
import hashlib
import time
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
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


class Locks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="birja-backup-test-")
        self.root = Path(self.tmp.name)
        (self.root / "state").mkdir(mode=0o700)
        self.lock = self.root / "operation.lock"
        self.parent = self.lock.open("w")
        self.lock.chmod(0o600)
        self.roles = self.root / "roles.json"
        self.roles.write_text(json.dumps({"project": "birja-ops-test", "db_name": "birja_source_test", "bootstrap": r.BOOT, "password_files": {k: str(self.root / k) for k in ["app", "scheduler", "migrator"]}}))
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
        result = subprocess.run([sys.executable, "-c", code, __file__, str(self.root), str(self.parent.fileno()), name, str(inherited)], pass_fds=(self.parent.fileno(),), capture_output=True, timeout=10)
        outcome = result.stdout.decode().rsplit("RESULT:", 1)[-1].strip()
        if outcome != "ok":
            raise {"BlockingIOError": BlockingIOError, "FileNotFoundError": FileNotFoundError}.get(outcome, ValueError)(outcome)

    def _caller(self, name, inherited=True):
        env = {"BIRJA_BACKUP_LOCK_FD": str(self.parent.fileno())} if inherited else {}
        with patch.dict(os.environ, env, clear=True):
            if name == "backup":
                c = {"_synthetic": True, "_config_root": str(self.root), "state_dir": str(self.root / "state"), "password_file": "unused", "repository": "unused", "source_project": "birja-ops-test", "docker_binary": "/usr/bin/docker"}
                with b.Job(c).lock():
                    return
            source = (HERE / name).read_text().split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
            source = source.rsplit("\ntry:\n    main()", 1)[0]
            scope = {"__name__": "contract"}
            exec(compile(source, name, "exec"), scope)
            args = ["script", str(HERE), "--synthetic", str(self.roles), "--inspect"] if name == "configure-db.sh" else ["script", str(HERE), "--synthetic", str(self.root), "--check"]
            scope["check"] = lambda *args: None
            with patch.object(sys, "argv", args), patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b"", b"")):
                scope["main"]()

    def test_held_parent_reused_by_actual_callers(self):
        fcntl.flock(self.parent, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for caller in ["backup", "configure-db.sh", "provision-db-tls.sh"]:
            with self.subTest(caller=caller):
                self.caller(caller)
                with self.lock.open("w") as other:
                    with self.assertRaises(BlockingIOError):
                        fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_unheld_and_shared_descriptor_rejected_before_commands(self):
        for mode in [None, fcntl.LOCK_SH]:
            if mode:
                fcntl.flock(self.parent, mode)
            for caller in ["backup", "configure-db.sh", "provision-db-tls.sh"]:
                with self.subTest(mode=mode, caller=caller), self.assertRaises((ValueError, OSError)):
                    self.caller(caller)

    def test_independent_callers_contend_on_parent(self):
        fcntl.flock(self.parent, fcntl.LOCK_EX)
        for caller in ["backup", "configure-db.sh", "provision-db-tls.sh"]:
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
            for caller in ["backup", "configure-db.sh", "provision-db-tls.sh"]:
                with self.subTest(mutation=mutation, caller=caller), self.assertRaises((ValueError, OSError)):
                    self.caller(caller)


class Evidence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="birja-backup-test-")
        self.root = Path(self.tmp.name)
        self.state = self.root / "state"
        self.state.mkdir(mode=0o700)
        self.sid = "a" * 64
        self.manifest = {"archive_sha256": hashlib.sha256(b"PGDMPtest").hexdigest(), "release": "1" * 40, "revision": "0007"}
        self.c = {"_synthetic": True, "_config_root": str(self.root), "state_dir": str(self.state), "password_file": str(self.root / "password"), "repository": str(self.root / "repository"), "source_project": "birja-ops-test", "docker_binary": str(self.root / "docker"), "restic_binary": str(self.root / "restic"), "release": "1" * 40, "db_user": r.BOOT, "db_name": "birja_source_test", "max_stage_bytes": 10000, "freshness_seconds": 93600, "timeout_seconds": 10, "quota": {}, "recovery_files": []}
        self.metadata = [{"id": self.sid, "hostname": b.HOST, "tags": [b.TAG], "paths": [str(self.state / "stage/backup")], "time": b.utc()}]

    def tearDown(self):
        self.tmp.cleanup()

    def remote(self, job, *args, **kwargs):
        if args[0] == "snapshots":
            return json.dumps(self.metadata).encode()
        if args[0] == "restore":
            target = Path(args[args.index("--target") + 1])
            for name, data in [("database.dump", b"PGDMPtest"), ("manifest.json", json.dumps(self.manifest).encode()), ("recovery.tar", b"material")]:
                (target / name).write_bytes(data)
        if args[0] == "dump":
            return json.dumps(self.manifest).encode()
        return b""

    def run_restore(self, failure=None):
        def verified(*args):
            if failure == "verify":
                raise ValueError("synthetic verification failure")
        with patch.object(r, "backup_module", return_value=b), patch.object(b, "load_config", return_value=self.c), patch.object(b.Job, "restic", self.remote), patch.object(b.Job, "quota"), patch.object(r, "check_running"), patch.object(r, "restored", return_value=contextlib.nullcontext()), patch.object(r, "verify", side_effect=verified):
            r.restore(["--synthetic", str(self.root / "config"), "--snapshot", self.sid])

    def test_restore_publishes_private_attempt_and_success_after_cleanup(self):
        self.run_restore()
        attempt = json.loads((self.state / "restore-last-attempt.json").read_text())
        success = json.loads((self.state / "restore-last-success.json").read_text())
        self.assertTrue(attempt["ok"])
        self.assertEqual(attempt, success)
        self.assertEqual(success["snapshot_id"], self.sid)
        self.assertFalse(list(self.state.glob("restore-*/*")))
        self.assertEqual((self.state / "restore-last-success.json").stat().st_mode & 0o077, 0)

    def test_failed_latest_restore_invalidates_previous_success(self):
        self.run_restore()
        with self.assertRaises(ValueError):
            self.run_restore("verify")
        attempt = json.loads((self.state / "restore-last-attempt.json").read_text())
        success = json.loads((self.state / "restore-last-success.json").read_text())
        self.assertFalse(attempt["ok"])
        self.assertNotEqual(attempt["run_id"], success["run_id"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ["locks", "evidence", "fixtures"]:
        parser.add_argument("--" + name, action="store_true")
    options = parser.parse_args()
    selected = [c for name, c in [("locks", Locks), ("evidence", Evidence)] if getattr(options, name) or not any(vars(options).values())]
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in selected)
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
