import hashlib,importlib.util,json,os,pathlib,subprocess,sys,tempfile,unittest
from unittest import mock
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import host,inner

class Tests(unittest.TestCase):
 def test_selection_environment_and_container_command(self):
  p=json.loads((host.DIAG/'root-diagnostic-recipe-r2.json').read_text())['commands'][0]
  c=host.command({},p,'v2',{'SLURM_JOB_ID':'123'},None)
  self.assertIn('DIAG253_SELECTION='+p['environment']['DIAG253_SELECTION'],c)
  self.assertTrue(any(x.startswith('A3_T1_OUTPUT=') and 'six-failure-traces' in x for x in c))
  self.assertIn(str(host.old.VIRT/host.REL/'inner.py'),c)
  self.assertEqual(c[-len(p['argv']):][0],p['argv'][0])
 def test_margins_strict(self):
  self.assertFalse(host.enough(0,1360,2));self.assertTrue(host.enough(0,1361,2))
  self.assertFalse(host.enough(0,740,1));self.assertTrue(host.enough(0,741,1))
 def test_exhaustion_after_costly_source_check_never_spawns(self):
  with tempfile.TemporaryDirectory() as d:
   p={'label':'six-failure-traces'}
   with mock.patch.object(host,'source_check'),mock.patch.object(host.old,'sha',return_value=host.old.IMAGE_SHA),mock.patch.object(host,'command',return_value=['never']),mock.patch.object(host,'allocation',return_value=({},1000)),mock.patch.object(host.time,'time',return_value=0),mock.patch.object(host.subprocess,'Popen') as popen:
    with self.assertRaises(AssertionError):host.execute_phase({},p,0,'v2',pathlib.Path(d),1000)
    popen.assert_not_called()
 def test_reaps_group_after_leader_exit(self):
  child=mock.Mock(pid=4321);child.poll.return_value=1
  with mock.patch.object(host.old,'group_signal') as sig,mock.patch.object(host.old,'group_exists',side_effect=[True,False]),mock.patch.object(host.os,'waitpid',side_effect=[(123,0),(0,0),ChildProcessError()]),mock.patch.object(host.time,'sleep'):
   host.cleanup_group(child)
   sig.assert_called_once_with(4321,host.signal.SIGTERM)
   child.wait.assert_called_once()
 def test_group_killed_after_term_grace(self):
  child=mock.Mock(pid=4321);child.poll.return_value=1
  with mock.patch.object(host.old,'group_signal') as sig,mock.patch.object(host.old,'group_exists',side_effect=[True,False]),mock.patch.object(host.os,'waitpid',side_effect=ChildProcessError()),mock.patch.object(host.time,'monotonic',side_effect=[0,16,16]),mock.patch.object(host.time,'sleep'):
   host.cleanup_group(child)
   self.assertEqual(sig.call_args_list,[mock.call(4321,host.signal.SIGTERM),mock.call(4321,host.signal.SIGKILL)])
 def test_effective_mount_longest_prefix(self):
  lines=['1 2 0:1 / /sys/fs/cgroup ro - cgroup2 cgroup rw','2 1 0:2 / /sys/fs/cgroup/memory rw - cgroup memory rw']
  self.assertIn('rw',inner.mount_for('/sys/fs/cgroup/memory',lines)[2])
  self.assertIn('ro',inner.mount_for('/sys/fs/cgroup',lines)[2])
 def test_direct_and_relocated_launcher_forwards_exact_arguments(self):
  with tempfile.TemporaryDirectory() as d:
   d=pathlib.Path(d); python=d/'python3'; python.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$CAPTURE"\n');python.chmod(0o755)
   env=dict(os.environ,SLURM_JOB_ID='12',PATH=str(d)+':'+os.environ['PATH'],CAPTURE=str(d/'capture'))
   for launch in (HERE/'launch.sh',d/'relocated.sh'):
    if launch.parent==d:launch.write_bytes((HERE/'launch.sh').read_bytes())
    subprocess.check_call(['bash',str(launch),'/absolute/config','abc','def'],env=env)
    args=(d/'capture').read_text().splitlines()
    self.assertEqual(args[-6:],['--config','/absolute/config','--config-sha256','abc','--manifest-sha256','def'])
    self.assertTrue(args[1].endswith('/diagnostic-transport254-r2/host.py'))
 def test_swapped_config_rejected_before_allocation(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'c';p.write_text('{}'); m=hashlib.sha256((HERE/'manifest.json').read_bytes()).hexdigest()
   result=subprocess.run([sys.executable,str(HERE/'host.py'),'--config',str(p),'--config-sha256','0'*64,'--manifest-sha256',m],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   self.assertNotEqual(result.returncode,0);self.assertIn(b'AssertionError',result.stderr)
if __name__=='__main__':unittest.main(verbosity=2)
