#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 - "$ROOT" <<'PY'
import os, pathlib, subprocess, sys, tempfile, unittest, importlib.util, json, tarfile, io, hashlib
from unittest import mock
sys.dont_write_bytecode=True
ROOT=pathlib.Path(sys.argv[1])
class Safety(unittest.TestCase):
 def test_successor_contract_inventory_is_exact_and_old_inventory_is_readable(self):
  spec=importlib.util.spec_from_file_location('restore',ROOT/'deploy/verify-restore.py'); r=importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
  expected={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in r.CONTRACT_PAYLOAD}
  r.verify_contract_inventory({},expected)
  record={'revisions':['0007','0008','0009','0010','0011','0012','0013','0014'],'payload_sha256':dict(expected)}
  r.verify_contract_inventory({'schema_contract':record},expected)
  with self.assertRaises(ValueError): r.verify_contract_inventory({'schema_contract':{**record,'revisions':record['revisions'][:-1]}},expected)
  record['payload_sha256']['deploy/backup-manifest.sql']='0'*64
  with self.assertRaises(ValueError): r.verify_contract_inventory({'schema_contract':record},expected)
  record['payload_sha256']=dict(expected); record['revisions'].append('9999')
  with self.assertRaises(ValueError): r.verify_contract_inventory({'schema_contract':record},expected)
 def test_unknown_or_omitted_stock_contract_cannot_verify_equal(self):
  spec=importlib.util.spec_from_file_location('restore',ROOT/'deploy/verify-restore.py'); r=importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
  core=['ck_accounts_cash_cents','ck_accounts_cash_non_negative','ck_holdings_quantity_non_negative','uq_holdings_user_coin','uq_trades_user_idempotency_key']
  for revision in ['9999','0010']:
   manifest={'revision':revision,'tables':{},'financial':{k:0 for k in ['negative_cash','fractional_cents','negative_holdings']},'schema':{'constraints':[['accounts',name,'c',True,'reviewed'] for name in core]}}
   def sql(dc,query,db=None):
    if 'contype=' in query: return b'8'
    if 'NOT indisvalid' in query: return b'0'
    return b't'
   with mock.patch.object(r,'canonical',return_value=manifest),mock.patch.object(r,'sql',side_effect=sql):
    with self.assertRaises((ValueError,KeyError)): r.verify([],manifest)
 def test_exact_quota_and_unit_inventory_before_runtime(self):
  spec=importlib.util.spec_from_file_location('restore',ROOT/'deploy/verify-restore.py'); r=importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
  self.assertIn('deploy/backup-quota.py',r.CORE)
  with tempfile.TemporaryDirectory(prefix='birja-backup-test-') as tmp:
   root=pathlib.Path(tmp); root.chmod(0o700)
   for missing in ['deploy/backup-quota.py',*r.UNITS,'extra.py']:
    names=set(r.CORE+r.UNITS+['tools/restic','images/postgres.tar','provenance/verified.json']+['provenance/'+n for n in r.PROVENANCE])
    if missing=='extra.py': names.add(missing)
    else: names.remove(missing)
    data={n:b'reviewed-test' for n in names}
    data['INVENTORY.json']=json.dumps({'files':sorted(names),'units':r.UNITS}).encode()
    data['SHA256SUMS']=''.join(hashlib.sha256(v).hexdigest()+'  '+n+'\n' for n,v in sorted(data.items())).encode()
    archive=root/'artifact.tar'
    with tarfile.open(archive,'w') as t:
     for n,v in sorted(data.items()):
      info=tarfile.TarInfo(n); info.size=len(v); info.mode=0o600; t.addfile(info,io.BytesIO(v))
    archive.chmod(0o600)
    with mock.patch.object(r,'runtime') as runtime, mock.patch.object(r,'call') as call:
     with self.assertRaises(ValueError): r.bundle_verify(archive,hashlib.sha256(archive.read_bytes()).hexdigest(),'deploy-recovery-v2')
     runtime.assert_not_called(); call.assert_not_called()
 def test_rejected_targets_have_no_calls(self):
  with tempfile.TemporaryDirectory(prefix='birja-backup-test-') as tmp:
   root=pathlib.Path(tmp); root.chmod(0o700)
   tool=root/'docker'; tool.write_text('#!/bin/sh\necho called >> "'+tmp+'/calls"\n'); tool.chmod(0o700)
   cases=[[],['--snapshot','latest'],['--snapshot','a'*64,'--project','birja-prod'],['--synthetic','/srv/birja/config','--snapshot','a'*64],['--synthetic',str(root/'missing'),'--snapshot','a'*64],['--snapshot','a'*64,'--database-url','postgres://prod'],['--snapshot','a'*64,'--role','postgres']]
   for args in cases:
    with self.subTest(args=args):
     r=subprocess.run(['bash',str(ROOT/'deploy/restore-check.sh'),*args],env={'PATH':tmp+':/usr/bin:/bin'},capture_output=True)
     self.assertNotEqual(r.returncode,0,r.stdout)
     self.assertFalse((root/'calls').exists())
 def test_source_safe(self):
  r=subprocess.run(['bash','-c','source "$1"','bash',str(ROOT/'deploy/restore-check.sh')],capture_output=True)
  self.assertEqual(r.returncode,0); self.assertEqual(r.stdout,b'')
 def test_bundle_rejects_before_install(self):
  for args in [[],['install'],['verify','/srv/birja/archive'],['install','--archive','/tmp/missing','--sha','a'*64],['package','--output','/srv/birja/archive'],['verify','--archive','/tmp/missing','--sha','bad']]:
   with self.subTest(args=args):
    r=subprocess.run(['bash',str(ROOT/'deploy/recovery-bundle.sh'),*args],capture_output=True)
    self.assertNotEqual(r.returncode,0)
unittest.main(argv=['safety'])
PY
