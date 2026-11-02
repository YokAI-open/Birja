#!/usr/bin/env bash
# Offline behavioral contracts. All executables/state are synthetic and private.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 - "$ROOT" "$@" <<'PY'
import fcntl
import json
import os
import hashlib
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
sys.dont_write_bytecode=True
from unittest import mock
import contextlib
import importlib.util
import io

ROOT = Path(sys.argv[1])
SID = 'a' * 64
OLD = 'b' * 64
MOCK = r'''#!/usr/bin/env python3
import json, os, signal, sys, time
from pathlib import Path
a=sys.argv[1:]; root=Path(os.environ['MOCK_ROOT']); fail=os.environ.get('FAIL','')
def stopped(*args):
 (root/'exporter').unlink(missing_ok=True); sys.exit(1)
signal.signal(signal.SIGTERM,stopped)
with (root/'calls').open('a') as f: f.write(json.dumps([Path(sys.argv[0]).name]+a)+'\n')
if Path(sys.argv[0]).name=='docker':
 if 'psql' in a:
  for line in sys.stdin:
   if 'pg_export_snapshot' in line:
    (root/'exporter').write_text('alive'); print('00000001-00000001-1',flush=True)
   elif line.startswith('SELECT json_build_object'):
    tables={k:{'count':0,'sha256':'0'*64} for k in ['users','accounts','auth_sessions','refresh_tokens','coins','prices','holdings','trades','alembic_version']}
    financial={k:'0.00000000' for k in ['cash','starting_cash','quantity','cost_basis','fees','cash_delta']}
    financial.update({k:0 for k in ['negative_cash','fractional_cents','negative_holdings']})
    if fail=='manifest': financial['negative_cash']=1
    print(json.dumps({'tables':tables,'revision':'0008','server_version':'18.6','financial':financial}),flush=True)
   elif 'ROLLBACK' in line: break
  (root/'exporter').unlink(missing_ok=True)
 elif 'pg_dump' in a:
  if '--version' in a: print('pg_dump (PostgreSQL) 18.6'); sys.exit(0)
  assert (root/'exporter').exists()
  assert '--snapshot=00000001-00000001-1' in a
  if fail=='dump': print('SECRET-dump',file=sys.stderr); sys.exit(3)
  if fail=='sleep': time.sleep(2)
  sys.stdout.buffer.write(b'' if fail=='empty' else b'PGDMPsynthetic-private-database')
 elif 'pg_restore' in a:
  data=sys.stdin.buffer.read()
  if fail=='archive' or not data.startswith(b'PGDMP'): sys.exit(2)
  print('; synthetic archive list')
 sys.exit(0)
cmd=next((x for x in a if x in ['version','backup','snapshots','ls','dump','check','forget','prune']),None)
sid='a'*64; old='b'*64
if cmd=='version': print('restic 0.19.1 compiled with go1.26.4 on linux/amd64')
elif cmd=='snapshots':
 paths=[str(root/'state'/'stage'/'backup')]
 rows=[{'id':old,'hostname':'birja-prod','tags':['birja-db-v1'],'paths':paths}]
 if (root/'stored-manifest.json').exists(): rows.append({'id':sid,'hostname':'birja-prod','tags':['birja-db-v1'],'paths':paths})
 if sid in a: rows=[{'id':('c'*64 if fail=='identity' else sid),'hostname':'birja-prod','tags':['birja-db-v1'],'paths':paths}]
 if fail=='foreign': rows[0]['tags']=['unrelated']
 print(json.dumps(rows))
elif cmd=='backup':
 if fail=='partial': (root/'orphan-incomplete-upload').write_text('synthetic partial ciphertext')
 if fail in ['upload','partial']: print('SECRET-upload',file=sys.stderr); sys.exit(3)
 for p in Path.cwd().iterdir():
  if p.is_file(): (root/('stored-'+p.name)).write_bytes(p.read_bytes())
 print(json.dumps({'message_type':'summary','snapshot_id':sid,'data_added':512,'data_added_packed':400}))
elif cmd=='ls':
 print(json.dumps({'struct_type':'snapshot','id':sid}))
 for name in ['database.dump','manifest.json','recovery.tar']:
  p=root/('stored-'+name)
  if p.exists(): print(json.dumps({'struct_type':'node','type':'file','path':'/'+name,'size':p.stat().st_size+(1 if fail=='contents' else 0)}))
elif cmd=='dump':
 sys.stdout.buffer.write((root/'stored-manifest.json').read_bytes())
elif cmd=='check':
 if fail=='verify': print('SECRET-check',file=sys.stderr); sys.exit(1)
elif cmd=='forget':
 assert sid not in a and old in a
elif cmd=='prune':
 if fail=='prune': sys.exit(1)
'''

class Backup(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='birja-backup-test-')
  self.p=Path(self.tmp.name); self.p.chmod(0o700)
  for name in ['docker','restic']:
   (self.p/name).write_text(MOCK); (self.p/name).chmod(0o700)
  (self.p/'password').write_text('synthetic-only'); (self.p/'password').chmod(0o600)
  (self.p/'recovery').mkdir(); (self.p/'recovery'/'config.txt').write_text('synthetic recovery'); (self.p/'recovery'/'config.txt').chmod(0o600)
  self.c={'source_project':'birja-ops-test','state_dir':str(self.p/'state'),
   'restic_binary':str(self.p/'restic'),'docker_binary':str(self.p/'docker'),
   'repository':str(self.p/'repository'),'password_file':str(self.p/'password'),
   'recovery_files':[str(self.p/'recovery'/'config.txt')], 'release':'1'*40,
   'db_user':'birja_test','db_name':'birja_test','max_stage_bytes':1000000,
   'timeout_seconds':10,'freshness_seconds':93600,
   'quota':{'observed_at':int(time.time()),'storage_limit_bytes':100000000,
    'visible_bytes':1000,'hidden_bytes':1000,'unfinished_bytes':1000,
    'other_bytes':1000,'upload_reserve_bytes':1000000,'repack_reserve_bytes':1000000,
    'download_remaining_bytes':10000000,'request_remaining':10000,
    'request_reserve':1000,'free_controls_verified':True,'dedicated_repository':True}}
  self.env={**os.environ,'MOCK_ROOT':str(self.p)}
  self.save()
 def tearDown(self): self.tmp.cleanup()
 def save(self):
  (self.p/'config').write_text(json.dumps(self.c)); (self.p/'config').chmod(0o600)
 def run_script(self,script='backup.sh',fail='',extra=(),pass_fds=()):
  self.save()
  return subprocess.run(['bash',str(ROOT/'deploy'/script),'--synthetic',str(self.p/'config'),*extra],env={**self.env,'FAIL':fail},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,pass_fds=pass_fds)
 def calls(self): return [json.loads(x) for x in (self.p/'calls').read_text().splitlines()] if (self.p/'calls').exists() else []
 def cmds(self): return [next((x for x in a if x in ['backup','snapshots','ls','dump','check','forget','prune']),a[0]) for a in self.calls()]
 def test_happy_path_exact_snapshot_before_scoped_rotation(self):
  r=self.run_script(); self.assertEqual(r.returncode,0,r.stdout)
  c=self.cmds(); self.assertLess(c.index('backup'),c.index('ls')); self.assertLess(c.index('check'),c.index('forget')); self.assertLess(c.index('forget'),c.index('prune'))
  self.assertEqual(self.run_script('backup-status.sh').returncode,0)
  self.assertEqual(json.loads((self.p/'state'/'last-success.json').read_text())['snapshot_id'],SID)
  self.assertFalse((self.p/'exporter').exists())
  self.assertFalse((self.p/'state'/'stage').exists())
 def test_failures_preserve_previous_success_and_redact(self):
  for failure in ['dump','empty','archive','manifest','upload','partial','identity','contents','verify']:
   with self.subTest(failure=failure):
    self.assertEqual(self.run_script().returncode,0)
    prior=(self.p/'state'/'last-success.json').read_bytes(); (self.p/'calls').unlink()
    r=self.run_script(fail=failure); self.assertNotEqual(r.returncode,0)
    self.assertNotIn(b'SECRET',r.stdout); self.assertNotIn('forget',self.cmds())
    self.assertEqual((self.p/'state'/'last-success.json').read_bytes(),prior)
    self.assertEqual(self.run_script('backup-status.sh').returncode,1)
    self.assertFalse((self.p/'exporter').exists())
 def test_prune_failure_is_failed_attempt(self):
  self.assertNotEqual(self.run_script(fail='prune').returncode,0)
  self.assertIn('forget',self.cmds()); self.assertEqual(self.run_script('backup-status.sh').returncode,1)
 def test_headroom_includes_hidden_unfinished_and_repack(self):
  for key in ['visible_bytes','hidden_bytes','unfinished_bytes','other_bytes','repack_reserve_bytes']:
   with self.subTest(key=key):
    self.c['quota'][key]=100000000
    self.assertNotEqual(self.run_script().returncode,0); self.assertNotIn('backup',self.cmds())
    self.c['quota'][key]=1000
 def test_quota_evidence_limits_and_stage_bound(self):
  for key,value in [('observed_at',0),('request_remaining',1),('download_remaining_bytes',0),('free_controls_verified',False),('dedicated_repository',False)]:
   with self.subTest(key=key):
    old=self.c['quota'][key]; self.c['quota'][key]=value
    self.assertNotEqual(self.run_script().returncode,0); self.c['quota'][key]=old
  self.c['max_stage_bytes']=1; self.assertNotEqual(self.run_script().returncode,0)
 def test_foreign_repository_refuses_prune_and_upload(self):
  self.assertNotEqual(self.run_script(fail='foreign').returncode,0); self.assertNotIn('backup',self.cmds())
 def test_missing_stale_future_failed_and_corrupt_status(self):
  self.assertEqual(self.run_script('backup-status.sh').returncode,1)
  self.assertEqual(self.run_script().returncode,0)
  p=self.p/'state'/'last-success.json'; d=json.loads(p.read_text())
  for stamp in [0,int(time.time())+100]:
   d['epoch']=stamp; p.write_text(json.dumps(d)); self.assertEqual(self.run_script('backup-status.sh').returncode,1)
  p.write_text('bad'); self.assertEqual(self.run_script('backup-status.sh').returncode,1)
 def test_invalid_config_and_shell_injection_not_executed(self):
  self.c['source_project']='birja-prod'; self.assertEqual(self.run_script().returncode,2); self.assertEqual(self.calls(),[])
  self.c['source_project']='birja-ops-test'; self.c['oops']='$(touch /tmp/unwanted)'
  self.assertEqual(self.run_script().returncode,2)
 def test_lock_contention_and_forged_descriptor(self):
  (self.p/'state').mkdir(mode=0o700)
  with (self.p/'state'/'operation.lock').open('w') as f:
   fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   self.assertNotEqual(self.run_script().returncode,0); self.assertEqual(self.calls(),[])
  self.env['BIRJA_BACKUP_LOCK_FD']='9'; self.assertNotEqual(self.run_script().returncode,0)
 def test_concurrent_runs_are_serialized(self):
  a=subprocess.Popen(['bash',str(ROOT/'deploy'/'backup.sh'),'--synthetic',str(self.p/'config')],env={**self.env,'FAIL':'sleep'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  try:
   for _ in range(100):
    if (self.p/'exporter').exists(): break
    time.sleep(0.02)
   self.assertNotEqual(self.run_script().returncode,0)
   self.assertEqual(a.wait(timeout=10),0)
  finally:
   if a.poll() is None: a.kill(); a.wait()
   a.stdout.close()
 def test_bounded_resource_arguments_and_requests(self):
  self.assertEqual(self.run_script().returncode,0)
  calls=self.calls(); self.assertLessEqual(len(calls),15)
  for a in calls:
   if a[0]=='restic' and 'version' not in a:
    self.assertIn('s3.retries=2',a); self.assertIn('s3.connections=2',a)
    self.assertNotIn('--read-data',a)
 def test_source_safe(self):
  for script in ['backup.sh','backup-status.sh']:
   r=subprocess.run(['bash','-c','source "$1"', '_',str(ROOT/'deploy'/script)],capture_output=True)
   self.assertEqual(r.returncode,0); self.assertEqual(r.stdout,b'')
 def test_cleanup_failure_does_not_publish_success(self):
  spec=importlib.util.spec_from_file_location('backup_snapshot',ROOT/'deploy'/'backup-snapshot.py')
  module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
  with mock.patch.dict(os.environ,self.env), mock.patch.object(module.shutil,'rmtree',side_effect=OSError('private cleanup error')), contextlib.redirect_stdout(io.StringIO()) as output:
   self.assertEqual(module.main(['backup','--synthetic',str(self.p/'config')]),1)
  self.assertNotIn('private cleanup error',output.getvalue())
  self.assertFalse(json.loads((self.p/'state'/'last-attempt.json').read_text())['cleanup_ok'])
  self.assertFalse((self.p/'state'/'last-success.json').exists())
 def test_inherited_descriptor_must_already_hold_exact_lock(self):
  (self.p/'state').mkdir(mode=0o700)
  with (self.p/'state'/'operation.lock').open('w') as f:
   self.env['BIRJA_BACKUP_LOCK_FD']=str(f.fileno())
   self.assertNotEqual(self.run_script(pass_fds=(f.fileno(),)).returncode,0)
   self.assertEqual(self.calls(),[])
   fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   self.assertEqual(self.run_script(pass_fds=(f.fileno(),)).returncode,0)
 def test_interrupted_export_cleanup_and_no_retry_storm(self):
  self.assertNotEqual(self.run_script(fail='upload').returncode,0)
  self.assertEqual(self.cmds().count('backup'),1)
  a=subprocess.Popen(['python3',str(ROOT/'deploy'/'backup-snapshot.py'),'backup','--synthetic',str(self.p/'config')],env={**self.env,'FAIL':'sleep'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  try:
   for _ in range(100):
    if (self.p/'exporter').exists(): break
    time.sleep(0.02)
   a.terminate(); out=a.communicate(timeout=10)[0]
   self.assertNotEqual(a.returncode,0); self.assertNotIn(b'SECRET',out)
   self.assertFalse((self.p/'state'/'stage').exists())
   self.assertFalse((self.p/'exporter').exists())
   self.assertEqual(self.run_script('backup-status.sh').returncode,1)
  finally:
   if a.poll() is None: a.kill(); a.wait()
   a.stdout.close()
 def test_actual_approved_restic_local_encryption_and_rotation(self):
  binary=Path('/tmp/birja-test-tools/restic-0.19.1/restic')
  self.assertTrue(binary.is_file(),'Approved local restic binary required; do not auto-install')
  self.assertEqual(hashlib.sha256(binary.read_bytes()).hexdigest(),'20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639')
  shutil.copyfile(binary,self.p/'restic'); (self.p/'restic').chmod(0o700)
  env={'PATH':'/usr/bin:/bin','HOME':str(self.p),'RESTIC_REPOSITORY':self.c['repository'],'RESTIC_PASSWORD_FILE':self.c['password_file']}
  init=subprocess.run([str(self.p/'restic'),'init'],env=env,capture_output=True)
  self.assertEqual(init.returncode,0)
  for _ in range(2):
   r=self.run_script()
   if r.returncode:
    info=subprocess.run([str(self.p/'restic'),'snapshots','--json'],env=env,capture_output=True)
    rows=json.loads(info.stdout)
    ls=subprocess.run([str(self.p/'restic'),'ls','--json',rows[-1]['id']],env=env,capture_output=True)
    details=[{k:v for k,v in json.loads(line).items() if k in ['path','size','type','struct_type']} for line in ls.stdout.splitlines()]
    self.fail(str((r.stdout,[(x['paths'],x['hostname'],x['tags']) for x in rows],details)))
  snapshots=subprocess.run([str(self.p/'restic'),'snapshots','--json'],env=env,capture_output=True)
  self.assertEqual(snapshots.returncode,0)
  self.assertEqual(len(json.loads(snapshots.stdout)),1)
  self.assertEqual(self.run_script('backup-status.sh').returncode,0)
  metrics=json.loads((self.p/'state'/'last-success.json').read_text())
  physical=sum(p.stat().st_size for p in (self.p/'repository').rglob('*') if p.is_file())
  print('synthetic-local-metrics '+json.dumps({k:metrics[k] for k in ['archive_bytes','elapsed_ms','cpu_milliseconds','peak_child_rss_kib','tool_invocations','data_added_packed']},sort_keys=True)+' repository_bytes='+str(physical)+' network_bytes=0 network_requests=0',flush=True)

unittest.main(argv=['backup-contract',*sys.argv[2:]],verbosity=2)
PY
