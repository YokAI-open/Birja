#!/usr/bin/env python3
"""Image identity and offline recovery contracts at actual command boundaries."""

import datetime
import copy
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
import tomllib
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
PG = "cgr.dev/chainguard/postgres@sha256:adbf3d8db097696ed6e997b108b51393786be999c04d543502f8959e1bafa8de"
REDIS = "cgr.dev/chainguard/redis@sha256:26bb2dd4412f902f3decd44fba5dfaef4360d97004d44f6cff7f28d6aba19c48"
NODE = "cgr.dev/chainguard/wolfi-base@sha256:24f549a7fcace88e69b9557941168c74645688ecc4acf7fb6d734a6b74e9019d"
WOLFI = "cgr.dev/chainguard/wolfi-base@sha256:24f549a7fcace88e69b9557941168c74645688ecc4acf7fb6d734a6b74e9019d"


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


class Identity(unittest.TestCase):
    def test_ci_recovery_preparation_requires_verification_before_import_and_binding(self):
        spec = importlib.util.spec_from_file_location("check_recovery", ROOT / "deploy/tests/check-recovery-image.py")
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        for failure in (None, "archive", "alias"):
            with self.subTest(failure=failure):
                events = []
                def command(argv, **kwargs):
                    if "load" in argv:
                        events.append("load")
                    return subprocess.CompletedProcess(argv, 0)
                def verify(*args):
                    events.append("verify")
                    if failure == "archive":
                        raise ValueError("unverified archive")
                def alias():
                    events.append("alias")
                    if failure == "alias":
                        raise ValueError("wrong image identity")
                with patch.object(helper.r, "call", return_value=b'[["driver-type","io.containerd.snapshotter.v1"]]'), patch.object(helper.r, "registry_manifests", return_value=(b"index", b"manifest")), patch.object(helper.r, "verify_saved_image", side_effect=verify), patch.object(helper.r, "loaded_recovery_image", side_effect=alias), patch.object(helper.r, "bind_recovery_image", side_effect=lambda: events.append("bind")), patch.object(helper.subprocess, "run", side_effect=command):
                    if failure:
                        with self.assertRaises(ValueError):
                            helper.main()
                        self.assertNotIn("load", events)
                        self.assertNotIn("bind", events)
                    else:
                        helper.main()
                        self.assertEqual(events, ["verify", "alias", "load", "bind"])

    def test_exact_inventory_rejects_unapproved_versions_and_artifact_changes(self):
        parse = tomllib.loads
        for target, field in (("opentelemetry-api", "version"), ("opentelemetry-api", "artifact"), ("dnspython", "version"), ("dnspython", "artifact"), ("fastapi", "artifact")):
            with self.subTest(target=target, field=field):
                def changed(source):
                    value = parse(source)
                    if "package" in value:
                        value = copy.deepcopy(value)
                        record = next(p for p in value["package"] if p["name"] == target)
                        if field == "version":
                            record["version"] = "999.0"
                        else:
                            record["wheels"][0]["hash"] = "sha256:" + "0" * 64
                    return value
                with patch.object(tomllib, "loads", side_effect=changed):
                    with self.assertRaises(AssertionError):
                        self.test_signed_exact_packages_and_complete_group_boundaries()

    def test_anonymous_registry_fixed_origin_and_bounded_graph(self):
        config = json.dumps({"os": "linux", "architecture": "amd64"}).encode()
        manifest = json.dumps({"config": {"digest": sha(config), "size": len(config)}}).encode()
        index = json.dumps({"manifests": [{"digest": sha(manifest), "size": len(manifest), "platform": {"os": "linux", "architecture": "amd64"}}]}).encode()
        seen = []
        class Response(io.BytesIO):
            status = 200
            def geturl(self):
                return self.url
        class Opener:
            def open(self, request, timeout):
                self_test.assertEqual(timeout, 30)
                seen.append(request)
                url = request.full_url
                self_test.assertTrue(url.startswith("https://cgr.dev/"))
                if len(seen) == 1:
                    self_test.assertEqual(url, "https://cgr.dev/token?service=cgr.dev&scope=repository%3Achainguard%2Fpostgres%3Apull")
                    self_test.assertNotIn("Authorization", request.headers)
                    data = b'{"token":"anonymous-test-token"}'
                else:
                    self_test.assertEqual(request.headers["Authorization"], "Bearer anonymous-test-token")
                    data = index if len(seen) == 2 else manifest
                response = Response(data)
                response.url = url
                return response
        self_test = self
        def build(handler):
            with self.assertRaises(ValueError):
                handler().redirect_request(None, None, 302, "redirect", {}, "https://other.invalid/")
            return Opener()
        with patch.object(r.urllib.request, "build_opener", side_effect=build), patch.object(r, "INDEX_DIGEST", sha(index)), patch.object(r, "PLATFORM_DIGEST", sha(manifest)):
            self.assertEqual(r.registry_manifests(), (index, manifest))
        self.assertEqual([request.full_url for request in seen[1:]], ["https://cgr.dev/v2/chainguard/postgres/manifests/" + value for value in [sha(index), sha(manifest)]])

    def test_replacement_layout_entrypoints_and_retained_build_routing(self):
        for name in ["docker-compose.yml", "docker-compose.prod.yml", "docker-compose.test.yml", "docker-compose.ops-test.yml"]:
            source = (ROOT / name).read_text()
            self.assertIn("PGDATA: /var/lib/postgresql/18/docker", source)
            self.assertIn('user: "70:70"', source)
            self.assertNotIn("redis-server --requirepass", source)
            self.assertNotIn('"redis-server", "--requirepass"', source)
            self.assertNotIn("      - postgres\n", source)
        overlay = (ROOT / "deploy/db-security.compose.yml").read_text()
        self.assertEqual(overlay.count("dockerfile: ${BIRJA_OPS_DIR:?retained entrypoint required}/backend/Dockerfile"), 3)
        self.assertIn("'backend/Dockerfile'", (ROOT / "deploy/deploy-entrypoint.sh").read_text())
        self.assertIn("0o640, 70", (ROOT / "deploy/provision-db-tls.sh").read_text())
        self.assertEqual(r.COMPOSE_SHA, hashlib.sha256((ROOT / "docker-compose.ops-test.yml").read_bytes()).hexdigest())

    def test_collation_preflight_fail_closed_before_privileged_sql(self):
        source = (ROOT / "deploy/configure-db.sh").read_text().split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
        source = source.rsplit("\ntry:\n    main()", 1)[0]
        scope = {"__name__": "contract"}
        exec(compile(source, "configure-db.sh", "exec"), scope)
        sql = scope["COLLATION_PREFLIGHT"]
        for required in ["BEGIN READ ONLY", "statement_timeout = '10s'", "pg_database_collation_actual_version", "pg_collation_actual_version", "NOT i.indisvalid", "IS NOT NULL"]:
            self.assertIn(required, sql)
        for forbidden in ["REFRESH", "REINDEX", "UPDATE "]:
            self.assertNotIn(forbidden, sql)
        self.assertLess(source.index("with backup.acquire_operation_lock"), source.index("input=COLLATION_PREFLIGHT.encode()"))
        self.assertLess(source.index('probe.stdout == b"collation_ok\\n"'), source.index('db/bootstrap-roles.sql'))
        with tempfile.TemporaryDirectory(prefix="birja-backup-test-") as tmp:
            root = Path(tmp)
            root.chmod(0o700)
            config = root / "roles.json"
            config.write_text(json.dumps({"project": "birja-ops-test", "db_name": "birja_source_test", "bootstrap": r.BOOT, "password_files": {role: str(root / role) for role in ["app", "scheduler", "migrator"]}}))
            config.chmod(0o600)
            argv = ["script", str(ROOT / "deploy"), "--synthetic", str(config), "--inspect"]
            for status, output in [(0, b"collation_blocked\n"), (0, b""), (1, b"collation_ok\n"), (0, b"collation_ok\nextra")]:
                with patch.object(sys, "argv", argv), patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], status, output, b"")) as run:
                    with self.assertRaises(ValueError):
                        scope["main"]()
                    self.assertEqual(run.call_count, 1)
                    self.assertEqual(run.call_args.kwargs["input"], sql.encode())

    def test_authenticated_optional_attestation_graph_and_tampering(self):
        config = json.dumps({"os": "linux", "architecture": "amd64"}).encode()
        manifest = json.dumps(
            {"config": {"digest": sha(config), "size": len(config)}, "layers": []}
        ).encode()
        mid = sha(manifest)
        att_config, att_layer = b"{}", b"authenticated in-toto statement"
        att_manifest = json.dumps(
            {
                "config": {"digest": sha(att_config), "size": len(att_config)},
                "layers": [
                    {
                        "digest": sha(att_layer),
                        "size": len(att_layer),
                        "mediaType": "application/vnd.in-toto+json",
                    }
                ],
            }
        ).encode()
        aid = sha(att_manifest)
        runnable = {
            "digest": mid,
            "size": len(manifest),
            "platform": {"os": "linux", "architecture": "amd64"},
        }
        attestation = {
            "digest": aid,
            "size": len(att_manifest),
            "platform": {"os": "unknown", "architecture": "unknown"},
            "annotations": {
                "vnd.docker.reference.type": "attestation-manifest",
                "vnd.docker.reference.digest": mid,
            },
        }
        for mutation in [
            None,
            "manifest",
            "config",
            "layer",
            "unknown-root",
            "unknown-blob",
            "subject",
            "size",
            "duplicate",
            "untrusted",
        ]:
            trusted_attestation = json.loads(json.dumps(attestation))
            if mutation == "untrusted":
                trusted_attestation["annotations"]["vnd.docker.reference.digest"] = sha(
                    config
                )
            index = json.dumps({"manifests": [runnable, trusted_attestation]}).encode()
            roots = [
                {"digest": mid, "size": len(manifest)},
                {
                    "digest": aid,
                    "size": len(att_manifest),
                    "annotations": {
                        "io.containerd.manifest.subject": sha(config)
                        if mutation == "subject"
                        else mid
                    },
                },
            ]
            if mutation == "size":
                roots[1]["size"] += 1
            if mutation == "duplicate":
                roots.append(roots[1])
            if mutation == "unknown-root":
                roots.append({"digest": "sha256:" + "0" * 64, "size": 1})
            files = {
                "manifest.json": json.dumps(
                    [{"Config": "blobs/sha256/" + sha(config)[7:], "Layers": []}]
                ).encode(),
                "index.json": json.dumps({"manifests": roots}).encode(),
            }
            for name, data in [
                ("runnable-config", config),
                ("runnable-manifest", manifest),
                ("manifest", att_manifest),
                ("config", att_config),
                ("layer", att_layer),
            ]:
                files["blobs/sha256/" + sha(data)[7:]] = (
                    data + b"tampered" if mutation == name else data
                )
            if mutation == "unknown-blob":
                files["blobs/sha256/" + "0" * 64] = b"unknown"
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
                patch.object(r, "IMAGE_ID", sha(config)),
            ):
                if mutation is None:
                    r.verify_saved_image(saved, index, manifest)
                else:
                    with self.assertRaises(ValueError, msg=mutation):
                        r.verify_saved_image(saved, index, manifest)

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
        backend = (ROOT / "backend/Dockerfile").read_text()
        self.assertIn("FROM " + WOLFI + " AS python-base", backend)
        self.assertIn("FROM python-base AS builder", backend)
        self.assertIn("FROM python-base AS runtime", backend)
        for filename in [
            "docker-compose.yml",
            "docker-compose.test.yml",
            "docker-compose.prod.yml",
        ]:
            source = (ROOT / filename).read_text()
            self.assertIn("image: " + PG, source)
            self.assertIn("image: " + REDIS, source)
        self.assertIn("FROM " + WOLFI, (ROOT / "frontend/Dockerfile").read_text())
        self.assertIn(
            "NODE_BASE_IMAGE=" + NODE, (ROOT / "deploy/deploy.sh").read_text()
        )

    def test_signed_exact_packages_and_complete_group_boundaries(self):
        backend = (ROOT / "backend/Dockerfile").read_text()
        frontend = (ROOT / "frontend/Dockerfile").read_text()
        self.assertIn("python-3.14=3.14.10_git20261104-r0", backend)
        self.assertIn("python-3.14-base=3.14.10_git20261104-r0", backend)
        self.assertIn("nodejs-24=24.22.3-r0", frontend)
        for pin in ("icu79-data-full=79.1-r1", "libicu79=79.1-r1", "libstdc++=16.2.0-r2"):
            self.assertIn(pin, frontend)
        self.assertIn("ghcr.io/astral-sh/uv:0.13.5", backend)
        for source in [backend, frontend]:
            self.assertIn("apk add --no-cache", source)
            for forbidden in ["--allow-untrusted", "site-packages/pip", "dist-info", "--ignore-unfixed", "--skip-files", "--skip-dirs"]:
                self.assertNotIn(forbidden, source)
        self.assertIn("uv sync --locked --no-install-project --no-default-groups\n", backend)
        self.assertIn("uv sync --locked --no-install-project --no-default-groups --group dev", backend)
        project = tomllib.loads((ROOT / "backend/pyproject.toml").read_text())
        self.assertEqual(set(project["tool"]["uv"]["default-groups"]), {"dev", "audit"})
        self.assertEqual(project["dependency-groups"]["audit"], ["pip-audit>=2.10.1"])
        self.assertFalse(any("pip-audit" in dep for dep in project["dependency-groups"]["dev"]))
        # Regrouping must retain every locked version and distribution artifact.
        current = tomllib.loads((ROOT / "backend/uv.lock").read_text())
        distributions = {
            p["name"]: p for p in current["package"]
            if p["name"] != "birja-backend"
        }
        # Canonical pre-regrouping inventory from e728855, including artifacts.
        # A digest keeps this contract usable in shallow CI checkouts.
        approved = {"exchange-calendars": "4.13.2", "numpy": "2.5.4", "pandas": "3.1.1", "pyluach": "2.3.0", "toolz": "1.2.0", "tzdata": "2026.6", "korean-lunar-calendar": "0.4.0", "python-dateutil": "4.0.0"}
        self.assertEqual({name: distributions[name]["version"] for name in approved}, approved)
        additions = {name: distributions.pop(name) for name in approved}
        # Exact reviewed wheels/sdist/source metadata, not just name/version.
        self.assertEqual(hashlib.sha256(json.dumps(additions, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), "e46b91fbe9b2d6fc9de6f974163816c14714b70b47b7751cd5bbf8bb24fadbd7")
        # Independently approved exact repairs: Phase11 OTEL and PR31 DNS.
        # Authenticate complete records; retain e728855's other records unchanged.
        otel = distributions.pop("opentelemetry-api")
        self.assertEqual(otel["version"], "1.45.2")
        self.assertEqual(hashlib.sha256(json.dumps(otel, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), "430ea33d87934b313fdff4a8ab39650757a7748c55f21d738f3a09d63b2b9c2c")
        dns = distributions.pop("dnspython")
        self.assertEqual(dns["version"], "2.9.2")
        self.assertEqual(hashlib.sha256(json.dumps(dns, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), "4ad11523a6d2c2d0989a1eb5dd28d6edfa8c86170728ffc04ca47e1b173d3f79")
        encoded = json.dumps(distributions, sort_keys=True, separators=(",", ":"))
        self.assertEqual(
            hashlib.sha256(encoded.encode()).hexdigest(),
            "e7415d7142069e6bca45afd4d37cd758a1d7c83ddd401a678b1b054c9b7b9509",
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
                                    "Tmpfs": {"/var/lib/postgresql": "size=268435456,uid=70,gid=70,mode=0750"},
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
                self.assertEqual(argv[argv.index("--user") + 1], "1001:1002")
                self.assertIn("--read-only", argv)
                self.assertIn("--cap-drop=ALL", argv)
                self.assertIn("--security-opt=no-new-privileges", argv)
                self.assertNotIn("/var/run/docker.sock", " ".join(argv))
                self.assertIn("HIGH,CRITICAL", argv)
                self.assertNotIn("--ignore-unfixed", argv)
                seen.append(argv)
                # The fake scanner writes the real mounted cache DB metadata.
                mount = next(arg for arg in argv if arg.endswith(",dst=/cache"))
                cache = Path(mount.split("src=", 1)[1].split(",dst=", 1)[0])
                self.assertEqual(cache.stat().st_mode & 0o777, 0o700)
                self.assertEqual(cache.parent.stat().st_mode & 0o777, 0o700)
                archive_mount = next(
                    arg for arg in argv if arg.endswith(",dst=/scan/image.tar,readonly")
                )
                archive = Path(archive_mount.split("src=", 1)[1].split(",dst=", 1)[0])
                self.assertEqual(archive.stat().st_mode & 0o777, 0o600)
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
                patch.object(producer.os, "geteuid", return_value=1001),
                patch.object(producer.os, "getegid", return_value=1002),
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
