"""Bounded source-bound probes. No native modules, model, scheduler or proof."""
import ast,hashlib,importlib.util,json,pathlib,tempfile
S=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd');W=S.parents[1];C=S/'plan-a2-full-score-operational186/candidate';SRC='50e947bb852613e3a270082651f2bd1b7bb0c525'
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,str(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
sup=module('independent224supervisor',C/'cpu/supervisor.py');v=module('independent224native',C/'cpu/validate-phase.py');tree=ast.parse((C/'gpu/common.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='gpu_release');statement=next(n for n in fn.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='write' and isinstance(n.value.args[0],ast.Name) and n.value.args[0].id=='waiting')
c=dict(phase='full_score',source_commit=SRC,standing_CPU_job_id='123',packet_manifest_sha256='1'*64,GPU_packet_manifest_sha256='5'*64,frozen_G3_sha256='2'*64,bank_file_sha256='3'*64,bank_manifest_sha256='4'*64,child_cap_seconds=240,CPU_finish_margin_seconds=20,publication_margin_seconds=15)
r=dict(phase='full_score',standing_CPU_job_id='123',standing_packet_manifest_sha256='1'*64,accepted_source_commit=SRC,frozen_G3_sha256='2'*64,bank_file_sha256='3'*64,bank_manifest_sha256='4'*64,GPU_packet_manifest_sha256='5'*64,actual_future_GPU_job_id='456',final_GPU_bound_config_sha256='6'*64,root_trigger_issued_at=1005.,GPU_WAITING_requested_at=1000.)
config=dict(actual_job_id='456',groups_file_sha256='2'*64,bank_file_sha256='3'*64,bank_manifest_sha256='4'*64,bank_internal_payload_sha256='7'*64,launch_packet_manifest_sha256='5'*64,resources={})
with tempfile.TemporaryDirectory() as td:
 waiting=pathlib.Path(td)/'WAITING-full_score.json';ns=dict(C=config,SOURCE=SRC,sha=lambda _:'6'*64,CONFIG='fixture',waiting=waiting,requested=1000.,publication_end=1285.,write=sup.write)
 exec(compile(ast.fix_missing_locations(ast.Module(body=[statement],type_ignores=[])),str(C/'gpu/common.py'),'exec'),ns);marker=json.loads(waiting.read_text());errors={}
 for name,call in [('validate_request',lambda:sup.validate_request(c,r,marker,now=1010.)),('child_deadline',lambda:sup.child_deadline(c,marker,2000.,1900.,now=1010.))]:
  try:call()
  except Exception as e:errors[name]=repr(e)
 assert errors=={'validate_request':"KeyError('packet_manifest_sha256')",'child_deadline':"KeyError('deadline_unix')"}
# Reproduce exact original manifest's alias rejection before any dataset bytes read.
h=W/'.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103/root-H100-R5/job-50189932';hc=json.loads((h/'config.json').read_text());mp=pathlib.Path(hc['input_manifest']);raw=mp.read_bytes();assert hashlib.sha256(raw).hexdigest()==hc['input_manifest_sha256'];manifest=json.loads(raw);current={}
for n in v.CATALOGUES:
 p=v.REMOTE+n[len(v.ALIGNMENT):];row=dict(virtual=n,physical=p,bytes=0,sha256=hashlib.sha256(b'').hexdigest())
 for label,cluster,path,at in [('delta_capture','delta',n,1000),('remote','bridges2',p,1001),('delta_reread','delta',n,1002)]:row[label]=dict(cluster=cluster,path=path,bytes=0,sha256=row['sha256'],observed_unix=at)
 current[n]=row
try:v.verify_input_closure(manifest,current,read_bytes=lambda _:(_ for _ in ()).throw(AssertionError('unexpected data read')))
except ValueError as e:alias_error=str(e)
assert alias_error=='exact corrected422 plus five aliases' and len(manifest['namespace_aliases'])==11
# Compare actual consumer key accesses with all fields actually emitted by the producer functions.
def func(path,name):return next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
consumer=func(C/'gpu/common.py','validate_release');required=set()
for n in ast.walk(consumer):
 if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=='cpu':
  k=n.slice
  if isinstance(k,ast.Constant):required.add(k.value)
def emitted(fn):
 result=set()
 for n in ast.walk(fn):
  if isinstance(n,ast.Return) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='dict':result.update(k.arg for k in n.value.keywords if k.arg)
 return result
fields=set()
for name in ['validate_full_score','validate_native_context','validate_domain_identity']:fields|=emitted(func(C/'cpu/validate-phase.py',name))
fields|={'complete','kind','status','standing_packet_manifest_sha256','final_GPU_bound_config_sha256','GPU_packet_manifest_sha256','guard_result_sha256','supervisor_finished_unix','deadline_unix','automatic_retry','CPU_bound_config_sha256','parameters_sha256','child_execution_sha256'}
missing=sorted(required-fields)
assert 'timely_window' in missing and 'full_rows' in missing and 'waiting_sha256' in missing
command=func(S/'plan-plan-a2-full-score-operational186/task2/green/run_cpu_green.py','command');literals={n.value for n in ast.walk(command) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
assert 'test_full_score_entry198.py' not in literals
print(json.dumps(dict(actual_Task1_WAITING_keys=sorted(marker),Task2_consumption_errors=errors,original_input_manifest_sha256=hc['input_manifest_sha256'],ordinary_count=len(manifest['ordinary_files']),actual_alias_count=len(manifest['namespace_aliases']),alias_rejection=alias_error,Task1_required_CPU_fields=sorted(required),missing_Task2_COMPLETE_fields=missing,GREEN_test_files=sorted(x for x in literals if x.endswith('.py')),GREEN_expected=204,GREEN_effective_scope=189),indent=2))
