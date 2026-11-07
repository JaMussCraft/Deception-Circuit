from pathlib import Path
import ast,collections,hashlib,json,xml.etree.ElementTree as ET,time
S=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd');V=S/'plan-a2-whole-packet-review327';P=S/'plan-a2-whole-packet-correction327/packet-r5';OLD=S/'plan-a2-whole-packet-correction321/packet-r4';R=S/'plan-a2-task4-deployment324/run-01'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
dump=lambda n:ast.dump(n,include_attributes=False)
assert sha(P/'packet-pins.json')=='9a5129f6c3fae0455c706a6077ac04047c5062f7abbea0f98018113da1f7e571'
pins=read(P/'packet-pins.json');oldpins=read(OLD/'packet-pins.json');assert set(pins)==set(oldpins)
for root,ps in [(P,pins),(OLD,oldpins)]:
 for n,h in ps.items():assert sha(root/n)==h,n
f='candidate/tests/test_full_score_integration.py';assert sha(P/f)=='b480636a8712de573916a4e9b438a82983156cebf180d36d0ed7429a4648ab03'
a,b=ast.parse((OLD/f).read_text()),ast.parse((P/f).read_text());fa={n.name:n for n in a.body if isinstance(n,ast.FunctionDef)};fb={n.name:n for n in b.body if isinstance(n,ast.FunctionDef)};assert set(fa)==set(fb)
changed=[n for n in fa if dump(fa[n])!=dump(fb[n])];assert changed==['test_whole_chain_normal_native_full_publication','test_transfer_failure_cannot_cross_score_boundary']
cases=0
for n in fa:
 assert [dump(x) for x in fa[n].decorator_list]==[dump(x) for x in fb[n].decorator_list]
 before=collections.Counter(dump(x) for x in ast.walk(fa[n]) if isinstance(x,ast.Assert));after=collections.Counter(dump(x) for x in ast.walk(fb[n]) if isinstance(x,ast.Assert));assert not before-after,n
 if n.startswith('test_'):
  count=1
  for d in fb[n].decorator_list:
   if isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and d.func.attr=='parametrize':count*=len(ast.literal_eval(d.args[1]))
  cases+=count
assert cases==33
assert [dump(n) for n in a.body if not isinstance(n,ast.FunctionDef)]==[dump(n) for n in b.body if not isinstance(n,ast.FunctionDef)]
manifest=read(P/'candidate/manifest.json');production=manifest['unchanged_component_files'];assert len(production)==17
for n,h in production.items():assert sha(n)==h,n
for n in ['run_cpu.py','source_checks.py','candidate/root-release-contract.json']:assert (P/n).read_bytes()==(OLD/n).read_bytes(),n
assert (P/'run_cpu.sh').read_text()==(OLD/'run_cpu.sh').read_text().replace(str(OLD),str(P))
expected_failed={'test_whole_chain_normal_native_full_publication','test_transfer_failure_cannot_cross_score_boundary[catalogue]'};actual=[]
result=read(R/'RESULT.json');assert result['complete'] is False and result['status']=='FAIL'
for x in result['observations']:
 label=x['environment'];xml=R/(label+'.xml');assert sha(xml)==x['junit_sha256'];cs=list(ET.parse(xml).getroot().iter('testcase'))
 assert len(cs)==33 and {c.get('name') for c in cs if c.find('failure') is not None}==expected_failed
 assert not any(c.find('error') is not None or c.find('skipped') is not None for c in cs)
 for c in cs:
  z=c.find('failure')
  if z is not None:
   text=''.join(z.itertext());assert ('score already exists or is symlink' if c.get('name').startswith('test_whole') else 'ordinary input changed: ') in text
 assert x['exit_code']==1 and x['passed']==31 and not x['complete']
 actual.append(dict(environment=label,passed=31,failed=2,errors=0,skips=0,observer_elapsed=x['elapsed_seconds'],pytest_seconds=float(ET.parse(xml).getroot().find('testsuite').get('time')),timeout_margin=1650-x['elapsed_seconds']))
# Replay only original prefix/predicate against retained actual test paths.
C=Path(next(iter(production))).parent
C=S/'plan-plan-a2-full-score-operational186/task3/green270-r4/closure/sdd/plan-a2-full-score-operational186/candidate'
common=ast.parse((C/'gpu/common.py').read_text());helper=ast.parse((C/'root/helper.py').read_text());fn=lambda tree,name:next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
def require(ok,msg):
 if not ok:raise ValueError(msg)
observed=[]
for label in ['base39','mgnp']:
 d=R/(label+'-tmp');normal=[p for p in d.glob('test_whole_chain_normal_*') if not p.is_symlink()];assert len(normal)==1
 ns=dict(Path=Path,c={'main_root':str(normal[0]/'MAIN')},allow_score=False,require=require)
 try:exec(compile(ast.Module(body=fn(common,'_bank_binding').body[:3],type_ignores=[]),'REVIEW_ORIGINAL_SCORE_PREFIX','exec'),ns)
 except ValueError as e:assert str(e)=='score already exists or is symlink'
 else:raise AssertionError('missing original existing-score rejection')
 case=d/'test_transfer_failure_cannot_c0';cfg=read(case/'evidence/bound-config.json');proof=read(cfg['input_manifest']);name=cfg['minimum_registry_paths'][0]
 loop=next(n for n in fn(common,'input_closure').body if isinstance(n,ast.For));predicate=next(n for n in loop.body if isinstance(n,ast.Expr));ns=dict(path=Path(name),digest=proof['ordinary_sha256'][name],sha=sha,name=name,require=require)
 try:exec(compile(ast.Module(body=[predicate],type_ignores=[]),'REVIEW_ORIGINAL_INPUT_PREDICATE','exec'),ns)
 except ValueError as e:assert str(e)=='ordinary input changed: '+name
 else:raise AssertionError('missing original retained catalogue rejection')
 observed.append(label)
claim=V/'pure-existing.claim';claim.write_bytes(b'original retained claim');prior=claim.read_bytes();ns=dict(Path=Path);exec(compile(ast.Module(body=[fn(helper,'exclusive')],type_ignores=[]),'REVIEW_ORIGINAL_EXCLUSIVE','exec'),ns)
try:ns['exclusive'](claim,b'replace forbidden')
except FileExistsError as e:assert e.filename==str(claim)
else:raise AssertionError('exclusive did not reject')
assert claim.read_bytes()==prior
proposal=read(P/'candidate/proposal.json')['CPU_test_proposal'];assert proposal['CPUs']==2 and proposal['RAM_bytes']==16*1024**3 and proposal['GPUs']==0 and proposal['per_environment_timeout_seconds']==1650 and proposal['walltime_seconds']==3600;assert proposal['actual_job_id'] is None and proposal['actual_resources'] is None
summary=dict(passed=True,packet_pins_sha256=sha(P/'packet-pins.json'),test_sha256=sha(P/f),changed_test_functions=changed,original_assertions_decorators_module_statements_preserved=True,total_cases=cases,production_components_unchanged=17,packet_members=len(pins),original_observer_bytes_unchanged=True,actual_red=actual,extracted_original_guards_reproduced=observed,exclusive_claim_bytes_preserved=True,native_imports=False,pytest_runs=0,new_full_path_measured=False,resource_proposal=dict(CPUs=2,RAM_bytes=16*1024**3,wall_seconds=3600,environment_cap=1650,dual_cap=3300,nominal_observer_headroom=300),metadata_qualification='Inherited memory_qualification says failed run never retained full score graphs. Actual normal full score was constructed/published/audited before failure; only mutation-copy plus reloaded-score coexistence and three subsequent audits remain unmeasured. MGNP pending-at-diagnosis context is historical; final runtime is recorded here.')
(V/'checks.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
