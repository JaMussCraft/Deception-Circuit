import ast,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).parent/'source-snapshot'))
import host,inner
class Targeted(unittest.TestCase):
 def gate(self,kind,flags):
  lines=['1 0 0:1 / /sys/fs/cgroup ro - tmpfs cgroup ro','2 1 0:2 / /sys/fs/cgroup/memory ro - cgroup memory rw','3 1 0:3 / /sys/fs/cgroup/cpu,cpuacct rw - cgroup cpu rw']
  with tempfile.TemporaryDirectory() as out,mock.patch.object(Path,'read_text',return_value='\n'.join(lines)),mock.patch.object(sys,'argv',['inner.py',kind,out,'never']),mock.patch.object(inner.os,'statvfs',side_effect=lambda p:types.SimpleNamespace(f_flag=flags[p])),mock.patch.object(inner.os,'execvpe') as execute:
   with self.assertRaises(AssertionError):inner.main()
   execute.assert_not_called()
 def test_actual_contract_layout_still_rejected(self):
  self.gate('v1',{'/sys/fs/cgroup':15,'/sys/fs/cgroup/memory':4111,'/sys/fs/cgroup/cpu,cpuacct':4110})
 def test_writable_declared_root_still_rejected(self):
  self.gate('v1',{'/sys/fs/cgroup':0,'/sys/fs/cgroup/memory':1,'/sys/fs/cgroup/cpu,cpuacct':1})
 def test_cleanup_has_single_absolute_twenty_second_budget(self):
  child=mock.Mock(pid=4321);child.poll.return_value=None
  with mock.patch.object(host.old,'group_signal') as sig,mock.patch.object(host.old,'group_exists',return_value=True),mock.patch.object(host.time,'monotonic',side_effect=[0,16,21]),mock.patch.object(host.time,'sleep'):
   with self.assertRaisesRegex(RuntimeError,'not reaped'):host.cleanup_group(child)
   self.assertEqual(sig.call_args_list,[mock.call(4321,host.signal.SIGTERM),mock.call(4321,host.signal.SIGKILL)])
   child.wait.assert_not_called()
 def test_host_reachable_python36_grammar(self):
  for p in ('host.py','transport229.py'):
   ast.parse((Path(__file__).parent/'source-snapshot'/p).read_text(),feature_version=(3,6))
if __name__=='__main__':unittest.main(verbosity=2)
