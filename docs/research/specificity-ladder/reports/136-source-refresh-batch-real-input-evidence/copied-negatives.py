"""Genuine copied artifacts; current additive registry and byte invalidation only."""
import pathlib,os,json,sys,shutil,time,resource
from types import SimpleNamespace
from component_analysis import a3_direction_runtime as authority,ladder_pipeline as ladder
from component_analysis import a3_mask_pipeline as mask,a3_edge_pipeline as edge
w=pathlib.Path(os.environ['W']);o=pathlib.Path(os.environ['O']);c=os.environ['C'];owner=sys.argv[1]
assert owner in ('mask','edge') and os.environ.get('SLURM_JOB_ID') and os.environ.get('CUDA_VISIBLE_DEVICES')==''
root=o/'negative-copies'/owner;root.mkdir(parents=True)
prepared_path=root/'prepared';shutil.copytree(o/owner/'prepared',prepared_path)
registry=root/'current-extra-registry.json'
def catalog(ids):
    temporary=registry.with_suffix('.new');temporary.write_text(json.dumps({'schema':1,'sets':[{'ids':ids}]}));temporary.replace(registry)
catalog([])
args=SimpleNamespace(commit=c,registry=[str(w/'docs/research/held_out.json'),str(registry)],design=str(o/'canonical/design.json'),prepared=str(prepared_path),work_dir=str(root),stage='pilot',seed=None,arm=None,task=None,group=None,chunk_size=4,steps=8,measure_stage='fit')
started=time.perf_counter();usage=resource.getrusage(resource.RUSAGE_SELF)
prepared=authority.read_object(prepared_path)
if owner=='mask':
    args._mask_source_started=time.perf_counter();mask._live_mask(prepared,args,inventory=None);state=args._mask_source_context
    def refresh():return mask._live_mask(prepared,args,inventory=None)[1]
else:
    args._source_started=time.perf_counter();design=ladder.read_artifact(args.design);state=edge._make_edge_source_state(prepared,design,args);assert state is not None
    def refresh():return state.refresh(owner='edge',bound_inputs={'prepared':prepared,'design':design},registry_paths=args.registry,scope=edge._edge_source_scope(args))
refresh()
rid=next(row['instance_id'] for task in state._protection.contexts.values() for rows in task['rows']['D'].values() for row in rows)
catalog([rid])
try:refresh()
except ValueError as error:
    protected_error=str(error);assert 'overlap' in protected_error
else:raise AssertionError('actual current protected overlap was accepted')
catalog([]);refresh()  # legitimate atomic catalog update revalidates safely
payload=prepared_path/'payload.json';before=payload.read_bytes();payload.write_bytes(before+b'\n')
try:refresh()
except ValueError as error:byte_error=str(error)
else:raise AssertionError('changed actual copied prepared bytes were accepted')
after=resource.getrusage(resource.RUSAGE_SELF)
result=dict(owner=owner,source_commit=c,job_id=os.environ['SLURM_JOB_ID'],copied_prepared=str(prepared_path),additional_registry=str(registry),all_original_registries_retained=True,real_current_overlap_rejected=protected_error,atomic_unrelated_reset_revalidated=True,prepared_byte_change_rejected=byte_error,original_artifacts_modified=False,immutable_runtime_modified=False,copied_artifact_intentionally_modified=True,execution_authorized=False,model_loaded=False,wall_seconds=time.perf_counter()-started,user_cpu_seconds=after.ru_utime-usage.ru_utime,system_cpu_seconds=after.ru_stime-usage.ru_stime,host_peak_bytes=after.ru_maxrss*1024)
(o/'evidence'/('copied-negatives-'+owner+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
