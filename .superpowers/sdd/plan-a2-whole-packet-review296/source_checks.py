import ast,hashlib,json,time
from pathlib import Path
s=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd');p=s/'plan-a2-whole-packet289';start=time.monotonic()
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest();read=lambda x:json.loads(x.read_text())
assert sha(p/'packet-pins.json')=='298f049da3440ccfe020b36d2e9c24a7d2c7bbf6452f75bdc45426daff73df59'
for name,h in read(p/'packet-pins.json').items():assert sha(p/name)==h
meta=read(p/'dependencies.json');f=Path(meta['frozen_task3_packet'])
for name,key in [('packet-pins.json','task3_packet_pins_sha256'),('original-source-pins.json','task3_original_source_pins_sha256')]:
 assert sha(f/name)==meta[key]
 for path,h in read(f/name).items():
  assert sha(f/path if name=='packet-pins.json' else Path(path))==h,path
  assert time.monotonic()-start<25
manifest=read(p/'candidate/manifest.json')
assert len(manifest['unchanged_component_files'])==17
for path,h in manifest['unchanged_component_files'].items():assert sha(Path(path))==h
code=p/'candidate/tests/test_full_score_integration.py';tree=ast.parse(code.read_text());counts={}
for n in tree.body:
 if isinstance(n,ast.FunctionDef) and n.name.startswith('test_'):
  count=1
  for dec in n.decorator_list:
   if isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute) and dec.func.attr=='parametrize':count*=len(ast.literal_eval(dec.args[1]))
  counts[n.name]=count
assert sum(counts.values())==25
common=f/'closure/sdd/plan-a2-full-score-operational186/candidate/gpu/common.py';ct=ast.parse(common.read_text())
values={n.targets[0].id:ast.literal_eval(n.value) for n in ct.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['W','SOURCE']}
MAIN=values['W']+'/outputs/_analyses/specificity-ladder/a2-analysis/bridges-h100-G3-v1'
fn=next(n for n in ct.body if isinstance(n,ast.FunctionDef) and n.name=='validate_release')
probe=ast.FunctionDef(name='release_identity_prefix',args=fn.args,body=fn.body[:2],decorator_list=[],returns=None,type_comment=None)
ns=dict(C=dict(actual_job_id='456',reservation_id='new',resources={'CPUs':2}),MAIN=MAIN,SOURCE=values['SOURCE'],CONFIG='synthetic-config',sha=lambda x:'fixed')
def require(ok,msg):
 if not ok:raise ValueError(msg)
ns['require']=require
exec(compile(ast.fix_missing_locations(ast.Module(body=[probe],type_ignores=[])),'EXTRACTED_NO_NATIVE_IMPORT','exec'),ns)
r=dict(phase='full_score',full_scoring_admitted=True,actual_job_id='456',reservation_id='new',source_commit=values['SOURCE'],main_root='/temporary-fixture/MAIN',bound_config_sha256='fixed',resources={'CPUs':2})
try:ns['release_identity_prefix'](r)
except ValueError as error:assert str(error)=='release actual binding';observed=str(error)
else:raise AssertionError('expected fixed MAIN mismatch absent')
result=dict(verdict='NEEDS_FIXES_BEFORE_TASK4_CPU_READINESS',own_packet_members=len(read(p/'packet-pins.json')),unchanged_components=17,case_counts=counts,total_cases=25,MAIN_identity_prefix_rejection=observed,probe_scope='only first two original validate_release assertions; no application imports or filesystem reads',elapsed_seconds=time.monotonic()-start)
Path(__file__).with_name('checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
