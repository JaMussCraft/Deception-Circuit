import importlib.util,json,os,signal,subprocess,sys,tempfile,time,unittest
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
    for source in ('direction-preallocation-candidate183','direction-metadata-optionA-candidate'):
     for rel in ('data','docs/research/directions.json','docs/research/held_out.json','outputs/_analyses/specificity-ladder/a1-control-77b6487-m07'):
      path=Path('Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3')/source/rel;p=host.PHYS/path;p.parent.mkdir(parents=True,exist_ok=True);p.symlink_to('target');aliases.append({'virtual':str(host.VIRT/path),'physical':str(p),'literal_target':'target'})
    c={'status':'ROOT_BOUND_A3_GREEN_MGNP_TRANSPORT','observer_virtual':str(host.VIRT/'run_packet.py'),'expected_cases':1,'expected_file_count':1,'files':files,'aliases':aliases};host.check_config(c)
    c['aliases']=aliases[:4]
    with self.assertRaises(AssertionError):host.check_config(c)
    c['aliases']=aliases;c['expected_file_count']=2
    with self.assertRaises(AssertionError):host.check_config(c)
   finally:host.PHYS,host.VIRT=oldp,oldv
 def test_spooled_launch_uses_absolute_packet(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);spool=root/'spool';spool.write_text((Path(__file__).parent/'launch.sh').read_text());tool=root/'python3';capture=root/'argv'
   tool.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$CAPTURE"\n');tool.chmod(0o755)
   env=dict(os.environ,SLURM_JOB_ID='123',CAPTURE=str(capture),PATH=str(root)+':'+os.environ['PATH'])
   p=subprocess.run(['bash',str(spool),'/config','sha','manifest'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   self.assertEqual(p.returncode,0,p.stderr);args=capture.read_text().splitlines();self.assertEqual(args[0],'-B');self.assertTrue(args[1].endswith('/a3-green-bridges-transport229-r3/host.py'));self.assertEqual(args[2:],['--config','/config','--config-sha256','sha','--manifest-sha256','manifest'])
 def test_actual_candidate_and_oracle_alias_inventory(self):
  root=Path(__file__).resolve().parent.parent.parent/'plan-a3'
  expected={'data','docs/research/directions.json','docs/research/held_out.json','outputs/_analyses/specificity-ladder/a1-control-77b6487-m07'}
  for source in ('direction-preallocation-candidate183','direction-metadata-optionA-candidate'):
   base=root/source;actual={str(Path(d,n).relative_to(base)) for d,dirs,files in os.walk(str(base),followlinks=False) for n in dirs+files if Path(d,n).is_symlink()}
   self.assertEqual(actual,expected)
   worktree=root.parent.parent.parent
   for rel in expected:self.assertEqual(os.readlink(str(base/rel)),str(worktree/rel))
  baseline=root.parent/'plan/task23-green-r4/baseline-source'
  self.assertFalse([str(Path(d,n)) for d,dirs,files in os.walk(str(baseline),followlinks=False) for n in dirs+files if Path(d,n).is_symlink()])
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
class ProcessGroups(unittest.TestCase):
 def exercise(self,leader_exits):
  with tempfile.TemporaryDirectory() as tmp:
   ready=Path(tmp)/'ready';script="""import os,signal,sys,time
p=os.fork()
if p==0:
 signal.signal(signal.SIGTERM,signal.SIG_IGN)
 open(sys.argv[1],'w').write(str(os.getpid()))
 while True: time.sleep(1)
while not os.path.exists(sys.argv[1]): time.sleep(.01)
if sys.argv[2]=='exit': sys.exit(0)
signal.signal(signal.SIGTERM,lambda a,b:sys.exit(0))
while True: time.sleep(1)
"""
   child=subprocess.Popen([sys.executable,'-c',script,str(ready),'exit' if leader_exits else 'wait'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   try:
    until=time.monotonic()+3
    while not ready.exists() and time.monotonic()<until:time.sleep(.01)
    self.assertTrue(ready.exists());pid=int(ready.read_text())
    if leader_exits:child.wait(timeout=3)
    else:time.sleep(.1)
    host.cleanup_group(child,grace=.15)
    until=time.monotonic()+3
    while time.monotonic()<until:
     try:state=Path('/proc/%d/stat'%pid).read_text().split(') ',1)[1][0]
     except FileNotFoundError:break
     if state=='Z':break
     time.sleep(.01)
    else:self.fail('grandchild survived process-group cleanup')
   finally:
    try:os.killpg(child.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    child.wait(timeout=3)
 def test_reaped_leader_live_child(self):self.exercise(True)
 def test_term_leader_exits_ignoring_child(self):self.exercise(False)
if __name__=='__main__':unittest.main()
