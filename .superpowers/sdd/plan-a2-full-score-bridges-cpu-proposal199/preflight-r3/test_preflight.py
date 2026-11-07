import os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from guards import job_scoped,fresh_output
from cgroup_probe import collect,controller_path

class Scope(unittest.TestCase):
 def test_exact_components(self):
  for path in ('/slurm/job_123/step_batch','/slurm/job123/step_batch'):self.assertTrue(job_scoped('123',path))
  for path in ('/slurm/job_1234/step_batch','/slurm/foo123/job_99','/slurm/123/step','/job_1234/job_999','/job_123/job_999'):self.assertFalse(job_scoped('123',path))
  self.assertFalse(job_scoped('', '/job_123'))
 def test_actual_v1_v2_and_missing(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);v2=root/'slurm/job_123';v2.mkdir(parents=True)
   for n in ('memory.peak','memory.events'):(v2/n).write_text('0')
   self.assertTrue(collect('123','0::/slurm/job_123/step_batch'.replace('/step_batch',''),root)['required_194_counter_visible'])
   self.assertFalse(collect('12','0::/slurm/job_123',root)['required_194_counter_visible'])
   (v2/'memory.events').unlink();self.assertFalse(collect('123','0::/slurm/job_123',root)['required_194_counter_visible'])
   v1=root/'memory/slurm/job123';v1.mkdir(parents=True)
   for n in ('memory.max_usage_in_bytes','memory.failcnt','memory.oom_control'):(v1/n).write_text('0')
   self.assertTrue(collect('123','5:memory:/slurm/job123',root)['required_194_counter_visible'])
   (v1/'memory.failcnt').unlink();self.assertFalse(collect('123','5:memory:/slurm/job123',root)['required_194_counter_visible'])
 def test_actual_mount_root_mapping(self):
  info='23 1 0:22 /slurm /my/cgroup rw - cgroup2 cgroup rw'
  self.assertEqual(controller_path('v2','/slurm/job_123',info,Path('/unused')),Path('/my/cgroup/job_123'))
  with self.assertRaises(AssertionError):controller_path('v2','/different/job_123',info,Path('/unused'))
 def test_output_confinement(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);root=base/'evidence';root.mkdir();dest=root/'execution'
   self.assertEqual(fresh_output(str(dest),root,os.getuid()),dest)
   with self.assertRaises(AssertionError):fresh_output(str(root/'..'/'elsewhere'/'execution'),root,os.getuid())
   dest.symlink_to(base/'missing')
   with self.assertRaises(AssertionError):fresh_output(str(dest),root,os.getuid())
   dest.unlink();dest.mkdir()
   with self.assertRaises(AssertionError):fresh_output(str(dest),root,os.getuid())
   alias=base/'alias';alias.symlink_to(root,target_is_directory=True)
   with self.assertRaises(AssertionError):fresh_output(str(alias/'execution'),alias,os.getuid())
 def test_real_helper_import_does_not_create_bytecode(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);shutil.copyfile(Path(__file__).parent/'allocation_helper.py',root/'allocation_helper.py')
   env=dict(os.environ,PYTHONPATH=str(root));env.pop('PYTHONDONTWRITEBYTECODE',None)
   result=subprocess.run([sys.executable,'-B','-c','import allocation_helper'],cwd=str(root),env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
   self.assertEqual(result.returncode,0,result.stderr);self.assertFalse(list(root.rglob('__pycache__')))
 def test_spool_launch_no_bytecode(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);spool=root/'spooled';shutil.copyfile(Path(__file__).parent/'launch.sh',spool);tool=root/'python3';capture=root/'args'
   tool.write_text('#!/bin/sh\nprintf "%s\\n" "$PYTHONDONTWRITEBYTECODE" "$@" > "$CAPTURE"\n');tool.chmod(0o755)
   env=dict(os.environ,SLURM_JOB_ID='123',PATH=str(root)+':'+os.environ['PATH'],CAPTURE=str(capture));res=subprocess.run(['bash',str(spool),'/unused','abc'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
   self.assertEqual(res.returncode,0,res.stderr);args=capture.read_text().splitlines();self.assertEqual(args[0:2],['1','-B']);self.assertTrue(args[2].endswith('/preflight-r3/host_probe.py'))
   self.assertFalse(list(root.rglob('__pycache__')))
if __name__=='__main__':unittest.main()
