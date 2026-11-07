import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PHYS = '/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment'
PIN = 'f12141b3b301d359dd7cf952ee47445b3bc637c31e9c4020c17da81cf268b26f'
REL = 'Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199'

class Dispatch(unittest.TestCase):
 def setUp(self):
  self.tmp = tempfile.mkdtemp(); self.base = Path(self.tmp) / 'physical'; self.rel = self.base / REL
  self.job = self.rel / 'root-genuine-proof-r2/job-123'; self.job.mkdir(parents=True)
  self.packet = self.rel / 'proof-adapter-r5'; self.packet.mkdir()
  (self.packet / 'manifest.json').write_bytes(b'fixture manifest')
  self.pin = hashlib.sha256(b'fixture manifest').hexdigest()
  self.capture = Path(self.tmp) / 'argv'
  (self.packet / 'launch.sh').write_text('#!/bin/bash\nprintf "%s\\n" "$@" > "$CAPTURE"\n')
  self.bind = self.job / 'bindings.json'; self.bind.write_bytes(b'fixture binding')
  self.digest = hashlib.sha256(b'fixture binding').hexdigest()
  self.side = self.job / 'bindings.sha256'; self.side.write_text(self.digest+'\n')
  script = (Path(__file__).parent / 'dispatch.sh').read_text().replace(PHYS, str(self.base)).replace(PIN, self.pin)
  self.spool = Path(self.tmp) / 'spooled.sh'; self.spool.write_text(script)
 def tearDown(self): shutil.rmtree(self.tmp)
 def run_dispatch(self, job='123'):
  env = dict(os.environ, SLURM_JOB_ID=job, CAPTURE=str(self.capture))
  return subprocess.run(['bash',str(self.spool)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
 def reject(self):
  self.assertNotEqual(self.run_dispatch().returncode, 0); self.assertFalse(self.capture.exists())
 def test_exact_spooled_argv(self):
  r=self.run_dispatch();self.assertEqual(r.returncode,0,r.stderr)
  self.assertEqual(self.capture.read_text().splitlines(),[str(self.job/'execution'), self.pin, str(self.bind), self.digest])
 def test_absent_leaves(self):
  for p in (self.bind,self.side):
   saved=p.read_bytes();p.unlink();self.reject();p.write_bytes(saved)
 def test_bad_jobid(self):
  for job in ('','123x','../123','123/4'):
   self.assertNotEqual(self.run_dispatch(job).returncode,0);self.assertFalse(self.capture.exists())
 def test_bad_and_split_hash(self):
  for content in ('0'*64+'\n', self.digest[:32]+'\n'+self.digest[32:]+'\n',self.digest+'\nextra\n', self.digest.upper()+'\n'):
   self.side.write_text(content);self.reject()
 def test_symlink_leaves_and_directory(self):
  for p in (self.bind,self.side):
   target=p.with_name(p.name+'.save');p.rename(target);p.symlink_to(target);self.reject();p.unlink();target.rename(p)
  saved=self.job.with_name('saved');self.job.rename(saved);self.job.symlink_to(saved,target_is_directory=True);self.reject()
 def test_partial_binding_and_empty_sidecar(self):
  self.bind.write_bytes(b'fixture');self.reject();self.bind.write_bytes(b'fixture binding')
  self.side.write_text('');self.reject()
 def test_symlink_ancestor(self):
  parent=self.job.parent; saved=parent.with_name('renamed-root');parent.rename(saved)
  parent.symlink_to(saved,target_is_directory=True);self.reject()
 def test_no_newline_sidecar(self):
  self.side.write_text(self.digest);self.assertEqual(self.run_dispatch().returncode,0)
 def test_wrong_packet(self):
  (self.packet/'manifest.json').write_text('different');self.reject()
if __name__=='__main__':unittest.main()
