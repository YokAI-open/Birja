#!/usr/bin/env python3
"""Protected candidate routing contracts; private files and intercepted Docker only."""

import copy
import fcntl
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


class Bindings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "deploy/datastore-bindings.py"
        if not path.is_file():
            raise AssertionError("protected selected-volume helper is missing")
        spec = importlib.util.spec_from_file_location("bindings", path)
        cls.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.m)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="birja-backup-test-")
        self.root = Path(self.tmp.name)
        self.config = self.root / "bindings.json"
        self.overlay = self.root / "volumes.json"
        self.binding = {"format": 1, "project": "birja-prod", "volumes": {}}
        for logical in ["pgdata", "redisdata"]:
            self.binding["volumes"][logical] = {
                kind: {"name": f"birja-prod_{logical}_{kind}", "created_at": "2026-11-09T00:00:00Z", "driver": "local", "scope": "local"}
                for kind in ["original", "candidate"]
            }
        self.config.write_text(json.dumps(self.binding))
        self.config.chmod(0o600)
        self.constants = patch.multiple(self.m, CONFIG=self.config, OVERLAY=self.overlay, LOCK=self.root / "operation.lock")
        self.constants.start()

    def tearDown(self):
        self.constants.stop()
        self.tmp.cleanup()

    def test_exact_schema_and_private_path(self):
        self.assertEqual(self.m.read_bindings(), self.binding)
        for mutation in ["project", "extra", "alias", "unknown-logical", "metadata"]:
            value = copy.deepcopy(self.binding)
            if mutation == "project":
                value["project"] = "birja"
            elif mutation == "extra":
                value["override"] = "/tmp/other"
            elif mutation == "alias":
                value["volumes"]["pgdata"]["candidate"] = value["volumes"]["redisdata"]["original"]
            elif mutation == "unknown-logical":
                value["volumes"]["other"] = value["volumes"]["pgdata"]
            else:
                value["volumes"]["pgdata"]["candidate"]["driver"] = "nfs"
            self.config.write_text(json.dumps(value))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.m.read_bindings()
        self.config.write_text(json.dumps(self.binding))
        self.config.chmod(0o644)
        with self.assertRaises(ValueError):
            self.m.read_bindings()
        self.config.chmod(0o600)
        target = self.root / "target.json"
        self.config.rename(target)
        self.config.symlink_to(target)
        with self.assertRaises(ValueError):
            self.m.read_bindings()

    def test_metadata_never_creates_and_rejects_missing_replaced_or_alias_volume(self):
        rows = [{"Name": v["name"], "CreatedAt": v["created_at"], "Driver": "local", "Scope": "local", "Options": None}
                for pair in self.binding["volumes"].values() for v in pair.values()]
        with patch.object(self.m, "command", return_value=json.dumps(rows).encode()) as run:
            self.m.inspect_volumes(self.binding)
            self.assertEqual(run.call_args.args[0][:3], ["/usr/bin/docker", "volume", "inspect"])
        for mutation in ["missing", "recreated", "alias", "duplicate"]:
            changed = copy.deepcopy(rows)
            if mutation == "missing":
                changed.pop()
            elif mutation == "recreated":
                changed[0]["CreatedAt"] = "2026-11-10T00:00:00Z"
            elif mutation == "alias":
                changed[0]["Options"] = {"device": "/original", "o": "bind", "type": "none"}
            else:
                changed[-1] = changed[0]
            with patch.object(self.m, "command", return_value=json.dumps(changed).encode()), self.assertRaises(ValueError):
                self.m.inspect_volumes(self.binding)

    def test_overlay_is_external_exact_private_and_forgery_rejected(self):
        self.m.write_overlay(self.binding)
        value = json.loads(self.overlay.read_text())
        self.assertEqual(value, {"volumes": {name: {"external": True, "name": pair["candidate"]["name"]}
                                            for name, pair in self.binding["volumes"].items()}})
        self.assertEqual(self.overlay.stat().st_mode & 0o777, 0o600)
        self.m.write_overlay(self.binding)
        value["services"] = {"postgres": {"privileged": True}}
        self.overlay.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            self.m.write_overlay(self.binding)
        self.overlay.unlink()
        self.overlay.symlink_to(self.config)
        with self.assertRaises(ValueError):
            self.m.write_overlay(self.binding)

    def test_candidate_data_probe_checks_real_existing_files(self):
        for logical, owner in [("pgdata", 70), ("redisdata", 65532)]:
            selected = self.root / logical
            selected.mkdir()
            if logical == "pgdata":
                data = selected / "18/docker"
                (data / "global").mkdir(parents=True)
                (data / "PG_VERSION").write_text("18\n")
                marker = data / "global/pg_control"
                marker.write_bytes(b"existing-control")
                owned = [data, data / "PG_VERSION", marker]
            else:
                data = selected / "appendonlydir"
                data.mkdir()
                marker = data / "appendonly.aof.manifest"
                marker.write_text("file appendonly.aof.1.base.rdb seq 1 type b\n")
                (data / "appendonly.aof.1.base.rdb").write_bytes(b"existing-aof-base")
                owned = [data, marker, data / "appendonly.aof.1.base.rdb"]
            for path in owned:
                os.chown(path, owner, owner)
            probe = self.m.PROBES[logical].replace("/selected", str(selected))
            subprocess.run(["sh", "-ec", probe], check=True, capture_output=True)
            marker.write_bytes(b"")
            rejected = subprocess.run(["sh", "-ec", probe], check=False, capture_output=True)
            self.assertNotEqual(rejected.returncode, 0)

    def test_running_identity_rejects_foreign_wrong_mount_and_ambiguity(self):
        images = {"postgres": "sha256:" + "1" * 64, "redis": "sha256:" + "2" * 64}
        rows = {}
        for service, logical in [("postgres", "pgdata"), ("redis", "redisdata")]:
            mounts = [{"Type": "volume", "Name": self.binding["volumes"][logical]["candidate"]["name"], "Destination": "/var/lib/postgresql" if service == "postgres" else "/data", "RW": True}]
            if service == "postgres":
                mounts += [{"Type": "bind", "Source": "/etc/birja/db-tls/server", "Destination": "/run/birja/db-server", "RW": False},
                           {"Type": "bind", "Source": str(self.m.HERE / "db"), "Destination": "/run/birja/db-hba", "RW": False}]
            rows[service] = {"Id": service, "Image": images[service], "Platform": "linux", "State": {"Running": True},
                             "Config": {"User": "70:70" if service == "postgres" else "65532", "Labels": {"com.docker.compose.project": "birja-prod", "com.docker.compose.service": service}},
                             "Mounts": mounts, "HostConfig": {"PortBindings": {}, "Privileged": False},
                             "NetworkSettings": {"Networks": {"birja-prod_data": {}}}}

        def docker(argv):
            if argv[1:3] == ["ps", "-aq"]:
                service = argv[-1].split("=")[-1]
                return service.encode()
            if argv[1] == "inspect":
                return json.dumps(rows[argv[2]]).encode()
            if argv[1:3] == ["image", "inspect"]:
                service = "postgres" if "postgres@" in argv[3] else "redis"
                return json.dumps([{"Id": images[service], "Os": "linux", "Architecture": "amd64"}]).encode()
            if argv[1:3] == ["network", "inspect"]:
                return b'[{"Internal":true}]'
            self.fail(repr(argv))

        with patch.object(self.m, "command", side_effect=docker):
            self.m.check_running(self.binding)
            for mutation in ["mount", "label", "image", "user", "port", "network", "stopped"]:
                saved = copy.deepcopy(rows["postgres"])
                if mutation == "mount": rows["postgres"]["Mounts"][0]["Name"] = "original"
                if mutation == "label": rows["postgres"]["Config"]["Labels"]["com.docker.compose.project"] = "other"
                if mutation == "image": rows["postgres"]["Image"] = "sha256:" + "3" * 64
                if mutation == "user": rows["postgres"]["Config"]["User"] = "0"
                if mutation == "port": rows["postgres"]["HostConfig"]["PortBindings"] = {"5432/tcp": [{}]}
                if mutation == "network": rows["postgres"]["NetworkSettings"]["Networks"]["foreign"] = {}
                if mutation == "stopped": rows["postgres"]["State"]["Running"] = False
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    self.m.check_running(self.binding)
                rows["postgres"] = saved
        with patch.object(self.m, "command", return_value=b"one\ntwo\n"), self.assertRaises(ValueError):
            self.m.check_running(self.binding)

    def test_root_and_inherited_real_kernel_lock_required(self):
        with patch.object(self.m.os, "geteuid", return_value=1001), self.assertRaises(ValueError):
            self.m.main(["--write-overlay"])
        with self.m.LOCK.open("w") as held:
            self.m.LOCK.chmod(0o600)
            with patch.dict(os.environ, {"BIRJA_BACKUP_LOCK_FD": str(held.fileno())}):
                with self.assertRaises(ValueError):
                    self.m.operation_lock()
                fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with self.m.operation_lock():
                    with self.m.LOCK.open("a") as other, self.assertRaises(BlockingIOError):
                        fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)


class Wiring(unittest.TestCase):
    def test_retained_recreation_and_secure_startup_use_fixed_helper(self):
        source = (ROOT / "deploy/deploy.sh").read_text()
        self.assertIn('bindings --write-overlay', source)
        self.assertIn('-f /var/lib/birja/ops/datastore-volumes.json', source)
        self.assertIn('--start-selected-datastores', source)
        start = source.split("start_selected_datastores() {", 1)[1].split("\n}", 1)[0]
        self.assertLess(start.index("--production --check"), start.index("dc up"))
        self.assertLess(start.index("bindings --check-volumes"), start.index("dc up"))
        self.assertIn("bindings --check-running", start)
        self.assertNotIn("migrate", start)
        installer = (ROOT / "deploy/deploy-entrypoint.sh").read_text()
        self.assertGreaterEqual(installer.count("'deploy/datastore-bindings.py'"), 2)
        roles = (ROOT / "deploy/configure-db.sh").read_text()
        self.assertIn("datastore-bindings.py", roles)
        self.assertLess(roles.index("datastore-bindings.py"), roles.index("input=COLLATION_PREFLIGHT"))


if __name__ == "__main__":
    unittest.main()
