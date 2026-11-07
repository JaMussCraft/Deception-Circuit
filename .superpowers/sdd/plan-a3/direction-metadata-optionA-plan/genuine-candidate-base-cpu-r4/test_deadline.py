import ast,datetime,json,os,runpy,signal,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import allocation_facts as af
P=Path(__file__).resolve().parent

class SupervisorTests(unittest.TestCase):
 def execute(self, scenario):
  import hashlib,types
  config=P/'config.template.json';digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'out';clock=iter([0,3299,3300,3314,3315,3316] if scenario=='timeout' else [0,3300 if scenario=='at_limit' else 3301 if scenario=='after_limit' else 3299 if scenario=='before_limit' else 1])
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
   with patch.object(sys,'argv',argv),patch.object(af,'read_current',return_value={'time_limit_seconds':3600}),patch.object(af,'cgroup_snapshot',return_value=[{'headroom_bytes':160*1024**3}]),patch.object(subprocess,'Popen',return_value=Child()),patch.object(os,'wait4',side_effect=wait4),patch.object(os,'killpg',side_effect=lambda pid,sig:calls.append(sig)),patch('time.monotonic',side_effect=lambda:next(clock)),patch('time.sleep'):
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
