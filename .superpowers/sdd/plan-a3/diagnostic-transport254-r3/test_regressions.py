"""Tiny independent reproductions; all non-fixture production actions are mocked."""
import json,os,signal,subprocess,sys,tempfile,time,types,unittest
from pathlib import Path
from unittest import mock
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import host,inner
class Independent(unittest.TestCase):
 def test_B1_known_effective_ro_stack_is_falsely_rejected(self):
  root=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/root-genuine-proof-r5-ops/actual-50316939')
  actual=json.loads((root/'container-cgroup-observation.json').read_text());ro=json.loads((root/'container-cgroup-readonly.json').read_text());self.assertTrue(ro['read_only']);lines=['1669 1 0:1 / /sys/fs/cgroup ro - tmpfs cgroup ro']+actual['memory_mount_lines'];self.assertTrue(ro['read_only'])
  with tempfile.TemporaryDirectory() as td,mock.patch.object(Path,'read_text',return_value='\n'.join(lines)),mock.patch.object(sys,'argv',['inner.py','v1',td,'never-exec']),mock.patch.object(inner.os,'statvfs',return_value=types.SimpleNamespace(f_flag=os.ST_RDONLY)),mock.patch.object(inner.os,'execvpe') as execute:
   inner.main()
   execute.assert_called_once()
 def test_effective_writable_mount_rejected(self):
  lines=['1 0 0:1 / /sys/fs/cgroup ro - tmpfs cgroup ro','2 1 0:2 / /sys/fs/cgroup/memory ro - cgroup memory ro']
  with tempfile.TemporaryDirectory() as td,mock.patch.object(Path,'read_text',return_value='\n'.join(lines)),mock.patch.object(sys,'argv',['inner.py','v1',td,'never']),mock.patch.object(inner.os,'statvfs',side_effect=lambda p:types.SimpleNamespace(f_flag=0 if p.endswith('/memory') else os.ST_RDONLY)),mock.patch.object(inner.os,'execvpe') as execute:
   with self.assertRaises(AssertionError):inner.main()
   execute.assert_not_called()
 def test_primary_and_cleanup_errors_both_recorded(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);child=mock.Mock(pid=5,returncode=None);child.poll.side_effect=ValueError('primary fixture')
   with mock.patch.object(host,'source_check'),mock.patch.object(host.old,'sha',return_value=host.old.IMAGE_SHA),mock.patch.object(host,'command',return_value=['fake']),mock.patch.object(host,'allocation',return_value=({},1500)),mock.patch.object(host.time,'time',return_value=0),mock.patch.object(host.subprocess,'Popen',return_value=child),mock.patch.object(host,'cleanup_group',side_effect=RuntimeError('cleanup fixture')) as cleanup:
    with self.assertRaises(RuntimeError):host.execute_phase({},dict(label='phase'),0,'v2',root,1500)
    report=json.loads((root/'phase-0.json').read_text());self.assertIn('primary fixture',report['error']);self.assertIn('cleanup fixture',report['cleanup_error']);cleanup.assert_called_once()
 def test_unrelated_writable_controller_is_allowed(self):
  lines=['1 0 0:1 / /sys/fs/cgroup ro - tmpfs cgroup ro','2 1 0:2 / /sys/fs/cgroup/memory ro - cgroup memory ro','3 1 0:3 / /sys/fs/cgroup/cpu rw - cgroup cpu rw']
  with tempfile.TemporaryDirectory() as td,mock.patch.object(Path,'read_text',return_value='\n'.join(lines)),mock.patch.object(sys,'argv',['inner.py','v1',td,'never']),mock.patch.object(inner.os,'statvfs',side_effect=lambda p:types.SimpleNamespace(f_flag=0 if p.endswith('/cpu') else os.ST_RDONLY)),mock.patch.object(inner.os,'execvpe') as execute:
   inner.main();execute.assert_called_once()
   with (Path(td)/'inner-mounts.json').open() as f:receipt=json.load(f)
   self.assertEqual(receipt['mountinfo'],lines);self.assertEqual(set(receipt['statvfs_flags']),{'/sys/fs/cgroup','/sys/fs/cgroup/memory'})
 def test_each_declared_target_writable_rejected(self):
  lines=['1 0 0:1 / /sys/fs/cgroup ro - tmpfs cgroup ro','2 1 0:2 / /sys/fs/cgroup/memory ro - cgroup memory ro']
  for kind,target in [('v1','/sys/fs/cgroup'),('v1','/sys/fs/cgroup/memory'),('v2','/sys/fs/cgroup')]:
   with self.subTest(kind=kind,target=target),tempfile.TemporaryDirectory() as td,mock.patch.object(Path,'read_text',return_value='\n'.join(lines)),mock.patch.object(sys,'argv',['inner.py',kind,td,'never']),mock.patch.object(inner.os,'statvfs',side_effect=lambda p:types.SimpleNamespace(f_flag=0 if p==target else os.ST_RDONLY)),mock.patch.object(inner.os,'execvpe') as execute:
    with self.assertRaises(AssertionError):inner.main()
    execute.assert_not_called()
 def phase(self,kind):
  clock=types.SimpleNamespace(now=0.);timer=types.SimpleNamespace(time=lambda:clock.now,monotonic=lambda:clock.now,sleep=lambda _:None);allocations=[1500,1500,1300] if kind=='post-reap-cut' else [1500,1500]
  def allocation(*a,**k):return {},allocations.pop(0) if len(allocations)>1 else allocations[0]
  class Child:
   returncode=0;pid=4321
   def poll(self):
    if kind=='post-reap-cut':clock.now=550
    return 0
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);real=Path.open
   def delayed(path,*args,**kwargs):
    out=real(path,*args,**kwargs)
    if kind=='delayed-open' and path.name=='pytest.stdout':clock.now=601
    return out
   with mock.patch.object(host,'source_check'),mock.patch.object(host.old,'sha',return_value=host.old.IMAGE_SHA),mock.patch.object(host,'command',return_value=['FAKE_NO_MODEL']),mock.patch.object(host,'allocation',allocation),mock.patch.object(host,'time',timer),mock.patch.object(host.subprocess,'Popen',return_value=Child()) as spawn,mock.patch.object(Path,'open',delayed),mock.patch.object(host,'cleanup_group',side_effect=RuntimeError('unreaped fixture') if kind=='cleanup-error' else None) as cleanup:
    try:host.execute_phase({},dict(label='six-failure-traces'),0,'v2',root,1500)
    except RuntimeError:
     self.assertEqual(kind,'cleanup-error')
    report=json.loads((root/'phase-0.json').read_text());return spawn.call_count,cleanup.call_count,report
 def test_B2_expired_after_log_open_still_launches(self):
  spawn,cleanup,report=self.phase('delayed-open');self.assertEqual(spawn,0);self.assertTrue(report['timed_out']);self.assertFalse(report['acceptance'])
 def test_B3_cleanup_error_restarts_cleanup_budget(self):
  spawn,cleanup,report=self.phase('cleanup-error');self.assertEqual(spawn,1);self.assertEqual(cleanup,1);self.assertIn('unreaped fixture',report['error'])
 def test_post_reap_shortened_end_is_correctly_clamped(self):
  spawn,cleanup,report=self.phase('post-reap-cut');self.assertEqual(spawn,1);self.assertEqual(cleanup,1);self.assertTrue(report['timed_out']);self.assertEqual(report['allocation_end_bound'],1300)
 def test_real_owned_group_is_reaped_after_leader_exit(self):
  host.enable_subreaper()
  with tempfile.TemporaryDirectory() as td:
   marker=Path(td)/'ready';code="import os,time;from pathlib import Path\np=os.fork()\nif p==0:\n Path("+repr(str(marker))+").write_text(str(os.getpid()))\n time.sleep(30)\nelse:\n while not Path("+repr(str(marker))+").exists():time.sleep(.01)\n os._exit(0)\n"
   child=subprocess.Popen([sys.executable,'-B','-c',code],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
   try:
    child.wait(timeout=5);self.assertTrue(host.old.group_exists(child.pid));host.cleanup_group(child);self.assertFalse(host.old.group_exists(child.pid))
   finally:
    host.old.group_signal(child.pid,signal.SIGKILL)
    stop=time.monotonic()+1
    while time.monotonic()<stop:
     try:p,_=os.waitpid(-child.pid,os.WNOHANG)
     except ChildProcessError:break
     if not p:time.sleep(.01)
if __name__=='__main__':unittest.main(verbosity=2)
