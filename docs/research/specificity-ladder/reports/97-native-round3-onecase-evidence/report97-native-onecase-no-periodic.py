from pathlib import Path
import faulthandler,functools,json,resource,sys,time
root=Path(sys.argv[1]);out=Path(sys.argv[2]);began=time.perf_counter();forward=[0]
stack=(out/'stacks.log').open('w');faulthandler.enable(file=stack,all_threads=True)
def mark(event,**fields):
 print(json.dumps(dict(event=event,elapsed_seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,observed_forward_calls=forward[0],**fields)),flush=True)
mark('import_start')
from tests import a3_direction_native_scenario as s
from component_analysis import hooks
mark('import_end')
def wrap(owner,name):
 original=getattr(owner,name)
 @functools.wraps(original)
 def logged(*a,**kw):
  mark('call_start',function=name);start=time.perf_counter()
  try:value=original(*a,**kw)
  except BaseException:
   mark('call_error',function=name,call_seconds=time.perf_counter()-start);raise
  mark('call_end',function=name,call_seconds=time.perf_counter()-start)
  return value
 setattr(owner,name,logged)
for owner,name in [(s,'verify_scenario'),(s,'inventory'),(s,'_case_invocations'),(s,'pilot_cases'),(s,'_read_pilot_case'),
 (s.r,'read_bundle'),(s.r,'load_selected_axes'),(s.r,'_pilot_invocation'),(s.r,'_numeric_backing_proof'),(s.r._CompletedPackingProof,'__init__')]:wrap(owner,name)
original_capture=hooks.capture_forward
def capture(*a,**kw):forward[0]+=1;return original_capture(*a,**kw)
hooks.capture_forward=capture
try:
 result=s.run_phase(root,'selected-pilot',start=0,count=1,resume=True)
 mark('one_case_complete',result=result)
finally:
 hooks.capture_forward=original_capture
 faulthandler.disable();stack.close()
