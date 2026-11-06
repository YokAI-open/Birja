#!/usr/bin/env python3
"""Image identity and offline recovery contracts at actual command boundaries."""

import hashlib
import importlib.util
import io
import json
import sys
import tarfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "recovery", ROOT / "deploy/verify-restore.py"
)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
PYTHON = "python:3.14.10-slim-trixie@sha256:af8a5aa14780025dbfbcfbc81bd8a91ebd87711dd5b0f48ed71090949dd7cb1d"
PG = "postgres:18.6-trixie@sha256:bd5dfa494a5a259704365813dbfa5fa6b3e69be7348d43b547f540c730478583"
REDIS = "redis:8.8.4-trixie@sha256:a008e2cb5579f3616b29bd9e9913a25f16ec09ae2f56ddab524664663b581228"
NODE = "node:24.22.2-trixie-slim@sha256:0820eaa85e07d0490446dd01d14707e17e6108a36988cf374899cd057eb3812d"


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


class Identity(unittest.TestCase):
    def test_saved_config_and_manifest_cannot_be_substituted(self):
        config = json.dumps(
            {"os": "linux", "architecture": "amd64", "rootfs": {"diff_ids": []}}
        ).encode()
        config_id = sha(config)
        manifest = json.dumps(
            {"config": {"digest": config_id, "size": len(config)}}
        ).encode()
        index = json.dumps(
            {
                "manifests": [
                    {
                        "digest": sha(manifest),
                        "size": len(manifest),
                        "platform": {"os": "linux", "architecture": "amd64"},
                    }
                ]
            }
        ).encode()
        for config_path, contents in [
            (config_id[7:] + ".json", config),
            (config_id[7:] + ".json", b"{}"),
            (sha(manifest)[7:] + ".json", manifest),
        ]:
            saved = io.BytesIO()
            with tarfile.open(fileobj=saved, mode="w") as tar:
                files = {
                    "manifest.json": json.dumps(
                        [{"Config": config_path, "Layers": []}]
                    ).encode(),
                    config_path: contents,
                }
                for name, data in files.items():
                    member = tarfile.TarInfo(name)
                    member.size = len(data)
                    tar.addfile(member, io.BytesIO(data))
            saved.seek(0)
            with (
                patch.object(r, "INDEX_DIGEST", sha(index)),
                patch.object(r, "PLATFORM_DIGEST", sha(manifest)),
                patch.object(r, "IMAGE_ID", config_id),
            ):
                if contents == config:
                    r.verify_saved_image(saved, index, manifest)
                else:
                    with self.assertRaises(ValueError):
                        r.verify_saved_image(saved, index, manifest)

    def test_all_actual_consumers_are_immutable(self):
        self.assertEqual(
            (ROOT / "backend/Dockerfile").read_text().count("FROM " + PYTHON), 2
        )
        for filename in [
            "docker-compose.yml",
            "docker-compose.test.yml",
            "docker-compose.prod.yml",
        ]:
            source = (ROOT / filename).read_text()
            self.assertIn("image: " + PG, source)
            self.assertIn("image: " + REDIS, source)
        self.assertIn("FROM " + NODE, (ROOT / "frontend/Dockerfile").read_text())
        self.assertIn("NODE_IMAGE=" + NODE, (ROOT / "deploy/deploy.sh").read_text())

    def test_authenticated_manifest_links_and_config_platform(self):
        config = json.dumps({"os": "linux", "architecture": "amd64"}).encode()
        manifest = json.dumps(
            {"config": {"digest": sha(config), "size": len(config)}}
        ).encode()
        index = json.dumps(
            {
                "manifests": [
                    {
                        "digest": sha(manifest),
                        "size": len(manifest),
                        "platform": {"os": "linux", "architecture": "amd64"},
                    }
                ]
            }
        ).encode()
        with (
            patch.object(r, "INDEX_DIGEST", sha(index)),
            patch.object(r, "PLATFORM_DIGEST", sha(manifest)),
            patch.object(r, "IMAGE_ID", sha(config)),
        ):
            r.verify_image_provenance(index, manifest, config)
            for values in [
                (index + b" ", manifest, config),
                (index, manifest + b" ", config),
                (index, manifest, config + b" "),
            ]:
                with self.assertRaises(ValueError):
                    r.verify_image_provenance(*values)
            with (
                patch.object(r, "IMAGE_ID", sha(manifest)),
                self.assertRaises(ValueError),
            ):
                r.verify_image_provenance(index, manifest, config)

    def test_import_only_mapping_classic_and_containerd_no_registry_or_pull(self):
        # Only the imported immutable identity exists. Registry refs and
        # RepoDigests are deliberately unavailable in this command model.
        for engine_id in [r.IMAGE_ID, getattr(r, "PLATFORM_DIGEST", "missing")]:
            calls = []
            aliases = {}

            def docker(
                argv, *args, calls=calls, aliases=aliases, engine_id=engine_id, **kwargs
            ):
                calls.append(argv)
                if argv[1:3] == ["image", "tag"]:
                    self.assertEqual(argv[3], engine_id)
                    aliases[argv[4]] = engine_id
                    return b""
                if argv[1:3] == ["image", "inspect"]:
                    ref = argv[3]
                    if ref != engine_id and ref not in aliases:
                        raise ValueError("not imported")
                    return json.dumps(
                        [
                            {
                                "Id": engine_id,
                                "Os": "linux",
                                "Architecture": "amd64",
                                "RepoDigests": [],
                            }
                        ]
                    ).encode()
                if argv[1:] == ["compose", "config", "--format", "json"]:
                    return json.dumps(
                        {
                            "services": {
                                "postgres": {
                                    "image": r.RECOVERY_IMAGE,
                                    "pull_policy": "never",
                                }
                            },
                            "networks": {"isolated": {"internal": True}},
                        }
                    ).encode()
                if "up" in argv:
                    self.assertEqual(argv[-2:], ["--pull", "never"])
                    return b""
                if argv[1:] == ["compose", "ps", "-q", "postgres"]:
                    return b"container"
                if argv[1:] == ["inspect", "container"]:
                    return json.dumps(
                        [
                            {
                                "Image": engine_id,
                                "Platform": "linux",
                                "HostConfig": {
                                    "Privileged": False,
                                    "Tmpfs": {"/var/lib/postgresql": "size=268435456"},
                                },
                                "Mounts": [],
                                "NetworkSettings": {"Networks": {"isolated": {}}},
                            }
                        ]
                    ).encode()
                if argv[1:] == ["network", "inspect", "isolated"]:
                    return b'[{"Internal": true}]'
                self.fail("unexpected Docker command: " + repr(argv))

            with patch.object(r, "call", side_effect=docker):
                self.assertEqual(r.bind_recovery_image(), engine_id)
                self.assertEqual(r.loaded_recovery_image(), engine_id)
                r.start_recovery(["docker", "compose"])
                r.check_running(["docker", "compose"])
            self.assertFalse(any("pull" in argv for argv in calls))
            self.assertFalse(
                any(
                    "postgres@" in arg or arg.startswith("postgres:")
                    for argv in calls
                    for arg in argv
                )
            )
        for returned in ["sha256:" + "0" * 64, r.IMAGE_ID]:
            doc = [{"Id": returned, "Os": "linux", "Architecture": "arm64"}]
            with (
                patch.object(r, "call", return_value=json.dumps(doc).encode()),
                self.assertRaises(ValueError),
            ):
                r.bind_recovery_image()
        with (
            patch.object(r, "call", side_effect=ValueError("missing")),
            self.assertRaises(ValueError),
        ):
            r.bind_recovery_image()


if __name__ == "__main__":
    unittest.main()
