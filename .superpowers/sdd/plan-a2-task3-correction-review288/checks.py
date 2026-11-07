from pathlib import Path
import ast,collections,hashlib,json,time,xml.etree.ElementTree as ET
s=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd');t=s/'plan-plan-a2-full-score-operational186/task3'
a=t/'green270-r3';b=t/'green270-r4';rel=Path('closure/sdd/plan-a2-full-score-operational186/candidate')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());dump=lambda x:ast.dump(x,include_attributes=False)
start=time.monotonic()
assert sha(b/'packet-pins.json')=='5cb997b946a30b1fccf2eec5c847e1caaee6251bbceb392979927e5f918fdd4e'
assert sha(b/'original-source-pins.json')=='af997a7cde132dbf5807e4f05e10a47352b5135ca1f3b084963c70047d469155'
counts={}
for name in ['packet-pins.json','original-source-pins.json']:
 pins=read(b/name)
 for path,h in pins.items():
  assert sha(b/path if name=='packet-pins.json' else Path(path))==h,path
  assert time.monotonic()-start<25
 counts[name]=len(pins)
changed=[str(p.relative_to(b/rel)) for p in (b/rel).rglob('*') if p.is_file() and sha(p)!=sha(a/rel/p.relative_to(b/rel))]
assert changed==['tests/test_full_score_root_integration.py']
assert sha(b/rel/'root/helper.py')=='522e6c9a87aaa041a2d63fb3218dd3637791ab859182d8619bc0a4ec0956d085'
file=Path(changed[0]);ta,tb=ast.parse((a/rel/file).read_text()),ast.parse((b/rel/file).read_text())
assert len(ta.body)==len(tb.body)
fn='test_original_native_normalizer_preserves_full_mapping_chain'
assert [getattr(x,'name',None) for x,y in zip(ta.body,tb.body) if dump(x)!=dump(y)]==[fn]
old=next(x for x in ta.body if getattr(x,'name',None)==fn);new=next(x for x in tb.body if getattr(x,'name',None)==fn)
aa=collections.Counter(dump(x) for x in ast.walk(old) if isinstance(x,ast.Assert));ba=collections.Counter(dump(x) for x in ast.walk(new) if isinstance(x,ast.Assert))
assert not aa-ba and sum(aa.values())==7 and sum(ba.values())==10
assert [dump(x) for x in old.decorator_list]==[dump(x) for x in new.decorator_list]
assert (a/'run_cpu_green.py').read_bytes()==(b/'run_cpu_green.py').read_bytes()
assert (a/'resources.json').read_bytes()==(b/'resources.json').read_bytes()
assert (b/'run_cpu.sh').read_text()==(a/'run_cpu.sh').read_text().replace('/task3/green270-r3','/task3/green270-r4')
xmlcounts={}
for env in ['base39','mgnp']:
 for mode in ['RED','GREEN']:
  cases=list(ET.parse(str(s/'plan-a2-task3-deployment275/run-01'/(env+'-'+mode+'.xml'))).getroot().iter('testcase'))
  fails=[x for x in cases if x.find('failure') is not None]
  assert len(cases)==(98 if mode=='RED' else 379) and len(fails)==(61 if mode=='RED' else 5)
  assert not any(x.find('error') is not None or x.find('skipped') is not None for x in cases)
  if mode=='GREEN':assert all("KeyError: 'groups_file_sha256'" in x.find('failure').get('message','') for x in fails)
  xmlcounts[env+'-'+mode]=dict(cases=len(cases),failed=len(fails))
result=dict(verdict='READY_FOR_BOUNDED_COMPLETE_CPU_VALIDATION_ONLY',pin_counts=counts,changed=changed,native_assertions_before=7,native_assertions_after=10,parametrization_unchanged=True,wrapper_and_resources_match=True,old_XML_counts=xmlcounts,elapsed_seconds=time.monotonic()-start)
Path(__file__).with_name('checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
