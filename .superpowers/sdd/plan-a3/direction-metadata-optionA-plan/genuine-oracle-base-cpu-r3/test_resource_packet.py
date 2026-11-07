import ast,datetime,json,os,runpy,signal,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import allocation_facts as af
P=Path(__file__).resolve().parent

class AllocationTests(unittest.TestCase):
 def exercise(self, changes=None, envchanges=None, remaining=4400):
  fields=dict(JobId='7',JobState='RUNNING',UserId='user(%d)'%os.getuid(),AllocTRES='cpu=4,mem=192G,node=1',NumNodes='1',Account='bimc-delta-cpu',Partition='cpu',WorkDir='/tmp',NodeList='node1',TimeLimit='01:15:00',EndTime='2030-01-01T00:00:00')
  fields.update(changes or {})
  env={'SLURM_JOB_ID':'7','SLURM_CLUSTER_NAME':'delta','SLURM_CPUS_PER_TASK':'4'};env.update(envchanges or {})
  class R:
   def __init__(self,text):self.stdout=text
  def fake(args,**kw):return R(' '.join(k+'='+v for k,v in fields.items()) if '-o' in args else fields['NodeList']+'\n')
  with patch.dict(os.environ,env,clear=True),patch.object(af.subprocess,'run',side_effect=fake),patch.object(af.os,'uname',return_value=type('U',(),{'nodename':'node1'})()),patch.object(af.time,'time',return_value=datetime.datetime(2029,12,31,22,45,tzinfo=datetime.timezone.utc).timestamp()):
   return af.read_current('/tmp',minimum_remaining_seconds=remaining)
 def test_accept_reviewed_allocation(self):self.assertEqual(self.exercise()['time_limit_seconds'],4500)
 def test_reject_wrong_allocation(self):
  for changes,env in [({'AllocTRES':'cpu=3,mem=192G'},{}),({'AllocTRES':'cpu=4,mem=191G'},{}),({'AllocTRES':'cpu=4,mem=192G,gres/gpu=1'},{}),({'Partition':'cpu-interactive'},{}),({'WorkDir':'/bad'},{}),({'UserId':'bad(99999999)'},{}),({'NodeList':'wrong'},{}),({'TimeLimit':'01:16:00'},{}),({}, {'SLURM_JOB_GPUS':'0'})]:
   with self.subTest(changes=changes,env=env):
    with self.assertRaises(AssertionError):self.exercise(changes,env)
 def test_reject_insufficient_remaining(self):
  with self.assertRaises(AssertionError):self.exercise(remaining=4501)

class StaticContract(unittest.TestCase):
 def test_limits_and_unmodified_child_contract(self):
  c=json.loads((P/'config.template.json').read_text());self.assertEqual((c['CPU_child_seconds'],c['Slurm_minutes'],c['kill_grace_seconds']),(4200,75,15))
  tree=ast.parse((P/'supervisor.py').read_text());text=ast.unparse(tree)
  for part in ('minimum_remaining_seconds=4400','4200','4500','SIGTERM','SIGKILL',"term is not None"):
   self.assertIn(part,text)
  child=(P/'run.py').read_text()
  for part in ("sink.write('\\n')","guard_after=r.live_guard","post=sources()","write('RESULT.json',result)"):
   self.assertIn(part,child)

class SupervisorTests(unittest.TestCase):
 def execute(self, scenario):
  import hashlib,types
  config=P/'config.template.json';digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'out';clock=iter([0,4199,4200,4214,4215,4216] if scenario=='timeout' else [0,4200 if scenario=='at_limit' else 4201 if scenario=='after_limit' else 4199 if scenario=='before_limit' else 1])
   calls=[];count=[0]
   class Child:
    pid=12345
    returncode=None
   def wait4(pid,flags):
    count[0]+=1
    if scenario=='timeout' and count[0]<=4:return (0,0,None)
    if scenario in ('normal','at_limit','after_limit','before_limit'):
     (out/'RESULT.json').write_text(json.dumps({'complete':False,'mode':'original','environment':'base'}))
    status=0 if scenario in ('normal','timeout','at_limit','after_limit','before_limit') else 256
    return (pid,status,types.SimpleNamespace(ru_utime=1,ru_stime=1,ru_maxrss=1))
   argv=['supervisor.py','--packet-sha256',digest(P/'manifest.json'),'--config',str(config),'--config-sha256',digest(config),'--mode','original','--environment','base','--output',str(out)]
   with patch.object(sys,'argv',argv),patch.object(af,'read_current',return_value={'time_limit_seconds':4500}),patch.object(af,'cgroup_snapshot',return_value=[{'headroom_bytes':160*1024**3}]),patch.object(subprocess,'Popen',return_value=Child()),patch.object(os,'wait4',side_effect=wait4),patch.object(os,'killpg',side_effect=lambda pid,sig:calls.append(sig)),patch('time.monotonic',side_effect=lambda:next(clock)),patch('time.sleep'):
    try:runpy.run_path(str(P/'supervisor.py'),run_name='__main__')
    except SystemExit as e:self.assertEqual(e.code,1)
   return calls,(out/'COMPLETE_ORACLE.json').exists(),(out/'FAILED.json').exists()
 def test_deadline_term_kill_and_no_complete_even_exit_zero(self):
  calls,complete,failed=self.execute('timeout');self.assertEqual(calls,[signal.SIGTERM,signal.SIGKILL]);self.assertFalse(complete);self.assertTrue(failed)
 def test_normal_child_only_completion(self):
  calls,complete,failed=self.execute('normal');self.assertEqual(calls,[]);self.assertTrue(complete);self.assertFalse(failed)
 def test_reaped_normal_exit_at_or_after_limit_fails(self):
  for scenario in ('at_limit','after_limit'):
   with self.subTest(scenario=scenario):
    calls,complete,failed=self.execute(scenario);self.assertFalse(complete);self.assertTrue(failed)
 def test_reaped_normal_exit_before_limit_passes(self):
  calls,complete,failed=self.execute('before_limit');self.assertTrue(complete);self.assertFalse(failed)
 def test_child_missing_stream_or_postguard_cannot_complete(self):
  for scenario in ('missing_stream','failed_postguard'):
   with self.subTest(scenario=scenario):
    calls,complete,failed=self.execute(scenario);self.assertFalse(complete);self.assertTrue(failed)

if __name__=='__main__':unittest.main()
