import unittest
from pathlib import Path
from cgroup_probe import collect
class ExistingFailure(unittest.TestCase):
 def test_mapping_failure_still_returns_membership_evidence(self):
  out=collect('123','5:memory:/slurm/job_123/step_batch',Path('/not-real'),'23 1 0:22 / /x rw - tmpfs tmpfs rw')
  self.assertFalse(out['required_194_counter_visible']);self.assertEqual(out['records'][0]['membership'],'/slurm/job_123/step_batch')
if __name__=='__main__':unittest.main()
