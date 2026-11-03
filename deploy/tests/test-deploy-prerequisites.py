#!/usr/bin/env python3
"""Fast stdlib contracts; synthetic files and intercepted command boundaries only."""

import argparse
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ["locks", "evidence", "fixtures"]:
        parser.add_argument("--" + name, action="store_true")
    options = parser.parse_args()
    selected = [Locks] if options.locks or not any(vars(options).values()) else []
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in selected)
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
