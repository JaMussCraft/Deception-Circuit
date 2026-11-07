import os,tempfile,unittest
from pathlib import Path
OLD=Path(__file__).resolve().parent.parent/'preflight'
class OriginalSemantics(unittest.TestCase):
 def test_exact_job_component(self):
  job='123';path='/sys/fs/cgroup/slurm/job_1234/step_batch';self.assertFalse(bool(job and job in path))
 def test_traversal_rejected(self):
  root=Path('/allowed/root');path=root/'../../outside';self.assertFalse(path.is_relative_to(root))
 def test_no_bytecode_option(self):
  self.assertIn('python3 -B', (OLD/'launch.sh').read_text())
if __name__=='__main__':unittest.main()
