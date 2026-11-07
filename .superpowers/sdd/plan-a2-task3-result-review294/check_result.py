from pathlib import Path
import hashlib,json,time,xml.etree.ElementTree as ET
s=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd');p=s/'plan-plan-a2-full-score-operational186/task3/green270-r4';d=s/'plan-a2-task3-deployment288';r=d/'run-01';old=s/'plan-a2-task3-deployment275/run-01'
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest();read=lambda x:json.loads(x.read_text());start=time.monotonic()
assert sha(p/'packet-pins.json')=='5cb997b946a30b1fccf2eec5c847e1caaee6251bbceb392979927e5f918fdd4e'
assert sha(p/'original-source-pins.json')=='af997a7cde132dbf5807e4f05e10a47352b5135ca1f3b084963c70047d469155'
for manifest in ['packet-pins.json','original-source-pins.json']:
 for name,h in read(p/manifest).items():
  assert sha(p/name if manifest=='packet-pins.json' else Path(name))==h,name
  assert time.monotonic()-start<25
inv=read(d/'root-terminal-inventory.json')
for f in inv['files']:
 path=Path(f['path']);assert path.stat().st_size==f['bytes'] and sha(path)==f['sha256']
assert len(inv['files'])==12 and inv['state']=='COMPLETED' and inv['exit_code']=='0:0' and inv['job_id']=='23635594'
manifest=read(r/'run_manifest.json');assert manifest['actual_job_id']=='23635594' and manifest['cluster']=='delta'
assert manifest['Slurm_env']==dict(SLURM_JOB_ID='23635594',SLURM_CPUS_PER_TASK='2',SLURM_MEM_PER_NODE='8192',SLURM_JOB_PARTITION='cpu-interactive')
result=read(r/'RESULT.json');assert result['complete'] is True and result['actual_model_or_GPU_authority'] is False
sets={};observations=[]
for env,pyver,pytest in [('base39','3.9.18','8.3.3'),('mgnp','3.12.13','9.1.1')]:
 identity=read(r/(env+'-identity.json'));assert identity['python'].startswith(pyver) and identity['pytest']==pytest and identity['optimize']==0
 for mode in ['RED','GREEN']:
  path=r/(env+'-'+mode+'.xml');cases=list(ET.parse(str(path)).getroot().iter('testcase'));previous=list(ET.parse(str(old/path.name)).getroot().iter('testcase'))
  names=[x.get('name') for x in cases];fails=[x.get('name') for x in cases if x.find('failure') is not None];passes=[x.get('name') for x in cases if x.find('failure') is None]
  assert len(names)==len(set(names))==(98 if mode=='RED' else 379)
  assert names==[x.get('name') for x in previous]
  assert not any(x.find('error') is not None or x.find('skipped') is not None for x in cases)
  if mode=='RED':
   assert len(fails)==61 and len(passes)==37
   assert fails==[x.get('name') for x in previous if x.find('failure') is not None]
  else:
   assert not fails
   assert len([n for n in names if n.startswith('test_original_native_normalizer_preserves_full_mapping_chain[')])==5
  sets[(env,mode)]=dict(names=names,failures=fails,passes=passes)
  obs=next(o for o in result['observations'] if o['environment']==env and o['mode']==mode)
  assert obs['junit_sha256']==sha(path) and obs['failed_names']==fails and obs['exit_code']==(1 if mode=='RED' else 0)
  assert obs['seconds']<(20 if mode=='RED' else 150) and '-I' not in obs['argv']
  observations.append(dict(environment=env,mode=mode,cases=len(names),failures=len(fails),passed=len(passes),seconds=obs['seconds']))
assert sets[('base39','RED')]==sets[('mgnp','RED')]
assert sets[('base39','GREEN')]==sets[('mgnp','GREEN')]
assert (d/'submitted-script.sh').read_bytes()==(p/'run_cpu.sh').read_bytes()
summary=dict(verdict='ACCEPT_TASK3_ONLY',job='23635594',sealed_files=12,observations=observations,ordered_cases_and_baseline_sets_match_previous=True,native_five_cases_all_pass=True,elapsed_seconds=time.monotonic()-start)
Path(__file__).with_name('checks.json').write_text(json.dumps(summary,indent=2)+'\n')
Path(__file__).with_name('baseline-named-sets.json').write_text(json.dumps(sets[('base39','RED')],indent=2)+'\n')
print(json.dumps(summary))
