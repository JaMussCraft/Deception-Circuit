import json,pathlib,hashlib,subprocess,shlex,base64,time,sys
A=pathlib.Path('/projects/beto/swong2/Alignment');W=A/'Deception-Circuit/.claude/worktrees/specificity-ladder';B=W/'.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199';O=B/'root-genuine-proof-r5-ops';O.mkdir(exist_ok=True)
RA='/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment';RB=RA+'/'+str(B.relative_to(A));M='f12141b3b301d359dd7cf952ee47445b3bc637c31e9c4020c17da81cf268b26f';D='9631dbf0c26f3576bda79787d1f1b6b8de89ffd8b19cfced0cf156bf917e5862';V=W/'.superpowers/sdd/plan-a2-proof-resource-review238/verdict.json';VS='8c684e2dca9a2ff49cb7842daad401d89720fe2bf1b5c79492edd80d10e6d7ba'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,x):
 with (O/n).open('x') as f:json.dump(x,f,indent=2)
def remote(n,code,x):
 cmd=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)]
 r=subprocess.run(cmd,input=json.dumps(x),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=90)
 save(n,{'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'observed_unix':time.time()})
 if r.returncode:print(r.stdout,r.stderr);r.check_returncode()
 return json.loads(r.stdout)
if sys.argv[1]=='stage':
 p=B/'proof-adapter-r5';assert sha((p/'manifest.json').read_bytes())==M;manifest=json.loads((p/'manifest.json').read_text())
 files=[p/n for n,h in manifest.items() if sha((p/n).read_bytes())==h];assert len(files)==37
 files += [p/'manifest.json',B/'root-proof-dispatch237/dispatch.sh',B/'root-proof-dispatch237/test_dispatch.py',V]
 assert sha(V.read_bytes())==VS and sha((B/'root-proof-dispatch237/dispatch.sh').read_bytes())==D
 rows=[]
 for f in files:
  b=f.read_bytes();rows.append({'virtual':str(f),'physical':RA+'/'+str(f.relative_to(A)),'sha256':sha(b),'bytes':len(b),'base64':base64.b64encode(b).decode()})
 save('deployment-inventory.json',[{k:v for k,v in r.items() if k!='base64'} for r in rows])
 code='''import sys,json,base64,hashlib,time,os
from pathlib import Path
x=json.load(sys.stdin);seen=[]
for row in x:
 p=Path(row['physical']);raw=base64.b64decode(row['base64']);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'];p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.is_symlink()
 if p.exists():assert p.read_bytes()==raw,str(p)
 else:
  with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'];seen.append({k:v for k,v in row.items() if k!='base64'})
print(json.dumps({'files':seen,'observed_unix':time.time()}))
'''
 result=remote('stage-readback.json',code,rows);print('staged',len(result['files']))
elif sys.argv[1]=='check':
 old=json.loads((B/'root-genuine-proof-r4-ops/host-and-scheduler-checks.json').read_text());code=shlex.split(old['command'][-1])[-1]
 code=code.replace('proof-adapter-r4','proof-adapter-r5').replace('root-proof-dispatch227','root-proof-dispatch237').replace('94a104fa5db26251b1f565baea61cf59b6e632ea453a0232ace01903ef8fecc0',M).replace('da3fd6aac9356a685410afd3800c824988ac90c4e0a60dfcbe63707382f9cddb',D)
 argv=json.loads((B/'root-genuine-proof-r4-ops/submission-argv.json').read_text());argv=[s.replace('root-proof-dispatch227','root-proof-dispatch237').replace('lad-A2-proof-r4','lad-A2-proof-r5') for s in argv];save('submission-argv.json',argv)
 x={'root':RB,'review_path':RA+'/'+str(V.relative_to(A)),'review':base64.b64encode(V.read_bytes()).decode(),'review_sha':VS,'submit':argv}
 result=remote('host-and-scheduler-checks.json',code,x);print(json.dumps(result))
elif sys.argv[1]=='submit':
 code='''import json,subprocess,sys,time
from pathlib import Path
x=json.load(sys.stdin);ops=Path(x['ops']);ops.mkdir(exist_ok=False);a=x['argv'];assert '--hold' in a
with(ops/'submission-intent.json').open('x') as f:json.dump({'argv':a,'observed_unix':time.time()},f)
r=subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=30);v={'argv':a,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'observed_unix':time.time()}
with(ops/'submission-result.json').open('x') as f:json.dump(v,f,indent=2)
print(json.dumps(v));sys.exit(r.returncode)
'''
 a=json.loads((O/'submission-argv.json').read_text());a.insert(1,'--hold');v=remote('held-submission.json',code,{'ops':RB+'/root-genuine-proof-r5-ops','argv':a});print(v['stdout'])
elif sys.argv[1]=='immutable':
 old=json.loads((B/'root-genuine-proof-r4-ops/immutable-readback.json').read_text());code=shlex.split(old['command'][-1])[-1];prior=json.loads(old['stdout']);assert prior['complete'] and len(prior['verified'])==1151
 c=json.loads((B/'proof-adapter-r5/transfer-closure.json').read_text());x={'files':prior['verified'],'aliases':c['all_required_namespace_aliases']}
 result=remote('immutable-readback.json',code,x);assert result['complete'];print('verified',len(result['verified']),'aliases',result['aliases_verified'],'seconds',result['wall_seconds'])
elif sys.argv[1]=='catalogues':
 job='50316939';j=RB+'/root-genuine-proof-r2/job-'+job
 w=json.loads((B/'root-genuine-proof-r2/job-50315944/transfer-attestation.json').read_text());w['complete']=False;w['adapter_manifest_sha256']=M;w['actual_job_id']=job
 for n,row in w['current_catalogues'].items():
  b=pathlib.Path(n).read_bytes();row['bytes']=len(b);row['sha256']=sha(b);row['delta_capture']={'cluster':'delta','path':n,'bytes':len(b),'sha256':sha(b),'observed_unix':time.time()};row['remote']=None;row['delta_reread']=None
 save('catalogue-capture.json',w)
 code='''import json,sys,subprocess,hashlib,os,time
from pathlib import Path
x=json.load(sys.stdin);j=Path(x['jobdir']);held=subprocess.check_output(['scontrol','show','job',x['job'],'-o'],universal_newlines=True,timeout=15);assert 'JobState=PENDING' in held and 'Reason=JobHeldUser' in held and 'RunTime=00:00:00' in held
j.mkdir(mode=0o700,exist_ok=False);spool=j/'spooled-batch.sh';subprocess.check_call(['scontrol','write','batch_script',x['job'],str(spool)],stdout=sys.stderr,timeout=15);assert hashlib.sha256(spool.read_bytes()).hexdigest()==x['dispatcher_sha']
seen={}
for n,row in x['catalogues'].items():
 p=Path(row['physical']);assert p.is_file() and not p.is_symlink();b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],str(p)
 seen[n]={'cluster':'bridges2','path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'observed_unix':time.time()}
r={'actual_job_id':x['job'],'held_state':held,'spooled_sha256':hashlib.sha256(spool.read_bytes()).hexdigest(),'current_catalogues':seen,'remote_catalogues_not_rewritten':True,'observed_unix':time.time()}
with(j/'catalogue-stage-receipt.json').open('x') as f:json.dump(r,f,indent=2)
print(json.dumps(r))
'''
 v=remote('catalogue-readback.json',code,{'job':job,'jobdir':j,'dispatcher_sha':D,'catalogues':w['current_catalogues']})
 for n,row in w['current_catalogues'].items():
  b=pathlib.Path(n).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256'];row['remote']=v['current_catalogues'][n];row['delta_reread']={'cluster':'delta','path':n,'bytes':len(b),'sha256':sha(b),'observed_unix':time.time()}
 raw=(O/'immutable-readback.json').read_bytes();im=json.loads(json.loads(raw)['stdout']);assert im['complete'];w['immutable_readback']={'sha256':sha(raw),'immutable_routes':len(im['verified']),'aliases':im['aliases_verified'],'observed_unix':im['observed_unix']};checks=json.loads(json.loads((O/'host-and-scheduler-checks.json').read_text())['stdout']);w['source_before_activation_evidence']=checks['source'];w['complete']=True
 localj=B/'root-genuine-proof-r2'/('job-'+job);localj.mkdir(exist_ok=False)
 wb=(json.dumps(w,indent=2)+'\n').encode();(localj/'transfer-attestation.json').write_bytes(wb)
 binding=json.loads((B/'root-genuine-proof-r2/job-50315944/bindings.json').read_text());binding.update(actual_job_id=job,adapter_manifest_sha256=M,output_physical=j+'/execution',independent_review={'path':RA+'/'+str(V.relative_to(A)),'sha256':VS},transfer_attestation={'path':j+'/transfer-attestation.json','sha256':sha(wb)})
 bb=(json.dumps(binding,indent=2)+'\n').encode();(localj/'bindings.json').write_bytes(bb);(localj/'bindings.sha256').write_text(sha(bb)+'\n')
 print('fresh witness',sha(wb),'binding',sha(bb),'catalogues unchanged remotely')
elif sys.argv[1]=='bind':
 job='50316939';localj=B/'root-genuine-proof-r2'/('job-'+job);rows=[]
 for n in ['transfer-attestation.json','bindings.json','bindings.sha256']:
  raw=(localj/n).read_bytes();rows.append({'name':n,'base64':base64.b64encode(raw).decode(),'bytes':len(raw),'sha256':sha(raw)})
 old=json.loads((B/'root-genuine-proof-r4-ops/binding-stage-readback.json').read_text());code=shlex.split(old['command'][-1])[-1];code=code.replace('proof-adapter-r4','proof-adapter-r5').replace('da3fd6aac9356a685410afd3800c824988ac90c4e0a60dfcbe63707382f9cddb',D)
 v=remote('binding-stage-readback.json',code,{'root':RB,'job':job,'jobdir':RB+'/root-genuine-proof-r2/job-'+job,'files':rows,'binding_sha':sha((localj/'bindings.json').read_bytes())});print(json.dumps(v))
elif sys.argv[1]=='release':
 review=W/'.superpowers/sdd/plan-a2-proof-release-review242/verdict.json';rv='a241a78ca46a626ecedbea23900277325d25c8ab672bc76b2ba44eccd6915fc7';assert sha(review.read_bytes())==rv
 j=B/'root-genuine-proof-r2/job-50316939';w=json.loads((j/'transfer-attestation.json').read_text())
 for n,row in w['current_catalogues'].items():
  raw=pathlib.Path(n).read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
 old=json.loads((B/'root-genuine-proof-r4-ops/release.json').read_text());code=shlex.split(old['command'][-1])[-1]
 for a,b in [('50315944','50316939'),('root-genuine-proof-r4-ops','root-genuine-proof-r5-ops'),('proof-adapter-r4','proof-adapter-r5'),('fcef0ac8380597cf349e7312c12e972279675d193f0fb72b5cead6d58e4f3de6','5a055aeff26499b3afc05901e2084e722e29deeaac6f18ce3172fdf33ce84188'),('da3fd6aac9356a685410afd3800c824988ac90c4e0a60dfcbe63707382f9cddb',D),('f7d6a0d05c7f4b148672fbbaff6a48f377f63d8a7edf7c361487bf4b95469777',rv)]:code=code.replace(a,b)
 code=code.replace("with(ops/'release-intent.json')", "h.source_before_activation()\nwith(ops/'release-intent.json')")
 v=remote('release.json',code,{});print(json.dumps(v))
