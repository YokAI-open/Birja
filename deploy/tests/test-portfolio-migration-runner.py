#!/usr/bin/env python3
"""Source-bound runner and pre-checkout refusal contracts; owned staged proof."""

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class RunnerContracts(unittest.TestCase):
    def backend(self, program):
        env = {k: os.environ[k] for k in ("PATH", "HOME", "LANG") if k in os.environ}
        env["PYTHONPATH"] = str(ROOT / "backend")
        return subprocess.run(
            [str(ROOT / "backend/.venv/bin/python"), "-c", program],
            env=env,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        )

    def test_source_identity_and_substitution_refusal(self):
        result = self.backend("""
import tempfile,shutil
from pathlib import Path
from app.db.portfolio_migrate import require_source
p=Path('backend').resolve()
require_source(p)
with tempfile.TemporaryDirectory(prefix='birja-runner-source-') as d:
 q=Path(d)
 shutil.copytree(p/'alembic',q/'alembic')
 (q/'alembic/versions/0017_portfolio_ownership.py').write_text('raise RuntimeError()')
 try:require_source(q)
 except ValueError:pass
 else:raise AssertionError('substituted source admitted')
""")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unsafe_runner_identity_refuses_before_connection(self):
        result = self.backend("""
import asyncio
from types import SimpleNamespace
from unittest.mock import patch
from app.db.portfolio_migrate import migrate
for env,url in [('prod','postgresql+asyncpg://birja:synthetic@postgres:5432/birja'),
 ('dev','postgresql+asyncpg://birja_migrator:synthetic@localhost:5432/birja'),
 ('test','postgresql+asyncpg://birja_migrator:synthetic@postgres:5432/birja')]:
 with patch('app.db.portfolio_migrate.create_async_engine',side_effect=AssertionError('connected')):
  try:asyncio.run(migrate(SimpleNamespace(env=env,database_url=url)))
  except ValueError:pass
  else:raise AssertionError('unsafe identity admitted')
""")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_target_admission_before_checkout(self):
        program = r"""
set -e
source deploy/deploy.sh
APP_DIR="$PWD"
ADMITTED_REVISION=0020
BIRJA_TESTED_SOURCE=$(git rev-parse HEAD)
# The retained deployment entrypoint must fail closed on successor state.
if admit_application_source "$BIRJA_TESTED_SOURCE"; then exit 47; fi
ADMITTED_REVISION=0014
if admit_application_source "$BIRJA_TESTED_SOURCE" portfolio-upgrade; then exit 48; fi
BIRJA_TESTED_SOURCE=c2c7af17e2cb225fe196c5dbf843a65022a69e37
admit_application_source "$BIRJA_TESTED_SOURCE"
ADMITTED_REVISION=0017
if admit_application_source bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb; then exit 42; fi
BIRJA_TESTED_SOURCE=c2c7af17e2cb225fe196c5dbf843a65022a69e37
if admit_application_source "$BIRJA_TESTED_SOURCE"; then exit 45; fi
ADMITTED_REVISION=0015
if admit_application_source "$BIRJA_TESTED_SOURCE"; then exit 43; fi
ADMITTED_REVISION=0016
if admit_application_source "$BIRJA_TESTED_SOURCE"; then exit 44; fi
"""
        result = subprocess.run(
            ["bash", "-c", program],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_authentic_retained_schema_consumer_refuses_successor_before_writes(self):
        result = self.backend("""
import asyncio,io,tarfile,types,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('sources',Path('deploy/tests/portfolio-sources.py'))
sources=importlib.util.module_from_spec(spec);spec.loader.exec_module(sources)
payload=sources.source_archive('portfolio0017')
with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
 code=archive.extractfile('backend/app/db/schema_contract.py').read()
retained=types.ModuleType('authentic_retained_schema');exec(compile(code,'<immutable0017-schema>','exec'),retained.__dict__)
class Read:
 def __init__(self,revision):self.revision=revision;self.calls=[]
 async def execute(self,query):
  self.calls.append(str(query));assert str(query)=='SELECT version_num FROM public.alembic_version';return self
 def scalars(self):return self
 def all(self):return [self.revision]
async def run():
 assert await retained.require_schema(Read('0017'))=='0017'
 for revision in ('0018','0019','0020','0021'):
  connection=Read(revision)
  try:await retained.require_schema(connection)
  except retained.SchemaAdmissionError:pass
  else:raise AssertionError('old runtime admitted successor')
  assert len(connection.calls)==1
asyncio.run(run())
""")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_ops_resume_has_explicit_gate_and_finalization_before_bootstrap(self):
        script = (ROOT / "deploy/configure-db.sh").read_text()
        self.assertIn('"--resume-portfolio-migration"', script)
        self.assertIn('"portfolio-migration-to-final"', script)
        self.assertLess(
            script.index('"app.db.portfolio_migrate"'), script.index("sql = prefix +")
        )
        self.assertIn('"--no-deps"', script)
        self.assertIn("birja_migrator", script)
        self.assertLess(
            script.index('["ps", "--status", "running", "--services"]'),
            script.index('"app.db.portfolio_migrate"'),
        )
        deploy = (ROOT / "deploy/deploy.sh").read_text()
        self.assertLess(
            deploy.index("dc stop $services"),
            deploy.index("--resume-portfolio-migration"),
        )

    def test_legacy_deploy_refuses_before_any_checkout_or_write(self):
        program = r"""
set -e
source deploy/deploy.sh
APP_DIR="$PWD"
ADMITTED_REVISION=0014
BIRJA_TESTED_SOURCE=c2c7af17e2cb225fe196c5dbf843a65022a69e37
BIRJA_DEPLOY_REEXEC=1
BIRJA_DEPLOY_SHA=$BIRJA_TESTED_SOURCE
checkout_source() { echo forbidden_checkout; return 42; }
install() { echo forbidden_write; return 43; }
if do_deploy; then exit 44; fi
"""
        result = subprocess.run(
            ["bash", "-c", program],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("forbidden_", result.stdout)
        self.assertIn("application_schema_incompatible=true", result.stderr)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RunnerContracts)
    if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
        raise SystemExit(1)
    if sys.argv[1:] == ["--postgres"]:
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "deploy/tests/test-portfolio-management-recovery.py"),
                "--postgres",
            ],
            check=True,
            cwd=ROOT,
            timeout=600,
        )
    elif sys.argv[1:]:
        raise SystemExit("supported optional mode: --postgres")
