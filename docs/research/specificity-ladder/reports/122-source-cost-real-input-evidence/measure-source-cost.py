"""Source-only used-path CPU measurements. No execution authority is supplied."""
import os,sys,json,pathlib,time,resource,datetime,subprocess,hashlib
w=pathlib.Path(os.environ['W']);b=pathlib.Path(os.environ['B']);o=pathlib.Path(os.environ['O']);commit=os.environ['C']
# This is coordination evidence only, never source/execution authority.
release=o/'evidence/isolation-release.json'
assert release.is_file(),'Root must report the concurrent direction case terminal before isolated measurement'
if len(sys.argv)==1:
    for owner in ('mask','edge'):
        cmd=[sys.executable,__file__,owner];started=time.time()
        with (o/'evidence'/('benchmark-'+owner+'.log')).open('w') as log:run=subprocess.run(cmd,cwd=b,env=dict(os.environ),stdout=log,stderr=subprocess.STDOUT,timeout=1200)
        (o/'evidence'/('benchmark-'+owner+'-command.json')).write_text(json.dumps(dict(command=cmd,cwd=str(b),exit_code=run.returncode,elapsed_seconds=time.time()-started,source_only=True,execution_authority_exercised=False),indent=2)+'\n')
        if run.returncode:raise SystemExit(run.returncode)
    raise SystemExit(0)
owner=sys.argv[1]
assert owner in ('mask','edge') and not os.environ.get('SLURM_JOB_ID')
from types import SimpleNamespace
from component_analysis import a3_direction_runtime as authority,ladder_pipeline as ladder
from component_analysis import a3_source_validation as sources
registry=[str(w/'docs/research/held_out.json')]
def observe(fn):
    before=resource.getrusage(resource.RUSAGE_SELF);wall=time.perf_counter();started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    value=fn();elapsed=time.perf_counter()-wall;after=resource.getrusage(resource.RUSAGE_SELF)
    return value,dict(started_utc=started,wall_seconds=elapsed,user_cpu_seconds=after.ru_utime-before.ru_utime,system_cpu_seconds=after.ru_stime-before.ru_stime,host_peak_bytes=int(after.ru_maxrss)*1024)
args=SimpleNamespace(commit=commit,registry=registry,design=str(o/'canonical/design.json'),prepared=str(o/owner/'prepared'),work_dir=str(o/owner),stage='pilot',seed=None,arm=None,task=None,group=None,chunk_size=4,steps=8,measure_stage='fit')
if owner=='mask':
    from component_analysis import a3_mask_pipeline as pipeline
    args._mask_source_started=time.perf_counter()
    def cold():
        prepared=authority.read_object(args.prepared)
        design,evidence=pipeline._live_mask(prepared,args,inventory=None)
        return prepared,design,evidence
    (prepared,design,evidence),cold_measure=observe(cold)
    state=args._mask_source_context
    def refresh():return pipeline._live_mask(prepared,args,inventory=None)[1]
else:
    from component_analysis import a3_edge_pipeline as pipeline
    args._source_started=time.perf_counter()
    def cold():
        design=ladder.read_artifact(args.design);prepared=authority.read_object(args.prepared)
        state=pipeline._make_edge_source_state(prepared,design,args)
        assert state is not None,'Genuine source bindings failed to mint source-only state'
        args._edge_source_context=state
        return prepared,design,state
    (prepared,design,state),cold_measure=observe(cold)
    evidence=None
    def refresh():return state.refresh(owner='edge',bound_inputs={'prepared':prepared,'design':design},registry_paths=args.registry,scope=pipeline._edge_source_scope(args))
# Diagnostic traversal is timed separately and never hidden inside hot refresh.
stats_before,stats_timing=observe(state.stats)
refreshes=[]
for index in range(3):
    fresh,timing=observe(refresh)
    assert fresh.get('injected') is False and fresh.get('commit')==commit
    assert fresh['registry_hashes'] and fresh['grader_registry']
    refreshes.append(dict(index=index,**timing,registry_hashes=fresh['registry_hashes'],grader_registry=fresh['grader_registry']))
stats_after=state.stats()
assert stats_after['refreshes']>=3 and stats_after['verified_bytes']>0 and stats_after['roots']>0
assert stats_after['retained_bytes']>0
consumed_startup=pipeline._source_startup_seconds(0.,args)
assert consumed_startup==stats_after['initialization_seconds']
assert sources.host_peak_bytes()>=stats_after['host_peak_bytes']
project_imports={name:module.__file__ for name,module in list(sys.modules.items()) if name.split('.')[0] in ('component_analysis','dataset','scripts','evaluation','models') and getattr(module,'__file__',None)}
assert all(pathlib.Path(path).resolve().is_relative_to(b) for path in project_imports.values())
report=dict(kind='actual_source_only_cost_measurement_v1',owner=owner,commit=commit,python=sys.executable,source_only=True,execution_authority_exercised=False,execution_authorized=False,model_loaded=False,job_id=None,cluster=None,
    semantics='Cold process-local source initialization and actual owner source-half refresh; unchanged ledger/reservation/lease hooks are not called without a real allocation, and are not replaced/injected.',
    cache_state='OS/filesystem caches not flushed; inputs warmed by genuine CPU preparation; cold means no process-local source state existed',
    cold=cold_measure,source_stats_before=stats_before,source_stats_after=stats_after,stats_walk=stats_timing,refreshes=refreshes,
    consumed_cost_fields=dict(startup_seconds_source_component=consumed_startup,host_peak_bytes=sources.host_peak_bytes(),projectors_unchanged=True,native_load_component_not_measured=True),
    runtime_signature=__import__('component_analysis.a3_edge_pipeline',fromlist=['runtime_signature']).runtime_signature(),hostname=os.uname().nodename,
    cpu_model=next((line.split(':',1)[1].strip() for line in pathlib.Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),None),
    thread_environment={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')},source_roots=list(state._witness.paths),isolation_release=json.loads(release.read_text()),project_imports=project_imports)
(o/'evidence'/('source-cost-'+owner+'.json')).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps({key:report[key] for key in ('owner','commit','cold','refreshes','consumed_cost_fields','cache_state','execution_authorized')},indent=2))
