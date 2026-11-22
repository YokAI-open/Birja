#!/usr/bin/env python3
"""Behavioral runner isolation/review contracts; no Docker or provider effects."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('portfolio_browser_runner', ROOT / 'deploy/tests/run-stock-browser.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class BrowserContracts(unittest.TestCase):
    def command(self, *, mutation=None, failure=False, occupied=False,
                suite='portfolios', timed_out=None, work=None):
        calls = []
        def run(argv, **kwargs):
            calls.append(list(argv))
            if argv[0].endswith('/playwright'):
                self.assertEqual(kwargs['timeout'], 1800 if suite == 'all' else 900)
                self.assertIn('--workers=1', argv)
                self.assertIn('--retries=0', argv)
                if timed_out is not None:
                    raise subprocess.TimeoutExpired(argv, kwargs['timeout'],
                                                    output=timed_out[0], stderr=timed_out[1])
            env = kwargs['env']
            self.assertNotIn('ALPACA_API_KEY', env)
            self.assertNotIn('RESEND_API_KEY', env)
            self.assertEqual(env['COMPOSE_DISABLE_ENV_FILE'], '1')
            self.assertEqual(env['COMPOSE_PROJECT_NAME'], runner.PROJECT)
            output = ''
            if '--filter' in argv and occupied and len(calls) == 1:
                output = 'owned-by-someone-else\n'
            if 'config' in argv and '--format' in argv:
                override = Path(env['COMPOSE_FILE'].split(':')[-1]).read_text()
                self.assertIn('volumes: !reset {}', override)
                services = {}
                name = None
                for line in override.splitlines():
                    if line.startswith('  ') and not line.startswith('    '):
                        name = line.strip().rstrip(':'); services[name] = {}
                    elif line.startswith('    '):
                        key, value = line.strip().split(': ', 1)
                        services[name][key] = [] if value == '!reset []' else json.loads(value)
                for service in services.values():
                    service.setdefault('environment', {}).update(ENV='dev', EMAIL_BACKEND='console', STOCK_DATA_ENABLED='false', PRICE_SOURCE='fake', STOCK_ACTIONS_ENABLED='false')
                services['frontend']['ports'] = [{'host_ip': '127.0.0.1'}]
                if mutation == 'mount': services['postgres']['volumes'] = ['/srv/birja:/data']
                if mutation == 'provider': services['backend']['environment']['STOCK_DATA_ENABLED'] = 'true'
                if mutation == 'port': services['postgres']['ports'] = [5432]
                if mutation == 'capacity': services['backend']['environment']['RL_SEND_GLOBAL_LIMIT'] = '201'
                if mutation == 'environment': services['backend']['environment']['ENV'] = 'prod'
                if mutation == 'project': services['backend']['environment']['COMPOSE_PROJECT_NAME'] = 'another-project'
                output = json.dumps({'name': runner.PROJECT, 'services': services})
            code = 1 if failure and argv[0].endswith('/playwright') else 0
            return subprocess.CompletedProcess(argv, code, output)
        original_mkdtemp = runner.tempfile.mkdtemp
        with patch.object(sys, 'argv', ['run-stock-browser.py', '--suite', suite]), \
             patch.object(runner.tempfile, 'mkdtemp', side_effect=(lambda **kw: str(work) if work else original_mkdtemp(**kw))), \
             patch.dict(os.environ, {'ALPACA_API_KEY': 'must-not-leak', 'RESEND_API_KEY': 'must-not-leak'}), \
             patch.object(runner.socket, 'socket') as socket, \
             patch.object(runner.subprocess, 'run', side_effect=run), \
             patch.object(runner, 'require_browser_specs'), \
             patch.object(runner.subprocess, 'check_output', return_value='a' * 40):
            socket.return_value.__enter__.return_value = SimpleNamespace(bind=lambda value: None, getsockname=lambda: ('127.0.0.1', 12345))
            if mutation or failure or occupied or timed_out is not None:
                with self.assertRaises((AssertionError, RuntimeError, subprocess.TimeoutExpired)):
                    runner.main()
            else:
                runner.main()
        return calls

    def test_actual_runner_scopes_data_migration_and_selects_new_journeys(self):
        calls = self.command()
        browser = next(c for c in calls if c[0].endswith('/playwright'))
        self.assertIn('e2e/portfolio-ownership.spec.ts', browser)
        self.assertIn('e2e/portfolio-strategies.spec.ts', browser)
        self.assertIn('e2e/portfolio-deletion.spec.ts', browser)
        legacy = next(c for c in calls if '/e2e/portfolio-browser-fixture.py' in c)
        self.assertEqual(legacy[-1], 'legacy')
        seed_roles = next(c[-1] for c in calls if 'CREATE ROLE birja_migrator' in c[-1])
        self.assertNotIn('CREATE ROLE birja_scheduler', seed_roles)
        # Immutable0011 requires the operator to exist for a restricted owner;
        # ordinary app/scheduler roles must still be provisioned after0014.
        self.assertIn('CREATE ROLE birja_action_operator', seed_roles)
        self.assertLess(calls.index(legacy), next(i for i, c in enumerate(calls) if '--wait-timeout' in c))
        self.assertTrue(any('down' in c and '--volumes' in c for c in calls))

    def test_default_command_explicitly_retains_every_financial_spec(self):
        expected = ('auth', 'csp', 'health', 'markets', 'trade', 'stocks',
                    'stock-trades', 'stock-actions', 'dividends-history',
                    'portfolio-history', 'portfolio-ownership', 'portfolio-strategies',
                    'portfolio-deletion')
        self.assertEqual(runner.browser_specs('all'),
                         ['e2e/' + name + '.spec.ts' for name in expected])
        with self.assertRaises(ValueError):
            runner.browser_specs('unknown')

    def test_missing_or_symlinked_journey_refuses_before_collection(self):
        with tempfile.TemporaryDirectory(prefix='birja-browser-spec-contract-') as tmp:
            root = Path(tmp)
            (root / 'e2e').mkdir()
            good = root / 'e2e/portfolio-ownership.spec.ts'
            good.write_text('actual test')
            with patch.object(runner, 'ROOT', root.parent):
                with self.assertRaisesRegex(ValueError, 'missing|unsafe'):
                    runner.require_browser_specs(['e2e/portfolio-strategies.spec.ts'], directory=root)
                runner.require_browser_specs(['e2e/portfolio-ownership.spec.ts'], directory=root)
                link = root / 'e2e/portfolio-strategies.spec.ts'
                link.symlink_to(good)
                with self.assertRaisesRegex(ValueError, 'missing|unsafe'):
                    runner.require_browser_specs(['e2e/portfolio-strategies.spec.ts'], directory=root)

    def test_runner_rejects_live_data_mount_provider_and_ports_before_build(self):
        for mutation in ('mount', 'provider', 'port', 'capacity', 'environment', 'project'):
            with self.subTest(mutation=mutation):
                calls = self.command(mutation=mutation)
                self.assertFalse(any('build' in c for c in calls))

    def test_browser_failure_propagates_and_cleans_only_owned_project(self):
        calls = self.command(failure=True)
        self.assertTrue(any('down' in c for c in calls))
        calls = self.command(occupied=True)
        self.assertFalse(any('down' in c for c in calls))

    def test_complete_suite_has_bounded_budget_and_retains_every_spec(self):
        calls = self.command(suite='all')
        browser = next(c for c in calls if c[0].endswith('/playwright'))
        self.assertEqual([c for c in browser if c.endswith('.spec.ts')], runner.browser_specs('all'))
        workflow = (ROOT / '.github/workflows/ci.yml').read_text()
        # Read the job through its next sibling, retaining setup/cleanup headroom.
        e2e = workflow.split('\n  e2e:\n', 1)[1].split('\n  ops:', 1)[0]
        self.assertIn('timeout-minutes: 40', e2e)

    def test_timeout_preserves_redacted_partial_output_and_still_fails_and_cleans(self):
        for values in ((b'to=synthetic@example.com code=123456\xff', b'partial stderr'),
                       ('to=synthetic@example.com code=123456', 'partial stderr')):
            with self.subTest(bytes=isinstance(values[0], bytes)), tempfile.TemporaryDirectory() as tmp:
                work = Path(tmp)
                calls = self.command(timed_out=values, work=work)
                output = (work / 'browser-portfolios.log').read_text()
                self.assertIn('to=*** code=******', output)
                self.assertIn('partial stderr', output)
                self.assertNotIn('synthetic@example.com', output)
                self.assertNotIn('123456', output)
                self.assertTrue(any('down' in c and '--volumes' in c for c in calls))

    def test_review_is_inert_source_bound_exclusive_and_never_claims_native_zoom(self):
        with tempfile.TemporaryDirectory(prefix='birja-phase12-review-contract-') as work:
            directory = Path(work) / 'review'; directory.mkdir()
            (directory / 'actual.html').write_text('<!doctype html><p>actual synthetic DOM</p>')
            with patch.object(runner, 'source_snapshot', return_value={'fixed': 'a' * 64}):
                runner.finish_review(directory, {'fixed': 'a' * 64}, 'b' * 40)
                manifest = json.loads((directory / 'manifest.json').read_text())
                self.assertIs(manifest['native_200_percent_verified'], False)
                self.assertIn('actual.html', manifest['artifacts'])
                with self.assertRaises((FileExistsError, RuntimeError)):
                    runner.finish_review(directory, {'fixed': 'a' * 64}, 'b' * 40)
                with self.assertRaisesRegex(RuntimeError, 'Source drift'):
                    runner.finish_review(directory, {'changed': 'a' * 64}, 'b' * 40)
            directory.chmod(0o700)

    def test_source_journeys_use_actual_scoped_transport_and_owner_snapshot(self):
        source = (ROOT / 'frontend/e2e/portfolio-ownership.spec.ts').read_text()
        self.assertIn('/api/v2/portfolios/${id}', source)
        self.assertIn('route.fetch()', source)
        self.assertIn('readCodeFromLogs(email)', source)
        self.assertNotIn('localStorage', source)
        self.assertIn('[320, 768, 1280]', source)
        self.assertIn('default-src', source)
        self.assertIn('flag: "wx"', source)

    def test_source_snapshot_binds_current_dividend_browser_evidence(self):
        import hashlib
        path = ROOT / 'deploy/tests/dividend-execution-fixture.py'
        snapshot = runner.source_snapshot()
        self.assertEqual(snapshot[path.relative_to(ROOT).as_posix()],
                         hashlib.sha256(path.read_bytes()).hexdigest())

    def test_opening_fixture_takes_instrument_gate_before_root_and_journal(self):
        import ast
        source = (ROOT / 'deploy/tests/dividend-execution-fixture.py').read_text()
        tree = ast.parse(source)
        browser = next(node for node in tree.body
                       if isinstance(node, ast.AsyncFunctionDef) and node.name == 'browser_main')
        transaction = next(node for node in ast.walk(browser)
                           if isinstance(node, ast.AsyncWith)
                           and 'pg_advisory_xact_lock' in ast.get_source_segment(source, node))
        body = ast.get_source_segment(source, transaction)
        gate = body.index('pg_advisory_xact_lock')
        self.assertLess(gate, body.index('SELECT id FROM accounts'))
        self.assertLess(gate, body.index('SELECT quantity FROM holdings'))
        self.assertLess(gate, body.index('INSERT INTO stock_ownership_movements'))
        self.assertIn("birja.stock.instrument:", body)


if __name__ == '__main__':
    unittest.main()
