import os,sys,json,pathlib,time,resource,datetime,subprocess,hashlib
w=pathlib.Path(os.environ['W']);b=pathlib.Path(os.environ['B']);o=pathlib.Path(os.environ['O']);e=pathlib.Path(os.environ['E']);commit=os.environ['C'];owner=sys.argv[1]
assert owner in ('mask','edge') and os.environ.get('SLURM_JOB_ID') and os.environ.get('CUDA_VISIBLE_DEVICES')==''
job=os.environ['SLURM_JOB_ID'];raw=subprocess.run(['scontrol','show','job',job,'-o'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True).stdout
facts=dict(x.split('=',1) for x in raw.split() if '=' in x)
assert facts['JobState']=='RUNNING' and facts['Account']=='beto-delta-cpu' and facts['Partition']=='cpu'
tres=dict(x.split('=',1) for x in facts.get('AllocTRES',facts.get('TRES','')).split(',') if '=' in x)
assert not any(k.startswith('gres/gpu') and float(v)>0 for k,v in tres.items())
release=e/'cpu-release.json';assert release.is_file()
import torch
assert not torch.cuda.is_available(),'CPU-only allocation must expose no CUDA device'
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
report=dict(kind='actual_source_only_cost_measurement_v1',owner=owner,commit=commit,python=sys.executable,source_only=True,execution_authority_exercised=False,execution_authorized=False,model_loaded=False,job_id=job,cluster='delta',allocated_resources=facts,scheduler_record=raw,diagnostic_comparison=True,
    semantics='Cold process-local source initialization and actual owner source-half refresh in a genuine Slurm CPU allocation; model reservation/lease hooks remain unchanged and unexercised because no model admission is requested, and are not replaced/injected.',
    cache_state='OS/filesystem caches uncontrolled; process-local cold only. New preparation warms inputs on this compute node; f5 CPU job23454781 used earlier node/cache state. Comparison is observational, not controlled attribution.',
    cold=cold_measure,source_stats_before=stats_before,source_stats_after=stats_after,stats_walk=stats_timing,refreshes=refreshes,
    consumed_cost_fields=dict(startup_seconds_source_component=consumed_startup,host_peak_bytes=sources.host_peak_bytes(),projectors_unchanged=True,native_load_component_not_measured=True),
    runtime_signature=__import__('component_analysis.a3_edge_pipeline',fromlist=['runtime_signature']).runtime_signature(),hostname=os.uname().nodename,
    cpu_model=next((line.split(':',1)[1].strip() for line in pathlib.Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),None),
    thread_environment={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')},source_roots=list(state._witness.paths),isolation_release=json.loads(release.read_text()),project_imports=project_imports)
(e/('source-cost-'+owner+'.json')).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps({key:report[key] for key in ('owner','commit','cold','refreshes','consumed_cost_fields','cache_state','execution_authorized')},indent=2))

# Clean costs above are already published before any diagnostic/audit extra work.
expected=state._witness.identities
oracle,oracle_timing=observe(lambda:tuple(authority._file_tree_identity(path) for path in state._witness.paths))
assert oracle==expected
batch,batch_timing=observe(lambda:state._scan_plan._rows_now(hash_files=True))
assert batch==oracle
expected_files=[row for tree in oracle for row in tree if row[0]=='file']
active=False;opened=[]
def audit(event,values):
    if not active or event!='open' or not isinstance(values[0],(str,bytes)):return
    frame=sys._getframe(1)
    while frame is not None:
        if frame.f_code.co_name=='_read_source_file' and frame.f_code.co_filename.endswith('a3_source_validation.py'):
            opened.append(os.fsdecode(values[0]));break
        frame=frame.f_back
sys.addaudithook(audit);active=True
try:audited,audit_timing=observe(refresh)
finally:active=False
assert opened==[row[1] for row in expected_files]
assert audited['commit']==commit and audited['registry_hashes'] and audited['grader_registry']
agreement=dict(owner=owner,commit=commit,oracle_timing=oracle_timing,batch_timing=batch_timing,audited_refresh=audit_timing,expected_paths=[row[1] for row in expected_files],audited_paths=opened,file_occurrences=len(expected_files),expected_bytes=sum(row[2][3] for row in expected_files),batch_bytes=sum(row[2][3] for tree in batch for row in tree if row[0]=='file'),full_rows_and_order_equal=True,complete_fd_reads_guaranteed_by_authenticated_owner_scanner=True,diagnostic_only=True,clean_refreshes_already_saved=True)
(e/('byte-agreement-'+owner+'.json')).write_text(json.dumps(agreement,indent=2)+'\n')
