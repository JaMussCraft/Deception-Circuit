from pathlib import Path
import os,sys,json,time,datetime,subprocess,hashlib
P=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-20261102');A=P/'Alignment';V=Path('/projects/beto/swong2/Alignment');W=V/'Deception-Circuit/.claude/worktrees/specificity-ladder';R=W/'outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5/runtime';C='6bd8bf5334f2e83613a129d2fcfeacf83e762191';PY='/ocean/projects/cis260361p/swong2/envs/mgnp/bin/python';IMAGE=P/'containers/ubuntu2204.sif'
mode=sys.argv[1];assert mode in ('dry-run','run');job=os.environ.get('SLURM_JOB_ID');assert mode!='run' or job
TAG=job if mode=='run' else sys.argv[2]
def dump(path,value):
 tmp=Path(str(path)+'.tmp-'+str(os.getpid()));tmp.write_text(json.dumps(value,indent=2)+'\n');os.replace(str(tmp),str(path))
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for data in iter(lambda:f.read(8*1024*1024),b''):h.update(data)
 return h.hexdigest()
def phase(value):dump(P/'deployment'/('phase-'+str(job)+'.json'),dict(job_id=job,updated_at=time.time(),**value))
def remaining():
 p=subprocess.run(['scontrol','show','job',job,'-o'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,check=True);facts=dict(x.split('=',1) for x in p.stdout.split() if '=' in x)
 assert facts['JobState']=='RUNNING' and facts['Account']=='cis260361p' and facts['Partition']=='GPU-shared'
 return time.mktime(time.strptime(facts['EndTime'],'%Y-%m-%dT%H:%M:%S'))-time.time()
def validate_timing_receipt(body):
 assert body['status']=='success' and body['exit_code']==0 and body['errors']==[]
 assert body['test_runner_injected'] is False and body['test_clock_injected'] is False
 assert body['purpose']=='timing-only' and body['actual_epochs']==20 and body['planned_epochs']==500
 assert body['execution_commit']==C and body['source_commit']=='77b6487b08b4410a4e5a9995c6ff5e46834a5ce3' and body['task']=='sdr_v2' and body['seed']==42

def validate_registry_paths(rows):
 expected={str(V/'Deception-Circuit/docs/research/held_out.json'),str(W/'docs/research/held_out.json')}
 assert isinstance(rows,list) and len(rows)==2 and {row['virtual_path'] for row in rows}==expected
 assert all(isinstance(row['sha256'],str) and len(row['sha256'])==64 and all(c in '0123456789abcdef' for c in row['sha256']) for row in rows)

def authorize(arm):
 phase(dict(state='waiting_for_fresh_registry_authorization',arm=arm));path=P/'deployment'/('authorization-'+job+'-'+arm+'.json');deadline=time.monotonic()+300
 while not path.exists():
  if time.monotonic()>deadline:raise RuntimeError('fresh root registry authorization did not arrive within300seconds')
  time.sleep(5)
 body=json.loads(path.read_text());assert body['job_id']==job and body['arm']==arm and body['source_commit']==C and body['purpose']=='timing-only'
 assert 0<=time.time()-body['issued_at']<=900 and body['expires_at']>=time.time()
 validate_registry_paths(body['registries'])
 for row in body['registries']:
  physical=A/Path(row['virtual_path']).relative_to(V);assert sha(physical)==row['sha256'];assert json.loads(physical.read_text()).get('sets')==[],'initial automatic authorization supports empty current catalog only; no protected-set omission allowed'
 return body
def check_current_model_cache():
 reference_path=P/'deployment/model-cache-reference.json'
 assert sha(reference_path)==model['reference_sha256']
 reference=json.loads(reference_path.read_text());cache=Path(reference['remote_cache'])
 assert reference['revision']=='0e9e39f249a16976918f6564b8830bc894c89659'
 assert (cache/'refs/main').read_text().strip()==reference['revision']
 snapshot=cache/'snapshots'/reference['revision']
 for item in reference['metadata']:
  path=snapshot/item['name'];assert path.stat().st_size==item['nbytes'] and sha(path)==item['sha256']
 for item in reference['weights']:
  path=snapshot/item['name'];assert path.stat().st_size==item['nbytes'] and path.resolve().name==item['expected_sha256']
 return dict(revision=reference['revision'],checked_at=time.time(),metadata_files=len(reference['metadata']),weight_links=len(reference['weights']),initial_full_weight_check_sha256=sha(P/'deployment/model-cache-check.json'))

verification=json.loads((P/'deployment/verification.json').read_text());assert sha(IMAGE)==verification['image_sha256'];model=json.loads((P/'deployment/model-cache-check.json').read_text());assert model['revision']=='0e9e39f249a16976918f6564b8830bc894c89659'
profile={'DC_CLUSTER':'bridges2','DC_B2_ALLOC':'cis260361p','HF_HUB_CACHE':'/ocean/projects/cis260361p/swong2/hf/hub','TRANSFORMERS_CACHE':'/ocean/projects/cis260361p/swong2/hf/hub','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','HF_DATASETS_OFFLINE':'1','PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','XDG_CACHE_HOME':'/tmp/a2-xdg-cache','WANDB_MODE':'disabled'}
for name in ('SLURM_JOB_ID','SLURM_JOB_NAME','SLURM_CLUSTER_NAME','SLURM_JOB_PARTITION','SLURM_JOB_ACCOUNT','SLURM_JOB_NODELIST','SLURM_NODELIST','SLURM_CPUS_PER_TASK','SLURM_GPUS_PER_NODE','SLURM_JOB_GPUS','SLURM_STEP_GPUS','CUDA_VISIBLE_DEVICES'):
 if name in os.environ:profile[name]=os.environ[name]
if mode=='run':assert profile.get('CUDA_VISIBLE_DEVICES'),'actual Slurm CUDA device visibility is required'
cells=[]
try:
 for arm in ('D','I'):
  cache_check=check_current_model_cache()
  if mode=='run':
   if arm=='I':
    required=max(1500.,1.25*cells[0]['elapsed_seconds']+300.)
    if remaining()<required:raise RuntimeError('insufficient live time for complete second timing arm plus finish reserve; no shortened run permitted')
   auth=authorize(arm)
   if arm=='I' and remaining()<required:raise RuntimeError('remaining time fell below second-arm guard while awaiting authorization')
   phase(dict(state='executing',arm=arm,authorization_sha256=sha(P/'deployment'/('authorization-'+job+'-'+arm+'.json'))))
  receipt=W/'outputs/_analyses/specificity-ladder/a2-bridges2-timing'/('sdr_v2-'+arm+'-seed42.json')
  cmd=['apptainer','exec','--cleanenv','--contain','--no-home','--writable-tmpfs','--pwd',str(R),'--bind',str(A)+':'+str(V)+':rw','--bind','/ocean:/ocean:ro']
  if mode=='run':cmd+=['--nv']
  for key,value in sorted(profile.items()):cmd+=['--env',key+'='+value]
  cmd += [str(IMAGE),'bash',str(R/'scripts/jobs/specificity_twin_training.sh')]
  if mode=='dry-run':cmd+=['--dry-run']
  cmd+=['--config',str(W/'outputs/_analyses/specificity-ladder/a2-timing-h200-config.json'),'--build-manifest',str(W/'outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07/build_manifest.json'),'--task','sdr_v2','--condition',arm,'--seed','42','--timing-epochs','20','--commit',C,'--receipt',str(receipt)]
  out=P/'logs'/(TAG+'-'+arm+'.stdout');err=P/'logs'/(TAG+'-'+arm+'.stderr');assert not out.exists() and not err.exists()
  started=time.time()
  with out.open('w') as stdout,err.open('w') as stderr:result=subprocess.run(cmd,stdout=stdout,stderr=stderr)
  cell=dict(mode=mode,arm=arm,source_commit=C,launcher_sha256=sha(Path(__file__)),current_cache_check=cache_check,purpose='timing-only',actual_epochs=20,configured_planned_epochs=500,cosine_T_max=20,job_id=job,command=cmd,started_at=started,elapsed_seconds=time.time()-started,exit_code=result.returncode,stdout=str(out),stderr=str(err),virtual_receipt=str(receipt));cells.append(cell);dump(P/'deployment'/(TAG+'-'+arm+'-execution.json'),cell);print(json.dumps(dict(arm=arm,mode=mode,exit_code=result.returncode,elapsed_seconds=cell['elapsed_seconds'])),flush=True)
  if result.returncode:raise RuntimeError('frozen wrapper failed; preserve cell log and stop')
  if mode=='run':
   actual=A/receipt.relative_to(V);body=json.loads(actual.read_text());validate_timing_receipt(body)
   assert body['condition']==arm and body['gpu_count']==1 and len(body['gpu_devices'])==1 and 'H100' in body['gpu_devices'][0]
   cell['actual_receipt_sha256']=sha(actual)
 dump(P/'deployment'/(TAG+'-completion.json'),dict(complete=True,mode=mode,job_id=job,cells=cells,scientific_seed=False))
 if mode=='run':phase(dict(state='completed',arms=['D','I']))
except BaseException as error:
 dump(P/'deployment'/(TAG+'-failure.json'),dict(complete=False,mode=mode,job_id=job,cells=cells,error=repr(error)))
 if mode=='run':phase(dict(state='failed',error=repr(error)))
 raise
