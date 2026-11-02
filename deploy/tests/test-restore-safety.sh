#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 - "$ROOT" <<'PY'
import os, pathlib, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(sys.argv[1])
class Safety(unittest.TestCase):
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
