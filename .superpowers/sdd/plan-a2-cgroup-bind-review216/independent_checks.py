"""Independent r5 metadata and tiny path checks; actual mounts remain untested."""
import ast,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
P=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/preflight-r5');OLD=P.parent/'preflight-r4';sys.path.insert(0,str(P))
from guards import cgroup_bind
from cgroup_probe import collect
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Review(unittest.TestCase):
 def test_manifest_and_preserved_nonselector_code(self):
  self.assertEqual(sha(P/'manifest.json'),'889ee0c986fd392ba1cf00300d93ae46f6714cae10a58175862a3a9ba7a88db7');m=json.loads((P/'manifest.json').read_text());self.assertEqual(len(m),8)
  for n,d in m.items():self.assertEqual(sha(P/n),d)
  for n in ('allocation_helper.py','cgroup_probe.py'):self.assertEqual(sha(P/n),sha(OLD/n))
  for n in ('host_probe.py','inner.sh','launch.sh','test_preflight.py'):self.assertEqual((P/n).read_text().replace('preflight-r5','preflight-r4').replace('root-cgroup199-r5','root-cgroup199-r4'),(OLD/n).read_text())
  def without_selector(path):
   t=ast.parse(path.read_text());t.body=[n for n in t.body if not isinstance(n,ast.FunctionDef) or n.name!='cgroup_bind'];return ast.dump(t)
  self.assertEqual(without_selector(P/'guards.py'),without_selector(OLD/'guards.py'))
 def test_ordered_argument_native_leaf_and_v2(self):
  parent='/sys/fs/cgroup:/sys/fs/cgroup:ro';child='/sys/fs/cgroup/memory:/sys/fs/cgroup/memory:ro';self.assertEqual(cgroup_bind('v1').split(','),[parent,child]);self.assertEqual(cgroup_bind('v2'),parent)
  with self.assertRaises(ValueError):cgroup_bind('other')
  text=(P/'host_probe.py').read_text();self.assertIn("actual_cgroup_bind=cgroup_bind(valid[0]['controller'])",text);self.assertIn("'--bind',actual_cgroup_bind",text)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);leaf=root/'memory/slurm/job_123/step_batch';leaf.mkdir(parents=True)
   for n in ('memory.max_usage_in_bytes','memory.failcnt','memory.oom_control'):(leaf/n).write_text('0')
   mi='954 940 0:32 / '+str(root/'memory')+' ro,nosuid - cgroup cgroup rw,memory';v=collect('123','4:memory:/slurm/job_123/step_batch',root,mi);self.assertTrue(v['required_194_counter_visible']);self.assertEqual(v['records'][0]['path'],str(leaf));self.assertEqual(v['records'][0]['frozen_worker_path'],str(leaf));self.assertTrue(v['records'][0]['same_as_frozen_worker_path']);self.assertEqual(v['memory_mount_lines'],[mi]);self.assertFalse(collect('12','4:memory:/slurm/job_123/step_batch',root,mi)['required_194_counter_visible'])
 def test_new_regression_reproduces_old_missing_child_failure(self):
  old=module('old_guards',OLD/'guards.py');tests=module('new_bind_tests',P/'test_bind_failures.py');tests.cgroup_bind=old.cgroup_bind;suite=unittest.defaultTestLoader.loadTestsFromTestCase(tests.Binding);result=unittest.TestResult();suite.run(result)
  self.assertEqual(result.testsRun,3);self.assertEqual(len(result.failures),1);self.assertEqual(len(result.errors),0);self.assertIn('test_real_controller_bind_is_readonly_same_path',str(result.failures[0][0]));self.assertIn('/sys/fs/cgroup/memory',result.failures[0][1])
 def test_host_python36_grammar_and_apis(self):
  for n in ('host_probe.py','allocation_helper.py','cgroup_probe.py','guards.py'):
   text=(P/n).read_text();ast.parse(text,feature_version=(3,6))
   for banned in ('capture_output=','text=','fromisoformat(','.is_relative_to(','.removeprefix('):self.assertNotIn(banned,text)
 def test_actual_r4_readable_but_memory_mount_writable(self):
  root=P.parent/'root-preflight-ops-r4';receipt=json.loads((root/'fetch-50311765.json').read_text())
  for n,v in receipt['files'].items():path=root/'actual-50311765'/n;self.assertEqual(sha(path),v['sha256']);self.assertEqual(path.stat().st_size,v['bytes'])
  out=root/'actual-50311765/execution';result=json.loads((out/'probe-result.json').read_text());host=json.loads((out/'host-cgroup.json').read_text());inner=json.loads((out/'container-cgroup.json').read_text());self.assertEqual(result['host_exit'],0);self.assertEqual(result['container_exit'],0);self.assertTrue(inner['required_194_counter_visible']);self.assertEqual(host['job'],inner['job']);self.assertEqual(host['records'][0]['membership'],inner['records'][0]['membership']);self.assertTrue(inner['records'][0]['same_as_frozen_worker_path']);line=inner['memory_mount_lines'][0];self.assertIn('rw',line.split(' - ',1)[0].split()[5].split(','));self.assertNotIn('ro',line.split(' - ',1)[0].split()[5].split(','))
if __name__=='__main__':unittest.main(verbosity=2)
