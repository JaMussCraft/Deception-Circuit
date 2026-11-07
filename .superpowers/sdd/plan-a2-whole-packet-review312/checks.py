from pathlib import Path
import ast,collections,hashlib,json,time,xml.etree.ElementTree as ET
s=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd');b=s/'plan-a2-whole-packet-correction312';p=b/'packet-r3';old=s/'plan-a2-whole-packet289-r2';start=time.monotonic()
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest();read=lambda x:json.loads(x.read_text());dump=lambda x:ast.dump(x,include_attributes=False)
assert sha(p/'packet-pins.json')=='4300cdabd1b612e228761b7b4ea204a023ff29121c5ddcd265cb211345ab4761'
assert sha(p/'candidate/tests/test_full_score_integration.py')=='fba62e22db8562a3807de1c73670bb549469583097dca50d5d9641c91668adbd'
for name,h in read(p/'packet-pins.json').items():assert sha(p/name)==h
meta=read(p/'dependencies.json');f=Path(meta['frozen_task3_packet'])
for name,key in [('packet-pins.json','task3_packet_pins_sha256'),('original-source-pins.json','task3_original_source_pins_sha256')]:
 assert sha(f/name)==meta[key]
 for path,h in read(f/name).items():
  assert sha(f/path if name=='packet-pins.json' else Path(path))==h,path
  assert time.monotonic()-start<25
cm=read(b/'correction-manifest.json');assert len(cm['original_component_files'])==17
for name,h in cm['original_component_files'].items():assert sha(Path(name))==h
for row in cm['actual_failed_evidence'].values():assert sha(Path(row['path']))==row['sha256']
a=ast.parse((old/'candidate/tests/test_full_score_integration.py').read_text());t=ast.parse((p/'candidate/tests/test_full_score_integration.py').read_text());funcs=lambda tr:{n.name:n for n in tr.body if isinstance(n,ast.FunctionDef)};aa,bb=funcs(a),funcs(t)
for name,n in aa.items():
 if not name.startswith('test_'):continue
 assert [dump(x) for x in n.decorator_list]==[dump(x) for x in bb[name].decorator_list]
 assertions=lambda node:collections.Counter(dump(x) for x in ast.walk(node) if isinstance(x,ast.Assert))
 assert not assertions(n)-assertions(bb[name]),name
counts={}
for name,n in bb.items():
 if not name.startswith('test_'):continue
 count=1
 for dec in n.decorator_list:
  if isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute) and dec.func.attr=='parametrize':count*=len(ast.literal_eval(dec.args[1]))
 counts[name]=count
assert sum(counts.values())==33
assert "assert 'stage' in j.events" in ast.unparse(bb['test_transfer_failure_cannot_cross_score_boundary'])
assert "monkeypatch.chdir(str(SOURCE))" in ast.unparse(bb['native_modules'])
# Replay only the unchanged raw copy guard against preserved actual failed bytes.
helper=f/'closure/sdd/plan-a2-full-score-operational186/candidate/root/helper.py';tree=ast.parse(helper.read_text());capture=funcs(tree)['capture_cpu']
node=next(n for n in capture.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and any(isinstance(x,ast.Constant) and x.value=='CPU immutable WAITING copy' for x in n.value.args))
code=compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'EXTRACTED_ORIGINAL_RAW_GUARD','exec')
def need(ok,msg):
 if not ok:raise ValueError(msg)
diag=read(b/'evidence/diagnosis.json');seen=0
for row in diag['observations']:
 actual=Path(row['marker']).read_bytes();prior=Path(row['CPU_copy']).read_bytes();r=read(Path(row['request']));root=Path(row['CPU_copy']).parent;key=str(root/'WAITING.json')
 assert json.loads(actual)==json.loads(prior) and actual!=prior
 ns=dict(need=need,sha_bytes=lambda x:hashlib.sha256(x).hexdigest(),root=root,r=r,files={key:actual})
 exec(code,ns)
 for bad in [prior,actual+b' ']:
  ns['files'][key]=bad
  try:exec(code,ns)
  except ValueError as error:assert str(error)=='CPU immutable WAITING copy'
  else:raise AssertionError('raw guard accepted changed bytes')
 seen+=1
assert seen==26
result=dict(verdict='SOURCE_READY_FOR_BOUNDED_CPU_DIAGNOSTIC_ONLY',packet_members=len(read(p/'packet-pins.json')),components_unchanged=17,original32_assertions_and_parameters_preserved=True,cases=33,actual_failed_marker_sets_replayed=seen,exact_bytes_accept_semantic_copies_and_tamper_reject=True,stage_reach_assertion=True,source_cwd_preserved=True,elapsed_seconds=time.monotonic()-start)
Path(__file__).with_name('checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
