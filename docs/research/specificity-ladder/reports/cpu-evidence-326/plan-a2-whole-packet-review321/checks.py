from pathlib import Path
import ast,collections,copy,hashlib,json,time
s=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd');b=s/'plan-a2-whole-packet-correction321';p=b/'packet-r4';old=s/'plan-a2-whole-packet-correction312/packet-r3';start=time.monotonic()
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest();read=lambda x:json.loads(Path(x).read_text());dump=lambda n:ast.dump(n,include_attributes=False)
assert sha(p/'packet-pins.json')=='88407b1745c6169afbf75de0d3789e5d10cb55cda88c4134580af58f6d1e679c'
assert sha(p/'candidate/tests/test_full_score_integration.py')=='c72af7507f19b79b9cf068e286048950bf0824b0b0308a2e14458d9f4064baca'
for name,h in read(p/'packet-pins.json').items():assert sha(p/name)==h
meta=read(p/'dependencies.json');f=Path(meta['frozen_task3_packet'])
for name,key in [('packet-pins.json','task3_packet_pins_sha256'),('original-source-pins.json','task3_original_source_pins_sha256')]:
 assert sha(f/name)==meta[key]
 for path,h in read(f/name).items():
  assert sha(f/path if name=='packet-pins.json' else Path(path))==h,path
  assert time.monotonic()-start<25
cm=read(b/'correction-manifest.json');assert len(cm['original17_components'])==17
for name,h in cm['original17_components'].items():assert sha(name)==h
for row in cm['failed315_raw_files'].values():assert sha(row['path'])==row['sha256']
support=meta['accepted_support_evidence'];assert sha(support['path'])==support['sha256'];assert read(support['path'])['verified']['support_reason_mask_sha256']==meta['accepted_native_support_reason_mask_sha256']
funcs=lambda t:{n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
a=funcs(ast.parse((old/'candidate/tests/test_full_score_integration.py').read_text()));tt=ast.parse((p/'candidate/tests/test_full_score_integration.py').read_text());z=funcs(tt);counts={}
for name,n in a.items():
 if not name.startswith('test_'):continue
 assert [dump(d) for d in n.decorator_list]==[dump(d) for d in z[name].decorator_list]
 aa=collections.Counter(dump(q) for q in ast.walk(n) if isinstance(q,ast.Assert));bb=collections.Counter(dump(q) for q in ast.walk(z[name]) if isinstance(q,ast.Assert));assert not aa-bb,name
for name,n in z.items():
 if not name.startswith('test_'):continue
 count=1
 for dec in n.decorator_list:
  if isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute) and dec.func.attr=='parametrize':count*=len(ast.literal_eval(dec.args[1]))
 counts[name]=count
assert sum(counts.values())==33
# Replay unchanged final lineage predicate against preserved failure bytes only.
helper=ast.parse((f/'closure/sdd/plan-a2-full-score-operational186/candidate/root/helper.py').read_text());auth=funcs(helper)['authenticate_cutover'];node=next(n for n in auth.body if isinstance(n,ast.If)).body[0]
code=compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'EXTRACTED_ORIGINAL_ANCHOR','exec')
def need(ok,msg):
 if not ok:raise ValueError(msg)
diag=read(cm['diagnosis318']['path']);pairs=diag['lineage']['pairs'];seen=[]
for env in ['base39','mgnp']:
 pair=next(x for x in pairs if x['environment']==env);value=read(pair['cutover_path']);normalized=dict(active_mapping_reference=value['active_mapping_reference'],mapping_lineage_references=value['mapping_lineage_references'],original_snapshot_path=pair['active_snapshot'])
 ns=dict(need=need,sha=sha,value=copy.deepcopy(value),normalized=normalized)
 try:exec(code,ns)
 except ValueError:pass
 else:raise AssertionError('old anchor accepted')
 ns['value']['ledger_sha256']=sha(pair['active_snapshot']);exec(code,ns);seen.append(env)
result=dict(verdict='SOURCE_READY_FOR_BOUNDED_ROOT_CPU_VALIDATION_ONLY',packet_pins_sha256=sha(p/'packet-pins.json'),test_sha256=sha(p/'candidate/tests/test_full_score_integration.py'),packet_members=len(read(p/'packet-pins.json')),production_components_unchanged=17,original33_cases_assertions_parameters_preserved=True,original_cutover_predicate_rejects_old_accepts_active_anchor=seen,support_evidence_bound=True,elapsed_seconds=time.monotonic()-start)
Path(__file__).with_name('checks.json').write_text(json.dumps(result,indent=2)+'\n');Path(__file__).with_name('verdict.json').write_text(json.dumps(dict(result,Task4_accepted=False,native_execution_observed=False,GPU_permission=False,operational_feasible=None),indent=2)+'\n');print(json.dumps(result))
