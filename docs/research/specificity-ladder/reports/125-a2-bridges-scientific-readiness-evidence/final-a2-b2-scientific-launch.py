from pathlib import Path
import os,sys,json,time,subprocess,hashlib
P=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-20261102');A=P/'Alignment';V=Path('/projects/beto/swong2/Alignment');W=V/'Deception-Circuit/.claude/worktrees/specificity-ladder';R=W/'outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5/runtime';C='6bd8bf5334f2e83613a129d2fcfeacf83e762191';IMAGE=P/'containers/ubuntu2204.sif'
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
def dump(path,value):
 path=Path(path);temp=path.with_name(path.name+'.tmp-'+str(os.getpid()));temp.write_text(json.dumps(value,indent=2)+'\n');os.replace(temp,path)
def key(cell):return cell['task']+'-'+cell['condition']+'-seed'+str(cell['seed'])
def validate_full_receipt(body,cell):
 assert body['status']=='success' and body['exit_code']==0 and body['errors']==[]
 assert body['test_runner_injected'] is False and body['test_clock_injected'] is False
 assert body['purpose']=='scientific-seed' and body['actual_epochs']==500 and body['planned_epochs']==500
 assert body['execution_commit']==C and body['source_commit']=='77b6487b08b4410a4e5a9995c6ff5e46834a5ce3'
 assert (body['task'],body['condition'],body['seed'])==(cell['task'],cell['condition'],cell['seed'])
 assert body['gpu_count']==1 and len(body['gpu_devices'])==1 and 'H100' in body['gpu_devices'][0]
def registry_rows(rows):
 expected={str(V/'Deception-Circuit/docs/research/held_out.json'),str(W/'docs/research/held_out.json')}
 assert isinstance(rows,list) and len(rows)==2 and {r['virtual_path'] for r in rows}==expected
 for row in rows:
  assert len(row['sha256'])==64 and all(c in '0123456789abcdef' for c in row['sha256'])
  physical=A/Path(row['virtual_path']).relative_to(V);assert sha(physical)==row['sha256'] and json.loads(physical.read_text())['sets']==[]
def cache_check():
 model=json.loads((P/'deployment/model-cache-check.json').read_text());reference=P/'deployment/model-cache-reference.json';assert sha(reference)==model['reference_sha256'];ref=json.loads(reference.read_text());cache=Path(ref['remote_cache']);assert ref['revision']=='0e9e39f249a16976918f6564b8830bc894c89659' and (cache/'refs/main').read_text().strip()==ref['revision'];snapshot=cache/'snapshots'/ref['revision']
 for row in ref['metadata']:
  path=snapshot/row['name'];assert path.stat().st_size==row['nbytes'] and sha(path)==row['sha256']
 for row in ref['weights']:
  path=snapshot/row['name'];assert path.stat().st_size==row['nbytes'] and path.resolve().name==row['expected_sha256']
 assert sha(IMAGE)==json.loads((P/'deployment/verification.json').read_text())['image_sha256']
 return dict(revision=ref['revision'],checked_at=time.time(),full_weight_check_sha256=sha(P/'deployment/model-cache-check.json'))
def phase(job,**fields):dump(P/'deployment'/('scientific-phase-'+job+'.json'),dict(job_id=job,updated_at=time.time(),**fields))
def authorize(job,cell,placement_hash):
 phase(job,state='waiting_for_fresh_registry_authorization',cell_key=key(cell));path=P/'deployment'/('scientific-authorization-'+job+'.json');end=time.monotonic()+300
 while not path.exists():
  if time.monotonic()>end:raise RuntimeError('fresh root authorization absent after300seconds')
  time.sleep(5)
 body=json.loads(path.read_text());assert body['job_id']==job and body['cell_key']==key(cell) and body['purpose']=='scientific-seed' and body['source_commit']==C and body['placement_sha256']==placement_hash
 assert 0<=time.time()-body['issued_at']<=300 and time.time()<=body['expires_at'];registry_rows(body['registries']);return sha(path)
def main():
 mode=sys.argv[1];assert mode in ('run','dry-run');cell_key=sys.argv[2];proposal=P/'deployment/scientific-replacement-proposal.json';plan=json.loads(proposal.read_text());cell=next(c for c in plan['cells'] if key(c)==cell_key);assert cell['task']=='sdr_v2' and cell['condition'] in ('D','I') and cell['seed'] in (42,1,123)
 original=cell['original_fleet_cell'];fleet=A/(W/'outputs/_analyses/specificity-ladder/a2-fleet-6bd8bf5-h200/fleet-plan.json').relative_to(V);assert sha(fleet)==plan['original_fleet_plan_sha256'];assert original==next(c for c in json.loads(fleet.read_text())['cells'] if key(c)==cell_key)
 assert original['epochs']==500 and original['cwd']==str(R) and '--timing-epochs' not in original['argv'];job=os.environ.get('SLURM_JOB_ID');tag=job if mode=='run' else sys.argv[3];placement_hash=None
 if mode=='run':
  assert job and job.isdigit();placement_path=P/'deployment/scientific-placement.json';placement=json.loads(placement_path.read_text());placement_hash=sha(placement_path);entry=placement['jobs'][job]
  assert entry['cell_key']==cell_key and entry['requested_minutes']==cell['requested_minutes'] and entry['source_commit']==C
  assert placement['proposal_sha256']==sha(proposal) and placement['launcher_sha256']==sha(Path(__file__)) and placement['job_script_sha256']==sha(P/'deployment/a2-b2-scientific-job.sh')
  assert placement['all_original_delta_jobs_cancelled_before_release'] is True
 cache=cache_check();profile={'DC_CLUSTER':'bridges2','DC_B2_ALLOC':'cis260361p','HF_HUB_CACHE':'/ocean/projects/cis260361p/swong2/hf/hub','TRANSFORMERS_CACHE':'/ocean/projects/cis260361p/swong2/hf/hub','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','HF_DATASETS_OFFLINE':'1','PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','XDG_CACHE_HOME':'/tmp/a2-xdg-cache','WANDB_MODE':'disabled'}
 for name in ('SLURM_JOB_ID','SLURM_JOB_NAME','SLURM_CLUSTER_NAME','SLURM_JOB_PARTITION','SLURM_JOB_ACCOUNT','SLURM_JOB_NODELIST','SLURM_NODELIST','SLURM_CPUS_PER_TASK','SLURM_GPUS_PER_NODE','SLURM_JOB_GPUS','SLURM_STEP_GPUS','CUDA_VISIBLE_DEVICES'):
  if name in os.environ:profile[name]=os.environ[name]
 receipt=Path(original['receipt']);physical=A/receipt.relative_to(V)
 if mode=='run':
  assert profile.get('CUDA_VISIBLE_DEVICES') and not physical.exists() and not physical.is_symlink()
  output=A/Path(cell['virtual_output_dir']).relative_to(V);assert not output.exists() and not output.is_symlink()
  assert entry['virtual_output_dir']==cell['virtual_output_dir']
  auth=authorize(job,cell,placement_hash);initial_cache=cache;cache=cache_check()
  assert not physical.exists() and not physical.is_symlink() and not output.exists() and not output.is_symlink()
  phase(job,state='executing',cell_key=cell_key,authorization_sha256=auth,initial_cache_check=initial_cache,current_cache_check=cache)
 command=['apptainer','exec','--cleanenv','--contain','--no-home','--writable-tmpfs','--pwd',str(R),'--bind',str(A)+':'+str(V)+':rw','--bind','/ocean:/ocean:ro']
 if mode=='run':command+=['--nv']
 for k,v in sorted(profile.items()):command+=['--env',k+'='+v]
 argv=list(original['argv'])
 if mode=='dry-run':argv.insert(2,'--dry-run')
 command += [str(IMAGE)]+argv
 out=P/'logs'/('scientific-'+tag+'-'+cell_key+'.stdout');err=out.with_suffix('.stderr');assert not out.exists() and not err.exists();started=time.time()
 with out.open('w') as stdout,err.open('w') as stderr:r=subprocess.run(command,stdout=stdout,stderr=stderr)
 evidence=dict(job_id=job,mode=mode,cell_key=cell_key,command=command,started_at=started,elapsed_seconds=time.time()-started,exit_code=r.returncode,source_commit=C,launcher_sha256=sha(Path(__file__)),placement_sha256=placement_hash,cache_check=cache,virtual_receipt=str(receipt),stdout=str(out),stderr=str(err));dump(P/'deployment'/('scientific-'+tag+'-'+cell_key+'-execution.json'),evidence)
 assert r.returncode==0,'frozen full500 wrapper failed'
 if mode=='run':
  body=json.loads(physical.read_text());validate_full_receipt(body,cell);assert body['environment']['SLURM_JOB_ID']==job and (body['environment'].get('SLURM_CLUSTER_NAME') or body['environment'].get('DC_CLUSTER'))=='bridges2';phase(job,state='completed',cell_key=cell_key,receipt_sha256=sha(physical))
 print(json.dumps(dict(cell_key=cell_key,mode=mode,exit_code=r.returncode,elapsed_seconds=evidence['elapsed_seconds'])),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as e:
  if sys.argv[1]=='run' and os.environ.get('SLURM_JOB_ID'):phase(os.environ['SLURM_JOB_ID'],state='failed',error=repr(e))
  raise
