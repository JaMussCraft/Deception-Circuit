import importlib.util,json,sys,types,unittest
from pathlib import Path
from unittest import mock
HERE=Path(__file__).parent/'source-snapshot';sys.path.insert(0,str(HERE));import supervisor
spec=importlib.util.spec_from_file_location('r6host',HERE/'bridges/host.py');host=importlib.util.module_from_spec(spec);sys.path.insert(0,str(HERE/'bridges'));spec.loader.exec_module(host)
class Focused(unittest.TestCase):
 def test_expired_caller_deadline_renews_and_is_accepted(self):
  # Exact host.command freezes oracle bound90 before expensive receipt/log I/O.
  c=dict(environment='base',output='/tmp/job-1/execution',shard=0)
  argv,env=host.command(c,'oracle','v1',90)
  self.assertEqual(env['A3_STAGE_DEADLINE'],'90')
  timer=types.SimpleNamespace(time=lambda:100.,monotonic=lambda:100.,sleep=lambda _:None)
  child=mock.Mock(pid=123,returncode=0);child.poll.return_value=0
  with mock.patch.object(supervisor,'time',timer),mock.patch.object(supervisor.subprocess,'Popen',return_value=child) as spawn,mock.patch.object(supervisor,'group_signal',return_value=False),mock.patch.object(supervisor.signal,'signal'):
   row=supervisor.execute(argv,None,None,90,10000,lambda timeout=15:({},10000),env=env)
  self.assertEqual(spawn.call_count,1);self.assertTrue(row['normal_completion']);self.assertEqual(row['deadline'],190.);self.assertGreater(row['finished'],float(env['A3_STAGE_DEADLINE']))
 def test_final_fresh_query_can_expire_bound_but_still_spawns(self):
  clock=types.SimpleNamespace(now=0.);timer=types.SimpleNamespace(time=lambda:clock.now,monotonic=lambda:clock.now,sleep=lambda _:None);queries=[]
  def allocation(timeout=15):
   queries.append(timeout)
   if len(queries)==2:clock.now=100.
   return {},10000
  child=mock.Mock(pid=123,returncode=0);child.poll.return_value=0
  with mock.patch.object(supervisor,'time',timer),mock.patch.object(supervisor.subprocess,'Popen',return_value=child) as spawn,mock.patch.object(supervisor,'group_signal',return_value=False),mock.patch.object(supervisor,'cleanup_group'),mock.patch.object(supervisor.signal,'signal'):
   row=supervisor.execute(['never-real'],None,None,90,10000,allocation)
  self.assertEqual(spawn.call_count,1);self.assertFalse(row['normal_completion']);self.assertEqual(row['deadline'],90.)
 def test_container_rw_scope_includes_host_receipts(self):
  out=str(host.old.VIRT/host.PACKET_REL/'jobs/job-1/execution');c=dict(output=out,environment='mgnp',shard=0)
  argv,_=host.command(c,'suite','v1',4000)
  binds=[argv[i+1] for i,x in enumerate(argv) if x=='--bind'];rw=[x for x in binds if x.endswith(':rw')]
  self.assertEqual(len(rw),1);_,target,_=rw[0].split(':');self.assertEqual(target,str(Path(out).parent))
  for name in ('host-before.json','baseline-command.json','baseline-terminal.json'):
   self.assertTrue((Path(target)/name).is_relative_to(Path(target)))
 def test_inner_receipts_have_distinct_stage_names(self):
  spec=importlib.util.spec_from_file_location('r6inner',HERE/'bridges/inner.py');inner=importlib.util.module_from_spec(spec);spec.loader.exec_module(inner)
  import tempfile,os
  with tempfile.TemporaryDirectory() as td:
   for stage in ('baseline','oracle','suite'):
    with mock.patch.object(sys,'argv',['inner.py','v1',td,'never']),mock.patch.object(inner.os,'environ',dict(A3_STAGE_NAME=stage)),mock.patch.object(inner.Path,'read_text',return_value='1 0 0:1 / /sys/fs/cgroup ro - tmpfs cgroup ro'),mock.patch.object(inner.os,'statvfs',return_value=types.SimpleNamespace(f_flag=os.ST_RDONLY)),mock.patch.object(inner.os,'execvpe') as execute:
     inner.main();execute.assert_called_once()
   self.assertEqual(sorted(p.name for p in Path(td).iterdir()),['inner-mounts-baseline.json','inner-mounts-oracle.json','inner-mounts-suite.json'])
if __name__=='__main__':unittest.main(verbosity=2)
