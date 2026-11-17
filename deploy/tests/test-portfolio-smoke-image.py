#!/usr/bin/env python3
"""Offline current-image provenance regressions; no database or Docker daemon."""

import importlib.util
import io
import json
import subprocess
import tarfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


def load(name):
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


smoke = load("portfolio-smoke")
sources_module = load("portfolio-sources")
COMMIT = "a" * 40
APP_TREE = "b" * 40
IMAGE = "sha256:" + "c" * 64
DOCKERFILE = b"FROM approved-pinned-base AS runtime\nCOPY app /app/app\nUSER app\n"


def payload():
    result = io.BytesIO()
    with tarfile.open(fileobj=result, mode="w") as archive:
        for name, data in (
            ("backend/Dockerfile", DOCKERFILE),
            ("backend/uv.lock", b"version = 1\n"),
            ("backend/app/__init__.py", b"# frozen source\n"),
            ("backend/alembic/env.py", b"# frozen migration\n"),
        ):
            member = tarfile.TarInfo(name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    return result.getvalue()


class Sources:
    image_binding = staticmethod(sources_module.image_binding)
    verify_image = staticmethod(sources_module.verify_image)
    verify_source_tree = staticmethod(sources_module.verify_source_tree)

    def __init__(self, *, dirty=False):
        self.dirty = dirty
        self.head = COMMIT
        self.payload = payload()

    def git(self, *args):
        if args == ("rev-parse", "HEAD"):
            return self.head.encode()
        if args in (("rev-parse", COMMIT + ":backend/app"), ("rev-parse", "HEAD:backend/app")):
            return APP_TREE.encode()
        if args[:2] == ("diff", "--name-only"):
            return b"backend/Dockerfile\n" if self.dirty else b""
        if args in (("archive", COMMIT, "backend"), ("archive", "HEAD", "backend")):
            return self.payload
        raise AssertionError("unqualified Git input: " + repr(args))


class ImageCommands:
    def __init__(self, sources):
        self.sources = sources
        self.calls = []
        self.image = [{"Id": IMAGE, "Config": {
            "Labels": {"org.opencontainers.image.revision": COMMIT}, "User": "app"
        }, "RootFS": {"Type": "layers", "Layers": ["sha256:" + "d" * 64]}}]
        self.fail_build = False
        self.change_head = False
        self.mutate_context = False

    def __call__(self, argv, **kwargs):
        self.calls.append(argv)
        if argv[:2] == ["docker", "build"]:
            self.assert_build(argv, kwargs)
            if self.fail_build:
                return SimpleNamespace(returncode=1, stdout=b"", stderr=b"build failed")
            if self.change_head:
                self.sources.head = "e" * 40
            if self.mutate_context:
                (Path(argv[-1]) / "app/__init__.py").write_text("substituted")
            return SimpleNamespace(returncode=0, stdout=b"build complete", stderr=b"")
        if argv[:3] == ["docker", "image", "inspect"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps(self.image).encode(), stderr=b"")
        raise AssertionError("unexpected Docker operation: " + repr(argv))

    def assert_build(self, argv, kwargs):
        assert argv[argv.index("--target") + 1] == "runtime"
        context = Path(argv[-1])
        assert context.name == "backend"
        assert (context / "Dockerfile").read_bytes() == DOCKERFILE
        assert (context / "uv.lock").read_bytes() == b"version = 1\n"
        assert (context / "app/__init__.py").read_bytes() == b"# frozen source\n"
        assert not (context.parent / "Smoke.Dockerfile").exists()
        assert "DOCKER_BUILDKIT" not in kwargs["env"]
        assert kwargs["timeout"] == 600


class CurrentImageContracts(unittest.TestCase):
    def test_builds_declared_frozen_runtime_before_first_use_and_rechecks_id(self):
        source = Sources()
        command = ImageCommands(source)
        binding = smoke.build_current_runtime(source, {"PATH": "/synthetic/bin"}, run=command)
        self.assertEqual(binding["id"], IMAGE)
        self.assertEqual(binding["source_commit"], COMMIT)
        self.assertEqual(binding["app_tree"], APP_TREE)
        self.assertEqual(command.calls[0][:2], ["docker", "build"])
        self.assertEqual(command.calls[-1], ["docker", "image", "inspect", IMAGE])
        self.assertFalse(any(argv[:2] == ["docker", "run"] for argv in command.calls))

    def test_dirty_backend_refuses_before_any_image_command(self):
        source = Sources(dirty=True)
        command = ImageCommands(source)
        with self.assertRaisesRegex(ValueError, "frozen"):
            smoke.build_current_runtime(source, {}, run=command)
        self.assertEqual(command.calls, [])

    def test_build_failure_never_inspects_or_adopts_existing_image(self):
        source = Sources()
        command = ImageCommands(source)
        command.fail_build = True
        with self.assertRaisesRegex(AssertionError, "runtime image build failed"):
            smoke.build_current_runtime(source, {}, run=command)
        self.assertEqual(len(command.calls), 1)

    def test_source_or_extracted_context_change_during_build_refuses(self):
        for field in ("change_head", "mutate_context"):
            source = Sources()
            command = ImageCommands(source)
            setattr(command, field, True)
            with self.subTest(field=field), self.assertRaises(ValueError):
                smoke.build_current_runtime(source, {}, run=command)

    def test_mismatched_revision_or_changed_immutable_image_refuses(self):
        for field in ("revision", "rootfs"):
            source = Sources()
            command = ImageCommands(source)
            if field == "revision":
                command.image[0]["Config"]["Labels"]["org.opencontainers.image.revision"] = "f" * 40
            else:
                original = command.__call__
                changing_command = command

                def changing(argv, **kwargs):
                    if argv == ["docker", "image", "inspect", IMAGE]:
                        changing_command.image[0]["RootFS"]["Layers"] = ["changed"]
                    return original(argv, **kwargs)

                command = changing
            with self.subTest(field=field), self.assertRaises(ValueError):
                smoke.build_current_runtime(source, {}, run=command)

    def test_real_smoke_dispatch_requires_the_declared_runtime_factory(self):
        ready = RuntimeError("image factory reached before database")
        source = Sources()

        def clean_runner(argv, **kwargs):
            if argv[:2] == ["uv", "export"]:
                return subprocess.CompletedProcess(argv, 0, b"approved==1.0\n", b"")
            if argv[:2] == ["docker", "run"]:
                return subprocess.CompletedProcess(argv, 1, b"", b"local cached runtime absent")
            return subprocess.CompletedProcess(argv, 0, b"", b"")

        with mock.patch.object(smoke, "load", side_effect=lambda name: source if name == "portfolio-sources" else object()), \
             mock.patch.object(smoke.subprocess, "run", side_effect=clean_runner), \
             mock.patch.object(smoke, "build_current_runtime", side_effect=ready, create=True) as factory:
            with self.assertRaisesRegex(RuntimeError, "image factory reached before database"):
                smoke.run()
        factory.assert_called_once()


if __name__ == "__main__":
    unittest.main()
