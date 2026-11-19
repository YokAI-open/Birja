#!/usr/bin/env python3
"""Offline current-image provenance regressions; no database or Docker daemon."""

import ast
import hashlib
import importlib.util
import os
import io
import json
import subprocess
import tarfile
import tempfile
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


class FreshAuthority(unittest.TestCase):
    def test_campaign_alias_and_id_both_bind_exact_image_without_rebuild(self):
        with tempfile.TemporaryDirectory(prefix='birja-backup-test-alias-') as temporary:
            root = Path(temporary)
            archive = root / 'recovery.tar'
            archive.write_bytes(b'qualified')
            archive.chmod(0o600)
            sha = hashlib.sha256(archive.read_bytes()).hexdigest()
            image = [{'Id':IMAGE, 'Config':{'Labels':{'org.opencontainers.image.revision':COMMIT}},
                      'RootFS':{'Type':'layers','Layers':['sha256:'+'d'*64]}}]
            binding = sources_module.image_binding(image, source_commit=COMMIT,
                app_tree=APP_TREE, context_sha256='e'*64)
            record = root / 'current0023-image-binding.json'
            record.write_text(json.dumps(binding))
            record.chmod(0o400)
            alias = smoke.campaign_image_tag('birja-portfolio-current:'+COMMIT[:12]+'-'+'e'*20, archive)
            calls = []
            def inspect(ref):
                calls.append(ref)
                return image
            smoke.authenticate_campaign_images(archive, sha, inspect_image=inspect)
            self.assertEqual(calls, [IMAGE, alias])
            def substituted(ref):
                return image if ref == IMAGE else [{**image[0], 'Id':'sha256:'+'f'*64}]
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                smoke.authenticate_campaign_images(archive, sha, inspect_image=substituted)
            def missing(ref):
                if ref == alias:
                    raise subprocess.CalledProcessError(1, ['docker','image','inspect'])
                return image
            with self.assertRaises(subprocess.CalledProcessError):
                smoke.authenticate_campaign_images(archive, sha, inspect_image=missing)

    def test_retained_writer_uses_its_own_consumer_and_refuses_current_before_writes(self):
        code = smoke.retained_writer_refusal_program()
        compile(code, '<retained-writer>', 'exec')
        self.assertLess(code.index('revision !='), code.index('from app.db.schema_contract'))
        self.assertIn('except SchemaAdmissionError', code)
        self.assertIn("session_user=='birja_app'", code)
        self.assertNotIn('INSERT', code)
        self.assertNotIn('UPDATE', code)

    def test_fresh_program_migrates_directly_to_current_and_uses_real_roles(self):
        code = smoke.fresh_authority_program()
        compile(code, '<fresh0023>', 'exec')
        self.assertIn("command.upgrade,Config('/app/alembic.ini'),'0023'", code)
        self.assertNotIn("'0017'", code)
        self.assertIn('GRANTS_0023_SQL', code)
        self.assertIn('create_portfolio', code)
        checked = smoke.closure_role_program(code)
        compile(checked, '<fresh0023-role-checks>', 'exec')
        function = next(node for node in ast.parse(checked).body
                        if isinstance(node, ast.AsyncFunctionDef) and node.name == 'run')
        local_imports = {alias.asname or alias.name for node in ast.walk(function)
                         if isinstance(node, ast.ImportFrom) for alias in node.names}
        self.assertNotIn('ClosureIntent', local_imports)
        self.assertNotIn('close_portfolio', local_imports)
        self.assertNotIn('AsyncSession', local_imports)
        self.assertIn('require_schema(restricted)', checked)
        self.assertIn('portfolio_authority=', checked)
        self.assertIn('DEFAULT_ACL_0023_SHA256', checked)
        self.assertIn('implicit public function defaults admitted', checked)
        self.assertIn('portfolio_verified_tls=true', code)

    def test_upgraded_program_preserves_complete_before_rows_and_identity_tails(self):
        code = smoke.closure_role_program(smoke.fresh_authority_program(upgraded=True))
        compile(code, '<populated0020-to0023-tls>', 'exec')
        self.assertIn('UPGRADED=True', code)
        self.assertIn('assert await snapshot(conn)==before', code)
        self.assertLess(
            code.index("assert await require_migrator(conn)==UPGRADED_FROM"),
            code.index("command.upgrade,Config('/app/alembic.ini'),'0023'"),
        )
        self.assertIn('last_value,is_called', code)
        self.assertIn('close_portfolio(db,original_intent)', code)
        retained = smoke.fresh_authority_program('0020')
        self.assertIn("command.upgrade,Config('/app/alembic.ini'),'0020'", retained)
        self.assertNotIn('0023', retained)

    def test_legacy14_oracle_retains_every_old_financial_column_and_tail(self):
        code = smoke.fresh_authority_program(upgraded=True, upgraded_from='0014')
        compile(code, '<legacy14-to23>', 'exec')
        values = {node.targets[0].id:ast.literal_eval(node.value) for node in ast.parse(code).body
                  if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name)
                  and node.targets[0].id in {'OLD_TABLES','OLD_IDENTITIES','EXTRA_COLUMNS','UPGRADED_FROM'}}
        producer = smoke.load('portfolio-closure-recovery-fixture').producer()
        old = producer.contract_columns('0014')
        current = producer.contract_columns('0023')
        self.assertEqual(values['OLD_TABLES'],sorted(old))
        self.assertEqual(values['OLD_IDENTITIES'],producer.identity_tables('0014'))
        for table, columns in old.items():
            extras = set(values['EXTRA_COLUMNS'][table])
            self.assertFalse(extras & columns)
            self.assertEqual(columns | extras,current[table])
        self.assertIn("==before",code)
        self.assertIn("=='legacy'",code)
        self.assertIn("portfolio_creations WHERE portfolio_id=:p",code)
        self.assertIn("Decimal('8765')",code)
        self.assertIn("Decimal('.001'),Decimal('12.34')",code)
        for kwargs in ({'upgraded':False,'upgraded_from':'0014'},
                       {'upgraded':True,'upgraded_from':'0017'}):
            with self.assertRaises(ValueError):
                smoke.fresh_authority_program(**kwargs)

    def test_selected_fresh_refuses_retained_before_build(self):
        with mock.patch.object(smoke, 'build_selected_runtime', side_effect=AssertionError('build')):
            with self.assertRaisesRegex(ValueError, 'fresh'):
                smoke.run(revision='0017', fresh_bootstrap=True)


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

    profile_for = staticmethod(sources_module.profile_for)
    source_archive = staticmethod(sources_module.source_archive)
    verify_archive_binding = staticmethod(sources_module.verify_archive_binding)
    record_image_binding = staticmethod(sources_module.record_image_binding)

    def __init__(self, *, dirty=False):
        self.dirty = dirty
        self.head = COMMIT
        self.payload = payload()

    def git(self, *args):
        if args == ("rev-parse", "HEAD"):
            return self.head.encode()
        if args in (
            ("rev-parse", COMMIT + ":backend/app"),
            ("rev-parse", "HEAD:backend/app"),
        ):
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
        self.image = [
            {
                "Id": IMAGE,
                "Config": {
                    "Labels": {"org.opencontainers.image.revision": COMMIT},
                    "User": "app",
                },
                "RootFS": {"Type": "layers", "Layers": ["sha256:" + "d" * 64]},
            }
        ]
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
            return SimpleNamespace(
                returncode=0, stdout=json.dumps(self.image).encode(), stderr=b""
            )
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
    def test_prepared14_requires_explicit_diagnostic_and_preimport_authority(self):
        code = smoke.fresh_authority_program(upgraded=True, upgraded_from='0014')
        current = smoke.admitted_program(code, '0023', prepared_legacy14=True)
        compile(current, '<prepared14>', 'exec')
        self.assertIn("version_num FROM alembic_version')!='0014'", current)
        self.assertIn("if await require_migrator(authority)!='0014'", current)
        self.assertLess(current.index('require_source()'), current.index('asyncio.run(smoke_admit())'))
        self.assertLess(current.index('asyncio.run(smoke_admit())'), current.rindex('from app.services.portfolio_closure import'))
        self.assertIn('SMOKE_LEGACY14=False', smoke.admitted_program(code, '0023'))
        for wrong, revision in ((code, '0020'), (code, '0017'),
                (smoke.fresh_authority_program(upgraded=True), '0023'),
                (smoke.fresh_authority_program(), '0023')):
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                smoke.admitted_program(wrong, revision, prepared_legacy14=True)

    def test_program_admits_schema_before_application_imports_and_wires_roles(self):
        fixture = smoke.selected_fixture(sources_module, '0023')
        for mode in ('create', 'verify', 'projection'):
            code = fixture.program(mode=mode)
            current = smoke.admitted_program(smoke.closure_role_program(code), '0023')
            compile(current, '<current0023-tls>', 'exec')
            self.assertLess(current.index('asyncio.run(smoke_admit())'), current.rindex('from sqlalchemy.ext.asyncio import'))
            self.assertIn("for role,client in (('app',app),('scheduler',scheduler))", current)
            self.assertIn('result.replayed', current)
            self.assertIn('DEFAULT_ACL_0023_SQL', current)
        management = smoke.selected_fixture(sources_module, '0020')
        self.addCleanup(management._source_directory.cleanup)
        code = management.program(mode='verify')
        self.assertIn('0020 source mismatch before import', code)
        self.assertNotIn('0023', management.SOURCE_SHA256)
        self.assertNotEqual(management.ROOT, smoke.ROOT)
        retained = smoke.selected_fixture(sources_module, '0017')
        self.addCleanup(retained._source_directory.cleanup)
        code = smoke.admitted_program(retained.program(mode='verify'), '0017')
        compile(code, '<retained0017-tls>', 'exec')
        self.assertLess(code.index('asyncio.run(smoke_admit())'), code.rindex('from app.core.config import'))
        self.assertNotIn('management_role', code)

    def test_selected_schema_source_refuses_unsupported_before_build(self):
        for revision in ("0018", "0019", "head", "0021"):
            command = ImageCommands(Sources())
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                smoke.build_selected_runtime(
                    Sources(), {}, revision=revision, run=command
                )
            self.assertEqual(command.calls, [])

    def test_retained_runtime_uses_the_complete_fixed_source(self):
        calls = []
        profile = sources_module.profile_for("0017")
        image = [
            {
                "Id": IMAGE,
                "Config": {
                    "Labels": {"org.opencontainers.image.revision": profile["commit"]},
                    "User": "app",
                },
                "RootFS": {"Type": "layers", "Layers": ["fixed"]},
            }
        ]

        def command(argv, **kwargs):
            calls.append(argv)
            if argv[:2] == ["docker", "build"]:
                context = Path(argv[-1])
                self.assertEqual(
                    (context / "app/db/portfolio_bootstrap.py").read_bytes(),
                    sources_module.git(
                        "show",
                        profile["commit"] + ":backend/app/db/portfolio_bootstrap.py",
                    ),
                )
                self.assertFalse(
                    (
                        context
                        / "alembic/versions/0020_portfolio_management_authority.py"
                    ).exists()
                )
            return subprocess.CompletedProcess(argv, 0, json.dumps(image).encode(), b"")

        binding = smoke.build_selected_runtime(
            sources_module, {}, revision="0017", run=command
        )
        self.assertEqual(binding["source_commit"], profile["commit"])
        self.assertEqual(calls[0][:2], ["docker", "build"])

    def test_builds_declared_frozen_runtime_before_first_use_and_rechecks_id(self):
        source = Sources()
        command = ImageCommands(source)
        binding = smoke.build_current_runtime(
            source, {"PATH": "/synthetic/bin"}, run=command
        )
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
                command.image[0]["Config"]["Labels"][
                    "org.opencontainers.image.revision"
                ] = "f" * 40
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
                return subprocess.CompletedProcess(
                    argv, 1, b"", b"local cached runtime absent"
                )
            return subprocess.CompletedProcess(argv, 0, b"", b"")

        with (
            mock.patch.object(
                smoke,
                "load",
                side_effect=lambda name: (
                    source if name == "portfolio-sources" else object()
                ),
            ),
            mock.patch.object(smoke, "selected_fixture", return_value=object()),
            mock.patch.object(
                smoke,
                "build_selected_runtime",
                side_effect=lambda *a, **k: smoke.build_current_runtime(*a),
            ),
            mock.patch.object(smoke.subprocess, "run", side_effect=clean_runner),
            mock.patch.object(
                smoke, "build_current_runtime", side_effect=ready, create=True
            ) as factory,
        ):
            with self.assertRaisesRegex(
                RuntimeError, "image factory reached before database"
            ):
                smoke.run()
        factory.assert_called_once()


class CampaignImageContracts(unittest.TestCase):
    def campaign(self, revision):
        temporary = tempfile.TemporaryDirectory(prefix="birja-image-contract-")
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        archive = directory / "recovery.tar"
        archive.write_bytes(b"independent authenticated synthetic recovery archive")
        archive.chmod(0o400)
        sha = hashlib.sha256(archive.read_bytes()).hexdigest()
        source = Sources()
        source.source_archive = lambda lane, **kwargs: (
            sources_module.verify_archive_binding(kwargs["archive"], kwargs["archive_sha"])
            or source.payload
        )
        command = ImageCommands(source)
        if revision != "0023":
            command.image[0]["Config"]["Labels"]["org.opencontainers.image.revision"] = source.profile_for(revision)["commit"]
        return archive, sha, source, command

    def invoke(self, revision, archive, sha, source, command):
        # Reloading the module models separate stage invocations: the file,
        # rather than process-local memory, is the first-use identity authority.
        return load("portfolio-smoke").build_selected_runtime(
            source, {}, revision=revision, archive=archive, archive_sha=sha, run=command
        )

    def test_repeated_current_and_retained_use_original_id_without_rebuild(self):
        for revision in ("0017", "0020", "0023"):
            with self.subTest(revision=revision):
                archive, sha, source, command = self.campaign(revision)
                first = self.invoke(revision, archive, sha, source, command)
                record = archive.parent / ("current" + revision + "-image-binding.json")
                self.assertTrue(record.is_file(), "first use must persist its campaign identity")
                self.assertEqual(record.stat().st_mode & 0o777, 0o400)
                before = record.read_bytes()
                second = self.invoke(revision, archive, sha, source, command)
                self.assertEqual(first, second)
                self.assertEqual(record.read_bytes(), before)
                self.assertEqual(sum(argv[:2] == ["docker", "build"] for argv in command.calls), 1)
                self.assertEqual(command.calls[-1], ["docker", "image", "inspect", first["id"]])

    def test_recorded_missing_or_reindexed_same_content_image_never_rebuilds(self):
        for revision in ("0017", "0020", "0023"):
            for mutation in ("missing", "id", "config", "rootfs"):
                with self.subTest(revision=revision, mutation=mutation):
                    archive, sha, source, command = self.campaign(revision)
                    first = self.invoke(revision, archive, sha, source, command)
                    record = archive.parent / ("current" + revision + "-image-binding.json")
                    before = record.read_bytes()
                    if mutation == "id":
                        command.image[0]["Id"] = "sha256:" + "e" * 64
                    elif mutation == "config":
                        command.image[0]["Config"]["User"] = "root"
                    elif mutation == "rootfs":
                        command.image[0]["RootFS"]["Layers"] = ["changed"]
                    def missing(argv, **kwargs):
                        if mutation == "missing" and argv == ["docker", "image", "inspect", first["id"]]:
                            command.calls.append(argv)
                            return subprocess.CompletedProcess(argv, 1, b"", b"missing")
                        return command(argv, **kwargs)
                    with self.assertRaises(ValueError):
                        self.invoke(revision, archive, sha, source, missing)
                    self.assertEqual(record.read_bytes(), before)
                    self.assertEqual(sum(argv[:2] == ["docker", "build"] for argv in command.calls), 1)

    def test_unsafe_or_wrong_campaign_record_refuses_before_docker(self):
        for mutation in ("mode", "symlink", "source_commit", "app_tree", "context_sha256", "id", "json"):
            with self.subTest(mutation=mutation):
                archive, sha, source, command = self.campaign("0023")
                self.invoke("0023", archive, sha, source, command)
                record = archive.parent / "current0023-image-binding.json"
                if mutation == "mode":
                    record.chmod(0o644)
                elif mutation == "symlink":
                    original = archive.parent / "original.json"
                    record.rename(original)
                    record.symlink_to(original)
                elif mutation == "json":
                    record.chmod(0o600)
                    record.write_text("{")
                else:
                    value = json.loads(record.read_text())
                    value[mutation] = "wrong"
                    record.chmod(0o600)
                    record.write_text(json.dumps(value))
                    record.chmod(0o400)
                command.calls.clear()
                with self.assertRaises(ValueError):
                    self.invoke("0023", archive, sha, source, command)
                self.assertEqual(command.calls, [])

    def test_changed_archive_dirty_source_or_unsafe_parent_never_reuses(self):
        for mutation in ("archive", "dirty", "parent", "owner"):
            with self.subTest(mutation=mutation):
                archive, sha, source, command = self.campaign("0023")
                self.invoke("0023", archive, sha, source, command)
                if mutation == "archive":
                    archive.chmod(0o600)
                    archive.write_bytes(b"changed")
                elif mutation == "dirty":
                    source.dirty = True
                elif mutation == "parent":
                    archive.parent.chmod(0o755)
                command.calls.clear()
                if mutation == "owner":
                    with mock.patch.object(smoke.os, "getuid", return_value=os.getuid() + 1):
                        with self.assertRaises(ValueError):
                            # Use the patched module specifically for ownership.
                            smoke.build_selected_runtime(source, {}, revision="0023", archive=archive, archive_sha=sha, run=command)
                else:
                    with self.assertRaises(ValueError):
                        self.invoke("0023", archive, sha, source, command)
                self.assertEqual(command.calls, [])

    def test_new_campaign_does_not_adopt_another_campaign_tag(self):
        archive, sha, source, command = self.campaign("0023")
        self.invoke("0023", archive, sha, source, command)
        archive2, sha2, source2, command2 = self.campaign("0023")
        self.invoke("0023", archive2, sha2, source2, command2)
        first_tag = next(argv[argv.index("-t") + 1] for argv in command.calls if argv[:2] == ["docker", "build"])
        second_tag = next(argv[argv.index("-t") + 1] for argv in command2.calls if argv[:2] == ["docker", "build"])
        self.assertNotEqual(first_tag, second_tag)
        self.assertEqual(command2.calls[0][:2], ["docker", "build"])


if __name__ == "__main__":
    unittest.main()
