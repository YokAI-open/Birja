#!/usr/bin/env python3
"""Successor campaign contracts. Command doubles are not qualification receipts."""

import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("validation", ROOT / "deploy/tests/run-portfolio-validation.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class CurrentCampaign(unittest.TestCase):
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
                    return "authority" if (name.startswith("tls-") or name == "current0023-cold") else None
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
        self.assertTrue(modes[4]["fresh_bootstrap"])
        for mode in modes:
            self.assertEqual(mode["archive"], runner.ARCHIVE)
            self.assertEqual(mode["archive_sha"], "a" * 64)
        self.assertEqual([mode["revision"] for mode in modes],
                         ["0017", "0020", "0023", "0023", "0023"])

    def test_all_three_current_authority_results_must_match(self):
        for changed in ("current0023-cold", "tls-upgraded", "tls-fresh"):
            operations = {name: (lambda name=name: "changed" if name == changed else "fixed")
                          for name in runner.STAGES}
            with self.assertRaisesRegex(ValueError, "authority differs"):
                runner.execute_stages(operations, lambda: None)

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

    def test_dev_diagnostic_uses_current_schema_without_app_account_insert(self):
        module = runner.load('test-dev-bootstrap')
        code = module.financial_program()
        compile(code, '<dev0020>', 'exec')
        self.assertIn("version_num FROM alembic_version\")=='0020'", code)
        self.assertIn("version_num='0018'", code)
        self.assertIn("version_num='0020'", code)
        self.assertIn("D('124.45')", code)
        self.assertIn('7777', code)
        self.assertLess(code.index('INSERT INTO accounts'), code.index('SET ROLE birja_app'))


if __name__ == "__main__":
    unittest.main()
