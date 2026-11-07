"""Independent diagnostic-only metadata and tiny path fixtures; no remote execution."""
import ast,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
P=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/preflight-r4');OLD=P.parent/'preflight-r3';sys.path.insert(0,str(P))
from guards import cgroup_bind,job_scoped
from cgroup_probe import collect
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Review(unittest.TestCase):
 def test_exact_manifest_and_only_scoped_delta(self):
  self.assertEqual(sha(P/'manifest.json'),'bf8beb34fe2db3d64a40c71a8fa85ec7de8305971073d602f4ff49ece7f39a81')
  m=json.loads((P/'manifest.json').read_text());self.assertEqual(len(m),8)
  for n,d in m.items():self.assertEqual(sha(P/n),d)
  for n in ('allocation_helper.py','cgroup_probe.py'):self.assertEqual(sha(P/n),sha(OLD/n))
  for n in ('host_probe.py','inner.sh','launch.sh','test_preflight.py'):
   actual=(P/n).read_text().replace('preflight-r4','preflight-r3').replace('root-cgroup199-r4','root-cgroup199-r3');self.assertEqual(actual,(OLD/n).read_text())
  self.assertEqual((P/'guards.py').read_text().replace("if kind=='v1':path='/sys/fs/cgroup'","if kind=='v1':path='/sys/fs/cgroup/memory'"),(OLD/'guards.py').read_text())
  self.assertEqual((P/'test_bind_failures.py').read_text().replace("('v1','/sys/fs/cgroup')","('v1','/sys/fs/cgroup/memory')"),(OLD/'test_bind_failures.py').read_text())
 def test_parent_selector_preserves_native_leaf_and_v2(self):
  self.assertEqual(cgroup_bind('v1'),'/sys/fs/cgroup:/sys/fs/cgroup:ro');self.assertEqual(cgroup_bind('v2'),'/sys/fs/cgroup:/sys/fs/cgroup:ro')
  with self.assertRaises(ValueError):cgroup_bind('fake')
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);leaf=root/'memory/slurm/uid_105853/job_50311480/step_batch/task_0';leaf.mkdir(parents=True)
   for n in ('memory.max_usage_in_bytes','memory.failcnt','memory.oom_control'):(leaf/n).write_text('0')
   mi='954 940 0:32 / '+str(root/'memory')+' ro,nosuid - cgroup cgroup rw,memory'
   v=collect('50311480','4:memory:/slurm/uid_105853/job_50311480/step_batch/task_0',root,mi);self.assertTrue(v['required_194_counter_visible']);r=v['records'][0];self.assertEqual(r['path'],str(leaf));self.assertEqual(r['path'],r['frozen_worker_path']);self.assertTrue(r['same_as_frozen_worker_path']);self.assertEqual(v['memory_mount_lines'],[mi])
   self.assertFalse(collect('5031148','4:memory:/slurm/uid_105853/job_50311480/step_batch/task_0',root,mi)['required_194_counter_visible'])
 def test_old_selector_fails_parent_destination_contract_semantically(self):
  spec=importlib.util.spec_from_file_location('old_guards',OLD/'guards.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
  self.assertEqual(old.cgroup_bind('v1'),'/sys/fs/cgroup/memory:/sys/fs/cgroup/memory:ro');self.assertNotEqual(old.cgroup_bind('v1'),cgroup_bind('v1'));self.assertEqual(old.cgroup_bind('v2'),cgroup_bind('v2'))
 def test_host_python36_syntax_and_apis(self):
  for n in ('host_probe.py','allocation_helper.py','cgroup_probe.py','guards.py'):
   text=(P/n).read_text();ast.parse(text,feature_version=(3,6))
   for banned in ('capture_output=','text=','fromisoformat(','.is_relative_to(','.removeprefix('):self.assertNotIn(banned,text)
if __name__=='__main__':unittest.main(verbosity=2)
