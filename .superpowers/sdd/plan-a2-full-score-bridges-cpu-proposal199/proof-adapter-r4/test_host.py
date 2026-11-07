import importlib.util,json,os,pathlib,sys,tempfile,types,unittest
from unittest import mock
P=pathlib.Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('host_adapter_test',P/('host_before_adapter_r2.py' if os.environ.get('ADAPTER201_RED')=='1' else 'host_supervisor.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)
from cgroup_probe import collect
from guards import cgroup_bind,job_scoped

def facts():
 e=dict(SLURM_JOB_ID='123',SLURM_CLUSTER_NAME='bridges2',SLURM_CPUS_PER_TASK='26',CUDA_VISIBLE_DEVICES='')
 f=dict(JobId='123',JobState='RUNNING',UserId='fixture(321)',Account='cis260361p',QOS='rm',Partition='RM-shared',NumNodes='1',NumCPUs='26',NumTasks='1',Requeue='0',Restarts='0',TimeLimit='00:45:00',TRES='cpu=26,mem=48G,node=1',WorkDir='/physical/runtime',BatchHost='r123');f['CPUs/Task']='26';return f,e

def report():return dict(status='CHILD_NORMAL_POSTGUARDS_AWAIT_SUPERVISOR',complete=False,**h.LABELS)
class HostTests(unittest.TestCase):
 def test_actual_bridges_identity_not_delta(self):
  f,e=facts();h.validate_allocation(f,e,321,'r123','/physical/runtime')
  for group,key,value in [('f','Account','cis260382p'),('f','Partition','cpu'),('f','QOS','gpu'),('f','NumCPUs','4'),('f','UserId','fixture(999)'),('f','WorkDir','/virtual/runtime'),('f','TRES','cpu=26,mem=48G,gres/gpu=1'),('e','SLURM_CLUSTER_NAME','delta')]:
   ff,ee=f.copy(),e.copy();(ff if group=='f' else ee)[key]=value
   with self.assertRaises((ValueError,AssertionError)):h.validate_allocation(ff,ee,321,'r123','/physical/runtime')
 def test_real_v1_job_path_and_readonly_bind(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);leaf=root/'memory/slurm/uid_321/job_123/step_batch/task_0';leaf.mkdir(parents=True)
   for n in ('memory.usage_in_bytes','memory.max_usage_in_bytes','memory.failcnt','memory.oom_control'):(leaf/n).write_text('0')
   mi='21 1 0:22 / '+str(root/'memory')+' rw - cgroup cgroup rw,memory'
   value=collect('123','7:memory:/slurm/uid_321/job_123/step_batch/task_0',root,mi);self.assertTrue(value['required_194_counter_visible']);self.assertTrue(value['records'][0]['same_as_frozen_worker_path'])
   self.assertFalse(job_scoped('123','/slurm/job_1234/step_batch'));self.assertEqual(cgroup_bind('v1'),'/sys/fs/cgroup:/sys/fs/cgroup:ro,/sys/fs/cgroup/memory:/sys/fs/cgroup/memory:ro')
 def case_main(self,finish,end):
  clock=types.SimpleNamespace(now=0.);ft=types.SimpleNamespace(time=lambda:clock.now,monotonic=lambda:clock.now,sleep=lambda _:None);allocs=[]
  def alloc():
   value={'job':'123','end_epoch':2700. if not allocs else end};allocs.append(value);return value
  with tempfile.TemporaryDirectory() as td:
   phys=pathlib.Path(td);out=phys/h.REL/'proof-evidence/execution';out.parent.mkdir(parents=True)
   ns=types.SimpleNamespace(output=str(out),manifest_sha256='fixture',bindings='fixture',bindings_sha256='fixture')
   parser=types.SimpleNamespace(add_argument=lambda *a,**k:None,parse_args=lambda:ns)
   class Child:
    returncode=0
    def __init__(self,*args,**kw):(out/'CHILD-REPORT.json').write_text(json.dumps(report()));(out/'container-cgroup-entry.json').write_text('{}')
    def poll(self):clock.now=finish;return 0
   with mock.patch.object(h,'PHYS',phys),mock.patch.object(h,'time',ft),mock.patch.object(h,'allocation',alloc),mock.patch.object(h,'check_packet',lambda *a:None),mock.patch.object(h,'sha',lambda p:h.IMAGE_SHA),mock.patch.object(h,'container_command',lambda *a,**k:['FAKE_CPU_ONLY']),mock.patch.object(h.subprocess,'Popen',Child),mock.patch.object(h.signal,'signal',lambda *a:None),mock.patch.object(h.argparse,'ArgumentParser',lambda:parser),mock.patch.object(h,'load_bindings',lambda *a:dict(actual_job_id='123',output_physical=str(out)),create=True),mock.patch.object(h,'observe_cgroup',lambda:dict(job='123',records=[],read_errors={}),create=True),mock.patch.object(h,'select_cgroup',lambda *a:dict(controller='v1'),create=True),mock.patch.object(h,'owned_output',lambda *a:out,create=True),mock.patch.object(h,'source_before_activation',lambda:dict(source_files=511),create=True),mock.patch.dict(os.environ,{'SLURM_JOB_ID':'123'},clear=False):
    with self.assertRaises((ValueError,AssertionError)):h.main()
   self.assertFalse((out/'COMPLETE-PROOF.json').exists())
   self.assertTrue((out/'child-execution.json').exists());self.assertFalse(json.loads((out/'child-execution.json').read_text())['timely'])
 def test_exact_cap_and_late_zero_reject(self):self.case_main(2400.,2700.);self.case_main(2401.,2700.)
 def test_post_reap_shortened_end_rejects(self):self.case_main(2390.,2500.)
 def test_container_cgroup_bind_is_not_omitted(self):
  with mock.patch.dict(os.environ,{},clear=True):
   try:cmd=h.container_command(h.PHYS/h.REL/'packet',h.PHYS/h.REL/'out','manifest',123,dict(controller='v1'))
   except TypeError:cmd=h.container_command(h.PHYS/h.REL/'packet',h.PHYS/h.REL/'out','manifest',123)
  self.assertIn(cgroup_bind('v1'),cmd);self.assertNotIn('--nv',cmd)
 def test_unbound_genuine_execution_rejects(self):
  path=P/'bindings.template.json'
  import hashlib
  with mock.patch.dict(os.environ,{'SLURM_JOB_ID':'123'},clear=False):
   with self.assertRaises((ValueError,AssertionError)):h.load_bindings(path,hashlib.sha256(path.read_bytes()).hexdigest())
 def test_absolute_wrapper_ignores_spool_directory(self):
  import subprocess
  with tempfile.TemporaryDirectory() as td:
   py=pathlib.Path(td)/'python';py.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n');py.chmod(0o700)
   r=subprocess.run(['bash',str(P/'launch.sh'),'OUT','SHA','BOUND','BSHA'],cwd=td,env=dict(os.environ,SLURM_JOB_ID='1',SLURM_CLUSTER_NAME='',ADAPTER201_TEST_PYTHON=str(py)),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
   self.assertEqual(r.returncode,0,r.stderr);self.assertIn('proof-adapter-r4/host_supervisor.py',r.stdout)
if __name__=='__main__':unittest.main(verbosity=2)
