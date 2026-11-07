"""Bridges model-boundary checks; unbound templates cannot authorize execution."""
import os,sys,pathlib,json,hashlib,subprocess,time,datetime
L=pathlib.Path(__file__).resolve().parent
CONFIG=pathlib.Path(os.environ['A2_H100_BOUND_CONFIG'])
def sha(path):
 h=hashlib.sha256()
 with pathlib.Path(path).open('rb') as stream:
  for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
assert sha(CONFIG)==os.environ['A2_H100_BOUND_CONFIG_SHA256']
C=json.loads(CONFIG.read_text());B=pathlib.Path(C['runtime']);MAIN=pathlib.Path(C['main_root']);PILOT=pathlib.Path(C['pilot_root'])
for key in ('actual_job_id','reservation_id','groups_file_sha256','groups_receipt_sha256','placement_sha256','input_manifest','input_manifest_sha256','delta_G3_receipt','delta_G3_receipt_sha256','bridges_G3_receipt','bridges_G3_receipt_sha256','model_cache_proof','model_cache_proof_sha256','launch_packet_manifest_sha256','allocation_capture'):assert C[key],('UNBOUND',key)
assert C['independent160_accepted'] is True and C['exact_requested_GPU_seconds']==3000 and C['maximum_reserved_gpu_hours']*3600>=3000
assert C['actual_job_id']==os.environ['SLURM_JOB_ID']
def write(path,value):
 with pathlib.Path(path).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def packet():
 assert sha(L/'manifest.json')==C['launch_packet_manifest_sha256']
 for name,digest in json.loads((L/'manifest.json').read_text()).items():assert sha(L/name)==digest,name
 assert sha(C['source_plan'])==C['source_plan_sha256']
 for pathkey,digestkey in [('input_manifest','input_manifest_sha256'),('delta_G3_receipt','delta_G3_receipt_sha256'),('bridges_G3_receipt','bridges_G3_receipt_sha256'),('model_cache_proof','model_cache_proof_sha256')]:assert sha(C[pathkey])==C[digestkey]
 assert sha(C['image'])==C['image_sha256']
def project_origins():
 result={}
 for name,module in list(sys.modules.items()):
  if name.split('.')[0] in ('component_analysis','models','dataset','evaluation','scripts','config') and getattr(module,'__file__',None):
   path=pathlib.Path(module.__file__).resolve();assert path.is_relative_to(B.resolve()),(name,str(path));result[name]=str(path)
 return result
def source():
 assert sha(C['snapshot'])==C['snapshot_sha256'];s=json.loads(pathlib.Path(C['snapshot']).read_text());assert s['source_commit']==C['commit'] and len(s['source_sha256'])==511 and not s['source_code_symlinks']
 files=s['source_sha256'];links=s['input_links'];assert len(links)==4 and not(set(files)&set(links))
 for name in list(files)+list(links):
  rel=pathlib.Path(name);assert not rel.is_absolute() and '..' not in rel.parts and str(rel)==name
 actual_files=set();actual_links=set()
 for item in B.rglob('*'):
  name=str(item.relative_to(B))
  if item.is_symlink():actual_links.add(name)
  elif item.is_file():actual_files.add(name)
 assert actual_files==set(files) and actual_links==set(links),'source extra/missing file or alias'
 for name,digest in files.items():
  item=B/name;assert not item.is_symlink() and item.resolve().is_relative_to(B.resolve()) and sha(item)==digest,name
 for name,target in links.items():
  item=B/name;assert item.is_symlink() and os.readlink(item)==target and item.exists() and item.resolve()==pathlib.Path(target).resolve(),name
 assert sha(C['groups'])==C['groups_file_sha256']
 for proofkey in ('delta_G3_receipt','bridges_G3_receipt','model_cache_proof'):assert pathlib.Path(C[proofkey]).is_file()
 return dict(source_commit=C['commit'],groups_file_sha256=C['groups_file_sha256'],snapshot_sha256=C['snapshot_sha256'],source_count=511,literal_links=4,project_module_origins=project_origins(),checked_utc=utc())

def imports():
 os.chdir(B);sys.path.insert(0,str(B))
 from component_analysis import a2_pipeline as a2,a3_direction_runtime as ar
 return a2,ar
def environment():
 return dict(os.environ,DC_CLUSTER='bridges2',DC_B2_ALLOC='cis260361p',DC_PYTHON=C['python'],DC_RUN_MANIFEST_GIT='0',PYTHONPATH=str(B),PYTHONDONTWRITEBYTECODE='1',HF_HOME='/ocean/projects/cis260361p/swong2/hf',HF_HUB_CACHE='/work/nvme/beto/swong2',TRANSFORMERS_CACHE='/work/nvme/beto/swong2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',WANDB_MODE='disabled',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
def allocation(*,gpu=True,release=None):
 job=os.environ['SLURM_JOB_ID'];assert job==C['actual_job_id']
 captured=json.loads(pathlib.Path(C['allocation_capture']).read_text());assert 0<=time.time()-captured['captured_unix']<=C['maximum_allocation_capture_age_seconds']
 raw=captured['raw_scontrol'];facts=dict(x.split('=',1) for x in raw.split() if '=' in x);assert captured['fields']==facts and captured['actual_job_id']==job and facts['JobId']==job
 assert facts['JobState']=='RUNNING' and facts['Account']==C['expected_account'] and facts['Partition'] in C['allowed_partitions'] and facts['QOS']==C['expected_qos']
 assert facts['Requeue']=='0' and facts['Restarts']=='0'
 assert os.uname().nodename.split('.')[0]==captured['host'].split('.')[0] and captured['host'].split('.')[0] in [x.split('.')[0] for x in captured['actual_hostnames']]
 tres=dict(x.split('=',1) for x in facts.get('AllocTRES',facts.get('TRES','')).split(',') if '=' in x)
 assert tres.get('gres/gpu')=='1' and (tres.get('gres/gpu:h100-80')=='1' or facts.get('TresPerNode')=='gres:gpu:h100-80:1'),'actual typed H100 TRES required'
 assert int(facts['NumCPUs'])==4 and int(facts['NumNodes'])==1
 memory=tres['mem'];scale={'K':1024,'M':1024**2,'G':1024**3,'T':1024**4};mem=float(memory[:-1])*scale[memory[-1]] if memory[-1] in scale else float(memory);assert mem>=64*1024**3
 assert facts['TimeLimit'] in ('00:50:00','50:00')
 return dict(job_id=job,hostname=os.uname().nodename,facts=facts,raw=raw,tres=tres,host_capture_unix=captured['captured_unix'])

def budget(*,prospective=False,release):
 assert not prospective;_,ar=imports();identity=dict(purpose='A2 H100 original-H bank plus prefix4 timing',source_commit=C['commit'],groups_sha256=C['groups_file_sha256'],main_root=C['main_root'],pilot_root=C['pilot_root'])
 normalized=ar.normalize_ledger(C['mapping_origin'],identity=identity,include_envelope=False,refresh_deadline=time.time()+20)
 assert normalized['current_snapshot_sha256']==release['ledger_sha256']==sha(C['canonical_ledger'])
 mapping=ar.read_object(normalized['active_mapping_reference']['path']);ledger=json.loads(pathlib.Path(C['canonical_ledger']).read_text());assert not ledger.get('legacy_totals') and mapping['ledger_path']==C['canonical_ledger']
 entries={row['id']:row for row in ledger['reservations']};phases={name:0. for name in C['experiment_limits']}
 for row in mapping['entries']:phases[row['experiment']]+=row['original_reserved_gpu_hours']
 total=round(sum(row['reserved_gpu_hours'] for row in entries.values()),4);assert total==ledger['totals']['reserved_gpu_hours'] and total<=125
 assert all(phases[name]<=limit for name,limit in C['experiment_limits'].items())
 row=entries[C['reservation_id']];owned=next(x for x in mapping['entries'] if x['reservation_id']==row['id']);assert owned['experiment']=='A2'
 assert row['job_id']==C['actual_job_id'] and row['cluster']=='bridges2' and row['account']==C['expected_account'] and row['partition'] in C['allowed_partitions']
 assert row['source_commit']==C['commit'] and pathlib.Path(row['output_dir']).resolve()==MAIN.resolve()
 assert row['gpus']==1 and row['requested_minutes']==50 and row['reserved_gpu_hours']==C['maximum_reserved_gpu_hours'] and row['reserved_gpu_hours']*3600>=3000
 assert row['status'] in ('PENDING','RUNNING') and release['reservation_id']==row['id'] and release['active_mapping_reference']==normalized['active_mapping_reference']
 return dict(ledger_sha256=normalized['current_snapshot_sha256'],active_mapping_reference=normalized['active_mapping_reference'],phase_reserved=phases,total_reserved=total,no_old_charge_refunded=True)
def gpu_release(stage):
 assert stage in ('bank','prefix4');root=pathlib.Path(os.environ['A2_H100_RELEASE_DIRECTORY']);path=root/(C['actual_job_id']+'-'+stage+'.json');wait_end=time.monotonic()+300
 phase=pathlib.Path(os.environ['A2_TIMING_EXECUTION_OUTPUT'])/('WAITING-'+stage+'.json');write(phase,dict(job_id=C['actual_job_id'],phase=stage,requested_at=time.time(),source_commit=C['commit'],bound_config_sha256=sha(CONFIG)))
 while not path.exists():
  if time.monotonic()>=wait_end:raise TimeoutError('fresh phase-specific root release absent after300s')
  time.sleep(5)
 release_bytes=path.read_bytes();r=json.loads(release_bytes);r['_release_path']=str(path);r['_release_sha256']=hashlib.sha256(release_bytes).hexdigest();assert sha(r['_release_path'])==r['_release_sha256'],'release changed after acquisition'
 now=time.time();assert r['phase']==stage and r['actual_job_id']==C['actual_job_id'] and r['source_commit']==C['commit']
 assert 0<=now-r['issued_at']<=300 and r['expires_at']==r['issued_at']+300 and now<=r['expires_at']
 for key in ('groups_file_sha256','snapshot_sha256','image_sha256','input_manifest_sha256','delta_G3_receipt_sha256','bridges_G3_receipt_sha256','placement_sha256','launch_packet_manifest_sha256'):assert r[key]==C[key],key
 assert r['bound_config_sha256']==sha(CONFIG) and r['bank_and_prefix4_only'] is True and r['full_scoring_admitted'] is False and r['current_usage_pass'] is True and r['delta_fresh_preflight_passed'] is True
 assert r['main_root']==C['main_root'] and r['pilot_root']==C['pilot_root']
 assert sha(r['delta_preflight_receipt'])==r['delta_preflight_receipt_sha256']
 proof=json.loads(pathlib.Path(r['delta_preflight_receipt']).read_text());assert proof['complete'] is True and proof['source_commit']==C['commit'] and proof['groups_file_sha256']==C['groups_file_sha256'] and proof['phase']==stage
 assert proof['stable_Delta_catalogues_before_after'] is True and proof['actual_Delta_owning_guards_passed'] is True
 rows=r['catalogues'];assert {x['virtual_path'] for x in rows}>=set(C['minimum_registry_paths']) and len(rows)==len({x['virtual_path'] for x in rows})
 for row in rows:assert sha(row['virtual_path'])==row['sha256']
 assert proof['catalogues']==rows and proof['ledger_sha256']==r['ledger_sha256']
 # Root producer must establish these using actual Delta CPU preflight + live ledger,
 # stable capture/transfer/remote hash/re-read; copied remote snapshots are not live Delta.
 packet();source();allocation(release=r);budget(release=r)
 return r

def entry_release(r,stage):
 # Final cheap phase-entry check AFTER full packet/source/ledger checks, before Popen.
 assert sha(r['_release_path'])==r['_release_sha256'],'release changed after acquisition'
 now=time.time();assert r['phase']==stage and 0<=now-r['issued_at']<=300 and now<=r['expires_at']
 assert r['actual_job_id']==os.environ['SLURM_JOB_ID'] and r['bound_config_sha256']==sha(CONFIG) and r['source_commit']==C['commit']
 assert r['main_root']==C['main_root'] and r['pilot_root']==C['pilot_root'] and r['launch_packet_manifest_sha256']==C['launch_packet_manifest_sha256']
 consumed=pathlib.Path(os.environ['A2_TIMING_EXECUTION_OUTPUT'])/('CONSUMED-'+stage+'.json')
 write(consumed,dict(phase=stage,job_id=C['actual_job_id'],release_sha256=r['_release_sha256'],consumed_at=time.time(),one_original_CLI_stage_only=True))
 for row in r['catalogues']:assert sha(row['virtual_path'])==row['sha256']
 a=allocation(release=r)
 current_end=datetime.datetime.fromisoformat(a['facts']['EndTime']).replace(tzinfo=datetime.timezone.utc).timestamp()
 deadline=min(float(os.environ['A2_H100_INITIAL_END_EPOCH']),current_end,float(os.environ.get('SLURM_JOB_END_TIME',current_end)))
 now=time.time()
 if stage=='prefix4' and deadline-now<C['score_lease_floor_seconds']:
  write(pathlib.Path(os.environ['A2_TIMING_EXECUTION_OUTPUT'])/'BANK_ONLY.json',dict(complete_bank=True,prefix_score_started=False,reason='final phase-entry deadline fell below fixed floor',remaining_seconds=deadline-now,required_seconds=C['score_lease_floor_seconds'],automatic_retry=False));raise SystemExit(0)
 assert deadline-now>C['finish_reserve_seconds']
 now=time.time();assert 0<=now-r['issued_at']<=300 and now<=r['expires_at']
