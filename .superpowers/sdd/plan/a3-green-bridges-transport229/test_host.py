import importlib.util,json,os,subprocess,tempfile,time,unittest
from pathlib import Path
import host

class Checks(unittest.TestCase):
 def test_mapping_and_command(self):
  c={'observer_virtual':str(host.VIRT/'packet/run_packet.py')};out=host.VIRT/'jobs/job-123/execution'
  cmd=host.container_command(c,out,'v1',{'SLURM_JOB_ID':'123','SLURM_CLUSTER_NAME':'bridges2'})
  self.assertEqual(cmd[cmd.index('--pwd')+1],str(Path(c['observer_virtual']).parent))
  self.assertIn('/sys/fs/cgroup:/sys/fs/cgroup:ro,/sys/fs/cgroup/memory:/sys/fs/cgroup/memory:ro',cmd)
  self.assertIn('/ocean/projects/cis260361p/swong2/envs/mgnp:/u/swong2/.conda/envs/mgnp:ro',cmd)
  self.assertEqual(cmd[-6:],['/u/swong2/.conda/envs/mgnp/bin/python','-B',c['observer_virtual'],'--mode=GREEN','--environment=mgnp','--output='+str(out)])
  self.assertEqual(host.virtual_to_physical(str(host.VIRT/'a')),str(host.PHYS/'a'))
  with self.assertRaises((AssertionError,ValueError)):host.virtual_to_physical('/unrelated/path')
 def test_pins_missing_modified_and_alias(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);f=root/'f';f.write_bytes(b'abc');link=root/'alias';link.symlink_to('f')
   files=[{'physical':str(f),'sha256':host.sha(f),'bytes':3}];aliases=[{'physical':str(link),'literal_target':'f'}]
   host.check_records(files,aliases);f.write_bytes(b'abd')
   with self.assertRaises(AssertionError):host.check_records(files,aliases)
   f.unlink()
   with self.assertRaises((AssertionError,OSError)):host.check_records(files,aliases)
   link.unlink();link.symlink_to('other')
   with self.assertRaises(AssertionError):host.check_records([],aliases)
 def test_sealed_source_mapping(self):
  with tempfile.TemporaryDirectory() as tmp:
   oldp,oldv=host.PHYS,host.VIRT;host.PHYS=Path(tmp)/'phys';host.VIRT=Path(tmp)/'virt';host.PHYS.mkdir()
   try:
    f=host.PHYS/'run_packet.py';f.write_text('fixture');files=[{'virtual':str(host.VIRT/'run_packet.py'),'physical':str(f),'sha256':host.sha(f),'bytes':len(f.read_bytes())}]
    aliases=[]
    for i in range(4):
     p=host.PHYS/('alias'+str(i));p.symlink_to('run_packet.py');aliases.append({'virtual':str(host.VIRT/p.name),'physical':str(p),'literal_target':'run_packet.py'})
    c={'status':'ROOT_BOUND_A3_GREEN_MGNP_TRANSPORT','observer_virtual':str(host.VIRT/'run_packet.py'),'expected_cases':1,'expected_file_count':1,'files':files,'aliases':aliases};host.check_config(c)
    c['expected_file_count']=2
    with self.assertRaises(AssertionError):host.check_config(c)
   finally:host.PHYS,host.VIRT=oldp,oldv
 def test_spooled_launch_uses_absolute_packet(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);spool=root/'spool';spool.write_text((Path(__file__).parent/'launch.sh').read_text());tool=root/'python3';capture=root/'argv'
   tool.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$CAPTURE"\n');tool.chmod(0o755)
   env=dict(os.environ,SLURM_JOB_ID='123',CAPTURE=str(capture),PATH=str(root)+':'+os.environ['PATH'])
   p=subprocess.run(['bash',str(spool),'/config','sha','manifest'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   self.assertEqual(p.returncode,0,p.stderr);args=capture.read_text().splitlines();self.assertEqual(args[0],'-B');self.assertTrue(args[1].endswith('/a3-green-bridges-transport229/host.py'));self.assertEqual(args[2:],['--config','/config','--config-sha256','sha','--manifest-sha256','manifest'])
 def test_unbound_config_rejected(self):
  with self.assertRaises((AssertionError,KeyError)):host.check_config({'status':'UNBOUND_NOT_EXECUTABLE'})
 def test_deadline_and_reaped_late(self):
  self.assertEqual(host.child_deadline(100,3600),3550)
  with self.assertRaises(AssertionError):host.child_deadline(100,3529)
  self.assertTrue(host.timely(0,False,109,110));self.assertFalse(host.timely(0,False,110,110));self.assertFalse(host.timely(0,True,109,110))
 def test_manifest_accepts_only_green_mgnp(self):
  row={'status':'GREEN_EXPECTED','normal_completion':True,'pytest_exit_code':0,'observed_cases':3,'expected_cases':3,'failures':0,'errors':0,'skipped':0,'source_pins_before_after_equal':True,'baseline_red':{'exit_code':0,'manifest':{'status':'CORRECTION_RED_EXPECTED','normal_completion':True}},'oracle_preflight':{'exit_code':0},'oracle':{'complete':True},'python':'/u/swong2/.conda/envs/mgnp/bin/python'}
  m={'status':'GREEN_EXPECTED','normal_completion':True,'exit_code':0,'job_id':'123','cluster':'bridges2','model_loaded':False,'execution_authorized':False,'results':{'mgnp':row}}
  self.assertTrue(host.normal_manifest(m,'123',3));row['skipped']=1;self.assertFalse(host.normal_manifest(m,'123',3))
  row['skipped']=0;m['results']['base']={};self.assertFalse(host.normal_manifest(m,'123',3))
if __name__=='__main__':unittest.main()
