import ast,copy,json,math
from pathlib import Path
from types import SimpleNamespace
b=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd');c=b/'plan-a3/direction-preallocation-candidate183'
def require(ok,message):
 if not ok:raise ValueError(message)
refs=dict(target={'path':'target'},preparation={'path':'prep'});source={'code_hashes':{'code':'hash'}};environment={}
context=dict(execution_class='injected',cpu_family={'model':'cpu','architecture':'x'},allocation_family=dict(cluster='fixture',cpus=2,memory_bytes=100),storage={'target':{'filesystem':'fixture'},'preparation':{'filesystem':'fixture'}})
phase=dict(cache_scope='synthetic-fresh-process-contract',wall_seconds=1.,user_seconds=.5,system_seconds=.1,
 observed_io=dict(full_payload_reads=2,SHA_passes=2,parse_passes=1,freeze_passes=1,target_writes=0),
 process=dict(scope='process lifetime high-water RSS on Linux',pid=1,rss_bytes=1,peak_rss_bytes=2),
 cgroup=dict(applicable=False,scope='not applicable',reason='cgroup-v2-observations-unavailable'))
phases=dict(cold=phase,warm=dict(copy.deepcopy(phase),cache_scope='same-process-repeat'))
record=dict(kind='a3_prepared_target_receiver_resources_v1',references=refs,source_identity=source,reader_sha256='hash',freeze_sha256='hash',
 environment=environment,recipe='recipe',scope='scope',observed_io=phase['observed_io'],provenance=dict(normal_completion=True,exit_code=0,source_before=source['code_hashes'],source_after=source['code_hashes']),
 model_loaded=False,execution_authorized=False,retained_metadata_bytes_bound=20,extra_transient_bytes_bound=30,process_peak_rss_bytes_bound=1000,cgroup_peak_bytes_bound=1000,
 deployment=context,measurement=dict(kind='a3_receiver_measurement_v1',deployment=context,run_id='fixture',run_manifest_reference={'path':'run'},phases=phases))
run=dict(kind='a3_receiver_measurement_run_v1',run_id='fixture',normal_completion=True,exit_code=0,pid=1,injected=True,source_identity=source,reader_sha256='hash',freeze_sha256='hash',references=refs,environment=environment,recipe='recipe',scope='scope',deployment=context,source_before=source['code_hashes'],source_after=source['code_hashes'],allocation=dict(context['allocation_family'],job_id='1'),phases=phases)
env=dict(require=require,Path=Path,common=SimpleNamespace(file_hash=lambda _:'hash'),__file__='runtime',workload=SimpleNamespace(__file__='workload'),math=math,
 _PREPARED_RECIPE='recipe',_PREPARED_RESOURCE_SCOPE='scope',object_reference=lambda _:{'path':'run'},read_object=lambda _:run,
 _prepared_receiver_context=lambda *a,**k:context)
def load(path,names,namespace):
 tree=ast.parse(path.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)
load(c/'component_analysis/a3_direction_runtime.py',{'_validate_prepared_receiver_resources','_validate_prepared_measurement'},env)
load(c/'tests/test_a3_prepared_pilot_target.py',{'damage_receiver_evidence'},env)
kwargs=dict(references=refs,source_identity=source,environment=environment,actual_host_capacity=100,existing_host_obligations=50)
assert env['_validate_prepared_receiver_resources'](record,**kwargs)==dict(retained_metadata_bytes=20,extra_transient_bytes=30)
try:env['_validate_prepared_receiver_resources'](record,**dict(kwargs,actual_host_capacity=99))
except ValueError:pass
else:raise AssertionError('99 accepted')
legacy=dict(env);load(b/'plan/task23-green-r2-source-snapshot/component_analysis/a3_direction_runtime.py',{'_validate_prepared_receiver_resources'},legacy)
damages=['measurement','deployment','cold-wall','warm-cpu','process-scope','cgroup-scope','storage-family','allocation-family','cpu-family']
for damage in damages:
 value=copy.deepcopy(record);env['damage_receiver_evidence'](value,damage)
 assert legacy['_validate_prepared_receiver_resources'](value,**kwargs)==dict(retained_metadata_bytes=20,extra_transient_bytes=30)
 try:env['_validate_prepared_receiver_resources'](value,**kwargs)
 except ValueError:pass
 else:raise AssertionError(damage+' accepted')
print(json.dumps(dict(status='PASS',scope='extracted stdlib-only schema probe; no runtime/native suite',r2_accepts_gaps=9,r3_rejects_gaps=9,arithmetic_100_pass_99_reject=True,model_loaded=False)))
