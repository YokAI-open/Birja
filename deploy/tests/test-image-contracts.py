#!/usr/bin/env python3
"""Image identity and offline recovery contracts at actual command boundaries."""

import datetime
import hashlib
import importlib.util
import io
import json
import os
import shlex
import subprocess
import sys
import tarfile
import tempfile
import textwrap
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
    def test_start_rejects_registry_and_pull_fallback_before_up(self):
        for image, policy in [
            (PG, "never"),
            (r.RECOVERY_IMAGE, "missing"),
            (r.RECOVERY_IMAGE, "always"),
        ]:
            config = {
                "services": {"postgres": {"image": image, "pull_policy": policy}},
                "networks": {"isolated": {"internal": True}},
            }
            with (
                patch.object(
                    r, "call", return_value=json.dumps(config).encode()
                ) as calls,
                self.assertRaises(ValueError),
            ):
                r.start_recovery(["docker", "compose"])
            self.assertEqual(calls.call_count, 1)
            self.assertEqual(
                calls.call_args.args[0][-3:], ["config", "--format", "json"]
            )

    def test_oci_import_graph_rejects_forged_index_and_extra_blobs(self):
        config = json.dumps({"os": "linux", "architecture": "amd64"}).encode()
        cid = sha(config)
        manifest = json.dumps(
            {"config": {"digest": cid, "size": len(config)}, "layers": []}
        ).encode()
        mid = sha(manifest)
        index = json.dumps(
            {
                "manifests": [
                    {
                        "digest": mid,
                        "size": len(manifest),
                        "platform": {"os": "linux", "architecture": "amd64"},
                    }
                ]
            }
        ).encode()
        for mutation in [None, "index", "extra", "tag"]:
            files = {
                "manifest.json": json.dumps(
                    [
                        {
                            "Config": "blobs/sha256/" + cid[7:],
                            "Layers": [],
                            "RepoTags": ["unreviewed:tag"]
                            if mutation == "tag"
                            else None,
                        }
                    ]
                ).encode(),
                "index.json": json.dumps(
                    {
                        "manifests": [
                            {
                                "digest": cid if mutation == "index" else mid,
                                "size": len(manifest),
                            }
                        ]
                    }
                ).encode(),
                "blobs/sha256/" + cid[7:]: config,
                "blobs/sha256/" + mid[7:]: manifest,
            }
            if mutation == "extra":
                files["blobs/sha256/" + "0" * 64] = b"unexpected graph"
            saved = io.BytesIO()
            with tarfile.open(fileobj=saved, mode="w") as tar:
                for name, data in files.items():
                    member = tarfile.TarInfo(name)
                    member.size = len(data)
                    tar.addfile(member, io.BytesIO(data))
            saved.seek(0)
            with (
                patch.object(r, "INDEX_DIGEST", sha(index)),
                patch.object(r, "PLATFORM_DIGEST", mid),
                patch.object(r, "IMAGE_ID", cid),
            ):
                if mutation is None:
                    r.verify_saved_image(saved, index, manifest)
                else:
                    with self.assertRaises(ValueError):
                        r.verify_saved_image(saved, index, manifest)

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
        self.assertIn(
            "NODE_BASE_IMAGE=" + NODE, (ROOT / "deploy/deploy.sh").read_text()
        )

    def test_complete_npm_distribution_and_retained_production_consumer(self):
        dockerfile = (ROOT / "frontend/Dockerfile").read_text()
        self.assertIn("AS toolchain", dockerfile)
        self.assertIn("npm-11.21.2.tgz", dockerfile)
        self.assertIn("AbortSignal.timeout(60000)", dockerfile)
        self.assertIn("10 * 1024 * 1024", dockerfile)
        self.assertIn("for await", dockerfile)
        self.assertIn(
            "7HPApk+AflMUavSseL1Pm6CnYqMIHk53x+KmuhqmTDqPkjPMgxIpTPcTqsE91EKNw4gFBJV9fnXiSdGm1DXq9A==",
            dockerfile,
        )
        self.assertLess(dockerfile.index("createHash"), dockerfile.index("tar -xzf"))
        deploy = (ROOT / "deploy/deploy.sh").read_text()
        self.assertIn('"$BIRJA_RETAINED_DIR/frontend/Dockerfile"', deploy)
        self.assertIn("--target toolchain", deploy)
        self.assertIn("--iidfile", deploy)
        retained = (ROOT / "deploy/deploy-entrypoint.sh").read_text()
        self.assertGreaterEqual(retained.count("'frontend/Dockerfile'"), 2)

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


class Scans(unittest.TestCase):
    def workflow_handoff(self, root, unavailable, inputs):
        """Execute the actual CI scan shell with one missing built image."""
        script = (
            (ROOT / ".github/workflows/ci.yml")
            .read_text()
            .split("- name: Scan all five actual images\n", 1)[1]
            .split("- name: Upload public image evidence", 1)[0]
            .split("run: |\n", 1)[1]
        )
        script = textwrap.dedent(script)
        capture = root / "capture.py"
        capture.write_text(
            "import json,sys\nfrom pathlib import Path\nPath('handoff.json').write_text(json.dumps(sys.argv[1:]))\n"
        )
        binpath = root / "bin"
        binpath.mkdir()
        tags = {
            "birja-backend-runtime:ci": "runtime",
            "birja-backend-test:ci": "builder",
            "birja-node-toolchain:ci": "node",
        }
        docker = binpath / "docker"
        docker.write_text(
            "#!"
            + sys.executable
            + "\nimport sys\ntags="
            + repr(tags)
            + "\ninputs="
            + repr(inputs)
            + "\nname=tags[sys.argv[3]]\nif name=="
            + repr(unavailable)
            + ":\n sys.stderr.write('original Docker inspect failed: image missing\\n')\n sys.exit(1)\nprint(inputs[name])\n"
        )
        docker.chmod(0o700)
        script = script.replace(
            "python3 deploy/scan-images.py",
            shlex.quote(sys.executable) + " " + shlex.quote(str(capture)),
        )
        script = script.replace("image-reports", shlex.quote(str(root)))
        completed = subprocess.run(
            ["bash", "-c", script],
            check=False,
            cwd=root,
            env={"PATH": str(binpath) + os.pathsep + os.defpath},
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode())
        args = json.loads((root / "handoff.json").read_text())
        self.assertEqual(args[args.index("--" + unavailable) + 1], "")
        return args

    def test_actual_producer_collects_all_targets_and_fails_closed(self):
        path = ROOT / "deploy/scan-images.py"
        self.assertTrue(path.is_file(), "strict scan producer missing")
        spec = importlib.util.spec_from_file_location("scan_images", path)
        producer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(producer)
        inputs = {
            name: "sha256:" + str(i) * 64
            for i, name in enumerate(
                ["runtime", "builder", "postgres", "redis", "node"], 1
            )
        }
        for mode in [
            "clean",
            "high",
            "critical",
            "scanner",
            "db",
            "malformed",
            "missing",
            "inspect",
            "export",
            "identity",
            "missing-node-id",
            "missing-runtime-id",
        ]:
            seen = []

            def command(argv, mode=mode, seen=seen, **kwargs):
                if argv[1:3] == ["image", "inspect"]:
                    if mode == "inspect" and argv[3] == inputs["runtime"]:
                        return subprocess.CompletedProcess(
                            argv, 1, b"", b"inspect error"
                        )
                    return subprocess.CompletedProcess(
                        argv,
                        0,
                        json.dumps(
                            [
                                {
                                    "Id": argv[3].rsplit("@", 1)[-1],
                                    "Os": "linux",
                                    "Architecture": "amd64",
                                    "RepoDigests": [],
                                }
                            ]
                        ).encode(),
                        b"",
                    )
                if argv[1:3] == ["image", "save"]:
                    if mode == "export" and argv[-1] == inputs["runtime"]:
                        return subprocess.CompletedProcess(
                            argv, 1, b"", b"export error"
                        )
                    config = json.dumps(
                        {"os": "linux", "architecture": "amd64"}
                    ).encode()
                    config_path = sha(config)[7:] + ".json"
                    with tarfile.open(argv[argv.index("-o") + 1], "w") as saved:
                        for name, data in {
                            "manifest.json": json.dumps(
                                [{"Config": config_path}]
                            ).encode(),
                            config_path: config,
                        }.items():
                            member = tarfile.TarInfo(name)
                            member.size = len(data)
                            saved.addfile(member, io.BytesIO(data))
                    return subprocess.CompletedProcess(argv, 0, b"", b"")
                if "--version" in argv:
                    return subprocess.CompletedProcess(
                        argv, 0, b'{"Version":"0.76.1"}', b""
                    )
                self.assertIn(producer.SCANNER, argv)
                self.assertIn("--read-only", argv)
                self.assertIn("--cap-drop=ALL", argv)
                self.assertNotIn("/var/run/docker.sock", " ".join(argv))
                self.assertIn("HIGH,CRITICAL", argv)
                seen.append(argv)
                # The fake scanner writes the real mounted cache DB metadata.
                mount = next(arg for arg in argv if arg.endswith(",dst=/cache"))
                cache = Path(mount.split("src=", 1)[1].split(",dst=", 1)[0])
                (cache / "db").mkdir(exist_ok=True)
                (cache / "db/metadata.json").write_text(
                    json.dumps(
                        {
                            "Version": 2,
                            "UpdatedAt": datetime.datetime.now(
                                datetime.UTC
                            ).isoformat(),
                            "DownloadedAt": datetime.datetime.now(
                                datetime.UTC
                            ).isoformat(),
                            "NextUpdate": (
                                datetime.datetime.now(datetime.UTC)
                                + datetime.timedelta(days=1)
                            ).isoformat(),
                        }
                    )
                    if mode != "db"
                    else "{}"
                )
                doc = {
                    "SchemaVersion": 2,
                    "Trivy": {"Version": "0.76.1"},
                    "Metadata": {
                        "ImageID": "sha256:" + "0" * 64
                        if mode == "identity"
                        else sha(
                            json.dumps(
                                {"os": "linux", "architecture": "amd64"}
                            ).encode()
                        )
                    },
                    "Results": [
                        {"Target": "fixture", "Type": "debian", "Vulnerabilities": []}
                    ],
                }
                status = 0
                if len(seen) == 1:
                    if mode in ["high", "critical"]:
                        doc["Results"][0]["Vulnerabilities"] = [
                            {"Severity": mode.upper(), "VulnerabilityID": "fixture"}
                        ]
                        # Findings must fail even if scanner mistakenly exits 0.
                    elif mode == "scanner":
                        status = 2
                stdout = (
                    b"{"
                    if mode == "malformed" and len(seen) == 1
                    else b""
                    if mode == "missing" and len(seen) == 1
                    else json.dumps(doc).encode()
                )
                return subprocess.CompletedProcess(
                    argv, status, stdout, b"fixture scanner log"
                )

            with (
                tempfile.TemporaryDirectory() as tmp,
                patch.object(producer, "command", side_effect=command),
            ):
                selected = dict(inputs)
                unavailable = {
                    "missing-node-id": "node",
                    "missing-runtime-id": "runtime",
                }.get(mode)
                if unavailable:
                    handoff = self.workflow_handoff(Path(tmp), unavailable, inputs)
                    with patch.object(sys, "argv", ["scan-images.py", *handoff]):
                        result = producer.main()
                else:
                    result = producer.run_scans(Path(tmp), selected)
                self.assertEqual(result, 0 if mode == "clean" else 1, mode)
                evidence = json.loads((Path(tmp) / "status.json").read_text())
                self.assertEqual(set(evidence["targets"]), set(inputs))
                self.assertEqual(
                    len(seen),
                    4
                    if mode
                    in ["inspect", "export", "missing-node-id", "missing-runtime-id"]
                    else 5,
                )
                if unavailable:
                    self.assertEqual(
                        evidence["targets"][unavailable]["error"],
                        "identity-resolution-failed",
                    )
                    self.assertIn(
                        "original Docker inspect failed",
                        (Path(tmp) / (unavailable + "-resolve.log")).read_text(),
                    )
                    for available in set(inputs) - {unavailable}:
                        self.assertTrue((Path(tmp) / (available + ".json")).is_file())
                else:
                    self.assertTrue((Path(tmp) / "node.json").is_file())
                self.assertFalse(list(Path(tmp).glob("*.tar")))
        with tempfile.TemporaryDirectory() as tmp:
            for invalid in [
                {},
                {**inputs, "node": inputs["redis"]},
                {**inputs, "node": "node:latest"},
                {**inputs, "node": "", "runtime": "runtime:latest"},
                {**inputs, "postgres": ""},
            ]:
                with self.assertRaises(ValueError):
                    producer.run_scans(Path(tmp), invalid)


if __name__ == "__main__":
    unittest.main()
