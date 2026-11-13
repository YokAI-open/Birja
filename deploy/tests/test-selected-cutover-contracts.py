#!/usr/bin/env python3
"""Offline dispatch/refusal/preservation/cleanup; never integration evidence."""
import ast
import copy
import contextlib
import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('selected', HERE / 'selected-cutover.py')
selected = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selected)


class Contracts(unittest.TestCase):
    def test_current_lane_runs_replay_refusal_and_failed_attempt_recovery(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'history').mkdir()
            (root/'history/deploys.log').write_bytes(b'unchanged log')
            (root/'web').mkdir()
            (root/'web/current').symlink_to('release')
            canonical = {'revision':'0014', 'cash':'10.00', 'authority':['fixed']}
            identities = {'users':b'2|t'}
            events = []
            def compose(*args, **kw):
                events.append(args)
                if args[0] == 'run':
                    return b'runtime_current_mixed_history=true revision0014=true verified_tls=true scheduler_quarantine=true'
                return b'stable'
            def target(argv, ok=True):
                events.append(('target',ok))
                if ok:
                    (root/'history/deploy.pending').unlink()
                    return SimpleNamespace(stdout=b'Rolling back', stderr=b'')
                return SimpleNamespace(stdout=b'', stderr=b'application_schema_incompatible=true')
            @contextlib.contextmanager
            def restored(*args):
                events.append(('restored',))
                yield
            kwargs = dict(session=object(), current='tested', old='old', app=root,
                          root=root, launcher=root/'launcher', target=target,
                          git=lambda *a:'tested', dc=['docker'], compose_env={}, compose=compose,
                          originals={'volume':'fingerprint'}, fingerprint=lambda n:'fingerprint', retained={},
                          original_canonical=canonical, original_identity=identities,
                          runtime_saved='r'*64, dividend_saved='d'*64, inherited=9)
            with mock.patch.object(selected.r, 'canonical', return_value=canonical), \
                 mock.patch.object(selected.r, 'sql', return_value=b'2|t'), \
                 mock.patch.object(selected.r, 'restored', side_effect=restored), \
                 mock.patch.object(selected.r, 'verify') as verify, \
                 mock.patch.object(selected.f, 'runtime_program', return_value='runtime'), \
                 mock.patch.object(selected.f, 'dividend_program', return_value='dividend'), \
                 mock.patch.object(selected.f, 'runtime_receipt_digest', return_value='r'*64), \
                 mock.patch.object(selected.f, 'dividend_digest', return_value='d'*64), \
                 mock.patch.object(selected.f, 'recovery_roundtrip') as recovery, \
                 redirect_stdout(io.StringIO()):
                selected.current0014_checks(**kwargs)
                self.assertEqual(verify.call_count,4)
                self.assertEqual(events.count(('restored',)),2)
                self.assertEqual([event for event in events if event[0]=='target'], [('target',False),('target',True)])
                recovery.assert_called_once_with(kwargs['session'],source_revision='0014',source_release='tested',inherited=9)
                # Independent full canonical and dumped-sequence failures must
                # abort before any success/refusal/rollback transition.
                for altered in ({**canonical,'cash':'9.00'}, {**canonical,'authority':['forged']}):
                    with mock.patch.object(selected.r,'canonical',return_value=altered), self.assertRaisesRegex(AssertionError,'preservation'):
                        selected.current0014_checks(**kwargs)
                with mock.patch.object(selected.r,'sql',return_value=b'3|t'), self.assertRaisesRegex(AssertionError,'preservation'):
                    selected.current0014_checks(**kwargs)

    def test_dispatch_forwards_exact_archive_and_keeps_lanes_distinct(self):
        archive = Path('/tmp/birja-backup-test-offline/recovery.tar')
        with mock.patch.object(selected, '_integration') as run:
            selected.integration(archive)
            selected.integration_current0014(archive)
        self.assertEqual(run.call_args_list, [mock.call(archive, current0014=False), mock.call(archive, current0014=True)])

    def test_refusal_requires_reason_and_exact_state(self):
        state = {'canonical': {'cash': '10.00'}, 'identity': [2, True], 'web': 'release', 'containers': ['a']}
        result = SimpleNamespace(stderr=b'application_schema_incompatible=true')
        target = mock.Mock(return_value=result)
        with redirect_stdout(io.StringIO()):
            selected.refused_rollback(target, Path('/tmp/launcher'), lambda: copy.deepcopy(state))
        target.assert_called_once_with(['/tmp/launcher', '--rollback'], ok=False)
        for stderr in (b'', b'connection failed', b'datastore_bindings_failed=true'):
            target.return_value = SimpleNamespace(stderr=stderr)
            with self.assertRaisesRegex(AssertionError, 'wrong rollback refusal'):
                selected.refused_rollback(target, Path('/tmp/launcher'), lambda: state)
        target.return_value = result
        for key, value in [('canonical', {'cash':'9.00'}), ('identity', [3,True]), ('web','changed'), ('containers',['b'])]:
            changed = {**state, key:value}
            with self.assertRaisesRegex(AssertionError, 'preservation'):
                selected.refused_rollback(target, Path('/tmp/launcher'), mock.Mock(side_effect=[copy.deepcopy(state), changed]))

    def test_finally_executes_owned_cleanup_after_failure(self):
        # Execute the actual scenario finally body, not a duplicate checklist.
        tree = ast.parse((HERE / 'selected-cutover.py').read_text())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_integration')
        block = next(n for n in ast.walk(function) if isinstance(n, ast.Try) and n.finalbody)
        cleanup = compile(ast.fix_missing_locations(ast.Module(body=block.finalbody, type_ignores=[])), '<actual-finally>', 'exec')
        calls = []
        server, held = mock.Mock(), mock.Mock()
        scope = dict(server=server, held=held, dc=['candidate'], dc0=['source'], compose_env={},
                     call=lambda argv, **kw: calls.append(argv) or b'',
                     r=SimpleNamespace(compose=lambda project:[project]),
                     owned=['owned-pg','owned-redis'], PROJECT='birja-ops-test', current0014=True)
        output = io.StringIO()
        with redirect_stdout(output):
            try:
                raise RuntimeError('synthetic operation failure')
            except RuntimeError:
                pass
            finally:
                exec(cleanup, scope)
        server.server_close.assert_called_once()
        held.close.assert_called_once()
        self.assertIn(['candidate','down','--remove-orphans'], calls)
        self.assertIn(['birja-restore-check','down','-v','--remove-orphans'], calls)
        for volume in scope['owned']:
            self.assertIn(['/usr/bin/docker','volume','rm',volume], calls)
        for kind in ('container','network','volume'):
            self.assertIn(['/usr/bin/docker',kind,'ls','-q','--filter','label=com.docker.compose.project=birja-ops-test'], calls)
        self.assertIn('selected0014_cleanup_complete=true revision0014=true', output.getvalue())
        scope['call'] = lambda *a, **kw:b'leftover'
        with redirect_stdout(io.StringIO()), self.assertRaises(AssertionError):
            exec(cleanup, scope)


if __name__ == '__main__':
    unittest.main()
