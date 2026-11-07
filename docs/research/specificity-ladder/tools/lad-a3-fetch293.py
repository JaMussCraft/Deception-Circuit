from pathlib import Path
import json,hashlib,subprocess,shlex,time,sys,base64
A=Path('/projects/beto/swong2/Alignment');S=A/'Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd';O=S/'plan-a3/sharded-deployment293';P=S/'plan/task23-green-r8-sharded';R=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment');job=sys.argv[1];assert job in ('50319331','50319334');slot='mgnp-'+str(('50319331','50319334').index(job));d=O/slot;target=P/('jobs/job-'+job);assert not target.exists() and not(d/'fetch-receipt.json').exists()
code='''import sys,json,subprocess,hashlib,time,base64
from pathlib import Path
x=json.load(sys.stdin);job=x['job'];p=Path(x['root']);r=subprocess.check_output(['sacct','-n','-X','-j',job,'-o','JobIDRaw,State,ExitCode,ElapsedRaw,AllocTRES,NodeList,Start,End','-P'],universal_newlines=True,timeout=15);lines=[z.split('|') for z in r.splitlines() if z.strip()];row=next(z for z in lines if z[0]==job);state=row[1].split()[0].rstrip('+');assert state in ['COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY','NODE_FAIL','PREEMPTED'],row
rows=[];allowed=['.json','.jsonl','.xml','.stdout','.stderr','.log'];total=0
for directory in [p,p/'child',p/'child/execution',p/'child/execution/baseline-red',p/'child/execution/fixture-preflight']:
 if not directory.exists():continue
 for f in sorted(directory.iterdir()):
  if f.is_file() and f.suffix in allowed:
   assert not f.is_symlink() and f.resolve()==f;size=f.stat().st_size;assert size<32*1024*1024,'large explicit file requires streaming fetch';total+=size;assert total<64*1024*1024
   b=f.read_bytes();rows.append(dict(relative=str(f.relative_to(p)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),base64=base64.b64encode(b).decode()))
log=Path(x['log']);b=log.read_bytes() if log.is_file() else None
if b is not None:rows.append(dict(relative='slurm-'+job+'.log',bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),base64=base64.b64encode(b).decode()))
print(json.dumps(dict(job_id=job,cluster='bridges2',raw_accounting=r,state=state,exit_code=row[2],elapsed_seconds=int(row[3]),AllocTRES=row[4],node=row[5],start=row[6],end=row[7],files=rows,observed_unix=time.time())))
'''
x=dict(job=job,root=str(R/target.relative_to(A)),log=str(R/(d/('slurm-'+job+'.log')).relative_to(A)))
a=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)]
r=subprocess.run(a,input=json.dumps(x),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=90);assert r.returncode==0,r.stderr;v=json.loads(r.stdout);target.mkdir(parents=True,exist_ok=False)
for f in v['files']:
 rel=Path(f['relative']);assert not rel.is_absolute() and '..' not in rel.parts;b=base64.b64decode(f.pop('base64'));assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'];q=target/rel;q.parent.mkdir(parents=True,exist_ok=True)
 with q.open('xb') as z:z.write(b)
 assert hashlib.sha256(q.read_bytes()).hexdigest()==f['sha256']
with(d/'fetch-receipt.json').open('x') as z:json.dump(v,z,indent=2);z.write('\n')
tres=dict(y.split('=',1) for y in v['AllocTRES'].split(',') if '=' in y);gpus=sum(float(n) for k,n in tres.items() if k=='gres/gpu');assert not any(k.startswith('gres/gpu') and float(n)>0 for k,n in tres.items())
accounting={k:v[k] for k in ['job_id','cluster','state','exit_code','elapsed_seconds','AllocTRES','node','start','end','raw_accounting','observed_unix']};accounting['gpus']=gpus
with(d/'terminal-accounting.json').open('x') as z:json.dump(accounting,z,indent=2);z.write('\n')
print(job,v['state'],v['exit_code'],v['elapsed_seconds'],'seconds;',len(v['files']),'explicit terminal files fetched;',sum(f['bytes'] for f in v['files']),'bytes')
