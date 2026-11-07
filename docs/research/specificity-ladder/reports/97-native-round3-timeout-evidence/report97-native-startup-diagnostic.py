from pathlib import Path
import faulthandler,json,os,resource,sys,time
root=Path(sys.argv[1]);out=Path(sys.argv[2]);started=time.perf_counter()
stack=(out/'stacks.log').open('w');faulthandler.dump_traceback_later(60,repeat=True,file=stack)
def mark(event,**extra):
 print(json.dumps(dict(event=event,elapsed_seconds=time.perf_counter()-started,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,**extra)),flush=True)
def step(name,fn):
 mark('step_start',step=name);before=time.perf_counter();value=fn();mark('step_end',step=name,step_seconds=time.perf_counter()-before);return value
mark('import_start')
from tests import a3_direction_native_scenario as s
from component_analysis import hooks
mark('import_end')
def denied(*a,**kw):raise RuntimeError('Diagnostic forbids model forwards/publication')
s.r.publish_object=denied;s.r.common.publish=denied;s.r._pilot_invocation=denied;hooks.capture_forward=denied
assert (root/'inventory/selected-pilot/COMPLETE.json').is_file()
d,p,model,plain=step('verify_scenario_full_model',lambda:s.verify_scenario(root))
hook=plain.register_forward_pre_hook(denied)
selected,_=step('read_selected_first',lambda:s.r.read_bundle(root/'selected'))
inv=step('inventory_rebuild_and_existing_compare',lambda:s.inventory(root,d,p,'selected-pilot',selected=selected))
invocations=step('run_phase_case_invocations_validation',lambda:s._case_invocations(d,inv,'selected'))
assert len(invocations)==63
binding=step('read_scenario_binding',lambda:s.r.read_object(root/'scenario'))
again=step('pilot_cases_case_invocations_validation',lambda:s._case_invocations(d,inv,'selected'))
selected2,_=step('read_selected_second',lambda:s.r.read_bundle(root/'selected'))
axes=step('load_selected_axes',lambda:s.r.load_selected_axes(root/'selected',selected2))
assert s.model_identity(plain)==binding['model_identity']
step('final_source_model_backing_verification',lambda:s.verify_scenario(root,load_model=False))
hook.remove();mark('diagnostic_complete',model_forward_calls=0,published_scientific_artifacts=0,case_count=len(again),axis_count=len(axes))
faulthandler.cancel_dump_traceback_later();stack.close()
