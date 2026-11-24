#!/usr/bin/env python3
"""Successor campaign contracts. Command doubles are not qualification receipts."""

import importlib.util
import ast
import json
import re
import unittest
import hashlib
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import io
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("validation", ROOT / "deploy/tests/run-portfolio-validation.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class CurrentCampaign(unittest.TestCase):
    def test_actual_db_config_admits_exact_phase15_preflight_project(self):
        script = (ROOT / "deploy/tests/test-db-config.sh").read_text()
        program = script.split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
        tree = ast.parse(program)
        gate = next(node for node in tree.body if isinstance(node, ast.If))
        self.assertIsInstance(gate.test, ast.UnaryOp)
        self.assertIsInstance(gate.test.op, ast.Not)
        call = gate.test.operand
        self.assertEqual(ast.unparse(call.func), "re.fullmatch")
        pattern = ast.literal_eval(call.args[0])
        for accepted in ("birja-test", "birja-p14-16-preflight", "birja-p15-01-preflight"):
            self.assertIsNotNone(re.fullmatch(pattern, accepted))
        for refused in ("birja-p15-02-preflight", "birja-p16-01-preflight", "birja-prod"):
            self.assertIsNone(re.fullmatch(pattern, refused))
        self.assertIn('"birja-p15-01-preflight"', (ROOT / "deploy/tests/run-portfolio-validation.py").read_text())

    def test_finite_phase_selection_and_current_only_dry_run(self):
        self.assertEqual(runner.archive_for_phase(), runner.ARCHIVE)
        self.assertEqual(str(runner.archive_for_phase(15)), "/tmp/birja-phase15-proof/recovery.tar.gz")
        for phase in (13, 16, True, "15"):
            with self.subTest(phase=phase), self.assertRaises(ValueError):
                runner.archive_for_phase(phase)
        with self.assertRaises(ValueError):
            runner.validate_selection("recovery-current")
        for argv, stages in ((["--suite", "recovery", "--dry-run"], runner.STAGES),
                             (["--phase", "15", "--suite", "recovery-current", "--dry-run"], ("current0023-cold",))):
            output = io.StringIO()
            with redirect_stdout(output):
                runner.main(argv)
            result = json.loads(output.getvalue())
            self.assertEqual(result["stages"], list(stages))
            self.assertEqual(result["archive"], str(runner.archive_for_phase(result["phase"])))
        with redirect_stdout(io.StringIO()), patch.object(runner, "execute_recovery", side_effect=AssertionError("execution")):
            with self.assertRaises(SystemExit):
                runner.main(["--suite", "recovery-current", "--dry-run"])

    def test_current_stage_authenticates_failure_and_validates_real_result_shape(self):
        for outcome in (["a" * 64, "b" * 64, "c" * 64], None, RuntimeError("failed current")):
            events = []
            def operation():
                events.append("current")
                if isinstance(outcome, Exception):
                    raise outcome
                return outcome
            actions = {"current0023-cold": operation}
            guard = lambda: events.append("authenticate")
            if isinstance(outcome, Exception):
                with self.assertRaisesRegex(RuntimeError, "failed current"):
                    runner.execute_current_stage(actions, guard)
            elif outcome is None:
                with self.assertRaisesRegex(ValueError, "authority"):
                    runner.execute_current_stage(actions, guard)
            else:
                self.assertEqual(runner.execute_current_stage(actions, guard), outcome)
            self.assertEqual(events, ["authenticate", "current", "authenticate"])

    def test_current_execution_retains_component_only_flags_and_full_marker_boundary(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory(prefix="birja-backup-test-current-dispatch-") as tmp:
            archive = Path(tmp) / "proof/recovery.tar.gz"
            fake = SimpleNamespace(
                r=SimpleNamespace(private=lambda *a: None, digest=lambda p: "a" * 64,
                                  bundle_verify=lambda *a, **k: None),
                package_current_archive=lambda p: p.write_bytes(b"packaging-boundary"),
                bind_source_archive=lambda *a: None,
            )
            authority = ["a" * 64, "b" * 64, "c" * 64]
            calls = []
            def operations(*args):
                return {name: (lambda name=name: calls.append(name) or authority) for name in runner.STAGES}
            output = io.StringIO()
            with patch.object(runner, "PHASE15_ARCHIVE", archive), patch.object(runner, "load", return_value=fake), \
                 patch.object(runner, "preserved_archive", return_value=None), \
                 patch.object(runner, "preserved_phase14_archive", return_value=None), \
                 patch.object(runner, "campaign_sources", return_value={}), \
                 patch.object(runner, "authenticate"), patch.object(runner, "recovery_operations", side_effect=operations), \
                 redirect_stdout(output):
                runner.execute_recovery(phase=15, suite="recovery-current")
            status = json.loads((archive.parent / "status.json").read_text())
            self.assertEqual(calls, ["current0023-cold"])
            self.assertEqual(status["authority"], authority)
            self.assertTrue(status["ok"])
            self.assertFalse(status["whole7"])
            self.assertFalse(status["same_archive_final_ci"])
            self.assertNotIn("same_archive_final_ci=true", output.getvalue())

    def test_phase14_preserved_archive_must_remain_exact_when_present(self):
        with tempfile.TemporaryDirectory(prefix="birja-backup-test-phase14-preserved-") as tmp:
            archive = Path(tmp) / "prior.tar"
            with patch.object(runner, "ARCHIVE", archive), \
                 patch.object(runner, "PHASE14_SHA256", hashlib.sha256(b"qualified").hexdigest()):
                self.assertIsNone(runner.preserved_phase14_archive())
                archive.write_bytes(b"qualified")
                self.assertEqual(runner.preserved_phase14_archive(), runner.PHASE14_SHA256)
                archive.write_bytes(b"changed")
                with self.assertRaisesRegex(ValueError, "changed"):
                    runner.preserved_phase14_archive()

    def test_consumer_admits_only_exact_new_phase15_archive_path(self):
        recovery = runner.load("portfolio-smoke").load_recovery()
        with patch.object(recovery, "private", side_effect=lambda path, *a: path):
            self.assertEqual(recovery.synthetic_path(runner.PHASE15_ARCHIVE, False), runner.PHASE15_ARCHIVE)
            with self.assertRaises(ValueError):
                recovery.synthetic_path(Path("/tmp/birja-phase16-proof/recovery.tar.gz"), False)

    def source_tree(self, directory):
        root = Path(directory) / 'checkout'
        root.mkdir()
        (root / 'backend').mkdir()
        (root / 'backend/input.py').write_bytes(b'original')
        subprocess.run(['git', 'init', '-q', str(root)], check=True)
        subprocess.run(['git', '-C', str(root), 'add', 'backend/input.py'], check=True)
        return root

    def test_source_linked_ancestors_refuse_even_identical_bytes(self):
        with tempfile.TemporaryDirectory(prefix='birja-backup-test-source-parents-') as directory:
            root = self.source_tree(directory)
            outside = Path(directory) / 'outside'
            outside.mkdir()
            (outside / 'input.py').write_bytes(b'original')
            original = root / 'saved'
            (root / 'backend').rename(original)
            for target in (outside, original):
                with self.subTest(target=target.name):
                    (root / 'backend').symlink_to(target, target_is_directory=True)
                    try:
                        with patch.object(runner, 'ROOT', root), \
                             patch.object(runner.subprocess, 'check_output', return_value=b'backend/input.py\0'), \
                             self.assertRaises(ValueError):
                            runner.security_sources()
                    finally:
                        (root / 'backend').unlink()

    def test_source_root_and_root_ancestor_links_refuse_before_git(self):
        with tempfile.TemporaryDirectory(prefix='birja-backup-test-source-root-') as directory:
            root = self.source_tree(directory)
            link = Path(directory) / 'linked'
            link.symlink_to(root, target_is_directory=True)
            parent_link = Path(directory) / 'parent-link'
            parent_link.symlink_to(directory, target_is_directory=True)
            for target in (link, parent_link / 'checkout'):
                with self.subTest(target=target), patch.object(runner, 'ROOT', target), \
                     patch.object(runner.subprocess, 'check_output') as git:
                    with self.assertRaises(ValueError):
                        runner.security_sources()
                    git.assert_not_called()

    def test_source_ignore_metadata_parent_link_refuses_before_git(self):
        with tempfile.TemporaryDirectory(prefix='birja-backup-test-source-ignore-') as directory:
            root = self.source_tree(directory)
            info = root / '.git/info'
            info.rename(root / '.git/original-info')
            info.symlink_to('original-info', target_is_directory=True)
            with patch.object(runner, 'ROOT', root), \
                 patch.object(runner.subprocess, 'check_output') as git:
                with self.assertRaises(ValueError):
                    runner.security_sources()
                git.assert_not_called()

    def test_source_leaf_replaced_at_open_cannot_read_link_target(self):
        with tempfile.TemporaryDirectory(prefix='birja-backup-test-source-swap-') as directory:
            root = self.source_tree(directory)
            outside = Path(directory) / 'outside.py'
            outside.write_bytes(b'original')
            actual_open = os.open
            swapped = []
            def swap(path, flags, *args, **kwargs):
                if path == 'input.py' and flags & os.O_RDONLY == os.O_RDONLY and not swapped:
                    swapped.append(True)
                    (root / 'backend/input.py').unlink()
                    (root / 'backend/input.py').symlink_to(outside)
                return actual_open(path, flags, *args, **kwargs)
            with patch.object(runner, 'ROOT', root), patch.object(runner.os, 'open', side_effect=swap):
                with self.assertRaises(ValueError):
                    runner.security_sources()
            self.assertTrue(swapped, 'ordinary source must be opened through the no-follow descriptor path')

    def test_source_parent_replaced_after_open_reads_only_original_descriptor(self):
        with tempfile.TemporaryDirectory(prefix='birja-backup-test-source-parent-swap-') as directory:
            root = self.source_tree(directory)
            outside = Path(directory) / 'outside'
            outside.mkdir()
            (outside / 'input.py').write_bytes(b'controlled-outside')
            actual_open, actual_fdopen = os.open, os.fdopen
            swapped, read_values = [], []
            def swap(path, flags, *args, **kwargs):
                if path == 'input.py' and not swapped:
                    swapped.append(True)
                    (root / 'backend').rename(root / 'original-backend')
                    (root / 'backend').symlink_to(outside, target_is_directory=True)
                return actual_open(path, flags, *args, **kwargs)
            def observe(descriptor, *args, **kwargs):
                stream = actual_fdopen(descriptor, *args, **kwargs)
                original_read = stream.read
                def read(*arguments):
                    data = original_read(*arguments)
                    read_values.append(data)
                    return data
                stream.read = read
                return stream
            with patch.object(runner, 'ROOT', root), \
                 patch.object(runner.os, 'open', side_effect=swap), \
                 patch.object(runner.os, 'fdopen', side_effect=observe):
                with self.assertRaises(ValueError):
                    runner.security_sources()
            self.assertTrue(swapped)
            self.assertIn(b'original', read_values)
            self.assertNotIn(b'controlled-outside', read_values)


    def test_exact_successor_path_and_seven_stages(self):
        self.assertEqual(str(runner.ARCHIVE), "/tmp/birja-phase14-proof/recovery.tar.gz")
        self.assertEqual(runner.STAGES, ("image-transition", "retained-roundtrip", "current0023-cold",
                                       "roles", "tls-upgraded", "tls-fresh", "selected-rollback"))

    def test_every_stage_including_failed_stage_authenticates_afterward(self):
        for failed in (None, *runner.STAGES):
            events = []
            def operation(name):
                def execute():
                    events.append(name)
                    if name == failed:
                        raise RuntimeError("stage failure")
                    return ["a"*64,"b"*64,"c"*64] if (name.startswith("tls-") or name == "current0023-cold") else None
                return execute
            operations = {name: operation(name) for name in runner.STAGES}
            if failed:
                with self.assertRaisesRegex(RuntimeError, "stage failure"):
                    runner.execute_stages(operations, lambda: events.append("authenticate"))
            else:
                runner.execute_stages(operations, lambda: events.append("authenticate"))
            count = runner.STAGES.index(failed) + 1 if failed else 7
            self.assertEqual(events, ["authenticate"] +
                             [event for name in runner.STAGES[:count] for event in (name, "authenticate")])

    def test_recovery_dispatch_keeps_retained_and_actual_current_modes(self):
        calls = []
        from types import SimpleNamespace
        ops = SimpleNamespace(image_transition=lambda: None,
                              roundtrip=lambda path: calls.append(("legacy", path)),
                              roles=lambda: calls.append(("roles",)),
                              tls=lambda **kw: calls.append(("legacy-tls", kw)))
        smoke = SimpleNamespace(run=lambda **kw: calls.append(("smoke", kw)) or "authority")
        with patch.object(runner, "load", return_value=smoke):
            graph = runner.recovery_operations(ops, runner.ARCHIVE, "a" * 64)
            graph["retained-roundtrip"]()
            graph["current0023-cold"]()
            graph["tls-upgraded"]()
            graph["tls-fresh"]()
        modes = [call[1] for call in calls if call[0] == "smoke"]
        self.assertEqual(modes[0]["revision"], "0017")
        self.assertTrue(modes[0]["cold"])
        self.assertEqual(modes[1]["revision"], "0020")
        self.assertEqual(modes[2]["revision"], "0023")
        self.assertTrue(modes[2]["cold"])
        self.assertTrue(modes[1]["cold"])
        self.assertTrue(modes[3]["upgraded_bootstrap"])
        self.assertEqual(modes[3]["upgraded_from"], "0014")
        self.assertTrue(modes[4]["upgraded_bootstrap"])
        self.assertTrue(modes[5]["fresh_bootstrap"])
        for mode in modes:
            self.assertEqual(mode["archive"], runner.ARCHIVE)
            self.assertEqual(mode["archive_sha"], "a" * 64)
        self.assertEqual([mode["revision"] for mode in modes],
                         ["0017", "0020", "0023", "0023", "0023", "0023"])

    def test_all_three_current_authority_results_must_match(self):
        for changed in ("current0023-cold", "tls-upgraded", "tls-fresh"):
            operations = {name: (lambda name=name: ["f"*64]*3 if name == changed else ["a"*64,"b"*64,"c"*64])
                          for name in runner.STAGES}
            with self.assertRaisesRegex(ValueError, "authority differs"):
                runner.execute_stages(operations, lambda: None)

    def test_missing_or_malformed_authority_cannot_pass_by_equal_empty_results(self):
        for value in (None, [], 'a'*64, ['a'*64]*2, ['x'*64]*3, [True,False,True]):
            with self.assertRaisesRegex(ValueError, 'authority differs'):
                runner.execute_stages({name:(lambda value=value:value) for name in runner.STAGES}, lambda:None)

    def test_concurrent_status_reads_never_observe_a_partial_json_document(self):
        with tempfile.TemporaryDirectory(prefix='birja-backup-test-status-') as directory:
            path=Path(directory)/'status.json'
            runner.write_status(path,{'counter':0})
            failures=[]
            def writer():
                try:
                    for counter in range(40):
                        runner.write_status(path,{'counter':counter,'padding':'x'*4096})
                except Exception as exc:
                    failures.append(exc)
            thread=threading.Thread(target=writer)
            thread.start()
            try:
                while thread.is_alive():
                    self.assertIsInstance(json.loads(path.read_text())['counter'],int)
            finally:
                thread.join()
            self.assertFalse(failures)
            self.assertEqual(path.stat().st_mode & 0o077,0)
            target=Path(directory)/'untouched'
            target.write_text('original')
            path.unlink()
            path.symlink_to(target)
            with self.assertRaisesRegex(ValueError,'symlink'):
                runner.write_status(path,{'counter':999})
            self.assertEqual(target.read_text(),'original')

    def test_preserved_archive_refuses_mutation_and_symlink(self):
        import hashlib
        import tempfile
        with tempfile.TemporaryDirectory(prefix="birja-backup-test-preserved-") as directory:
            archive = Path(directory) / "prior.tar"
            with patch.object(runner, "PRESERVED_ARCHIVE", archive), \
                 patch.object(runner, "PRESERVED_SHA256", hashlib.sha256(b"qualified").hexdigest()):
                self.assertIsNone(runner.preserved_archive())
                archive.write_bytes(b"qualified")
                self.assertIsNotNone(runner.preserved_archive())
                archive.write_bytes(b"substituted")
                with self.assertRaisesRegex(ValueError, "changed"):
                    runner.preserved_archive()
                archive.unlink()
                archive.symlink_to(Path(directory) / "missing")
                with self.assertRaisesRegex(ValueError, "symlink"):
                    runner.preserved_archive()

    def test_raw_audits_full_tests_builds_and_five_images_remain_required(self):
        commands = runner.security_commands()
        flat = [argv for _, argv in commands]
        for argv in (["uv", "run", "pytest", "--cov=app", "--cov-branch", "--cov-fail-under=80"],
                     ["uv", "run", "pip-audit"], ["npm", "run", "test", "--", "--coverage"],
                     ["node", "../deploy/audit-frontend.mjs"],
                     ["python3", "deploy/tests/test-portfolio-validation-contracts.py"],
                     ["python3", "deploy/tests/run-stock-browser.py"]):
            self.assertIn(argv, flat)
        scan = next(argv for argv in flat if argv[:2] == ["python3", "deploy/scan-images.py"])
        self.assertEqual(scan[4::2], ["--runtime", "--builder", "--postgres", "--redis", "--node"])

    def test_successor_path_is_exact_not_prefix_or_legacy_replacement(self):
        recovery = runner.load("portfolio-smoke").load_recovery()
        import tempfile
        with tempfile.TemporaryDirectory(prefix="birja-backup-test-path-") as temporary:
            with patch.object(recovery, "private", return_value=Path(temporary)):
                self.assertEqual(recovery.synthetic_path(runner.ARCHIVE, False), runner.ARCHIVE)
                legacy = Path("/tmp/birja-phase12-proof/recovery.tar.gz")
                self.assertEqual(recovery.synthetic_path(legacy, False), legacy)
                for path in ("/tmp/birja-phase13-proof/other.tar", "/tmp/birja-phase13-proof-extra/recovery.tar.gz"):
                    with self.assertRaises(ValueError):
                        recovery.synthetic_path(path, False)

    def test_security_source_drift_stops_and_cleans_owned_stack(self):
        from types import SimpleNamespace
        calls = []
        def command(argv, **kwargs):
            calls.append(argv)
            return SimpleNamespace(stdout=b'')
        with patch.object(runner, 'security_sources', side_effect=[{'fixed': 'a'}, {'changed': 'b'}]), \
             patch.object(runner, 'security_commands', return_value=[('.', ['bounded-probe'])]):
            with self.assertRaisesRegex(ValueError, 'source changed'):
                runner.execute_security(run=command)
        self.assertNotIn(['bounded-probe'], calls)
        self.assertEqual(calls[-1], runner.STACK + ['down', '-v'])

    def test_actual_file_hash_detects_in_command_source_edit_and_stops(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory(prefix='birja-backup-test-source-') as directory:
            root = Path(directory)
            (root / 'input').write_text('original')
            calls = []
            def command(argv, **kwargs):
                calls.append(argv)
                if argv == ['bounded-probe']:
                    (root / 'input').write_text('changed')
                return SimpleNamespace(stdout=b'')
            with patch.object(runner, 'ROOT', root), \
                 patch.object(runner.subprocess, 'check_output', return_value=b'input\0'), \
                 patch.object(runner, 'security_commands', return_value=[('.', ['bounded-probe']), ('.', ['never'])]):
                with self.assertRaisesRegex(ValueError, 'source changed'):
                    runner.execute_security(run=command)
            self.assertNotIn(['never'], calls)
            self.assertEqual(calls[-1], runner.STACK + ['down', '-v'])

    def test_dev_diagnostic_uses_current_schema_without_app_account_insert(self):
        module = runner.load('test-dev-bootstrap')
        code = module.financial_program()
        compile(code, '<dev0025>', 'exec')
        self.assertIn("version_num FROM alembic_version\")=='0025'", code)
        self.assertIn("PREFLIGHT_0025_SQL", code)
        self.assertIn("version_num='0018'", code)
        self.assertIn("version_num='0025'", code)
        self.assertIn("D('124.45')", code)
        self.assertIn('7777', code)
        self.assertLess(code.index('INSERT INTO accounts'), code.index('SET ROLE birja_app'))
        source = (ROOT / 'deploy/tests/test-dev-bootstrap.py').read_text()
        self.assertIn('services[name]["volumes"] = "RESET"', source)

    def test_preflight_uses_stripped_tools_and_exact_owned_fixture_tail(self):
        from types import SimpleNamespace
        calls = []
        def command(argv, **kwargs):
            calls.append((argv, kwargs))
            value = b'v24.0.0' if argv[-1] == '--version' and 'node' in argv[0] else b'checked'
            if argv[-1] == 'version':
                value = b'restic 0.19.1 compiled with approved Go'
            return SimpleNamespace(stdout=value, stderr=b'')
        # Command doubles test dispatch/environment, not host tool installation.
        # Real tool/checksum admission remains exercised by actual preflight.
        required = {ROOT / 'backend/.venv/bin' / name for name in ('pytest', 'ruff', 'mypy', 'pip-audit')}
        required |= {ROOT / 'frontend/node_modules/.bin' / name
                     for name in ('prettier', 'eslint', 'tsc', 'vitest', 'vite', 'playwright')}
        original_file, original_access = Path.is_file, os.access
        def installed_file(path):
            return True if path in required else original_file(path)
        def installed_access(path, mode):
            return True if Path(path) in required and mode == os.X_OK else original_access(path, mode)
        with tempfile.TemporaryDirectory(prefix='birja-backup-test-preflight-unit-') as directory:
            tools = Path(directory)
            for name in ('uv', 'node', 'python3', 'restic', 'nginx', 'docker'):
                (tools / name).write_bytes(b'unit-test-tool')
            with patch.object(runner.shutil, 'which', side_effect=lambda name, **kw: str(tools / name)), \
                 patch.object(runner, 'RESTIC_SHA256', hashlib.sha256(b'unit-test-tool').hexdigest()), \
                 patch.object(Path, 'is_file', installed_file), patch.object(os, 'access', installed_access), \
                 patch.object(runner, 'PHASE15_ARCHIVE', tools / 'absent-proof/recovery.tar.gz'), \
                 patch.dict(os.environ, {'ALPACA_API_KEY':'private', 'DATABASE_URL':'production'}):
                result = runner.preflight('all-security', run=command)
                self.assertTrue(result['ok'])
                self.assertIn('/usr/sbin', result['path'].split(os.pathsep))
                self.assertEqual(calls[-1][0], ['bash', 'deploy/tests/test-db-config.sh'])
                self.assertEqual(calls[-1][1]['env']['BIRJA_TEST_PROJECT'], 'birja-p14-16-preflight')
                self.assertNotIn('ALPACA_API_KEY', calls[-1][1]['env'])
                self.assertIn('@127.0.0.1:55432/birja_test', calls[-1][1]['env']['DATABASE_URL'])
                selected = runner.preflight('recovery-current', phase=15, run=command)
                self.assertEqual(selected['phase'], 15)
                self.assertEqual(selected['archive'], str(runner.PHASE15_ARCHIVE))
                self.assertEqual(calls[-1][0], ['bash', 'deploy/tests/test-db-config.sh'])
                self.assertEqual(calls[-1][1]['env']['BIRJA_TEST_PROJECT'], 'birja-p15-01-preflight')

    def test_untracked_addition_rename_and_link_changes_are_real_source_drift(self):
        with tempfile.TemporaryDirectory(prefix='birja-backup-test-source-git-') as directory:
            root=Path(directory)
            env={**runner.environment(),'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
            subprocess.run(['git','init','-q',str(root)],env=env,check=True)
            (root/'backend').mkdir()
            (root/'.gitignore').write_text('*.env\n')
            (root/'backend/tracked.py').write_text('original')
            subprocess.run(['git','-C',str(root),'add','.gitignore','backend/tracked.py'],env=env,check=True)
            (root/'backend/private.env').write_text('must-never-be-read')
            with patch.object(runner,'ROOT',root):
                first=runner.security_sources()
                self.assertNotIn('backend/private.env',first)
                (root/'backend/new.py').write_text('new-untracked')
                second=runner.security_sources()
                self.assertNotEqual(second,first)
                self.assertIn('backend/new.py',second)
                link=root/'backend/link.py'
                link.symlink_to('tracked.py')
                linked=runner.security_sources()
                link.unlink()
                link.symlink_to('new.py')
                self.assertNotEqual(runner.security_sources(),linked)
                link.unlink()
                outside=root.parent/(root.name+'-outside')
                outside.write_text('never-read-outside-source')
                try:
                    link.symlink_to(outside)
                    with self.assertRaisesRegex(ValueError,'escapes'):
                        runner.security_sources()
                finally:
                    link.unlink()
                    outside.unlink()
                (root/'backend/tracked.py').rename(root/'backend/renamed.py')
                with self.assertRaisesRegex(ValueError,'disappeared'):
                    runner.security_sources()


campaign_spec = importlib.util.spec_from_file_location(
    'durable_campaign', ROOT / 'deploy/tests/run-portfolio-campaign.py')
campaign = importlib.util.module_from_spec(campaign_spec)
campaign_spec.loader.exec_module(campaign)


class DurableCampaign(unittest.TestCase):
    def test_phase15_worker_forwards_original_selection_and_status_is_read_only(self):
        root, fixture, request = self.fixture()
        archive = root / "phase15/recovery.tar.gz"
        fixture.archive_for_phase = lambda phase: archive if phase == 15 else fixture.ARCHIVE
        fixture.preserved_phase14_archive = lambda: None
        fixture.preflight = lambda suite, *, phase=14: {"ok": True, "suite": suite, "phase": phase}
        request.update(suite="recovery-current", qualification_phase=15,
                       archive=str(archive), preserved_phase14_archive_sha256=None)
        campaign.write_json(root / "request.json", request)
        (root / "request.json").chmod(0o400)
        original_request = (root / "request.json").read_bytes()
        original_popen = campaign.subprocess.Popen
        commands = []
        def launch(argv, **kwargs):
            commands.append(argv)
            self.assertEqual(argv[-4:], ["--suite", "recovery-current", "--phase", "15"])
            return original_popen([sys.executable, "-c", "print('component boundary')"], **kwargs)
        with patch.object(campaign.subprocess, "Popen", side_effect=launch):
            self.assertEqual(campaign.worker(root, runner=fixture), 0)
        state = campaign.read_json(root / "status.json")
        self.assertEqual(state["qualification_phase"], 15)
        self.assertEqual(state["archive"], str(archive))
        self.assertEqual(campaign.read_json(root / "preflight.json")["phase"], 15)
        self.assertEqual(len(commands), 1)
        before = {name: (root / name).read_bytes() for name in ("request.json", "claim.json", "status.json", "command.log")}
        with patch.object(campaign.subprocess, "Popen", side_effect=AssertionError("restart")):
            self.assertEqual(campaign.inspect_status(root)["qualification_phase"], 15)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(campaign.main(["--resume", "--receipt-dir", str(root)]), 0)
        self.assertEqual(before, {name: (root / name).read_bytes() for name in before})
        self.assertEqual(original_request, (root / "request.json").read_bytes())
        changed = {**state, "qualification_phase": 14}
        campaign.write_json(root / "status.json", changed)
        with self.assertRaisesRegex(ValueError, "phase mismatch"):
            campaign.inspect_status(root)

    def test_finite_receipt_namespaces_match_the_original_phase_and_suite(self):
        for phase in (14, 15):
            request = {"suite": "recovery", "qualification_phase": phase}
            self.assertEqual(campaign.qualification_phase(request, f"/tmp/birja-phase{phase}-campaign-test"), phase)
            with self.assertRaisesRegex(ValueError, "namespace"):
                campaign.qualification_phase(request, f"/tmp/birja-phase{29-phase}-campaign-test")
        self.assertEqual(campaign.qualification_phase({"suite": "recovery"}), 14)
        for request in ({"suite": "recovery-current"}, {"suite": "recovery", "qualification_phase": 16},
                        {"suite": "recovery", "qualification_phase": True}):
            with self.assertRaises(ValueError):
                campaign.qualification_phase(request)

    def test_phase15_archive_snapshot_refuses_other_qualification_before_inspection(self):
        root, fixture, request = self.fixture()
        fixture.archive_for_phase = lambda phase: root / "phase15/recovery.tar.gz"
        archive = fixture.archive_for_phase(15)
        archive.parent.mkdir()
        campaign.write_json(archive.parent / "status.json", {"phase": 14, "suite": "recovery", "archive_sha256": "a" * 64})
        with patch.object(campaign.subprocess, "check_output", side_effect=AssertionError("image inspection")):
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                campaign.artifact_snapshot(fixture, None, phase=15, suite="recovery-current")

    def test_legacy_request_bytes_and_phase14_interpretation_are_preserved(self):
        root, fixture, request = self.fixture()
        before = (root / "request.json").read_bytes()
        self.assertNotIn("qualification_phase", request)
        self.assertEqual(campaign.worker(root, runner=fixture, command=[sys.executable, "-c", "pass"]), 0)
        self.assertEqual(campaign.inspect_status(root)["qualification_phase"], 14)
        self.assertEqual(before, (root / "request.json").read_bytes())

    def wait_for(self, predicate, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(.02)
        self.fail('bounded child did not reach expected phase')

    def test_preflight_interrupt_reaps_nested_children_before_terminal_receipt(self):
        root, fixture, request = self.fixture()
        pidfile, marker = root/'nested.pid', root/'nested.finally'
        wrapper_marker = root/'wrapper.finally'
        def preflight(suite):
            code = "import os,time\nfrom pathlib import Path\nPath("+repr(str(pidfile))+").write_text(str(os.getpid()))\ntry: time.sleep(20)\nfinally: Path("+repr(str(marker))+").write_text('clean')"
            wrapper = 'import subprocess,sys\nfrom pathlib import Path\np=subprocess.Popen([sys.executable,"-u","-c",'+repr(code)+'])\ntry: p.wait()\nfinally:\n p.wait()\n Path('+repr(str(wrapper_marker))+').write_text("clean")'
            subprocess.run([sys.executable,'-u','-c',wrapper], check=True, timeout=25)
            return {'ok':True}
        fixture.preflight = preflight
        def interrupt():
            self.wait_for(pidfile.exists)
            os.kill(os.getpid(), signal.SIGTERM)
        timer = threading.Timer(.05, interrupt)
        timer.start()
        try:
            result = campaign.worker(root, runner=fixture,
                command=[sys.executable,'-c',"raise AssertionError('long command forbidden')"])
            leaked = campaign.process_identity(int(pidfile.read_text())) is not None
            finalized = marker.exists() and wrapper_marker.exists()
        finally:
            timer.cancel(); timer.join()
            if pidfile.exists() and campaign.process_identity(int(pidfile.read_text())) is not None:
                os.kill(int(pidfile.read_text()), signal.SIGINT)
                self.wait_for(lambda: campaign.process_identity(int(pidfile.read_text())) is None)
        self.assertEqual(result, 1)
        self.assertFalse(leaked, 'terminal receipt published while nested child remains alive')
        self.assertTrue(finalized, 'nested child finalizer missing at terminal receipt')
        state = campaign.read_json(root/'status.json')
        self.assertEqual(state['state'], 'interrupted')
        self.assertEqual(state['phase'], 'preflight')
        self.assertGreater(state['preflight_start_ticks'], 0)
        self.assertIsNone(campaign.process_identity(state['preflight_pid']))
        self.assertIsNone(campaign.process_identity(int(pidfile.read_text())))
        self.assertEqual(marker.read_text(), 'clean')
        self.assertFalse((root/'command.log').exists())
        self.assertEqual(state['cleanup'], 'preflight-group-reaped;long-command-not-started')

    def test_completed_worker_replay_preserves_original_claim_status_and_log(self):
        root, fixture, request = self.fixture()
        count = root/'preflight-count'
        def preflight(suite):
            with count.open('a') as stream: stream.write('once\n')
            return {'ok':True}
        fixture.preflight = preflight
        self.assertEqual(campaign.worker(root,runner=fixture,command=[sys.executable,'-c',"print('original')"]),0)
        before = {p.name:p.read_bytes() for p in root.iterdir() if p.name in {'status.json','claim.json','command.log','preflight.log'}}
        self.assertEqual(campaign.worker(root,runner=fixture,command=[sys.executable,'-c',"print('replacement')"]),1)
        self.assertEqual(count.read_text(),'once\n')
        self.assertIn('claim.json',before)
        self.assertEqual(before,{name:(root/name).read_bytes() for name in before})

    def test_forced_preflight_kill_does_not_attest_resource_finalizers(self):
        root, fixture, request = self.fixture()
        entered, finalized = root/'entered', root/'never-finalized'
        def preflight(suite):
            entered.touch()
            try:
                while True: time.sleep(.02)
            finally:
                finalized.touch()
        fixture.preflight = preflight
        original_stop = campaign.stop_child
        def bounded(child, ticks):
            return original_stop(child,ticks,grace_seconds=.1)
        def interrupt():
            self.wait_for(entered.exists)
            os.kill(os.getpid(),signal.SIGTERM)
        timer = threading.Timer(.05,interrupt)
        timer.start()
        try:
            with patch.object(campaign,'stop_child',side_effect=bounded):
                result = campaign.worker(root,runner=fixture,command=['false'])
        finally:
            timer.cancel(); timer.join()
        state = campaign.read_json(root/'status.json')
        self.assertEqual(result,1)
        self.assertEqual(state['exit_code'],-signal.SIGKILL)
        self.assertFalse(finalized.exists())
        self.assertIsNone(campaign.process_identity(state['preflight_pid']))
        self.assertEqual(state['cleanup'],'preflight-group-killed;finalizers-unconfirmed;long-command-not-started')
        self.assertEqual(state['resource_cleanup'],'not-attested;see-preflight-log')
        self.assertFalse((root/'command.log').exists())

    def test_claim_binds_request_bytes_and_original_process_identity(self):
        root, fixture, request = self.fixture()
        self.assertEqual(campaign.worker(root,runner=fixture,command=[sys.executable,'-c','pass']),0)
        original = campaign.read_json(root/'status.json')
        campaign.write_json(root/'status.json',{**original,'start_ticks':original['start_ticks']+1})
        with self.assertRaisesRegex(ValueError,'claimed launch'):
            campaign.inspect_status(root)
        campaign.write_json(root/'status.json',original)
        campaign.write_json(root/'request.json',{**request,'extra':'changed'})
        with self.assertRaisesRegex(ValueError,'claimed launch'):
            campaign.inspect_status(root)
        before = (root/'status.json').read_bytes()
        self.assertEqual(campaign.worker(root,runner=fixture,command=['false']),1)
        self.assertEqual((root/'status.json').read_bytes(),before)

    def test_concurrent_and_stale_worker_claims_never_replace_original(self):
        root, fixture, request = self.fixture()
        release, entered = root/'release', root/'entered'
        def preflight(suite):
            with entered.open('a') as stream: stream.write('once\n')
            while not release.exists(): time.sleep(.02)
            return {'ok':True}
        fixture.preflight = preflight
        children = []
        try:
            for _ in range(2):
                pid = os.fork()
                if pid == 0:
                    os._exit(campaign.worker(root,runner=fixture,command=[sys.executable,'-c',"print('original')"]))
                children.append(pid)
            self.wait_for(entered.exists)
            before = (root/'status.json').read_bytes()
            # The losing concurrent worker must already refuse without preflight.
            outcomes = []
            for pid in children:
                observed, status = os.waitpid(pid, os.WNOHANG)
                if observed: outcomes.append((pid,os.waitstatus_to_exitcode(status)))
            replay = os.fork()
            if replay == 0:
                os._exit(campaign.worker(root,runner=fixture,command=[sys.executable,'-c','raise SystemExit(99)']))
            self.assertEqual(os.waitstatus_to_exitcode(os.waitpid(replay,0)[1]),1)
            self.assertEqual((root/'status.json').read_bytes(),before)
            self.assertEqual(entered.read_text(),'once\n')
            release.touch()
            outcomes += [(pid,os.waitstatus_to_exitcode(os.waitpid(pid,0)[1])) for pid in children if pid not in {p for p,_ in outcomes}]
            children.clear()
            self.assertEqual(sorted(code for _,code in outcomes),[0,1])
            claim = campaign.read_json(root/'claim.json')
            state = campaign.read_json(root/'status.json')
            self.assertEqual((claim['pid'],claim['start_ticks']),(state['pid'],state['start_ticks']))
            self.assertEqual(claim['run_id'],request['run_id'])
            original = (root/'status.json').read_bytes()
            # A consumed claim remains consumed after the original process exits.
            self.assertEqual(campaign.worker(root,runner=fixture,command=['false']),1)
            self.assertEqual((root/'status.json').read_bytes(),original)
        finally:
            release.touch()
            for pid in children:
                try: os.kill(pid,signal.SIGTERM)
                except ProcessLookupError: pass
                os.waitpid(pid,0)

    def fixture(self):
        directory = tempfile.TemporaryDirectory(prefix='birja-backup-test-durable-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / 'input').write_text('original')
        (root / 'deploy/tests').mkdir(parents=True)
        (root / 'deploy/tests/run-portfolio-campaign.py').write_text('bounded-test-source')
        class FixtureRunner:
            ARCHIVE = root / 'recovery.tar'
            @staticmethod
            def security_sources():
                return {'input': hashlib.sha256((root / 'input').read_bytes()).hexdigest()}
            @staticmethod
            def preserved_archive():
                return None
            @staticmethod
            def environment():
                return {'PATH':'/usr/sbin:/usr/bin:/bin'}
            @staticmethod
            def preflight(suite):
                return {'ok':True, 'suite':suite}
            load = staticmethod(runner.load)
        fixture = FixtureRunner()
        self.enterContext(patch.object(campaign, 'ROOT', root))
        self.enterContext(patch.object(campaign, 'validation', return_value=fixture))
        request = {'format':1, 'run_id':'bounded-original', 'suite':'all-security',
                   'source_sha256':campaign.source_snapshot(fixture),
                   'preserved_archive_sha256':None}
        campaign.write_json(root / 'request.json', request)
        (root / 'request.json').chmod(0o400)
        return root, fixture, request

    def test_actual_child_has_durable_log_exit_and_status_does_not_restart(self):
        root, fixture, request = self.fixture()
        self.assertEqual(campaign.worker(root, runner=fixture,
            command=[sys.executable,'-c',"print('bounded-command-complete')"]), 0)
        state = campaign.read_json(root / 'status.json')
        self.assertEqual(state['state'], 'passed')
        self.assertEqual(state['exit_code'], 0)
        self.assertGreater(state['child_start_ticks'], 0)
        self.assertIn('bounded-command-complete', (root / 'command.log').read_text())
        with patch.object(campaign.subprocess, 'Popen', side_effect=AssertionError('replacement')):
            self.assertEqual(campaign.inspect_status(root)['run_id'], request['run_id'])
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(campaign.main(['--resume','--receipt-dir',str(root)]), 0)
            self.assertEqual(json.loads(output.getvalue())['run_id'], request['run_id'])

    def test_private_path_mode_and_symlink_are_not_accepted(self):
        root, fixture, request = self.fixture()
        root.chmod(0o755)
        with self.assertRaisesRegex(ValueError, 'mode'):
            campaign.private_directory(root)
        root.chmod(0o700)
        link = root.with_name(root.name + '-link')
        link.symlink_to(root, target_is_directory=True)
        try:
            with self.assertRaises(ValueError):
                campaign.private_directory(link)
        finally:
            link.unlink()
        request_path = root / 'request.json'
        request_path.chmod(0o644)
        with self.assertRaisesRegex(ValueError, 'mode'):
            campaign.inspect_status(root)

    def test_failed_original_exit_is_retained_and_resume_cannot_replace_it(self):
        root, fixture, request = self.fixture()
        self.assertEqual(campaign.worker(root, runner=fixture,
            command=[sys.executable,'-c','raise SystemExit(7)']), 1)
        state = campaign.inspect_status(root)
        self.assertEqual(state['state'], 'failed')
        self.assertEqual(state['exit_code'], 7)
        with patch.object(campaign.subprocess, 'Popen', side_effect=AssertionError('replacement')):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(campaign.main(['--resume','--receipt-dir',str(root)]), 1)

    def test_source_change_during_child_stops_reaps_and_retains_refusal(self):
        root, fixture, request = self.fixture()
        timer = threading.Timer(0.4, lambda: (root / 'input').write_text('changed'))
        timer.start()
        try:
            self.assertEqual(campaign.worker(root, runner=fixture,
                command=[sys.executable,'-u','-c',
                         "import time\ntry: time.sleep(20)\nfinally: print('drift-child-finally')"]), 1)
        finally:
            timer.cancel()
            timer.join()
        state = campaign.read_json(root / 'status.json')
        self.assertEqual(state['state'], 'refused')
        self.assertIsNone(campaign.process_identity(state['child_pid']))
        self.assertIn('drift-child-finally', (root / 'command.log').read_text())

    def test_reused_pid_and_existing_receipt_cannot_be_resumed_by_launching(self):
        root, fixture, request = self.fixture()
        state = {'format':1, 'suite':'all-security', 'run_id':request['run_id'], 'state':'running', 'pid':os.getpid(),
                 'start_ticks':campaign.process_identity(os.getpid()) + 1, 'artifacts':None}
        campaign.write_json(root / 'status.json', state)
        with self.assertRaisesRegex(ValueError, 'PID reused'):
            campaign.inspect_status(root)
        with self.assertRaises(FileExistsError):
            campaign.start('all-security', root)

    def test_terminal_receipt_cannot_claim_pass_with_a_failed_exit(self):
        root, fixture, request = self.fixture()
        campaign.write_json(root/'status.json',{'format':1,'suite':'all-security',
            'run_id':request['run_id'],'state':'passed','exit_code':7})
        with self.assertRaisesRegex(ValueError,'outcome mismatch'):
            campaign.inspect_status(root)

    def test_source_change_during_preflight_refuses_before_child(self):
        root, fixture, request = self.fixture()
        def changed(suite):
            (root / 'input').write_text('changed')
            return {'ok':True}
        with patch.object(fixture, 'preflight', side_effect=changed), \
             patch.object(campaign.subprocess, 'Popen', side_effect=AssertionError('child')):
            self.assertEqual(campaign.worker(root, runner=fixture), 1)
        state = campaign.read_json(root / 'status.json')
        self.assertEqual(state['state'], 'refused')
        self.assertEqual(state['cleanup'], 'long-command-not-started')

    def test_interrupt_reaps_original_child_and_preserves_interrupted_receipt(self):
        root, fixture, request = self.fixture()
        timer = threading.Timer(0.4, lambda: os.kill(os.getpid(), signal.SIGTERM))
        timer.start()
        started = time.monotonic()
        try:
            result = campaign.worker(root, runner=fixture, command=[sys.executable, '-u', '-c',
                "import time\ntry: time.sleep(20)\nfinally: print('original-child-finally')"])
        finally:
            timer.cancel()
            timer.join()
        self.assertEqual(result, 1)
        self.assertLess(time.monotonic()-started, 5)
        state = campaign.read_json(root / 'status.json')
        self.assertEqual(state['state'], 'interrupted')
        self.assertIsNone(campaign.process_identity(state['child_pid']))
        self.assertNotEqual(state['exit_code'], 0)
        self.assertIn('original-child-finally', (root / 'command.log').read_text())

    def test_archive_image_records_missing_or_mutated_are_never_rebuilt(self):
        root, fixture, request = self.fixture()
        archive = fixture.ARCHIVE
        archive.write_bytes(b'qualified-archive')
        archive.chmod(0o600)
        campaign.write_json(root / 'status.json', {'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()})
        sources = fixture.load('portfolio-sources')
        image = [{'Id':'sha256:'+'a'*64, 'Config':{'Labels':{'org.opencontainers.image.revision':'b'*40}},
                  'RootFS':{'Type':'layers','Layers':['sha256:'+'c'*64]}}]
        binding = sources.image_binding(image, source_commit='b'*40, app_tree='d'*40, context_sha256='e'*64)
        record = root / 'current0023-image-binding.json'
        campaign.write_json(record, binding)
        with patch.object(campaign.subprocess, 'check_output', return_value=json.dumps(image).encode()):
            before = campaign.artifact_snapshot(fixture, None)
            record.unlink()
            with self.assertRaisesRegex(ValueError, 'disappeared'):
                campaign.artifact_snapshot(fixture, before)
            campaign.write_json(record, binding)
            archive.write_bytes(b'substituted')
            with self.assertRaisesRegex(ValueError, 'archive'):
                campaign.artifact_snapshot(fixture, before)
        archive.write_bytes(b'qualified-archive')
        changed = [{**image[0], 'Id':'sha256:'+'f'*64}]
        with patch.object(campaign.subprocess, 'check_output', return_value=json.dumps(changed).encode()):
            with self.assertRaisesRegex(ValueError, 'identity|mismatch'):
                campaign.artifact_snapshot(fixture, before)
        with patch.object(campaign.subprocess, 'check_output', side_effect=subprocess.CalledProcessError(1, ['docker'])):
            with self.assertRaises(subprocess.CalledProcessError):
                campaign.artifact_snapshot(fixture, before)


if __name__ == "__main__":
    unittest.main()
