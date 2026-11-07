"""Pure dispatcher integration fixtures; no real root paths, jobs or model entry."""
import hashlib,importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
P=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/root-proof-dispatch220');PACKET=P.parent/'proof-adapter-r3';sys.path.insert(0,str(PACKET));import host_supervisor as h
spec=importlib.util.spec_from_file_location('dispatch_author_fixture',P/'test_dispatch.py');fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Review(unittest.TestCase):
 def test_exact_frozen_source_and_target_packet(self):
  self.assertEqual(sha(P/'dispatch.sh'),'8abf86b1295addd5cd8b41f13176199fb0fcf753cf6f1c40c044a073fa05e6aa');self.assertEqual(sha(P/'test_dispatch.py'),'47855038052b2ffc3f14365df70858fac1e1cd6493ee69c756dbca6d90076afe');self.assertEqual(sha(PACKET/'manifest.json'),'4e4b4bcf1ddcd6481fac1eccd966a2a1cbfa385b2bd16a9a00504cfaa05def3f')
  source=(P/'dispatch.sh').read_text();self.assertIn('root-genuine-proof-r2/job-$SLURM_JOB_ID',source);self.assertIn('MANIFEST_SHA='+sha(PACKET/'manifest.json'),source);self.assertNotIn('sbatch',source);self.assertNotIn('scontrol',source)
 def test_independent_sidecar_is_not_self_adopted_and_rejects_raw_junk(self):
  case=fixtures.Dispatch();case.setUp()
  try:
   original=case.side.read_bytes();case.bind.write_bytes(b'new binding whose hash was not sealed');self.assertNotEqual(case.run_dispatch().returncode,0);self.assertFalse(case.capture.exists());case.bind.write_bytes(b'fixture binding')
   for suffix in (b'\r\n',b'\x00',b'\n\n',b' ',b'\nignored'):
    case.side.write_bytes(case.digest.encode()+suffix);self.assertNotEqual(case.run_dispatch().returncode,0);self.assertFalse(case.capture.exists())
   case.side.write_bytes(original);self.assertEqual(case.run_dispatch().returncode,0);self.assertEqual(case.capture.read_text().splitlines()[-1],case.digest)
  finally:case.tearDown()
 def test_dispatch_output_matches_unchanged_owner_guard_and_job_binding_rejects(self):
  case=fixtures.Dispatch();case.setUp()
  try:
   out=case.job/'execution';binding=dict(output_physical=str(out));
   with mock.patch.object(h,'PHYS',case.base):
    self.assertEqual(h.owned_output(str(out),binding,os.getuid()),out);out.mkdir()
    with self.assertRaises(AssertionError):h.owned_output(str(out),binding,os.getuid())
   # The transport does not create authority: unchanged host still rejects a
   # correctly hashed binding carrying the wrong actual allocation identity.
   case.bind.write_text(json.dumps(dict(status='ROOT_BOUND_FOR_ONE_CPU_PROOF',actual_job_id='999')))
   with mock.patch.dict(os.environ,{'SLURM_JOB_ID':'123'}),self.assertRaises(AssertionError):h.load_bindings(case.bind,sha(case.bind))
  finally:case.tearDown()
if __name__=='__main__':unittest.main(verbosity=2)
