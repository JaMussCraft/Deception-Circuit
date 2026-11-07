from pathlib import Path
import json,os,sys,time,subprocess,hashlib,shlex
V=Path('/projects/beto/swong2/Alignment');W=V/'Deception-Circuit/.claude/worktrees/specificity-ladder';P=V/'Deception-Circuit/docs/research/specificity-ladder';B=W/'outputs/_analyses/specificity-ladder/a2-bridges2-20261102';R=W/'outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5/runtime';REMOTE='/ocean/projects/cis260361p/swong2/specificity-ladder-20261102';C='6bd8bf5334f2e83613a129d2fcfeacf83e762191'
REG=[V/'Deception-Circuit/docs/research/held_out.json',W/'docs/research/held_out.json']
def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,body):
 temp=path.with_name(path.name+'.tmp');temp.write_text(json.dumps(body,indent=2)+'\n');os.replace(temp,path)
def run(args,**kw):return subprocess.run(args,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=120,**kw)
def remote(command):return run(['ssh','-o','BatchMode=yes','bridges2',command]).stdout

def registry_snapshot():
 result=[]
 for path in REG:
  data=path.read_bytes();assert json.loads(data).get('sets')==[], 'new protected sets require explicit complete transfer/check; refuse automatic authorization'
  result.append((path,data))
 return result

def local_preflight(arm,tag):
 before=registry_snapshot();cmd=['bash',str(R/'scripts/jobs/specificity_twin_training.sh'),'--dry-run','--config',str(W/'outputs/_analyses/specificity-ladder/a2-timing-h200-config.json'),'--build-manifest',str(W/'outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07/build_manifest.json'),'--task','sdr_v2','--condition',arm,'--seed','42','--timing-epochs','20','--commit',C,'--receipt',str(B/('unused-local-'+tag+'.json'))]
 env=os.environ.copy();env.update(DC_CLUSTER='delta',DC_PYTHON='/u/swong2/.conda/envs/mgnp/bin/python',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
 started=time.time();r=run(cmd,cwd=R,env=env)
 (B/(tag+'.stdout')).write_text(r.stdout);(B/(tag+'.stderr')).write_text(r.stderr)
 assert before==registry_snapshot(),'primary registries changed during actual source preflight'
 write(B/(tag+'-preflight.json'),dict(command=cmd,exit_code=r.returncode,started_at=started,elapsed_seconds=time.time()-started,registries=[dict(virtual_path=str(p),sha256=sha(d)) for p,d in before]))
 return before

def validate_reservation(job):
 ledger=json.loads((P/'ledger.json').read_text());rows=[r for r in ledger['reservations'] if r['job_id']==job and r['cluster']=='bridges2'];assert len(rows)==1;row=rows[0]
 assert row['account']=='cis260361p' and row['partition']=='GPU-shared' and row['gpus']==1 and row['requested_minutes']==50 and row['source_commit']==C
 assert ledger['totals']['reserved_gpu_hours']<=125
 return row

def authorize(job,arm):
 assert arm in ('D','I');row=validate_reservation(job)
 facts=remote('scontrol show job '+job+' -o');fields=dict(x.split('=',1) for x in facts.split() if '=' in x)
 assert fields['JobState']=='RUNNING' and fields['Account']=='cis260361p' and fields['Partition']=='GPU-shared' and fields['TimeLimit']=='00:50:00'
 assert 'gres/gpu=1' in fields['AllocTRES'] and fields['JobName']=='lad-a2-b2-timing'
 tag='authorization-'+job+'-'+arm;registries=local_preflight(arm,tag)
 staged=B/(tag+'-registries');staged.mkdir(exist_ok=False)
 rows=[]
 for n,(path,data) in enumerate(registries):
  local=staged/(str(n)+'.json');local.write_bytes(data);physical=REMOTE+'/Alignment/'+str(path.relative_to(V))
  run(['rsync','--no-perms','--no-times','-e','ssh -o BatchMode=yes',str(local),'b2dtn:'+physical])
  digest=remote('sha256sum '+shlex.quote(physical)).split()[0];assert digest==sha(data)
  rows.append(dict(virtual_path=str(path),sha256=digest))
 assert registries==registry_snapshot(),'primary registries changed while copying'
 now=time.time();body=dict(job_id=job,arm=arm,source_commit=C,purpose='timing-only',issued_at=now,expires_at=now+300,registries=rows,reservation_id=row['id'],local_preflight=str(B/(tag+'-preflight.json')))
 path=B/(tag+'.json');assert not path.exists();write(path,body)
 destination=REMOTE+'/deployment/'+path.name;run(['rsync','--no-perms','--no-times','-e','ssh -o BatchMode=yes',str(path),'b2dtn:'+destination+'.pending']);remote('mv '+shlex.quote(destination+'.pending')+' '+shlex.quote(destination));print('authorized '+job+' '+arm,flush=True)

if __name__=='__main__':
 if sys.argv[1]=='check':
  local_preflight('D','authorizer-check-D');local_preflight('I','authorizer-check-I');print('actual local preflights passed',flush=True)
 else:
  job=sys.argv[1];assert job.isdigit();validate_reservation(job);deadline=time.monotonic()+3600;last=None;authorized=set()
  while time.monotonic()<deadline:
   accounting=remote('sacct -j '+job+' -X -n -P -o JobIDRaw,State,ElapsedRaw,ExitCode');record=[x.split('|') for x in accounting.splitlines() if x.startswith(job+'|')];assert len(record)==1;state=record[0][1].split()[0]
   if state!=last:
    print(accounting.strip(),flush=True);run(['research-session','job','update',str(P),job,'--status',state]);last=state
   write(B/('watch-'+job+'.json'),dict(checked_at=time.time(),accounting=accounting))
   if state in ('COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY','NODE_FAIL','PREEMPTED'):break
   if state=='RUNNING':
    raw=remote('if test -f '+REMOTE+'/deployment/phase-'+job+'.json; then cat '+REMOTE+'/deployment/phase-'+job+'.json; else echo "{}"; fi');phase=json.loads(raw)
    if phase.get('state')=='waiting_for_fresh_registry_authorization' and phase['arm'] not in authorized:
     assert phase['job_id']==job;authorize(job,phase['arm']);authorized.add(phase['arm'])
   time.sleep(15)
  print('bounded authorizer stopped',flush=True)
