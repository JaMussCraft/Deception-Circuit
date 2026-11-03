"""Independent real-input review; no model, reservation, or execution authority."""
import os,sys,pathlib,json,hashlib,time,subprocess,traceback,copy,gc,resource
from types import SimpleNamespace
E=pathlib.Path(__file__).resolve().parent
Q=json.loads((E/'config.json').read_text());B=pathlib.Path(Q['runtime']);W=pathlib.Path(Q['worktree']);O=pathlib.Path(Q['output']);C=Q['commit']
def save(name,x):(E/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def binding():
 assert sha(Q['snapshot'])==Q['snapshot_sha256']
 s=json.loads(pathlib.Path(Q['snapshot']).read_text());assert s['source_commit']==C and len(s['source_sha256'])==511 and len(s['input_links'])==4
 for n,h in s['source_sha256'].items():
  p=B/n;assert not p.is_symlink() and not p.stat().st_mode&0o222 and sha(p)==h,n
 for n,target in s['input_links'].items():assert (B/n).is_symlink() and (B/n).resolve()==pathlib.Path(target).resolve()
 return dict(source_sha256=s['source_sha256'],input_links=s['input_links'],snapshot_sha256=sha(Q['snapshot']))
def main():
 job=os.environ['SLURM_JOB_ID'];assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
 raw=subprocess.check_output(['scontrol','show','job',job,'-o'],text=True);facts=dict(i.split('=',1) for i in raw.split() if '=' in i)
 assert facts['JobState']=='RUNNING' and facts['Account'] in Q['cpu_accounts'] and facts['Partition'] in Q['cpu_partitions'] and int(facts['NumCPUs'])>=4
 tres=dict(i.split('=',1) for i in facts.get('AllocTRES','').split(',') if '=' in i);assert not any(k.startswith('gres/gpu') and float(v)>0 for k,v in tres.items())
 hosts=subprocess.check_output(['scontrol','show','hostnames',facts['NodeList']],text=True).split();assert os.uname().nodename.split('.')[0] in [n.split('.')[0] for n in hosts]
 save('allocation-'+job+'.json',dict(raw=raw,hostname=os.uname().nodename,slurm={k:v for k,v in os.environ.items() if k.startswith('SLURM_') and not any(x in k.upper() for x in ('TOKEN','SECRET','AUTH','CREDENTIAL','JWT'))}))
 before=binding();save('source-before-'+job+'.json',before)
 complete=json.loads((O/'run_manifest.json').read_text());terminal=json.loads((O/'evidence/cpu-job-completion.json').read_text())
 assert complete['complete'] and complete['exit_code']==0 and terminal['complete'] and terminal['exit_code']==0 and complete['commit']==C
 assert complete['execution_authorized'] is False and complete['model_loaded'] is False
 parent_job=str(complete['actual_slurm_job_id']);assert parent_job=='23473734' and terminal['actual_slurm_job_id']==parent_job
 parent_accounting=subprocess.check_output(['sacct','-n','-P','-j',parent_job,'--format=JobIDRaw,State,ExitCode'],text=True)
 save('parent-terminal-'+job+'.json',dict(job=parent_job,raw=parent_accounting))
 rows=[line.split('|') for line in parent_accounting.splitlines() if line.strip()];assert any(row[0]==parent_job for row in rows)
 assert all(row[1]=='COMPLETED' and row[2]=='0:0' for row in rows),('parent or batch/extern step not cleanly terminal',rows)
 am=json.loads((O/'evidence/complete-artifact-manifest.json').read_text());assert am['commit']==C and am['artifacts']==complete['artifacts']
 for n,v in am['artifacts'].items():assert (O/n).stat().st_size==v['bytes'] and sha(O/n)==v['sha256'],n
 sys.path.insert(0,str(B))
 from component_analysis import a3_direction_runtime as ar,a3_direction_workload as dw,a3_mask_pipeline as mp,a3_mask_workload as mw,a3_pipeline as cp,ladder_pipeline as lp
 imports=lambda:{n:m.__file__ for n,m in list(sys.modules.items()) if n.split('.')[0] in ('component_analysis','dataset','models','evaluation','scripts') and getattr(m,'__file__',None)}
 assert all(pathlib.Path(p).resolve().is_relative_to(B) for p in imports().values())
 d=lp.read_artifact(O/'canonical/design.json');old=lp.read_artifact(W/'outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819/canonical/design.json')
 for key in ('tasks','utility','ioi_validation','mmlu_validation','access_rows','parent_evidence'):assert d[key]==old[key],key
 assert d['direction_protocol']['workload']==old['direction_protocol']['workload'] and d['direction_protocol']['numeric_profile']==old['direction_protocol']['numeric_profile']
 for name in ('root-ruling.json','execution-settings.json'):assert (O/name).read_bytes()==(W/'outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819'/name).read_bytes()
 prepared=ar.read_object(O/'mask/prepared');assert prepared['identity']['commit']==C and prepared['identity']['code_hashes']==mp.mask_code_hashes() and prepared['execution_authorized'] is False
 args=SimpleNamespace(commit=C,registry=[Q['required_registry']],stage='prepare',design=str(O/'canonical/design.json'),prepared=str(O/'mask/prepared'),work_dir=str(O/'mask'),chunk_size=4,seed=42,arm=None,task=None,group=None)
 live_design,source=mp._live_mask(prepared,args);assert live_design==mp.execution_design(d,prepared['widths'])
 inventories={}
 for stage,count,phase in [('pilot',31191,'M1'),('full',3437966,'M5')]:
  p=O/'mask'/('inventory-'+stage);inv=ar.read_object(p);mw.validate_inventory(inv)
  assert inv['identity']==prepared['identity'] and len(inv['expected_keys'])==count and inv['phase']==phase and inv['chunk_size']==4 and inv['finish_reserve_seconds']==300
  for task,rows in d['tasks'].items():
   for split in ('fit_ids','selection_ids','assessment_ids'):assert inv['scope']['tasks'][task][split]==rows[split]
  assert inv['scope']['hbank_sources']==prepared['hbank_sources'] and inv['scope']['widths']==prepared['widths'] and inv['scope']['new30_reference']==prepared['new30']
  inventories[stage]=dict(keys=count,inventory_sha256=inv['inventory_sha256'],reference=ar.object_reference(p));del inv;gc.collect()
 ledger=ar.normalize_ledger(Q['original_mapping'],identity=prepared['identity'],include_envelope=False,refresh_deadline=time.time()+20)
 active=ar.read_object(ledger['active_mapping_reference']['path']);assert active['generation']>=3 and len(active['expected_entry_ids'])>=39
 assert ledger['snapshot_sha256']==ledger['current_snapshot_sha256']
 sums=dw._ledger(ledger,prepared['identity']);ar.validate_global_budgets(ledger['entries'],contingency_remaining=sums['contingency_remaining']);assert sums['mask_retry_gpu_hours']==0
 policy=dw.mask_replacement_policy();assert sha(Q['approved_policy_path'])==Q['approved_policy_sha256']==policy['approved_policy_sha256']
 original=next(x for x in ledger['entries'] if x['id']=='r-031');assert original['reserved_gpu_hours']==.75 and all(original['actual_entry'].get(k)==v for k,v in policy['original_reservation'].items())
 env=ar.read_object(O/'prospective-admission');assert env['kind'] not in ar.ROOT_ADMISSION_KINDS and env['execution_authorized'] is False and env['actual_reservation_bound'] is False
 draft=env['draft_admission'];assert draft['identity']==prepared['identity'] and draft['upper_inventory_sha256']==inventories['pilot']['inventory_sha256'] and draft['reservation_ids']==[] and draft['max_gpu_hours']==.75
 assert dw.validate_mask_replacement_admission(draft,ledger['entries'])==dict(execution_authorized=False,reservation_bound=False)
 contract=draft['allocation_contract'];assert contract==dict(kind='a3_allocation_contract_v1',scheduler_work_dir=str(B),source_commit=C,cpus=4,memory_bytes=68719476736,gpus=1,gpu_type='h200')
 negatives=[]
 for key,value in [('max_gpu_hours',.750001),('mask_replacement_policy',{}),('reservation_ids',['r-031'])]:
  bad=copy.deepcopy(draft);bad[key]=value;bad['admission_sha256']=dw.digest({k:v for k,v in bad.items() if k!='admission_sha256'})
  try:dw.validate_mask_replacement_admission(bad,ledger['entries'])
  except (ValueError,AssertionError):negatives.append(key)
  else:raise AssertionError('real-draft invalid mutation accepted: '+key)
 after=binding();assert before==after
 assert all(pathlib.Path(p).resolve().is_relative_to(B) for p in imports().values())
 save('review-detail-'+job+'.json',dict(commit=C,inventories=inventories,source_evidence=source,imports=imports(),completed_mapping=ledger['active_mapping_reference'],mapping_generation=active['generation'],mapping_rows=len(active['expected_entry_ids']),original=original,current_ledger_sha256=ledger['snapshot_sha256'],negative_probes=negatives,source_unchanged=True,prospective_not_execution_authority=True,actual_h200_launch_review_pending=True))
START=time.time();status=dict(commit=C,execution_authorized=False,models_loaded=False,job=os.environ.get('SLURM_JOB_ID'))
try:main();status.update(complete=True,exit_code=0)
except BaseException as err:status.update(complete=False,exit_code=1,error=repr(err),traceback=traceback.format_exc());raise
finally:
 status.update(elapsed_seconds=time.time()-START,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024);save('COMPLETE-'+str(status['job'])+'.json',status);print(json.dumps(status),flush=True)
