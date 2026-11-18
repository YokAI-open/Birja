#!/usr/bin/env python3
"""Offline negative contracts; these are not browser execution receipts."""
import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

PATH = Path(__file__).with_name('portfolio-ui-evidence.py')


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

    def test_artifact_missing_tampered_symlink_and_traversal_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            artifact = directory / 'screen.html'
            artifact.write_text('actual bytes')
            hashes = {'screen.html': self.module.digest(artifact.read_bytes())}
            self.module.verify_artifacts(directory, hashes)
            artifact.write_text('tampered')
            with self.assertRaises(ValueError):
                self.module.verify_artifacts(directory, hashes)
            artifact.unlink()
            with self.assertRaises(ValueError):
                self.module.verify_artifacts(directory, hashes)
            artifact.symlink_to(PATH)
            with self.assertRaises(ValueError):
                self.module.verify_artifacts(directory, hashes)
            with self.assertRaises(ValueError):
                self.module.verify_artifacts(directory, {'../screen.html': 'a' * 64})

    def test_active_html_credentials_and_external_resources_refused(self):
        for content in ('<script>x</script>', '<form>x</form>', '<img src="https://bad.invalid/x">', 'bj_access=secret'):
            with self.subTest(content=content), self.assertRaises(ValueError):
                self.module.validate_html(content)

    def test_render_inventory_includes_fonts_configuration_and_backend(self):
        sources = self.module.source_snapshot()
        for path in ('frontend/src/App.tsx', 'frontend/index.html', 'frontend/package-lock.json',
                     'frontend/vite.config.ts', 'backend/app/services/portfolios.py',
                     'frontend/e2e/portfolio-strategies.spec.ts', 'deploy/tests/portfolio-ui-evidence.py'):
            self.assertIn(path, sources)
        self.assertTrue(any(name.endswith('.woff2') for name in sources))


if __name__ == '__main__':
    unittest.main(verbosity=2)
