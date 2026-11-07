from pathlib import Path
from types import SimpleNamespace
import ast,collections,hashlib,json,time
s=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd');p=s/'plan-a2-whole-packet289-r2';old=s/'plan-a2-whole-packet289'
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest();read=lambda x:json.loads(x.read_text());dump=lambda x:ast.dump(x,include_attributes=False);start=time.monotonic()
assert sha(p/'packet-pins.json')=='7dc299d5f9662b81dd90289f7a1369b0d6bc63f130027d4469895628cf1cfec7'
assert sha(p/'candidate/tests/test_full_score_integration.py')=='f60fafe49d5d3f14f226c7a6286cd7a8ce54153d4cd9b454ff4b0a080f25e9fa'
for name,h in read(p/'packet-pins.json').items():assert sha(p/name)==h
meta=read(p/'dependencies.json');f=Path(meta['frozen_task3_packet'])
for name,key in [('packet-pins.json','task3_packet_pins_sha256'),('original-source-pins.json','task3_original_source_pins_sha256')]:
 assert sha(f/name)==meta[key]
 for path,h in read(f/name).items():
  assert sha(f/path if name=='packet-pins.json' else Path(path))==h,path
  assert time.monotonic()-start<25
members=read(p/'candidate/manifest.json')['unchanged_component_files'];assert len(members)==17
for name,h in members.items():assert sha(Path(name))==h
prior=ast.parse((old/'candidate/tests/test_full_score_integration.py').read_text());current=ast.parse((p/'candidate/tests/test_full_score_integration.py').read_text())
funcs=lambda t:{n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
a,b=funcs(prior),funcs(current);counts={}
for name,node in b.items():
 if not name.startswith('test_'):continue
 count=1
 for dec in node.decorator_list:
  if isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute) and dec.func.attr=='parametrize':count*=len(ast.literal_eval(dec.args[1]))
 counts[name]=count
for name,node in a.items():
 if not name.startswith('test_'):continue
 assert [dump(n) for n in node.decorator_list]==[dump(n) for n in b[name].decorator_list]
 orig=collections.Counter(dump(n) for n in ast.walk(node) if isinstance(n,ast.Assert));new=collections.Counter(dump(n) for n in ast.walk(b[name]) if isinstance(n,ast.Assert));assert not orig-new,name
assert sum(counts.values())==32
# Exercise only extracted MAIN routing plus original release identity prefix.
common=ast.parse((f/'closure/sdd/plan-a2-full-score-operational186/candidate/gpu/common.py').read_text());native=funcs(common)['validate_release']
fn=ast.FunctionDef(name='release_prefix',args=native.args,body=native.body[:2],decorator_list=[],returns=None,type_comment=None)
MAIN=meta['alignment_root']+'/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-analysis/bridges-h100-G3-v1';tmp='/synthetic/MAIN'
g=dict(main_root=tmp,actual_job_id='456',reservation_id='new',resources={'CPUs':2})
guard=SimpleNamespace(S=meta['original_runtime'],SOURCE=meta['original_source_commit'],MAIN=MAIN,C=g,full_score_command=lambda x:['bash','fixed','--work-dir',x['main_root']])
ns=dict(SOURCE=Path(meta['original_runtime']),META=meta)
exec(compile(ast.fix_missing_locations(ast.Module(body=[b['route_main']],type_ignores=[])),'EXTRACTED_ROUTE','exec'),ns)
ns['route_main'](guard,g,SimpleNamespace(setattr=setattr))
assert guard.MAIN==tmp and guard.S==meta['original_runtime']
def require(ok,msg):
 if not ok:raise ValueError(msg)
ns=dict(C=g,MAIN=guard.MAIN,SOURCE=meta['original_source_commit'],CONFIG='synthetic',sha=lambda _: 'fixed',require=require)
exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'EXTRACTED_RELEASE_PREFIX','exec'),ns)
r=dict(phase='full_score',full_scoring_admitted=True,main_root=tmp,actual_job_id='456',reservation_id='new',source_commit=meta['original_source_commit'],bound_config_sha256='fixed',resources=g['resources'])
ns['release_prefix'](r);r['main_root']='/wrong'
try:ns['release_prefix'](r)
except ValueError as error:assert str(error)=='release actual binding'
else:raise AssertionError('wrong MAIN accepted')
assert 'return original()' in ast.unparse(b['restore_root_gates'])
assert 'real_verify(b, g, c)' in ast.unparse(b['restore_root_gates'])
assert 'return real_reviewed_admission()' in ast.unparse(b['consumer'])
assert not any("setattr(guard, '"+n+"', lambda" in ast.unparse(b['consumer']) for n in ['reviewed_admission','packet','input_closure'])
proposal=read(p/'candidate/proposal.json');q=proposal['CPU_test_proposal'];assert q['new_cases']==32 and q['CPUs']==2 and q['RAM_bytes']==17179869184 and q['walltime_seconds']==900 and q['per_environment_timeout_seconds']==360
assert proposal['operational_feasible'] is None and proposal['actual_operational_admission'] is None
result=dict(verdict='SOURCE_READY_FOR_BOUNDED_ROOT_CPU_VALIDATION_ONLY',own_members=len(read(p/'packet-pins.json')),unchanged_components=17,total_cases=32,original_test_assertions_and_decorators_preserved=True,delegating_spies_present=True,extracted_MAIN_positive_and_wrong_MAIN_rejection=True,source_runtime_unchanged=True,elapsed_seconds=time.monotonic()-start)
Path(__file__).with_name('checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
