import importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest import mock
HERE=Path(__file__).parent/'source-snapshot';sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE/'bridges'));spec=importlib.util.spec_from_file_location('r2host',HERE/'bridges/host.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
class PostLog(unittest.TestCase):
 def run_case(self,wall,mono,accept):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)/'job-1';root.mkdir();c=dict(environment='base',output=str(root/'child/execution'),job_id='1',shard=0);clock=types.SimpleNamespace(wall=0.,mono=0.);timer=types.SimpleNamespace(time=lambda:clock.wall,monotonic=lambda:clock.mono,sleep=lambda _:None);original=Path.open
   def opening(p,*a,**k):
    f=original(p,*a,**k)
    if p.name=='oracle.stderr':clock.wall=wall;clock.mono=mono
    return f
   child=mock.Mock(pid=123,returncode=0);child.poll.return_value=0
   with mock.patch.object(h,'time',timer),mock.patch.object(h.supervisor,'time',timer),mock.patch.object(h,'allocation',return_value=({},10000)),mock.patch.object(h,'check_source'),mock.patch.object(Path,'open',opening),mock.patch.object(h.supervisor.subprocess,'Popen',return_value=child) as spawn,mock.patch.object(h.supervisor,'group_signal',return_value=False),mock.patch.object(h.supervisor,'cleanup_group') as cleanup,mock.patch.object(h.supervisor.signal,'signal'):
    row,end,ref=h.execute_stage(c,'oracle','v1',root,10000,10000)
   self.assertEqual(row['normal_completion'],accept);self.assertEqual(row['deadline'],90.);self.assertEqual(row['monotonic_deadline'],90.);self.assertEqual(spawn.call_count,1 if accept else 0);cleanup.assert_not_called();self.assertTrue((root/'oracle-terminal.json').exists());self.assertEqual(ref['path'],str(root/'oracle-terminal.json'))
 def test_wall_expired_during_final_log_open_never_spawns(self):self.run_case(100.,0.,False)
 def test_monotonic_expired_during_final_log_open_never_spawns(self):self.run_case(0.,100.,False)
 def test_remaining_original_budget_is_preserved_after_logs(self):self.run_case(10.,10.,True)
if __name__=='__main__':unittest.main(verbosity=2)
