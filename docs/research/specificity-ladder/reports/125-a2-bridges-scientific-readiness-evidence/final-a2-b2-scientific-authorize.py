from pathlib import Path
import json,os,sys,time,subprocess,hashlib,shlex,threading,concurrent.futures
V=Path('/projects/beto/swong2/Alignment');W=V/'Deception-Circuit/.claude/worktrees/specificity-ladder';P=V/'Deception-Circuit/docs/research/specificity-ladder';B=W/'outputs/_analyses/specificity-ladder/a2-bridges2-20261102';R=W/'outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5/runtime';REMOTE='/ocean/projects/cis260361p/swong2/specificity-ladder-20261102';C='6bd8bf5334f2e83613a129d2fcfeacf83e762191';REG=[V/'Deception-Circuit/docs/research/held_out.json',W/'docs/research/held_out.json'];TRANSFER=threading.Lock()
def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,body):
 temp=path.with_name(path.name+'.tmp');temp.write_text(json.dumps(body,indent=2)+'\n');os.replace(temp,path)
def run(args,**kw):return subprocess.run(args,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=120,**kw)
def remote(command):return run(['ssh','-o','BatchMode=yes','bridges2',command]).stdout
def key(cell):return cell['task']+'-'+cell['condition']+'-seed'+str(cell['seed'])
def registry_snapshot():
 rows=[]
 for p in REG:
  data=p.read_bytes();assert json.loads(data)['sets']==[],'new protected sets need verified complete closure, no automatic authorization';rows.append((p,data))
 return rows
def original_cancellations(plan):
 ids=[c['old_delta_job_id'] for c in plan['cells']];raw=run(['sacct','-j',','.join(ids),'-X','-n','-P','-o','JobIDRaw,State,ElapsedRaw,ExitCode']).stdout;rows={r.split('|')[0]:r.split('|') for r in raw.splitlines() if '|' in r};assert set(rows)==set(ids)
 for job in ids:assert rows[job][1].startswith('CANCELLED') and int(rows[job][2])==0
 return raw
def local_preflight(cell,tag):
 before=registry_snapshot();cmd=list(cell['original_fleet_cell']['argv']);cmd.insert(2,'--dry-run');assert '--timing-epochs' not in cmd
 env=os.environ.copy();env.update(DC_CLUSTER='delta',DC_PYTHON='/u/swong2/.conda/envs/mgnp/bin/python',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1');started=time.time();r=run(cmd,cwd=R,env=env)
 (B/(tag+'.stdout')).write_text(r.stdout);(B/(tag+'.stderr')).write_text(r.stderr);assert before==registry_snapshot()
 write(B/(tag+'-preflight.json'),dict(command=cmd,cell_key=key(cell),exit_code=r.returncode,elapsed_seconds=time.time()-started,registries=[dict(virtual_path=str(p),sha256=sha(d)) for p,d in before]));return before

def reservation(job,cell):
 ledger=json.loads((P/'ledger.json').read_text());matches=[r for r in ledger['reservations'] if r['job_id']==job and r['cluster']=='bridges2'];assert len(matches)==1;r=matches[0]
 assert (r['account'],r['partition'],r['gpus'],r['requested_minutes'],r['source_commit'])==('cis260361p','GPU-shared',1,cell['requested_minutes'],C)
 assert ledger['totals']['reserved_gpu_hours']<=125 and sum(r['reserved_gpu_hours'] for r in ledger['reservations'] if 'a2-' in (r.get('output_dir') or ''))<=60
 return r

def authorize(job,entry,plan,placement_path):
 cell=next(c for c in plan['cells'] if key(c)==entry['cell_key']);row=reservation(job,cell);cancel=original_cancellations(plan)
 facts=remote('scontrol show job '+job+' -o');f=dict(x.split('=',1) for x in facts.split() if '=' in x);minutes=cell['requested_minutes'];limit='%02d:%02d:00'%(minutes//60,minutes%60)
 assert f['JobState']=='RUNNING' and f['Account']=='cis260361p' and f['Partition']=='GPU-shared' and f['TimeLimit']==limit and f['NumCPUs']=='4' and f['MinMemoryNode']=='64G'
 tres=dict(x.split('=',1) for x in f.get('AllocTRES',f.get('TRES','')).split(',') if '=' in x)
 assert tres.get('gres/gpu')=='1' and f['TresPerNode']=='gres:gpu:h100-80:1' and f['JobName']==entry['job_name'] and f['Command']==REMOTE+'/deployment/a2-b2-scientific-job.sh' and f['WorkDir']==REMOTE
 local_receipt=Path(cell['original_fleet_cell']['receipt']);local_output=Path(cell['virtual_output_dir'])
 assert not local_receipt.exists() and not local_receipt.is_symlink() and not local_output.exists() and not local_output.is_symlink()
 tag='scientific-authorization-'+job;registries=local_preflight(cell,tag);stage=B/(tag+'-registries');stage.mkdir(exist_ok=False)
 with TRANSFER:
  assert registries==registry_snapshot();rows=[]
  for n,(path,data) in enumerate(registries):
   local=stage/(str(n)+'.json');local.write_bytes(data);physical=REMOTE+'/Alignment/'+str(path.relative_to(V));run(['rsync','--no-perms','--no-times','-e','ssh -o BatchMode=yes',str(local),'b2dtn:'+physical]);digest=remote('sha256sum '+shlex.quote(physical)).split()[0];assert digest==sha(data);rows.append(dict(virtual_path=str(path),sha256=digest))
  assert registries==registry_snapshot();now=time.time();body=dict(job_id=job,cell_key=key(cell),source_commit=C,purpose='scientific-seed',issued_at=now,expires_at=now+300,registries=rows,reservation_id=row['id'],placement_sha256=sha(placement_path.read_bytes()),original_cancellation_check=cancel,local_preflight=str(B/(tag+'-preflight.json')));dest=B/(tag+'.json');assert not dest.exists();write(dest,body);target=REMOTE+'/deployment/'+dest.name;run(['rsync','--no-perms','--no-times','-e','ssh -o BatchMode=yes',str(dest),'b2dtn:'+target+'.pending']);remote('mv '+shlex.quote(target+'.pending')+' '+shlex.quote(target));print('authorized '+job+' '+key(cell),flush=True)

def main():
 plan=json.loads((B/'scientific-replacement-proposal.json').read_text())
 if sys.argv[1]=='check':
  for cell in plan['cells']:local_preflight(cell,'scientific-check-'+key(cell))
  print('six actual full500 local preflights passed',flush=True);return
 placement_path=B/'scientific-placement.json';raw=placement_path.read_bytes();placement=json.loads(raw);assert placement['proposal_sha256']==sha((B/'scientific-replacement-proposal.json').read_bytes());assert placement['authorizer_sha256']==sha(Path(__file__).read_bytes());jobs=placement['jobs'];assert len(jobs)==6 and len({v['cell_key'] for v in jobs.values()})==6
 deadline=time.monotonic()+3540;last={};futures={};terminal=set()
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  while time.monotonic()<deadline and len(terminal)<len(jobs):
   assert placement_path.read_bytes()==raw;accounting=remote('sacct -j '+','.join(jobs)+' -X -n -P -o JobIDRaw,State,ElapsedRaw,ExitCode');write(B/'scientific-watcher-current.json',dict(checked_at=time.time(),accounting=accounting))
   for record in accounting.splitlines():
    row=record.split('|');job=row[0]
    if job not in jobs:continue
    state=row[1].split()[0]
    if last.get(job)!=state:print(record,flush=True);run(['research-session','job','update',str(P),job,'--status',state]);last[job]=state
    if state in ('COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY','NODE_FAIL','PREEMPTED'):terminal.add(job);continue
    if state=='RUNNING' and job not in futures:
     path=REMOTE+'/deployment/scientific-phase-'+job+'.json';phase=json.loads(remote('if test -f '+path+'; then cat '+path+'; else echo "{}"; fi'))
     if phase.get('state')=='waiting_for_fresh_registry_authorization':
      assert phase['job_id']==job and phase['cell_key']==jobs[job]['cell_key'];futures[job]=pool.submit(authorize,job,jobs[job],plan,placement_path)
   for job,future in futures.items():
    if future.done():future.result()
   time.sleep(10)
 print('bounded scientific monitor finished',flush=True)
if __name__=='__main__':main()
