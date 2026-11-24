#!/usr/bin/env python3
"""Stdlib structural/behavioral CI contracts; no YAML package dependency."""

import ast
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def jobs():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text().split("\njobs:\n", 1)[1]
    matches = list(re.finditer(r"^  ([a-z][a-z0-9-]*):\n", workflow, re.MULTILINE))
    return {
        m[1]: workflow[
            m.end() : matches[i + 1].start() if i + 1 < len(matches) else len(workflow)
        ]
        for i, m in enumerate(matches)
    }


def image_policy(image, aggregate):
    """Validate strict required image wiring; also used against mutations."""
    checkout = re.search(
        r"(?m)^      - uses: actions/checkout@[^\n]+\n"
        r"        with:\n          fetch-depth: 0$", image
    )
    contracts = image.find("python3 deploy/tests/test-ci-ops.py")
    if checkout is None or contracts < 0 or checkout.start() > contracts:
        raise ValueError("image fixture contracts require full Git history first")
    for text in [
        "target: test-builder",
        "target: runtime",
        "tags: birja-backend-runtime:ci",
        "python3 deploy/scan-images.py",
        "--runtime",
        "--builder",
        "--postgres",
        "--redis",
        "--node",
        "actions/upload-artifact@",
        "image-reports",
        "if-no-files-found: error",
        "retention-days: 7",
        "if: always()",
        "2> image-reports/runtime-resolve.log",
        "2> image-reports/builder-resolve.log",
        "2> image-reports/node-resolve.log",
    ]:
        if text not in image:
            raise ValueError("missing image policy: " + text)
    if image.count("load: true") < 2 or "load: false" in image:
        raise ValueError("both built stages must load")
    for forbidden in [
        "continue-on-error",
        "ignore-unfixed",
        "ignorefile",
        "--vex",
        "|| true",
    ]:
        if forbidden in image:
            raise ValueError("fail-open image policy")
    if not re.search(r"needs: \[[^\]]*\bimage\b", aggregate):
        raise ValueError("image is required")


def recovery_policy(ops, runner_source=None):
    command = "run: sudo -- python3 deploy/tests/run-portfolio-validation.py --suite recovery"
    if sum(line.strip() == command for line in ops.splitlines()) != 1:
        raise ValueError("missing exact serial runner")
    source = runner_source if runner_source is not None else (ROOT / "deploy/tests/run-portfolio-validation.py").read_text()
    tree = ast.parse(source)
    constants = {node.targets[0].id: node.value for node in tree.body
                 if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)}
    expected = ("image-transition", "retained-roundtrip", "current0023-cold", "roles",
                "tls-upgraded", "tls-fresh", "selected-rollback")
    if ast.literal_eval(constants["STAGES"]) != expected:
        raise ValueError("missing or reordered serial stage")
    for required in (
        "ops.package_current_archive(archive)", "ops.r.bundle_verify(archive, expected",
        "ops.bind_source_archive(archive, expected)", "ops.roundtrip(archive)",
        "cold=True", "ops.roles", "fresh_bootstrap=fresh", "--recovery-bundle",
        "authenticate(ops, archive, expected, source, image_records)", "verify_archive_binding(archive, expected)",
        "retained.extractfile(name).read() != (ROOT / name).read_bytes()",
        "source != {name: ops.r.digest(ROOT / name) for name in source}",
        "verify_image(binding, inspect)", "PORTFOLIO_PAYLOAD_V4", "RETAINED_CLOSURE_SOURCE_PAYLOADS",
        "Path(\"/tmp/birja-phase14-proof/recovery.tar.gz\")",
    ):
        if required not in source:
            raise ValueError("missing source-frozen graph: " + required)
    for command in ("bash deploy/tests/test-deploy-compatibility.sh",
                    "python3 deploy/tests/test-selected-cutover-contracts.py"):
        if command not in ops:
            raise ValueError("missing selected compatibility contract")


def postgres_stack_policy(ops):
    """Execute the actual CI try/finally with command effects replaced."""
    marker = "- name: Real PostgreSQL recovery contracts with owned stack"
    if ops.count(marker) != 1:
        raise ValueError("missing owned PostgreSQL contract step")
    step = ops.split(marker, 1)[1].split("\n      - name:", 1)[0]
    if ops.index(marker) < ops.index("bash deploy/tests/test-db-config.sh"):
        raise ValueError("PostgreSQL contracts precede prior stack cleanup")
    lines = step.splitlines()
    start = lines.index("          python3 - <<'PY'") + 1
    end = lines.index("          PY", start)
    tree = ast.parse(textwrap.dedent("\n".join(lines[start:end])))
    body = [node for node in tree.body if not isinstance(node, ast.Import)]
    code = compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])),
                   "<actual-postgres-stack-step>", "exec")
    stack = ["docker", "compose", "-f", "docker-compose.test.yml"]
    expected = [stack + ["up", "-d", "--wait"],
                ["sudo", "--", "python3", "deploy/tests/test-stock-recovery-contracts.py", "--postgres"],
                stack + ["down", "-v"]]
    for failed in (None, 0, 1, 2):
        calls = []
        failure = RuntimeError("synthetic command failure")
        def run(argv, *, check):
            if check is not True or argv not in expected:
                raise ValueError("changed PostgreSQL command or failure policy")
            calls.append(argv)
            if failed is not None and argv == expected[failed]:
                raise failure
        try:
            exec(code, {"subprocess": SimpleNamespace(run=run)})
        except RuntimeError as error:
            if error is not failure or failed is None:
                raise ValueError("unexpected PostgreSQL failure") from error
        else:
            if failed is not None:
                raise ValueError("swallowed PostgreSQL setup/test/cleanup failure")
        if calls != ([expected[0], expected[2]] if failed == 0 else expected):
            raise ValueError("PostgreSQL setup/order/cleanup missing")


def selected_policy(rollback):
    """Execute actual default dispatch with effect fakes, including each failure."""
    body = rollback.split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    tree = ast.parse(body)
    dispatch = tree.body[-1]
    if not isinstance(dispatch, ast.If) or not isinstance(dispatch.orelse[0], ast.If):
        raise ValueError("missing runner dispatch")
    code = compile(ast.fix_missing_locations(ast.Module(
        body=dispatch.orelse[0].orelse, type_ignores=[])), "<actual-rollback-dispatch>", "exec")
    expected = ["self-test", "rollback", "legacy0008", "current0014"]
    archive = object()  # identity, not just equal path spelling
    for failed in [None, *expected]:
        calls = []
        failure = RuntimeError("synthetic stage failure")

        def stage(name, argument=archive):
            if argument is not archive:
                raise ValueError("selected archive replaced")
            calls.append(name)
            if name == failed:
                raise failure

        selected = SimpleNamespace(
            integration=lambda arg: stage("legacy0008", arg),
            integration_current0014=lambda arg: stage("current0014", arg))
        fake_import = SimpleNamespace(util=SimpleNamespace(
            spec_from_file_location=lambda *args: SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module: None)),
            module_from_spec=lambda spec: selected))
        scope = dict(ROOT=ROOT, importlib=fake_import,
                     args=SimpleNamespace(recovery_bundle=archive),
                     orchestration_self_test=lambda: stage("self-test"),
                     integration=lambda arg: stage("rollback", arg))
        try:
            exec(code, scope)
        except RuntimeError as exc:
            if exc is not failure:
                raise
            wanted = expected[:expected.index(failed) + 1]
        else:
            if failed is not None:
                raise ValueError("runner swallowed stage failure: " + failed)
            wanted = expected
        if calls != wanted:
            raise ValueError("selected stages omitted or reordered")


def dev_authority_policy(ops, compose_files):
    if "python3 deploy/tests/test-dev-bootstrap.py --image birja-backend-test:phase05-07" not in ops:
        raise ValueError("missing actual ordinary dev financial gate")
    for source in compose_files:
        sequence = ["python -m app.db.dev_bootstrap --migrate &&", "exec uvicorn"]
        if any(part not in source for part in sequence):
            raise ValueError("missing dev owner authority stage")
        if [source.index(part) for part in sequence] != sorted(source.index(part) for part in sequence):
            raise ValueError("dev owner authority stages reordered")


def required_gate_policy(j):
    # Reuse the independent fixed inventory without importing pytest/DB code.
    tree = ast.parse((ROOT / "backend/tests/test_critical_coverage_config.py").read_text())
    modules = ast.literal_eval(next(node.value for node in tree.body
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and
            t.id == "CRITICAL_MODULES" for t in node.targets)))
    required = {
        "backend": ["pytest --cov=app --cov-branch --cov-fail-under=80",
                    "coverage report --include=" + ",".join(modules) + " --fail-under=100",
                    "uv run pip-audit"],
        "frontend": ["npm run test -- --coverage", "node --test ../deploy/tests/test-frontend-audit.mjs",
                     "node ../deploy/audit-frontend.mjs"],
        "ci-pass": ["needs: [backend, frontend, image, e2e, ops]", "if: always()",
                    *["contains(needs.*.result, '" + result + "')"
                      for result in ("failure", "cancelled", "skipped")], "exit 1"],
    }
    for job, tokens in required.items():
        if any(token not in j[job] for token in tokens):
            raise ValueError("required coverage/security/aggregate gate removed: " + job)
    image_policy(j["image"], j["ci-pass"])


class CI(unittest.TestCase):
    def test_tls_retained_services_keep_image_code_and_only_mount_public_ca(self):
        tree = ast.parse((ROOT / "deploy/tests/ops-fixtures.py").read_text())
        tls = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "tls")
        loop = next(node for node in ast.walk(tls)
                    if isinstance(node, ast.For) and isinstance(node.target, ast.Tuple)
                    and [item.id for item in node.target.elts] == ["name", "source"])
        image = "sha256:" + "b" * 64
        root = Path("/private-synthetic-tls")
        services = {name: {"image": "unselected", "user": "1001:1001",
                          "command": ["actual-migration-command"],
                          "volumes": ["unrelated:/app/app:ro"], "ports": ["1234:1234"]}
                    for name in ("postgres", "redis", "backend", "scheduler", "migrate")}
        import copy
        original = copy.deepcopy(services)
        namespace = {"prod": {"services": services}, "fixture": {"services": {}},
                     "root": root, "hba": root / "hba", "retained_image": image,
                     "retained_source": Path("/unreadable-private-retained-context"), "copy": copy}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[loop], type_ignores=[])),
                     "<actual-retained-tls-composition>", "exec"), namespace)
        actual = namespace["fixture"]["services"]
        self.assertEqual(services, original)
        for name in ("backend", "scheduler", "migrate"):
            with self.subTest(service=name):
                self.assertEqual(actual[name]["image"], image)
                self.assertEqual(actual[name]["user"], "1001:1001")
                self.assertEqual(actual[name]["volumes"],
                                 [str(root / "db-tls/ca.crt") + ":/run/birja/db-ca.crt:ro"])
                self.assertNotIn("ports", actual[name])
        self.assertEqual(actual["migrate"]["command"], ["actual-migration-command"])

    def test_retained_role_child_uses_authenticated_image_without_source_overlays(self):
        tree = ast.parse((ROOT / "deploy/tests/ops-fixtures.py").read_text())
        function = next(node for node in tree.body
                        if isinstance(node, ast.FunctionDef) and node.name == "role_python")
        image = "sha256:" + "a" * 64
        with patch("subprocess.run") as run:
            run.return_value = SimpleNamespace(returncode=0, stdout=b"original-receipt", stderr=b"")
            source = SimpleNamespace(BOOT="birja_ops_bootstrap", ENV={"PATH": "/usr/bin:/bin"})
            retained = lambda: (Path("/unreadable-root-owned-retained-source"), image)
            namespace = {"r": source, "subprocess": subprocess, "retained_runtime": retained}
            exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])),
                         "<actual-retained-role-child>", "exec"), namespace)
            self.assertEqual(namespace["role_python"]("assert original_receipt", "birja_migrator"),
                             b"original-receipt")
            argv = run.call_args.args[0]
            self.assertEqual(argv[-2:], [image, "-"])
            self.assertEqual(argv[argv.index("--network") + 1], "birja-ops-test_isolated")
            self.assertEqual(argv[argv.index("--entrypoint") + 1], "python")
            self.assertNotIn("-v", argv)
            self.assertNotIn("--volume", argv)
            self.assertNotIn("--mount", argv)
            self.assertNotIn("--user", argv)
            self.assertEqual(run.call_args.kwargs["input"], b"assert original_receipt")
            self.assertEqual(run.call_args.kwargs["env"], source.ENV)
            namespace["retained_runtime"] = lambda: (_ for _ in ()).throw(ValueError("source binding"))
            run.reset_mock()
            with self.assertRaisesRegex(ValueError, "source binding"):
                namespace["role_python"]("assert original_receipt")
            run.assert_not_called()

    def portfolio_sources(self):
        spec = importlib.util.spec_from_file_location('source_binding_contract', ROOT / 'deploy/tests/portfolio-sources.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_exact_retained_source_matrix_before_import(self):
        import copy
        source = self.portfolio_sources()
        source.validate_matrix()
        for revision,kind in [('0013','execution'),('0013','runtime'),('0014','runtime'),('0014','dividend'),('0017','portfolio')]:
            source.qualified_revision(revision,kind)
        for revision,kind in [('0013','portfolio'),('0014','portfolio'),('0017','runtime'),('0013','dividend'),('head','runtime')]:
            with self.assertRaises(ValueError):source.qualified_revision(revision,kind)
        mutations=[]
        for key in ('commit','app_tree','alembic_tree','archive_sha256'):
            value=copy.deepcopy(source.MATRIX);value['retained'][key]='0'*40;mutations.append(value)
        for path in source.MATRIX['retained']['files']:
            value=copy.deepcopy(source.MATRIX);value['retained']['files'][path]='0'*40;mutations.append(value)
        value=copy.deepcopy(source.MATRIX);del value['retained']['files']['backend/uv.lock'];mutations.append(value)
        for lane in ('legacy0008','legacy0007'):
            value=copy.deepcopy(source.MATRIX);value[lane]['commit']=source.FIXED_COMMIT;mutations.append(value)
        for value in mutations:
            with self.assertRaises(ValueError):source.validate_matrix(value)
        with tempfile.TemporaryDirectory(prefix='birja-source-archive-') as tmp:
            import io, tarfile, hashlib
            archive=Path(tmp)/'recovery.tar'
            with tarfile.open(archive,'w') as recovery:
                for name,data in source.archive_payloads().items():
                    info=tarfile.TarInfo(name);info.size=len(data)
                    recovery.addfile(info,io.BytesIO(data))
            sha=hashlib.sha256(archive.read_bytes()).hexdigest()
            program=source.retained_program('runtime',revision='0013',archive=archive,archive_sha=sha,seed=True)
            for bad in ('0'*64,None):
                with self.assertRaises(ValueError):
                    source.retained_program('runtime',revision='0013',archive=archive,archive_sha=bad,seed=True)
            for missing in (True,False):
                wrong=Path(tmp)/('missing.tar' if missing else 'modified.tar')
                with tarfile.open(wrong,'w') as recovery:
                    if not missing:
                        data=b'wrong retained payload';info=tarfile.TarInfo('sources/retained.tar');info.size=len(data)
                        recovery.addfile(info,io.BytesIO(data))
                wrong_sha=hashlib.sha256(wrong.read_bytes()).hexdigest()
                with self.assertRaises(ValueError):source.retained_program('runtime',revision='0013',archive=wrong,archive_sha=wrong_sha,seed=True)
        self.assertLess(program.index('asyncio.run(declared_revision())'),program.index('sys.path.insert'))
        self.assertIn(source.FIXED_COMMIT,program)
        self.assertIn("EXPECTED_REVISION='0013'",program)
        compile(program,'<exact-retained-program>','exec')

    def test_image_config_roots_source_and_same_archive_substitution_refused(self):
        import copy
        source=self.portfolio_sources()
        image=[{'Id':'sha256:'+'a'*64,'Config':{'Labels':{'org.opencontainers.image.revision':source.FIXED_COMMIT},'User':'app'},'RootFS':{'Layers':['sha256:'+'b'*64]}}]
        binding=source.image_binding(image,source_commit=source.FIXED_COMMIT,app_tree=source.FIXED_APP,context_sha256=source.MATRIX['retained']['archive_sha256'])
        self.assertEqual(source.verify_image(binding,image),image[0]['Id'])
        for section,key,value in [('Config','User','root'),('RootFS','Layers',['sha256:'+'c'*64])]:
            changed=copy.deepcopy(image);changed[0][section][key]=value
            with self.assertRaises(ValueError):source.verify_image(binding,changed)
        changed=copy.deepcopy(image);changed[0]['Id']='sha256:'+'d'*64
        with self.assertRaises(ValueError):source.verify_image(binding,changed)
        changed=copy.deepcopy(image);changed[0]['Config']['Labels']['org.opencontainers.image.revision']='0'*40
        with self.assertRaises(ValueError):source.verify_image(binding,changed)
        with tempfile.TemporaryDirectory(prefix='birja-source-binding-') as tmp:
            path=Path(tmp)/'one.tar';path.write_bytes(b'one immutable archive')
            digest=__import__('hashlib').sha256(path.read_bytes()).hexdigest()
            source.verify_archive_binding(path,digest)
            path.write_bytes(b'rebuilt archive')
            with self.assertRaises(ValueError):source.verify_archive_binding(path,digest)
            binding_archive=Path(tmp)/'selected.tar'
            source.record_image_binding(binding_archive,'retained',binding)
            source.record_image_binding(binding_archive,'retained',binding)
            with self.assertRaises(ValueError):source.record_image_binding(binding_archive,'retained',{**binding,'id':'sha256:'+'d'*64})

    def test_identical_archives_have_independent_campaign_image_namespaces(self):
        import hashlib, io, tarfile
        source = self.portfolio_sources()
        row = {'Id': 'sha256:' + 'a' * 64,
               'Config': {'Labels': {'org.opencontainers.image.revision': source.FIXED_COMMIT},
                          'User': 'app'},
               'RootFS': {'Layers': ['sha256:' + 'b' * 64]}}
        images, builds = {}, []
        check_output = source.subprocess.check_output
        run = source.subprocess.run

        def inspect(argv, **kwargs):
            if argv[:3] == ['docker', 'image', 'inspect']:
                return json.dumps([images[argv[3]]]).encode()
            return check_output(argv, **kwargs)

        def docker(argv, **kwargs):
            if argv[0] != 'docker':
                return run(argv, **kwargs)
            if argv[:3] == ['docker', 'image', 'inspect']:
                image = images.get(argv[3])
                return SimpleNamespace(returncode=0 if image else 1,
                                       stdout=json.dumps([image]).encode() if image else b'')
            self.assertEqual(argv[:2], ['docker', 'build'])
            tag = argv[argv.index('-t') + 1]
            self.assertNotIn(tag, images, 'another campaign tag must never be overwritten')
            images[tag] = row
            builds.append(tag)
            return SimpleNamespace(returncode=0, stdout=b'')

        with tempfile.TemporaryDirectory(prefix='birja-source-campaigns-') as tmp:
            root = Path(tmp)
            campaign = root / 'fixed-proof'
            campaign.mkdir(mode=0o700)
            archive = campaign / 'recovery.tar'
            with tarfile.open(archive, 'w') as recovery:
                for name, data in source.archive_payloads().items():
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    recovery.addfile(info, io.BytesIO(data))
            archive.chmod(0o400)
            payload = archive.read_bytes()
            sha = hashlib.sha256(payload).hexdigest()
            with patch.object(source.subprocess, 'run', side_effect=docker), \
                    patch.object(source.subprocess, 'check_output', side_effect=inspect):
                # Git identity is real; only Docker's external boundary is replaced.
                first = source.build_retained_image(root / 'context-one', archive=archive,
                                                    archive_sha=sha)
                replay = source.build_retained_image(root / 'context-replay', archive=archive,
                                                     archive_sha=sha)
                self.assertEqual(first, replay)
                self.assertEqual(len(builds), 1)
                historical = root / 'preserved-proof'
                campaign.rename(historical)
                campaign.mkdir(mode=0o700)
                archive.write_bytes(payload)
                archive.chmod(0o400)
                second = source.build_retained_image(root / 'context-two', archive=archive,
                                                     archive_sha=sha)
                self.assertEqual(first, second)
                self.assertEqual(len(builds), 2)
                self.assertNotEqual(builds[0], builds[1])
                # An existing image with its own campaign binding removed still refuses.
                record = campaign / 'retained-image-binding.json'
                record.unlink()
                with self.assertRaisesRegex(ValueError, 'no private campaign binding'):
                    source.build_retained_image(root / 'context-unbound', archive=archive,
                                                archive_sha=sha)

    def test_selected_tooling_checks_content_image_and_archive_before_use(self):
        import copy, hashlib
        selected_spec=importlib.util.spec_from_file_location('selected_source_contract', ROOT/'deploy/tests/selected-cutover.py')
        selected=importlib.util.module_from_spec(selected_spec);selected_spec.loader.exec_module(selected)
        source=self.portfolio_sources()
        row={'Id':'sha256:'+'a'*64,'Config':{'Labels':{'org.opencontainers.image.revision':source.FIXED_COMMIT},'User':'app'},'RootFS':{'Layers':['sha256:'+'b'*64]}}
        binding=source.image_binding([row],source_commit=source.FIXED_COMMIT,app_tree=source.FIXED_APP,context_sha256=source.MATRIX['retained']['archive_sha256'])
        with tempfile.TemporaryDirectory(prefix='birja-selected-contract-') as tmp:
            archive=Path(tmp)/'recovery.tar';archive.write_bytes(b'immutable selected archive')
            sha=hashlib.sha256(archive.read_bytes()).hexdigest()
            code=selected.qualified_image_program({source.FIXED_COMMIT:binding},archive=archive,archive_sha=sha,migrator_commit=source.FIXED_COMMIT)
            def invoke(image,commit=source.FIXED_COMMIT):
                import contextlib,io
                result=io.StringIO()
                with patch.object(sys,'argv',['qualified-images.py',commit]),patch.object(subprocess,'check_output',return_value=json.dumps([image]).encode()),contextlib.redirect_stdout(result):
                    exec(compile(code,'<actual-private-image-binding>','exec'),{})
                return result.getvalue().strip()
            self.assertEqual(invoke(row),row['Id']+' '+row['Id'])
            for field,key,value in [('Config','User','root'),('RootFS','Layers',[]),('Config','Labels',{})]:
                changed=copy.deepcopy(row);changed[field][key]=value
                with self.assertRaises((AssertionError,KeyError)):invoke(changed)
            with self.assertRaises(KeyError):invoke(row,'0'*40)
            archive.write_bytes(b'rebuilt archive')
            with self.assertRaises(AssertionError):invoke(row)
        text=(ROOT/'deploy/tests/selected-cutover.py').read_text()
        self.assertNotIn('git("commit"',text)
        self.assertNotIn('legacy_archive.extractall(app',text)
        self.assertIn("git('checkout', '--detach', current)",text)
        self.assertIn("source_binding.chmod(0o400)",text)

    def test_complete_source_context_mutation_fails_before_child(self):
        import io,tarfile
        source=self.portfolio_sources();payload=source.source_archive()
        with tempfile.TemporaryDirectory(prefix='birja-source-context-') as tmp:
            root=Path(tmp)
            with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
                archive.extractall(root,filter='data')
            source.verify_source_tree(root,payload)
            path=root/'backend/app/main.py';old=path.read_bytes();path.write_bytes(old+b'\n# substitution\n')
            with self.assertRaises(ValueError):source.verify_source_tree(root,payload)
            path.write_bytes(old);(root/'unreviewed.py').write_text('pass\n')
            with self.assertRaises(ValueError):source.verify_source_tree(root,payload)

    def test_actual_postgres_stack_order_and_failure_cleanup(self):
        ops = jobs()["ops"]
        postgres_stack_policy(ops)
        up = 'subprocess.run(stack + ["up", "-d", "--wait"], check=True)'
        contracts = 'subprocess.run(["sudo", "--", "python3", "deploy/tests/test-stock-recovery-contracts.py", "--postgres"], check=True)'
        mutations = [
            ops.replace('subprocess.run(stack + ["up", "-d", "--wait"], check=True)', 'pass'),
            ops.replace('subprocess.run(stack + ["down", "-v"], check=True)', 'pass'),
            ops.replace('          finally:', '          except Exception:'),
            ops.replace('"deploy/tests/test-stock-recovery-contracts.py", "--postgres"', '"deploy/tests/test-stock-recovery-contracts.py", "--offline"'),
            ops.replace('docker-compose.test.yml', 'docker-compose.yml'),
            ops.replace('check=True', 'check=False'),
            ops.replace(up, '__swap__').replace(contracts, up).replace('__swap__', contracts),
            ops.replace(contracts, 'try:\n                  '+contracts+
                        '\n              except RuntimeError:\n                  pass'),
        ]
        for mutated in mutations:
            with self.assertRaises((ValueError, SyntaxError)):
                postgres_stack_policy(mutated)

    def test_mandatory_coverage_audits_and_aggregate_reject_omission_mutations(self):
        j = jobs()
        required_gate_policy(j)
        mutations = {
            "backend": ["--cov-branch", "--cov-fail-under=80", "--fail-under=100",
                        "uv run pip-audit", *re.findall(r"app/[\w/]+\.py", j["backend"])],
            "frontend": ["npm run test -- --coverage", "node --test ../deploy/tests/test-frontend-audit.mjs",
                         "node ../deploy/audit-frontend.mjs"],
            "ci-pass": ["backend, ", "frontend, ", "image, ", "e2e, ", ", ops",
                        "if: always()", "'failure'", "'cancelled'", "'skipped'", "exit 1"],
        }
        for job, tokens in mutations.items():
            for token in tokens:
                with self.subTest(job=job, omitted=token), self.assertRaises(ValueError):
                    required_gate_policy({**j, job: j[job].replace(token, "omitted")})

    def test_selected_runner_requires_both_same_archive_serial_fail_closed_lanes(self):
        runner = (ROOT / "deploy/tests/test-rollback-db-security.sh").read_text()
        selected_policy(runner)
        legacy = "selected.integration(args.recovery_bundle)"
        current = "selected.integration_current0014(args.recovery_bundle)"
        mutations = [runner.replace(call, "pass") for call in (legacy, current)]
        mutations += [runner.replace(call, call.replace("args.recovery_bundle", "None"))
                      for call in (legacy, current)]
        mutations.append(runner.replace(legacy + "\n    " + current,
                                        current + "\n    " + legacy))
        for call in (legacy, current):
            mutations.append(runner.replace(call, "try:\n        " + call +
                                            "\n    except RuntimeError:\n        pass"))
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                selected_policy(mutation)

    def test_actual_ordinary_dev_financial_gate_and_postmigration_order_are_required(self):
        ops = jobs()["ops"]
        sources = [(ROOT / name).read_text() for name in ("docker-compose.yml", "docker-compose.override.yml")]
        dev_authority_policy(ops, sources)
        with self.assertRaises(ValueError):
            dev_authority_policy(ops.replace("python3 deploy/tests/test-dev-bootstrap.py", "omitted"), sources)
        for index in range(2):
            changed = sources.copy()
            changed[index] = changed[index].replace("python -m app.db.dev_bootstrap --migrate &&", "")
            with self.assertRaises(ValueError):
                dev_authority_policy(ops, changed)

    def test_same_archive_recovery_rejects_missing_or_reordered_stages(self):
        ops = jobs()["ops"]
        recovery_policy(ops)
        source = (ROOT / "deploy/tests/run-portfolio-validation.py").read_text()
        for old in (
            "ops.package_current_archive(archive)", "ops.roundtrip(archive)",
            "cold=True", "fresh_bootstrap=fresh", "--recovery-bundle",
            "verify_archive_binding(archive, expected)", "verify_image(binding, inspect)",
            "retained.extractfile(name).read() != (ROOT / name).read_bytes()",
            "source != {name: ops.r.digest(ROOT / name) for name in source}",
        ):
            with self.assertRaises((ValueError, SyntaxError)):
                recovery_policy(ops, source.replace(old, "omitted_stage"))
        with self.assertRaises(ValueError):
            recovery_policy(ops.replace("--suite recovery", "--suite all-security"))
        with self.assertRaises(ValueError):
            recovery_policy(ops.replace("--suite recovery", "--suite recovery-current"))
        with self.assertRaises(ValueError):
            recovery_policy(ops, source.replace("\"roles\", \"tls-upgraded\"", "\"tls-upgraded\", \"roles\"", 1))
        for old in ("bash deploy/tests/test-deploy-compatibility.sh", "python3 deploy/tests/test-selected-cutover-contracts.py"):
            with self.assertRaises(ValueError):
                recovery_policy(ops.replace(old, "omitted_stage"))

    def test_dividend_authority_history_and_schedulers_are_required(self):
        backend = jobs()["backend"]
        for module in [
            "services/dividend_rules", "services/dividends", "services/event_history",
            "schemas/event_history", "api/v1/event_history", "tasks/dividends",
            "tasks/scheduler", "db/dev_bootstrap",
        ]:
            self.assertIn("app/" + module + ".py", backend)
        self.assertIn("--cov-branch", backend)
        self.assertIn('"deploy/tests/test-stock-recovery-contracts.py", "--postgres"', jobs()["ops"])
        fixture = (ROOT / "deploy/tests/ops-fixtures.py").read_text()
        for proof in [
            "actual_restored_dividend_saved_replay=true financial_quarantine=true",
            "actual_restored_current_stock_history_0014=true original_receipt_unchanged=true financial_quarantine=true",
            "assert b'runtime_current_mixed_history=true revision0014=true' in current_runtime",
            "actual_dividend_sql_verified_tls=true", "dividend_authority",
            "tls(fresh_bootstrap=True)",
        ]:
            self.assertIn(proof, fixture)
        dividend = (ROOT / "deploy/tests/dividend-execution-fixture.py").read_text()
        self.assertIn("record_stock_dividend_hold", dividend)

    def test_stock_safety_and_real_tls_evaluator_are_required(self):
        j = jobs()
        for module in ["stock_admission", "stock_quote_rules", "stock_quotes", "stock_sessions", "stocks"]:
            self.assertIn("app/services/" + module + ".py", j["backend"])
        self.assertIn("app/api/v1/stocks.py", j["backend"])
        fixture = (ROOT / "deploy/tests/ops-fixtures.py").read_text()
        self.assertIn("from app.services.stock_sessions import", fixture)
        self.assertIn("await calendar_consumer_contract(app,scheduler,migrator)", fixture)
        self.assertIn("tls(fresh_bootstrap=True)", fixture)
        self.assertIn("calendar_runtime_tls_consumer=true", fixture)
        self.assertNotIn("evaluator_proof=plan08_13", fixture)

    def test_ops_pins_compose_with_explicit_retained_dockerfile_consent(self):
        ops = jobs()["ops"]
        self.assertIn("compose_version=5.7.0-1~ubuntu.24.04~noble", ops)
        self.assertIn('"docker-compose-plugin=$compose_version"', ops)
        check = "test \"$(sudo -- env -i PATH=/usr/bin:/bin HOME=/tmp LANG=C.UTF-8 /usr/bin/docker compose version --short)\" = '5.7.0'"
        self.assertIn(check, ops)
        self.assertLess(
            ops.index(check), ops.index("- name: Build locked operations fixture image")
        )
        for bypass in [
            "BUILDX_BAKE_ENTITLEMENTS_FS",
            "COMPOSE_BAKE=false",
            "fs.read=*",
            "fs=*",
        ]:
            self.assertNotIn(bypass, ops)

    def test_ops_preserves_daemon_settings_and_checks_strict_archive_before_build(self):
        ops = jobs()["ops"]
        merge = ops.split("sudo python3 -c '\n", 1)[1].split("\n          '\n", 1)[0]
        merge = textwrap.dedent(merge)
        for initial in [None, {"log-driver": "local", "features": {"buildkit": True}}]:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "daemon.json"
                if initial is not None:
                    path.write_text(json.dumps(initial))
                subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        merge.replace("/etc/docker/daemon.json", str(path)),
                    ],
                    check=True,
                )
                expected = initial or {}
                expected.setdefault("features", {})["containerd-snapshotter"] = True
                self.assertEqual(json.loads(path.read_text()), expected)
        self.assertLess(
            ops.index("containerd-snapshotter"),
            ops.index("sudo systemctl restart docker"),
        )
        check = "sudo -- env -i PATH=/usr/bin:/bin HOME=/tmp LANG=C.UTF-8 python3 deploy/tests/check-recovery-image.py"
        self.assertIn(check, ops)
        self.assertLess(
            ops.index(check), ops.index("- name: Build locked operations fixture image")
        )
        spec = importlib.util.spec_from_file_location(
            "image_preflight", ROOT / "deploy/tests/check-recovery-image.py"
        )
        preflight = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(preflight)
        for store in [[], [["driver-type", "io.containerd.snapshotter.v1"]]]:
            with (
                patch.object(
                    preflight.r, "call", return_value=json.dumps(store).encode()
                ),
                patch.object(preflight.subprocess, "run") as save,
                patch.object(
                    preflight.r,
                    "registry_manifests",
                    return_value=(b"index", b"manifest"),
                ) as manifests,
                patch.object(preflight.r, "verify_saved_image") as verify,
                patch.object(preflight.r, "bind_recovery_image") as bind,
            ):
                if not store:
                    with self.assertRaises(ValueError):
                        preflight.main()
                    save.assert_not_called()
                    manifests.assert_not_called()
                    verify.assert_not_called()
                    bind.assert_not_called()
                else:
                    preflight.main()
                    self.assertEqual(
                        save.call_args_list[0].args[0],
                        [
                            "/usr/bin/docker",
                            "image",
                            "save",
                            "--platform",
                            "linux/amd64",
                            preflight.r.REGISTRY_REF,
                        ],
                    )
                    self.assertEqual(verify.call_args.args[1:], (b"index", b"manifest"))
                    self.assertEqual(save.call_args_list[-1].args[0], ["/usr/bin/docker", "image", "load"])
                    bind.assert_called_once_with()

    def test_ops_prepares_default_socket_docker_platform_api_before_fixtures(self):
        ops = jobs()["ops"]
        setup = ops.index("- name: Prepare Docker platform API for recovery fixtures")
        verify = ops.index("- name: Verify recovery image platform capability")
        build = ops.index("- name: Build locked operations fixture image")
        self.assertLess(setup, verify)
        self.assertLess(verify, build)
        preparation = ops[setup:verify]
        for required in [
            "timeout-minutes: 8",
            "https://download.docker.com/linux/ubuntu/gpg",
            "signed-by=/etc/apt/keyrings/docker.asc",
            "signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg",
            '-o "Dir::Etc::sourcelist=$sources"',
            "-o Dir::Etc::sourceparts=-",
            "-o Acquire::Retries=2",
            "-o Acquire::https::Timeout=30",
            'sudo apt-get "${apt_options[@]}" -o APT::Update::Error-Mode=any update',
            'sudo apt-get "${apt_options[@]}" install',
            "docker_version=5:29.2.1-1~ubuntu.24.04~noble",
            '"docker-ce=$docker_version"',
            '"docker-ce-cli=$docker_version"',
            "sudo systemctl restart docker",
        ]:
            self.assertIn(required, preparation)
        preflight = ops[verify:build]
        for required in [
            "sudo -- /usr/bin/docker version",
            "29.2.1 29.2.1",
            "sudo -- /usr/bin/docker pull --platform linux/amd64",
            "env -i PATH=/usr/bin:/bin HOME=/tmp LANG=C.UTF-8",
            'image inspect "$postgres" --platform linux/amd64',
        ]:
            self.assertIn(required, preflight)
        for forbidden in ["trusted=yes", "--allow-unauthenticated", "DOCKER_HOST="]:
            self.assertNotIn(forbidden, ops[setup:build])

    def test_ops_prepares_locked_host_backend_before_db_config_contracts(self):
        ops = jobs()["ops"]
        self.assertIn("uses: astral-sh/setup-uv@v10.3.2", ops)
        setup = ops.index("uses: astral-sh/setup-uv@v10.3.2")
        install = ops.index("uv python install")
        sync = ops.index("uv sync --locked")
        contracts = ops.index("- name: Offline operational contracts")
        self.assertLess(setup, install)
        self.assertLess(install, sync)
        self.assertLess(sync, contracts)
        environment = ops[setup:contracts]
        self.assertIn("working-directory: backend", environment)
        self.assertIn("cache-dependency-glob: backend/uv.lock", environment)
        for excluded in ["--no-default-groups", "--no-dev", "--only-group"]:
            self.assertNotIn(excluded, environment)

    def test_image_policy_and_mutation_regressions(self):
        j = jobs()
        image_policy(j["image"], j["ci-pass"])
        for old, new in [
            ("fetch-depth: 0", "fetch-depth: 1"),
            ("        with:\n          fetch-depth: 0\n", ""),
            ("python3 deploy/scan-images.py", "true"),
            ("--node", "--omitted"),
            ("image-reports", "other"),
            ("load: true", "load: false"),
            ("--runtime", "--ignore-unfixed --runtime"),
            ("push: false", "continue-on-error: true"),
            ("2> image-reports/node-resolve.log", "2>/dev/null"),
        ]:
            with self.assertRaises(ValueError):
                image_policy(j["image"].replace(old, new), j["ci-pass"])
        checkout = re.search(
            r"(?m)^      - uses: actions/checkout@[^\n]+\n"
            r"        with:\n          fetch-depth: 0\n", j["image"]
        )[0]
        with self.assertRaises(ValueError):
            image_policy(j["image"].replace(checkout, "") + checkout, j["ci-pass"])
        with self.assertRaises(ValueError):
            image_policy(j["image"], j["ci-pass"].replace(", image", ""))

    def test_required_aggregate_rejects_every_nonsuccess(self):
        j = jobs()
        self.assertIn("ops", j)
        needs = re.search(r"^    needs: \[([^\]]+)\]$", j["ci-pass"], re.MULTILINE)
        self.assertIsNotNone(needs)
        self.assertEqual(
            {s.strip() for s in needs[1].split(",")},
            {"backend", "frontend", "image", "e2e", "ops"},
        )
        self.assertIn("if: always()", j["ci-pass"])
        for result in ["failure", "cancelled", "skipped"]:
            self.assertIn("contains(needs.*.result, '" + result + "')", j["ci-pass"])
        self.assertRegex(j["ci-pass"], r"(?s)if \[.*exit 1")

    def test_ops_exports_only_exact_archive_after_full_recovery(self):
        ops = jobs()["ops"]
        serial = ops.index("- name: Serial real PostgreSQL recovery")
        stage = ops.index("- name: Stage verified recovery tooling")
        upload = ops.index("- name: Upload verified recovery tooling")
        cleanup = ops.index("- name: Clean fixed synthetic projects")
        self.assertLess(serial, stage)
        self.assertLess(stage, upload)
        self.assertLess(upload, cleanup)
        preparation = ops[stage:upload]
        collection = ops[upload:cleanup]
        self.assertIn("if: success()", preparation)
        self.assertIn("if: success()", collection)
        self.assertIn("if-no-files-found: error", collection)
        self.assertIn("name: verified-recovery-tooling", collection)
        paths = collection.split("path: |\n", 1)[1].split("if-no-files-found:", 1)[0]
        self.assertEqual(
            [line.strip() for line in paths.splitlines() if line.strip()],
            [
                "${{ runner.temp }}/birja-verified-recovery/recovery.tar.gz",
                "${{ runner.temp }}/birja-verified-recovery/recovery.tar.gz.sha256",
            ],
        )
        script = textwrap.dedent(preparation.split("run: |\n", 1)[1])
        canonical = "/tmp/birja-phase14-proof"
        self.assertIn(canonical + "/recovery.tar.gz", script)
        payload = b"public recovery tooling fixture\n"
        for case in ("matching", "modified", "missing"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source, runner, tools = root / "source", root / "runner", root / "bin"
                for folder in (source, runner, tools):
                    folder.mkdir()
                if case != "missing":
                    (source / "recovery.tar.gz").write_bytes(
                        payload + (b"modified" if case == "modified" else b"")
                    )
                (source / "recovery.tar.gz.sha256").write_text(
                    hashlib.sha256(payload).hexdigest() + "\n"
                )
                # The real snippet operates only on owned test files here.
                sudo = tools / "sudo"
                sudo.write_text('#!/bin/sh\nexec "$@"\n')
                sudo.chmod(0o700)
                result = subprocess.run(
                    ["bash", "-c", script.replace(canonical, str(source))],
                    env={"PATH": str(tools) + ":/usr/bin:/bin", "RUNNER_TEMP": str(runner)},
                    capture_output=True,
                    check=False,
                    timeout=10,
                )
                if case == "matching":
                    self.assertEqual(result.returncode, 0, result.stderr.decode())
                    self.assertEqual(
                        (runner / "birja-verified-recovery/recovery.tar.gz").read_bytes(),
                        payload,
                    )
                else:
                    self.assertNotEqual(result.returncode, 0)

    def test_ops_runs_real_serial_producers_with_verified_tool(self):
        ops = jobs().get("ops", "")
        rollback = (ROOT / "deploy/tests/test-rollback-db-security.sh").read_text()
        self.assertIn("selected.integration(args.recovery_bundle)", rollback)
        selected_policy(rollback)
        self.assertIn("sudo -- python3 deploy/tests/test-deploy-prerequisites.py", ops)
        self.assertIn("sudo -- python3 deploy/tests/test-datastore-bindings.py", ops)
        self.assertRegex(
            ops, r"(?m)^          sudo -- bash deploy/check-nginx-config\.sh$"
        )
        self.assertIn("run: sudo -- python3 deploy/tests/run-portfolio-validation.py --suite recovery", ops)
        recovery_policy(ops)
        self.assertNotIn("sudo -- bash deploy/tests/test-db-config.sh", ops)
        for forbidden in ["sudo -E", "safe.directory=*", "git config --global"]:
            self.assertNotIn(forbidden, ops)
        self.assertIn("timeout-minutes: 45", ops)
        self.assertNotIn("secrets.", ops)
        self.assertIn("fetch-depth: 0", ops)
        self.assertIn("CF8F18F2844575973F79D4E191A6868BD3F7A907", ops)
        self.assertIn("VALIDSIG", ops)
        self.assertIn(
            "f415415624dcc452f2a02b8c33641791a8c6d6d3b65bbb3543fcf9a25151585c", ops
        )
        self.assertIn(
            "20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639", ops
        )
        self.assertIn("birja-backend-test:phase05-07", ops)
        for producer in [
            "test-backup.sh",
            "test-restore-safety.sh",
            "test-db-config.sh",
            "test-deploy-prerequisites.py",
            "test-reexec.sh",
            "test-rollback-target.sh",
            "test-app-services.sh",
            "test-smoke-ports.sh",
            "test-smoke-trading.sh",
        ]:
            self.assertIn(producer, ops)
        self.assertLess(
            ops.index("- name: Ordinary dev financial authority"),
            ops.index("--suite recovery"),
        )
        cleanup = ops.split("- name: Clean fixed synthetic projects")[-1]
        self.assertIn("if: always()", cleanup)
        self.assertIn("--env-file /dev/null", cleanup)
        self.assertIn('"$GITHUB_WORKSPACE/docker-compose.ops-test.yml"', cleanup)
        self.assertNotIn("birja-prod", cleanup)

    def test_existing_browser_coverage_audits_are_preserved(self):
        j = jobs()
        for text in [
            "--cov-fail-under=80",
            "--fail-under=100",
            "uv run pip-audit",
            "app/services/trading.py",
            "app/services/portfolio.py",
            "app/api/v1/history.py",
        ]:
            self.assertIn(text, j["backend"])
        for text in [
            "npm run test -- --coverage",
            "node ../deploy/audit-frontend.mjs",
            "npm run lint",
            "npm run typecheck",
        ]:
            self.assertIn(text, j["frontend"])
        self.assertIn("PRICE_SOURCE=fake", j["e2e"])
        self.assertIn("EMAIL_BACKEND=console", j["e2e"])
        self.assertRegex(j["e2e"], r"(?m)^        run: python3 deploy/tests/run-stock-browser.py$")
        browser = (ROOT / "deploy/tests/run-stock-browser.py").read_text()
        for token in ('"frontend/node_modules/.bin/playwright"', '"test"', '"--workers=1"', '"--retries=0"', 'default="all"', 'COMPOSE_DISABLE_ENV_FILE'):
            self.assertIn(token, browser)
        self.assertIn('default="all"', browser)
        self.assertIn('len(args.grep) > 256', browser)
        self.assertRegex(j["e2e"], r"(?m)^        run: python3 deploy/tests/run-stock-browser.py$")
        self.assertIn("target: test-builder", j["image"])
        self.assertIn("target: runtime", j["image"])
        self.assertIn("pytest tests/test_smoke.py -q", j["image"])


class PortfolioValidation(unittest.TestCase):
    def runner(self):
        spec = importlib.util.spec_from_file_location("validation", ROOT / "deploy/tests/run-portfolio-validation.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_actual_dry_run_binds_exact_ci_coverage_and_commands(self):
        runner = self.runner()
        result = subprocess.check_output([sys.executable, str(ROOT / "deploy/tests/run-portfolio-validation.py"),
                                          "--suite", "all-security", "--dry-run"])
        commands = json.loads(result)
        self.assertEqual(commands, [[directory, argv] for directory, argv in runner.security_commands()])
        ci = jobs()
        backend = [argv for directory, argv in commands if directory == "backend"]
        frontend = [argv for directory, argv in commands if directory == "frontend"]
        self.assertEqual(backend[:4], [
            ["uv", "run", "ruff", "check", "."], ["uv", "run", "ruff", "format", "--check", "."],
            ["uv", "run", "mypy", "app"], ["uv", "run", "pytest", "--cov=app", "--cov-branch", "--cov-fail-under=80"]])
        import shlex
        for argv in backend:
            self.assertIn("run: " + shlex.join(argv), ci["backend"])
        self.assertEqual(frontend, [shlex.split(c) for c in (
            "npm run lint", "npm run typecheck", "npx prettier --check .", "npm run test -- --coverage",
            "npm run build", "node --test ../deploy/tests/test-frontend-audit.mjs",
            "node ../deploy/audit-frontend.mjs")])
        for argv in frontend:
            self.assertIn("run: " + shlex.join(argv), ci["frontend"])
        self.assertEqual(commands[13], [".", ["python3", "deploy/tests/run-stock-browser.py"]])
        self.assertEqual([argv[argv.index("--target") + 1] for _, argv in commands if argv[:2] == ["docker", "build"]],
                         ["test-builder", "runtime", "toolchain", "test-builder"])
        scan = commands[-1][1]
        self.assertEqual(scan[0:4], ["python3", "deploy/scan-images.py", "--output", "image-reports"])
        self.assertEqual(scan[4::2], ["--runtime", "--builder", "--postgres", "--redis", "--node"])
        self.assertEqual(len(backend[4][4].split(",")), 64)
        recovery = json.loads(subprocess.check_output([sys.executable, str(ROOT / "deploy/tests/run-portfolio-validation.py"),
            "--suite", "recovery", "--dry-run"]))
        self.assertEqual(recovery, {"phase": 14, "suite": "recovery", "archive": "/tmp/birja-phase14-proof/recovery.tar.gz", "stages": list(runner.STAGES)})

    def test_security_failures_propagate_and_owned_stack_always_cleans(self):
        runner = self.runner()
        commands = runner.security_commands()
        expected = [runner.STACK + ["ps", "-q"], runner.STACK + ["up", "-d", "--wait"],
                    *[argv for _, argv in commands]]
        for failed in range(2, len(expected)):
            calls = []
            def run(argv, **kwargs):
                self.assertTrue(kwargs["check"])
                self.assertEqual(kwargs["env"]["PRICE_SOURCE"], "fake")
                self.assertNotIn("ALPACA_API_KEY", kwargs["env"])
                calls.append(argv)
                if argv == expected[failed]:
                    raise subprocess.CalledProcessError(1, argv)
                return SimpleNamespace(stdout=b"sha256:" + b"a" * 64 if "inspect" in argv else b"")
            # The scan argv is resolved to immutable IDs, so fail its real form.
            if failed == len(expected) - 1:
                expected[failed] = commands[-1][1].copy()
                for flag in ("--runtime", "--builder", "--node"):
                    expected[failed][expected[failed].index(flag) + 1] = "sha256:" + "a" * 64
            # This finite command-failure matrix tests orchestration, not a
            # repeated multi-megabyte filesystem hash for every mocked command.
            # Real source mutation is checked independently below and in the
            # validation contracts; production source guards stay unchanged.
            with patch.object(runner, "security_sources", return_value={"fixed": "a"}), \
                 self.assertRaises(subprocess.CalledProcessError):
                runner.execute_security(run=run)
            self.assertEqual(calls[-1], runner.STACK + ["down", "-v"])
        calls = []
        def preexisting(argv, **kwargs):
            calls.append(argv)
            return SimpleNamespace(stdout=b"someone-elses-container")
        # Keep this mocked orchestration case independent of checkout layout.
        # Real source-inventory behavior is covered by the separate guard tests.
        with patch.object(runner, "security_sources", return_value={"fixed": "a"}), \
             self.assertRaises(ValueError):
            runner.execute_security(run=preexisting)
        self.assertEqual(calls, [runner.STACK + ["ps", "-q"]])

    def test_recovery_order_guards_and_every_failure_propagates(self):
        runner = self.runner()
        for failed in (None, *runner.STAGES):
            events = []
            def operation(name):
                def call():
                    events.append(name)
                    if name == failed:
                        raise RuntimeError(name)
                    return ["a"*64,"b"*64,"c"*64] if (name.startswith("tls-") or name == "current0023-cold") else None
                return call
            def guard():
                events.append("authenticate")
            ops = {name: operation(name) for name in runner.STAGES}
            if failed:
                with self.assertRaisesRegex(RuntimeError, failed):
                    runner.execute_stages(ops, guard)
            else:
                runner.execute_stages(ops, guard)
            count = runner.STAGES.index(failed) + 1 if failed else len(runner.STAGES)
            wanted = ["authenticate"]
            for name in runner.STAGES[:count]:
                wanted.append(name)
                wanted.append("authenticate")
            self.assertEqual(events, wanted)
        with self.assertRaisesRegex(ValueError, "authority differs"):
            runner.execute_stages({name: (lambda name=name: name) for name in runner.STAGES}, lambda: None)

    def test_source_drift_stops_before_next_stage(self):
        runner = self.runner()
        events = []
        def guard():
            if events:
                raise ValueError("source/archive/image drift")
        with self.assertRaisesRegex(ValueError, "drift"):
            runner.execute_stages({name: (lambda name=name: events.append(name)) for name in runner.STAGES}, guard)
        self.assertEqual(events, [runner.STAGES[0]])

    def test_actual_authentication_rejects_archive_source_payload_and_image_mutations(self):
        import hashlib
        import io
        import tarfile
        runner = self.runner()
        sources = CI().portfolio_sources()
        r = runner.load("portfolio-smoke").load_recovery()
        with tempfile.TemporaryDirectory(prefix="birja-backup-test-auth-") as directory:
            root = Path(directory)
            root.chmod(0o700)
            (root / "current.py").write_bytes(b"current-app")
            archive = root / "recovery.tar"
            inspect = [{"Id": "sha256:" + "a" * 64, "Config": {"Labels": {"org.opencontainers.image.revision": "b" * 40}},
                        "RootFS": {"Type": "layers", "Layers": ["sha256:" + "c" * 64]}}]
            binding = sources.image_binding(inspect, source_commit="b" * 40, app_tree="d" * 40, context_sha256="e" * 64)
            (root / "current0023-image-binding.json").write_text(json.dumps(binding))
            (root / "current0023-image-binding.json").chmod(0o400)
            for mutation in (None, "outer", "source", "packaged", "retained", "inventory", "image"):
                (root / "current.py").write_bytes(b"current-app")
                content = {"current.py": b"changed" if mutation == "packaged" else b"current-app",
                           "sources/retained.tar": b"changed" if mutation == "retained" else b"fixed-retained",
                           "INVENTORY.json": json.dumps({"portfolio_payload": {"version": 3 if mutation == "inventory" else 4, "revision": "0024"}, "recovery_profile": "deploy-recovery-v5"}).encode()}
                with tarfile.open(archive, "w") as tar:
                    for name, data in content.items():
                        info = tarfile.TarInfo(name)
                        info.size = len(data)
                        tar.addfile(info, io.BytesIO(data))
                archive.chmod(0o600)
                expected = r.digest(archive)
                source = {"current.py": r.digest(root / "current.py")}
                if mutation == "outer":
                    expected = "0" * 64
                if mutation == "source":
                    (root / "current.py").write_bytes(b"changed")
                actual_image = inspect if mutation != "image" else [{**inspect[0], "RootFS": {"Type": "layers", "Layers": []}}]
                fake_r = SimpleNamespace(CORE=["current.py"], UNITS=[], PORTFOLIO_PAYLOAD_V4=[],
                    RETAINED_CLOSURE_SOURCE_PAYLOADS={"sources/retained.tar": hashlib.sha256(b"fixed-retained").hexdigest()},
                    digest=r.digest, sha_bytes=r.sha_bytes, private=r.private, call=lambda argv: json.dumps(actual_image))
                ops = SimpleNamespace(r=fake_r, portfolio_sources=lambda: sources)
                with patch.object(runner, "ROOT", root), patch.object(sources, "validate_matrix"):
                    if mutation:
                        with self.assertRaises(ValueError, msg=mutation):
                            runner.authenticate(ops, archive, expected, source)
                    else:
                        known = {}
                        runner.authenticate(ops, archive, expected, source, known)
                        record = root / "current0023-image-binding.json"
                        original = record.read_bytes()
                        record.chmod(0o600)
                        record.write_text(json.dumps({**binding, "context_sha256": "f" * 64}))
                        with self.assertRaisesRegex(ValueError, "disappeared/changed"):
                            runner.authenticate(ops, archive, expected, source, known)
                        record.unlink()
                        with self.assertRaisesRegex(ValueError, "disappeared/changed"):
                            runner.authenticate(ops, archive, expected, source, known)
                        record.write_bytes(original)
                        record.chmod(0o400)

    def test_synthetic_environment_discards_private_provider_and_compose_inputs(self):
        runner = self.runner()
        with patch.dict("os.environ", {"ALPACA_API_KEY": "private", "AWS_SECRET_ACCESS_KEY": "private",
             "DATABASE_URL": "production", "COMPOSE_FILE": "production", "DOCKER_HOST": "remote"}):
            env = runner.environment()
        for key in ("ALPACA_API_KEY", "AWS_SECRET_ACCESS_KEY", "COMPOSE_FILE", "DOCKER_HOST"):
            self.assertNotIn(key, env)
        self.assertIn("@127.0.0.1:55432/birja_test", env["DATABASE_URL"])
        self.assertEqual(env["COMPOSE_DISABLE_ENV_FILE"], "1")

    def test_successor_inventory_is_exact_and_legacy_absence_compatible(self):
        r = self.runner().load("portfolio-smoke").load_recovery()
        hashes = {name: r.digest(ROOT / name) for name in r.PORTFOLIO_PAYLOAD_V1}
        r.verify_portfolio_inventory({}, {})
        valid = {"portfolio_payload": {"version": 1, "sha256": hashes}}
        r.verify_portfolio_inventory(valid, hashes)
        import copy
        for mutate in (lambda x: x["portfolio_payload"].update(version=2),
                       lambda x: x["portfolio_payload"]["sha256"].pop(next(iter(hashes))),
                       lambda x: x["portfolio_payload"]["sha256"].update({"unexpected": "a" * 64}),
                       lambda x: x["portfolio_payload"]["sha256"].update({next(iter(hashes)): "a" * 64})):
            changed = copy.deepcopy(valid)
            mutate(changed)
            with self.assertRaises(ValueError):
                r.verify_portfolio_inventory(changed, hashes)
        with tempfile.TemporaryDirectory(prefix="birja-backup-test-path-") as directory:
            root = Path(directory)
            root.chmod(0o700)
            self.assertEqual(r.synthetic_path(root / "new", False), root / "new")
            root.chmod(0o755)
            with self.assertRaises(ValueError):
                r.synthetic_path(root / "new", False)
        for name in ("/tmp/birja-phase12-proof/other.tar", "/tmp/birja-phase12-proof-extra/recovery.tar.gz"):
            with self.assertRaises(ValueError):
                r.synthetic_path(name, False)

    def test_old_released_schema_inventory_and_current_successor_remain_distinct(self):
        r = self.runner().load("portfolio-smoke").load_recovery()
        hashes = {name: "a" * 64 for name in r.CONTRACT_PAYLOAD}
        legacy = ["0007", "0008", "0009", "0010", "0011", "0012", "0013", "0014"]
        old = {"schema_contract": {"revisions": legacy, "payload_sha256": hashes}}
        r.verify_contract_inventory(old, hashes)
        current = {"schema_contract": {"revisions": legacy + ["0017"], "payload_sha256": hashes},
                   "portfolio_payload": {"version": 1}}
        r.verify_contract_inventory(current, hashes)
        for changed in ({**old, "portfolio_payload": {"version": 1}},
                        {"schema_contract": {"revisions": legacy + ["0015"], "payload_sha256": hashes}},
                        {"schema_contract": {"revisions": legacy[:-1], "payload_sha256": hashes}}):
            with self.assertRaises(ValueError):
                r.verify_contract_inventory(changed, hashes)


class FixtureGitIsolation(unittest.TestCase):
    def test_generated_launcher_git_ignores_denied_host_config(self):
        spec = importlib.util.spec_from_file_location(
            "selected_cutover", ROOT / "deploy/tests/selected-cutover.py"
        )
        selected = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(selected)
        with (
            tempfile.TemporaryDirectory(prefix="birja-backup-test-git-") as tmp,
            tempfile.TemporaryDirectory(
                prefix="birja-backup-test-host-config-"
            ) as host,
        ):
            root = Path(tmp)
            app = root / "old/app"
            app.mkdir(parents=True)
            (root / "home").mkdir()
            (root / "tmp").mkdir()
            subprocess.run(["git", "init", "-q", str(app)], check=True)
            subprocess.run(
                ["git", "-C", str(app), "config", "fixture.marker", "local-only"],
                check=True,
            )
            denied = Path(host) / "gitconfig"
            denied.write_text("[fixture]\nmarker=host-only\n")
            result = selected.f.target(
                root,
                [
                    "env",
                    "GIT_CONFIG_SYSTEM=" + str(denied),
                    "git",
                    "-C",
                    str(app),
                    "rev-parse",
                    "--git-dir",
                ],
                ok=False,
            )
            self.assertIn(b"Permission denied", result.stderr)
            # Execute the actual generated launcher's clean environment block,
            # not a hand-built approximation. Production source is unchanged.
            source = (
                (ROOT / "deploy/deploy-entrypoint.sh")
                .read_text()
                .replace("/root", str(root / "home"))
            )
            generated = selected.isolate_entrypoint_environment(source, root)
            block = (
                "env = {"
                + generated.split("    env = {", 1)[1].split(
                    "\n    if 'DEPLOY_REF'", 1
                )[0]
            )
            script = (
                "import os, subprocess\nfrom pathlib import Path\nrelease=Path("
                + repr(str(root / "ops"))
                + ")\n"
                + textwrap.dedent(block)
                + "\nenv['GIT_CONFIG_SYSTEM']="
                + repr(str(denied))
                + "\nsubprocess.run(['/usr/bin/git','-C',"
                + repr(str(app))
                + ",'rev-parse','--git-dir'],env=env,check=True,stdout=subprocess.DEVNULL)"
                + "\nos.execve('/usr/bin/git',['git','-C',"
                + repr(str(app))
                + ",'config','fixture.marker'],env)"
            )
            result = selected.f.target(root, ["/usr/bin/python3", "-c", script])
            self.assertEqual(result.stdout.strip(), b"local-only")
            (app / ".git").rename(app / "hidden-git")
            result = selected.f.target(
                root, ["/usr/bin/python3", "-c", script], ok=False
            )
            self.assertIn(b"not a git repository", result.stderr)
            self.assertEqual(
                (ROOT / "deploy/deploy-entrypoint.sh")
                .read_text()
                .count("GIT_CONFIG_NOSYSTEM"),
                0,
            )


def load_tests(loader, tests, pattern):
    """Keep fresh-runner current-image regressions in the existing CI gate."""
    for filename in ("test-portfolio-smoke-image.py", "test-portfolio-validation-contracts.py",
                     "test-portfolio-browser-contracts.py"):
        path = Path(__file__).with_name(filename)
        spec = importlib.util.spec_from_file_location(filename.replace('-', '_'), path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tests.addTests(loader.loadTestsFromModule(module))
    return tests


if __name__ == "__main__":
    unittest.main()
