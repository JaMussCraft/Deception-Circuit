"""Tiny source-bound entry tests; no cgroup writes, native imports or model."""
import ast, copy, json, os, pathlib, runpy, sys, tempfile, types, unittest
from unittest import mock
P=pathlib.Path(__file__).resolve().parent
class ReadonlyEntryTests(unittest.TestCase):
 def helper(self):
  tree=ast.parse((P/'entry_guard.py').read_text());functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='observe_effective_readonly']
  self.assertEqual(len(functions),1,'EFFECTIVE_RO_ENTRY_MISSING')
  ns=dict(os=os,Path=pathlib.Path);exec(compile(ast.fix_missing_locations(ast.Module(body=functions,type_ignores=[])),str(P/'entry_guard.py'),'exec'),ns);return ns['observe_effective_readonly']
 def record(self,path):
  st=path.stat();return dict(controller='v1',membership='/slurm/uid_1/job_123/step_batch/task_0',path=str(path),frozen_worker_path=str(path),live_directory_stat=[st.st_dev,st.st_ino,st.st_mode],same_as_frozen_worker_path=True)
 def test_actual_selected_path_and_raw_flags_are_recorded(self):
  helper=self.helper()
  with tempfile.TemporaryDirectory() as td:
   p=pathlib.Path(td);inner=self.record(p)
   with mock.patch.object(os,'statvfs',return_value=types.SimpleNamespace(f_flag=os.ST_RDONLY|2)) as call:
    observation=helper(inner)
   self.assertEqual(call.call_args[0],(str(p),));self.assertEqual(observation['path'],str(p));self.assertEqual(observation['f_flag'],os.ST_RDONLY|2);self.assertTrue(observation['read_only'])
 def test_rw_missing_flag_and_oserror_cannot_imply_readonly(self):
  helper=self.helper()
  with tempfile.TemporaryDirectory() as td:
   inner=self.record(pathlib.Path(td))
   with mock.patch.object(os,'statvfs',return_value=types.SimpleNamespace(f_flag=0)):self.assertFalse(helper(inner)['read_only'])
   for outcome in [types.SimpleNamespace(),OSError('missing actual controller')]:
    with mock.patch.object(os,'statvfs',side_effect=outcome if isinstance(outcome,Exception) else None,return_value=outcome),self.assertRaises((OSError,AttributeError,AssertionError)):helper(inner)
 def test_replaced_selected_or_native_path_rejects(self):
  helper=self.helper()
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);p=root/'actual';p.mkdir();inner=self.record(p);other=root/'other';other.mkdir()
   mismatch=copy.deepcopy(inner);mismatch['path']=str(other)
   with self.assertRaises((OSError,AssertionError)):helper(mismatch)
   def replace(_):p.rename(root/'old');p.mkdir();return types.SimpleNamespace(f_flag=os.ST_RDONLY)
   with mock.patch.object(os,'statvfs',side_effect=replace),self.assertRaises((OSError,AssertionError)):helper(inner)
 def execute_entry(self,kind):
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td);native=out/'actual';native.mkdir();inner=self.record(native);writes={};events=[]
   g=types.SimpleNamespace(packet=lambda _:None,sha=lambda _:'4dfb62711dfe598041db9e836e8f1589dc05c54c3b649f007b625f8a1a34669e',current_catalogues=lambda:{},read=lambda _:dict(records=[inner]),write=lambda p,v:(writes.update({pathlib.Path(p).name:v}),events.append(pathlib.Path(p).name)))
   host=types.SimpleNamespace(observe_cgroup=lambda:dict(records=[inner]),select_cgroup=lambda value,job:value['records'][0])
   argv=['entry_guard.py','--output',str(out),'--manifest-sha256','a'*64,'--deadline-monotonic','999999999999']
   def flags(_):
    if kind=='missing':return types.SimpleNamespace()
    if kind=='replaced':native.rename(out/'old');native.mkdir()
    return types.SimpleNamespace(f_flag=0 if kind=='rw' else os.ST_RDONLY)
   def execute(*args):events.append('exec');raise SystemExit(0)
   with mock.patch.dict(sys.modules,dict(proof_guards=g,host_supervisor=host)),mock.patch.object(sys,'argv',argv),mock.patch.dict(os.environ,dict(SLURM_JOB_ID='123',A2_CPU_PACKET_SHA256='a'*64)),mock.patch.object(os,'statvfs',side_effect=flags),mock.patch.object(os,'execv',side_effect=execute):
    try:runpy.run_path(str(P/'entry_guard.py'),run_name='__main__')
    except (AssertionError,AttributeError,OSError,SystemExit):pass
   return events,writes
 def test_real_entry_allows_only_observed_readonly_before_permission_and_exec(self):
  self.helper()
  events,writes=self.execute_entry('ro');self.assertIn('exec',events);self.assertLess(events.index('container-cgroup-readonly.json'),events.index('container-cgroup-entry.json'));self.assertLess(events.index('container-cgroup-entry.json'),events.index('exec'));self.assertTrue(writes['container-cgroup-entry.json']['effective_readonly']['read_only'])
  for kind in ['rw','missing','replaced']:
   with self.subTest(kind=kind):
    events,writes=self.execute_entry(kind);self.assertNotIn('exec',events);self.assertNotIn('container-cgroup-entry.json',writes);self.assertIn('FAILED-container-entry.json',writes)
 def test_r5_binds_parent_then_explicit_memory_child_without_requiring_host_ro(self):
  import guards
  self.assertEqual(guards.cgroup_bind('v1'),'/sys/fs/cgroup:/sys/fs/cgroup:ro,/sys/fs/cgroup/memory:/sys/fs/cgroup/memory:ro')
  import host_supervisor as h
  record=dict(controller='v1',job_scoped=True,same_as_frozen_worker_path=True,values={'memory.max_usage_in_bytes':'0','memory.failcnt':'0','memory.oom_control':'0'},live_directory_stat=[1,2,3],read_only=False)
  self.assertEqual(h.select_cgroup(dict(job='123',required_194_counter_visible=True,records=[record]),'123'),record)
if __name__=='__main__':unittest.main(verbosity=2)
