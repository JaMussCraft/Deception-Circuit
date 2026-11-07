import json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest import mock
HERE=Path(__file__).parent;sys.path.insert(0,str(HERE/'source-snapshot'));import inner
class ActualFlags(unittest.TestCase):
 def replay(self,kind):
  flags=json.loads((HERE/'actual-r2-flags.json').read_text());lines=['%d 0 0:1 / %s rw - cgroup cgroup rw'%(i,p) for i,p in enumerate(flags,1)]
  with tempfile.TemporaryDirectory() as out,mock.patch.object(Path,'read_text',return_value='\n'.join(lines)),mock.patch.object(sys,'argv',['inner.py',kind,out,'never']),mock.patch.object(inner.os,'statvfs',side_effect=lambda p:types.SimpleNamespace(f_flag=flags[p])) as stat,mock.patch.object(inner.os,'execvpe') as execute:
   inner.main();execute.assert_called_once()
   with (Path(out)/'inner-mounts.json').open() as f:record=json.load(f)
   wanted={'/sys/fs/cgroup'}|({'/sys/fs/cgroup/memory'} if kind=='v1' else set())
   self.assertEqual(set(record['statvfs_flags']),wanted);self.assertEqual(record['mountinfo'],lines);self.assertEqual(stat.call_count,len(wanted))
 def test_v1_actual_flag_values_allow_declared_ro(self):self.replay('v1')
 def test_v2_only_declared_root_checked(self):self.replay('v2')
if __name__=='__main__':unittest.main(verbosity=2)
