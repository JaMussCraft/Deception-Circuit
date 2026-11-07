import unittest
from pathlib import Path
from cgroup_probe import collect
from guards import cgroup_bind

class Binding(unittest.TestCase):
 def test_real_controller_bind_is_readonly_same_path(self):
  for kind,path in [('v1','/sys/fs/cgroup'),('v2','/sys/fs/cgroup')]:
   self.assertEqual(cgroup_bind(kind),path+':'+path+':ro')
 def test_host_command_uses_actual_readonly_bind(self):
  source=(Path(__file__).parent/'host_probe.py').read_text()
  self.assertIn("actual_cgroup_bind=cgroup_bind(valid[0]['controller'])",source)
  self.assertIn("'--bind',actual_cgroup_bind",source)
 def test_failed_mapping_preserves_membership_and_candidate_error(self):
  out=collect('123','5:memory:/slurm/job_123/step_batch',Path('/not-real'),'23 1 0:22 / /x rw - tmpfs tmpfs rw')
  self.assertFalse(out['required_194_counter_visible'])
  self.assertEqual(out['records'][0]['membership'],'/slurm/job_123/step_batch')
  self.assertIn('unavailable',out['records'][0]['path_error'])
  self.assertEqual(out['memory_mount_lines'],[])
if __name__=='__main__':unittest.main()
