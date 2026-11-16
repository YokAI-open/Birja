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
    def command(self, *, mutation=None, failure=False, occupied=False):
        calls = []
        def run(argv, **kwargs):
            calls.append(list(argv))
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
                    service.setdefault('environment', {}).update(EMAIL_BACKEND='console', STOCK_DATA_ENABLED='false', PRICE_SOURCE='fake', STOCK_ACTIONS_ENABLED='false')
                services['frontend']['ports'] = [{'host_ip': '127.0.0.1'}]
                if mutation == 'mount': services['postgres']['volumes'] = ['/srv/birja:/data']
                if mutation == 'provider': services['backend']['environment']['STOCK_DATA_ENABLED'] = 'true'
                if mutation == 'port': services['postgres']['ports'] = [5432]
                output = json.dumps({'name': runner.PROJECT, 'services': services})
            code = 1 if failure and argv[0].endswith('/playwright') else 0
            return subprocess.CompletedProcess(argv, code, output)
        with patch.object(sys, 'argv', ['run-stock-browser.py', '--suite', 'portfolios']), \
             patch.dict(os.environ, {'ALPACA_API_KEY': 'must-not-leak', 'RESEND_API_KEY': 'must-not-leak'}), \
             patch.object(runner.socket, 'socket') as socket, \
             patch.object(runner.subprocess, 'run', side_effect=run), \
             patch.object(runner.subprocess, 'check_output', return_value='a' * 40):
            socket.return_value.__enter__.return_value = SimpleNamespace(bind=lambda value: None, getsockname=lambda: ('127.0.0.1', 12345))
            if mutation or failure or occupied:
                with self.assertRaises((AssertionError, RuntimeError)):
                    runner.main()
            else:
                runner.main()
        return calls

    def test_actual_runner_scopes_data_migration_and_selects_new_journeys(self):
        calls = self.command()
        browser = next(c for c in calls if c[0].endswith('/playwright'))
        self.assertIn('e2e/portfolio-ownership.spec.ts', browser)
        legacy = next(c for c in calls if '/e2e/portfolio-browser-fixture.py' in c)
        self.assertEqual(legacy[-1], 'legacy')
        self.assertLess(calls.index(legacy), next(i for i, c in enumerate(calls) if '--wait-timeout' in c))
        self.assertTrue(any('down' in c and '--volumes' in c for c in calls))

    def test_runner_rejects_live_data_mount_provider_and_ports_before_build(self):
        for mutation in ('mount', 'provider', 'port'):
            with self.subTest(mutation=mutation):
                calls = self.command(mutation=mutation)
                self.assertFalse(any('build' in c for c in calls))

    def test_browser_failure_propagates_and_cleans_only_owned_project(self):
        calls = self.command(failure=True)
        self.assertTrue(any('down' in c for c in calls))
        calls = self.command(occupied=True)
        self.assertFalse(any('down' in c for c in calls))

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


if __name__ == '__main__':
    unittest.main()
