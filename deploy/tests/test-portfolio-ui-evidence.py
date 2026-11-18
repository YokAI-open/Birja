#!/usr/bin/env python3
"""Offline negative contracts; these are not browser execution receipts."""
import copy
import hashlib
import html
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

PATH = Path(__file__).with_name('portfolio-ui-evidence.py')
EXPECTED_WIDTHS = (320, 375, 768, 1024, 1280, 1440)
EXPECTED_STATES = ('overview', 'create-long-astral', 'keyboard-error-focus', 'unknown',
                   'edit', 'stale-draft', 'switch', 'incomplete', 'failed-refresh', 'cap', 'empty', 'error')


def expected_paths(width, state):
    stem = f'phase13-{state}-{width}'
    return {'html': stem + '.html', 'png': stem + '.png', 'trace': stem + '.trace.json',
            **({'reflow_png': stem + '.reflow.png'} if width >= 768 else {})}


def required_names():
    return {'index.html'} | {name for width in EXPECTED_WIDTHS for state in EXPECTED_STATES
                            for name in expected_paths(width, state).values()}


class EvidenceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('portfolio_ui_evidence', PATH)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def sample(self):
        return self.module.contract_example()

    def test_valid_complete_packet(self):
        self.module.validate_manifest(self.sample())

    def test_source_drift_refused(self):
        value = self.sample()
        with self.assertRaises(ValueError):
            self.module.validate_manifest(value, source={'frontend/src/App.tsx': 'b' * 64})

    def test_browser_version_and_width_refused(self):
        for field, replacement in [('browser_version', ''), ('browser', 'unknown'), ('width', 321)]:
            value = self.sample()
            value['captures'][0][field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.module.validate_manifest(value)

    def test_missing_duplicate_and_cross_owner_capture_refused(self):
        for operation in ('missing', 'duplicate', 'owner'):
            value = self.sample()
            if operation == 'missing':
                value['captures'].pop()
            elif operation == 'duplicate':
                value['captures'].append(copy.deepcopy(value['captures'][0]))
            else:
                value['captures'][1]['scope'] = 'b' * 64
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                self.module.validate_manifest(value)

    def test_cannot_inherit_native_zoom_or_owner_approval(self):
        for field in ('native_200_percent_verified', 'owner_accepted'):
            value = self.sample()
            value[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.module.validate_manifest(value)

    def test_malformed_hash_and_render_input_mismatch_refused(self):
        for operation in ('hash', 'render'):
            value = self.sample()
            value['captures'][0]['render_inputs_sha256'] = 'x' if operation == 'hash' else 'b' * 64
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                self.module.validate_manifest(value)

    def packet(self, directory):
        """Offline schema fixture, independently enumerated; never a browser receipt."""
        value = self.sample()
        for capture in value['captures']:
            width, state = capture['width'], capture['state']
            capture['artifacts'] = expected_paths(width, state)
            metadata = {'phase': 13, 'state': state, 'width': width, 'browser': 'chromium',
                        'version': '1.2.3', 'scope': capture['scope'], 'source': value['git_commit'],
                        'synthetic': True, 'native_200_percent_verified': False,
                        'artifacts': expected_paths(width, state), 'trace': [{'path': '/synthetic', 'start': 1, 'duration': 2}]}
            text = '<!doctype html><meta name="birja-evidence" content="' + html.escape(json.dumps(metadata), quote=True) + '">'
            for kind, name in expected_paths(width, state).items():
                (directory / name).write_text(text if kind == 'html' else json.dumps(metadata['trace']) if kind == 'trace' else 'offline-image-specimen')
        (directory / 'index.html').write_text('<!doctype html>Offline contract specimen')
        value['artifacts'] = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                              for name in required_names()}
        self.write_manifest(directory, value)
        return value

    def write_manifest(self, directory, value):
        (directory / 'manifest.json').write_text(json.dumps(value))

    def test_independent_required_matrix_and_complete_packet_control(self):
        self.assertEqual(len(required_names()), 265)
        self.assertEqual({(c['width'], c['state']) for c in self.sample()['captures']},
                         {(w, s) for w in EXPECTED_WIDTHS for s in EXPECTED_STATES})
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            value = self.packet(directory)
            self.module.validate_manifest(value)
            self.module.verify_artifacts(directory, value['artifacts'])

    def test_coherent_artifact_omission_cannot_qualify_metadata_only_evidence(self):
        for missing in ('phase13-unknown-1280.html', 'phase13-unknown-1280.png',
                        'phase13-unknown-1280.reflow.png', 'phase13-unknown-1280.trace.json', 'index.html'):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                value = self.packet(directory)
                (directory / missing).unlink()
                del value['artifacts'][missing]
                for capture in value['captures']:
                    capture['artifacts'] = {k: n for k, n in capture['artifacts'].items() if n != missing}
                # Coherently rewrite all remaining declarations and their hashes.
                for capture in value['captures']:
                    page = directory / expected_paths(capture['width'], capture['state'])['html']
                    if page.exists():
                        text = page.read_text()
                        start = text.index('content="') + len('content="')
                        metadata = json.loads(html.unescape(text[start:-2]))
                        metadata['artifacts'] = capture['artifacts']
                        page.write_text(text[:start] + html.escape(json.dumps(metadata), quote=True) + '">')
                        value['artifacts'][page.name] = hashlib.sha256(page.read_bytes()).hexdigest()
                value['render_inputs_sha256'] = self.module.input_digest(value['source_sha256'])
                self.write_manifest(directory, value)
                with self.assertRaises(ValueError):
                    self.module.verify_artifacts(directory, value['artifacts'])

    def test_extra_missing_tampered_symlink_traversal_and_manifest_refused(self):
        for operation in ('extra', 'missing', 'tampered', 'symlink', 'manifest-symlink', 'manifest-missing', 'traversal', 'index-only'):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                value = self.packet(directory)
                path = directory / 'phase13-overview-320.html'
                if operation == 'extra':
                    (directory / 'extra.html').write_text('unexpected')
                elif operation == 'tampered':
                    path.write_text('tampered')
                elif operation == 'index-only':
                    value['artifacts'] = {'index.html': value['artifacts']['index.html']}
                    self.write_manifest(directory, value)
                elif operation == 'traversal':
                    value['artifacts']['../unsafe.html'] = 'a' * 64
                    self.write_manifest(directory, value)
                else:
                    target = directory / 'manifest.json' if operation.startswith('manifest') else path
                    target.unlink()
                    if 'symlink' in operation:
                        target.symlink_to(PATH)
                with self.assertRaises(ValueError):
                    self.module.verify_artifacts(directory, value['artifacts'])

    def test_capture_paths_and_embedded_metadata_must_correspond(self):
        for operation in ('capture-path', 'html-state', 'trace-body'):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                value = self.packet(directory)
                if operation == 'capture-path':
                    value['captures'][0]['artifacts']['html'] = 'phase13-cap-1440.html'
                else:
                    path = directory / ('phase13-overview-320.html' if operation == 'html-state' else 'phase13-overview-320.trace.json')
                    text = path.read_text()
                    path.write_text(text.replace('overview', 'unknown') if operation == 'html-state' else '[]')
                    value['artifacts'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
                self.write_manifest(directory, value)
                with self.assertRaises(ValueError):
                    self.module.verify_artifacts(directory, value['artifacts'])

    def test_active_html_credentials_and_external_resources_refused(self):
        for content in ('<script>x</script>', '<form>x</form>', '<img src="https://bad.invalid/x">', 'bj_access=secret'):
            with self.subTest(content=content), self.assertRaises(ValueError):
                self.module.validate_html(content)

    def test_render_inventory_includes_fonts_configuration_and_backend(self):
        sources = self.module.source_snapshot()
        for path in ('frontend/src/App.tsx', 'frontend/index.html', 'frontend/package-lock.json',
                     'frontend/vite.config.ts', 'frontend/tsconfig.app.json',
                     'frontend/node_modules/@fontsource-variable/inter/index.css', 'backend/app/services/portfolios.py',
                     'frontend/e2e/portfolio-strategies.spec.ts', 'deploy/tests/portfolio-ui-evidence.py'):
            self.assertIn(path, sources)
        self.assertTrue(any(name.endswith('.woff2') for name in sources))


if __name__ == '__main__':
    unittest.main(verbosity=2)
