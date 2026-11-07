"""Review197 boundary regressions exercise the actual supervisor.main path."""
import importlib.util,json,os,pathlib,sys,tempfile,types,unittest
from unittest import mock
P=pathlib.Path(__file__).resolve().parent
path=P/('supervisor-before-r2.py' if os.environ.get('PROOF194_R2_TEST_RED')=='1' else 'supervisor.py')
sp=importlib.util.spec_from_file_location('supervisor_boundary_r2',path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def report():return dict(status='CHILD_NORMAL_POSTGUARDS_AWAIT_SUPERVISOR',complete=False,**m.LABELS)
class DeadlineR2Tests(unittest.TestCase):
 def test_observed_before_at_after_cap(self):
  m.normal_child(0,None,99,100,report())
  with self.assertRaises(ValueError):m.normal_child(0,None,100,100,report())
  with self.assertRaises(ValueError):m.normal_child(0,None,101,100,report())
 def test_actual_main_reclamps_after_poll_reap_shortening(self):
  clock=types.SimpleNamespace(now=0.)
  fake_time=types.SimpleNamespace(time=lambda:clock.now,monotonic=lambda:clock.now,sleep=lambda _:None)
  allocations=[]
  def allocation():
   end=2700. if not allocations else 2500.
   value={'job':'UNIT','end_epoch':end};allocations.append(value);return value
  class Child:
   returncode=0
   def __init__(self,cmd,**kw):
    target=pathlib.Path(cmd[cmd.index('--output')+1]);(target/'CHILD-REPORT.json').write_text(json.dumps(report()))
   def poll(self):clock.now=2390.;return 0
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/'fresh-evidence'
   argv=['supervisor','--output',str(out),'--manifest-sha256','TINY_FIXTURE']
   with mock.patch.object(m,'time',fake_time),mock.patch.object(m,'allocation',allocation),mock.patch.object(m.g,'packet',lambda _:None),mock.patch.object(m.subprocess,'Popen',Child),mock.patch.object(m.signal,'signal',lambda *a:None),mock.patch.object(sys,'argv',argv):
    with self.assertRaises(ValueError):m.main()
   self.assertFalse((out/'COMPLETE-PROOF.json').exists())
   execution=json.loads((out/'child-execution.json').read_text());self.assertEqual(execution['deadline_monotonic'],2380.);self.assertFalse(execution['timely'])
   self.assertGreaterEqual(len(allocations),2)
if __name__=='__main__':unittest.main(verbosity=2)
