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
import json, os, signal, sys, time, importlib.util
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
   elif 'SELECT version_num' in line:
    print('9999' if fail=='unknown-schema' else '0008',flush=True)
   elif line.startswith('SELECT json_build_object'):
    tables={k:{'count':0,'sha256':'0'*64} for k in ['users','accounts','auth_sessions','refresh_tokens','coins','prices','holdings','trades','alembic_version']}
    financial={k:'0.00000000' for k in ['cash','starting_cash','quantity','cost_basis','fees','cash_delta']}
    financial.update({k:0 for k in ['negative_cash','fractional_cents','negative_holdings']})
    if fail=='manifest': financial['negative_cash']=1
    spec=importlib.util.spec_from_file_location('contract',(root/'contract-source').read_text()); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    identities=[[table,column,'a' if column=='id' else '', 'bigint' if column=='id' else 'text'] for table,columns in module.contract_columns('0008').items() for column in sorted(columns)]
    print(json.dumps({'tables':tables,'revision':'0008','server_version':'18.7','financial':financial,'schema':{'identities':identities,'indexes':[],'constraints':[]}}),flush=True)
   elif 'ROLLBACK' in line: break
  (root/'exporter').unlink(missing_ok=True)
 elif 'pg_dump' in a:
  if '--version' in a: print('pg_dump (PostgreSQL) '+(fail.removeprefix('dump-version:') if fail.startswith('dump-version:') else '18.7')); sys.exit(0)
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
 def test_native_http_budget_is_cumulative_at_transport(self):
  q=self.quota_module(); api=q.API(request_budget=2,download_budget=100000)
  response=mock.MagicMock(); response.status=200; response.__enter__.return_value=response
  def opened(*args,**kwargs):
   response.read1.side_effect=[b'{}',b'']; return response
  with mock.patch.object(api.opener,'open',side_effect=opened) as transport:
   for _ in range(2): self.assertEqual(api.call('https://api003.backblazeb2.com','b2_list_buckets',{},'synthetic'),{})
   with self.assertRaises(ValueError): api.call('https://api003.backblazeb2.com','b2_list_buckets',{},'synthetic')
   self.assertEqual(transport.call_count,2); self.assertEqual(api.calls,2)
   self.assertEqual(api.bytes,2*(8192+2))
  small=q.API(request_budget=1,download_budget=8192)
  with mock.patch.object(small.opener,'open') as transport:
   with self.assertRaises(ValueError): small.call('https://api003.backblazeb2.com','b2_list_buckets',{},'synthetic')
   transport.assert_not_called()
 def test_download_budget_changes_actual_command_rate_and_rejects_small(self):
  q=self.quota_module(); c=q.backup.load_config(['--synthetic',str(self.p/'config')])
  Path(c['state_dir']).mkdir(mode=0o700)
  job=q.backup.Job(c); job.quota(); first=job.download_rate
  c['quota']['download_remaining_bytes']//=2
  smaller=q.backup.Job(c); smaller.quota(); self.assertLess(smaller.download_rate,first)
  with mock.patch.object(smaller,'call',return_value=b'') as call:
   smaller.restic('snapshots'); self.assertEqual(call.call_args.args[0][call.call_args.args[0].index('--limit-download')+1],str(smaller.download_rate))
  c['quota']['download_remaining_bytes']=1000000
  with mock.patch.object(job,'call') as call:
   with self.assertRaises(ValueError): q.backup.Job(c).restic('snapshots')
   call.assert_not_called()
  c['quota']['download_remaining_bytes']=10000000
  api=q.API(download_budget=10000000); c['_inventory_api']=api; api.bytes=9000000
  with self.assertRaises(ValueError): q.backup.Job(c).quota()
 def quota_module(self):
  spec=importlib.util.spec_from_file_location('quota',ROOT/'deploy'/'backup-quota.py')
  q=importlib.util.module_from_spec(spec); spec.loader.exec_module(q); return q
 def test_native_inventory_includes_all_versions_parts_and_other_buckets(self):
  q=self.quota_module()
  for name in ['inventory-id','inventory-key','writer-id','writer-key']:
   (self.p/name).write_text(name); (self.p/name).chmod(0o600)
  a={'inventory_key_id_file':str(self.p/'inventory-id'),'inventory_key_file':str(self.p/'inventory-key')}
  target={'bucketId':'target','bucketName':'Birja-backup','bucketType':'allPrivate','fileLockConfiguration':{'isClientAuthorizedToRead':True,'value':{'isFileLockEnabled':False}},'lifecycleRules':[{'fileNamePrefix':'','daysFromHidingToDeleting':1}]}
  allowed={'buckets':None,'namePrefix':None,'capabilities':['listBuckets','listFiles','readBucketRetentions']}
  auth={'accountId':'account','authorizationToken':'synthetic-token','apiInfo':{'storageApi':{'apiUrl':'https://api003.backblazeb2.com','s3ApiUrl':q.ENDPOINT,'allowed':allowed}}}
  def file(name,fid,size,action='upload',bid='target'):
   return {'bucketId':bid,'accountId':'account','fileName':name,'fileId':fid,'contentLength':size,'action':action}
  calls=[]
  outside_partial=False
  class Fake:
   def call(s,base,op,body,token):
    calls.append((base,op,body))
    if op=='b2_authorize_account':
     import base64
     if 'writer-id' in base64.b64decode(token.split()[1]).decode():
      import copy
      writer=copy.deepcopy(auth); writer['apiInfo']['storageApi']['allowed']={'buckets':[{'id':'target','name':'Birja-backup'}],'namePrefix':'prod/','capabilities':['writeFiles']}; return writer
     return auth
    if op=='b2_list_buckets': return {'buckets':[target,{'bucketId':'other','bucketName':'other'}]}
    if op=='b2_list_file_versions':
     if body['bucketId']=='other': return {'files':[file('outside','o',31,bid='other')],'nextFileName':None,'nextFileId':None}
     if 'startFileId' not in body: return {'files':[file('prod/a','new',7)],'nextFileName':'prod/a','nextFileId':'old'}
     return {'files':[file('prod/a','old',11),file('prod/b','hide',0,'hide'),file('prod/b','hidden',13),file('zzz','outside',17)],'nextFileName':None,'nextFileId':None}
    if op=='b2_list_unfinished_large_files': return {'files':[file('prod/partial','partial',0,'start')] if body['bucketId']=='target' else ([file('elsewhere','otherpartial',0,'start',bid='other')] if outside_partial else []),'nextFileId':None}
    if op=='b2_list_parts': return {'parts':[{'fileId':'partial','partNumber':1,'contentLength':19}],'nextPartNumber':None}
    raise AssertionError(op)
  expected={'visible_bytes':7,'hidden_bytes':24,'unfinished_bytes':19,'other_bytes':48}
  c={'access_key_file':str(self.p/'writer-id'),'secret_key_file':str(self.p/'writer-key')}
  self.assertEqual(q.inventory(c,a,Fake()),expected)
  self.assertTrue(any(c[1]=='b2_list_parts' for c in calls))
  # Backblaze's standard web-console Read Only key includes shareFiles.
  # It delegates downloads, not storage/account mutations; inventory never
  # invokes its download-authorization API.
  allowed['capabilities'].append('shareFiles')
  self.assertEqual(q.inventory(c,a,Fake()),expected)
  # Real HTTP adapter -> inventory -> refreshed quota -> actual Job admission.
  api=q.API(request_budget=1000,download_budget=10000000)
  response=mock.MagicMock(); response.status=200; response.__enter__.return_value=response
  def opened(request,**kwargs):
   op=request.full_url.rsplit('/',1)[1]
   result=Fake().call(request.full_url.split('/b2api/')[0],op,json.loads(request.data) if request.data else {},request.headers['Authorization'])
   response.read1.side_effect=[json.dumps(result).encode(),b'']; return response
  actual=q.backup.load_config(['--synthetic',str(self.p/'config')]); actual.update(c)
  actual.update(_synthetic=False,_inventory_api=api)
  controls={**a,'local_request_budget':1000,'local_download_budget_bytes':10000000}
  Path(actual['state_dir']).mkdir(mode=0o700)
  with mock.patch.object(api.opener,'open',side_effect=opened), mock.patch.object(q,'controls',return_value=controls):
   actual['quota']=q.refresh(actual); q.backup.Job(actual).quota()
   first=api.calls; self.assertGreater(first,0)
   actual['quota']=q.refresh(actual); q.backup.Job(actual).quota()
   self.assertEqual(api.calls,2*first)
   api.request_budget=api.calls
   with self.assertRaises(ValueError): q.refresh(actual)
  outside_partial=True
  with self.assertRaises(ValueError): q.inventory(c,a,Fake())
  outside_partial=False
  for capability in ['writeFiles','deleteFiles','writeBuckets','deleteBuckets','writeKeys','deleteKeys','writeBucketRetentions','bypassGovernance','shareOtherResources']:
   with self.subTest(capability=capability):
    allowed['capabilities'].append(capability)
    with self.assertRaises(ValueError): q.inventory(c,a,Fake())
    allowed['capabilities'].pop()
  for key,value in [('buckets',[{'id':'target'}]),('namePrefix','prod/')]:
   prior=allowed[key]; allowed[key]=value
   with self.assertRaises(ValueError): q.inventory({},a,Fake())
   allowed[key]=prior
  target['bucketType']='allPublic'
  with self.assertRaises(ValueError): q.inventory({},a,Fake())
  target['bucketType']='allPrivate'; target['lifecycleRules'][0]['daysFromUploadingToHiding']=1
  with self.assertRaises(ValueError): q.inventory({},a,Fake())
 def test_native_transport_rejects_redirect_endpoint_and_bounds(self):
  q=self.quota_module(); api=q.API()
  with mock.patch.object(api.opener,'open') as opened:
   for host in ['http://api003.backblazeb2.com','https://api003.backblazeb2.com.evil','https://evil','https://user@api003.backblazeb2.com']:
    with self.assertRaises(ValueError): api.call(host,'b2_list_buckets',{},'secret')
   for operation in ['b2_get_download_authorization','b2_create_key','b2_upload_file','b2_update_bucket','b2_delete_file_version']:
    with self.assertRaises(ValueError): api.call('https://api003.backblazeb2.com',operation,{},'secret')
   opened.assert_not_called()
   api.calls=q.MAX_CALLS
   with self.assertRaises(ValueError): api.call('https://api003.backblazeb2.com','b2_list_buckets',{},'secret')
   opened.assert_not_called()
  with self.assertRaises(ValueError): q.NoRedirect().redirect_request(None,None,302,'',{},'https://evil')
  api=q.API()
  response=mock.MagicMock(); response.status=200; response.read1.return_value=b'x'*65536
  response.__enter__.return_value=response
  with mock.patch.object(api.opener,'open',return_value=response):
   with self.assertRaises(ValueError): api.call('https://api003.backblazeb2.com','b2_list_buckets',{},'secret')
  self.assertLessEqual(response.read1.call_count,32)
  api=q.API(); api.started-=121
  with mock.patch.object(api.opener,'open') as opened:
   with self.assertRaises(ValueError): api.call('https://api003.backblazeb2.com','b2_list_buckets',{},'secret')
   opened.assert_not_called()
 def test_nightly_success_and_local_inventory_exhaustion(self):
  q=self.quota_module(); (self.p/'repository').mkdir()
  with mock.patch.dict(os.environ,self.env):
   self.assertEqual(q.main(['--synthetic',str(self.p/'config')]),0)
  prior=(self.p/'state'/'last-success.json').read_bytes()
  self.c['quota']['storage_limit_bytes']=1; self.save(); (self.p/'calls').unlink()
  with mock.patch.dict(os.environ,self.env), contextlib.redirect_stdout(io.StringIO()):
   self.assertNotEqual(q.main(['--synthetic',str(self.p/'config')]),0)
  self.assertEqual(self.calls(),[])
  self.assertEqual((self.p/'state'/'last-success.json').read_bytes(),prior)
  self.assertEqual(self.run_script('backup-status.sh').returncode,1)
 def test_setup_attestation_is_private_mature_and_separate(self):
  q=self.quota_module()
  for name in ['inventory-id','inventory-key']:
   (self.p/name).write_text('synthetic'); (self.p/name).chmod(0o600)
  a={'format':1,'verified_at':int(time.time())-601,'console_zero_caps':True,'daily_owner_checks':True,'exclusive_account_writes':True,'inventory_key_id_file':str(self.p/'inventory-id'),'inventory_key_file':str(self.p/'inventory-key'),'local_request_budget':1000,'local_download_budget_bytes':1000000}
  p=self.p/'backup-controls.json'; p.write_text(json.dumps(a)); p.chmod(0o600)
  c=q.backup.load_config(['--synthetic',str(self.p/'config')])
  self.assertEqual(q.controls(c),a)
  for key,value in [('verified_at',int(time.time())),('verified_at',0),('console_zero_caps',False),('exclusive_account_writes',False),('local_request_budget',0)]:
   p.write_text(json.dumps({**a,key:value}))
   with self.assertRaises(ValueError): q.controls(c)
  p.write_text(json.dumps(a)); p.chmod(0o644)
  with self.assertRaises(ValueError): q.controls(c)
 def test_nightly_preflight_failure_blocks_backup_and_status(self):
  spec=importlib.util.spec_from_file_location('quota',ROOT/'deploy'/'backup-quota.py')
  self.assertTrue(spec.origin and Path(spec.origin).is_file(),'Callable nightly preflight required')
  quota=importlib.util.module_from_spec(spec); spec.loader.exec_module(quota)
  with mock.patch.object(quota,'refresh',side_effect=ValueError('SECRET-provider')) as preflight, contextlib.redirect_stdout(io.StringIO()) as out:
   self.assertNotEqual(quota.main(['--synthetic',str(self.p/'config')]),0)
  preflight.assert_called_once()
  self.assertNotIn('SECRET',out.getvalue()); self.assertEqual(self.calls(),[])
  self.assertEqual(self.run_script('backup-status.sh').returncode,1)
  self.assertFalse((self.p/'state'/'last-success.json').exists())
 def test_nightly_policy_and_measured_inventory(self):
  service=(ROOT/'deploy/systemd/birja-backup.service').read_text()
  timer=(ROOT/'deploy/systemd/birja-backup.timer').read_text()
  self.assertIn('Type=oneshot',service); self.assertIn('ExecStart=/usr/local/sbin/birja-backup',service)
  self.assertNotIn('EnvironmentFile=',service); self.assertNotIn('RemainAfterExit=yes',service)
  self.assertIn('OnCalendar=*-*-* 03:00:00 UTC',timer)
  self.assertIn('RandomizedDelaySec=15m',timer); self.assertIn('Persistent=true',timer)
  spec=importlib.util.spec_from_file_location('quota',ROOT/'deploy'/'backup-quota.py')
  quota=importlib.util.module_from_spec(spec); spec.loader.exec_module(quota)
  (self.p/'repository').mkdir(); (self.p/'repository'/'actual').write_bytes(b'x'*37)
  c=quota.backup.load_config(['--synthetic',str(self.p/'config')])
  updated=quota.refresh(c)
  self.assertEqual(updated['visible_bytes'],37)
  self.assertGreaterEqual(updated['observed_at'],int(time.time())-1)
  self.assertEqual(self.run_script().returncode,0)
  p=self.p/'state'/'last-success.json'; d=json.loads(p.read_text())
  d['epoch']=int(time.time())-93601; p.write_text(json.dumps(d))
  self.assertEqual(self.run_script('backup-status.sh').returncode,1)
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
  (self.p/'contract-source').write_text(str(ROOT/'deploy/backup-snapshot.py'))
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
 def test_reviewed_dump_minors_allow_preupgrade_backup_and_reject_other_versions(self):
  for version in ['18.6','18.7','18.6 (Debian 18.6-1.pgdg13+1)']:
   with self.subTest(version=version):
    r=self.run_script(fail='dump-version:'+version)
    self.assertEqual(r.returncode,0,r.stdout)
  for version in ['18.5','18.70','19.0','18.6evil']:
   with self.subTest(version=version):
    (self.p/'calls').unlink(missing_ok=True)
    r=self.run_script(fail='dump-version:'+version)
    self.assertNotEqual(r.returncode,0)
    self.assertNotIn('backup',self.cmds())
 def test_failures_preserve_previous_success_and_redact(self):
  for failure in ['dump','empty','archive','manifest','unknown-schema','upload','partial','identity','contents','verify']:
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
  with (self.p/'operation.lock').open('w') as f:
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
 def test_retained_source_compose_and_private_pack_temp(self):
  source=self.p/'old'/'docker-compose.ops-test.yml'; source.parent.mkdir(mode=0o700)
  shutil.copyfile(ROOT/'docker-compose.ops-test.yml',source)
  self.c['source_compose']=str(source)
  self.assertEqual(self.run_script().returncode,0)
  calls=self.calls()
  self.assertTrue(any(str(source) in call and '/dev/null' in call for call in calls if call[0]=='docker'))
  (self.p/'calls').unlink(); source.write_text('hostile compose')
  self.assertEqual(self.run_script().returncode,2); self.assertEqual(self.calls(),[])
  self.c['source_compose']='/srv/birja/docker-compose.prod.yml'
  self.assertEqual(self.run_script().returncode,2); self.assertEqual(self.calls(),[])
  spec=importlib.util.spec_from_file_location('backup_snapshot',ROOT/'deploy'/'backup-snapshot.py')
  module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
  self.assertEqual(module.Job({**self.c,'_synthetic':True}).env['TMPDIR'],self.c['state_dir'])
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
  with (self.p/'operation.lock').open('w') as f:
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
