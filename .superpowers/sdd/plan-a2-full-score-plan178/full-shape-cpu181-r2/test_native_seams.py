import inspect,sys,unittest
from pathlib import Path
R=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime')
sys.path.insert(0,str(R))
from component_analysis.ladder_tasks import task_batches
from component_analysis.specificity_ladder import _rows,_map_index
import shape

def rows():
 result=[]
 for i in range(16):
  n=2 if i<8 else 9
  stream={'tokens':list(range(n)),'readout':n-1,'layout':None}
  result.append(dict(instance_id=str(i),task='ioi',condition='IOI',streams={'clean':stream,'corrupt':stream},expected_token=1,honest_token=1,opposite_token=2))
 return result

class NativeSeams(unittest.TestCase):
 def test_native_utility_donor_default16(self):
  self.assertEqual(inspect.signature(task_batches).parameters['batch_size'].default,16)
  rec=task_batches(rows(),batch_size=8);don=shape.utility_donors(task_batches,rows(),'corrupt')
  self.assertEqual(int(next(_rows(rec[0])).input_ids.shape[1]),2)
  self.assertEqual(int(next(_rows(don[0])).input_ids.shape[1]),9)
 def test_native_operation_filter(self):
  m={'recipient_condition':'IOI','recipient_id':'0','recipient_stream':'clean','operation':'item_swap','supported':False}
  self.assertEqual(_map_index([m],'zero'),{})
  self.assertFalse(shape.selected_map([m],'zero',('IOI','0','clean')))
  self.assertIs(shape.selected_map([m],'item_swap',('IOI','0','clean')),m)
 def test_support_and_capture_counts(self):
  m={'supported':False,'unsupported_reason':'unequal'}
  self.assertEqual(shape.capture_counts(m,False,2),(5,0))
  zero=dict(m,operation='zero',recipient_condition='IOI',recipient_id='0',recipient_stream='clean');self.assertEqual(shape.capture_counts(shape.selected_map([zero],'zero',('IOI','0','clean')),False,2),(5,0))
  self.assertEqual(shape.capture_counts(None,False,2),(7,0))
  self.assertEqual(shape.capture_counts(m,True,2),(5,0))
 def test_calibration_ignores_assay_support_and_validates_readouts(self):
  m={'supported':False,'recipient_positions':[],'donor_positions':[]}
  self.assertEqual(shape.calibration_width('ioi',m,2,9,1,8),9)
  self.assertEqual(shape.calibration_width('assessment',m,2,9,1,8),9)
  with self.assertRaises(AssertionError):shape.calibration_width('mmlu',dict(supported=True,recipient_positions=[0],donor_positions=[8]),2,9,1,8)
if __name__=='__main__':unittest.main()
