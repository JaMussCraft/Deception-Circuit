import ast,hashlib,json,subprocess,time
from pathlib import Path
s=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd')
d=s/'plan-a3/validation-correction282'
pairs=[(s/'plan-a3/direction-preallocation-candidate183/component_analysis/a3_direction_runtime.py',d/'component_analysis/a3_direction_runtime.py','_completed_pilot_source','aea07dbf153824f373be70629dd24edc28dd6566cafa5955f43c69fd1119ec90','1d6c3886a7634641a8a4ad64135adeef34dcdac7ce6b388e8441df1bf2cea116'),(s/'plan/task23-green-r6-r2-sharded/suite/test_a3_prepared_pilot_target.py',d/'tests/test_a3_prepared_pilot_target.py','test_prepared_costs_and_envelope_are_charged','e2a7c5622508974fafafe016e9c3d1d55903302f646f05c5f35630570a1f6e86','2f89de3edb0ac5d513b98c018c6ab1393179b73d9ee67c64d725a064eaa09fb3')]
dump=lambda n:ast.dump(n,include_attributes=False)
records=[]
for old,new,allowed,oh,nh in pairs:
 a,b=old.read_bytes(),new.read_bytes()
 assert hashlib.sha256(a).hexdigest()==oh and hashlib.sha256(b).hexdigest()==nh
 ta,tb=ast.parse(a),ast.parse(b)
 assert len(ta.body)==len(tb.body)
 changed=[getattr(x,'name',None) for x,y in zip(ta.body,tb.body) if dump(x)!=dump(y)]
 assert changed==[allowed]
 aa=[dump(n) for n in ast.walk(ta) if isinstance(n,ast.Assert)]
 ba=[dump(n) for n in ast.walk(tb) if isinstance(n,ast.Assert)]
 assert aa==ba
 decorators=lambda t:[(n.name,[dump(x) for x in n.decorator_list]) for n in ast.walk(t) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
 assert decorators(ta)==decorators(tb)
 records.append(dict(changed=changed,assertions=len(aa),decorators_unchanged=True,hashes_match=True))
observed=[]
for py in ['/sw/external/python/anaconda3/bin/python3.9','/u/swong2/.conda/envs/mgnp/bin/python']:
 for mode in ['red','green']:
  result=subprocess.run([py,'-B',str(d/'pure_probe.py'),mode],capture_output=True,text=True,timeout=8)
  payload=json.loads(result.stdout)
  assert result.returncode==(1 if mode=='red' else 0)
  assert len(payload['failures'])==(9 if mode=='red' else 0)
  observed.append(dict(python=py,mode=mode,exit=result.returncode,result=payload))
result=dict(scope='independent AST/hash and extracted boundary only; no native imports',files=records,probes=observed)
Path(__file__).with_name('checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
