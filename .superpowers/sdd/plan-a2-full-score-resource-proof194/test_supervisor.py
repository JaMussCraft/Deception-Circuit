import importlib.util,pathlib,unittest,os
P=pathlib.Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('supervisor',P/('red-initial-supervisor.py' if os.environ.get('PROOF194_VERIFY_INITIAL_RED')=='1' else 'supervisor.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
class SupervisorTests(unittest.TestCase):
 def test_late_zero_is_not_complete(self):
  with self.assertRaises(ValueError):m.normal_child(0,None,101,100,{'status':'CHILD_NORMAL_POSTGUARDS_AWAIT_SUPERVISOR','complete':False,'MODEL_LOADED':False,'EFFECTS_READ':False,'SYNTHETIC_SCHEMA_ONLY':True,'NUMERICAL_CONTROLS_TESTED':False,'GPU_ADMITTED':False})
 def test_term_zero_is_not_complete(self):
  with self.assertRaises(ValueError):m.normal_child(0,90,95,100,{'status':'CHILD_NORMAL_POSTGUARDS_AWAIT_SUPERVISOR','complete':False,'MODEL_LOADED':False,'EFFECTS_READ':False,'SYNTHETIC_SCHEMA_ONLY':True,'NUMERICAL_CONTROLS_TESTED':False,'GPU_ADMITTED':False})
 def test_partial_child_not_complete(self):
  with self.assertRaises(ValueError):m.normal_child(0,None,95,100,{'status':'CHILD_NORMAL_POSTGUARDS_AWAIT_SUPERVISOR','complete':True,'MODEL_LOADED':False,'EFFECTS_READ':False,'SYNTHETIC_SCHEMA_ONLY':True,'NUMERICAL_CONTROLS_TESTED':False,'GPU_ADMITTED':False})
 def test_normal_child_does_not_infer_numeric_controls(self):
  m.normal_child(0,None,95,100,{'status':'CHILD_NORMAL_POSTGUARDS_AWAIT_SUPERVISOR','complete':False,'MODEL_LOADED':False,'EFFECTS_READ':False,'SYNTHETIC_SCHEMA_ONLY':True,'NUMERICAL_CONTROLS_TESTED':False,'GPU_ADMITTED':False})
if __name__=='__main__':unittest.main(verbosity=2)
