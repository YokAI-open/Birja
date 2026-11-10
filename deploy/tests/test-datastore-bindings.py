#!/usr/bin/env python3
"""Protected candidate routing contracts; private files and intercepted Docker only."""

import copy
import fcntl
import importlib.util
import json
import os
import shutil
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
                kind: {
                    "name": f"birja-prod_{logical}_{kind}",
                    "created_at": "2026-11-09T00:00:00Z",
                    "driver": "local",
                    "scope": "local",
                }
                for kind in ["original", "candidate"]
            }
        self.config.write_text(json.dumps(self.binding))
        self.config.chmod(0o600)
        self.constants = patch.multiple(
            self.m,
            CONFIG=self.config,
            OVERLAY=self.overlay,
            LOCK=self.root / "operation.lock",
        )
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
                value["volumes"]["pgdata"]["candidate"] = value["volumes"]["redisdata"][
                    "original"
                ]
            elif mutation == "unknown-logical":
                value["volumes"]["other"] = value["volumes"]["pgdata"]
            else:
                value["volumes"]["pgdata"]["candidate"]["driver"] = "nfs"
            self.config.write_text(json.dumps(value))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.m.read_bindings()
        self.config.write_text(json.dumps(self.binding))
        self.config.write_text(
            self.config.read_text().replace('"format": 1', '"format": 1, "format": 1')
        )
        with self.assertRaises(ValueError):
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
        rows = [
            {
                "Name": v["name"],
                "CreatedAt": v["created_at"],
                "Driver": "local",
                "Scope": "local",
                "Options": None,
            }
            for pair in self.binding["volumes"].values()
            for v in pair.values()
        ]
        with patch.object(
            self.m, "command", return_value=json.dumps(rows).encode()
        ) as run:
            self.m.inspect_volumes(self.binding)
            self.assertEqual(
                run.call_args.args[0][:3], ["/usr/bin/docker", "volume", "inspect"]
            )
        for mutation in ["missing", "recreated", "alias", "duplicate"]:
            changed = copy.deepcopy(rows)
            if mutation == "missing":
                changed.pop()
            elif mutation == "recreated":
                changed[0]["CreatedAt"] = "2026-11-10T00:00:00Z"
            elif mutation == "alias":
                changed[0]["Options"] = {
                    "device": "/original",
                    "o": "bind",
                    "type": "none",
                }
            else:
                changed[-1] = changed[0]
            with (
                patch.object(
                    self.m, "command", return_value=json.dumps(changed).encode()
                ),
                self.assertRaises(ValueError),
            ):
                self.m.inspect_volumes(self.binding)

    def test_overlay_is_external_exact_private_and_forgery_rejected(self):
        self.m.write_overlay(self.binding)
        value = json.loads(self.overlay.read_text())
        self.assertEqual(
            value,
            {
                "volumes": {
                    name: {"external": True, "name": pair["candidate"]["name"]}
                    for name, pair in self.binding["volumes"].items()
                }
            },
        )
        self.assertEqual(self.overlay.stat().st_mode & 0o777, 0o600)
        self.m.write_overlay(self.binding)
        self.overlay.write_text(
            '{"volumes": {}, "volumes": ' + json.dumps(value["volumes"]) + "}"
        )
        with self.assertRaises(ValueError):
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
            rejected = subprocess.run(
                ["sh", "-ec", probe], check=False, capture_output=True
            )
            self.assertNotEqual(rejected.returncode, 0)

    def test_real_redis_88_offset_manifest_and_malformed_rows(self):
        selected = self.root / "selected"
        data = selected / "appendonlydir"
        data.mkdir(parents=True)
        manifest = data / "appendonly.aof.manifest"
        base = "file appendonly.aof.1.base.rdb seq 1 type b\n"
        incremental = "file appendonly.aof.1.incr.aof seq 1 type i"
        (data / "appendonly.aof.1.base.rdb").write_bytes(b"existing-base")
        (data / "appendonly.aof.1.incr.aof").write_bytes(b"")
        manifest.write_text(base)
        for path in [data, *data.iterdir()]:
            os.chown(path, 65532, 65532)
        probe = self.m.PROBES["redisdata"].replace("/selected", str(selected))
        for row in [
            incremental,
            incremental + " startoffset 0",
            incremental + " startoffset 0 endoffset 1",
            incremental + " startoffset 0 endoffset -1",
        ]:
            manifest.write_text(base + row + "\n")
            with self.subTest(row=row):
                subprocess.run(["sh", "-ec", probe], check=True, capture_output=True)
        for row in [
            incremental + " startoffset nope",
            incremental + " wronglabel 0",
            incremental + " startoffset -1",
            incremental + " startoffset nope endoffset 1",
            incremental + " startoffset 0 endoffset 1 extra 2",
            incremental + " startoffset 0 wronglabel 1",
            incremental.replace("seq 1", "seq -1"),
            incremental.replace("appendonly.aof.1.incr.aof", "../outside"),
            base.strip() + " startoffset 0 endoffset 1",
        ]:
            manifest.write_text(base + row + "\n")
            with self.subTest(row=row):
                result = subprocess.run(
                    ["sh", "-ec", probe], check=False, capture_output=True
                )
                self.assertNotEqual(result.returncode, 0)

    def test_running_identity_rejects_foreign_wrong_mount_and_ambiguity(self):
        images = {"postgres": "sha256:" + "1" * 64, "redis": "sha256:" + "2" * 64}
        container_ids = {"postgres": "a" * 64, "redis": "b" * 64}
        rows = {}
        for service, logical in [("postgres", "pgdata"), ("redis", "redisdata")]:
            mounts = [
                {
                    "Type": "volume",
                    "Name": self.binding["volumes"][logical]["candidate"]["name"],
                    "Destination": "/var/lib/postgresql"
                    if service == "postgres"
                    else "/data",
                    "RW": True,
                }
            ]
            if service == "postgres":
                mounts += [
                    {
                        "Type": "bind",
                        "Source": "/etc/birja/db-tls/server",
                        "Destination": "/run/birja/db-server",
                        "RW": False,
                    },
                    {
                        "Type": "bind",
                        "Source": str(self.m.HERE / "db"),
                        "Destination": "/run/birja/db-hba",
                        "RW": False,
                    },
                ]
            rows[service] = {
                "Id": container_ids[service],
                "Image": images[service],
                "Platform": "linux",
                "State": {"Running": True},
                "Config": {
                    "User": "70:70" if service == "postgres" else "65532",
                    "Labels": {
                        "com.docker.compose.project": "birja-prod",
                        "com.docker.compose.service": service,
                    },
                },
                "Mounts": mounts,
                "HostConfig": {"PortBindings": {}, "Privileged": False},
                "NetworkSettings": {"Networks": {"birja-prod_data": {}}},
            }

        def docker(argv):
            if argv[1:3] == ["ps", "-aq"]:
                service = argv[-1].split("=")[-1]
                identity = container_ids[service]
                return (identity if "--no-trunc" in argv else identity[:12]).encode()
            if argv[1] == "inspect":
                service = next(
                    name
                    for name, identity in container_ids.items()
                    if identity.startswith(argv[2])
                )
                return json.dumps(rows[service]).encode()
            if argv[1:3] == ["image", "inspect"]:
                service = "postgres" if "postgres@" in argv[3] else "redis"
                return json.dumps(
                    [{"Id": images[service], "Os": "linux", "Architecture": "amd64"}]
                ).encode()
            if argv[1:3] == ["network", "inspect"]:
                return b'[{"Internal":true}]'
            self.fail(repr(argv))

        with patch.object(self.m, "command", side_effect=docker):
            self.m.check_running(self.binding)
            for mutation in [
                "mount",
                "label",
                "image",
                "user",
                "port",
                "network",
                "stopped",
            ]:
                saved = copy.deepcopy(rows["postgres"])
                if mutation == "mount":
                    rows["postgres"]["Mounts"][0]["Name"] = "original"
                if mutation == "label":
                    rows["postgres"]["Config"]["Labels"][
                        "com.docker.compose.project"
                    ] = "other"
                if mutation == "image":
                    rows["postgres"]["Image"] = "sha256:" + "3" * 64
                if mutation == "user":
                    rows["postgres"]["Config"]["User"] = "0"
                if mutation == "port":
                    rows["postgres"]["HostConfig"]["PortBindings"] = {"5432/tcp": [{}]}
                if mutation == "network":
                    rows["postgres"]["NetworkSettings"]["Networks"]["foreign"] = {}
                if mutation == "stopped":
                    rows["postgres"]["State"]["Running"] = False
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    self.m.check_running(self.binding)
                rows["postgres"] = saved
            # Docker29 containerd records the index in container.Image, while
            # platform image inspect and this actual descriptor name its child.
            for service, row in rows.items():
                row["Image"] = self.m.images()[service].split("@", 1)[1]
                row["ImageManifestDescriptor"] = {
                    "digest": images[service],
                    "platform": {"architecture": "amd64", "os": "linux"},
                }
            self.m.check_running(self.binding)
            for mutation in ["missing", "digest", "architecture", "os", "index"]:
                saved = copy.deepcopy(rows["postgres"])
                descriptor = rows["postgres"]["ImageManifestDescriptor"]
                if mutation == "missing":
                    rows["postgres"]["ImageManifestDescriptor"] = None
                elif mutation == "digest":
                    descriptor["digest"] = "sha256:" + "3" * 64
                elif mutation in {"architecture", "os"}:
                    descriptor["platform"][mutation] = "unknown"
                else:
                    rows["postgres"]["Image"] = "sha256:" + "3" * 64
                with self.subTest(descriptor=mutation), self.assertRaises(ValueError):
                    self.m.check_running(self.binding)
                rows["postgres"] = saved
        with (
            patch.object(self.m, "command", return_value=b"one\ntwo\n"),
            self.assertRaises(ValueError),
        ):
            self.m.check_running(self.binding)

    def test_root_and_inherited_real_kernel_lock_required(self):
        with (
            patch.object(self.m.os, "geteuid", return_value=1001),
            self.assertRaises(ValueError),
        ):
            self.m.main(["--write-overlay"])
        with self.m.LOCK.open("w") as held:
            self.m.LOCK.chmod(0o600)
            with patch.dict(os.environ, {"BIRJA_BACKUP_LOCK_FD": str(held.fileno())}):
                with self.assertRaises(ValueError):
                    self.m.operation_lock()
                fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with (
                    self.m.operation_lock(),
                    self.m.LOCK.open("a") as other,
                    self.assertRaises(BlockingIOError),
                ):
                    fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_missing_binding_and_caller_flags_rejected_before_docker(self):
        self.config.unlink()
        with self.m.LOCK.open("w") as held:
            self.m.LOCK.chmod(0o600)
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with patch.object(self.m, "command") as run:
                with self.assertRaises(FileNotFoundError):
                    self.m.main(["--write-overlay"], inherited=str(held.fileno()))
                for args in [
                    ["--write-overlay", "--file", "/tmp/other"],
                    ["--project", "other"],
                ]:
                    with self.assertRaises(ValueError):
                        self.m.main(args, inherited=str(held.fileno()))
                run.assert_not_called()

    def test_data_probe_bind_mount_and_metadata_races_fail_without_creation(self):
        records = {}
        for pair in self.binding["volumes"].values():
            for value in pair.values():
                data = self.root / value["name"] / "_data"
                data.mkdir(parents=True)
                records[value["name"]] = {
                    "Name": value["name"],
                    "CreatedAt": value["created_at"],
                    "Driver": "local",
                    "Scope": "local",
                    "Options": None,
                    "Mountpoint": str(data),
                }
        calls = []

        def docker(argv):
            calls.append(argv)
            if argv[1:3] == ["volume", "inspect"]:
                return json.dumps(list(records.values())).encode()
            self.assertEqual(argv[1], "run")
            mount = argv[argv.index("--mount") + 1]
            self.assertTrue(mount.startswith("type=bind,source="))
            self.assertTrue(mount.endswith(",target=/selected,readonly"))
            self.assertIn("--read-only", argv)
            self.assertIn("never", argv)
            self.assertNotIn("original", mount)
            self.assertFalse(any(arg == "create" for arg in argv))
            return b""

        with patch.object(self.m, "command", side_effect=docker):
            self.m.check_data(self.binding, records)
            self.assertEqual(sum(argv[1] == "run" for argv in calls), 2)
            self.assertEqual(calls[-1][1:3], ["volume", "inspect"])
        selected = records[self.binding["volumes"]["pgdata"]["candidate"]["name"]]
        shutil.rmtree(selected["Mountpoint"])
        with patch.object(self.m, "command") as run, self.assertRaises(ValueError):
            self.m.check_data(self.binding, records)
        run.assert_not_called()
        Path(selected["Mountpoint"]).mkdir()

        def replaced(argv):
            result = docker(argv)
            if argv[1] == "run":
                selected["CreatedAt"] = "2026-11-10T00:00:00Z"
            return result

        with (
            patch.object(self.m, "command", side_effect=replaced),
            self.assertRaises(ValueError),
        ):
            self.m.check_data(self.binding, records)

    def test_docker_environment_scrubbed_and_failure_redacted(self):
        with (
            patch.dict(
                os.environ,
                {"DOCKER_HOST": "tcp://foreign", "COMPOSE_FILE": "/tmp/other"},
            ),
            patch.object(
                self.m.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(
                    [], 1, b"private-output", b"private-error"
                ),
            ) as run,
        ):
            with self.assertRaisesRegex(ValueError, "^datastore binding guard$"):
                self.m.command(["/usr/bin/docker", "volume", "inspect", "candidate"])
            self.assertEqual(
                run.call_args.kwargs["env"],
                {"PATH": "/usr/bin:/bin", "HOME": "/tmp", "LANG": "C.UTF-8"},
            )


class Wiring(unittest.TestCase):
    def test_startup_revision_requires_exact_protected_completed_profile(self):
        source = (ROOT / "deploy/deploy.sh").read_text()
        function = source.split("startup_revision() {", 1)[1].split("\n}\n", 1)[0]
        with tempfile.TemporaryDirectory(prefix="birja-backup-test-") as tmp:
            state = Path(tmp)
            profile = state / "restore-last-success.json"
            expected = {
                "ok": True,
                "source_release": "1" * 40,
                "snapshot_id": "a" * 64,
                "source_revision": "0007",
            }
            function = function.replace(
                "/var/lib/birja/backup/restore-last-success.json", str(profile)
            )
            script = (
                "startup_revision() {" + function + '\n}\nstartup_revision "$1" "$2"'
            )

            def call():
                return subprocess.run(
                    ["bash", "-c", script, "_", "1" * 40, "a" * 64],
                    capture_output=True,
                    check=False,
                )

            for field, value in [
                (None, None),
                ("ok", False),
                ("source_release", "2" * 40),
                ("snapshot_id", "b" * 64),
                ("source_revision", "../unknown"),
            ]:
                data = {**expected, **({field: value} if field else {})}
                profile.write_text(json.dumps(data))
                profile.chmod(0o600)
                result = call()
                self.assertEqual(result.returncode == 0, field is None)
                if field is None:
                    self.assertEqual(result.stdout, b"0007\n")
            profile.unlink()
            self.assertNotEqual(call().returncode, 0)
            profile.write_text(json.dumps(expected))
            profile.chmod(0o644)
            self.assertNotEqual(call().returncode, 0)
            profile.chmod(0o600)
            saved = state / "saved"
            profile.rename(saved)
            profile.symlink_to(saved)
            self.assertNotEqual(call().returncode, 0)

    def test_retained_recreation_and_secure_startup_use_fixed_helper(self):
        source = (ROOT / "deploy/deploy.sh").read_text()
        self.assertIn("bindings --write-overlay", source)
        self.assertIn("-f /var/lib/birja/ops/datastore-volumes.json", source)
        self.assertIn("--start-selected-datastores", source)
        start = source.split("start_selected_datastores() {", 1)[1].split("\n}", 1)[0]
        self.assertLess(start.index("--production --check"), start.index("dc up"))
        self.assertLess(start.index("bindings --check-volumes"), start.index("dc up"))
        self.assertIn("bindings --check-running", start)
        self.assertIn('[ "$actual" = "$ADMITTED_REVISION" ]', start)
        self.assertNotIn("migrate", start)
        installer = (ROOT / "deploy/deploy-entrypoint.sh").read_text()
        self.assertGreaterEqual(installer.count("'deploy/datastore-bindings.py'"), 2)
        roles = (ROOT / "deploy/configure-db.sh").read_text()
        self.assertIn("datastore-bindings.py", roles)
        self.assertLess(
            roles.index("datastore-bindings.py"),
            roles.index("input=COLLATION_PREFLIGHT"),
        )


if __name__ == "__main__":
    unittest.main()
